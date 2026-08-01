"""S3 / boto3 bridge for the bundled AltaStata S3 gateway (port 9876).

Credentials are issued over the authenticated gRPC session
(``S3CredentialsService.IssueCredentials``). Legacy HTTP admin PUTs
(``/setUserProperties``, ``/setPrivateKey``, ``/setPassword`` with
``?password=``) were removed from the Java gateway and are no longer used.
"""

from __future__ import annotations

import os
import re
import urllib.parse
import warnings
from typing import Dict, Optional, Tuple

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1"})
_SAFE_MYUSER = re.compile(r"^[A-Za-z0-9._-]+$")


def _parse_user_name_from_properties(text: str) -> str:
    """Extract the ``myuser`` value from a user.properties text blob.

    Mirrors what {@code com.altastata.utils.Account} does on the Java side
    so helpers can derive the same user name that account load would have
    chosen.

    Raises:
        ValueError: if no ``myuser=...`` line is present or the value is unsafe.
    """
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("myuser="):
            value = line.split("=", 1)[1].strip()
            if value:
                if not _SAFE_MYUSER.fullmatch(value):
                    raise ValueError(
                        f"Unsafe myuser value {value!r}: only [A-Za-z0-9._-] allowed"
                    )
                return value
    raise ValueError("user_properties does not contain a non-empty 'myuser=' line")


def _is_loopback_host(host: str) -> bool:
    return (host or "").strip().lower() in _LOOPBACK_HOSTS


