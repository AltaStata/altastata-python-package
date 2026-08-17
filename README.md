# Altastata Python Package

Sovereign encrypted data fabric for any cloud Python SDK — with support for **fsspec**, **PyTorch**, **TensorFlow**, **LangChain**, **AI Agents**, **Databricks**, **Snowflake** (via S3), **boto3/S3 CLI**, **gRPC**, and a bundled **Web UI User Console**.

**Package version `1.0.20260817.1`** (`1.0.YYYYMMDD.N` — see [VERSIONING.md](VERSIONING.md))
is built on the Java/BSL runtime from
[sovereign-data-fabric `v2026.08.17`](https://github.com/AltaStata/sovereign-data-fabric/releases/tag/v2026.08.17)
(bundled `altastata-services` uber jar + MCP). The last `1.0.6.x` wheel was `1.0.6.16`.

```bash
pip install altastata
```

## Supported clouds

Works on **AWS**, **Azure**, **GCP**, **IBM**, **Fusion**, **MinIO**, **POSIX** (local / NFS-style paths), and **hybrid** setups — any S3-compatible or cloud object store the account is configured for.

## Python API

SDK reference for `AltaStataFunctions`: **[PYTHON_API.md](PYTHON_API.md)**

Day-to-day operations (upload, download, share, streams, events):
**[HOWTO.md](HOWTO.md)**

## What you get

- **Pythonic APIs:** Standard Python file I/O via fsspec (`create_filesystem`)
- **PyTorch:** Train and load datasets directly from encrypted cloud paths (`AltaStataPyTorchDataset`)
- **TensorFlow:** Same for TensorFlow / `tf.data` (`AltaStataTensorFlowDataset`)
- **LangChain & AI Agents:** RAG loaders and agent tools over encrypted data; gateway auto-starts
- **S3-compatible API:** boto3, aws CLI, s3fs on port **9876** — including Snowflake external stages that read S3
- **Distributed apps:** gRPC API (Python client + JS clients via port **9877**)
- **Sharing & events:** Users share encrypted files with each other; Python apps subscribe to SHARE/DELETE notifications
- **Web UI User Console:** Finder-style file manager in the browser (http://127.0.0.1:9877)
- **Big Data:** Databricks / Apache Spark (AltaStata Hadoop FS JAR)

---

## Configure your account

See **[USER_SETUP_GUIDE.md](https://github.com/AltaStata/altastata-python-package/blob/main/USER_SETUP_GUIDE.md)** for create-account (CLI/SDK),
inline credentials, and generatable key types (rsa/pqc/hpcs).

```bash
altastata help    # list CLI commands
```

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.bob123",
    password="your_password",
)
```

---

## Quick start

`from_account_dir` / `from_credentials` auto-start the bundled Java gateway (Web UI User Console + gRPC + S3).

```python
from altastata import AltaStataFunctions

# RSA / PQC
f = AltaStataFunctions.from_account_dir(
    "/path/to/.altastata/accounts/amazon.rsa.bob123",
    password="your_password",
)

# HPCS / HSM — empty password
f = AltaStataFunctions.from_account_dir(
    "/path/to/.altastata/accounts/amazon.rsa.hpcs.myuser",
    password="",
)

print(f.list_cloud_files_versions("Public/", True, None, None))
```

### Ports

One bundled Java process (altastata-services) listens on:

- **9877**: gRPC (file ops, auth, events) + Web UI User Console at http://127.0.0.1:9877
- **9876**: S3-compatible REST API

---

## fsspec

```python
from altastata import AltaStataFunctions
from altastata.fsspec import create_filesystem

f = AltaStataFunctions.from_account_dir("/path/to/account", password="secret")
fs = create_filesystem(f, "my_account")

with fs.open("Public/readme.txt", "r") as fh:
    print(fh.read())
```

Works with pandas, dask, and other fsspec consumers.

---

## LangChain & AI Agents

### LangChain / RAG

Load encrypted documents without copying them to local disk:

```python
from altastata import AltaStataFunctions
from altastata.fsspec import create_filesystem
from langchain_core.documents import Document

f = AltaStataFunctions.from_account_dir("/path/to/account", password="secret")
fs = create_filesystem(f, "my_account")

with fs.open("Public/docs/policy.txt", "r") as fh:
    docs = [Document(page_content=fh.read(), metadata={"source": "Public/docs/policy.txt"})]
```

TextLoader, DirectoryLoader, and other LangChain loaders work via the altastata:// fsspec protocol once the filesystem is registered — see [examples/fsspec-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/fsspec-example/) and full RAG pipelines in [examples/rag-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/rag-example/).

### Integration with AI Agents

Python agents (LangGraph, notebooks, scripts) use the same `AltaStataFunctions` /
fsspec APIs as above — `from_account_dir` auto-starts the gateway. For external
agents that speak MCP over stdio (Claude Desktop, Cursor/Windsurf, …), see
[altastata-mcp](https://github.com/AltaStata/sovereign-data-fabric/tree/main/altastata-mcp)
(`altastata mcp` is optional).

---

## S3-compatible API (boto3, aws CLI, s3fs)

```python
f = AltaStataFunctions.from_account_dir("/path/to/account", password="secret")

s3 = f.boto3_s3()   # pip install boto3
s3.put_object(Bucket="altastata-bucket", Key="hello.txt", Body=b"hi")

f.install_aws_env()   # AWS_* for !aws s3 ls in Jupyter
```

### Snowflake

Snowflake can read AltaStata-backed objects through the S3-compatible gateway:

- **External stage via S3:** point Snowflake at the bundled S3 Gateway (`http://host:9876`) as an S3-compatible endpoint for encrypted objects in your backing bucket.
- **Snowpark Python:** use fsspec / `create_filesystem` in Snowpark notebooks to read AltaStata paths with the same account credentials.

---

## PyTorch

```python
from altastata import AltaStataFunctions, AltaStataPyTorchDataset
from altastata.altastata_pytorch_dataset import register_altastata_functions_for_pytorch

f = AltaStataFunctions.from_account_dir("/path/to/account", password="secret")
register_altastata_functions_for_pytorch(f, "my_account")
dataset = AltaStataPyTorchDataset("my_account", root_dir="Public/", file_pattern="*.jpg")
```

See [examples/pytorch-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/pytorch-example/).

---

## TensorFlow

```python
from altastata import AltaStataFunctions, AltaStataTensorFlowDataset
from altastata.altastata_tensorflow_dataset import register_altastata_functions_for_tensorflow

f = AltaStataFunctions.from_account_dir("/path/to/account", password="secret")
register_altastata_functions_for_tensorflow(f, "my_account")
dataset = AltaStataTensorFlowDataset(
    "my_account",
    root_dir="Public/",
    file_pattern="*.jpg",
)
```

See [examples/tensorflow-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/tensorflow-example/).

---

## Event notifications

AltaStata lets users **share encrypted files with each other**. When files are shared or deleted, Python applications can catch those events in real time and react (refresh caches, notify users, trigger pipelines).

```python
def on_event(name, data):
    print(name, data)

f = AltaStataFunctions.from_account_dir(
    "/path/to/account",
    password="secret",
)
f.add_event_listener(on_event)
```

SHARE and DELETE events also appear in the Web UI User Console and via gRPC `EventsService.Watch`.

See [examples/event-listener-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/event-listener-example/).

---

## Web UI User Console

The wheel ships a browser file manager. Start the gateway:

```bash
altastata-grpc-server
# same as: python -m altastata.grpc_server
```

Open **http://127.0.0.1:9877** — Miller-column browser, upload/download, share, generate keys, and live refresh on SHARE/DELETE events.

**Sign in:** Settings → **Choose account folder** → **Sign in**

- **RSA / PQC:** Use your account password.
- **HPCS / HSM:** Leave the password blank.

Set ALTASTATA_WEB_UI_DIR= (empty) to disable the UI and run gRPC-only.

---

## More documentation

- **Python HOWTO** (upload, download, share, streams, events): [HOWTO.md](HOWTO.md)
- **Python API** (`AltaStataFunctions`): [PYTHON_API.md](PYTHON_API.md)
- **Developers** (build wheel, bundle JAR + Console SPA, PyPI): [README-developer.md](README-developer.md)
- **Examples**: [examples/](examples/)

## Questions?

Email [contact@altastata.com](mailto:contact@altastata.com).

## License

Licensed under the **Apache License, Version 2.0** — see [LICENSE](LICENSE).

The Python / TypeScript sources in this repository are Apache 2.0. Bundled AltaStata
Java runtime JARs (when present under `altastata/lib/`) remain under the
[Business Source License 1.1](https://github.com/AltaStata/sovereign-data-fabric/blob/main/LICENSE.md).
See [NOTICE](NOTICE) for attribution of bundled components.

---

## Spark / Databricks

The Hadoop filesystem JAR is **not** inside this pip wheel. Download it from
the BSL release and put it on the Spark classpath — see
[how to use the Hadoop and Services uber JARs](https://github.com/AltaStata/sovereign-data-fabric/blob/main/UBER_JARS.md).
