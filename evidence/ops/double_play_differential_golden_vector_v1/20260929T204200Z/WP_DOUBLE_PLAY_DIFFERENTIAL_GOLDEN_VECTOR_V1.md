# WP-2 — Differential Golden Vector / OLD↔CURRENT Double-Play Behavioral Proof V1

```text
MODE=READ_ONLY_FORENSICS_TEST_HARNESS
IMPLEMENTATION=false
RUNTIME_VENUE_EXECUTION=false
NETWORK_ACCESS=false
PRODUCTIVE_STATE_MUTATED=false
PRODUCTION_CODE_MUTATED=false
```

## 1. Baseline verification

| Check | Result |
| --- | --- |
| `CURRENT origin&#47;main` | `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` (matches WP-1) |
| `HISTORICAL_TARGET_SHA` | `23dccab71eac79c8d39498bbe5bfc84bd54ebf9d` |
| WP-1 artifacts | Present and parsed |
| Worktree | Clean; historical via detached worktree `wt_historical&#47;` (no main checkout) |
| `BASELINE_DRIFT` | **false** |

## 2. Imported WP-1 Minimal Divergence Set (exact)

1. `F1M9-CONSUMER-PATH-01`
2. `F1M9-MAX-AGE-ENFORCEMENT-01`
3. `G17-CMC-BIND-01`
4. `SINGLE-LANE-LIFECYCLE-01`
5. `LAYERED-CORE-OBS-INIT-01`
6. `RECON-ADMISSION-GATE-01`

## 3. Harness architecture

- **Side executor:** `wp2_side_executor_v1.py` (evidence-only; imports canonical test fixtures + production modules read-only).
- **Isolation:** CURRENT runs on main repo; HISTORICAL runs in detached worktree `wt_historical` with `WP2_REPO_ROOT` path bootstrap (`conftest.py`).
- **API bridging:** `_apply_single_lane_lifecycle_v1()` adapts `prior_presence` (OLD) vs `prior_carrier` (CURRENT) without mutating production code.
- **Orchestrator:** `wp2_orchestrate_v1.py` → `WP_DOUBLE_PLAY_DIFFERENTIAL_GOLDEN_VECTOR_V1.json`.
- **Pytest launcher:** `test_wp2_harness_runner_v1.py` (ephemeral; not production tests).
- **Supplementary contract test:** `test_6_long_only_admissible_enter_long_no_execution` executed on both SHAs (both **PASS**).

No venue, credentials, POST, or productive persistence touched.

## 4. Logical golden vector definitions

| Vector | WP-1 IDs exercised | Intent |
| --- | --- | --- |
| A | Core path | Bull / LONG_ARMED single-cycle replay (canonical `_replay_input`) |
| B | Core path | Bear / SHORT_ARMED symmetric replay |
| C | SINGLE-LANE-LIFECYCLE-01 | DISTINCT → DISTINCT → DUPLICATE_NOOP → DISTINCT lifecycle + confirmation progress |
| D/E | F1M9-* | Fresh vs stale typed vol; presence gate vs F1/M9 consumer + integrated replay with gate ON |
| F | RECON-ADMISSION-GATE-01 | `ReconciliationState.RECONCILED` vs `RECONCILIATION_REQUIRED` at replay input |
| G | SINGLE-LANE-LIFECYCLE-01 | Two-cycle integrated replay with real C1 acceptors + carrier carry-forward |
| H | LAYERED-CORE-OBS-INIT-01 | Module markers for obs-init helpers (CMC mark vs close grid + carryforward param) |
| I | CMC-PRICE-01 (host) | Canonical price provenance fail-closed (CURRENT-only module) |
| G17 | G17-CMC-BIND-01 | Host bind policy string / reuse outcomes |

## 5. Bull / ENTER_LONG trace (Vector A + test_6)

**Vector A (single-cycle LONG_ARMED):** OLD and CURRENT **IDENTICAL** — `decision_outcome=no_action`, `composition_status=no_action`, `enter_long=false`.

**Canonical fixture test_6** (both SHAs): pytest **PASS**; captured outcome `no_action` / `no_action` on both (test only asserts `ENTER_LONG` when composition reaches `long_selected`).

