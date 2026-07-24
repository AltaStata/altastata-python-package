import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class AccountSetupTests(unittest.TestCase):
    def setUp(self):
        pkg = types.ModuleType("altastata.grpc.v1")
        grpc_pkg = types.ModuleType("altastata.grpc")
        account_setup_pb2 = types.ModuleType("account_setup_pb2")
        account_setup_pb2_grpc = types.ModuleType("account_setup_pb2_grpc")

        account_setup_pb2.RSA = 1
        account_setup_pb2.PQC = 2
        account_setup_pb2.HPCS = 3

        class GenerateKeysRequest:
            def __init__(self, account_type=0, password=""):
                self.account_type = account_type
                self.password = password
                self.suggested_display_name = ""

        account_setup_pb2.GetSupportedAccountTypesRequest = MagicMock
        account_setup_pb2.GenerateKeysRequest = GenerateKeysRequest

        class Stub:
            def __init__(self, channel):
                self.channel = channel
                self.GetSupportedAccountTypes = MagicMock(
                    return_value=types.SimpleNamespace(account_types=[1, 2, 3])
                )
                self.GenerateKeys = MagicMock(
                    return_value=types.SimpleNamespace(
                        suggested_display_name="rsa.test",
                        account_files={
                            "private.key": b"priv",
                            "public.key": b"pub",
                        },
                    )
                )

        account_setup_pb2_grpc.AccountSetupServiceStub = Stub

        sys.modules["altastata.grpc"] = grpc_pkg
        sys.modules["altastata.grpc.v1"] = pkg
        sys.modules["altastata.grpc.v1.account_setup_pb2"] = account_setup_pb2
        sys.modules["altastata.grpc.v1.account_setup_pb2_grpc"] = account_setup_pb2_grpc

    def tearDown(self):
        for name in list(sys.modules.keys()):
            if name.startswith("altastata.grpc"):
                sys.modules.pop(name, None)

    @patch("altastata.grpc_client.AltaStataGrpcClient._create_channel", return_value=object())
    def test_generate_keys_writes_files(self, _mock_channel):
        from altastata.account_setup import AccountSetupClient

        client = AccountSetupClient()
        result = client.generate_keys(
            "rsa", password="secret", suggested_display_name="rsa.test"
        )
        self.assertEqual("rsa.test", result.suggested_display_name)
        self.assertEqual(b"priv", result.account_files["private.key"])

        with tempfile.TemporaryDirectory() as tmp:
            out = result.write_to(tmp)
            self.assertEqual(b"priv", (Path(out) / "private.key").read_bytes())
            self.assertEqual(b"pub", (Path(out) / "public.key").read_bytes())

    def test_write_to_rejects_path_traversal(self):
        from altastata.account_setup import GenerateKeysResult

        result = GenerateKeysResult(
            suggested_display_name="x",
            account_files={"../evil.key": b"nope"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                result.write_to(tmp)

    def test_cli_account_create_help(self):
        from altastata.cli import main

        with self.assertRaises(SystemExit) as cm:
            main(["account", "create", "--help"])
        self.assertEqual(0, cm.exception.code)

    def test_cli_account_change_password_help(self):
        from altastata.cli import main

        with self.assertRaises(SystemExit) as cm:
            main(["account", "change-password", "--help"])
        self.assertEqual(0, cm.exception.code)

    @patch("altastata.cli.create_account")
    def test_cli_account_create_invokes_sdk(self, mock_create):
        from altastata.account_setup import GenerateKeysResult
        from altastata.cli import main

        mock_create.return_value = GenerateKeysResult(
            suggested_display_name="rsa.alice",
            account_files={"private.key": b"a", "public.key": b"b"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            code = main(
                [
                    "account",
                    "create",
                    "--type",
                    "rsa",
                    "--password",
                    "secret",
                    "--out",
                    tmp,
                    "--name",
                    "rsa.alice",
                    "--no-auto-start",
                ]
            )
        self.assertEqual(0, code)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args.kwargs
        self.assertEqual("secret", kwargs["password"])
        self.assertEqual("rsa.alice", kwargs["name"])

    @patch("altastata.cli.change_account_password")
    def test_cli_account_change_password_invokes_sdk(self, mock_change):
        from pathlib import Path

        from altastata.account_setup import ChangePasswordResult
        from altastata.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            mock_change.return_value = ChangePasswordResult(
                account_dir=Path(tmp),
                account_files={"private.key": b"reenc"},
            )
            code = main(
                [
                    "account",
                    "change-password",
                    "--account-dir",
                    tmp,
                    "--current-password",
                    "old",
                    "--new-password",
                    "new",
                    "--no-auto-start",
                ]
            )
        self.assertEqual(0, code)
        mock_change.assert_called_once()
        kwargs = mock_change.call_args.kwargs
        self.assertEqual("old", kwargs["current_password"])
        self.assertEqual("new", kwargs["new_password"])


if __name__ == "__main__":
    unittest.main()
