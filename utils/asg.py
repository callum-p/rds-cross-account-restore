from utils.iam import get_client, get_account_id_from_name


def suspend_asg_action(account, region, asg_action, asg_name):
    client = get_client(account, 'autoscaling', region)
    args = {'AutoScalingGroupName': asg_name}
    if asg_action.lower() != 'all':
        if not isinstance(asg_action, list):
            asg_action = [asg_action]
            args['ScalingProcesses'] = asg_action
    client.suspend_processes(**args)


def resume_asg_action(account, region, asg_action, asg_name):
    client = get_client(account, 'autoscaling', region)
    args = {'AutoScalingGroupName': asg_name}
    if asg_action.lower() != 'all':
        if not isinstance(asg_action, list):
            asg_action = [asg_action]
            args['ScalingProcesses'] = asg_action
    client.resume_processes(**args)
