# Python package versioning

PyPI versions use **`1.0.YYYYMMDD.N`** so the wheel name shows which Java/BSL
runtime is bundled, and so same-day wheels can increment without retagging Java.

Java/BSL stays on the **date tag** `vYYYY.MM.DD` because BSL `Change Date` is
tied to that publication date. Do not add `.N` to the Java tag for a Python
rebuild.

| Segment | Meaning |
| --- | --- |
| `1.0` | Product line (unchanged) |
| `YYYYMMDD` | Date of the bundled `sovereign-data-fabric` / mycloud tag `vYYYY.MM.DD` |
| `N` | Wheel build on that Java date (`1` first cut, `2` same-day rebuild) |

Examples:

| Wheel | Bundled Java |
| --- | --- |
| `1.0.20260819.17` | `v2026.08.19` (latest; same-day docs rebuild) |
| `1.0.20260819.2` | `v2026.08.19` (same Java tag, second wheel that day) |
| `1.0.20260819.1` | `v2026.08.19` (first wheel for that Java date) |

Same-day rebuilds only bump `.N`; Java stays on `v2026.08.19`.

`pip install altastata==1.0.20260819.17` is valid [PEP 440](https://peps.python.org/pep-0440/).

Also set `BUNDLED_JAVA_RELEASE` in `altastata/__init__.py` to `YYYY.MM.DD`
(same date, dotted). The PyPI version is for humans; the constant is what
runtime/docs checks.

**Ordering note:** `1.0.YYYYMMDD.N` sorts **above** a bare `1.0.YYYYMMDD`. Keep
using `.N` for the advertised latest. Prefer **yank** over delete so a version
number cannot be reused.

## Release checklist (version only)

1. Java/BSL date tag exists (or is being cut the same day): `vYYYY.MM.DD`.
2. `setup.py` `version=` → `1.0.YYYYMMDD.N`.
3. `BUNDLED_JAVA_RELEASE` → `YYYY.MM.DD`.
4. README / release notes name both the wheel and the Java tag.
