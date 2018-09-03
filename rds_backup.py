#!/usr/bin/env python3

import logging
from utils.iam import assume_role, iam_init
from utils.args import setup_args
from utils.rds import create_rds_snapshot, share_rds_snapshot, \
    copy_rds_snapshot, restore_db_from_snapshot, modify_db_instance, \
    reboot_db_instance, get_rds_instance_kms_key
from utils.kms import share_kms_key, unshare_kms_key
from utils.ssm import get_parameter, run_command


def main():
    args = setup_args()
    iam_init()

    # setup logging
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, args.log_level.upper()))

    # create snapshot
    create_rds_snapshot(
        account=args.source_account,
        db_instance=args.source_instance,
        snapshot_name=args.source_snapshot_name,
        wait=True)

    # share snapshot with dest account
    share_rds_snapshot(
        args.source_account, args.source_snapshot_name, args.dest_account)

    # if kms key provided in args, share with destination account temporarily
    source_kms_key = get_rds_instance_kms_key(
        account=args.source_account,
        db_instance=args.source_instance)
    if source_kms_key is not None:
        share_kms_key(
            account=args.source_account,
            share_accounts=args.dest_account,
            key=source_kms_key)

    # copy snapshot to destination account
    copy_args = {
        'source_account': args.source_account,
        'dest_account': args.dest_account,
        'snapshot_name': args.source_snapshot_name,
        'dest_snapshot_name': args.dest_snapshot_name,
        'region': args.source_region,
        'wait': True
    }
    if args.dest_kms_key:
        copy_args['kms_key'] = args.dest_kms_key
    copy_rds_snapshot(**copy_args)

    # unshare kms key now that snapshot is copied
    if source_kms_key is not None:
        unshare_kms_key(
            account=args.source_account,
            share_accounts=args.dest_account,
            key=source_kms_key)

    # run any SSM pre restore commands
    if len(args.pre_restore_ssm_command):
        for idx, command in enumerate(args.pre_restore_ssm_command):
            run_command(
                args.dest_account,
                command,
                args.pre_restore_ssm_instance_names[idx])

    # restore snapshot in destination account
    restore_db_from_snapshot(
        account=args.dest_account,
        snapshot_name=args.dest_snapshot_name,
        db_instance=args.dest_instance,
        db_instance_type=args.instance_type,
        subnet_group=get_parameter(args.dest_account, args.ssm_subnet_group),
        multi_az=args.multi_az,
        public=args.public,
        option_group=get_parameter(args.dest_account, args.ssm_option_group),
        storage_type=args.storage_type,
        wait=True)

    # reset password, security groups etc
    modify_db_instance(
        account=args.dest_account,
        db_instance=args.dest_instance,
        db_security_groups=get_parameter(args.dest_account,
                                         args.ssm_security_group),
        master_password=get_parameter(args.dest_account, args.ssm_db_password),
        parameter_group=get_parameter(args.dest_account,
                                      args.ssm_parameter_group),
        wait=True)

    # reboot instance to apply final changes
    reboot_db_instance(
        account=args.dest_account,
        db_instance=args.dest_instance,
        wait=True)

    # run any SSM post restore commands
    if len(args.post_restore_ssm_command):
        for idx, command in enumerate(args.post_restore_ssm_command):
            run_command(
                args.dest_account,
                command,
                args.post_restore_ssm_instance_names[idx])


if __name__ == '__main__':
    main()