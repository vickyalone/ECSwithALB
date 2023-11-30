import boto3

def create_cluster():
    ecs = boto3.client('ecs', region_name='ap-south-1')
    response = ecs.create_cluster(clusterName='my-cluster')

def register_task_definition():
    ecs = boto3.client('ecs', region_name='ap-south-1')
    response = ecs.register_task_definition(
        family='taskdef',
        networkMode='awsvpc',
        requiresCompatibilities=['FARGATE'],
        cpu='256',
        memory='512',
        containerDefinitions=[
            {
                'name': 'nginx',
                'image': 'nginx',
                'essential': True,
                'portMappings': [
                    {
                        'containerPort': 80,
                        'hostPort': 80
                    },
                ],
            },
        ],
        executionRoleArn='arn:aws:iam::497595539056:role/ecsTaskExecutionRole'
    )

def create_load_balancer():
    elbv2 = boto3.client('elbv2', region_name='ap-south-1')
    response = elbv2.create_load_balancer(
        Name='alb-test',
        Subnets=['subnet-09a00c70dac535df0', 'subnet-0150e21d640382ae9'],  # Replace with your public subnets
        SecurityGroups=['sg-0e4d166343cc1e44b'],  # Replace with your security group
        Scheme='internet-facing',
        Type='application',
    )
    
    load_balancer_arn = response['LoadBalancers'][0]['LoadBalancerArn']
    
    return load_balancer_arn

def create_target_group():
    elbv2 = boto3.client('elbv2', region_name='ap-south-1')
    response = elbv2.create_target_group(
        Name='tg-test',
        Protocol='HTTP',
        Port=80,
        VpcId=	'vpc-0fbcaed020cc53d30',
        TargetType='ip',
    )
    
    target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
    
    return target_group_arn

def create_listener(load_balancer_arn, target_group_arn):
    elbv2 = boto3.client('elbv2', region_name='ap-south-1')
    response = elbv2.create_listener(
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': target_group_arn,
            },
        ],
        LoadBalancerArn=load_balancer_arn,
        Port=80,
        Protocol='HTTP',
    )

def create_service(target_group_arn):
    ecs = boto3.client('ecs', region_name='ap-south-1')
    response = ecs.create_service(
        cluster='my-cluster',
        serviceName='ecs-nginx-service',
        taskDefinition='taskdef:1',
        desiredCount=1,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': ['subnet-059dd88ec72530590'],  # Replace with your private subnet
                'securityGroups': ['sg-0e4d166343cc1e44b'],  # Replace with your security group
                'assignPublicIp': 'ENABLED'
            }
        },
        platformVersion='1.4.0',
        loadBalancers=[
            {
                'targetGroupArn': target_group_arn,
                'containerName': 'nginx',
                'containerPort': 80,
            },
        ],
    )

if __name__ == "__main__":
    create_cluster()
    register_task_definition()
    load_balancer_arn = create_load_balancer()
    target_group_arn = create_target_group()
    create_listener(load_balancer_arn, target_group_arn)
    create_service(target_group_arn)

    # Retrieve DNS name of the ALB
    elbv2 = boto3.client('elbv2', region_name='ap-south-1')
    response = elbv2.describe_load_balancers(Names=['alb-test'])
    alb_dns_name = response['LoadBalancers'][0]['DNSName']

    print(f"ALB DNS Name: {alb_dns_name}")
