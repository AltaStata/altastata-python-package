# AltaStata Python package

Python SDK for the AltaStata sovereign data fabric: run AI/ML workloads and data pipelines as an AltaStata user, with per-file encryption on AWS, Azure, GCP, IBM, MinIO, POSIX, and hybrid backends.

Integrations: **fsspec**, **PyTorch**, **TensorFlow**, **LangChain**, **AI Agents**, **Databricks**, **Snowflake** (via S3), **boto3/S3 CLI**, **gRPC**, and a bundled **Web UI User Console**.

Cookbooks: [INTEGRATIONS.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/INTEGRATIONS.md) · Account setup: [USER_SETUP_GUIDE.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/USER_SETUP_GUIDE.md)

### Featured by Red Hat and IBM

- [Red Hat: end-to-end security for AI (OpenShift confidential containers)](https://www.redhat.com/en/blog/end-end-security-ai-integrating-altastata-storage-red-hat-openshift-confidential-containers)
- [IBM: data sovereignty for AI (LinuxONE Confidential Computing)](https://community.ibm.com/community/user/blogs/savita-kumari/2026/06/24/data-sovereignty-for-ai-integrating-alta-stata)

### Demo

- Video with Red Hat: [YouTube](https://www.youtube.com/watch?v=2EGncReIi00)
- For a live demo, email [contact@altastata.com](mailto:contact@altastata.com)

![AltaStata data flow](https://raw.githubusercontent.com/AltaStata/altastata-python-package/main/docs/images/altastata_dataflow.png)

Technology overview: [sovereign-data-fabric README](https://github.com/AltaStata/sovereign-data-fabric#altastata).

## Capabilities

- **Pythonic APIs:** Standard Python file I/O via fsspec (`create_filesystem`)
- **PyTorch:** Train and load datasets directly from encrypted cloud paths (`AltaStataPyTorchDataset`)
- **TensorFlow:** Same for TensorFlow / `tf.data` (`AltaStataTensorFlowDataset`)
- **LangChain & AI Agents:** RAG loaders and agent tools over encrypted data; gateway auto-starts
- **S3-compatible API:** boto3, aws CLI, s3fs on port **9876** — including Snowflake external stages that read S3
- **Distributed apps:** gRPC API (Python client + JS clients via port **9877**)
- **Sharing & events:** Users share encrypted files with each other; Python apps subscribe to SHARE/DELETE notifications
- **Web UI User Console:** Lighter browser UI on localhost only — same host as the Python install (http://127.0.0.1:9877)
- **Big Data:** Databricks / Apache Spark (AltaStata Hadoop FS JAR — not in the wheel; see [UBER_JARS](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/UBER_JARS.md))
- **Clouds & backends:** **AWS**, **Azure**, **GCP**, **IBM**, **Fusion**, **MinIO**, **POSIX / LocalFS** (local or shared path), and hybrid setups

## Quick start

Requires a configured account directory (steps 1–3 in **[USER_SETUP_GUIDE.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/USER_SETUP_GUIDE.md)**).

`from_account_dir` auto-starts the bundled Java gateway (Web UI + gRPC on **9877**, S3 on **9876**):

```python
from altastata import AltaStataFunctions

# Two backends in one process — AWS and Azure accounts side by side
bobAmazon = AltaStataFunctions.from_account_dir(
    "/path/to/.altastata/accounts/amazon.rsa.bob123",
    password="your_password",
)
bobAzure = AltaStataFunctions.from_account_dir(
    "/path/to/.altastata/accounts/azure.rsa.bob123",
    password="your_password",
)

print(bobAmazon.list_cloud_files_versions("Public/", True, None, None))
print(bobAzure.list_cloud_files_versions("Public/", True, None, None))
```

Next: file operations in [HOWTO.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/HOWTO.md); PyTorch, fsspec, S3 in [INTEGRATIONS.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/INTEGRATIONS.md).

One bundled Java process (`altastata-services`) listens on **9877** (gRPC + Web UI at http://127.0.0.1:9877) and **9876** (S3-compatible REST API).

## Documentation

| Topic | Guide |
|-------|--------|
| **Account setup & getting started** | [USER_SETUP_GUIDE.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/USER_SETUP_GUIDE.md) |
| **Upload, download, share, streams, events** | [HOWTO.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/HOWTO.md) |
| **fsspec, PyTorch, TensorFlow, LangChain, S3, Web UI** | [INTEGRATIONS.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/INTEGRATIONS.md) |
| **`AltaStataFunctions` API** | [PYTHON_API.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/PYTHON_API.md) |
| **Enterprise (Custodian, PQC, HSM/HPCS)** | [ENTERPRISE.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/ENTERPRISE.md) |
| **Examples** | [examples/](https://github.com/AltaStata/altastata-python-package/tree/main/examples) |
| **Build wheel, bundle JAR, PyPI** | [README-developer.md](https://github.com/AltaStata/altastata-python-package/blob/main/docs/guides/README-developer.md) |

## Questions?

Email [contact@altastata.com](mailto:contact@altastata.com).

## License

Licensed under the **Apache License, Version 2.0** — see [LICENSE](https://github.com/AltaStata/altastata-python-package/blob/main/LICENSE).

The Python / TypeScript sources in this repository are Apache 2.0. Bundled AltaStata
Java runtime JARs (when present under `altastata/lib/`) remain under the
[Business Source License 1.1](https://github.com/AltaStata/sovereign-data-fabric/blob/main/LICENSE.md).
See [NOTICE](https://github.com/AltaStata/altastata-python-package/blob/main/NOTICE) for attribution of bundled components.
