import argparse
import boto3
import json
import os
import re

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
else:
    iam = boto3.client("iam")
    sts = boto3.client("sts")


def update_load_balancer_manifest():
    # Get the Account ID
    ACCOUNT_ID = sts.get_caller_identity()["Account"]
    print(f"Using the following AWS Account: {ACCOUNT_ID}")

    # Regular expression to match the ACCOUNT_ID line
    # within the m04-01-cluster-config.yaml file
    pattern = r"(ACCOUNT_ID)"

    # File path for cluster load balancer controller service account config
    # used to replace the value with the new role ARN
    template_file_path = "./aws-load-balancer-controller-service-account-template.yaml"
    final_file_path = "./2-aws-load-balancer-controller-service-account.yaml"

    # Open the original file, read, edit, and save to the final file
    with open(template_file_path, "r") as file, open(
        final_file_path, "w"
    ) as final_file:
        content = file.read()
        new_content = re.sub(pattern, ACCOUNT_ID, content)
        final_file.write(new_content)


def get_oidc_info():
    # Scanning for OIDC ARN
    oidc_provider_pattern = re.compile(
        r"arn:aws:iam::\d{12}:oidc-provider/oidc\.eks\.us-east-1\.amazonaws\.com/id/[A-F0-9]{5,}"
    )

    # Get list of OIDC providers
    response = iam.list_open_id_connect_providers()
    providers = response["OpenIDConnectProviderList"]

    # Search for matching providers
    matching_providers = []
    for provider in providers:
        arn = provider["Arn"]
        if oidc_provider_pattern.match(arn):
            matching_providers.append(arn)

    # Set results
    oidc_arn = ""
    oidc_condition_string = ""
    if matching_providers:
        print(f"Matching OIDC Providers: {matching_providers[0]}")
        oidc_arn = matching_providers[0]
        oidc_condition_string = oidc_arn.split(":")[5].split("/", maxsplit=1)[1]
        return oidc_arn, oidc_condition_string
    else:
        print(
            "No matching OIDC Providers found. Have you created one using the cluster config files?"
        )
        return oidc_arn, oidc_condition_string


