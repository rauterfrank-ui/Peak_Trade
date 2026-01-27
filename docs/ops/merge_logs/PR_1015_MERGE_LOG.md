# PR 1015 — Merge Log — Optional dependencies hardening (ccxt) + gates + docs

> Status: **DRAFT** (GitHub PR created)  
> Target repo: `rauterfrank-ui/Peak_Trade`  
> PR URL: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1015`

## Summary
Make `ccxt` a strictly optional dependency and enforce a dependency-free core import graph via lazy shims, leak scanning, importability gates, and dev-only typechecking.

## Why
Minimal environments (CI/docs/tools) must remain importable without optional provider SDKs. A single top-level import leak (e.g. `ccxt`) can break `import src.data.backend` transitively and block verification/ops workflows.

## Changes
- Optional dependency policy + packaging:
  - `ccxt` removed from core dependencies; added as extra `.[kraken]` in `pyproject.toml`.
  - Documentation updated: optional deps + install hints.
- Import graph hardening:
  - `src/data/__init__.py` no longer imports Kraken/ccxt at import time; lazy symbols via `__getattr__` (PEP 562) with helpful on-demand error.
  - Read-only Kraken OHLCV backend implemented with lazy `ccxt` import; offline deterministic tests.
  - `ccxt` imports moved into `src/data/providers/**` only; core modules use lazy shims/factory loading.
- Enforcement (CI/local):
  - Leak scanner: `scripts/ops/check_optional_deps_leaks.sh` enforces `ccxt` import allowlist.
  - Importability gate: `scripts/ops/check_optional_deps_importability.sh` validates core install vs `.[kraken]`.
  - Workflow: `optional-deps-gate.yml` runs leak scan before importability gate.
- Types (dev-only, not required):
  - Dependency-free `ExchangeClient` Protocol added.
  - `pyright` + `mypy` dev-only workflows added (tolerant baseline configs).
- Docs:
  - New: `docs/architecture/OPTIONAL_DEPENDENCIES_POLICY.md` + linked in architecture index.
  - `docs/DEV_SETUP.md` includes optional deps gates + dev-only typechecking instructions.
  - Exchange guide updated: new SDK deps must live in `providers/**` + lazy shim/factory.

## Verification
- Leak scan: `bash scripts/ops/check_optional_deps_leaks.sh` → PASS
- Importability gate: `bash scripts/ops/check_optional_deps_importability.sh` → PASS
- Unit tests:
  - `pytest -q tests/data/test_optional_deps_imports.py tests/data/test_backend_registry_lazy_import.py` → PASS
  - `pytest -q tests/exchange/test_ccxt_shims_importability.py` → PASS
- Dev-only typecheck:
  - `pip install -e ".[dev]" && mypy --config-file mypy.ini src tests` → PASS
  - `pip install -e ".[dev]" && bash scripts/ops/typecheck_pyright.sh` → PASS

## Risk
LOW — dependency organization + lazy import shims + read-only provider path + CI/dev tooling. No trading/order execution behavior changes.

## Create PR checklist (when ready)
- [ ] Branch exists and is pushed to `origin`
- [ ] `bash scripts/ops/check_optional_deps_leaks.sh` → PASS
- [ ] `bash scripts/ops/check_optional_deps_importability.sh` → PASS
- [ ] `pytest -q` (or targeted suite) → PASS
- [ ] Create PR via `gh pr create ...` and then replace `PR URL: TBD` with the real link

## Operator How-To
- Confirm no optional dep leak:
  - `bash scripts/ops/check_optional_deps_leaks.sh`
- Confirm minimal env importability (core vs extra):
  - `bash scripts/ops/check_optional_deps_importability.sh`
- Install Kraken provider deps:
  - `pip install -e ".[kraken]"` (or `pip install ccxt`)
- Dev-only typecheck:
  - `pip install -e ".[dev]"`
  - `mypy --config-file mypy.ini src tests`
  - `bash scripts/ops/typecheck_pyright.sh`

## References
- Policy doc: `docs/architecture/OPTIONAL_DEPENDENCIES_POLICY.md`
- DEV setup: `docs/DEV_SETUP.md`
