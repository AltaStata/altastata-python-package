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
| `1.0.20260819.3` | `v2026.08.19` |
| `1.0.20260819.2` | `v2026.08.19` |
| `1.0.20260819.1` | `v2026.08.19` |
| `1.0.20260817.1` | `v2026.08.17` |
| `1.0.20260817.2` | same Java tag, second wheel that day |

`pip install altastata==1.0.20260819.3` is valid [PEP 440](https://peps.python.org/pep-0440/).
Do **not** use `1.0.2026.08.16.1`: PEP 440 drops leading zeros (`08` → `8`).

Also set `BUNDLED_JAVA_RELEASE` in `altastata/__init__.py` to `YYYY.MM.DD`
(same date, dotted). The PyPI version is for humans; the constant is what
runtime/docs checks.

**Ordering note:** `1.0.YYYYMMDD.N` sorts **above** a bare `1.0.YYYYMMDD`. Keep
using `.N` for the advertised latest.

## Last `1.0.6.x` wheels

The last `1.0.6.x` line was `1.0.6.16`. Those versions are **no longer on
PyPI** (deleted, not yanked — the same numbers cannot be re-uploaded). Install
the current `1.0.YYYYMMDD.N` (`pip install -U altastata`). Do not pin
`1.0.6.x`. Going forward, **yank** a wheel instead of deleting it.

## Release checklist (version only)

1. Java/BSL date tag exists (or is being cut the same day): `vYYYY.MM.DD`.
2. `setup.py` `version=` → `1.0.YYYYMMDD.N`.
3. `BUNDLED_JAVA_RELEASE` → `YYYY.MM.DD`.
4. README / release notes name both the wheel and the Java tag.
