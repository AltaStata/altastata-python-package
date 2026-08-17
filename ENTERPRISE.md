# Enterprise mode

AltaStata has **two access-control and sharing models**. Day-to-day Python
operations are the same ([HOWTO.md](HOWTO.md)); this page is **who governs
access** and **which crypto / CA features** a commercial license unlocks.

Account files and CLI: [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md).
Admin provisioning (Java tree):
[ADMIN_TOOL_GUIDE](https://github.com/AltaStata/sovereign-data-fabric/blob/main/ADMIN_TOOL_GUIDE.md).
Full Enterprise write-up on the BSL tree:
[ENTERPRISE.md](https://github.com/AltaStata/sovereign-data-fabric/blob/main/ENTERPRISE.md).

---

## Community vs Enterprise (sharing)

### Community

Whoever **uploads** the file is the **owner**. The owner shares with readers
and controls who has access.

If an **AI-powered service** creates a report, that service stays the owner
and the organization is a **reader**. A reader can see who has access
(observation) but does not control sharing.

### Enterprise (Custodian as access manager)

A special **Custodian** user is the **access manager** for files. All sharing
goes through the Custodian. The Custodian **does not see the plaintext** —
only manages access (share / revoke / delete).

There is nothing to “transfer” for control: the organization’s security
owner, via the Custodian, already governs the file even if an AI-powered
service uploaded it.

When `enterprise-custodian-mode=true` is stamped on the account, peer SHARE /
DELETE from ordinary users is rejected. The Custodian routes share, revoke,
and delete. Login needs `license.jwt` with feature `custodian`.

### Policies, graph, and compliance audit

Custodian mode is the control plane for **governance**. Because every share /
revoke / delete goes through the Custodian, the organization can enforce
**who may share which files with whom**.

AltaStata offers a **commercial governance product** for that: policy
evaluation (including automatically from a **policy graph**), allow/deny of
share requests, and a **full audit trail** for **compliance reports** (GDPR,
DORA, AI Act, and similar). The Custodian does **not** see plaintext.

You can also run **your own** program as the Custodian (including Python).
Listen as an organization user with [HOWTO.md](HOWTO.md#events-share--delete).
For the commercial product: `contact@altastata.com`.

### Example — AI-powered service sends an encrypted report

Material produced **inside a confidential container** stays in the AltaStata
fabric; it is not shared as plaintext outside it.

1. The AI-powered service uploads the encrypted JSON to the
   AltaStata-protected cloud. The **Custodian becomes the access manager**.
2. The service asks the Custodian to share it with the organization user
   (human or application).
3. The Custodian checks organization policy (automatically, or via an app
   where the CISO approves) and then grants **read** access to that user.
4. The Custodian can **revoke the AI-powered service’s access** while the
   organization user **keeps** access to the file.

---

## What Enterprise unlocks

| Capability | Community | Enterprise (as granted in the JWT) |
|------------|-----------|--------------------------------------|
| RSA, AES-256-GCM, Python SDK, S3 / gRPC | Yes | Yes |
| Users | ≤5 + one org custodian | JWT `seats` |
| Certificate signing | AltaStata cloud CA, RSA only | **Customer-owned org CA** |
| **PQC** (ML-KEM / Kyber, ML-DSA / Dilithium) | No | Feature `pqc` |
| **HSM / IBM HPCS** | No | Features `hsm`, `hpcs` |
| **Enterprise Custodian mode** | Community custodian identity only | Feature `custodian` |
| **Governance product** (policy graph, compliance audit) | No | Commercial add-on; `contact@altastata.com` |

A commercial license can also include SSO / directory integration and SLA
support — confirm with `contact@altastata.com`.

---

## Python: account files

Community `from_account_dir` / `from_credentials` needs keys and
`*user.properties`.

Enterprise / eval also needs **`license.jwt`** and **`org-ca.pem`** in the
account folder (or in the `account_files` map):

```python
from altastata import AltaStataFunctions

f = AltaStataFunctions.from_upload(
    user_properties,   # *user.properties text
    {
        "private.key": private_key_bytes,
        "license.jwt": license_jwt_bytes,
        "org-ca.pem": org_ca_pem_bytes,
        # PQC / HPCS files as required by key-protection
    },
    password="your-password",
)
```

Do not put the org CA **private** key on ordinary user accounts — only Admin
and the **custodian** account.
