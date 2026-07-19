# Altastata Python Package

Secure, encrypted cloud storage for Python — with **fsspec**, **PyTorch/TensorFlow**, **LangChain**, **Databricks**, **Snowflake**, **boto3/S3**, **gRPC**, and a bundled **Web UI** (AltaStata Console).

```bash
pip install altastata
```

## What you get

- **Storage:** Encrypted files in S3, Azure, IBM COS, etc. (AltaStataFunctions)
- **Pythonic APIs:** Standard Python file I/O via fsspec (create_filesystem)
- **ML & AI:** Datasets (AltaStataPyTorchDataset, AltaStataTensorFlowDataset)
- **RAG:** LangChain document loading (fsspec + DirectoryLoader / TextLoader)
- **Big Data:** Databricks / Apache Spark (AltaStata Hadoop FS JAR)
- **Data Warehousing:** Snowflake external stages (S3 Gateway) or Snowpark Python (fsspec)
- **AWS Ecosystem:** S3 tools like boto3, aws CLI, and s3fs (S3-compatible API on port **9876**)
- **Distributed apps:** gRPC API (Python client + JS clients via port **9877**)
- **Real-time:** Real-time share/delete events (gRPC EventsService or Web UI)
- **Web UI:** Finder-style file manager in the browser (http://127.0.0.1:9877)

---

## Configure your account

See **[USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md)** for create-account (CLI/SDK),
inline credentials, and account types.

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.bob123",
    password="your_password",
)
```

---

## Quick start (gRPC — recommended)

`from_account_dir` / `from_credentials` auto-start the bundled Java gateway (Web UI + gRPC + S3).

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

print(f.list_cloud_versions("Public/", True))
```

### Ports

One bundled Java process (altastata-grpc-server / altastata-services) listens on:

- **9877**: gRPC (file ops, auth, events) + Web UI static files
- **9876**: S3-compatible REST API

### HPCS in Docker / Jupyter

Mount a populated grep11client.yaml (e.g. /etc/ep11client/grep11client.yaml) and hpcs-privkey.blob. See [containers/jupyter/README-Docker.md](https://github.com/AltaStata/altastata-python-package/tree/main/containers/jupyter/README-Docker.md).

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

## LangChain, Databricks, Snowflake

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

### Databricks / Apache Spark

Use the AltaStata Hadoop filesystem implementation so Spark jobs read encrypted paths on cluster storage (altastata://… or configured Hadoop URI). Deploy the altastata-hadoop shadow JAR on Databricks / Spark clusters.

### Snowflake

- **External stage via S3:** point Snowflake at the bundled S3 Gateway (http://host:9876) as an S3-compatible endpoint for encrypted objects in your backing bucket.
- **Snowpark Python:** use fsspec / create_filesystem in Snowpark notebooks to read AltaStata paths with the same account credentials.

---

## S3-compatible API (boto3, aws CLI, s3fs)

```python
f = AltaStataFunctions.from_account_dir("/path/to/account", password="secret")

s3 = f.boto3_s3()   # pip install boto3
s3.put_object(Bucket="altastata-bucket", Key="hello.txt", Body=b"hi")

f.install_aws_env()   # AWS_* for !aws s3 ls in Jupyter
```

---

## PyTorch & TensorFlow

```python
from altastata import AltaStataFunctions, AltaStataPyTorchDataset
from altastata.altastata_pytorch_dataset import register_altastata_functions_for_pytorch

f = AltaStataFunctions.from_account_dir("/path/to/account", password="secret")
register_altastata_functions_for_pytorch(f, "my_account")
dataset = AltaStataPyTorchDataset("my_account", root_dir="Public/", file_pattern="*.jpg")
```

See [examples/pytorch-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/pytorch-example/) and [examples/tensorflow-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/tensorflow-example/).

---

## Event notifications

```python
def on_event(name, data):
    print(name, data)

f = AltaStataFunctions.from_account_dir(
    "/path/to/account",
    password="secret",
)
f.add_event_listener(on_event)
```

With gRPC / Web UI, SHARE and DELETE events also appear in the browser and via EventsService.Watch.

See [examples/event-listener-example/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/event-listener-example/).

---

## Docker Jupyter (optional)

```bash
cd containers/jupyter
docker compose -f docker-compose.yml -f docker-compose-ghcr.yml up -d
```

- JupyterLab: http://127.0.0.1:8888  
- **Web UI** / gRPC: http://127.0.0.1:9877  

Images: ghcr.io/altastata/altastata/jupyter-datascience-{arm64,amd64}:latest

---

## Web UI (AltaStata Console)

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

- **Developers** (build wheel, bundle JAR + Console SPA, PyPI): [README-developer.md](https://github.com/AltaStata/altastata-python-package/blob/main/README-developer.md)
- **Examples**: [examples/](https://github.com/AltaStata/altastata-python-package/tree/main/examples/)

## Questions?

Email [contact@altastata.com](mailto:contact@altastata.com).

## License

Licensed under the **Apache License, Version 2.0** — see [LICENSE](LICENSE).

The Python / TypeScript sources in this repository are Apache 2.0. Bundled AltaStata
Java runtime JARs (when present under `altastata/lib/`) remain under the
[Business Source License 1.1](https://github.com/AltaStata/sovereign-data-fabric/blob/main/LICENSE.md).
See [NOTICE](NOTICE) for attribution of bundled components.
