# Enterprise mode

Two access models — **Community** (uploader owns sharing) vs **Enterprise**
(CISO / **Custodian** governs access without plaintext). Day-to-day Python
ops: [HOWTO.md](HOWTO.md). Full write-up (Custodian flow, Admin egress, files):
[ENTERPRISE.md](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ENTERPRISE.md).

Account setup: [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md). Admin:
[ADMIN_TOOL_GUIDE](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md).

---

## What Enterprise unlocks

| Capability | Community | Enterprise (JWT features) |
|------------|-----------|-------------------------|
| RSA, AES-256-GCM, Python SDK, S3 / gRPC | Yes | Yes |
| Users | ≤5 + one org custodian | JWT `seats` (`0` = unlimited) |
| Certificate signing | AltaStata cloud CA, RSA only | Customer org CA; no `/sign` fallback |
| **PQC** (ML-KEM, ML-DSA) | No | `pqc` |
| **HSM / IBM HPCS** | No | `hsm`, `hpcs` |
| **Custodian mode** (CISO access manager) | Custodian identity only | `custodian` |
| **Governance** (policy graph, audit) | No | Commercial; `contact@altastata.com` |
| Runtime files | `*user.properties` | Also `license.jwt`, `org-ca.pem` |

Evaluation / PoC without a commercial contract is Community (RSA) unless AltaStata
issues a **trial** JWT for Enterprise features. `contact@altastata.com`.

---

## Python: account files

Community: keys + `*user.properties` → `from_account_dir` / `from_credentials`.

Enterprise / eval: also **`license.jwt`** and **`org-ca.pem`**:

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_upload(
    user_properties,
    {
        "private.key": private_key_bytes,
        "license.jwt": license_jwt_bytes,
        "org-ca.pem": org_ca_pem_bytes,
    },
    password="your-password",
)
```

Do not put the org CA **private** key on ordinary user accounts.
