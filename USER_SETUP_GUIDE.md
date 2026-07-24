# AltaStata Python — User Account Setup

How to **create** keys and **connect** from Python. For Desktop UI screenshots
(Public Key → admin → properties), see also
[USER_SETUP_GUIDE.md in sovereign-data-fabric](https://github.com/AltaStata/sovereign-data-fabric/blob/main/USER_SETUP_GUIDE.md).

---

## Configure your account

Two equivalent ways to connect from Python:

### 1. Account folder on disk (typical)

Each user keeps a directory under `~/.altastata/accounts/<display-name>/`:

```text
amazon.rsa.bob123/
  altastata-myorg-bob123.user.properties   # from your admin
  private.key                              # RSA (password-encrypted PEM)
  public.key
```

**Account types:**

- **RSA:** Needs `private.key`, `public.key`, and a password.
- **PQC:** Needs `kyber_private.key`, `dilithium_private.key`, etc., and a password.
- **HPCS:** Needs `hpcs-privkey.blob`, `public.key`, `hpcs.marker`, and **no** password (leave empty).
- **HSM:** Needs `*user.properties` only, and **no** password.

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_account_dir(
    "/path/to/.altastata/accounts/amazon.rsa.bob123",
    password="your_password",
)
```

### 2. Inline credentials (`user_properties` + private key)

Pass the same text you would have in files — useful for notebooks, secrets managers, or CI:

```python
from altastata import AltaStataFunctions

user_properties = """#My Properties
#Sun Jan 05 12:10:23 EST 2025
AWSSecretKey=*****
AWSAccessKeyId=*****
myuser=bob123
accounttype=amazon-s3-secure
acccontainer-prefix=altastata-myorg-
region=us-east-1
metadata-encryption=RSA"""

private_key = """-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3,F26EBECE6DDAEC52

... encrypted PEM body ...
-----END RSA PRIVATE KEY-----"""

altastata_functions = AltaStataFunctions.from_credentials(
    user_properties,
    private_key,
    password="my_password",
)
```

Your org admin creates `*user.properties` after you send them `public.key` (RSA/PQC/HPCS).

---

## Create an account without the Desktop UI (CLI / SDK)

Uses the same gRPC `AccountSetupService` as Console / SetupUI.

### Requirements

- `pip install altastata`
- Local gateway on port **9877** (CLI/SDK auto-starts the bundled runtime by default)
- For Docker / non-loopback binds: `ALTASTATA_LOCAL_MODE_ALLOW_ACCOUNT_SETUP=true`

### CLI

```bash
# RSA
altastata account create --type rsa --password 'secret' \
  --out ~/.altastata/accounts/amazon.rsa.alice --name amazon.rsa.alice

# PQC
altastata account create --type pqc --password 'secret' \
  --out ~/.altastata/accounts/amazon.pqc.bob --name amazon.pqc.bob

altastata account types

# Change the private-key password (RSA/PQC) — bootstrap, no login
altastata account change-password \
  --account-dir ~/.altastata/accounts/amazon.rsa.alice
```

Tips:

- Prefer `--password-env` / `--current-password-env` / `--new-password-env` in scripts.
- Use a **new** `--out` directory so you never overwrite an existing account.
- The private key stays on disk encrypted with your password; send only the
  **public** key material to your org admin.
- `change-password` only re-encrypts key files on disk (same local bootstrap
  mode as `create`; no LoginV2 / `*user.properties`).

### Python SDK

```python
from altastata import change_account_password, create_account

result = create_account(
    "rsa",
    "~/.altastata/accounts/amazon.rsa.alice",
    password="secret",
    name="amazon.rsa.alice",
)
print(result.suggested_display_name, sorted(result.account_files))

# Later — re-encrypt keys (no login / *user.properties needed)
change_account_password(
    "~/.altastata/accounts/amazon.rsa.alice",
    current_password="secret",
    new_password="new-secret",
)
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

### After the admin returns `*user.properties`

Place the file in the same account directory, then connect with
`AltaStataFunctions.from_account_dir` (see **Configure your account** above).
