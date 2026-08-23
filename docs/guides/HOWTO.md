# How to work with AltaStata (Python)

Task-oriented `AltaStataFunctions` examples. Java / Desktop / S3:
[sovereign-data-fabric HOWTO](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/HOWTO.md).

Account: [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md). API: [PYTHON_API.md](PYTHON_API.md).

```python
from altastata import AltaStataFunctions

# Two backends in one process — AWS and Azure accounts side by side
bobAmazon = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.bob123",
    password="your-password",
)
bobAzure = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/azure.rsa.alice222",
    password="your-password",
)
```

Task examples below use **`bobAmazon`** (AWS). Use **`bobAzure`** (Azure) the same way.

Times are milliseconds since epoch. On `share_files`, `delete_files`,
`list_cloud_files_versions`, and `revoke_reader_access`, pass `None` for a
time bound you do not want. `retrieve_files` takes a snapshot time; pass
`int(time.time() * 1000)` for the latest version.

A **path prefix** names a subtree. `"Public/inbox"` with
`including_subdirectories=True` is every file under that folder; `False`
applies only to that exact path.

---

## Upload

```python
bobAmazon.store(
    ["/data/report.pdf", "/data/images"],  # local files/dirs to upload
    "/data",          # local prefix stripped from every selected path
    "Public/inbox",   # destination prefix inside AltaStata
    True,             # wait for every upload to finish
)

# create_file creates a new version rather than overwriting version history.
bobAmazon.create_file("Public/inbox/hello.txt", b"hello")

bobAmazon.append_buffer_to_file(
    "Public/inbox/hello.txt",   # existing cloud path
    b"\nmore",                  # bytes appended to that version
    snapshot_time=None,         # None = latest version
)
```

---

## Download

```python
import time

bobAmazon.retrieve_files(
    "./out",                    # local destination directory
    "Public/inbox",             # cloud path or prefix to download
    True,                       # include subdirectories
    int(time.time() * 1000),    # latest version at or before this snapshot
    False,                      # False = regular download, True = streaming mode
    True,                       # wait until all downloads finish
)

data = bobAmazon.get_buffer(
    "Public/inbox/hello.txt",  # cloud path
    None,                      # None = latest version
    0,                         # starting byte offset
    4,                         # chunks prefetched in parallel
    -1,                        # -1 = entire file
)
```

---

## List / see versions

```python
for row in bobAmazon.list_cloud_files_versions(
    "Public/",  # cloud path or prefix to list
    True,       # recursively include subdirectories
    None,       # no minimum create-time
    None,       # no maximum create-time
):
    print(row)
```

---

## Share

```python
bobAmazon.share_files(
    "Public/inbox/report.pdf",  # cloud path or prefix to share
    True,                       # include descendants when the path is a directory
    None,                       # no minimum version create-time
    None,                       # no maximum version create-time
    ["bob123"],                 # reader usernames
)
```

---

## Revoke

```python
bobAmazon.revoke_reader_access(
    "Public/inbox/report.pdf",  # cloud path whose readers change
    True,                       # include descendants
    None,                       # no minimum version create-time
    None,                       # no maximum version create-time
    ["bob123"],                 # readers to remove
)
```

---

## Delete

```python
bobAmazon.delete_files(
    "Public/inbox/report.pdf",  # cloud path or prefix to delete
    True,                       # recursively delete descendants
    None,                       # no minimum version create-time
    None,                       # no maximum version create-time
)
```

---

## Find / search

No dedicated search. List under a prefix and filter locally.

```python
for row in bobAmazon.list_cloud_files_versions("Public/", True, None, None):
    path = row[0] if isinstance(row, (list, tuple)) else row
    if "report" in str(path):
        print(path)
```

---

## Copy (same fabric)

```python
bobAmazon.copy_file(
    "Public/inbox/report.pdf",     # latest source version is read
    "Public/archive/report.pdf",   # source is preserved
)
```

---

## Who can see a file

```python
bobAmazon.get_file_attribute(
    "Public/inbox/report.pdf",  # cloud path
    None,                       # version create-time; None = latest
    "readers",                  # attribute name
)
bobAmazon.get_file_attribute(
    "Public/inbox/report.pdf",
    None,
    "size",
)
```

`owner` is not a data attribute. The creator is the version tag in
`list_cloud_files_versions`.

---

## Streams

Python does not expose Java `AltaStataChunkedInputStream` /
`AltaStataChunkedOutputStream` objects. Read large files as chunks with
`get_input_stream`. Write with `create_file` / `append_buffer_to_file` or
`store`.

```python
for chunk in bobAmazon.get_input_stream(
    "Public/inbox/video.mp4",  # cloud path
    snapshot_time=None,        # None = latest version
    start_position=0,          # starting byte offset
    parallel_chunks=4,         # chunks prefetched in parallel
):
    process(chunk)             # successive plaintext bytes
```

---

## Events (share / delete)

When someone **shares** a file with you or **deletes** a version you can see,
the client fires `SHARE` / `DELETE`. The payload is the cloud path (often with
a version suffix). Keep the process running. Runnable pair:
[examples/event-listener-example](examples/event-listener-example/).

```python
def on_event(name, data):
    # name is "SHARE" or "DELETE"; data is the cloud path of the version
    print(name, data)

listener = bobAmazon.add_event_listener(on_event)
# later:
bobAmazon.remove_event_listener(listener)
```

---

## What to read next

| If you want… | Go to |
|--------------|--------|
| Method reference | [PYTHON_API.md](PYTHON_API.md) |
| Create account (CLI/SDK) | [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md) |
| Enterprise / Custodian / PQC | [ENTERPRISE.md](ENTERPRISE.md) |
| fsspec / PyTorch / S3 | [INTEGRATIONS.md](INTEGRATIONS.md) |
| Java / Desktop / S3 how-to | [sovereign-data-fabric HOWTO](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/HOWTO.md) |
| Scala `CloudFile` API | [Low-level-Scala-API](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/Low-level-Scala-API.md) |
