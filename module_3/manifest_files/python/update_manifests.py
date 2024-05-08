import argparse
import boto3
import re
import os

# Argument parsing
parser = argparse.ArgumentParser(
    # description="Create IAM role and policy for EKS Load Balancer using the provided AWS Account ID and OIDC ARN."
    description="Create IAM role and policy for EKS Load Balancer using the provided OIDC ARN."
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
    ec2 = session.client("ec2")
else:
    try:
        iam = boto3.client("iam")
        sts = boto3.client("sts")
        ec2 = boto3.client("ec2")
    except botocore.exceptions.NoCredentialsError as e:
        print(
            f"It looks like we could not find any AWS credentials. Did you forget to set the profile flag using '-p'?"
        )

# Get the Account ID
ACCOUNT_ID = sts.get_caller_identity()["Account"]
print(f"Using the following AWS Account: {ACCOUNT_ID}")


def update_load_balancer_manifest():
    # Filter for the VPC by name
    # Requires the use of the default VPC via the eksctl command and m04-01-cluster-config.yaml file
    filters = [{"Name": "tag:Name", "Values": ["eksctl-test-cluster/VPC"]}]

    # Describe VPCs with the filter
    response = ec2.describe_vpcs(Filters=filters)

    # Print VPC details if found
    vpcs = response.get("Vpcs", [])
    if vpcs:
        vpc = vpcs[0]
        print("Found matching VPC...")
        print(f"VPC ID: {vpc['VpcId']}")
        print(f"VPC CIDR: {vpc['CidrBlock']}")
        vpc_id = vpc["VpcId"]
    else:
        print("VPC with the name 'eksctl-test-cluster/VPC' not found.")

    # Setting pattern for RegEx substitution in manifest file
    pattern = r"(VPC_ID)"

    # File path for load balancer manifest config
    # replaces VPC_ID with new VPC id from cluster_config creation
    template_file_path = "./load-balancer-controller-template.yaml"
    final_file_path = "./4-load-balancer-controller-config.yaml"

    # Open the original file, read, edit, and save to the final file
    with open(template_file_path, "r") as file, open(
        final_file_path, "w"
    ) as final_file:
        content = file.read()
        new_content = re.sub(pattern, vpc_id, content)
        final_file.write(new_content)
        print("Updated manifest file to include newly created VPC.")


def tls_config_manifest():
    dns_record = f"app.{ACCOUNT_ID}.realhandsonlabs.net"
    print(f"Using the following DNS Record: {dns_record}")

    # Setting pattern for RegEx substitution in manifest file
    pattern = r"(DNS_RECORD)"

    # File path for load balancer manifest config
    # replaces VPC_ID with new VPC id from cluster_config creation
    template_file_path = "./tls-ingress-config-template.yaml"
    final_file_path = "./9-tls-ingress-config.yaml"

    # Open the original file, read, edit, and save to the final file
    with open(template_file_path, "r") as file, open(
        final_file_path, "w"
    ) as final_file:
        content = file.read()
        new_content = re.sub(pattern, dns_record, content)
        final_file.write(new_content)
        print("Updated manifest file to include newly created VPC.")


def main():
    update_load_balancer_manifest()
    tls_config_manifest()


if __name__ == "__main__":
    main()
