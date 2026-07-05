# CI / Docs Path Consistency Fix Report v1

**Date:** 2026-07-05  
**Scope:** Documentation path normalization + one safe import alignment  
**Branch:** `main` (local, uncommitted)  
**Constraints honored:** No new modules, no architecture redesign, no SSOT/governance edits, no runbook changes.

---

## Summary

Stale documentation references to deferred theory modules, legacy ECM paths, and renamed data-layer files were normalized to match the current repository layout. One script import was aligned to the existing Kraken data API. Full-repo docs token policy and docs reference-target scans pass locally (best effort).

---

## 1. Replaced Paths

| Old reference | New / resolution | Files touched |
|---------------|------------------|---------------|
| `src/theory/stochastics.py` | **DEFERRED_MODULE** + pointers to `src/risk/monte_carlo.py`, `src/experiments/monte_carlo.py` | `src/docs/architecture.md`, `src/docs/nicole_el_karoui_notes.md` |
| `src/theory/pricing.py` | **DEFERRED_MODULE** | `src/docs/architecture.md`, `src/docs/nicole_el_karoui_notes.md` |
| `src/theory/credit.py` | **DEFERRED_MODULE** | `src/docs/nicole_el_karoui_notes.md` |
| `src/features/ecm.py` | Already `src/strategies/ecm.py` in most docs; token encoding fixed in `docs/features/FEHLENDE_FEATURES_PEAK_TRADE.md` | `docs/features/FEHLENDE_FEATURES_PEAK_TRADE.md` |
| `src/data/data_loader.py` | `src/data/loader.py` / `src/data/kraken.fetch_ohlcv_df` | `docs/PEAK_TRADE_OVERVIEW.md` |
| `load_ohlcv_data` (non-existent) | `fetch_ohlcv_df` | `docs/PEAK_TRADE_OVERVIEW.md` |
| `docs/armstrong_notes.md` | `src/docs/armstrong_notes.md` | `src/docs/PEAK_TRADE_PROJECT_SUMMARY.md` (tree + list) |
| `docs/trading_bot_notes.md` | `src/docs/trading_bot_notes.md` | `src/docs/PEAK_TRADE_PROJECT_SUMMARY.md` |
| `docs/Peak_Trade_setup_notes.md` | `src/docs/Peak_Trade_setup_notes.md` | `src/docs/PEAK_TRADE_PROJECT_SUMMARY.md` |
| `docs/llm_workflows.md` | **DEFERRED_DOC** (not in repo; not required by CI) | `src/docs/PEAK_TRADE_PROJECT_SUMMARY.md` |
| `src/data/data_contracts.py` | *(historical)* — canonical module is `src/data/contracts.py` | Not renamed in historical merge logs (ignored by full-scan) |
| `src/data/parquet_cache.py` | *(historical)* — canonical module is `src/data/cache.py` | Not renamed in historical merge logs (ignored by full-scan) |

### Import alignment (Step 2)

| File | Before | After |
|------|--------|-------|
| `scripts/run_risk_stress_report.py` | `from src.data.loader import load_market_data` (missing) | `from src.data.kraken import fetch_ohlcv_df` (exists) |

---

## 2. Deferred Modules (documented, not implemented)

| Module | Status in runtime |
|--------|-------------------|
| `src/theory/stochastics.py` | **DEFERRED_MODULE** — placeholder only (`src/theory/__init__.py`) |
| `src/theory/pricing.py` | **DEFERRED_MODULE** |
| `src/theory/credit.py` | **DEFERRED_MODULE** |
| `src/features/` (Feature-Engine pipeline) | **Deferred placeholder** — ECM math lives in `src/strategies/ecm.py` + `src/strategies/armstrong/` |
| `docs/llm_workflows.md` | **DEFERRED_DOC** — file does not exist |

**Partial overlap (existing, not theory modules):**

- `src/risk/monte_carlo.py`
- `src/experiments/monte_carlo.py`

---

## 3. Unchanged Risky Imports (left intentionally)

| Location | Reason |
|----------|--------|
| `tests/integration/test_kill_switch_e2_safety_guard.py` → `src.live.kill_switch` | Test is wired to `src.live.safety.SafetyGuard` + `KillSwitchBlocked`; kill-switch runtime lives under `src/risk_layer/kill_switch/` with different exception types (`TradingBlockedError`). Changing imports would alter test semantics — **skipped per “if uncertain → leave unchanged”**. |
| Historical ops/merge-log docs referencing `data_contracts.py`, `parquet_cache.py`, `data_loader.py` | Point-in-time records; excluded from full-scan via `DOCS_REFERENCE_TARGETS_IGNORE.txt` patterns. **Not edited** (runbook/historical scope). |

---

## 4. CI Consistency Verification (local, best effort)

| Gate | Command | Result |
|------|---------|--------|
| Docs reference targets (full scan) | `bash scripts/ops/verify_docs_reference_targets.sh` | ✅ PASS — 0 missing targets |
| Docs reference targets trend | `bash scripts/ops/verify_docs_reference_targets_trend.sh --verbose` | ✅ PASS |
| Docs token policy (all files) | `python3 scripts/ops/validate_docs_token_policy.py --all` | ✅ PASS — 2217 files |
| Python import AST scan (prior audit) | No hard broken imports to deferred theory/feature ECM paths | ✅ unchanged |

**Note:** PR gates (`docs-token-policy-gate`, `docs-reference-targets-gate`) run on **committed** diffs vs. base; this report reflects working-tree fixes ready for commit.

---

## 5. Files Modified

- `src/docs/architecture.md`
- `src/docs/nicole_el_karoui_notes.md`
- `src/docs/PEAK_TRADE_PROJECT_SUMMARY.md`
- `docs/PEAK_TRADE_OVERVIEW.md`
- `docs/features/FEHLENDE_FEATURES_PEAK_TRADE.md`
- `scripts/run_risk_stress_report.py`
- `docs/audit/ci_docs_fix_report_v1.md` *(this report)*

---

## 6. Explicitly Out of Scope (not done)

- No new theory modules created
- No `src/features/ecm.py` reintroduced
- No changes under `docs/governance/**`
- No runbook edits
- No SSOT / governance system changes
- No kill-switch test refactor

---

**Verdict:** Documentation paths and token policy are aligned with current repo state; one safe data import fixed. CI doc gates should be green after commit of these changes (best effort, local verification only).
