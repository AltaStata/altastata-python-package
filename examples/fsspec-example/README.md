# AltaStata fsspec Integration

Simple fsspec filesystem interface for AltaStata that automatically uses the latest version of files.

## Examples

This directory contains working examples and tests:

- **`example.py`** - Basic fsspec usage example
- **`test_simple.py`** - Simple fsspec functionality test (small file)
- **`test_large_file_fsspec.py`** - Performance test with 100MB files and data verification

## Running Tests

```bash
# Basic example
python example.py

# Simple functionality test (small file)
python test_simple.py

# Large file performance test (100MB with data verification)
python test_large_file_fsspec.py
```

## RAG Pipeline

For secure RAG (Retrieval-Augmented Generation) implementations with AltaStata, see the **[rag-example/](../rag-example/)** (under examples/) directory:

- Complete working RAG pipeline with LangChain
- Security architecture documentation
- Sample policy documents
- Real test output examples

## Installation

```bash
pip install altastata fsspec
```

## Usage

```python
import fsspec
from altastata import AltaStataFunctions
from altastata.fsspec import create_filesystem, register_filesystem

# 1. Initialize AltaStata session
functions = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.alice222",
    password="your_password"
)

# 2. Create fsspec filesystem instance
fs = create_filesystem(functions, account_id="alice222")
files = fs.ls("Public/")

# 3. Read file (always latest version)
with fs.open("Public/Documents/file.txt", "rb") as f:
    content = f.read()
```

> **Note on File I/O:** `fsspec` provides read access to the encrypted fabric. For creating or uploading files, use `functions.create_file(...)` or the S3 compatibility layer (`functions.boto3_s3()`).

## LangChain Integration

```python
from altastata import AltaStataFunctions
from altastata.fsspec import register_filesystem
from langchain_community.document_loaders import TextLoader

# Initialize AltaStata and register global filesystem protocol
functions = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.alice222",
    password="your_password"
)
register_filesystem(functions)

# Load document directly via altastata:// URI
loader = TextLoader("altastata://Public/Documents/file.txt")
documents = loader.load()
```