def _assert_s3_endpoint_allowed(endpoint: str) -> None:
    """Refuse cleartext S3 admin/data URLs aimed at non-loopback hosts."""
    parsed = urllib.parse.urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").lower()
    if scheme == "https":
        return
    if scheme == "http" and _is_loopback_host(host):
        return
    allow = os.environ.get("ALTASTATA_ALLOW_INSECURE_REMOTE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if allow:
        return
    raise ValueError(
        f"Refusing cleartext S3 endpoint {endpoint!r} for non-loopback host. "
        "Use https://, a loopback URL, or set ALTASTATA_ALLOW_INSECURE_REMOTE=1."
    )


class S3BridgeMixin:
    """Mixin providing :meth:`s3_credentials` / :meth:`boto3_s3` / :meth:`install_aws_env`.

    Expects the host class to populate:

    - ``grpc_client`` (required for credential issuance)
    - ``_s3_credentials_cache``
    - optionally ``_cached_password`` (kept for API compatibility; unused for issue)
    """

    def s3_credentials(
        self,
        *,
        endpoint: Optional[str] = None,
        region: str = "us-east-1",
        label: str = "python-sdk",
        password: Optional[str] = None,
    ) -> Dict[str, str]:
        """Issue and return boto3-ready S3 credentials via gRPC.

        Calls ``S3CredentialsService.IssueCredentials`` on the already
        authenticated session (``LoginV2``), then returns the access/secret
        pair for the co-hosted S3 gateway on port 9876.

        Args:
            endpoint: Base URL of the S3 gateway. Defaults to
                ``http://<grpc-host>:9876`` for loopback gRPC hosts, or
                ``http://127.0.0.1:9876`` when no gRPC client is set.
            region: AWS region for SigV4. The gateway is region-agnostic but
                boto3 still demands a value; ``us-east-1`` is the safe default.
            label: Optional label stored with the issued credential on the
                gateway (visible via ``ListMyCredentials``).
            password: Deprecated / ignored. Credentials come from the Bearer
                session, not an HTTP ``?password=`` bootstrap.

        Returns:
            Dict with keys ``endpoint_url``, ``aws_access_key_id``,
            ``aws_secret_access_key``, ``region_name`` — directly usable as
            ``boto3.client('s3', **result)``.
        """
        if password is not None:
            warnings.warn(
                "password= is ignored for s3_credentials(); credentials come "
                "from the authenticated gRPC session (IssueCredentials). "
                "Remove the argument from your call site.",
                DeprecationWarning,
                stacklevel=2,
            )

        endpoint = (endpoint or self._resolve_s3_endpoint()).rstrip("/")
        _assert_s3_endpoint_allowed(endpoint)

        cached = self._s3_credentials_cache.get(endpoint)
        if cached is not None and cached.get("region_name") == region:
            return dict(cached)

        grpc_client = getattr(self, "grpc_client", None)
        if grpc_client is None:
            raise RuntimeError(
                "s3_credentials() requires a logged-in gRPC client. "
                "Construct AltaStataFunctions via from_account_dir / "
                "from_credentials / from_upload first."
            )

        issued = grpc_client.issue_s3_credentials(label=label)
        access_key = issued.get("access_key_id")
        secret_key = issued.get("secret_access_key")
        if not access_key or not secret_key:
            raise RuntimeError(
                "S3CredentialsService.IssueCredentials did not return "
                f"access_key_id/secret_access_key; response was: {issued}"
            )

        creds = {
            "endpoint_url": endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region,
        }
        self._s3_credentials_cache[endpoint] = dict(creds)
        return creds

    def boto3_s3(self, **overrides):
        """Return a ready-to-use boto3 S3 client.

        Equivalent to::

            boto3.client('s3', **self.s3_credentials(), **overrides)

        Any keyword in ``overrides`` wins over the helper's defaults — use
        this to pass ``config=botocore.config.Config(...)``, override
        ``endpoint_url`` for a remote deployment, etc.

        Requires ``boto3`` to be installed in the environment; raises
        ``ImportError`` with a clear hint otherwise. ``boto3`` is not in
        ``install_requires`` because not every wheel consumer wants the AWS
        SDK on the import path.
        """
        try:
            import boto3
        except ImportError as e:
            raise ImportError(
                "boto3 is required for AltaStataFunctions.boto3_s3(). "
                "Install it with `pip install boto3`."
            ) from e
        creds = self.s3_credentials()
        return boto3.client("s3", **{**creds, **overrides})

    def install_aws_env(
        self,
        *,
        endpoint: Optional[str] = None,
        region: str = "us-east-1",
        password: Optional[str] = None,
    ) -> Dict[str, str]:
        """Bootstrap S3 credentials and export them as ``AWS_*`` env vars.

        Sets four variables in ``os.environ`` so that subprocess shells
        (``!aws s3 ls``, ``!s3cmd``, etc.) and any AWS SDK that reads the
        ambient environment can see them without further configuration:

        - ``AWS_ACCESS_KEY_ID``
        - ``AWS_SECRET_ACCESS_KEY``
        - ``AWS_DEFAULT_REGION``
        - ``AWS_ENDPOINT_URL_S3`` (picked up by boto3 ≥ 1.30 and the
          ``aws`` CLI v2 via ``--endpoint-url`` shorthand)

        ``password`` is deprecated/ignored (same as :meth:`s3_credentials`).

        Returns:
            The dict that was applied to ``os.environ`` — handy for
            eval-exporting into a parent shell.
        """
        if password is not None:
            warnings.warn(
                "password= is ignored for install_aws_env(); credentials come "
                "from the authenticated gRPC session (IssueCredentials). "
                "Remove the argument from your call site.",
                DeprecationWarning,
                stacklevel=2,
            )
        creds = self.s3_credentials(endpoint=endpoint, region=region)
        aws_env = {
            "AWS_ACCESS_KEY_ID": creds["aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": creds["aws_secret_access_key"],
            "AWS_DEFAULT_REGION": creds["region_name"],
            "AWS_ENDPOINT_URL_S3": creds["endpoint_url"],
        }
        os.environ.update(aws_env)
        return aws_env

    def _resolve_s3_endpoint(self) -> str:
        """Best-effort default URL for the S3 gateway.

        - gRPC mode: same host as the gRPC target, port 9876.
        - Local fallback: ``http://127.0.0.1:9876``.
        """
        if self.grpc_client is not None:
            host = self.grpc_client.endpoint.host
            return f"http://{host}:9876"
        return "http://127.0.0.1:9876"

    def _read_bootstrap_material(self) -> Tuple[str, str, str]:
        """Resolve ``(user_name, user_properties, private_key_encrypted)``.

        Retained for callers that inspect account material. S3 credential
        issuance no longer depends on these HTTP PUT payloads.
        """
        if self._account_dir_path is not None:
            props_path = None
            for fname in sorted(os.listdir(self._account_dir_path)):
                if fname.endswith("user.properties"):
                    props_path = os.path.join(self._account_dir_path, fname)
                    break
            if props_path is None:
                raise FileNotFoundError(
                    f"No *user.properties file in account dir {self._account_dir_path}"
                )
            with open(props_path, "r", encoding="utf-8") as f:
                user_properties = f.read()
            key_path = os.path.join(self._account_dir_path, "private.key")
            with open(key_path, "r", encoding="utf-8") as f:
                private_key_encrypted = f.read()
        elif self._user_properties is not None and self._private_key_encrypted is not None:
            user_properties = self._user_properties
            private_key_encrypted = self._private_key_encrypted
        else:
            raise RuntimeError(
                "S3 bootstrap material unavailable. Construct this "
                "AltaStataFunctions via from_account_dir(path) or "
                "from_credentials(user_properties, private_key)."
            )

        user_name = _parse_user_name_from_properties(user_properties)
        return user_name, user_properties, private_key_encrypted
