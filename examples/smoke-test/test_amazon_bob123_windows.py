"""
Windows smoke test: amazon.rsa.bob123 via pip-installed altastata.

Prerequisites
-------------
1. pip install -U altastata
2. Java 17+ on PATH (java -version)
3. Copy account folder to:
     %USERPROFILE%\\.altastata\\accounts\\amazon.rsa.bob123\\
   (must contain *user.properties, private.key, public.key)
4. Set the account password (PowerShell):
     $env:ALTASTATA_PASSWORD = "your_password"
   cmd.exe:
     set ALTASTATA_PASSWORD=your_password

Run:
    python examples\\smoke-test\\test_amazon_bob123_windows.py
  or copy this file anywhere and:
    python test_amazon_bob123_windows.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from altastata import AltaStataFunctions


def main() -> int:
    account = Path.home() / ".altastata" / "accounts" / "amazon.rsa.bob123"
    password = os.environ.get("ALTASTATA_PASSWORD")
    if not password:
        print(
            "Set ALTASTATA_PASSWORD to the bob123 account password, then re-run.",
            file=sys.stderr,
        )
        return 2

    if not account.is_dir():
        print(f"Account folder not found: {account}", file=sys.stderr)
        print(
            "Copy amazon.rsa.bob123 under %USERPROFILE%\\.altastata\\accounts\\",
            file=sys.stderr,
        )
        return 2

    props = list(account.glob("*.user.properties"))
    if not props or not (account / "private.key").is_file():
        print(
            f"Account folder incomplete (need *user.properties + private.key): {account}",
            file=sys.stderr,
        )
        return 2

    print(f"Account:  {account}")
    print(f"Python:   {sys.version.split()[0]}")
    print("Logging in (gateway auto-starts on 127.0.0.1:9877 if free)...")

    f = AltaStataFunctions.from_account_dir(str(account), password=password)
    try:
        versions = list(f.list_cloud_files_versions("Public/", True, None, None))
        print(f"list Public/: {len(versions)} version row(s)")

        path = "Public/windows-bob123-smoke.txt"
        payload = b"hello from Windows python package smoke test\n"
        status = f.create_file(path, payload)
        print("create:", status)

        data = f.get_buffer(path, None, 0, 4, len(payload))
        text = data.decode("utf-8")
        print("read back:", text.rstrip())
        if data != payload:
            print("FAIL: read-back mismatch", file=sys.stderr)
            return 1

        print("SUCCESS")
        return 0
    finally:
        f.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