**Classification:** `NOT_REACHED` for ENTER_LONG on Vector A; **no OLD/CURRENT delta** on reachable outcomes.

## 6. Bear / ENTER_SHORT trace (Vector B)

OLD and CURRENT **IDENTICAL** — `enter_short=false`, `decision_outcome=no_action`, same scope/runtime scope traces.

**Classification:** `NOT_REACHED` for ENTER_SHORT; symmetric regression vector shows **no behavioral delta**.

## 7. Duplicate C1 trace (Vector C)

| Cycle | Event | CURRENT | HISTORICAL |
| --- | --- | --- | --- |
| 2 | DUPLICATE_NOOP | `confirmation_advanced=false` | `confirmation_advanced=false` |
| 2 | lifecycle | `rejected_no_lane` | `rejected_no_lane` |

**Duplicate double-advance:** **PROVEN_NO** on both sides.

**Carrier tracing:** CURRENT exposes `carrier_after_lifecycle`; HISTORICAL lifecycle result has no carrier field → **STRUCTURALLY_DIFFERENT** observability, not an extra logical advance on DUPLICATE.

**First divergence (observability):** `duplicate_distinct_increment` `(0,0,0)` vs `(null,null,null)` — padding metadata only.

## 8. F1/M9 fresh/stale trace (Vectors D/E)

### Fresh (aligned CMC + replay input)

| Checkpoint | OLD | CURRENT |
| --- | --- | --- |
| `old_presence_alpha_allowed` | true | true |
| `new_consumer_alpha_allowed` | n/a (no module) | true |
| Integrated replay | `replay_pass=true`, `no_action` | `replay_pass=true`, `no_action` |

**Fresh equivalence at integrated replay boundary:** **PROVEN_CURRENT** (same pass/fail and outcome).

### Stale (600s age condition)

| Checkpoint | OLD | CURRENT |
| --- | --- | --- |
| Presence gate alpha | true | true |
| F1/M9 consumer alpha | n/a | **false** |
| Integrated replay | `replay_pass=true`, `no_action` | **`replay_pass=false`**, `blocked`, `TYPED_VOLATILITY_ESTIMATE_MISSING` |

**First decision-effective divergence (Vector E):** Cycle 0 — `alpha_scope_entry_authority_allowed` — OLD **true** vs CURRENT consumer **false**, then CURRENT integrated replay **fail-closed** where OLD continues.

**Causal chain (CURRENT stale):**

```text
F1M9-MAX-AGE-ENFORCEMENT-01
  → consumer alpha_scope_entry_authority_allowed=false
  → integrated replay presence gate path blocks
  → replay_pass=false (TYPED_VOLATILITY_ESTIMATE_MISSING)
  → DP scope/C3/composition/ENTER not reached
```

**Adjudication:** **CURRENT_ADDITIONAL_GATE** — not representation-only; proven behavior change on stale typed vol with productive gate enabled.

## 9. Reconciliation / position / flat (Vector F)

| Case | OLD outcome | CURRENT outcome |
| --- | --- | --- |
| `RECONCILED` + flat | `no_action` | `no_action` |
| `RECONCILIATION_REQUIRED` | `reconcile_only` | `reconcile_only` |

**Classification:** **IDENTICAL** at integrated replay input (WP-1 `PROVEN_CURRENT` confirmed behaviorally).

**RECON-ADMISSION-GATE-01:** Host-only witness wrapper; **no DP divergence** when equivalent `ReconciliationState` is supplied to replay.

## 10. Single-lane carrier t→t+1 (Vector G)

- Cycle 0: **IDENTICAL** carrier + outcomes.
- Cycle 1: Both reach C3 `candidate`; **carrier padding differs** (`bear_latest_epoch` epoch value) — **BEHAVIORALLY_DIVERGENT** at carrier metadata, not at duplicate/double-advance.

Integrated replay cycle 1 **replay_pass=true** on both after epoch-aligned CMC fix.

## 11. Layered-core init / carryforward (Vector H)

| Marker | OLD | CURRENT |
| --- | --- | --- |
| `_observation_candidates_from_cmc_mark_v1` | false | true |
| `_observation_candidates_from_finalized_closes_v1` | false | true |
| `side_state_from_transition_carryforward` | false | true |

