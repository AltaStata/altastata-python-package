# AltaStata Python — User Account Setup

Create your keys, send the **public key** to your org admin, then put the
`*user.properties` they return next to the keys. The private key never leaves
your machine.

Desktop UI (screenshots, **Account Properties**):
[USER_SETUP_GUIDE in sovereign-data-fabric](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/USER_SETUP_GUIDE.md).
Admins:
[ADMIN_TOOL_GUIDE](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md).

## Typical flow

1. **You** create keys (CLI / SDK below, or Desktop UI) and send the **public
   key** to the admin.
2. **Admin** provisions storage and sends you a `*user.properties` file.
3. **You** drop that file into the same account directory, then connect with
   `AltaStataFunctions.from_account_dir`.

## Create keys (CLI / SDK)

Same gRPC `AccountSetupService` as Console / Desktop Setup.

- `pip install altastata`
- Local gateway on port **9877** (CLI/SDK auto-starts the bundled runtime by default)
- For Docker / non-loopback binds: `ALTASTATA_LOCAL_MODE_ALLOW_ACCOUNT_SETUP=true`

### CLI

```bash
altastata help          # list all commands

# RSA
altastata account create --type rsa --password 'secret' \
  --out ~/.altastata/accounts/amazon.rsa.alice --name amazon.rsa.alice

# PQC
altastata account create --type pqc --password 'secret' \
  --out ~/.altastata/accounts/amazon.pqc.bob --name amazon.pqc.bob

# Optional — change private-key password later (RSA/PQC; no login)
altastata account change-password \
  --account-dir ~/.altastata/accounts/amazon.rsa.alice
```

- Run `altastata help` (or `altastata --help`) for the full command list.
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

# Optional — you can change the private-key password later
# (no login / *user.properties needed)
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

## Connect from Python

### Account folder (typical)

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.alice",
    password="your-password",  # "" for HPCS / HSM
)
```

RSA: `private.key` + `public.key` + a password.
PQC: `kyber_private.key`, `dilithium_private.key`, etc. + a password.
HPCS: `hpcs-privkey.blob`, `public.key`, `hpcs.marker`, and **no** password
(leave empty).
HSM: `*user.properties` only, and **no** password.

After the admin returns `*user.properties` (filename
`altastata-{org}-{username}.user.properties`), drop it in that same directory.
Enterprise / eval: also `license.jwt` and `org-ca.pem` —
[ENTERPRISE.md](ENTERPRISE.md).

### Inline credentials

Same text as the files — useful for notebooks, secrets managers, or CI:

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

## Security notes

- Never share private keys (`private.key`, PQC private keys, `hpcs-privkey.blob`).
- Never commit account folders or passwords to git.
- You need the passphrase at every login (RSA / PQC). Leave it empty for HPCS.
