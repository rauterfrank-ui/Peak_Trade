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
| `src&#47;theory&#47;stochastics.py` | **DEFERRED_MODULE** + pointers to `src&#47;risk&#47;monte_carlo.py`, `src&#47;experiments&#47;monte_carlo.py` | `src&#47;docs&#47;architecture.md`, `src&#47;docs&#47;nicole_el_karoui_notes.md` | <!-- pt:ref-target-ignore -->
| `src&#47;theory&#47;pricing.py` | **DEFERRED_MODULE** | `src&#47;docs&#47;architecture.md`, `src&#47;docs&#47;nicole_el_karoui_notes.md` | <!-- pt:ref-target-ignore -->
| `src&#47;theory&#47;credit.py` | **DEFERRED_MODULE** | `src&#47;docs&#47;nicole_el_karoui_notes.md` | <!-- pt:ref-target-ignore -->
| `src&#47;features&#47;ecm.py` | Already `src&#47;strategies&#47;ecm.py` in most docs; token encoding fixed in `docs&#47;features&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` | `docs&#47;features&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` | <!-- pt:ref-target-ignore -->
| `src&#47;data&#47;data_loader.py` | `src&#47;data&#47;loader.py` / `src&#47;data&#47;kraken.py` (`fetch_ohlcv_df`) | `docs&#47;PEAK_TRADE_OVERVIEW.md` | <!-- pt:ref-target-ignore -->
| `load_ohlcv_data` (non-existent) | `fetch_ohlcv_df` | `docs&#47;PEAK_TRADE_OVERVIEW.md` |
| `docs&#47;armstrong_notes.md` | `src&#47;docs&#47;armstrong_notes.md` | `src&#47;docs&#47;PEAK_TRADE_PROJECT_SUMMARY.md` (tree + list) | <!-- pt:ref-target-ignore -->
| `docs&#47;trading_bot_notes.md` | `src&#47;docs&#47;trading_bot_notes.md` | `src&#47;docs&#47;PEAK_TRADE_PROJECT_SUMMARY.md` | <!-- pt:ref-target-ignore -->
| `docs&#47;Peak_Trade_setup_notes.md` | `src&#47;docs&#47;Peak_Trade_setup_notes.md` | `src&#47;docs&#47;PEAK_TRADE_PROJECT_SUMMARY.md` | <!-- pt:ref-target-ignore -->
| `docs&#47;llm_workflows.md` | **DEFERRED_DOC** (not in repo; not required by CI) | `src&#47;docs&#47;PEAK_TRADE_PROJECT_SUMMARY.md` | <!-- pt:ref-target-ignore -->
| `src&#47;data&#47;data_contracts.py` | *(historical)* — canonical module is `src&#47;data&#47;contracts.py` | Not renamed in historical merge logs (ignored by full-scan) | <!-- pt:ref-target-ignore -->
| `src&#47;data&#47;parquet_cache.py` | *(historical)* — canonical module is `src&#47;data&#47;cache.py` | Not renamed in historical merge logs (ignored by full-scan) | <!-- pt:ref-target-ignore -->

### Import alignment (Step 2)

| File | Before | After |
|------|--------|-------|
| `scripts&#47;run_risk_stress_report.py` | `from src.data.loader import load_market_data` (missing) | `from src.data.kraken import fetch_ohlcv_df` (exists) |

---

## 2. Deferred Modules (documented, not implemented)

| Module | Status in runtime |
|--------|-------------------|
| `src&#47;theory&#47;stochastics.py` | **DEFERRED_MODULE** — placeholder only (`src&#47;theory&#47;__init__.py`) | <!-- pt:ref-target-ignore -->
| `src&#47;theory&#47;pricing.py` | **DEFERRED_MODULE** | <!-- pt:ref-target-ignore -->
| `src&#47;theory&#47;credit.py` | **DEFERRED_MODULE** | <!-- pt:ref-target-ignore -->
| `src&#47;features&#47;` (Feature-Engine pipeline) | **Deferred placeholder** — ECM math lives in `src&#47;strategies&#47;ecm.py` + `src&#47;strategies&#47;armstrong&#47;` | <!-- pt:ref-target-ignore -->
| `docs&#47;llm_workflows.md` | **DEFERRED_DOC** — file does not exist | <!-- pt:ref-target-ignore -->

**Partial overlap (existing, not theory modules):**

- `src&#47;risk&#47;monte_carlo.py`
- `src&#47;experiments&#47;monte_carlo.py`

---

## 3. Unchanged Risky Imports (left intentionally)

| Location | Reason |
|----------|--------|
| `tests&#47;integration&#47;test_kill_switch_e2_safety_guard.py` → `src.live.kill_switch` | Test is wired to `src.live.safety.SafetyGuard` + `KillSwitchBlocked`; kill-switch runtime lives under `src&#47;risk_layer&#47;kill_switch&#47;` with different exception types (`TradingBlockedError`). Changing imports would alter test semantics — **skipped per “if uncertain → leave unchanged”**. |
| Historical ops/merge-log docs referencing `data_contracts.py`, `parquet_cache.py`, `data_loader.py` | Point-in-time records; excluded from full-scan via `DOCS_REFERENCE_TARGETS_IGNORE.txt` patterns. **Not edited** (runbook/historical scope). |

---

## 4. CI Consistency Verification (local, best effort)

| Gate | Command | Result |
|------|---------|--------|
| Docs reference targets (full scan) | `bash scripts&#47;ops&#47;verify_docs_reference_targets.sh` | ✅ PASS — 0 missing targets |
| Docs reference targets trend | `bash scripts&#47;ops&#47;verify_docs_reference_targets_trend.sh --verbose` | ✅ PASS |
| Docs token policy (all files) | `python3 scripts&#47;ops&#47;validate_docs_token_policy.py --all` | ✅ PASS — 2217 files |
| Python import AST scan (prior audit) | No hard broken imports to deferred theory/feature ECM paths | ✅ unchanged |

**Note:** PR gates (`docs-token-policy-gate`, `docs-reference-targets-gate`) run on **committed** diffs vs. base; this report reflects working-tree fixes ready for commit.

---

## 5. Files Modified

- `src&#47;docs&#47;architecture.md`
- `src&#47;docs&#47;nicole_el_karoui_notes.md`
- `src&#47;docs&#47;PEAK_TRADE_PROJECT_SUMMARY.md`
- `docs&#47;PEAK_TRADE_OVERVIEW.md`
- `docs&#47;features&#47;FEHLENDE_FEATURES_PEAK_TRADE.md`
- `scripts&#47;run_risk_stress_report.py`
- `docs&#47;audit&#47;ci_docs_fix_report_v1.md` *(this report)*

---

## 6. Explicitly Out of Scope (not done)

- No new theory modules created
- No `src&#47;features&#47;ecm.py` reintroduced <!-- pt:ref-target-ignore -->
- No changes under `docs&#47;governance&#47;**`
- No runbook edits
- No SSOT / governance system changes
- No kill-switch test refactor

---

**Verdict:** Documentation paths and token policy are aligned with current repo state; one safe data import fixed. CI doc gates should be green after commit of these changes (best effort, local verification only).
