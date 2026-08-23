import unittest
import warnings
from unittest.mock import MagicMock, patch


class AltaStataFunctionsTransportTests(unittest.TestCase):
    @patch("altastata.altastata_functions.AltaStataGrpcClient")
    def test_from_credentials_uses_grpc_backend(self, mock_grpc_cls):
        mock_client = MagicMock()
        mock_grpc_cls.from_upload.return_value = mock_client

        from altastata.altastata_functions import AltaStataFunctions

        f = AltaStataFunctions.from_credentials(
            "myuser=bob123\nregion=us-east-1\n",
            "-----BEGIN RSA PRIVATE KEY-----\n...\n",
            password="123",
        )

        self.assertEqual("grpc", f.transport)
        self.assertIs(f.grpc_client, mock_client)
        mock_grpc_cls.from_upload.assert_called_once()
        f.set_password("abc")
        mock_client.set_password.assert_called_once_with("abc")

    @patch("altastata.altastata_functions.AltaStataGrpcClient")
    def test_get_file_attribute_delegates_to_grpc(self, mock_grpc_cls):
        mock_client = MagicMock()
        mock_client.get_file_attribute.return_value = "42"
        mock_grpc_cls.from_upload.return_value = mock_client

        from altastata.altastata_functions import AltaStataFunctions

        f = AltaStataFunctions.from_credentials(
            "myuser=bob123\nregion=us-east-1\n",
            "-----BEGIN RSA PRIVATE KEY-----\n...\n",
            password="123",
        )
        value = f.get_file_attribute("a/b.txt", None, "size")
        self.assertEqual("42", value)

    @patch("altastata.altastata_functions.AltaStataGrpcClient")
    def test_delete_files_by_paths_delegates_to_grpc(self, mock_grpc_cls):
        mock_client = MagicMock()
        mock_client.delete_files_by_paths.return_value = [{"operation_state": "DONE"}]
        mock_grpc_cls.from_upload.return_value = mock_client

        from altastata.altastata_functions import AltaStataFunctions

        f = AltaStataFunctions.from_credentials("myuser=bob123\n", "PK", password="123")
        paths = ["Public/a.txt", "Public/b.txt"]
        result = f.delete_files_by_paths(paths)
        self.assertEqual(1, len(result))
        mock_client.delete_files_by_paths.assert_called_once_with(
            paths, time_interval_start=None, time_interval_end=None
        )

    @patch("altastata.altastata_functions.AltaStataGrpcClient")
    def test_share_paths_delegates_to_grpc(self, mock_grpc_cls):
        mock_client = MagicMock()
        mock_client.share.return_value = [{"operation_state": "DONE"}]
        mock_grpc_cls.from_upload.return_value = mock_client

        from altastata.altastata_functions import AltaStataFunctions

        f = AltaStataFunctions.from_credentials("myuser=bob123\n", "PK", password="123")
        paths = ["Public/a.txt", "Public/b.txt"]
        result = f.share_paths(paths, ["alice222"])
        self.assertEqual(1, len(result))
        mock_client.share.assert_called_once_with(paths, ["alice222"])

    @patch("altastata.altastata_functions.AltaStataGrpcClient")
    def test_revoke_paths_delegates_to_grpc(self, mock_grpc_cls):
        mock_client = MagicMock()
        mock_client.revoke.return_value = [{"operation_state": "DONE"}]
        mock_grpc_cls.from_upload.return_value = mock_client

        from altastata.altastata_functions import AltaStataFunctions

        f = AltaStataFunctions.from_credentials("myuser=bob123\n", "PK", password="123")
        paths = ["Public/a.txt", "Public/b.txt"]
        result = f.revoke_paths(paths, ["alice222"])
        self.assertEqual(1, len(result))
        mock_client.revoke.assert_called_once_with(paths, ["alice222"])

    @patch("altastata.altastata_functions.AltaStataGrpcClient")
    def test_legacy_transport_kwarg_warns_and_is_ignored(self, mock_grpc_cls):
        mock_grpc_cls.from_upload.return_value = MagicMock()
        from altastata.altastata_functions import AltaStataFunctions

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            f = AltaStataFunctions.from_credentials(
                "myuser=bob\n",
                "PK",
                transport="grpc",
                password="x",
            )
        self.assertEqual("grpc", f.transport)
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) and "transport=" in str(w.message)
                for w in caught),
            caught,
        )


if __name__ == "__main__":
    unittest.main()
