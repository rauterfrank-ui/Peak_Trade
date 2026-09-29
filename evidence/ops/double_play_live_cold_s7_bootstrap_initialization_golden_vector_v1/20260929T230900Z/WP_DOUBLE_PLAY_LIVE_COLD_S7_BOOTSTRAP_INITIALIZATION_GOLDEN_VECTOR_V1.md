# WP — LIVE COLD S7 BOOTSTRAP INITIALIZATION GOLDEN VECTOR V1

**MODE:** READ_ONLY_RUNTIME_DIFFERENTIAL_GOLDEN_VECTOR  
**BASELINE:** `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` @ `wp3/double-play-compatibility-boundary-v1`  
**Worktree:** WP-3 + ROOT_WIRING_01 uncommitted (unchanged by this WP)

## Executive summary

After ROOT_WIRING_01 closed `BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED`, live cold bootstrap reaches S7 compose but fails at **layered episode store bootstrap** with `INITIALIZATION_INCOMPLETE`. The addressing join **propagates** the failure; it is **not** the semantic root.

**Root cause (proven):** WP-3 enables `_observation_candidates_from_cmc_mark_v1` in `ensure_productive_layered_core_episode_store_v1`, producing two **DISTINCT** observations with the **same** CMC mark at `t-60` and `t`. Layered init L3 requires **BULL or BEAR** on a DISTINCT acceptance (`durable_state_v1` loop). First DISTINCT is **NEUTRAL** (first observation); second DISTINCT with unchanged mark is **NEUTRAL** → no L4/L5 → `INITIALIZATION_INCOMPLETE`.

**Live vs forensic E2E:** Post-patch E2E `enter_long` uses `run_current_productive_master_v2_runtime_cycle_v1` and **does not invoke** `ensure_productive_layered_core_episode_store_v1` (0 calls traced). Live cold path uses `bootstrap_s8_lane_via_s7_compose_v1` → `compose_occupied_lane_mv2_dp_durable_cycle_v1` → **always hits** `ensure_productive` when outgoing cursor carries scope and store is absent.

**Historical (`23dccab`):** `ensure_productive` built observations from **finalized closes only** (no WP-3 CMC branch) → **DIFFERENT_WIRING**.

## Failure site (code-proven)

| Item | Value |
|------|--------|
| Exception string | `NakedLayeredCoreDurableStateError: INITIALIZATION_INCOMPLETE` |
| Raised in | `initialize_naked_layered_core_episode_v1` |
| File | `src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/durable_state_v1.py` |
| Branch | `if nullline is None or regime_state is None:` (after L1–L5 init loop) |
| Wrapped by | `ensure_productive_layered_core_episode_store_v1` → `(f"layered_core_bootstrap_init_fail_closed:{exc}",)` |
| Join surface | `compose_occupied_lane_mv2_dp_durable_cycle_v1` → `_fail(MISMATCHED_LANE_STATE, …)` |

## Runtime reproduction (consumed)

No new live GET run required; identical failure captured in:

`evidence/ops/double_play_root_wiring_01_patch_golden_vector_reproof_v1/20260929T221500Z/runtime/run_stdout.json`

- Instrument: `0G-USDT-SWAP`, mark snapshot `0.3283` (`runtime/wp4_natural_enter_pre_external_v1/20260929T221500Z/productivity/mark_prices_by_native_id_v1.json`)
- POST=0, productive cycles=0

## Causal isolation (read-only)

See `initialization_causal_isolation.json`:

| Test | Init result |
|------|-------------|
| BASELINE_LIVE_CMC_WP3 | `INITIALIZATION_INCOMPLETE` |
| SUBSTITUTE_CLOSE_GRID_ONLY | `INITIALIZED` |
| SUBSTITUTE_VARIED_MARKS_ON_CMC_TIMES | `INITIALIZED` |

**MINIMAL_CAUSAL_INPUT_SET:** `INIT_OBS_BUILDER_LIVE` (WP-3 CMC static mark pair for layered init observations in `ensure_productive`).

## Artifacts

- `initialization_contract_matrix.json`
- `live_vs_forensic_success_diff.json`
- `initialization_causal_isolation.json`
- `initialization_root_cause_graph.json`
- `s7_bootstrap_initialization_forensic_harness_v1.py`
- `WP_DOUBLE_PLAY_LIVE_COLD_S7_BOOTSTRAP_INITIALIZATION_GOLDEN_VECTOR_V1.json`

## Minimal patch plan (NOT IMPLEMENTED)

| Field | Value |
|-------|--------|
| ROOT_ID | `INIT_ROOT_01_WP3_CMC_STATIC_MARK_L3_INCOMPATIBLE` |
| Surface | `ensure_productive_layered_core_episode_store_v1` (+ symmetric `prepare_productive_layered_core_replay_bind_v1` if same builder) |
| Producer | `_observation_candidates_from_cmc_mark_v1` |
| Consumer | `initialize_naked_layered_core_episode_v1` / L3 gate |
| Expected | Two initialization observation marks that yield L3 BULL or BEAR while preserving CMC authority for mechanical `M_t` |
| Observed | Identical CMC `M_t` at synthetic `t-60`/`t` grid → L3 NEUTRAL/NEUTRAL |
| Minimal correction | Re-bind initialization observation marks to **decision-effective distinct values already available at cold bootstrap** (e.g. last two `finalized_closes` on the 1m grid) **without** weakening canonical price provenance on mechanical/CMC bind; or proven prior CMC mark at `t-60` from GET history if a canonical producer exists |
| Likely files | `productive_cycle_bind_seam_v1.py` only (bounded) |
| Tests | `test_productive_layered_core_episode_store_bootstrap_v1`, WP-3 layered init, cold S7 compose regression with WP-3 flag ON |
| Blast radius | Cold S7 bootstrap + first episode persist only |
| Safety | No POST; preserve provenance validators |
| Authority / state | No ownership move |

**Preference order:** (1) wire existing finalized-close marks into init observation sequence while keeping `mark_price_m_t` CMC-bound; (2) proven historical mark at t-60 via existing GET surfaces — only if (1) contradicts OLD-effective contract with evidence.

## Git

PRODUCTION_FILES_CHANGED=0, CONFIG=0, TEST=0, COMMIT/PUSH/PR=false
