# ROOT_WIRING_01 Patch + Post-Patch Golden Vector + Runtime Reproof V1

## Phase A — Patch surface

| Question | Answer |
|----------|--------|
| Cold bootstrap observation producer | `LiveFreshC1ContinuousObservationSourceV1.poll` |
| Mark producer | Public GET `ENDPOINT_PUBLIC_MARK_PRICE` (`/api/v5/public/mark-price?instId=<Cap24 native_id>`) |
| Mark consumer | `bootstrap_s8_lane_via_s7_compose_v1` → `build_cmc_mark_provenance_from_okx_mark_price_payload_v1` |
| Index | Optional GET `ENDPOINT_MARKET_INDEX_TICKERS` only when `idxPx` absent on mark payload |
| Schema | OKX public mark-price envelope; provenance validated before return |
| Implementation | Single file: `current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py` |

**INDEX_PAYLOAD_REQUIRED_FOR_BOOTSTRAP=false** when mark payload carries `idxPx` (canonical path).

## Phase B — Tests

- `tests/ops/test_current_productive_s6_live_fresh_c1_mark_attachment_v1.py` (new)
- Updated live-C1 mock tests in `test_current_productive_persistent_natural_enter_policy_governed_live_c1_v1.py`
- WP-3 + G17 + integrated replay + WP-2 harness: **PASS**

## Phase C — Post-patch E2E golden vector

Re-run: `e2e_forensic_harness_v1.py` → artifacts in this directory.

| Metric | Post-patch |
|--------|------------|
| BOOTSTRAP_MARK_ATTACHMENT | **CURRENT_EQUIVALENT** |
| ROOT_WIRING_01 | **CLOSED** |
| ROOT_DIVERGENCES_TOTAL | **0** |
| WIRING_DIVERGENCES | **0** |
| BEHAVIORAL_DIVERGENCES | 1 (G17 module policy string; effective bind WP-3 compat) |
| Forensic productive enter_long | **enter_long** (FORENSIC_CONTINUATION=true) |

## Phase D — Runtime (GET-only)

Entry script with `--wp-branch-evidence-run`.

**Progress vs WP-4:** `BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED` **no longer** observed. Real GETs: universe, Cap24, G17 mark-history, Fresh-C1 candles, **public mark-price**.

**New first stop (cycle 0, pre-MV2 cycles):**

```text
FULL_AUTONOMY_MV2_DP_DECISION_STATE_ADDRESSING_MISMATCHED_LANE_STATE
layered_core_bootstrap_init_fail_closed:INITIALIZATION_INCOMPLETE
```

**Classification:** `RUNTIME_ONLY_TECHNICAL_BLOCKER` — not patched in this WP (only ROOT_WIRING_01 authorized).

**Relation to golden vector:** Deterministic forensic continuation uses fixture path with full layered init; live cold bootstrap after mark attach reaches S7 compose but fails layered-core bootstrap completeness.

## File inventory

**PRE_EXISTING_WP3 (unchanged scope):** 5 production + 2 test + 1 config (uncommitted).

**ROOT_WIRING_01:**

- Production: `current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py`
- Tests: `test_current_productive_s6_live_fresh_c1_mark_attachment_v1.py`, updates to live-C1 policy tests

No commit / push / PR.
