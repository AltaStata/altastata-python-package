# AltaStata Python — Create an Account (CLI / SDK)

Create RSA / PQC / HPCS keys **without** the Desktop UI. Uses the same gRPC
`AccountSetupService` as Console / SetupUI.

For the full end-user flow (Desktop UI screenshots, Public Key → admin →
`*user.properties`), see the main product guide:
[USER_SETUP_GUIDE.md in sovereign-data-fabric](https://github.com/AltaStata/sovereign-data-fabric/blob/main/USER_SETUP_GUIDE.md).

## Requirements

- `pip install altastata`
- Local gateway on port **9877** (CLI/SDK auto-starts the bundled runtime by default)
- For Docker / non-loopback binds: `ALTASTATA_LOCAL_MODE_ALLOW_ACCOUNT_SETUP=true`

## CLI

```bash
# RSA
altastata account create --type rsa --password 'secret' \
  --out ~/.altastata/accounts/amazon.rsa.alice --name amazon.rsa.alice

# PQC
altastata account create --type pqc --password 'secret' \
  --out ~/.altastata/accounts/amazon.pqc.bob --name amazon.pqc.bob

altastata account types
```

Tips:

- Prefer `--password-env VAR` in scripts.
- Use a **new** `--out` directory so you never overwrite an existing account.
- The private key stays on disk encrypted with your password; send only the
  **public** key material to your org admin.

## Python SDK

```python
from altastata import create_account

result = create_account(
    "rsa",
    "~/.altastata/accounts/amazon.rsa.alice",
    password="secret",
    name="amazon.rsa.alice",
)
print(result.suggested_display_name, sorted(result.account_files))
```

Or with an explicit client:

```python
from altastata import AccountSetupClient

with AccountSetupClient.connect() as client:
    result = client.generate_keys(
        "pqc",
        password="secret",
        suggested_display_name="amazon.pqc.bob",
    )
    result.write_to("~/.altastata/accounts/amazon.pqc.bob")
```

## After the admin returns `*user.properties`

Place the file in the same account directory, then:

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.alice",
    password="secret",
)
```
