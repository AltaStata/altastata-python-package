# AltaStata Python — User Account Setup

Create keys (Desktop UI or CLI below), send the **public key** to your admin,
drop `*user.properties` next to your keys. One account folder for **Python**,
**Java**, **Scala**, **S3**, and **gRPC**.

Desktop UI:
[USER_SETUP_GUIDE](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/USER_SETUP_GUIDE.md)
· Admins:
[ADMIN_TOOL_GUIDE](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md)

## Getting started

| Step | Who | What to do |
|------|-----|------------|
| **1. Keys** | You | [Desktop UI](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/USER_SETUP_GUIDE.md#desktop-ui-altastata-ui) or **Create keys using CLI** below. Send the **public key** to your org admin. |
| **2. Provision** | Org admin | [Admin Tool](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md) output: `~/.altastata/admin/properties.<cloud>/` ([§3.2](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md#32-output-paths)); send `*user.properties` to the user. |
| **3. Account directory** | You | Drop `*user.properties` in `~/.altastata/accounts/<name>/` next to your keys → **Connect from Python** below. Paths & logs: [USER_SETUP](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/USER_SETUP_GUIDE.md#where-files-live). |

Backends include cloud object storage and **POSIX / LocalFS**
([ADMIN_TOOL_GUIDE §3.3](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md#33-evaluate-on-local-disk-posix--localfs)).

## Create keys (CLI / SDK)

Same gRPC `AccountSetupService` as Desktop / Console. Gateway on **9877**
(auto-starts by default); Docker / remote bind:
`ALTASTATA_LOCAL_MODE_ALLOW_ACCOUNT_SETUP=true`.

### CLI

```bash
altastata help

altastata account create --type rsa --password 'secret' \
  --out ~/.altastata/accounts/amazon.rsa.alice --name amazon.rsa.alice

altastata account create --type pqc --password 'secret' \
  --out ~/.altastata/accounts/amazon.pqc.bob --name amazon.pqc.bob

altastata account change-password --account-dir ~/.altastata/accounts/amazon.rsa.alice
```

Use a **new** `--out` directory; send only the **public** key to the admin.
In scripts, prefer `--password-env` variants. `change-password` re-encrypts
keys on disk only (no `*user.properties` yet).

### Python SDK

```python
from altastata import change_account_password, create_account

result = create_account(
    "rsa", "~/.altastata/accounts/amazon.rsa.alice",
    password="secret", name="amazon.rsa.alice",
)
print(result.suggested_display_name, sorted(result.account_files))

change_account_password(
    "~/.altastata/accounts/amazon.rsa.alice",
    current_password="secret", new_password="new-secret",
)
```

```python
from altastata import AccountSetupClient

with AccountSetupClient.connect() as client:
    result = client.generate_keys("pqc", password="secret", suggested_display_name="amazon.pqc.bob")
    result.write_to("~/.altastata/accounts/amazon.pqc.bob")
```

## Connect from Python

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.alice",
    password="your-password",  # "" for HPCS / HSM
)
```

**Key types:** RSA — `private.key` + `public.key` + password. PQC — Kyber/Dilithium
files + password. HPCS — `hpcs-privkey.blob`, `hpcs.marker`, empty password.
HSM — `*user.properties` only, empty password.

Enterprise / eval: also `license.jwt` and `org-ca.pem` — [ENTERPRISE.md](ENTERPRISE.md).

### Inline credentials

Notebooks / CI — same file contents as text:

```python
from altastata import AltaStataFunctions

altastata_functions = AltaStataFunctions.from_credentials(
    user_properties, private_key, password="my_password",
)
```

## Security notes

- Never share private keys or commit account folders / passwords to git.
- Passphrase at every login (RSA/PQC); empty for HPCS.

## What to read next

| If you want… | Go to |
|--------------|--------|
| File ops | [HOWTO.md](HOWTO.md) |
| fsspec, PyTorch, LangChain, S3 | [INTEGRATIONS.md](INTEGRATIONS.md) |
| API reference | [PYTHON_API.md](PYTHON_API.md) |
| Enterprise | [ENTERPRISE.md](ENTERPRISE.md) |
