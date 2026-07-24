"""
Launch the bundled AltaStata services jar as an MCP stdio server.

Claude Desktop / specialized agents / IDEs spawn this as a child process and talk JSON-RPC on
stdin/stdout. That is separate from the gRPC gateway your notebooks already
start on :9877 — Desktop agents own the child's stdio, so MCP cannot reuse
that daemon. Same jar, different entry flag (``--mcp-stdio``).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from typing import List, Optional

from .java_runtime import find_bundled_grpc_uber_jar, resolve_java_memory_opts


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="altastata mcp",
        description=(
            "Run the bundled altastata-services jar as an MCP stdio server "
            "(Claude Desktop / specialized agents / IDEs)."
        ),
    )
    parser.add_argument(
        "--account-dir",
        default=os.environ.get("ALTASTATA_MCP_ACCOUNT_DIR"),
        help="Account directory (sets ALTASTATA_MCP_ACCOUNT_DIR)",
    )
    parser.add_argument(
        "--password-env",
        default=None,
        help="Env var holding the unlock password (copied to ALTASTATA_MCP_PASSWORD)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the java command and exit",
    )
    args = parser.parse_args(argv)

    jar = find_bundled_grpc_uber_jar()
    if not jar:
        print(
            "Bundled altastata-services-*-uber.jar not found under altastata/lib/. "
            "Rebuild with scripts/build-bundled-artifacts.sh or install a release wheel.",
            file=sys.stderr,
        )
        return 1

    java = shutil.which("java")
    if not java:
        print("java not found on PATH", file=sys.stderr)
        return 1

    env = os.environ.copy()
    if args.account_dir:
        env["ALTASTATA_MCP_ACCOUNT_DIR"] = os.path.expanduser(args.account_dir)
    if args.password_env:
        value = os.environ.get(args.password_env)
        if value is None:
            print(f"environment variable {args.password_env!r} is not set", file=sys.stderr)
            return 1
        env["ALTASTATA_MCP_PASSWORD"] = value

    command = [java, *resolve_java_memory_opts(), "-jar", jar, "--mcp-stdio"]
    if args.dry_run:
        print("command:", " ".join(command))
        if env.get("ALTASTATA_MCP_ACCOUNT_DIR"):
            print("ALTASTATA_MCP_ACCOUNT_DIR=", env["ALTASTATA_MCP_ACCOUNT_DIR"], sep="")
        return 0

    # Replace this process so stdin/stdout stay the MCP JSON-RPC wire.
    os.execvpe(java, command, env)
    return 1  # unreachable


if __name__ == "__main__":
    sys.exit(main())
