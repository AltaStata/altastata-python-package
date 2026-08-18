# Enterprise mode

AltaStata has **two access-control and sharing models**. Day-to-day Python
operations are the same ([HOWTO.md](HOWTO.md)); this page is **who governs
access** and **which crypto / CA features** a commercial license unlocks.

Account files and CLI: [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md).
Admin provisioning:
[ADMIN_TOOL_GUIDE](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md).
Full Enterprise write-up (CISO / egress):
[ENTERPRISE.md](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ENTERPRISE.md).

---

## Who controls a shared file

When two organizations exchange files in the usual way, the sender **loses
control** once a copy leaves their boundary. With AltaStata, whoever puts a
**file** into the fabric **keeps cryptographic control of that file** after
sharing it across organizational boundaries. They know **which humans or
applications** — in their own organization or a partner’s — have access.

### Community mode

Whoever **uploads** the file is the **owner**. They share with readers and
control who has access. A reader can open the file and **observe** who has
access, but cannot grant or revoke.

RSA only, up to **5 users** plus **one org custodian**, on the entity’s **own**
cloud or internal storage.

### Enterprise (CISO / security as access manager)

The access manager is **not** the uploader. It is CISO / security, acting
through a **Custodian**. All sharing goes through the Custodian.

CISO can **observe** who has access and **fully manage** it (share / revoke /
delete) — including across partners — **without plaintext**. The Custodian
never decrypts the file.

Runtime stamp: `enterprise-custodian-mode=true`. Login needs `license.jwt`
with feature `custodian`. Peer SHARE / DELETE from ordinary users is rejected;
the Custodian routes share, revoke, and delete.

### Example — Bob shares a file with Alice

1. Bob uploads the file. He is **not** the access manager: CISO / security
   already is, via the Custodian.
2. Bob asks the Custodian to share it with Alice (human or application).
3. The Custodian checks organization policy (automatically, or via an app
   where the CISO approves) and then grants **read** access to Alice.
4. The Custodian can **revoke Bob’s access** while Alice **keeps** access to
   the file — or revoke Alice while Bob keeps it.

### Policies, graph, and compliance audit

Custodian mode is the governance control plane: every share / revoke / delete
goes through it, so the org can enforce **who may share which files with whom**.

AltaStata’s commercial product adds policy evaluation (including from a
**policy graph**), allow/deny of share requests, and a **compliance audit trail**
(GDPR, DORA, AI Act, and similar). The Custodian never sees plaintext.

You can also run **your own** program as the Custodian (including Python).
Listen as an organization user with [HOWTO.md](HOWTO.md#events-share--delete).
Evaluation: `contact@altastata.com`.

---

## What Enterprise unlocks

| Capability | Community | Enterprise (as granted in the JWT) |
|------------|-----------|--------------------------------------|
| RSA, AES-256-GCM, Python SDK, S3 / gRPC | Yes | Yes |
| Users | ≤5 + one org custodian | JWT `seats` (`0` = unlimited) |
| Certificate signing | AltaStata cloud CA, RSA only | **Customer-owned org CA**. No `/sign` fallback |
| **PQC** (ML-KEM / Kyber, ML-DSA / Dilithium) | No | Feature `pqc` |
| **HSM / IBM HPCS** (private key stays in the HSM) | No | Features `hsm`, `hpcs` |
| **Enterprise Custodian mode** (Custodian is access manager; no plaintext) | Community custodian identity only | Feature `custodian` |
| **Governance product** (policy graph, compliance audit) | No | Commercial add-on; `contact@altastata.com` |
| Runtime files beside keys | `*user.properties` | Also `license.jwt` and `org-ca.pem` |

A commercial license can also include **SSO / directory integration** and
**SLA support** — confirm what your JWT and contract actually grant.
`contact@altastata.com`.

Evaluation / PoC without a commercial contract is Community-level (RSA)
unless AltaStata issues a **trial license** for Enterprise features.

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
