# Python package versioning

PyPI versions use **`1.0.YYYYMMDD`** so the wheel name shows which Java/BSL
runtime is bundled. Same-day rebuilds append **`.N`** only when needed.

| Segment | Meaning |
| --- | --- |
| `1.0` | Product line (unchanged) |
| `YYYYMMDD` | Date of the bundled `sovereign-data-fabric` / mycloud tag `vYYYY.MM.DD` |
| `.N` (optional) | Same-day rebuild (`1`, `2`, …). Omit for the primary cut of that date. |

Examples:

| Wheel | Bundled Java |
| --- | --- |
| `1.0.20260817` | `v2026.08.17` (primary cut) |
| `1.0.20260817.1` | same Java tag, first same-day rebuild |

`pip install altastata==1.0.20260817` is valid [PEP 440](https://peps.python.org/pep-0440/).
Do **not** use `1.0.2026.08.16.1`: PEP 440 drops leading zeros (`08` → `8`).

Also set `BUNDLED_JAVA_RELEASE` in `altastata/__init__.py` to `YYYY.MM.DD`
(same date, dotted). The PyPI version is for humans; the constant is what
runtime/docs checks.

**Ordering note:** `1.0.YYYYMMDD.N` sorts **above** `1.0.YYYYMMDD`. If you
publish a bare date after same-day `.N` wheels, yank the `.N` builds (or keep
`.N` as latest). Prefer cutting the bare date first.

## Last `1.0.6.x` wheels

`1.0.6.16` and earlier stay on PyPI. Do not rename them.
`1.0.20260816.1` sorts after `1.0.6.16` (`20260816 > 6`), so `pip install -U`
works.

## Release checklist (version only)

1. Java/BSL date tag exists (or is being cut the same day): `vYYYY.MM.DD`.
2. `setup.py` `version=` → `1.0.YYYYMMDD` (or `1.0.YYYYMMDD.N` for a rebuild).
3. `BUNDLED_JAVA_RELEASE` → `YYYY.MM.DD`.
4. README / release notes name both the wheel and the Java tag.
