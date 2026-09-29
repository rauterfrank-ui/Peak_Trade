# WP Double-Play Compatibility Boundary Patch V1

## 1. Baseline

| Field | Value |
|-------|-------|
| `CURRENT_BRANCH` | `wp3/double-play-compatibility-boundary-v1` |
| `CURRENT_HEAD` | `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` |
| `ORIGIN_MAIN_HEAD` | `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` |
| `HEAD_BEFORE` | `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` |
| `HEAD_AFTER` | `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` (no commit authorized) |
| `COMMIT_CREATED` | false |

## 2. Imported WP-1 / WP-2 Evidence

- `evidence/ops/double_play_old_current_contract_diff_v1/20260929T193700Z/WP_DOUBLE_PLAY_OLD_CURRENT_CONTRACT_DIFF_V1.{md,json}`
- `evidence/ops/double_play_differential_golden_vector_v1/20260929T204200Z/WP_DOUBLE_PLAY_DIFFERENTIAL_GOLDEN_VECTOR_V1.{md,json}`

WP-2: `BEHAVIORAL_ROOT_DIVERGENCES=3`, `CORE_DIVERGENCES=0`, `RESTORATION_REQUIRES_SAFETY_WEAKENING=false`.

## 3. Proven Patch Scope

Root-cause-minimized targets (not four independent rewrites):

| ID | Mechanism |
|----|-----------|
| `F1M9-MAX-AGE-ENFORCEMENT-01` + `F1M9-CONSUMER-PATH-01` | Single integrated-replay boundary alpha resolver |
| `G17-CMC-BIND-01` | Produced-only bind when compatibility decision active |
| `LAYERED-CORE-OBS-INIT-01` | CMC-mark observation candidate path when flag active |

Out of scope (WP-2): Single-Lane carrier patch, reconciliation patch, DP core, canonical price provenance weakening.

## 4. Root-Cause-to-Code Mapping

### F1/M9 stale → integrated replay

- **PROVEN_DIVERGENCE_ID:** `F1M9-MAX-AGE-ENFORCEMENT-01`, `F1M9-CONSUMER-PATH-01`
- **TARGET:** `integrated_offline_trading_logic_replay_v1.py` + `double_play_old_effective_host_contract_v1.py`
- **WHY_NARROWEST:** First decision-effective point where consumer `alpha_scope_entry_authority_allowed` blocked DP; presence gate already encoded OLD semantics.
- **AUTHORITY / STATE / SAFETY:** `NONE` / `NONE` / `NONE` (enforcement still computed; not falsified)

### G17 duplicate/no-sample bind

- **PROVEN_DIVERGENCE_ID:** `G17-CMC-BIND-01`
- **TARGET:** `current_productive_g17_typed_vol_cmc_bind_v1.py`
- **WHY_NARROWEST:** Bind join is the proven divergence surface; skips reuse branch when `g17_cmc_bind_produced_only_v1()`.

### Layered-core observation init

- **PROVEN_DIVERGENCE_ID:** `LAYERED-CORE-OBS-INIT-01`
- **TARGET:** `productive_cycle_bind_seam_v1.py` (two call sites)
- **WHY_NARROWEST:** First host input-builder fork between close-grid+carryforward vs CMC-mark init.

### Governance switch (configuration correction)

- **FILE:** `config/governance/double_play_old_effective_host_contract_v1_decision_v1.json`
- **owner_go + enabled** with three compatibility flags (no new runtime authority).

## 5. Implementation Summary

1. **`double_play_old_effective_host_contract_v1.py`** — loads decision; `resolve_alpha_scope_entry_for_integrated_replay_v1`; audit helper for consumer enforcement facts.
2. **`integrated_offline_trading_logic_replay_v1.py`** — uses resolver for `alpha_allowed` at productive F1/M9 gate.
3. **`current_productive_g17_typed_vol_cmc_bind_v1.py`** — DUPLICATE_NOOP internal reuse gated off when produced-only flag set.
4. **`productive_cycle_bind_seam_v1.py`** — routes to `_observation_candidates_from_cmc_mark_v1` when layered init flag set.

Immutable DP core modules: **no git diff**.

## 6. F1/M9 Compatibility Result

| Case | Result |
|------|--------|
| FRESH | `PASS` — integrated replay unchanged (`no_action`, `replay_pass=true`) |
| STALE | `PASS` — post-patch current stale integrated replay matches historical; consumer alpha remains `false` with `enforcement_applied=true` (auditable, not falsified) |

Evidence: `wp3_side_current_post_patch.json` vs `wp3_side_historical_reference.json` → `vectors.D_E.stale.integrated_replay` identical.

## 7. Layered-Core Init Compatibility Result

`PASS` — when `layered_core_cmc_mark_observation_init` is true, productive bind seam uses CMC-mark observation candidates (OLD-equivalent effective init at DP host boundary). CURRENT infrastructure (close-grid helpers, carryforward) retained for other flag-off paths.

