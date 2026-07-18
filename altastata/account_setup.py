"""
Account setup via gRPC ``AccountSetupService`` (SetupUI / Console parity).

Bootstrap RPCs (no Bearer session required):

- ``GetSupportedAccountTypes``
- ``GenerateKeys`` — RSA / PQC / HPCS key material as ``filename → bytes``

Typical flow after ``generate_keys`` / CLI ``altastata account create``:

1. Send ``public.key`` (or PQC public keys) to your org admin.
2. Admin returns ``*user.properties`` into the same account directory.
3. Login with ``AltaStataGrpcClient.from_account_dir`` / ``AltaStataFunctions``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import grpc

from .grpc_client import (
    GrpcEndpoint,
    _is_port_open,
    _wait_for_port,
)
from .java_runtime import start_local_grpc_service

AccountTypeName = str  # "rsa" | "pqc" | "hpcs"


@dataclass(frozen=True)
class GenerateKeysResult:
    """Result of ``AccountSetupService.GenerateKeys``."""

    suggested_display_name: str
    account_files: Dict[str, bytes]

    def write_to(self, directory: Union[str, Path], *, exist_ok: bool = True) -> Path:
        """
        Write key files into ``directory`` (created if missing).

        Returns the absolute path of the directory.
        """
        out = Path(directory).expanduser().resolve()
        if out.exists() and not out.is_dir():
            raise NotADirectoryError(f"Not a directory: {out}")
        out.mkdir(parents=True, exist_ok=exist_ok)
        for name, data in self.account_files.items():
            # Basenames only — reject path traversal from a hostile gateway.
            basename = Path(name).name
            if not basename or basename != name:
                raise ValueError(f"Refusing to write unsafe account file name: {name!r}")
            (out / basename).write_bytes(data)
        return out


class AccountSetupClient:
    """
    Thin gRPC client for account keygen (no login / session required).

    Local-mode gateways typically allow ``GenerateKeys`` on loopback; see
    ``altastata-grpc/CONSOLE_ACCOUNT_SETUP_DESIGN.md``.
    """

    def __init__(
        self,
        endpoint: GrpcEndpoint = GrpcEndpoint(),
        *,
        channel: Optional[grpc.Channel] = None,
        owns_channel: bool = True,
    ):
        self.endpoint = endpoint
        self._owns_channel = owns_channel if channel is None else owns_channel
        if channel is None:
            from .grpc_client import AltaStataGrpcClient

            channel = AltaStataGrpcClient._create_channel(endpoint)
        self._channel = channel
        self._server_process = None

        try:
            from .grpc.v1 import account_setup_pb2, account_setup_pb2_grpc
        except Exception as exc:
            raise ImportError(
                "gRPC stubs are missing. Run: python scripts/generate_grpc_stubs.py"
            ) from exc

        self._pb2 = account_setup_pb2
        self._stub = account_setup_pb2_grpc.AccountSetupServiceStub(self._channel)

    @classmethod
    def connect(
        cls,
        endpoint: GrpcEndpoint = GrpcEndpoint(),
        *,
        auto_start_server: bool = True,
        grpc_server_command: Optional[Sequence[str]] = None,
        grpc_server_working_dir: Optional[str] = None,
        start_timeout_s: int = 45,
    ) -> "AccountSetupClient":
        """Open a client; optionally start the local gateway if the port is closed."""
        started = None
        if (
            not endpoint.socket_path
            and not _is_port_open(endpoint.host, endpoint.port)
            and auto_start_server
        ):
            started = start_local_grpc_service(
                grpc_server_command=grpc_server_command,
                working_dir=grpc_server_working_dir,
            )
            _wait_for_port(endpoint.host, endpoint.port, timeout_s=start_timeout_s)

        client = cls(endpoint=endpoint)
        client._server_process = started
        return client

    def close(self) -> None:
        if self._owns_channel:
            self._channel.close()
        if self._server_process is not None:
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=5)
            except Exception:
                pass
            self._server_process = None

    def __enter__(self) -> "AccountSetupClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def get_supported_account_types(self, *, timeout_s: float = 30.0) -> List[str]:
        """Return supported types as lower-case names: ``rsa``, ``pqc``, ``hpcs``."""
        resp = self._stub.GetSupportedAccountTypes(
            self._pb2.GetSupportedAccountTypesRequest(),
            timeout=timeout_s,
        )
        return [_account_type_to_name(t) for t in resp.account_types]

    def generate_keys(
        self,
        account_type: AccountTypeName,
        *,
        password: str = "",
        suggested_display_name: Optional[str] = None,
        timeout_s: float = 120.0,
    ) -> GenerateKeysResult:
        """
        Generate RSA / PQC / HPCS key material on the gateway.

        RSA and PQC require a non-empty ``password`` (encrypts private keys).
        HPCS typically uses an empty password and GREP11 yaml on the gateway.
        """
        pb_type = _account_type_from_name(account_type, self._pb2)
        if pb_type in (self._pb2.RSA, self._pb2.PQC) and not password:
            raise ValueError(f"password is required for account type {account_type!r}")

        req = self._pb2.GenerateKeysRequest(
            account_type=pb_type,
            password=password or "",
        )
        if suggested_display_name:
            req.suggested_display_name = suggested_display_name

        resp = self._stub.GenerateKeys(req, timeout=timeout_s)
        files = {name: bytes(data) for name, data in resp.account_files.items()}
        return GenerateKeysResult(
            suggested_display_name=resp.suggested_display_name,
            account_files=files,
        )


def create_account(
    account_type: AccountTypeName,
    out_dir: Union[str, Path],
    *,
    password: str = "",
    name: Optional[str] = None,
    endpoint: GrpcEndpoint = GrpcEndpoint(),
    auto_start_server: bool = True,
    grpc_server_command: Optional[Sequence[str]] = None,
    grpc_server_working_dir: Optional[str] = None,
) -> GenerateKeysResult:
    """
    Generate keys and write them under ``out_dir``.

    Convenience wrapper used by the CLI and SDK callers who want a one-shot
    create without managing the client lifecycle.
    """
    with AccountSetupClient.connect(
        endpoint=endpoint,
        auto_start_server=auto_start_server,
        grpc_server_command=grpc_server_command,
        grpc_server_working_dir=grpc_server_working_dir,
    ) as client:
        result = client.generate_keys(
            account_type,
            password=password,
            suggested_display_name=name,
        )
        result.write_to(out_dir)
        return result


def _account_type_from_name(name: AccountTypeName, pb2) -> int:
    key = (name or "").strip().lower()
    mapping = {
        "rsa": pb2.RSA,
        "pqc": pb2.PQC,
        "hpcs": pb2.HPCS,
    }
    if key not in mapping:
        raise ValueError(
            f"Unknown account type {name!r}; expected one of: rsa, pqc, hpcs"
        )
    return mapping[key]


def _account_type_to_name(value: int) -> str:
    # Enum values: UNSPECIFIED=0, RSA=1, PQC=2, HPCS=3
    mapping = {1: "rsa", 2: "pqc", 3: "hpcs"}
    name = mapping.get(int(value))
    if name is None:
        raise ValueError(f"Unsupported AccountType enum value: {value}")
    return name
