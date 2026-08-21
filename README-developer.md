# AltaStata Python Package Developer Guide

> Package version is tracked in `setup.py` (`pip show altastata` to inspect).
> **Scheme:** `1.0.YYYYMMDD.N` = bundled Java/BSL tag `vYYYY.MM.DD`, last digit =
> wheel build that day (easy to increment; Java stays on the BSL date). See
> [VERSIONING.md](VERSIONING.md).
> In-tree `setup.py`: **1.0.20260819.4** (Java **`2026.08.19`**). Last `1.0.6.x`
> line was **1.0.6.16** (no longer on PyPI; do not pin it).

## Prerequisites

### Bundled artifacts setup

The wheel ships with two binary artifacts that this repo deliberately does
not commit to git:

- `altastata/lib/altastata-services-<ver>-uber.jar` (built from
  `AltaStata/sovereign-data-fabric (altastata-services)` — the unified Micronaut app that hosts gRPC,
  and the S3 gateway under `com.altastata.services.AltaStataServicesApplication`)
- `altastata/lib/altastata-console-static/` (built from sibling
  [`AltaStata/altastata-console`](https://github.com/AltaStata/altastata-console) `frontend/`)

Everything under `altastata/lib/` is gitignored (`lib/` rule in `.gitignore`)
and must be populated locally before `pip install -e .` or `python -m build`.

#### Quick start (recommended)

Run the helper script — it builds both artifacts in one shot and stages
them under `altastata/lib/`:

```bash
bash scripts/build-bundled-artifacts.sh
```

The script assumes the sibling layout next to this repo:

- `../sovereign-data-fabric` (or `ALTASTATA_MYCLOUD_DIR`) for the services uber jar
- `../altastata-console` (or `ALTASTATA_CONSOLE_DIR`) for the Console SPA

Pass `SKIP_GRPC=1` / `SKIP_UI=1` to leave one side untouched.

#### Manual fallback

If you prefer to drive each build yourself:

1. Build the unified services uber jar in `altastata-services`:
   ```bash
   (cd ../sovereign-data-fabric && ./gradlew :altastata-services:shadowJar)
   cp ../sovereign-data-fabric/altastata-services/build/libs/altastata-services-*-uber.jar altastata/lib/
   # BouncyCastle is externalized as signed JCE jars referenced from the
   # uber jar manifest Class-Path; co-locate them alongside the uber jar:
   cp ../sovereign-data-fabric/altastata-services/build/libs/lib/bc*.jar altastata/lib/
   ```

2. Build the Console SPA from the sibling checkout:
   ```bash
   (cd ../altastata-console/frontend && npm install && npm run build)
   rm -rf altastata/lib/altastata-console-static
   mkdir -p altastata/lib/altastata-console-static
   cp -R ../altastata-console/frontend/dist/. altastata/lib/altastata-console-static/
   ```

3. Run the server (Java + bundled SPA on the same port):
   ```bash
   altastata-grpc-server
   # gRPC + UI both on http://127.0.0.1:9877
   ```

   The launcher exports `ALTASTATA_WEB_UI_DIR` automatically when the
   bundled `altastata/lib/altastata-console-static/` is present, so the Java
   gRPC gateway serves the SPA from the same port. Set
   `ALTASTATA_WEB_UI_DIR=` (empty) before running to disable the UI and
   keep gRPC-only routing for legacy testing.

### gRPC login (`LoginV2`)

`AltaStataGrpcClient.from_account_dir` authenticates via `AuthService.LoginV2`
with `user_account_directory` (account folder on the same host as the gateway).
`from_credentials` uses the `upload` form (`user_properties` + private key
bytes). Legacy `SetUserProperties` / `SetPrivateKey` bootstrap is not used on
the gRPC path. See **[USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md)**.

### Account setup CLI / SDK (no Desktop UI)

CLI: `altastata help`, `altastata account create`, `altastata account change-password`,
`altastata grpc-server`, `altastata mcp`.
SDK: `create_account`, `change_account_password`.

See **[USER_SETUP_GUIDE.md](https://github.com/AltaStata/altastata-python-package/blob/main/USER_SETUP_GUIDE.md)**. When `account_setup.proto`
changes in the Java repo, sync and regenerate:

```bash
cp ../sovereign-data-fabric/altastata-grpc/src/main/proto/altastata/grpc/v1/account_setup.proto \
  proto/altastata/grpc/v1/
python scripts/generate_grpc_stubs.py
```

### Agents / MCP

Python agents use `AltaStataFunctions.from_account_dir` (gateway auto-starts) —
see **Agents (Python)** in [README.md](README.md). Optional Desktop MCP stdio:
`altastata mcp` / `python -m altastata.mcp_server`.

### Logging Configuration
- To customize logging, copy and modify the logback configuration:
  ```bash
  # Optional: provide your own logback.xml in altastata/lib/
  ```

## boto3 / `aws` CLI against the bundled S3 gateway

The `altastata-services` JVM hosts the S3-compatible REST API on port `9876`
inside the same process that backs gRPC. When the S3 gate is on
(`ALTASTATA_SERVICES_S3GATEWAY_ENABLED=true`, default in the Jupyter docker
compose), `boto3` can hit the gateway directly and reads/writes will resolve
to the **same** `AltaStataFileSystem` instance the Python API uses, via the
shared `AccountRegistry`. See [UBER_JARS.md](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/UBER_JARS.md) for the wiring.

`AltaStataFunctions` exposes three helpers that call gRPC
`S3CredentialsService.IssueCredentials` on the logged-in Bearer session
(legacy HTTP admin PUTs with `?password=` were removed from the gateway)
and surface the issued access/secret pair:

```python
from altastata import AltaStataFunctions

alt = AltaStataFunctions.from_account_dir(
    "/home/jovyan/.altastata/accounts/amazon.rsa.bob123",
    password="your-account-password",
)

# One-liner — IssueCredentials on first call, dict-lookup on subsequent calls.
s3 = alt.boto3_s3()
print(s3.list_buckets())

# Or: get kwargs and pass to any AWS SDK / s3fs / pyarrow / awswrangler.
creds = alt.s3_credentials()
# {'endpoint_url': 'http://127.0.0.1:9876',
#  'aws_access_key_id': 'AKIA...',
#  'aws_secret_access_key': '...',
#  'region_name': 'us-east-1'}

# Or: install AWS_* env vars so `!aws s3 ls`, `!s3cmd`, and any SDK that
# reads the ambient env all "just work" from this Python process.
alt.install_aws_env()
```

`boto3` is not in `install_requires` — pip-install it separately when you
want the convenience wrapper (`pip install boto3`). `s3_credentials` /
`install_aws_env` use the authenticated gRPC client (no password-in-URL).

## Local Development

### Installation

```bash
# Install the package in development mode
pip install -e .

# Install from PyPI
pip install altastata
```

### Testing

**Unit tests** (mocked gRPC/S3; no live account or cloud):

```bash
pip install pytest   # not in install_requires — install once for dev
python -m pytest tests/ -q
```

Expect ~60 tests; **one is skipped by default** — the boto3 object-tagging
integration in `tests/test_object_tagging_boto3_integration.py` needs a real
account directory and the bundled services JVM:

```bash
ALTASTATA_ACCOUNT_DIR=$HOME/.altastata/accounts/amazon.rsa.bob123 \
  python -m pytest tests/test_object_tagging_boto3_integration.py -q
```

**Smoke test** (live account + gateway; not part of `pytest tests/`):

```bash
python examples/smoke-test/test_script.py
```

Example-specific tests live under `examples/*/README.md` (fsspec sharing, RAG,
event listener, and so on).

## Build and Upload

Use the comprehensive build script for easy deployment:

```bash
# Complete build and upload process
./containers/jupyter/build-and-upload.sh

# Or run individual steps:
python -m build                                    # Build Python package
twine upload dist/*                               # Upload to PyPI
./containers/jupyter/build-all-images.sh           # Build Docker images
./containers/jupyter/push-to-ghcr.sh               # Push to GHCR
```

## Docker Deployment

Full guide: [containers/jupyter/README-Docker.md](containers/jupyter/README-Docker.md)

### Version Management

The Docker image version is centrally managed in `version.sh`. To update the version:

1. Edit `version.sh` and update the `VERSION` variable
2. Run `./update-version.sh` to sync the version to all configuration files

All build scripts automatically use the version from `version.sh`.

### Multi-Architecture Support

The project builds **architecture-specific images** for AMD64 and ARM64.
Each architecture has its own GHCR package. The s390x (IBM Z/LinuxONE) image
is built separately using `containers/jupyter/Dockerfile.s390x`.

- **AMD64 (x86_64)**: `jupyter-datascience-amd64` — Intel/AMD processors and GCP nodes
- **ARM64**: `jupyter-datascience-arm64` — Apple Silicon Macs and ARM servers
- **s390x**: Build and tag separately for IBM Z/LinuxONE

### Building and Pushing Images
```bash
# Build and push architecture-specific images to GHCR
./containers/jupyter/push-to-ghcr.sh

# This creates:
# - ghcr.io/altastata/jupyter-datascience-arm64:${VERSION}
# - ghcr.io/altastata/jupyter-datascience-amd64:${VERSION}
```

### Running the Container

**Option A: Use pre-built image from GHCR (recommended — no build)**

The image is published to GitHub Container Registry, not Docker Hub. Use the GHCR compose file so the container runs without building:

```bash
# Run from GitHub Container Registry (no build, fast start)
docker compose -f containers/jupyter/docker-compose-ghcr.yml up -d
```

Then open **http://localhost:8888/lab**. The token is generated at startup; get it from the logs:

```bash
docker compose -f containers/jupyter/docker-compose-ghcr.yml logs altastata-jupyter 2>&1 | grep -E "127.0.0.1:8888|token"
# or
docker exec altastata-jupyter jupyter server list
```
Use the URL with `?token=...` from the output, or paste the token on the login page. If you still see an old fixed token, rebuild the image and recreate the container (see containers/jupyter/README-Docker.md).

**Option B: Single `docker run` with GHCR image**

```bash
source version.sh
# Use image matching your platform (arm64 for Apple Silicon, amd64 for Intel/AMD)
docker run \
  --name altastata-jupyter \
  -d \
  -p 8888:8888 \
  -v ~/.altastata:/opt/app-root/src/.altastata:rw \
  -v ~/Desktop:/opt/app-root/src/Desktop:rw \
  ghcr.io/altastata/jupyter-datascience-arm64:${VERSION}   # or jupyter-datascience-amd64
```

**Option C: Local build with docker-compose**

`docker compose -f containers/jupyter/docker-compose.yml up -d` uses image `altastata/jupyter-datascience-${ARCH}:${VERSION}` (ARCH is arm64 or amd64). Compose may **build** the image locally (can take 10–20 minutes). To use this path:

```bash
./update-version.sh   # writes VERSION and ARCH to .env (detects your platform)
docker compose -f containers/jupyter/docker-compose.yml up -d  # builds then runs
```

Then open **http://localhost:8888/lab**. Get the generated token from the logs: `docker compose -f containers/jupyter/docker-compose.yml logs altastata-jupyter 2>&1 | grep -E "127.0.0.1:8888|token"` or `docker exec altastata-jupyter jupyter server list`.

**IBM Z / LinuxONE (s390x)**

```bash
docker run \
  --name altastata-jupyter-s390x \
  -d \
  -p 8888:8888 \
  icr.io/altastata/jupyter-datascience-s390x:${VERSION}
```

**If the container won’t run**

- **“pull access denied” **— Use the GHCR image for your platform: `ghcr.io/altastata/jupyter-datascience-arm64` or `jupyter-datascience-amd64` with your version.
- **“container name already in use”** — Remove the existing container: `docker rm -f altastata-jupyter`, then start again.
- **Port 8888 in use** — Stop the process using it or change the host port, e.g. `"8889:8888"` in the compose file.
- **Get Jupyter URL/token** — `docker logs altastata-jupyter 2>&1 | grep -E "http://|token="`

### Platform Compatibility
- **Apple Silicon Macs**: Native ARM64 performance
- **Intel Macs**: Native AMD64 performance  
- **GCP Confidential GKE**: Native AMD64 performance
- **IBM Z and LinuxONE**: Use the `jupyter-datascience-s390x` image
- **Other platforms**: Automatic architecture selection for AMD64/ARM64

## PyPI Package Management

### Prerequisites
```bash
# Install required tools
pip install --upgrade pip build twine
```

### Building the Package
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Verify the built package
twine check dist/*
```

### Uploading to PyPI
```bash
# Upload to PyPI Test (optional)
# twine upload --repository testpypi dist/*

# Upload to PyPI Production
twine upload dist/*
```

### PyPI Configuration
1. Create a PyPI account if you don't have one
2. Generate an API token:
   - Go to https://pypi.org/manage/account/token/
   - Create a new token with appropriate permissions
   - Store the token securely

3. Configure `.pypirc`:
   ```ini
   [pypi]
   username = __token__
   password = pypi-your-token-here
   ```

### Large File Handling
For large files (like JARs), you may need to request a file size limit increase:
- Documentation: https://docs.pypi.org/project-management/storage-limits/#requesting-a-file-size-limit-increase
- Support Issue: https://github.com/pypi/support/issues/6225

### Project Links
- PyPI Project: https://pypi.org/project/altastata/


