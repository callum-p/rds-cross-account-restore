from utils.iam import get_client
import logging
import time


def get_parameter(account, parameter_name):
    client = get_client(account, 'ssm')
    response = client.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']


def wait_for_command(account, command_id, instances):
    completions = 0
    completed_statuses = [
        'Success',
        'Cancelled',
        'Failed',
        'TimedOut'
    ]
    while True:
        for instance in instances:
            status = get_command_invocation_status(
                account, command_id, instance)
            if status in completed_statuses:
                logging.warning(f'Command {command_id} finished on '
                                f'{instance} with status {status}')
                completions += 1
        if completions >= len(instances):
            break
        time.sleep(5)
    logging.warning(f'Command {command_id} finished on all instances.')


def run_command(account, command, instance_name):
    client = get_client(account, 'ssm')
    logging.warning(f'Running command {command} on instances with name '
                    f'{instance_name}')
    response = client.send_command(
        Targets=[{
            'Key': 'tag:Name',
            'Values': [instance_name]
        }],
        DocumentName=command)
    command_id = response['Command']['CommandId']
    instances = get_command_invocation_instances(account, command_id)
    logging.warning(f'Waiting for command {command_id} to finish executing.')
    wait_for_command(account, command_id, instances)


def get_command_invocation_instances(account, command_id):
    client = get_client(account, 'ssm')
    instances = []
    args = {
        'CommandId': command_id
    }
    while True:
        response = client.list_command_invocations(**args)
        if 'NextToken' in response and response['NextToken'] != '':
            args['NextToken'] = response['NextToken']
        else:
            break
    for invocation in response['CommandInvocations']:
        instances.append(invocation['InstanceId'])
    return instances


def get_command_invocation_status(account, command_id, instance_id):
    client = get_client(account, 'ssm')
    response = client.get_command_invocation(
        CommandId=command_id, InstanceId=instance_id)
    return response['Status']