**Classification:** **BEHAVIORALLY_DIVERGENT** at host bind initialization layer (cold-start observation seeding). Full multi-cycle DP outcome delta **not isolated** in this harness (init-only proof).

## 12. Canonical price provenance (Vector I)

- CURRENT: valid fixture provenance passes; `ORDINARY_MARKET_CANDLE_CLOSE` **blocked**.
- OLD: module absent — **no equivalent restriction**.

**Effect class:** **CURRENT_SAFETY_BOUNDARY** — not DP-core semantic change.

**RESTORATION_REQUIRES_SAFETY_WEAKENING:** **false** for restore-via-boundary-adapter (provenance must remain; adapter supplies valid provenance).

## 13. G17 CMC bind policy (Vector G17)

- OLD: `BIND_ONLY_WHEN_PRODUCED`
- CURRENT: `BIND_WHEN_PRODUCED_OR_PROCESS_INTERNAL_REUSE`

**Classification:** **STRUCTURALLY_DIFFERENT**; behavioral delta only when host hits `DUPLICATE_NOOP` with retained estimate (not exercised in integrated replay vectors here). WP-3: **HOST_INPUT_BUILDER_CANDIDATE**.

## 14. Cycle-by-cycle differential matrix (summary)

See `WP_DOUBLE_PLAY_DIFFERENTIAL_GOLDEN_VECTOR_V1.json` → `differential.comparisons`.

| Comparison key | Classification |
| --- | --- |
| vector_A_enter_long | IDENTICAL |
| vector_B_enter_short | IDENTICAL |
| vector_C_duplicate_advanced | IDENTICAL |
| vector_F_* | IDENTICAL |
| f1m9_fresh integrated replay | IDENTICAL (outcome) |
| f1m9_stale alpha + replay | BEHAVIORALLY_DIVERGENT |
| vector_G_cycle_1_carrier | BEHAVIORALLY_DIVERGENT (padding) |
| vector_H_layered_init | BEHAVIORALLY_DIVERGENT |
| vector_I | CURRENT_SAFETY_BOUNDARY_ONLY |
| g17_policy | STRUCTURALLY_DIFFERENT (host) |

## 15. First-divergence causal analysis

Documented in JSON `differential.first_divergences[]`. Root **decision-effective** divergence for restore impact:

1. **F1M9-MAX-AGE-ENFORCEMENT-01** (Vector E stale) — blocks CURRENT integrated replay; OLD continues.
2. **LAYERED-CORE-OBS-INIT-01** (Vector H) — changes episode observation seeding at host bind.
3. **G17-CMC-BIND-01** — host bind policy (conditional on DUPLICATE_NOOP reuse).
4. **SINGLE-LANE-LIFECYCLE-01** — carrier padding / resume semantics (Vector G minor; Vector C observability).

**Non-root for DP replay when enum supplied:** RECON-ADMISSION-GATE-01.

## 16. Core integrity result

- `test_6` **PASS** on OLD and CURRENT.
- No evidence contradicting WP-1 zero-diff on DP core modules.
- **`WP1_CORE_EQUIVALENCE_CONTRADICTION=false`**
- **`CORE_EQUIVALENCE_AFTER_RUNTIME_PROOF=PROVEN_CURRENT`**

## 17. Safety-invariant result

- Canonical price provenance is a **new CURRENT host safety boundary**.
- Restore must **not** weaken it (`RESTORATION_REQUIRES_SAFETY_WEAKENING=false`).
- F1/M9 stale enforcement is an **additional admission constraint**, not a safety weakening.

## 18. Minimal behavioral divergence set (WP-3 inputs)

| Root ID | Proven behavioral effect | WP-3 class |
| --- | --- | --- |
| F1M9-MAX-AGE-ENFORCEMENT-01 (+ consumer path) | Stale typed vol blocks CURRENT integrated replay | BOUNDARY_CONFIG_BINDING_CANDIDATE / PURE_ADAPTER_CANDIDATE |
| LAYERED-CORE-OBS-INIT-01 | Different cold-start observation candidates | HOST_INPUT_BUILDER_CANDIDATE |
| G17-CMC-BIND-01 | DUPLICATE_NOOP reuse binds estimate on CURRENT | HOST_INPUT_BUILDER_CANDIDATE |
| SINGLE-LANE-LIFECYCLE-01 | Carrier padding / resume path differences | HOST_INPUT_BUILDER_CANDIDATE (not core) |
| RECON-ADMISSION-GATE-01 | Host fail-closed only; replay identical when RECONCILED | No WP-3 patch unless host omit witness |
| CMC-PRICE-01 (provenance) | Host admission only | CURRENT_SAFETY_INVARIANT (valid provenance required) |

