# WP Double-Play Productive Host E2E Golden Vector V1

## Mode and baseline

| Field | Value |
|-------|-------|
| MODE | READ_ONLY_FORENSIC_DIFFERENTIAL_GOLDEN_VECTOR |
| BRANCH | `wp3/double-play-compatibility-boundary-v1` |
| BASELINE_SHA | `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` |
| HISTORICAL_TARGET_SHA | `23dccab71eac79c8d39498bbe5bfc84bd54ebf9d` |
| HISTORICAL_ENTER_EVIDENCE_SHA | `34e0f887f351137a3566fe73c400b2fa570ff668` |
| WP-3 | Uncommitted in worktree (included in CURRENT trace) |

Harness: `e2e_forensic_harness_v1.py` (evidence-only). Run: `./scripts/pt -c "import runpy; runpy.run_path('evidence/ops/double_play_productive_host_e2e_golden_vector_v1/20260929T220100Z/e2e_forensic_harness_v1.py', run_name='__main__')"`.

## Imported prior WPs (not re-opened)

WP-1/2/3/4 artifacts consumed as specified. Core DP modules: **PROVEN_CURRENT** equivalent @ git diff. WP-3 boundary flags active on CURRENT worktree.

## Level A — Deterministic differential vector

Re-ran WP-2 side executor: CURRENT (`8475ebb` + WP-3) vs historical worktree (`23dccab71`).

| Vector | Purpose | Key adjudication |
|--------|---------|------------------|
| A | Bull enter (integrated replay) | `enter_long=false` (armed shortcut; **NOT_REACHED**) |
| B | Bear enter (integrated replay) | `enter_short=false` (**NOT_REACHED**) |
| C | DISTINCT/DUPLICATE C1 | `duplicate_advanced_confirmation=false` → **DUPLICATE_DOUBLE_ADVANCE=PROVEN_NO** |
| D_E | F1 fresh/stale | Stale integrated replay **IDENTICAL** OLD vs CURRENT (WP-3) |
| F | Recon/flat | **CURRENT_EQUIVALENT** |
| G | Two-cycle integrated + carrier | Carrier metadata may differ (Single-Lane; not a new root in this WP) |
| G17 | Policy string | OLD `BIND_ONLY_WHEN_PRODUCED` vs CURRENT constant → **BEHAVIORAL_DIVERGENCE** (effective bind **WP3_COMPAT** when flag on) |
| H | Layered init markers | Structural surface differs; WP-3 path **WP3_COMPAT_EQUIVALENT** |
| I | Canonical price provenance | **CURRENT_SAFETY_BOUNDARY** |

Full payloads: `side_current_e2e.json`, `side_historical_e2e.json`, `golden_vector_cycles.json`.

## Level B — CURRENT productive trace

From WP-4 (reused, not re-run for this WP):

- Entry: `run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py`
- Real GET: universe, Cap24, G17 mark-history, Fresh-C1 candles
- **PRODUCTIVE_FIRST_STOP:** `BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED`
- **PRODUCTIVE_CYCLES:** 0
- Instrument (Cap24): `0G-USDT-SWAP` — identity consistent across GET handoff (**PROVEN_CURRENT** for that run)

Code trace:

- `LiveFreshC1ContinuousObservationSourceV1.poll` builds `InjectedContinuousObservationV1` with **candles only** (`mark_price_payload` never set).
- `bootstrap_s8_lane_via_s7_compose_v1` / `make_n1_occupied_lane_s5_runner_v1` require **non-null** `mark_price_payload`.
- Entry script performs G17 mark-history GET but does **not** attach it to bootstrap observation.

**Classification:** `WIRING_DIVERGENCE` — not WP-3, not DP core, not market conditions.

## Forensic counterfactual continuation (Level A downstream)

**PRODUCTIVE_REACHABLE=false**, **FORENSIC_CONTINUATION=true**, **CONTINUATION_REASON=BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED**

Deterministic productive fixture path (`run_natural_enter_long_sequence_for_governed_pre_external_v1`) with mark/provenance/CMC wired as in existing ops tests:

- **decision_outcome:** `enter_long`
- **pre_external_or_enter:** true

This is **not** natural-market proof. It shows: after correcting the bootstrap wiring gap, **no second ROOT wiring defect** was found in this golden vector run before enter_long on the productive MV2 host chain.

Bear **ENTER_SHORT** on integrated vector B remains **NOT_REACHED** (regression logic proof only; no historical runtime enter_short claim).

## Master contract matrix

See `golden_vector_contract_matrix.json` (12 traced contracts, execution order by `seq`).

First divergence (productive): **BOOTSTRAP_MARK_PAYLOAD** → downstream C1/scope/C3/composition unreachable in Level B.

## Root-cause graph

See `golden_vector_root_cause_graph.json`.

- **ROOT_WIRING_01:** LiveFreshC1 poll omits mark → cold bootstrap fail-closed → no S5 cycles → natural ENTER unreachable (Level B).
- **ROOT_STRUCT_G17_POLICY:** Module policy string vs WP-3 effective bind — **does not block** liveness when WP-3 flag on; not counted in `MINIMAL_PATCHES_REQUIRED`.

## Minimal patch plan (not implemented)

| Patch | Closes | Mechanism |
|-------|--------|-----------|
| PATCH_1 | ROOT_WIRING_01 + derived productive stop | Binding / host input-builder: attach scoped public mark-price (and index if required) to cold bootstrap observation |

Likely surfaces:

- `current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py`
- `run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py`

**SAFETY_WEAKENING_REQUIRED=false**, **STATE_OWNERSHIP_CHANGE_REQUIRED=false**, **AUTHORITY_CHANGE_REQUIRED=false**, **CORE_CHANGE_REQUIRED=false**.

## Equivalence summary (golden vector)

| Domain | Verdict |
|--------|---------|
| F1/M9 (WP-3) | **PROVEN_CURRENT** @ integrated replay stale |
| G17 CMC (effective) | **PROVEN_CURRENT** with WP-3 produced-only on DUPLICATE_NOOP |
| Layered init (effective) | **PROVEN_CURRENT** with WP-3 CMC-mark branch |
| C1 cursor / duplicate | **PROVEN_NO** double advance (vector C) |
| Recon/flat | **PROVEN_CURRENT** |
| Canonical provenance | **PRESERVED** (safety boundary) |
| SideState / scope / C3 (integrated G) | Traced in `golden_vector_cycles.json`; no new root beyond bootstrap for productive reach |
| Productive natural ENTER | **not_attempted** post-fix; WP-4 **false** |

## Artifacts

- `WP_DOUBLE_PLAY_PRODUCTIVE_HOST_E2E_GOLDEN_VECTOR_V1.json`
- `golden_vector_contract_matrix.json`
- `golden_vector_root_cause_graph.json`
- `golden_vector_cycles.json`
- `e2e_forensic_harness_v1.py`

**PRODUCTION_FILES_CHANGED=0** | **CONFIG_FILES_CHANGED=0** | **TEST_FILES_CHANGED=0**
