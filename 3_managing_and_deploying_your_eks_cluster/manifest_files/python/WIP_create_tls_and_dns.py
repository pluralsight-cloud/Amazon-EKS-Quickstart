import boto3
import argparse

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
    route53 = session.client("route53")
    sts = session.client("sts")
    elbv2 = session.client("elbv2")
    acm = session.client("acm")
else:
    try:
        sts = boto3.client("sts")
        route53 = boto3.client("route53")
        elbv2 = boto3.client("elbv2")
        acm = boto3.client("acm")
    except botocore.exceptions.NoCredentialsError as e:
        print(
            f"It looks like we could not find any AWS credentials. Did you forget to set the profile flag using '-p'?"
        )

# 1. Get the current account ID
account_id = sts.get_caller_identity()["Account"]

# 2. Find matching hosted zone
hosted_zones = route53.list_hosted_zones()["HostedZones"]
matching_zone = next(
    (zone for zone in hosted_zones if zone["Name"].startswith(account_id)), None
)

if not matching_zone:
    print("Matching hosted zone not found")
    exit(1)  # Or handle the error differently


# 3. Find matching ALB
albs = elbv2.describe_load_balancers()["LoadBalancers"]
matching_alb = next(
    (alb for alb in albs if alb["LoadBalancerName"].startswith("k8s-game2048")), None
)

if not matching_alb:
    print("Matching load balancer not found")
    exit(1)  # Or handle the error differently

# 4. Create the alias record
r53_response = route53.change_resource_record_sets(
    HostedZoneId=matching_zone["Id"],
    ChangeBatch={
        "Changes": [
            {
                "Action": "CREATE",
                "ResourceRecordSet": {
                    "Name": "app."
                    + matching_zone["Name"],  # Concatenate for full record name
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId": matching_alb["CanonicalHostedZoneId"],
                        "DNSName": matching_alb["DNSName"],
                        "EvaluateTargetHealth": False,
                    },
                },
            }
        ]
    },
)

# 4. Request a new ACM certificate
acm_response = acm.request_certificate(
    DomainName="app." + matching_zone["Name"].removesuffix("."),  # Full record name
    ValidationMethod="DNS",
)
print(acm_response)
certificate_arn = acm_response["CertificateArn"]

# 5. Get DNS validation records from ACM
response = acm.describe_certificate(CertificateArn=certificate_arn)
print(response)
"""
validation_option = response["Certificate"]["DomainValidationOptions"][0]
resource_record = validation_option["ResourceRecord"]

# 6. Create the DNS validation record in Route 53
response = route53.change_resource_record_sets(
    HostedZoneId=matching_zone["Id"],
    ChangeBatch={
        "Changes": [{"Action": "CREATE", "ResourceRecordSet": resource_record}]
    },
)
"""
