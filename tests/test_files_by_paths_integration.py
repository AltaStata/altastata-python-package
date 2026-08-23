"""Optional integration test for batch delete/share/revoke by explicit paths.

Requires a configured account and the bundled altastata-services uber jar built
from the matching mycloud branch (see scripts/build-bundled-artifacts.sh).

Run manually:

    ALTASTATA_ACCOUNT_DIR=$HOME/.altastata/accounts/amazon.rsa.bob123 \\
    ALTASTATA_PASSWORD=your_password \\
    ALTASTATA_GRPC_PORT=9888 \\
        python3 -m unittest tests.test_files_by_paths_integration

Use a non-default ``ALTASTATA_GRPC_PORT`` when :9877 is already taken (e.g. Docker).
The client auto-starts the bundled gateway on that port via ``GRPCGATEWAY_PORT``.
"""

import os
import time
import unittest
import uuid

from altastata import AltaStataFunctions
from altastata.grpc_client import GrpcEndpoint


@unittest.skipUnless(
    os.environ.get("ALTASTATA_ACCOUNT_DIR"),
    "set ALTASTATA_ACCOUNT_DIR to run files-by-paths integration test",
)
class FilesByPathsIntegration(unittest.TestCase):
  def setUp(self):
    password = os.environ.get("ALTASTATA_PASSWORD", "123")
    port = int(os.environ.get("ALTASTATA_GRPC_PORT", "9877"))
    self.af = AltaStataFunctions.from_account_dir(
        os.environ["ALTASTATA_ACCOUNT_DIR"],
        password=password,
        grpc_endpoint=GrpcEndpoint(port=port),
    )
    self.prefix = f"BatchPathsTest/{uuid.uuid4().hex}/"
    self.path_a = f"{self.prefix}a.txt"
    self.path_b = f"{self.prefix}b.txt"
    self.af.create_file(self.path_a, b"alpha")
    self.af.create_file(self.path_b, b"beta")

  def tearDown(self):
    try:
      self.af.delete_files_by_paths([self.path_a, self.path_b])
    finally:
      self.af.shutdown()

  def test_share_revoke_delete_by_paths(self):
    share_statuses = self.af.share_paths([self.path_a, self.path_b], ["alice222"])
    self.assertEqual(2, len(share_statuses))
    for row in share_statuses:
      self.assertEqual("DONE", row["operation_state"])

    revoke_statuses = self.af.revoke_paths([self.path_a, self.path_b], ["alice222"])
    self.assertEqual(2, len(revoke_statuses))

    delete_statuses = self.af.delete_files_by_paths([self.path_a, self.path_b])
    self.assertGreaterEqual(len(delete_statuses), 2)
    for row in delete_statuses:
      self.assertEqual("DONE", row["operation_state"])

    time.sleep(1)
    remaining = list(self.af.list_cloud_files_versions(self.prefix, True, None, None))
    self.assertEqual([], remaining)


if __name__ == "__main__":
  unittest.main()
