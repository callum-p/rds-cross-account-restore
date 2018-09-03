import time
import logging
from utils.iam import get_client, get_account_id_from_name


def get_rds_instance_kms_key(account, db_instance):
    client = get_client(account, 'rds')
    response = client.describe_db_instances(DBInstanceIdentifier=db_instance)
    if 'KmsKeyId' in response['DBInstances'][0]:
        return response['DBInstances'][0]['KmsKeyId']
    return None


def rds_instance_exists(account, db_instance):
    client = get_client(account, 'rds')
    try:
        client.describe_db_instances(DBInstanceIdentifier=db_instance)
    except client.exceptions.DBInstanceNotFoundFault as e:
        return False
    return True


def get_rds_instance_status(account, db_instance):
    client = get_client(account, 'rds')
    response = client.describe_db_instances(
        DBInstanceIdentifier=db_instance)
    return response['DBInstances'][0]['DBInstanceStatus']


def rds_snapshot_exists(account, snapshot_name):
    client = get_client(account, 'rds')
    try:
        client.describe_db_snapshots(DBSnapshotIdentifier=snapshot_name)
    except client.exceptions.DBSnapshotNotFoundFault as e:
        return False
    return True


def get_rds_snapshot_status(account, snapshot_name):
    client = get_client(account, 'rds')
    response = client.describe_db_snapshots(DBSnapshotIdentifier=snapshot_name)
    return response['DBSnapshots'][0]['Status']


def delete_rds_snapshot(account, snapshot_name):
    client = get_client(account, 'rds')
    logging.warning(f'Deleting snapshot {snapshot_name}...')
    status = None
    while status != 'available' and status != 'failed':
        status = get_rds_snapshot_status(account, snapshot_name)
        time.sleep(5)
    client.delete_db_snapshot(DBSnapshotIdentifier=snapshot_name)


def create_rds_snapshot(account, db_instance, snapshot_name, wait=False):
    client = get_client(account, 'rds')

    if rds_snapshot_exists(account, snapshot_name):
        logging.warning(f'Snapshot {snapshot_name} exists...')
        delete_rds_snapshot(account, snapshot_name)

    logging.warning(f'Creating snapshot {snapshot_name} from DB {db_instance}')
    client.create_db_snapshot(
        DBSnapshotIdentifier=snapshot_name,
        DBInstanceIdentifier=db_instance)

    if wait is True:
        status = None
        last_status = None
        while status != 'available':
            status = get_rds_snapshot_status(account, snapshot_name)
            if last_status != status:
                last_status = status
                logging.warning(f'Snapshot {snapshot_name} status: {status}')
            time.sleep(5)


def share_rds_snapshot(account, snapshot_name, share_accounts):
    if not isinstance(share_accounts, list):
        share_accounts = [share_accounts]
    share_account_ids = []
    for sa in share_accounts:
        share_account_ids.append(get_account_id_from_name(sa))
    client = get_client(account, 'rds')
    logging.warning(f'Sharing DB snapshot {snapshot_name} with accounts ' +
                    ' '.join(share_accounts))
    client.modify_db_snapshot_attribute(
        DBSnapshotIdentifier=snapshot_name,
        AttributeName='restore',
        ValuesToAdd=share_account_ids)


def copy_rds_snapshot(source_account, dest_account, snapshot_name,
                      dest_snapshot_name, region, kms_key, wait=False):
    client = get_client(dest_account, 'rds')
    source_account_id = get_account_id_from_name(source_account)
    if rds_snapshot_exists(dest_account, dest_snapshot_name):
        logging.warning(f'Destination snapshot {dest_snapshot_name} exists...')
        delete_rds_snapshot(dest_account, dest_snapshot_name)

    logging.warning(f'Copying RDS snapshot {snapshot_name} '
                    f'from {source_account} to {dest_account}')
    client.copy_db_snapshot(
        SourceDBSnapshotIdentifier=f'arn:aws:rds:{region}:{source_account_id}:snapshot:{snapshot_name}',  # noqa
        TargetDBSnapshotIdentifier=dest_snapshot_name,
        KmsKeyId=kms_key)

    if wait is True:
        status = None
        last_status = None
        while status != 'available':
            status = get_rds_snapshot_status(dest_account, dest_snapshot_name)
            if last_status != status:
                last_status = status
                logging.warning(f'Snapshot {dest_snapshot_name} status: '
                                f'{status}')
            time.sleep(5)


def delete_rds_instance(account, db_instance, wait=False):
    client = get_client(account, 'rds')
    logging.warning(f'Deleting RDS instance {db_instance}')
    client.delete_db_instance(
        DBInstanceIdentifier=db_instance,
        SkipFinalSnapshot=True)
    if wait is True:
        while rds_instance_exists(account, db_instance):
            time.sleep(5)


def restore_db_from_snapshot(account, snapshot_name, db_instance,
                             db_instance_type, subnet_group, multi_az, public,
                             option_group, storage_type, wait=False):
    client = get_client(account, 'rds')

    if rds_instance_exists(account, db_instance):
        logging.warning(f'DB {db_instance} exists.')
        delete_rds_instance(account, db_instance, True)

    logging.warning(f'Restoring DB {db_instance} from snapshot '
                    f'{snapshot_name}..')
    client.restore_db_instance_from_db_snapshot(
        DBInstanceIdentifier=db_instance,
        DBSnapshotIdentifier=snapshot_name,
        DBInstanceClass=db_instance_type,
        DBSubnetGroupName=subnet_group,
        MultiAZ=multi_az,
        PubliclyAccessible=public,
        OptionGroupName=option_group,
        StorageType='gp2',
        CopyTagsToSnapshot=True)

    if wait is True:
        status = None
        last_status = None
        while status != 'available':
            status = get_rds_instance_status(account, db_instance)
            if last_status != status:
                last_status = status
                logging.warning(f'DB {db_instance} status: {status}')
            time.sleep(5)


def modify_db_instance(account, db_instance, db_security_groups=None,
                       master_password=None, parameter_group=None, wait=False):
    client = get_client(account, 'rds')
    args = {}
    if db_security_groups is not None:
        if not isinstance(db_security_groups, list):
            db_security_groups = [db_security_groups]
        args['VpcSecurityGroupIds'] = db_security_groups

    if master_password is not None:
        args['MasterUserPassword'] = master_password

    if parameter_group is not None:
        args['DBParameterGroupName'] = parameter_group

    if args == {}:
        return

    args['DBInstanceIdentifier'] = db_instance

    logging.warning(f'Modifying DB instance {db_instance}')
    client.modify_db_instance(**args)
    time.sleep(10)

    if wait is True:
        status = None
        last_status = None
        while status != 'available':
            status = get_rds_instance_status(account, db_instance)
            if last_status != status:
                last_status = status
                logging.warning(f'DB {db_instance} status: {status}')
            time.sleep(5)


def reboot_db_instance(account, db_instance, wait=False):
    client = get_client(account, 'rds')
    logging.warning(f'Rebooting DB instance {db_instance}...')
    client.reboot_db_instance(DBInstanceIdentifier=db_instance)
    time.sleep(10)
    if wait is True:
        status = None
        last_status = None
        while status != 'available':
            status = get_rds_instance_status(account, db_instance)
            if last_status != status:
                last_status = status
                logging.warning(f'DB {db_instance} status: {status}')
            time.sleep(5)