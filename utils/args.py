import argparse


def validate_args(args):
    if len(args.pre_restore_ssm_command) != \
            len(args.pre_restore_ssm_instance_names):
        raise ValueError("Pre-restore SSM commands and instances don't"
                         'match')
    if len(args.post_restore_ssm_command) != \
            len(args.post_restore_ssm_instance_names):
        raise ValueError("Post-restore SSM commands and instances don't"
                         'match')


def setup_args():
    parser = argparse.ArgumentParser()
    source = parser.add_argument_group('source')
    source.add_argument(
        '--source-account',
        help='Account with the source DB',
        required=True)
    source.add_argument(
        '--source-instance',
        required=True,
        help='Source RDS instance name')
    source.add_argument(
        '--source-snapshot-name',
        required=True,
        help='Name of snapshot to take for the source DB')
    source.add_argument(
        '--source-region',
        default='ap-southeast-2',
        help='AWS region for source snapshot')

    dest = parser.add_argument_group('destination')
    dest.add_argument(
        '--dest-account',
        help='Account with the destination DB',
        required=True)
    dest.add_argument(
        '--dest-kms-key',
        help='Destination KMS key to use if copying encrypted database')
    dest.add_argument(
        '--instance-type',
        required=True,
        help='Destination RDS instance type')

    dest.add_argument(
        '--dest-instance',
        required=True,
        help='Destination RDS instance name')

    dest.add_argument(
        '--dest-snapshot-name',
        required=True,
        help='Name of destination snapshot when copying source')

    dest.add_argument(
        '--dest-region',
        default='ap-southeast-2',
        help='AWS region for destination snapshot')
    dest.add_argument(
        '--multi-az',
        action='store_true',
        help='Make destination DB multi AZ')
    dest.add_argument(
        '--public',
        action='store_true',
        help='Make destination DB public')
    dest.add_argument(
        '--storage-type',
        default='gp2',
        help='Specify storage type for destination RDS instance')

    ssm = parser.add_argument_group('SSM')
    ssm.add_argument(
        '--ssm-security-group',
        default='shared.LAPIS_DB_SG',
        help='Name of SSM parameter containing the SG for the DB')
    ssm.add_argument(
        '--ssm-db-password',
        default='lapis.DB_PASSWORD',
        help='Name of SSM parameter containing the DB password')
    ssm.add_argument(
        '--ssm-subnet-group',
        default='shared.PRIVATE_RDS_SUBNET_GROUP',
        help='Name of SSM parameter containing the subnet group for the DB')
    ssm.add_argument(
        '--ssm-option-group',
        default='shared.POSTGRES_96_OPTION_GROUP',
        help='Name of SSM parameter containing the option group for the DB')
    ssm.add_argument(
        '--ssm-parameter-group',
        default='lapis.DB_PARAMETER_GROUP',
        help='Name of SSM parameter containing the parameter group for the DB')

    parser.add_argument(
        '--log-level',
        default='warning',
        help='Log level'
    )

    pre = parser.add_argument_group('Pre Restore Commands')
    pre.add_argument(
        '--pre-restore-ssm-command',
        action='append',
        default=[],
        help='An SSM command to run before starting restore actions')
    pre.add_argument(
        '--pre-restore-ssm-instance-names',
        action='append',
        default=[],
        help='Name tag of instances to run pre-restore commands on')

    post = parser.add_argument_group('Post Restore Commands')
    post.add_argument(
        '--post-restore-ssm-command',
        action='append',
        default=[],
        help='An SSM command to run after restore actions have finished')
    post.add_argument(
        '--post-restore-ssm-instance-names',
        action='append',
        default=[],
        help='Name tag of instances to run post-restore commands on')

    args = parser.parse_args()
    if args.multi_az is None:
        args.multi_az = False
    if args.public is None:
        args.public = False
    validate_args(args)
    return args