**`BEHAVIORAL_ROOT_DIVERGENCES=3`** (F1M9 stale path, layered init, G17 conditional host bind).  
**`BOUNDARY_ONLY_DIVERGENCES=3`**  
**`CORE_DIVERGENCES=0`**

## 19. WP-3 candidate boundary classes

- **Primary patch surface:** F1/M9 consumer + stale enforcement alignment adapter (preserve 600s semantics; align OLD productive reachability or document intentional stricter gate).
- **Secondary:** Layered-core obs init + G17 bind policy for parity on no-new-sample cycles.
- **Do not patch:** `transition_state`, composition matrix, entry/exit policy modules.

## 20. Answers to 16 required adjudication questions

1. OLD ENTER_LONG on Vector A? **NOT_REACHED** (same as CURRENT).
2. CURRENT equivalent ENTER_LONG Vector A? **NOT_REACHED** — **IDENTICAL** to OLD.
3. OLD ENTER_SHORT Vector B? **NOT_REACHED**.
4. CURRENT ENTER_SHORT Vector B? **NOT_REACHED** — **IDENTICAL**.
5. DUPLICATE_NOOP extra advance? **PROVEN_NO** both sides.
6. F1/M9 fresh equivalent? **PROVEN_CURRENT** (integrated replay + alpha true both sides).
7. CURRENT 600s max-age real restriction vs OLD? **YES** — **CURRENT_ADDITIONAL_GATE** (proven stale integrated replay block).
8. Recon/position/flat equivalent? **PROVEN_CURRENT** at replay input.
9. Single-lane carrier t→t+1 equivalent? **CONFLICTING_CURRENT** (padding/resume metadata; not duplicate double-advance).
10. Layered init/carryforward equivalent? **CONFLICTING_CURRENT** (helpers differ; init behavior changed).
11. Canonical price provenance? **CURRENT_SAFETY_BOUNDARY** — not DP-core semantics.
12. Which WP-1 items cause **decision-effective** divergence? **F1M9-MAX-AGE-ENFORCEMENT-01** (+ consumer wiring on stale); **LAYERED-CORE-OBS-INIT-01** (host init); **G17-CMC-BIND-01** (conditional host); SINGLE-LANE **minor** carrier padding only.
13. Structurally different but equivalent? **G17 policy string** when every cycle PRODUCED; **RECON admission** when witness supplies RECONCILED.
14. First divergence failing vectors: **Vector E stale** — consumer alpha false (CURRENT); **Vector H** — obs init helpers.
15. All behavioral differences outside DP core? **PROVEN_YES** (harness + test_6; zero core module edits).
16. Compatibility restore without core/ownership change? **PROVEN_YES** — boundary/host adapters only; safety provenance must remain.

## 21. Blockers / unknowns

```text
BLOCKER=NONE
UNKNOWN_REMEDIATION_CLASS=conditional G17 DUPLICATE_NOOP (needs host-cycle vector with producer DUPLICATE_NOOP)
NEXT_WP=WP-3 boundary adapter design against JSON minimal set
```

## 22. Final adjudication

WP-2 **behaviorally confirms** WP-1: DP **core** remains equivalent; **proven restore-impacting deltas** are **host/admission boundaries** — chiefly **F1/M9 stale max-age enforcement on the integrated replay path**, plus **layered-core initialization** and **G17 bind reuse policy**. No core patch authorized.

Machine-readable: `WP_DOUBLE_PLAY_DIFFERENTIAL_GOLDEN_VECTOR_V1.json`

Harness artifacts (evidence-only): `wp2_side_executor_v1.py`, `wp2_orchestrate_v1.py`, `side_current.json`, `side_historical.json`, `wt_historical&#47;` (detached read-only tree).