def create_iam_role(oidc_arn, oidc_condition_string):
    # JSON templates for the policy and trust policy
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["iam:CreateServiceLinkedRole"],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"
                    }
                },
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeAccountAttributes",
                    "ec2:DescribeAddresses",
                    "ec2:DescribeAvailabilityZones",
                    "ec2:DescribeInternetGateways",
                    "ec2:DescribeVpcs",
                    "ec2:DescribeVpcPeeringConnections",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeInstances",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DescribeTags",
                    "ec2:GetCoipPoolUsage",
                    "ec2:DescribeCoipPools",
                    "elasticloadbalancing:DescribeLoadBalancers",
                    "elasticloadbalancing:DescribeLoadBalancerAttributes",
                    "elasticloadbalancing:DescribeListeners",
                    "elasticloadbalancing:DescribeListenerCertificates",
                    "elasticloadbalancing:DescribeSSLPolicies",
                    "elasticloadbalancing:DescribeRules",
                    "elasticloadbalancing:DescribeTargetGroups",
                    "elasticloadbalancing:DescribeTargetGroupAttributes",
                    "elasticloadbalancing:DescribeTargetHealth",
                    "elasticloadbalancing:DescribeTags",
                ],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cognito-idp:DescribeUserPoolClient",
                    "acm:ListCertificates",
                    "acm:DescribeCertificate",
                    "iam:ListServerCertificates",
                    "iam:GetServerCertificate",
                    "waf-regional:GetWebACL",
                    "waf-regional:GetWebACLForResource",
                    "waf-regional:AssociateWebACL",
                    "waf-regional:DisassociateWebACL",
                    "wafv2:GetWebACL",
                    "wafv2:GetWebACLForResource",
                    "wafv2:AssociateWebACL",
                    "wafv2:DisassociateWebACL",
                    "shield:GetSubscriptionState",
                    "shield:DescribeProtection",
                    "shield:CreateProtection",
                    "shield:DeleteProtection",
                ],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:RevokeSecurityGroupIngress",
                ],
                "Resource": "*",
            },
            {"Effect": "Allow", "Action": ["ec2:CreateSecurityGroup"], "Resource": "*"},
            {
                "Effect": "Allow",
                "Action": ["ec2:CreateTags"],
                "Resource": "arn:aws:ec2:*:*:security-group/*",
                "Condition": {
                    "StringEquals": {"ec2:CreateAction": "CreateSecurityGroup"},
                    "Null": {"aws:RequestTag/elbv2.k8s.aws/cluster": "false"},
                },
            },
            {
                "Effect": "Allow",
                "Action": ["ec2:CreateTags", "ec2:DeleteTags"],
                "Resource": "arn:aws:ec2:*:*:security-group/*",
                "Condition": {
                    "Null": {
                        "aws:RequestTag/elbv2.k8s.aws/cluster": "true",
                        "aws:ResourceTag/elbv2.k8s.aws/cluster": "false",
                    }
                },
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:RevokeSecurityGroupIngress",
                    "ec2:DeleteSecurityGroup",
                ],
                "Resource": "*",
                "Condition": {
                    "Null": {"aws:ResourceTag/elbv2.k8s.aws/cluster": "false"}
                },
            },
            {
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:CreateLoadBalancer",
                    "elasticloadbalancing:CreateTargetGroup",
                ],
                "Resource": "*",
                "Condition": {
                    "Null": {"aws:RequestTag/elbv2.k8s.aws/cluster": "false"}
                },
            },
            {
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:CreateListener",
                    "elasticloadbalancing:DeleteListener",
                    "elasticloadbalancing:CreateRule",
                    "elasticloadbalancing:DeleteRule",
                ],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:AddTags",
                    "elasticloadbalancing:RemoveTags",
                ],
                "Resource": [
                    "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
                    "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
                    "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*",
                ],
                "Condition": {
                    "Null": {
                        "aws:RequestTag/elbv2.k8s.aws/cluster": "true",
                        "aws:ResourceTag/elbv2.k8s.aws/cluster": "false",
                    }
                },
            },
            {
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:AddTags",
                    "elasticloadbalancing:RemoveTags",
                ],
                "Resource": [
                    "arn:aws:elasticloadbalancing:*:*:listener/net/*/*/*",
                    "arn:aws:elasticloadbalancing:*:*:listener/app/*/*/*",
                    "arn:aws:elasticloadbalancing:*:*:listener-rule/net/*/*/*",
                    "arn:aws:elasticloadbalancing:*:*:listener-rule/app/*/*/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:ModifyLoadBalancerAttributes",
                    "elasticloadbalancing:SetIpAddressType",
                    "elasticloadbalancing:SetSecurityGroups",
                    "elasticloadbalancing:SetSubnets",
                    "elasticloadbalancing:DeleteLoadBalancer",
                    "elasticloadbalancing:ModifyTargetGroup",
                    "elasticloadbalancing:ModifyTargetGroupAttributes",
                    "elasticloadbalancing:DeleteTargetGroup",
                ],
                "Resource": "*",
                "Condition": {
                    "Null": {"aws:ResourceTag/elbv2.k8s.aws/cluster": "false"}
                },
            },
            {
                "Effect": "Allow",
                "Action": ["elasticloadbalancing:AddTags"],
                "Resource": [
                    "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
                    "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
                    "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*",
                ],
                "Condition": {
                    "StringEquals": {
                        "elasticloadbalancing:CreateAction": [
                            "CreateTargetGroup",
                            "CreateLoadBalancer",
                        ]
                    },
                    "Null": {"aws:RequestTag/elbv2.k8s.aws/cluster": "false"},
                },
            },
            {
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:RegisterTargets",
                    "elasticloadbalancing:DeregisterTargets",
                ],
                "Resource": "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:SetWebAcl",
                    "elasticloadbalancing:ModifyListener",
                    "elasticloadbalancing:AddListenerCertificates",
                    "elasticloadbalancing:RemoveListenerCertificates",
                    "elasticloadbalancing:ModifyRule",
                ],
                "Resource": "*",
            },
        ],
    }

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Federated": oidc_arn, "Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        f"{oidc_condition_string}:aud": "sts.amazonaws.com",
                        f"{oidc_condition_string}:sub": "system:serviceaccount:kube-system:aws-load-balancer-controller",
                    }
                },
            }
        ],
    }

    # Create the policy
    policy_response = iam.create_policy(
        PolicyName="AWSLoadBalancerControllerIAMPolicy",
        PolicyDocument=json.dumps(policy_document),
        Path="/eks/",
    )
    policy_arn = policy_response["Policy"]["Arn"]

    # Create the role
    role_response = iam.create_role(
        RoleName="AmazonEKSLoadBalancerControllerRole",
        AssumeRolePolicyDocument=json.dumps(trust_policy),
    )
    role_arn = role_response["Role"]["Arn"]

    # Attach the policy to the role
    iam.attach_role_policy(
        RoleName="AmazonEKSLoadBalancerControllerRole", PolicyArn=policy_arn
    )
    print(f"New IAM Policy ARN: {policy_arn}")
    print(f"New IAM Role ARN: {role_arn}")


def update_oidc_thumprint(oidc_arn):
    """Takes in the OIDC ARN used for the EKS authentication and authorization, and then adds a thumbprint to it.
    Helps support thumbprint errors that can occur when using the default eksctl cluster creation.
    """

    # Getting current thumbprint list
    oidc_provider = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=oidc_arn)
    thumbprint_list = oidc_provider["ThumbprintList"]

    # Could set this as an argument at some point
    # Appending this to existing thumbprint list
    new_thumbprint = ["9E99A48A9960B14926BB7F3B02E22DA2B0AB7280"]
    thumbprint_list.append(new_thumbprint[0])

    # Updating the thumbprint list to include the new and old values
    iam.update_open_id_connect_provider_thumbprint(
        OpenIDConnectProviderArn=oidc_arn, ThumbprintList=thumbprint_list
    )


def main():
    update_load_balancer_manifest()
    oidc_info = get_oidc_info()
    create_iam_role(oidc_arn=oidc_info[0], oidc_condition_string=oidc_info[1])
    update_oidc_thumprint(oidc_arn=oidc_info[0])


if __name__ == "__main__":
    main()
