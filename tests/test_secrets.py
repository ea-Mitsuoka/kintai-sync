from unittest.mock import MagicMock, patch
import os
from src.secrets import get_secret, get_jobcan_password


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_secret_from_gcp(mock_client_class):
    mock_client = MagicMock()
    mock_client.access_secret_version.return_value.payload.data.decode.return_value = (
        "my-secret-val"
    )
    mock_client_class.return_value = mock_client

    with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"}):
        val = get_secret("MY_SECRET")
        assert val == "my-secret-val"


def test_get_secret_fallback_to_env():
    with patch.dict(os.environ, {"MY_SECRET": "env-val"}, clear=True):
        # Ensure GOOGLE_CLOUD_PROJECT is not set
        val = get_secret("MY_SECRET")
        assert val == "env-val"


@patch("src.secrets.get_secret")
def test_get_jobcan_password(mock_get_secret):
    mock_get_secret.return_value = "pass123"
    val = get_jobcan_password("S-001")
    mock_get_secret.assert_called_with("JOBCAN_PASSWORD_S_001")
    assert val == "pass123"
