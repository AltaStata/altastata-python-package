# AltaStata Python API — `AltaStataFunctions`

Primary SDK entry point — `AltaStataFunctions`.

Account setup (create keys / password): see [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md).  
Task-oriented examples: [HOWTO.md](HOWTO.md).  
Integrations (fsspec, PyTorch, S3, LangChain): see [INTEGRATIONS.md](INTEGRATIONS.md).

`from_account_dir` / `from_credentials` / `from_upload` talk to the bundled Java
gateway over **gRPC** (default `127.0.0.1:9877`) and can auto-start it.

---

## Construct

```python
from altastata import AltaStataFunctions

# Two backends in one process — AWS and Azure accounts side by side
f_aws = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.bob123",
    password="your_password",
)
f_azure = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/azure.rsa.alice222",
    password="your_password",
)

# Inline Community credentials (*user.properties + private.key)
f = AltaStataFunctions.from_credentials(
    user_properties,
    private_key,
    password="your_password",
)

# Enterprise / eval: properties + map of files
# (e.g. private.key, license.jwt, org-ca.pem)
f = AltaStataFunctions.from_upload(
    user_properties,
    account_files,
    password="your_password",
)
```

| Factory | When |
|---------|------|
| `from_account_dir(path, *, password, user_name=None, grpc_endpoint=None, grpc_auto_start_server=True)` | Local host: spawns or connects to gateway with local account folder |
| `from_credentials(user_properties, private_key_encrypted, *, password, user_name=None, grpc_endpoint=None, grpc_auto_start_server=True)` | Remote/Cloud: sends properties + encrypted private key over gRPC payload |
| `from_upload(user_properties, account_files, *, password, user_name=None, grpc_endpoint=None, grpc_auto_start_server=True)` | Enterprise/Cloud: sends properties + full account files map over gRPC |

Do not call `AltaStataFunctions()` directly.

**Local:** `from_account_dir` — account folder on the gateway host (auto-starts JAR).
**Remote:** `from_credentials` / `from_upload` — send properties and keys to `grpc_endpoint`.

---

## Files

| Method | Role |
|--------|------|
| `create_file(cloud_file_path, buffer=None)` | Create new cloud file version; optional initial `bytes` |
| `append_buffer_to_file(cloud_file_path, buffer, snapshot_time=None)` | Append bytes to a version |
| `get_buffer(path, snapshot_time, start_position, how_many_chunks_in_parallel, size, trust_cached_size=False)` | Read file as `bytes` |
| `get_input_stream(path, snapshot_time=None, start_position=0, parallel_chunks=4, chunk_size=8MiB, trust_cached_size=False)` | Yield `bytes` chunks (no full in-memory buffer) |
| `get_file_attribute(path, snapshot_time, name)` | Read a file attribute |
| `copy_file(from_path, to_path)` | Copy cloud → cloud |
| `store(local_paths, local_fs_prefix, cloud_path_prefix, wait_until_done)` | Upload local files/dirs |
| `retrieve_files(output_dir, cloud_path_prefix, including_subdirectories, snapshot_time, is_streaming, wait_until_done)` | Download to local dir |
| `delete_files(cloud_path_prefix, including_subdirectories, time_interval_start, time_interval_end)` | Delete matching versions |
| `list_cloud_files_versions(cloud_path_prefix, including_subdirectories, time_interval_start, time_interval_end)` | List versions under a prefix |

Time filters: use `None` where you want “no bound” (see method docs / examples).

```python
f.create_file("Public/hello.txt", b"hi")
# size must match the bytes you intend to read (or the known object size)
data = f.get_buffer("Public/hello.txt", None, 0, 4, 2)
versions = f.list_cloud_files_versions("Public/", True, None, None)

# Large files: stream chunks without buffering the whole object
for chunk in f.get_input_stream("Public/hello.txt"):
    process(chunk)
```

---

## Sharing

| Method | Role |
|--------|------|
| `share_files(prefix, including_subdirectories, time_start, time_end, users)` | Grant readers |
| `revoke_reader_access(prefix, including_subdirectories, time_start, time_end, readers_to_revoke)` | Revoke readers (owner/custodian) |

---

## Events

```python
def on_event(name, data):
    print(name, data)  # e.g. SHARE, DELETE

listener = f.add_event_listener(on_event)
# later, when done listening:
f.remove_event_listener(listener)
# or f.remove_all_event_listeners()
```

---

## S3 gateway helpers (mixin)

Same instance; uses the S3-compatible API on port **9876** (auto-started with the gateway).

| Method | Role |
|--------|------|
| `s3_credentials(*, endpoint=None, region="us-east-1", label="python-sdk")` | Dict of boto3-ready credentials via gRPC `IssueCredentials` (do not pass `password=`; deprecated) |
| `boto3_s3(**overrides)` | `boto3` S3 client (`pip install boto3`) |
| `install_aws_env(*, endpoint=None, region="us-east-1")` | Export `AWS_*` for shell / Jupyter `!aws` |

```python
s3 = f.boto3_s3()
s3.put_object(Bucket="altastata-bucket", Key="hello.txt", Body=b"hi")
```

---

## Lifecycle

| Method | Role |
|--------|------|
| `set_password(password)` | Update session password (also cached for S3 helpers) |
| `shutdown()` | Close gRPC client / release session |

Always call `shutdown()` (or use a `try`/`finally`) in long-running apps when done.

---

## Related

- **fsspec:** `from altastata.fsspec import create_filesystem` — [INTEGRATIONS.md § fsspec](INTEGRATIONS.md#fsspec)
- **PyTorch / TensorFlow:** [INTEGRATIONS.md](INTEGRATIONS.md) + [`examples/`](examples/)
- **gRPC (advanced):** most apps should stay on `AltaStataFunctions`. For remote/JS clients or proto-level control, see protos under `proto/altastata/grpc/v1/` and `AltaStataGrpcClient` in the package source. Java-side services: [sovereign-data-fabric `altastata-grpc`](https://github.com/AltaStata/sovereign-data-fabric/tree/main/altastata-grpc).
