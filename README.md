# Cross Account RDS Restore

## Warning
Running this script will delete the target RDS instance. Run at your own risk.

## Setup
Copy aws_accounts.json.example to aws_accounts.json and setup appropriate assume role configurations in aws_accounts.json.example

## Usage

```
./rds_backup.py --source-account prod-old --dest-account dev --source-instance db-dev --dest-instance db --source-snapshot-name callum --dest-snapshot-name callum --instance-type db.t2.small --dest-kms-key alias/rds --pre-restore-ssm-command StopCron --pre-restore-ssm-instance-names callum-test
```

```
usage: rds_backup.py [-h] --source-account SOURCE_ACCOUNT --source-instance
                     SOURCE_INSTANCE --source-snapshot-name
                     SOURCE_SNAPSHOT_NAME [--source-region SOURCE_REGION]
                     --dest-account DEST_ACCOUNT [--dest-kms-key DEST_KMS_KEY]
                     --instance-type INSTANCE_TYPE --dest-instance
                     DEST_INSTANCE --dest-snapshot-name DEST_SNAPSHOT_NAME
                     [--dest-region DEST_REGION] [--multi-az] [--public]
                     [--storage-type STORAGE_TYPE]
                     [--ssm-security-group SSM_SECURITY_GROUP]
                     [--ssm-db-password SSM_DB_PASSWORD]
                     [--ssm-subnet-group SSM_SUBNET_GROUP]
                     [--ssm-option-group SSM_OPTION_GROUP]
                     [--ssm-parameter-group SSM_PARAMETER_GROUP]
                     [--log-level LOG_LEVEL]
                     [--pre-restore-ssm-command PRE_RESTORE_SSM_COMMAND [PRE_RESTORE_SSM_COMMAND ...]]
                     [--pre-restore-ssm-instance-names PRE_RESTORE_SSM_INSTANCE_NAMES [PRE_RESTORE_SSM_INSTANCE_NAMES ...]]
                     [--post-restore-ssm-command POST_RESTORE_SSM_COMMAND [POST_RESTORE_SSM_COMMAND ...]]
                     [--post-restore-ssm-instance-names POST_RESTORE_SSM_INSTANCE_NAMES [POST_RESTORE_SSM_INSTANCE_NAMES ...]]

optional arguments:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        Log level

source:
  --source-account SOURCE_ACCOUNT
                        Account with the source DB
  --source-instance SOURCE_INSTANCE
                        Source RDS instance name
  --source-snapshot-name SOURCE_SNAPSHOT_NAME
                        Name of snapshot to take for the source DB
  --source-region SOURCE_REGION
                        AWS region for source snapshot

destination:
  --dest-account DEST_ACCOUNT
                        Account with the destination DB
  --dest-kms-key DEST_KMS_KEY
                        Destination KMS key to use if copying encrypted
                        database
  --instance-type INSTANCE_TYPE
                        Destination RDS instance type
  --dest-instance DEST_INSTANCE
                        Destination RDS instance name
  --dest-snapshot-name DEST_SNAPSHOT_NAME
                        Name of destination snapshot when copying source
  --dest-region DEST_REGION
                        AWS region for destination snapshot
  --multi-az            Make destination DB multi AZ
  --public              Make destination DB public
  --storage-type STORAGE_TYPE
                        Specify storage type for destination RDS instance

SSM:
  --ssm-security-group SSM_SECURITY_GROUP
                        Name of SSM parameter containing the SG for the DB
  --ssm-db-password SSM_DB_PASSWORD
                        Name of SSM parameter containing the DB password
  --ssm-subnet-group SSM_SUBNET_GROUP
                        Name of SSM parameter containing the subnet group for
                        the DB
  --ssm-option-group SSM_OPTION_GROUP
                        Name of SSM parameter containing the option group for
                        the DB
  --ssm-parameter-group SSM_PARAMETER_GROUP
                        Name of SSM parameter containing the parameter group
                        for the DB

Pre Restore Commands:
  --pre-restore-ssm-command PRE_RESTORE_SSM_COMMAND [PRE_RESTORE_SSM_COMMAND ...]
                        An SSM command to run before starting restore actions
  --pre-restore-ssm-instance-names PRE_RESTORE_SSM_INSTANCE_NAMES [PRE_RESTORE_SSM_INSTANCE_NAMES ...]
                        Name tag of instances to run pre-restore commands on

Post Restore Commands:
  --post-restore-ssm-command POST_RESTORE_SSM_COMMAND [POST_RESTORE_SSM_COMMAND ...]
                        An SSM command to run after restore actions have
                        finished
  --post-restore-ssm-instance-names POST_RESTORE_SSM_INSTANCE_NAMES [POST_RESTORE_SSM_INSTANCE_NAMES ...]
                        Name tag of instances to run post-restore commands on
```
