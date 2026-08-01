"""Unit tests for AltaStataFunctions S3 / boto3 helper surface.

These tests do not boot a real JVM. They mock out:
  * AltaStataFunctions instance construction (via ``__new__`` + manual field
    assignment), so we do not depend on a running altastata-services process,
  * ``grpc_client.issue_s3_credentials`` (gRPC IssueCredentials),
  * and ``boto3.client`` (so ``boto3`` does not need to be installed for the
    test suite).

They exercise the public surface of s3_credentials(), boto3_s3(),
install_aws_env(), and the underlying _resolve_s3_endpoint() /
_read_bootstrap_material() helpers.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from altastata.altastata_functions import AltaStataFunctions
from altastata.s3_bridge import _parse_user_name_from_properties


def _make_instance(transport: str = "grpc") -> AltaStataFunctions:
    """Build an AltaStataFunctions without touching any real JVM / gRPC.

    We bypass __init__ and only care about the helper surface in unit tests.
    """
    inst = AltaStataFunctions.__new__(AltaStataFunctions)
    inst.transport = transport
    inst.gateway = None
    inst.altastata_file_system = None
    inst.grpc_client = MagicMock()
    inst.grpc_client.endpoint.host = "127.0.0.1"
    inst.grpc_client.issue_s3_credentials.return_value = {
        "access_key_id": "AKIAFAKE",
        "secret_access_key": "SECRETFAKE",
    }
    inst._event_listeners = []
    inst._account_dir_path = None
    inst._user_properties = None
    inst._private_key_encrypted = None
    inst._cached_password = None
    inst._s3_credentials_cache = {}
    return inst


class ParseUserNameTests(unittest.TestCase):
    def test_picks_myuser_line(self):
        self.assertEqual(
            "bob123",
            _parse_user_name_from_properties(
                "region=us-east-1\nmyuser=bob123\naccounttype=amazon\n"
            ),
        )

    def test_strips_whitespace(self):
        self.assertEqual(
            "alice",
            _parse_user_name_from_properties("myuser=  alice  \n"),
        )

    def test_ignores_commented_line(self):
        with self.assertRaises(ValueError):
            _parse_user_name_from_properties("# myuser=ghost\nfoo=bar\n")

    def test_missing_raises(self):
        with self.assertRaises(ValueError):
            _parse_user_name_from_properties("region=us-east-1\n")

    def test_empty_value_raises(self):
        with self.assertRaises(ValueError):
            _parse_user_name_from_properties("myuser=\n")

    def test_rejects_path_traversal_myuser(self):
        with self.assertRaises(ValueError):
            _parse_user_name_from_properties("myuser=bob/../../admin\n")


class ResolveS3EndpointTests(unittest.TestCase):
    def test_default_endpoint_falls_back_to_loopback(self):
        inst = _make_instance("grpc")
        inst.grpc_client = None
        self.assertEqual("http://127.0.0.1:9876", inst._resolve_s3_endpoint())

    def test_follows_grpc_host(self):
        inst = _make_instance("grpc")
        inst.grpc_client.endpoint.host = "altastata.internal"
        self.assertEqual("http://altastata.internal:9876", inst._resolve_s3_endpoint())


class S3CredentialsTests(unittest.TestCase):
    def test_returns_boto3_kwargs_via_issue_credentials(self):
        inst = _make_instance("grpc")
        creds = inst.s3_credentials()
        self.assertEqual(
            {
                "endpoint_url": "http://127.0.0.1:9876",
                "aws_access_key_id": "AKIAFAKE",
                "aws_secret_access_key": "SECRETFAKE",
                "region_name": "us-east-1",
            },
            creds,
        )
        inst.grpc_client.issue_s3_credentials.assert_called_once_with(label="python-sdk")

    def test_caches_result_per_endpoint(self):
        inst = _make_instance("grpc")
        inst.s3_credentials()
        inst.s3_credentials()
        self.assertEqual(1, inst.grpc_client.issue_s3_credentials.call_count)

    def test_explicit_endpoint_override(self):
        inst = _make_instance("grpc")
        with patch.dict(os.environ, {"ALTASTATA_ALLOW_INSECURE_REMOTE": "1"}):
            creds = inst.s3_credentials(endpoint="http://altastata.example:19876/")
        self.assertEqual("http://altastata.example:19876", creds["endpoint_url"])

    def test_refuses_cleartext_remote_endpoint(self):
        inst = _make_instance("grpc")
        with patch.dict(os.environ, {"ALTASTATA_ALLOW_INSECURE_REMOTE": ""}, clear=False):
            os.environ.pop("ALTASTATA_ALLOW_INSECURE_REMOTE", None)
            with self.assertRaises(ValueError):
                inst.s3_credentials(endpoint="http://altastata.example:19876")

    def test_requires_grpc_client(self):
        inst = _make_instance("grpc")
        inst.grpc_client = None
        with self.assertRaises(RuntimeError):
            inst.s3_credentials()

    def test_password_kwarg_warns_and_is_ignored(self):
        inst = _make_instance("grpc")
        with self.assertWarns(DeprecationWarning):
            creds = inst.s3_credentials(password="ignored")
        self.assertEqual("AKIAFAKE", creds["aws_access_key_id"])

    def test_grpc_mode_default_endpoint_follows_grpc_host(self):
        inst = _make_instance("grpc")
        inst.grpc_client.endpoint.host = "altastata.internal"
        with patch.dict(os.environ, {"ALTASTATA_ALLOW_INSECURE_REMOTE": "1"}):
            creds = inst.s3_credentials()
        self.assertEqual("http://altastata.internal:9876", creds["endpoint_url"])


class Boto3ClientTests(unittest.TestCase):
    def test_boto3_s3_passes_creds_and_overrides(self):
        fake_boto3 = MagicMock()
        fake_boto3.client.return_value = "<s3-client>"
        with patch.dict(sys.modules, {"boto3": fake_boto3}):
            inst = _make_instance("grpc")
            client = inst.boto3_s3(verify=False)

        self.assertEqual("<s3-client>", client)
        fake_boto3.client.assert_called_once()
        call_args, call_kwargs = fake_boto3.client.call_args
        self.assertEqual(("s3",), call_args)
        self.assertEqual("http://127.0.0.1:9876", call_kwargs["endpoint_url"])
        self.assertEqual("AKIAFAKE", call_kwargs["aws_access_key_id"])
        self.assertEqual("SECRETFAKE", call_kwargs["aws_secret_access_key"])
        self.assertIs(False, call_kwargs["verify"])

    def test_boto3_s3_missing_dependency_raises_importerror(self):
        inst = _make_instance("grpc")
        prev = sys.modules.get("boto3", None)
        sys.modules["boto3"] = None
        try:
            with self.assertRaises(ImportError):
                inst.boto3_s3()
        finally:
            if prev is not None:
                sys.modules["boto3"] = prev
            else:
                del sys.modules["boto3"]


class InstallAwsEnvTests(unittest.TestCase):
    def test_install_aws_env_populates_environ(self):
        inst = _make_instance("grpc")
        captured = {
            k: os.environ.get(k)
            for k in (
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_DEFAULT_REGION",
                "AWS_ENDPOINT_URL_S3",
            )
        }
        try:
            aws_env = inst.install_aws_env()
            self.assertEqual("AKIAFAKE", os.environ["AWS_ACCESS_KEY_ID"])
            self.assertEqual("SECRETFAKE", os.environ["AWS_SECRET_ACCESS_KEY"])
            self.assertEqual("us-east-1", os.environ["AWS_DEFAULT_REGION"])
            self.assertEqual("http://127.0.0.1:9876", os.environ["AWS_ENDPOINT_URL_S3"])
            self.assertEqual("AKIAFAKE", aws_env["AWS_ACCESS_KEY_ID"])
        finally:
            for k, v in captured.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class SetPasswordCachesTests(unittest.TestCase):
    @patch("altastata.altastata_functions.AltaStataGrpcClient")
    def test_set_password_caches_value(self, mock_grpc_cls):
        mock_client = MagicMock()
        mock_grpc_cls.from_upload.return_value = mock_client

        f = AltaStataFunctions.from_credentials(
            "myuser=bob\n",
            "PK",
        )
        self.assertIsNone(f._cached_password)
        f.set_password("hunter2")
        self.assertEqual("hunter2", f._cached_password)


if __name__ == "__main__":
    unittest.main()
