# AltaStata Python — Integrations

Code patterns for **fsspec**, **LangChain**, **S3**, **PyTorch**, **TensorFlow**, **events**, and the bundled **Web UI User Console**.

Account setup: [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md). File operations: [HOWTO.md](HOWTO.md). API reference: [PYTHON_API.md](PYTHON_API.md).

![AltaStata data flow](https://raw.githubusercontent.com/AltaStata/altastata-python-package/main/docs/images/altastata_dataflow.png)

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

Works with pandas, dask, and other fsspec consumers. See [examples/fsspec-example/](examples/fsspec-example/).

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

TextLoader, DirectoryLoader, and other LangChain loaders work via the altastata:// fsspec protocol once the filesystem is registered — see [examples/fsspec-example/](examples/fsspec-example/) and full RAG pipelines in [examples/rag-example/](examples/rag-example/).

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

See [examples/pytorch-example/](examples/pytorch-example/).

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

See [examples/tensorflow-example/](examples/tensorflow-example/).

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

See [examples/event-listener-example/](examples/event-listener-example/).

---

## Web UI User Console

A lighter browser UI bundled with this package. It listens on **localhost**
(http://127.0.0.1:9877), so only a browser on the **same host** as the Python
install (and Java gateway) can open it. Start the gateway:

```bash
altastata-grpc-server
# same as: python -m altastata.grpc_server
```

Open **http://127.0.0.1:9877** — Miller-column browser, upload/download, share, generate keys, and live refresh on SHARE/DELETE events.

**Sign in:** Settings → **Choose account folder** → **Sign in**

- **RSA / PQC:** Use your account password.
- **HPCS / HSM:** Leave the password blank.

Set `ALTASTATA_WEB_UI_DIR=` (empty) to disable the UI and run gRPC-only.

---

## Desktop UI (separate download)

The native **Desktop UI** is not in this pip package. Download the Desktop UI from
[Releases](https://github.com/AltaStata/sovereign-data-fabric/releases) —
[user account setup](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/USER_SETUP_GUIDE.md).

![AltaStata Desktop UI — browse, preview, upload/download, and share encrypted files](https://raw.githubusercontent.com/AltaStata/altastata-python-package/main/docs/images/altastata_desktop_ui.png)

---

## Spark / Databricks

The Hadoop filesystem JAR is **not** inside this pip wheel. Download it from
the BSL release and put it on the Spark classpath — see
[how to use the Hadoop and Services uber JARs](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/UBER_JARS.md).
