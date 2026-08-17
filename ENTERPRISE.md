# Enterprise mode

AltaStata has **two access-control and sharing models**. Day-to-day Python
operations are the same ([HOWTO.md](HOWTO.md)); this page is **who governs
access** and **which crypto / CA features** a commercial license unlocks.

Account files and CLI: [USER_SETUP_GUIDE.md](USER_SETUP_GUIDE.md).
Admin provisioning (Java tree):
[ADMIN_TOOL_GUIDE](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ADMIN_TOOL_GUIDE.md).
Full Enterprise write-up on the BSL tree:
[ENTERPRISE.md](https://github.com/AltaStata/sovereign-data-fabric/blob/main/docs/guides/ENTERPRISE.md).

---

## Who controls a shared file

When two organizations exchange files in the usual way, the sender **loses
control** once a copy leaves their boundary. With AltaStata, a user who puts a
**file** into the fabric **keeps cryptographic control of that file** even
after sharing it across organizational boundaries. They know **which humans
or applications** — in their own organization or a partner’s — have access.

**Bob** puts a file in AltaStata and wants to **share access** with **Alice**
(another user: a person or an application). The rest of this page is who
**owns** that file and who may **grant or revoke** access.

### Community mode

Whoever **uploads** the file is the **owner of that file**. The owner shares
with readers and controls who has access.

Bob stays the owner. Alice is a **reader**: she can open the file and
**observe** who has access, but she does not grant or revoke sharing.

### Enterprise (CISO / security as access manager)

The access manager is **not** the user who created the file. It is the
organization’s **CISO / security team**, acting through a special
**Custodian** user. All sharing goes through the Custodian.

CISO / security can **observe** who has access and **fully manage** it
(share / revoke / delete) — including across partner organizations —
without having access to plaintext. The Custodian only manages access;
it never decrypts the file.

When `enterprise-custodian-mode=true` is stamped on the account, peer SHARE /
DELETE from ordinary users is rejected. The Custodian routes share, revoke,
and delete. Login needs `license.jwt` with feature `custodian`.

### Example — Bob shares a file with Alice

1. Bob uploads the file. He is **not** the access manager: CISO / security
   already is, via the Custodian.
2. Bob asks the Custodian to share it with Alice (human or application).
3. The Custodian checks organization policy (automatically, or via an app
   where the CISO approves) and then grants **read** access to Alice.
4. The Custodian can **revoke Bob’s access** while Alice **keeps** the file —
   or revoke Alice while Bob keeps it.


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
