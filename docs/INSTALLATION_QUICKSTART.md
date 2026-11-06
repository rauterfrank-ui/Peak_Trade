# Peak_Trade – Installation Quickstart

**Purpose:** Current entry point for installation, bootstrap, and first verification  
**Target Audience:** New checkouts, onboarding, setup verification

```text
DOCUMENT_ROLE=CURRENT_INSTALL_NAVIGATION
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
ORDERS_ALLOWED=false
```

This page does **not** authorize Live, Testnet, orders, credentials, or capital movement.

---

## Current install authority

Install and local Python runtime are defined by:

1. [`README.md`](../README.md) — Schnelleinstieg
2. [`GETTING_STARTED.md`](./GETTING_STARTED.md) — first-hour onboarding
3. [`DEV_SETUP.md`](./DEV_SETUP.md) — developer environment
4. [`PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md`](./runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md) — launcher / interpreter contract
5. [`PEAK_TRADE_WORKTREE_PYTHON_ENVIRONMENT_BOOTSTRAP_CONTRACT_V1.md`](./runtime/PEAK_TRADE_WORKTREE_PYTHON_ENVIRONMENT_BOOTSTRAP_CONTRACT_V1.md) — per-checkout `.venv`

Canonical launcher: `scripts/pt`  
Canonical bootstrap: `scripts/pt-bootstrap`  
Canonical interpreter: repository `.venv` Python (never PATH `python` / `python3`)

Do **not** use PATH `python` / `python3`, `python -m venv`, or venv activation as the supported runtime.

A 2026-01-12 installation/roadmap snapshot exists only as historical archive:

[`docs/ops/_archive/installation_roadmap/2026-01-12/INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12_ORIGINAL.md`](ops/_archive/installation_roadmap/2026-01-12/INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12_ORIGINAL.md)

That snapshot is **not** current install, bootstrap, or product-roadmap authority.

---

## Requirements

- **Python floor:** `requires-python = ">=3.10"` in `pyproject.toml`. Recommended local interpreter: repository `.venv` (CPython 3.11.x) via `scripts/pt-bootstrap`.
- **Git**
- **uv** (used by `scripts/pt-bootstrap`)
- **Disk:** budget on the order of 10 GB for data, reports, logs, and local caches
- **OS:** macOS (typical), Linux, or Windows via WSL2
- Optional: exchange credentials only when a separate Owner-authorized network session requires them (not part of install)

---

## Zero to ready

```bash
# 1. Clone
git clone <REPO_URL> Peak_Trade
cd Peak_Trade

# 2. Bootstrap (once per checkout / worktree)
./scripts/pt-bootstrap

# 3. Canonical runtime check
./scripts/pt runtime-check

# 4. Smoke / tests
./scripts/pt -m pytest -m smoke -q
./scripts/pt -m pytest -q

# 5. Optional first backtest
./scripts/pt scripts/run_strategy_from_config.py --strategy ma_crossover --symbol BTC/USDT
```

Activation of the venv is not required. The launcher selects the checkout `.venv` interpreter.

Worktrees: each checkout owns a real `.venv` via `scripts/pt-bootstrap`. Do not symlink another worktree `.venv`.

Optional Web-UI extra:

```bash
uv sync --extra web
./scripts/pt -m pytest -m web
```

---

## Pathways

### New users

1. This page
2. [`README.md`](../README.md) Schnelleinstieg
3. [`GETTING_STARTED.md`](./GETTING_STARTED.md)

### Developers

1. [`DEV_SETUP.md`](./DEV_SETUP.md)
2. [`CLI_CHEATSHEET.md`](./CLI_CHEATSHEET.md)
3. [`STRATEGY_DEV_GUIDE.md`](./STRATEGY_DEV_GUIDE.md)

### Operators

1. [`docs/ops/README.md`](./ops/README.md)
2. [`docs/ops/RUNBOOK_INDEX.md`](./ops/RUNBOOK_INDEX.md)
3. [`WORKFLOW_FRONTDOOR.md`](./WORKFLOW_FRONTDOOR.md)
4. [`LIVE_OPERATIONAL_RUNBOOKS.md`](./LIVE_OPERATIONAL_RUNBOOKS.md) (non-authorizing)

---

## Governance / Live boundary

Installation does not enable Live, Testnet, or orders.

Current semantic authority: [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](./runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md)

Safety / policy (non-authorizing):

- [`SAFETY_POLICY_TESTNET_AND_LIVE.md`](./SAFETY_POLICY_TESTNET_AND_LIVE.md)
- [`docs/risk/KILL_SWITCH.md`](./risk/KILL_SWITCH.md)
- [`docs/ops/KILL_SWITCH_RUNBOOK.md`](./ops/KILL_SWITCH_RUNBOOK.md)

---

## If bootstrap fails

1. Confirm `pyproject.toml`, `uv.lock`, and `scripts/pt` exist in this checkout
2. Re-run `scripts/pt-bootstrap` (it will not unlink a foreign `.venv` symlink)
3. Re-run `scripts&#47;pt runtime-check`
4. Do not fall back to PATH `python3` or `PYTHONPATH`

---

## Related

- [`docs/README.md`](./README.md) — docs topic index
- [`docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`](./governance/PEAK_TRADE_MAP_OF_TRUTH.md) — navigation only
- Historical install snapshot (archive): [`docs/ops/_archive/installation_roadmap/2026-01-12/README.md`](ops/_archive/installation_roadmap/2026-01-12/README.md)
