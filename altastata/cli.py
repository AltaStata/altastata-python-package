"""
AltaStata command-line interface.

Account setup (no Desktop UI required)::

    altastata account create --type rsa --password 'secret' --out ~/.altastata/accounts/amazon.rsa.alice
    altastata account create --type pqc --password 'secret' --out ~/.altastata/accounts/amazon.pqc.bob --name amazon.pqc.bob
    altastata account change-password --account-dir ~/.altastata/accounts/amazon.rsa.alice
    altastata account types
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from typing import List, Optional

from .account_setup import AccountSetupClient, change_account_password, create_account
from .grpc_client import GrpcEndpoint


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="altastata",
        description="AltaStata CLI — account setup and local gateway helpers.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    account = sub.add_parser("account", help="Create and inspect end-user accounts")
    account_sub = account.add_subparsers(dest="account_command", required=True)

    create = account_sub.add_parser(
        "create",
        help="Generate RSA/PQC/HPCS keys via gRPC AccountSetupService (SetupUI parity)",
    )
    create.add_argument(
        "--type",
        dest="account_type",
        required=True,
        choices=("rsa", "pqc", "hpcs"),
        help="Account key type",
    )
    create.add_argument(
        "--out",
        required=True,
        help="Directory to write key files into (created if missing)",
    )
    create.add_argument(
        "--name",
        default=None,
        help="Suggested display name for the account (optional)",
    )
    create.add_argument(
        "--password",
        default=None,
        help="Password to encrypt private keys (RSA/PQC). Prefer --password-env in scripts.",
    )
    create.add_argument(
        "--password-env",
        default=None,
        help="Read password from this environment variable",
    )
    create.add_argument(
        "--host",
        default="127.0.0.1",
        help="gRPC host (default: 127.0.0.1)",
    )
    create.add_argument(
        "--port",
        type=int,
        default=9877,
        help="gRPC port (default: 9877)",
    )
    create.add_argument(
        "--no-auto-start",
        action="store_true",
        help="Do not auto-start the local gateway if the port is closed",
    )

    change_pw = account_sub.add_parser(
        "change-password",
        help="Re-encrypt private keys under a new password (RSA/PQC; no login)",
    )
    change_pw.add_argument(
        "--account-dir",
        required=True,
        help="Existing account directory containing private key material",
    )
    change_pw.add_argument(
        "--current-password",
        default=None,
        help="Current password. Prefer --current-password-env in scripts.",
    )
    change_pw.add_argument(
        "--current-password-env",
        default=None,
        help="Read current password from this environment variable",
    )
    change_pw.add_argument(
        "--new-password",
        default=None,
        help="New password. Prefer --new-password-env in scripts.",
    )
    change_pw.add_argument(
        "--new-password-env",
        default=None,
        help="Read new password from this environment variable",
    )
    change_pw.add_argument("--host", default="127.0.0.1")
    change_pw.add_argument("--port", type=int, default=9877)
    change_pw.add_argument("--no-auto-start", action="store_true")

    types_cmd = account_sub.add_parser(
        "types",
        help="List account types supported by the gateway",
    )
    types_cmd.add_argument("--host", default="127.0.0.1")
    types_cmd.add_argument("--port", type=int, default=9877)
    types_cmd.add_argument("--no-auto-start", action="store_true")

    server = sub.add_parser(
        "grpc-server",
        help="Start the bundled local gRPC / Console gateway (same as altastata-grpc-server)",
    )
    server.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved startup command and exit",
    )

    mcp = sub.add_parser(
        "mcp",
        help="Run bundled services jar as MCP stdio server (Claude Desktop / specialized agents / IDEs)",
    )
    mcp.add_argument(
        "--account-dir",
        default=None,
        help="Account directory (sets ALTASTATA_MCP_ACCOUNT_DIR)",
    )
    mcp.add_argument(
        "--password-env",
        default=None,
        help="Env var with unlock password (copied to ALTASTATA_MCP_PASSWORD)",
    )
    mcp.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved java command and exit",
    )

    args = parser.parse_args(argv)

    if args.command == "account":
        if args.account_command == "create":
            return _cmd_account_create(args)
        if args.account_command == "change-password":
            return _cmd_account_change_password(args)
        if args.account_command == "types":
            return _cmd_account_types(args)
    if args.command == "grpc-server":
        from .grpc_server import main as grpc_server_main

        return grpc_server_main(["--dry-run"] if args.dry_run else [])
    if args.command == "mcp":
        from .mcp_server import main as mcp_server_main

        mcp_argv = []
        if args.account_dir:
            mcp_argv.extend(["--account-dir", args.account_dir])
        if args.password_env:
            mcp_argv.extend(["--password-env", args.password_env])
        if args.dry_run:
            mcp_argv.append("--dry-run")
        return mcp_server_main(mcp_argv)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _cmd_account_create(args: argparse.Namespace) -> int:
    password = _resolve_password(
        args.password,
        args.password_env,
        required=args.account_type in ("rsa", "pqc"),
        prompt="Account password: ",
    )
    endpoint = GrpcEndpoint(host=args.host, port=args.port, secure=False)
    try:
        result = create_account(
            args.account_type,
            args.out,
            password=password,
            name=args.name,
            endpoint=endpoint,
            auto_start_server=not args.no_auto_start,
        )
    except Exception as exc:
        print(f"account create failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created account keys in {os.path.abspath(args.out)}")
    print(f"Display name: {result.suggested_display_name}")
    print("Files:")
    for name in sorted(result.account_files):
        print(f"  - {name} ({len(result.account_files[name])} bytes)")
    print()
    print("Next: send public key material to your org admin and place the")
    print("returned *user.properties file in the same directory, then:")
    print(f'  AltaStataFunctions.from_account_dir("{os.path.abspath(args.out)}", password=...)')
    return 0


def _cmd_account_change_password(args: argparse.Namespace) -> int:
    current_password = _resolve_password(
        args.current_password,
        args.current_password_env,
        required=True,
        prompt="Current password: ",
    )
    new_password = _resolve_password(
        args.new_password,
        args.new_password_env,
        required=True,
        prompt="New password: ",
    )
    if current_password == new_password:
        print("New password must differ from the current password", file=sys.stderr)
        return 1

    if sys.stdin.isatty() and args.new_password is None and args.new_password_env is None:
        confirm = getpass.getpass("Confirm new password: ")
        if confirm != new_password:
            print("New passwords do not match", file=sys.stderr)
            return 1

    endpoint = GrpcEndpoint(host=args.host, port=args.port, secure=False)
    try:
        result = change_account_password(
            args.account_dir,
            current_password=current_password,
            new_password=new_password,
            endpoint=endpoint,
            auto_start_server=not args.no_auto_start,
        )
    except Exception as exc:
        print(f"account change-password failed: {exc}", file=sys.stderr)
        return 1

    print(f"Password updated for account directory {result.account_dir}")
    print("Updated files:")
    for name in sorted(result.account_files):
        print(f"  - {name} ({len(result.account_files[name])} bytes)")
    print()
    print("Use the new password for subsequent logins.")
    return 0


def _cmd_account_types(args: argparse.Namespace) -> int:
    endpoint = GrpcEndpoint(host=args.host, port=args.port, secure=False)
    try:
        with AccountSetupClient.connect(
            endpoint=endpoint,
            auto_start_server=not args.no_auto_start,
        ) as client:
            types = client.get_supported_account_types()
    except Exception as exc:
        print(f"account types failed: {exc}", file=sys.stderr)
        return 1
    for t in types:
        print(t)
    return 0


def _resolve_password(
    password: Optional[str],
    password_env: Optional[str],
    *,
    required: bool,
    prompt: str = "Account password: ",
) -> str:
    if password is not None and password_env is not None:
        raise SystemExit("Pass only one of --password / --*-password and the matching --*-env flag")
    if password_env:
        value = os.environ.get(password_env)
        if value is None:
            raise SystemExit(f"Environment variable {password_env!r} is not set")
        return value
    if password is not None:
        return password
    if not required:
        return ""
    if sys.stdin.isatty():
        return getpass.getpass(prompt)
    raise SystemExit("password is required (pass a flag or --*-password-env)")


if __name__ == "__main__":
    raise SystemExit(main())
