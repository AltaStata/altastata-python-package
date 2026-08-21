# Altastata Python Package

Sovereign encrypted data fabric for any cloud Python SDK — with support for **fsspec**, **PyTorch**, **TensorFlow**, **LangChain**, **AI Agents**, **Databricks**, **Snowflake** (via S3), **boto3/S3 CLI**, **gRPC**, and a bundled **Web UI User Console**.

```bash
pip install altastata
```

When two organizations exchange files in the usual way, the sender **loses
control** once a copy leaves their boundary. With AltaStata, a user who puts a
**file** into the fabric **keeps cryptographic control of that file** even
after sharing it with a partner. They know **which humans or applications**
— in their own organization or a partner’s — have access, and they can
revoke it.

**Package version `1.0.20260819.8`** (`1.0.YYYYMMDD.N` — see [VERSIONING.md](https://github.com/AltaStata/altastata-python-package/blob/main/VERSIONING.md))
is built on the Java/BSL runtime from
[sovereign-data-fabric `v2026.08.19`](https://github.com/AltaStata/sovereign-data-fabric/releases/tag/v2026.08.19)
(bundled `altastata-services` uber jar + MCP). The last `1.0.6.x` line was `1.0.6.16` (no longer on PyPI).

Encryption usually slows pipelines — and most tools cannot work on encrypted
data. AltaStata keeps per-file cryptographic control **without losing speed**.
**Post-quantum** cryptography (ML-KEM / ML-DSA) is available in **Enterprise**;
Community uses RSA. With **data compression**, you can even **boost throughput**
and **lower storage costs**.

Each uploaded file is **immutable**. That is **cryptographically guaranteed**
by **AES-256-GCM**: even the owner cannot modify the file in place.
If a change is needed, the owner creates a **new version**.

## Integration

AltaStata is **seamlessly integrated** with **AI/ML** tools for **model training
and use** — PyTorch, TensorFlow, LangChain, agents (`pip install altastata`).

We collaborate with **Red Hat** and **IBM** on **confidential computing**:

- [Red Hat: end-to-end security for AI (OpenShift confidential containers)](https://www.redhat.com/en/blog/end-end-security-ai-integrating-altastata-storage-red-hat-openshift-confidential-containers)
- [IBM: data sovereignty for AI (LinuxONE Confidential Computing)](https://community.ibm.com/community/user/blogs/savita-kumari/2026/06/24/data-sovereignty-for-ai-integrating-alta-stata)

## How to use

Your organization’s **admin** (not each Python developer) provisions ordinary
cloud or local storage into this sovereign fabric with the **Admin Tool**.
Download it from [Releases](https://github.com/AltaStata/sovereign-data-fabric/releases)
— [how to use the Admin Tool](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md).
They return a `*user.properties` file; you then use this package (`pip install altastata`)
with your keys and that file.

### Typical data flow

**Bob** uploads a report and shares access with **Alice** (a person or an
application). In **Community** mode, Bob stays the **owner of that file**. Alice
is a **reader**: she can open it and see who has access, but she does not
grant or revoke sharing.

In **Enterprise** mode the access manager is **not** the user who created
the file. It is the organization’s **CISO / security team**, acting through
the **Custodian**. They fully manage users' access (share, revoke, delete) without
having access to plaintext. See **[ENTERPRISE.md](https://github.com/AltaStata/altastata-python-package/blob/main/ENTERPRISE.md)**.

![AltaStata data flow — library, package, or S3 gateway over any cloud, with per-file encryption, verification, and compression](https://raw.githubusercontent.com/AltaStata/altastata-python-package/main/docs/images/altastata_dataflow.png)

## Getting started

| Step | What to do |
|------|------------|
| **1. User account** | Create keys in the Desktop UI or with the CLI/SDK in this package (`pip install altastata`). See **[USER_SETUP_GUIDE.md](https://github.com/AltaStata/altastata-python-package/blob/main/USER_SETUP_GUIDE.md)**. |
| **2. Admin Tool** | Download the Admin Tool from [Releases](https://github.com/AltaStata/sovereign-data-fabric/releases) — [how to use the Admin Tool](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md). Org admin returns `*user.properties`. |

Then use the SDK below.

No cloud subscription yet? Provision the fabric on a local directory instead —
[evaluate on local disk (POSIX / LocalFS)](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md#33-evaluate-on-local-disk-posix--localfs).

## Supported clouds

Works on **AWS**, **Azure**, **GCP**, **IBM**, **Fusion**, **MinIO**, **POSIX** (local / NFS-style paths), and **hybrid** setups — any S3-compatible or cloud object store the account is configured for.

## Python API

SDK reference for `AltaStataFunctions`: **[PYTHON_API.md](https://github.com/AltaStata/altastata-python-package/blob/main/PYTHON_API.md)**

Day-to-day operations (upload, download, share, streams, events):
**[HOWTO.md](https://github.com/AltaStata/altastata-python-package/blob/main/HOWTO.md)**

Enterprise (Custodian, PQC, HSM/HPCS): **[ENTERPRISE.md](https://github.com/AltaStata/altastata-python-package/blob/main/ENTERPRISE.md)**

## What you get

- **Pythonic APIs:** Standard Python file I/O via fsspec (`create_filesystem`)
- **PyTorch:** Train and load datasets directly from encrypted cloud paths (`AltaStataPyTorchDataset`)
- **TensorFlow:** Same for TensorFlow / `tf.data` (`AltaStataTensorFlowDataset`)
- **LangChain & AI Agents:** RAG loaders and agent tools over encrypted data; gateway auto-starts
- **S3-compatible API:** boto3, aws CLI, s3fs on port **9876** — including Snowflake external stages that read S3
- **Distributed apps:** gRPC API (Python client + JS clients via port **9877**)
- **Sharing & events:** Users share encrypted files with each other; Python apps subscribe to SHARE/DELETE notifications
- **Web UI User Console:** Lighter browser UI on localhost only — same host as the Python install (http://127.0.0.1:9877)
- **Big Data:** Databricks / Apache Spark (AltaStata Hadoop FS JAR)

---

## Configure your account

See **[USER_SETUP_GUIDE.md](https://github.com/AltaStata/altastata-python-package/blob/main/USER_SETUP_GUIDE.md)**
for create keys (CLI/SDK), inline credentials, key types (rsa/pqc/hpcs), then
drop `*user.properties` and connect.

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

Set ALTASTATA_WEB_UI_DIR= (empty) to disable the UI and run gRPC-only.

---

## Desktop UI (separate download)

The native **Desktop UI** is not in this pip package. Download the Desktop UI from
[Releases](https://github.com/AltaStata/sovereign-data-fabric/releases) —
[user account setup](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/USER_SETUP_GUIDE.md).

![AltaStata Desktop UI — browse, preview, upload/download, and share encrypted files](https://raw.githubusercontent.com/AltaStata/altastata-python-package/main/docs/images/altastata_desktop_ui.png)

---

## More documentation

- **Python HOWTO** (upload, download, share, streams, events): [HOWTO.md](https://github.com/AltaStata/altastata-python-package/blob/main/HOWTO.md)
- **Enterprise mode** (Custodian, PQC, HSM/HPCS): [ENTERPRISE.md](https://github.com/AltaStata/altastata-python-package/blob/main/ENTERPRISE.md)
- **Python API** (`AltaStataFunctions`): [PYTHON_API.md](https://github.com/AltaStata/altastata-python-package/blob/main/PYTHON_API.md)
- **Developers** (build wheel, bundle JAR + Console SPA, PyPI, **`pytest tests/`**): [README-developer.md](https://github.com/AltaStata/altastata-python-package/blob/main/README-developer.md)
- **Examples**: [examples/](https://github.com/AltaStata/altastata-python-package/tree/main/examples)

## Questions?

Email [contact@altastata.com](mailto:contact@altastata.com).

## License

Licensed under the **Apache License, Version 2.0** — see [LICENSE](https://github.com/AltaStata/altastata-python-package/blob/main/LICENSE).

The Python / TypeScript sources in this repository are Apache 2.0. Bundled AltaStata
Java runtime JARs (when present under `altastata/lib/`) remain under the
[Business Source License 1.1](https://github.com/AltaStata/sovereign-data-fabric/blob/main/LICENSE.md).
See [NOTICE](https://github.com/AltaStata/altastata-python-package/blob/main/NOTICE) for attribution of bundled components.

---

## Spark / Databricks

The Hadoop filesystem JAR is **not** inside this pip wheel. Download it from
the BSL release and put it on the Spark classpath — see
[how to use the Hadoop and Services uber JARs](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/UBER_JARS.md).
