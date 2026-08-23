"""Unit tests for fsspec share/revoke routing to batch vs prefix APIs."""

import unittest
from unittest.mock import MagicMock

from altastata.fsspec import AltaStataFileSystem


class FsspecShareRevokeRoutingTests(unittest.TestCase):
    def setUp(self):
        self.af = MagicMock()
        self.af.grpc_client = MagicMock()
        self.fs = AltaStataFileSystem(self.af, "bob123")

    def test_share_single_file_uses_share_paths(self):
        self.af.share_paths.return_value = [{"operation_state": "DONE"}]
        self.fs.share("Public/a.txt", ["alice222"], including_subdirectories=False)
        self.af.share_paths.assert_called_once_with(["Public/a.txt"], ["alice222"])
        self.af.share_files.assert_not_called()

    def test_share_prefix_uses_share_files(self):
        self.af.share_files.return_value = [{"operation_state": "DONE"}]
        self.fs.share("Public/dir/", ["alice222"], including_subdirectories=True)
        self.af.share_files.assert_called_once_with(
            "Public/dir/", True, None, None, ["alice222"]
        )
        self.af.share_paths.assert_not_called()

    def test_revoke_single_file_uses_revoke_paths(self):
        self.af.revoke_paths.return_value = [{"operation_state": "DONE"}]
        self.fs.revoke("Public/a.txt", ["alice222"], including_subdirectories=False)
        self.af.revoke_paths.assert_called_once_with(["Public/a.txt"], ["alice222"])
        self.af.revoke_reader_access.assert_not_called()


if __name__ == "__main__":
    unittest.main()