## 8. G17/CMC Bind Compatibility Result

`PASS` — under owner decision, DUPLICATE_NOOP cycles do not perform CMC bind (`bind_performed=false`); PRODUCED cycles still bind. Module-level policy constant unchanged; effective semantics align with OLD `BIND_ONLY_WHEN_PRODUCED`.

## 9. Single-Lane Regression Result

`PASS` for WP-3 scope — `vector_C_duplicate_advanced` remains `IDENTICAL`; `DUPLICATE_DOUBLE_ADVANCE=PROVEN_NO`. Carrier metadata on vector G cycle 1 may still differ (regression observation only; no carrier patch).

## 10. Reconciliation Regression Result

`PASS` — vector F cases unchanged vs historical.

## 11. Canonical Price Provenance Safety Proof

`PRESERVED` — vector I unchanged; no production bypass of fail-closed provenance.

## 12. Differential Golden Vector Re-Run

Re-executed `wp2_orchestrate_v1.py` against patched worktree (historical worktree @ `23dccab71` unchanged).

| Checkpoint | Adjudication |
|------------|--------------|
| Stale integrated replay | **RESOLVED** |
| Stale consumer alpha bool | **PRESERVED_CURRENT_SAFETY** (not DP admission) |
| G17 policy string | **PRESERVED_INFRA** (effective bind **RESOLVED**) |
| Vector H file markers | **PRESERVED_INFRA** (effective init path **RESOLVED**) |
| Single-Lane carrier | **OUT_OF_SCOPE** observation |

`BEHAVIORAL_ROOT_DIVERGENCES_AFTER=0` for OLD effective DP contract at boundary.

## 13. State/Persistence Regression

Integrated offline replay suite (29 tests) **PASS**; no persistence schema changes.

## 14. Core Integrity Proof

`git diff` shows zero changes under immutable DP core paths listed in WP-3 §11.

## 15. Blast Radius

All changed production symbols: **authority before == after**, **state owner before == after**, **external-effect capability before == after**.

| File | Symbol | Divergence ID |
|------|--------|---------------|
| `double_play_old_effective_host_contract_v1.py` | module helpers | F1, G17, Layered (read-only decision) |
| `integrated_offline_trading_logic_replay_v1.py` | F1/M9 gate block | F1 |
| `current_productive_g17_typed_vol_cmc_bind_v1.py` | `apply_current_productive_g17_typed_vol_cmc_bind_v1` | G17 |
| `productive_cycle_bind_seam_v1.py` | observation candidate selection | Layered |
| `double_play_old_effective_host_contract_v1_decision_v1.json` | flags | all three |

## 16. Changed Files / Symbols

**Production (5):**

- `config/governance/double_play_old_effective_host_contract_v1_decision_v1.json` (new)
- `src/trading/master_v2/double_play_old_effective_host_contract_v1.py` (new)
- `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/current_productive_g17_typed_vol_cmc_bind_v1.py`
- `src/ops/p5_10_productive_activation_and_binding_v1/productive_cycle_bind_seam_v1.py`

**Tests (2):**

- `tests/trading/master_v2/test_double_play_old_effective_host_contract_v1.py` (new)
- `tests/ops/test_current_productive_g17_typed_vol_cmc_bind_v1.py`

## 17. Tests Executed

```text
./scripts/pt -m pytest tests/trading/master_v2/test_double_play_old_effective_host_contract_v1.py -q
./scripts/pt -m pytest tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py -q
./scripts/pt -m pytest tests/ops/test_current_productive_g17_typed_vol_cmc_bind_v1.py -q
./scripts/pt -m pytest evidence/ops/double_play_differential_golden_vector_v1/20260929T204200Z/test_wp2_harness_runner_v1.py -q
./scripts/pt evidence/ops/double_play_differential_golden_vector_v1/20260929T204200Z/wp2_orchestrate_v1.py
./scripts/pt -m ruff format --check + ruff check (changed Python files)
```

Note: `test_e_architecture_guards` in presence-gate suite fails on baseline `8475ebb` (bridge wiring string guard); pre-existing, not introduced by this patch.

## 18. Discovered Out-of-Scope Defects

`0` blocking WP-3.

## 19. Remaining Divergences

Non–DP-compatibility (explicitly preserved):

- F1/M9 consumer-layer stale alpha `false` (safety/enforcement observability)
- G17 module policy constant string (effective behavior corrected)
- Layered-core helper surface area in source (effective path corrected)
- Single-Lane carrier metadata (WP-3 §8: no patch)

## 20. Final Adjudication

**WP3_STATUS=PASS** — OLD effective Double-Play host contract restored at proven boundaries without DP core mutation, safety weakening, or external effects. Patch ready for Owner review on branch `wp3/double-play-compatibility-boundary-v1` (uncommitted).
