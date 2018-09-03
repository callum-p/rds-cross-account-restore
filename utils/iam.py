#!/usr/bin/env python3

import boto3
import os
import pwd
import json
from datetime import datetime, timezone

accounts = {}
creds = {}


def iam_init():
    load_accounts()


def load_accounts():
    global accounts
    with open('aws_accounts.json') as f:
        accounts = json.load(f)


def get_account_id_from_name(name):
    account = accounts[name]
    account = account[13:]
    account = account[0:account.index(':')]
    return account


def get_client(account, service, region='ap-southeast-2'):
    creds = assume_role(account)
    client = boto3.client(
        service_name=service,
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken'],
        region_name=region
    )
    return client


def assume_role(account, timeout=28800):
    global creds

    if account in creds:
        if creds[account]['Expiration'] < datetime.now(tz=timezone.utc):
            return creds[account]

    arn = None
    for a, k in accounts.items():
        if a.startswith(account):
            arn = k
            break

    if arn is None:
        raise ValueError(f'ARN for account {account} not found.')

    client = boto3.client('sts')
    username = pwd.getpwuid(os.getuid())[0]
    response = client.assume_role(
        RoleArn=arn,
        RoleSessionName=username,
        DurationSeconds=timeout
    )

    creds[account] = response['Credentials']
    return response['Credentials']
