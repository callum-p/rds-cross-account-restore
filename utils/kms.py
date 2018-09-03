from utils.iam import get_client, get_account_id_from_name
import json
from hashlib import md5


def get_key_id_from_alias(account, key_alias):
    client = get_client(account, 'kms')
    args = {}
    while True:
        response = client.list_aliases(**args)
        for alias in response['Aliases']:
            if alias['AliasName'] == key_alias:
                return alias['TargetKeyId']
        if response['Truncated'] is True:
            args['Marker'] = response['NextMarker']
        else:
            break
    raise ValueError(f'KMS key alias {key_alias} not found.')


def get_temporary_permissions_sid(share_accounts):
    return 'temporary permissions ' + \
        md5(' '.join(share_accounts).encode('utf-8')).hexdigest()


def share_kms_key(account, key, share_accounts):
    client = get_client(account, 'kms')
    key_id = key

    if key.startswith('alias/'):
        key_id = get_key_id_from_alias(account, key)

    response = client.get_key_policy(KeyId=key_id, PolicyName='default')
    key_policy = json.loads(response['Policy'])

    sid = get_temporary_permissions_sid(share_accounts)

    new_policy_part_a = {
        "Sid": sid,
        "Effect": "Allow",
        "Principal": {
            "AWS": []
        },
        "Action": [
            "kms:CreateGrant"
        ],
        "Resource": "*"
    }
    new_policy_part_b = {
        "Sid": sid + '-b',
        "Effect": "Allow",
        "Principal": {
            "AWS": []
        },
        "Action": [
            "kms:CreateGrant"
        ],
        "Resource": "*",
        "Condition": {
            "Bool": {
                "kms:GrantIsForAWSResource": "true"
            }
        }
    }
    if not isinstance(share_accounts, list):
        share_accounts = [share_accounts]

    for sa in share_accounts:
        if not sa.isnumeric():
            sa = get_account_id_from_name(sa)
        new_policy_part_a['Principal']['AWS'].append(
            f'arn:aws:iam::{sa}:root')
        new_policy_part_b['Principal']['AWS'].append(
            f'arn:aws:iam::{sa}:root')

    key_policy['Statement'].append(new_policy_part_a)
    key_policy['Statement'].append(new_policy_part_b)

    try:
        client.put_key_policy(
            KeyId=key_id,
            PolicyName='default',
            Policy=json.dumps(key_policy))
    except client.exceptions.MalformedPolicyDocumentException as e:
        print(json.dumps(key_policy))
        raise(e)


def unshare_kms_key(account, key, share_accounts):
    client = get_client(account, 'kms')
    key_id = key

    if key.startswith('alias/'):
        key_id = get_key_id_from_alias(account, key)

    response = client.get_key_policy(KeyId=key_id, PolicyName='default')
    key_policy = json.loads(response['Policy'])

    sid = get_temporary_permissions_sid(share_accounts)
    for idx, statement in enumerate(key_policy['Statement']):
        if statement['Sid'] == sid:
            del key_policy['Statement'][idx]
        elif statement['Sid'] == sid + '-b':
            del key_policy['Statement'][idx]
    client.put_key_policy(
        KeyId=key_id,
        PolicyName='default',
        Policy=json.dumps(key_policy))
