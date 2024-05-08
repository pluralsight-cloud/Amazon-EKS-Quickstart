import argparse
import boto3

# Argument parsing
parser = argparse.ArgumentParser(
    description="Cleans up resources with dependencies from within the AWS account after EKSCTL deletion command."
)
parser.add_argument(
    "-p", "--profile-name", required=False, help="AWS CLI Profile to leverage for creds"
)
args = parser.parse_args()

# AWS CLI Profile Name and IAM boto3 client set up and STS client set up
if args.profile_name:
    AWS_PROFILE_NAME = args.profile_name
    session = boto3.Session(profile_name=AWS_PROFILE_NAME)
    iam = session.client("iam")
    sts = session.client("sts")
    elbv2 = session.client("elbv2")
else:
    iam = boto3.client("iam")
    sts = boto3.client("sts")
    elbv2 = boto3.client("elbv2")


def delete_ingress(alb_name_prefix):
    """Lists ALBs in the region and deletes an ALB with a matching name prefix."""

    # List ALBs
    response = elbv2.describe_load_balancers()
    for alb in response["LoadBalancers"]:
        alb_arn = alb["LoadBalancerArn"]
        alb_name = alb["LoadBalancerName"]

        # Check if the ALB name matches the prefix
        if alb_name.startswith(alb_name_prefix):
            try:
                print(f"Deleting ALB: {alb_name}")
                elbv2.delete_load_balancer(LoadBalancerArn=alb_arn)
                print("ALB deleted successfully")
            except Exception as e:
                print(f"Failed to delete ALB {alb_name}: {e}")


def delete_iam_resources():
    # Getting Account ID
    account_id = sts.get_caller_identity()["Account"]

    role_name = "AmazonEKSLoadBalancerControllerRole"
    policy_name = "AWSLoadBalancerControllerIAMPolicy"

    # 0. Detach policy from IAM Role
    # 1. Delete the IAM Policy (if exists)
    # 2. Delete the IAM Role (if exists)

    try:
        # Get the policy's ARN
        policy_arn = f"arn:aws:iam::{account_id}:policy/eks/{policy_name}"

        # Detach the policy
        iam.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        print(f"IAM Policy '{policy_name}' detached.")

        # Delete the policy
        iam.delete_policy(PolicyArn=policy_arn)
        print(f"IAM Policy '{policy_name}' deleted.")

        # Delete the role
        iam.delete_role(RoleName=role_name)
        print(f"IAM Role '{role_name}' deleted.")

    except iam.exceptions.NoSuchEntityException as e:
        print(f"Error: {e}")


def delete_vpc(vpc_name_prefix):
    # AWS CLI Profile Name and IAM boto3 client set up and STS client set up
    if args.profile_name:
        AWS_PROFILE_NAME = args.profile_name
        session = boto3.Session(profile_name=AWS_PROFILE_NAME)
        ec2 = session.client("ec2")
    else:
        ec2 = boto3.client("ec2")
    """Finds a VPC with a matching name prefix and force deletes it."""

    # Find matching VPC
    response = ec2.describe_vpcs(
        Filters=[{"Name": "tag:Name", "Values": [f"{vpc_name_prefix}*"]}]
    )

    for vpc in response["Vpcs"]:
        vpc_id = vpc["VpcId"]

        try:
            print(f"Deleting VPC: {vpc_id}")

            # 0. Delete Security Groups
            for sg in ec2.describe_security_groups(
                Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
            )["SecurityGroups"]:
                if sg["GroupName"] != "default":  # Avoid deleting the default SG
                    print(f'Deleting Security Group: {sg["GroupId"]}')
                    ec2.delete_security_group(GroupId=sg["GroupId"])

            # 1. Delete Subnets
            for subnet in ec2.describe_subnets(
                Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
            )["Subnets"]:
                print(f'Deleting Subnet: {subnet["SubnetId"]}')
                ec2.delete_subnet(SubnetId=subnet["SubnetId"])

            # 2. Detach Internet Gateways (if any)
            for igw in ec2.describe_internet_gateways(
                Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
            )["InternetGateways"]:
                ec2.detach_internet_gateway(
                    InternetGatewayId=igw["InternetGatewayId"], VpcId=vpc_id
                )
                print(f'Deleting IGW: {igw["InternetGatewayId"]}')
                ec2.delete_internet_gateway(InternetGatewayId=igw["InternetGatewayId"])

            # 3. Delete VPC
            ec2.delete_vpc(VpcId=vpc_id)
            print("VPC deleted successfully")

        except Exception as e:
            print(f"Failed to delete VPC {vpc_id}: {e}")


if __name__ == "__main__":
    delete_ingress(alb_name_prefix="k8s-game2048")
    delete_iam_resources()
    delete_vpc(vpc_name_prefix="eksctl-test-cluster")
