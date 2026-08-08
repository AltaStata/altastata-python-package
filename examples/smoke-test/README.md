# Smoke tests (core API)

Manual scripts to verify AltaStataFunctions: store, retrieve, share, list, buffer, stream, delete.

- **test_script.py** – macOS/Linux (edit account path and Desktop paths for your machine).
- **test_script_windows.py** – Windows (edit account path and Desktop paths).
- **test_amazon_bob123_windows.py** – Windows smoke for `amazon.rsa.bob123` (uses `%USERPROFILE%\.altastata\accounts\amazon.rsa.bob123` + `ALTASTATA_PASSWORD`).

Run from repo root after `pip install -e .` (or `pip install altastata`):

```bash
python examples/smoke-test/test_script.py
# or
python examples/smoke-test/test_script_windows.py
```

Windows + bob123:

```bat
set ALTASTATA_PASSWORD=your_password
python examples\smoke-test\test_amazon_bob123_windows.py
```
