#!/usr/bin/env python3

import logging
from utils.iam import assume_role, iam_init
from utils.args import setup_args
from utils.rds import create_rds_snapshot, share_rds_snapshot, \
    copy_rds_snapshot, restore_db_from_snapshot, modify_db_instance, \
    reboot_db_instance, get_rds_instance_kms_key
from utils.kms import share_kms_key, unshare_kms_key
from utils.ssm import get_parameter, run_command
from utils.asg import suspend_asg_action, resume_asg_action


def main():
    args = setup_args()
    iam_init()

    # setup logging
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, args.log_level.upper()))

    # create snapshot
    create_rds_snapshot(
        account=args.source_account,
        region=args.source_region,
        db_instance=args.source_instance,
        snapshot_name=args.source_snapshot_name,
        wait=True)

    # share snapshot with dest account
    share_rds_snapshot(
        args.source_account,
        args.source_region,
        args.source_snapshot_name, args.dest_account)

    # if kms key provided in args, share with destination account temporarily
    source_kms_key = get_rds_instance_kms_key(
        account=args.source_account,
        region=args.source_region,
        db_instance=args.source_instance)

    if args.source_account != args.dest_account:
        if source_kms_key is not None:
            share_kms_key(
                account=args.source_account,
                region=args.source_region,
                share_accounts=args.dest_account,
                key=source_kms_key)

    # copy snapshot to destination account
    copy_args = {
        'source_account': args.source_account,
        'source_region': args.source_region,
        'dest_account': args.dest_account,
        'region': args.dest_region,
        'snapshot_name': args.source_snapshot_name,
        'dest_snapshot_name': args.dest_snapshot_name,
        'wait': True
    }
    if args.dest_kms_key:
        copy_args['kms_key'] = args.dest_kms_key
    if args.source_account != args.dest_account or \
            args.source_region != args.dest_region:
        copy_rds_snapshot(**copy_args)

    # unshare kms key now that snapshot is copied
    if args.source_account != args.dest_account:
        if source_kms_key is not None:
            unshare_kms_key(
                account=args.source_account,
                region=args.source_region,
                share_accounts=args.dest_account,
                key=source_kms_key)

    # run any asg pre restore suspend actions
    if len(args.pre_restore_asg_suspend_action):
        for idx, action in enumerate(args.pre_restore_asg_suspend_action):
            suspend_asg_action(
                args.dest_account,
                args.dest_region,
                action,
                args.pre_restore_asg_name[idx])

    # run any SSM pre restore commands
    if len(args.pre_restore_ssm_command):
        for idx, command in enumerate(args.pre_restore_ssm_command):
            run_command(
                args.dest_account,
                args.dest_region,
                command,
                args.pre_restore_ssm_instance_names[idx])

    # restore snapshot in destination account
    restore_db_from_snapshot(
        account=args.dest_account,
        region=args.dest_region,
        snapshot_name=args.dest_snapshot_name,
        db_instance=args.dest_instance,
        db_instance_type=args.instance_type,
        subnet_group=get_parameter(args.dest_account, args.dest_region,
                                   args.ssm_subnet_group),
        multi_az=args.multi_az,
        public=args.public,
        option_group=get_parameter(args.dest_account, args.dest_region,
                                   args.ssm_option_group),
        storage_type=args.storage_type,
        wait=True)

    # reset password, security groups etc
    db_security_groups = [
        get_parameter(args.dest_account, args.dest_region, x) for sg in
        args.ssm_security_group]
    modify_db_instance(
        account=args.dest_account,
        region=args.dest_region,
        db_instance=args.dest_instance,
        db_security_groups=db_security_groups,
        master_password=get_parameter(args.dest_account, args.dest_region,
                                      args.ssm_db_password),
        parameter_group=get_parameter(args.dest_account, args.dest_region,
                                      args.ssm_parameter_group),
        wait=True)

    # reboot instance to apply final changes
    reboot_db_instance(
        account=args.dest_account,
        region=args.dest_region,
        db_instance=args.dest_instance,
        wait=True)

    # run any SSM post restore commands
    if len(args.post_restore_ssm_command):
        for idx, command in enumerate(args.post_restore_ssm_command):
            run_command(
                args.dest_account,
                args.dest_region,
                command,
                args.post_restore_ssm_instance_names[idx])

    # run any asg post restore resume actions
    if len(args.post_restore_asg_resume_action):
        for idx, action in enumerate(args.post_restore_asg_resume_action):
            resume_asg_action(
                args.dest_account,
                args.dest_region,
                action,
                args.post_restore_asg_name[idx])


if __name__ == '__main__':
    main()
