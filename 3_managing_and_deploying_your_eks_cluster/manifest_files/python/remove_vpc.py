import argparse
import boto3

# Argument parsing
parser = argparse.ArgumentParser(
    # description="Create IAM role and policy for EKS Load Balancer using the provided AWS Account ID and OIDC ARN."
    description="Create IAM role and policy for EKS Load Balancer using the provided OIDC ARN."
)
parser.add_argument(
    "-p", "--profile-name", required=False, help="AWS CLI Profile to leverage for creds"
)
args = parser.parse_args()


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
    delete_vpc(vpc_name_prefix="eksctl-test-cluster")
