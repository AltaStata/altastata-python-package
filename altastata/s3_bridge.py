"""S3 / boto3 bridge for the bundled AltaStata S3 gateway (port 9876).

Extracted from :mod:`altastata.altastata_functions` so the file-ops facade
stays focused on gRPC while S3 admin bootstrap lives here.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


def _parse_user_name_from_properties(text: str) -> str:
    """Extract the ``myuser`` value from a user.properties text blob.

    Mirrors what {@code com.altastata.utils.Account} does on the Java side
    so the boto3 helper can derive the same user name that
    ``AccountRegistry.getOrCreate`` / ``getOrCreateFromDir`` would have
    chosen.

    Raises:
        ValueError: if no ``myuser=...`` line is present.
    """
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("myuser="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value
    raise ValueError("user_properties does not contain a non-empty 'myuser=' line")


def _http_put_text(url: str, body: str, timeout_s: float = 30.0) -> Tuple[int, bytes]:
    """Issue a ``PUT`` with a plain-text body using stdlib urllib.

    Used by the S3 boto3 helper to drive the three admin bootstrap PUTs
    (setUserProperties / setPrivateKey / setPassword). Kept on stdlib so we
    don't have to pull ``requests`` into install_requires just for this one
    code path.

    Returns:
        (status_code, body_bytes). Caller decides how to handle non-2xx.
    """
    req = urllib.request.Request(
        url=url,
        data=body.encode("utf-8"),
        method="PUT",
        headers={"Content-Type": "text/plain"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b""


class S3BridgeMixin:
    """Mixin providing :meth:`s3_credentials` / :meth:`boto3_s3` / :meth:`install_aws_env`.

    Expects the host class to populate (via constructors / :meth:`set_password`):

    - ``_account_dir_path``, ``_user_properties``, ``_private_key_encrypted``
    - ``_cached_password``, ``_s3_credentials_cache``
    - ``grpc_client`` (optional; used to derive the default S3 endpoint host)
    """

    def s3_credentials(
        self,
        *,
        password: Optional[str] = None,
        endpoint: Optional[str] = None,
        region: str = "us-east-1",
    ) -> Dict[str, str]:
        """Bootstrap and return boto3-ready S3 credentials.

        Drives the three admin PUTs against the S3 gateway running inside the
        same ``altastata-services`` JVM that backs this Python session
        (setUserProperties → setPrivateKey → setPassword), then returns the
        access/secret pair the gateway generated.

        Args:
            password: Plaintext account password used to unlock the encrypted
                private key on the gateway side. Falls back to the value
                cached by :meth:`set_password` (or the ``password`` kwarg
                passed to :meth:`from_account_dir` / :meth:`from_credentials`).
                Required for non-HSM users; HSM/HPCS users can pass ``""``.
            endpoint: Base URL of the S3 gateway. Defaults to
                ``http://<grpc-host>:9876`` for remote gRPC endpoints, or
                ``http://127.0.0.1:9876`` for a local co-hosted gateway.
            region: AWS region for SigV4. The gateway is region-agnostic but
                boto3 still demands a value; ``us-east-1`` is the safe default.

        Returns:
            Dict with keys ``endpoint_url``, ``aws_access_key_id``,
            ``aws_secret_access_key``, ``region_name`` — directly usable as
            ``boto3.client('s3', **result)``.

        Caveat:
            The third PUT (``setPassword``) calls
            ``AltaStataFileSystem.setPassword(...)`` on the shared instance
            stored in ``AccountRegistry``. Passing the same password you
            already used for this session is a no-op; passing a different
            one mutates the shared instance. The planned unified
            ``UserAdminRegistry`` (see
            ``mycloud/ALTASTATA_SERVICES_UBER_DESIGN.md`` §3.1) will close
            this gap.
        """
        endpoint = (endpoint or self._resolve_s3_endpoint()).rstrip("/")

        cached = self._s3_credentials_cache.get(endpoint)
        if cached is not None and cached.get("region_name") == region:
            return dict(cached)

        pw = password if password is not None else self._cached_password
        if pw is None:
            raise ValueError(
                "s3_credentials() requires a password. Either pass "
                "password=... explicitly, or call set_password() (or pass "
                "password=... to from_account_dir / from_credentials) first."
            )

        user_name, user_properties, private_key_encrypted = (
            self._read_bootstrap_material()
        )

        def _put(path: str, body: str) -> Dict[str, Any]:
            status, raw = _http_put_text(f"{endpoint}{path}", body)
            if status < 200 or status >= 300:
                raise RuntimeError(
                    f"S3 admin PUT {path} failed with HTTP {status}: "
                    f"{raw[:500].decode('utf-8', errors='replace')}"
                )
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except ValueError:
                return {"_raw": raw.decode("utf-8", errors="replace")}

        # setUserProperties / setPrivateKey are idempotent on the S3 side
        # ONLY when no UserData exists yet. Once the user has been bootstrapped
        # in this JVM (this same wheel call, an earlier wheel call, the
        # standalone S3 daemon, or external admin tooling), the gateway
        # refuses both PUTs with HTTP 400 unless `?password=<current>` is
        # supplied so it can validate the caller against the existing private
        # key (S3Controller.setUserProperties / setPrivateKey). Always send
        # the password as query — for fresh users it is ignored, for known
        # users it unblocks re-bootstrap with the same credentials.
        pw_q = "?password=" + urllib.parse.quote(pw, safe="")
        _put(f"/setUserProperties/{user_name}{pw_q}", user_properties)
        _put(f"/setPrivateKey/{user_name}{pw_q}", private_key_encrypted)
        body = _put(f"/setPassword/{user_name}", pw)

        access_key = body.get("accessKey")
        secret_key = body.get("secretKey")
        if not access_key or not secret_key:
            raise RuntimeError(
                "S3 gateway did not return accessKey/secretKey from "
                f"setPassword; response was: {body}"
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
        password: Optional[str] = None,
        endpoint: Optional[str] = None,
        region: str = "us-east-1",
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

        Returns:
            The dict that was applied to ``os.environ`` — handy for
            eval-exporting into a parent shell.
        """
        creds = self.s3_credentials(password=password, endpoint=endpoint, region=region)
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

        For instances built via :meth:`from_account_dir`, reads the
        ``*user.properties`` file and ``private.key`` from disk on each call
        so updates to those files take effect on the next bootstrap.
        For :meth:`from_credentials` instances, returns the strings supplied
        at construction.
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
