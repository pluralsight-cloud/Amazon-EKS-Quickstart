import pytest
from unittest.mock import MagicMock, mock_open, patch
import boto3

# Assuming your main code is in a module named create_eks_iam_role
# and the update_load_balancer_manifest function is defined there.

@pytest.fixture
def sts_client():
    # Setup the mock sts client
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
    return mock_sts

@pytest.fixture
def mocked_file_open():
    # Setup the mock open
    return mock_open(read_data="ACCOUNT_ID: old_value")

def test_update_load_balancer_manifest(sts_client, mocked_file_open):
    with patch('boto3.client', return_value=sts_client), \
            patch('builtins.open', mocked_file_open, create=True):
        from create_eks_iam_role import update_load_balancer_manifest
        update_load_balancer_manifest()

        mocked_file_open.assert_called_once_with("./2-aws-load-balancer-controller-service-account.yaml", "w")
        handle = mocked_file_open()
        handle.write.assert_called_once_with("ACCOUNT_ID: 123456789012")