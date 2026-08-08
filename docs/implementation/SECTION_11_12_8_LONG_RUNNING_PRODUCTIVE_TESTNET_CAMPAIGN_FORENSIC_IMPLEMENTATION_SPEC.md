# Forensic Semantic Implementation Spec — §11.12.8 Bounded Long-Running Productive Testnet Campaign

```text
DOCUMENT_CLASS=FORENSIC_SEMANTIC_IMPLEMENTATION_SPEC
DOCUMENT_ROLE=IMPLEMENTATION_PACKAGE_BLUEPRINT_ONLY
RUNTIME_AUTHORIZATION_EFFECT=NONE
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
CODE_MUTATION_IN_THIS_DOCUMENT=false
GOVERNANCE_MUTATION_IN_THIS_DOCUMENT=false
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
BASELINE_ORIGIN_MAIN_SHA=35519be2684b65491fbe53b09f82e91370e7cc89
TARGET_CAPABILITY_OUTCOME=BOUNDED_LONG_RUNNING_AUTONOMOUS_PRODUCTIVE_TESTNET_CAMPAIGN_PATH_PRESENT
SECTION_11_12_8_CLOSED_BY_THIS_SPEC=false
SECTION_11_13_STARTED_BY_THIS_SPEC=false
NO_NUMBER_INVENTION_FOR_DURATION_BOUND=true
```

This document is the sole deliverable of
`OWNER_GO FORENSIC_SEMANTIC_IMPLEMENTATION_SPEC_FOR_SECTION_11_12_8_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN`.

It does **not** implement, activate, authorize, or close §11.12.8.
It specifies the **one coherent implementation package** that must later be
merged so a **separate** `OWNER_GO EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW`
can run a bounded long-running autonomous PRODUCTIVE_REAL OKX Testnet
campaign and only then close §11.12.8 via real productive evidence.

A senior engineer must be able to implement the package from this document
alone, without rediscovering architecture.

---

## 0. Baseline validation (frozen at authorship)

```text
BASELINE_VALIDATION=PASS
CURRENT_ORIGIN_MAIN_SHA=35519be2684b65491fbe53b09f82e91370e7cc89
HEAD_EQ_ORIGIN_MAIN=true
TRACKED_WORKTREE_CLEAN=true
UNTRACKED_EVIDENCE_PRESERVED=true
MASTER_RUNBOOK_STATUS=READ_CURRENT
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY_CONSULTED
WORKING_MODEL_DRIFT=NONE
CURRENT_PHASE=SECTION_11_12_8_OPEN_POST_UNLOCK_EXECUTE_PATH_PRESENT_BUT_ONE_SHOT_ONLY
LAST_CANONICALLY_CLOSED_STEP=CAPABILITY_11_SECTION_11_12_8_REAL_PRODUCTIVE_TESTNET_EXECUTE_PATH_UNLOCK_V1_MERGED
EARLIEST_UNRESOLVED_DEPENDENCY=BOUNDED_LONG_RUNNING_MULTI_CYCLE_PRODUCTIVE_TESTNET_CAMPAIGN_EXECUTOR_PLUS_CANONICAL_DURATION_BOUND
REQUESTED_STEP=FORENSIC_SEMANTIC_IMPLEMENTATION_SPEC_ONLY
REQUEST_MATCHES_CANONICAL_NEXT_STEP=true_for_FORENSIC_SPEC_PREPARATION_OF_MISSING_LONG_RUNNING_PATH
AUTHORIZATION_REQUIRED=OWNER_GO_PRESENT_FOR_SPEC_ONLY
EXECUTION_SURFACE_TOUCHED=DOCS_IMPLEMENTATION_SPEC_ONLY
HARD_STOP_REASONS=NONE_FOR_SPEC_AUTHORSHIP
PROPOSED_SAFE_ACTION=WRITE_THIS_FORENSIC_SPEC_ONLY
SECTION_11_12_8_CANONICALLY_CLOSED=false
SECTION_11_13_STARTED=false
LIVE_HARD_BLOCK_INTACT=true
CURRENT_PRODUCTIVE_PATH_CLASS=SINGLE_BOUNDED_ONE_SHOT_PRODUCTIVE_REAL
LONG_RUNNING_CAMPAIGN_PATH_PRESENT=false
SECTION_11_12_8_REQUIREMENT_SATISFIED=false
```

Untracked local evidence observed (must remain untouched by implementers of
this package unless a later Owner-GO explicitly binds it):

- `evidence&#47;ops&#47;section_11_12_8_execute_productive_testnet_campaign_now_abort_v1&#47;`
- `evidence&#47;ops&#47;section_11_12_8_execute_productive_testnet_campaign_now&#47;`
- `evidence&#47;ops&#47;section_11_12_8_bounded_long_running_campaign_hard_stop_v1&#47;`

Hard-stop forensic (local, untracked) already recorded:

```text
LONG_RUNNING_CAMPAIGN_PATH_PRESENT=false
MERGED_PRODUCTIVE_EXECUTE_PATH_IS_SINGLE_BOUNDED_ONE_SHOT_ONLY
NO_MULTI_CYCLE_WALLCLOCK_LONG_RUNNING_CAMPAIGN_EXECUTOR_ON_ORIGIN_MAIN
NO_CANONICAL_NUMERIC_DURATION_BOUND_IN_MASTER_RUNBOOK_SECTION_11_12_8
LONG_RUNNING_PACKAGES_REMAIN_FIXTURE_OR_IMPLEMENTATION_ONLY
PRODUCTIVE_LIFECYCLE_IS_SINGLE_SUBMIT_THEN_COMPLETE
```

---

## 1. Baseline forensics

### 1.1 Repository authorities consulted

| Authority | Path | Role |
| --- | --- | --- |
| SSOT | `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` | Semantic authority |
| Map of Truth | `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md` | Navigation only |
| Canonical productive start consumer | `src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/` | PRODUCTIVE consumer/executor |
| Unlock package | `src/ops/section_11_12_8_real_productive_testnet_execute_path_unlock_v1/` | Real wire client + operator entry |
| Fixture long-running residual | `src/ops/capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1/` | FIXTURE_ONLY |
| Terminal consumer | `src/ops/section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1/` | IMPLEMENTATION_ONLY |
| Cap 11.4 adapter contracts | `src/ops/capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1/` | Venue-native serialization (fixture) |
| Cap 11.6 campaign evidence | `src/ops/capability_11_6_long_running_autonomous_testnet_evidence_v1/` | FIXTURE_ONLY continuity paths |

### 1.2 Confirmed baseline facts

1. `HEAD == origin&#47;main == 35519be2684b65491fbe53b09f82e91370e7cc89`
2. Tracked worktree clean; only untracked ops evidence present
3. §11.12.8 open (`SECTION_11_12_8_CANONICALLY_CLOSED=false`)
4. §11.13 not started (`SECTION_11_13_STARTED=false` constants + closeout)
5. LIVE hard-block intact (`LIVE_FORBIDDEN_HOSTS`, runtime_mode!=TESTNET raises, `live_authorized=false`)
6. PRODUCTIVE_REAL consumer/executor present and merged
7. Real Testnet wire path present (`BoundOkxTestnetHttpClientV1` + `--allow-wire-send`)
8. One-shot path is real productive semantics (`wire_sent=true` observed in local run evidence)
9. Long-running packages exist but are fixture/implementation-only and **not** wired into the productive execute entrypoint

### 1.3 Repo-wide semantic inventory (classification)

| Surface | Semantic state | Productive long-running? |
| --- | --- | --- |
| `scripts/ops/run_section_11_12_8_real_productive_testnet_execute_operator_entrypoint_v1.py` | PRODUCTIVE | No — dispatches one-shot lifecycle |
| `unlock_orchestrator_v1.execute_unlocked_productive_path_v1` | PRODUCTIVE | No |
| `productive_consumer_v1._execute_productive_real_network_v1` | PRODUCTIVE | No — calls one-shot executor |
| `campaign_executor_v1.run_campaign_lifecycle_v1` | PRODUCTIVE / MISWIRED_AS_CAMPAIGN | **Prevents** long-running: single submit → `completed=True` |
| `bound_testnet_http_client_v1.BoundOkxTestnetHttpClientV1` | PRODUCTIVE transport | Wire send works; response parse MISSING |
| `productive_execution_port_v1.submit_order_v1` | PRODUCTIVE / MISWIRED body | Non-venue-native body; drops response semantics |
| `closeout_v1.evaluate_section_11_12_8_closeout_v1` | PRODUCTIVE gate present / constants false | Cannot close without real PROVEN fields |
| Cap 11 §11.12.8 long-running residual | FIXTURE_ONLY | Explicitly refuses activation |
| Terminal package | IMPLEMENTATION_ONLY | `PRODUCTIVE_RUN_AUTHORIZED=false` |
| PATH/EXECUTION/RUN/RUN_ACTIVATION/CONSUMER/HANDOFF packages | DEPRECATED / NON_EXTENDABLE residuals | Not the productive execute edge |
| Cap 11.6 long-running evidence | FIXTURE_ONLY | Continuity fixture paths only |
| Cap 11.9/11.10 `duration_bound_seconds` | FIXTURE_ONLY Live contracts | **Not** normative for §11.12.8 |

---

## 2. Current end-to-end execution graph

Directed graph of the **merged productive** path on `origin/main`:

```text
OWNER_GO EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
 → scripts/ops/run_section_11_12_8_real_productive_testnet_execute_operator_entrypoint_v1.py::main
 → unlock_orchestrator_v1.execute_unlocked_productive_path_v1
 → productive_consumer_v1.execute_productive_section_11_12_8_campaign_run_v1(mode=PRODUCTIVE_REAL_NETWORK)
 → _execute_productive_real_network_v1
 → owner_go_consumer_v1.consume_actual_start_owner_go_v1
 → testnet_authorization_v1.authorize_testnet_runtime_v1
 → enabled/armed durable transitions
 → hidden_confirm_v1.latch_and_consume_confirm_digest_v1
 → secretref_credential_v1.resolve_and_load_secretref_ephemeral_v1 (+ vault_resolver)
 → account_endpoint_binding_v1.bind_and_verify_testnet_account_v1
 → safety_preflight_v1.evaluate_safety_preflight_v1 (risk/kill/emergency once)
 → network_session_v1.reach_network_session_entry_boundary_v1
 → bound_testnet_http_client_v1.construct_bound_okx_testnet_http_client_v1
 → testnet_transport_v1.build_productive_testnet_transport_v1
 → productive_execution_port_v1.construct_productive_testnet_execution_port_v1
 → campaign_executor_v1.run_campaign_lifecycle_v1   ★ ONE-SHOT TERMINAL
 → evidence_v1.write_productive_execution_evidence_v1 + seal
 → closeout_v1.evaluate_section_11_12_8_closeout_v1
```

### 2.1 Node/edge forensic table

| Node | File | Symbol / key | Semantic state | Long-running support | Required change |
| --- | --- | --- | --- | --- | --- |
| OWNER_GO | Master Runbook §11.12.8 + entrypoint argv | `EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW` | PRODUCTIVE auth token | Permits execute; does not define duration | Add SSOT numeric duration (+ optional cycle) bound |
| Command/consumer entry | `scripts/ops/run_section_11_12_8_real_productive_testnet_execute_operator_entrypoint_v1.py` | `main` | PRODUCTIVE | No campaign-duration CLI/config | Wire long-running executor; bind duration from SSOT |
| Unlock orchestrator | `...&#47;unlock_orchestrator_v1.py` | `execute_unlocked_productive_path_v1` | PRODUCTIVE | Still one-shot | Dispatch long-running lifecycle; keep unlock reuse |
| Authorization | `...&#47;owner_go_consumer_v1.py` | `consume_actual_start_owner_go_v1` | PRODUCTIVE | One-time GO consume OK | Preserve; campaign must not re-consume GO per cycle |
| Enabled/Armed | `...&#47;productive_consumer_v1.py` + `durable_state_v1.py` | `STATE_ENABLED` / `STATE_ARMED` | PRODUCTIVE | Ephemeral once | Persist across cycles; re-check each cycle |
| Hidden confirm | `...&#47;hidden_confirm_v1.py` | `latch_and_consume_confirm_digest_v1` | PRODUCTIVE | Consumed once at start | Lifetime = campaign start only; replay blocked |
| SecretRef load | `...&#47;secretref_credential_v1.py` + `vault_resolver_v1.py` | `resolve_and_load_secretref_ephemeral_v1` | PRODUCTIVE | Loaded once | Lifetime = campaign; release only at terminal |
| Account binding | `...&#47;account_endpoint_binding_v1.py` | `bind_and_verify_testnet_account_v1` | PRODUCTIVE (identity stub-tolerant) | Once | Keep; re-verify on restart recovery path |
| Risk gates | `...&#47;safety_preflight_v1.py` | `evaluate_safety_preflight_v1` | PRODUCTIVE but FIXED fixture ctx | Once before session | **Re-evaluate each cycle** with real market age / position |
| Kill switch | `src/risk_layer/kill_switch/core.py` via safety | `KillSwitch.check_and_block` | PRODUCTIVE reuse | Once | Check before every side effect / each cycle |
| Emergency controls | constants + safety | `CANONICAL_EMERGENCY_COMMANDS` | PRODUCTIVE presence check | Once | Wire abort reactions into cycle loop |
| Executor dispatch | `campaign_executor_v1.py` | `run_campaign_lifecycle_v1` | PRODUCTIVE **ONE_SHOT** | **Prevents** | Replace with multi-cycle wallclock loop |
| PRODUCTIVE_REAL network session | `network_session_v1.py` | `reach_network_session_entry_boundary_v1` | PRODUCTIVE | Session start only | Keep session open across cycles |
| Strategy/signal boundary | **MISSING** | — | MISSING | No autonomous evaluation cycle | Add no-trading-logic cycle evaluation hook (existing decision boundary reuse only; no Alpha change) |
| Order intent | hardcoded in executor | `client_order_id="coid-actual-start-1"` | PRODUCTIVE / HARDCODED | Single intent | Per-cycle intent only when signal present; idempotent IDs |
| Submit adapter | `productive_execution_port_v1.submit_order_v1` | body uses Peak fields | PRODUCTIVE / MISWIRED | Single submit | Venue-native OKX body via Cap 11.4 mapping |
| OKX testnet request | `BoundOkxTestnetHttpClientV1.request` | urllib wire send | PRODUCTIVE | Works | Keep; parse response body |
| Response handling | same + port | returns `body_bytes` only | MISSING/MISWIRED | No ACK/reject | Parse `code`/`data[]`/`sCode`/`ordId`/`clOrdId` |
| ACK / order-id / fill | **MISSING** | — | MISSING | Prevents lifecycle proof | Capture ACK/reject; optional fill poll |
| Campaign lifecycle | `CampaignLifecycleRecordV1` | `completed` after first submit | PRODUCTIVE / WRONG | One-shot autocomplete | Separate cycle vs campaign terminal states |
| Persistence | `durable_state_v1.py` | stages IDLE→…→COMPLETED→SEALED | PRODUCTIVE incomplete | No cycle states | Add RUNNING/CYCLE_*/BOUND_REACHED fields |
| Evidence | `evidence_v1.py` | hardcodes `STUBBED_ACCEPTANCE=true`, `NETWORK_EFFECT=NONE` | MISWIRED | Top-level lies on real path | Real counters/timestamps/duration |
| Evidence seal | `seal_evidence_dir_v1` | SHA256 manifest | PRODUCTIVE | OK | Keep; seal only after terminal |
| Closeout evaluator | `closeout_v1.py` | reads module constants always false | PRODUCTIVE gate / UNBOUND | Cannot close | Bind real evidence → PROVEN fields |

### 2.2 Critical graph defects (summary)

1. **No multi-cycle loop** anywhere on the productive edge.
2. **Campaign completion coupled to first side effect.**
3. **Synthetic heartbeat** (`heartbeat_count += 1`) without wallclock loop.
4. **Safety evaluated once** with fixture `RiskContext` (`now_epoch=1`, age=1s).
5. **OKX request body is not venue-native** (Cap 11.4 already defines `clOrdId`/`instId`/`ordType`/`sz`).
6. **HTTP response body discarded** (`body_bytes=len(raw)` only).
7. **Evidence top-level fields mis-claim stubbed/none** even when payload shows wire send.
8. **Closeout PROVEN fields are module constants**, never derived from evidence.
9. **No canonical numeric duration bound** in Master Runbook §11.12.8.
10. **Long-running packages exist but are dead for productive execute.**

---

## 3. One-shot root-cause analysis

### 3.1 Exact call chain (productive wire path)

```text
main(--allow-wire-send)
  → execute_unlocked_productive_path_v1(allow_wire_send=True)
    → execute_productive_section_11_12_8_campaign_run_v1(mode=MODE_PRODUCTIVE_REAL)
      → _execute_productive_real_network_v1(...)
        → ... gates ...
        → run_campaign_lifecycle_v1(port=..., stubbed=False)
             ★ ROOT CAUSE OWNER
```

### 3.2 Exact one-shot transitions inside `run_campaign_lifecycle_v1`

File: `src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/campaign_executor_v1.py`

| Step | Code behavior | State effect |
| --- | --- | --- |
| Init | `CampaignLifecycleRecordV1(started=True, running=True)` | campaign starts |
| Cycle init | **none** — no `cycles_started`, no loop counter | cycle model absent |
| First iteration | implicit: function body is the only iteration | begins immediately |
| Network/order submit | `port.submit_order_v1(client_order_id="coid-actual-start-1", ...)` | first side effect |
| Synthetic continuity | `heartbeat_count += 1`; `continuity_ok=True`; `restart_handled=True` | fake multi-step proof |
| Terminal | `record.completed = True`; `running=False`; event `complete` | **campaign ends** |
| Seal coupling (caller) | consumer transitions `CAMPAIGN_RUNNING → COMPLETED → SEALED` | sealed after one submit |

**Completion coupling class:**

```text
COMPLETION_TRIGGER=EXPLICIT_TERMINAL_ASSIGNMENT_AFTER_FIRST_SUBMIT_RETURN
NOT=context_manager_exit
NOT=external_scheduler
YES=function_return_after_single_submit
YES=first_side_effect_then_autocomplete
```

There is **no** `while`, **no** `for cycle`, **no** `sleep`, **no** `time.monotonic` duration check in the productive executor (structural forensic confirmed).

### 3.3 Why existing “long-running” code does not help

| Package | Why not productive long-running |
| --- | --- |
| Cap 11 §11.12.8 long-running residual | `LIFECYCLE_SOURCE=FIXTURE_ONLY`, `ORDER_SEND_DISABLED=true`, refuses activation |
| Cap 11.6 campaign evidence | Fixture path names only; `refuse_long_running_campaign_activation_v1` |
| Terminal package | `IMPLEMENTATION_ONLY=true`, `PRODUCTIVE_RUN_AUTHORIZED=false` |
| PATH/EXECUTION/RUN wrappers | Non-extendable residuals; not wired to unlock entrypoint |

### 3.4 State model today

- Durable state is **campaign-stage** only (IDLE…COMPLETED/SEALED).
- Lifecycle record is **campaign-level** flags, not per-cycle.
- No `campaign_id`, no `execution_start_utc`, no `duration_bound_seconds`, no `cycles_*`.

### 3.5 Semantic change required so one submit does not end the campaign

```text
REQUIRED:
  CYCLE_COMPLETE != CAMPAIGN_COMPLETED
  FIRST_SIDE_EFFECT != CAMPAIGN_COMPLETED
  CAMPAIGN_COMPLETED only if:
      (wallclock_elapsed >= CANONICAL_DURATION_BOUND_SECONDS)
      OR (optional max_cycles reached AND duration policy allows cycle-bound terminal)
      OR (fail-closed abort terminal)
  WHILE RUNNING:
      re-evaluate strategy boundary
      re-check risk/kill/emergency
      optionally submit 0..N orders per cycle under existing risk bounds
      persist per-cycle evidence
```

---

## 4. Canonical campaign contract

### Target name

```text
BOUNDED_LONG_RUNNING_AUTONOMOUS_PRODUCTIVE_TESTNET_CAMPAIGN
```

Derived from Master Runbook §11.12 sequence item
`11.12.8 Long-running autonomous Testnet campaign` plus §11.12.8 post-unlock
`MODE_PRODUCTIVE_REAL` gate list. **No trading/Alpha logic changes.**

### Contract fields

| ID | Requirement | Normative source / note |
| --- | --- | --- |
| A Start conditions | Unlock merged; Owner-GO present; all MODE_PRODUCTIVE_REAL gates pass; LIVE hard-block | MR §11.12.8 |
| B Authorization | Scoped `EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW`; one-time consume; ephemeral TESTNET auth | MR §11.12.8 |
| C Testnet-only binding | `runtime_mode=TESTNET`; OKX EEA simulated hosts; `x-simulated-trading:1`; live hosts hard-blocked | constants + MR |
| D Campaign-ID | Durable unique ID per Owner-GO consumption | MISSING → required |
| E Start timestamp | UTC ISO8601 at RUNNING entry | MISSING → required |
| F Monotonic wall-clock | `time.monotonic()` elapsed for bound enforcement | MISSING → required |
| G Numeric duration bound | **Must be defined in SSOT §11.12.8** before runtime may choose a value | **ABSENT today — governance fix required; DO NOT invent number in code PR without SSOT** |
| H Optional/max cycle bound | Optional secondary bound; if both present, **first reached wins** (specify in SSOT) | ABSENT |
| I Cycle cadence | Deterministic schedule (fixed interval or event-driven tick) under bound; no busy-spin | MISSING |
| J Strategy evaluation | Each cycle may invoke existing decision boundary **without mutating trading core** | MISSING wiring |
| K Order-attempt semantics | Submit only if signal + risk allow; venue-native payload; idempotent client order id | Partial/MISWIRED |
| L No signal | Cycle completes with `order_attempt=false`; campaign continues | MISSING |
| M Reject | Record exchange reject; campaign continues unless policy says abort | MISSING |
| N ACK | Increment ack count; persist `exchange_order_id` | MISSING |
| O Partial fill | Record if observed; not required to close campaign unless PROVEN field needs it | Observational |
| P Fill | Record if observed; **campaign success ≠ fill** unless SSOT PROVEN field requires lifecycle proof evidence | Observational + closeout binding |
| Q Timeout | Transport timeout → classify; retry policy or abort | Partial (raises) |
| R Transient network error | Bounded retry; no silent success | MISSING taxonomy |
| S Retry | Bounded; no zero-interval burst (MR §13) | MISSING |
| T Idempotency / client_order_id | Unique per intent; replay-safe | Hardcoded today |
| U exchange_order_id capture | Persist when ACK provides ordId | MISSING |
| V Kill-switch | Check before every side effect; abort campaign | Once today |
| W Emergency-stop | Cancel-all / halt paths; abort | Injection-only today |
| X Risk-gate re-evaluation | Each cycle with current context | Once/fixture today |
| Y SecretRef lifetime | Ephemeral for whole campaign; release at terminal; no plaintext evidence | Load once OK; ensure no cycle re-print |
| Z Hidden-confirm lifetime | Latch once at start; replay blocked for campaign | OK |
| AA Persistent state | Campaign + per-cycle durable fields; restart-safe | Incomplete |
| AB Graceful bounded completion | Bound reached → COMPLETING → COMPLETED → evidence → SEALED | MISSING |
| AC Abort semantics | Fail-closed abort with reason; seal abort evidence; no §11.12.8 close | Partial |
| AD Evidence semantics | Full counter/timestamp schema (§9) | Incomplete/MISWIRED |
| AE Closeout semantics | PROVEN fields from real evidence only; not from sealed alone | Unbound |
| AF LIVE hard-block | Unchanged invariants | Intact — must preserve |

---

## 5. Duration / bound governance gap

### 5.1 Finding

```text
CANONICAL_NUMERIC_DURATION_BOUND_IN_MASTER_RUNBOOK_SECTION_11_12_8=false
```

Master Runbook §11.12.8 authorizes `EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW` and
lists gates, but **does not define** a numeric campaign duration, max cycles,
or cadence.

Repo search across §11.12.8 packages/specs: **no** `duration_bound`,
`DURATION_BOUND`, `max_cycles`, or campaign wallclock bound.

### 5.2 Nearby values (non-normative for §11.12.8)

| Location | Value | Normative for §11.12.8? |
| --- | --- | --- |
| Cap 11.9 live canary fixture default | `duration_bound_seconds=3600` | **NO** — Live fixture-only |
| Cap 11.10 live bounded continuity fixture default | `duration_bound_seconds=86400` | **NO** — Live fixture-only |
| Cap 11.2 auth binding | `maximum_session_duration="PT0S"` | **NO** — fail-closed zero default |
| HTTP client timeout | `timeout_seconds=10.0` | **NO** — per-request transport only |
| Phase 9.2 wallclock packaging | packaging/continuity, not §11.12.8 duration | **NO** |

**No number may be invented in the implementation PR.** Owner must add the
bound to SSOT first (or in the same coherent package’s RUNBOOK change,
explicitly Owner-authorized as governance content of that package).

### 5.3 Required governance fix (spec only; not applied here)

**Where:** `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` section
`### 11.12.8 Post-unlock Owner-EXECUTE authority (binding)` (or an immediately
adjacent `#### 11.12.8.1 Campaign bounds` subsection under 11.12.8).

**What must be added (semantics, not a guessed number):**

```text
SECTION_11_12_8_CAMPAIGN_DURATION_BOUND_SECONDS=<OWNER_RATIFIED_POSITIVE_INTEGER>
SECTION_11_12_8_CAMPAIGN_MAX_CYCLES=<OPTIONAL_POSITIVE_INTEGER_OR_NONE>
SECTION_11_12_8_CYCLE_CADENCE_SECONDS=<OWNER_RATIFIED_POSITIVE_INTEGER>
BOUND_PRIORITY=DURATION_FIRST_UNLESS_SSOT_STATES_OTHERWISE
# Recommended explicit rule to encode:
# if both bounds set: terminal when either is reached (first-reached-wins)
# duration measurement: monotonic elapsed since RUNNING, also record UTC start/end
```

**Evidence proof of bound:**

- `duration_bound_seconds` copied from SSOT constant into evidence
- `execution_start_utc` / `execution_end_utc`
- `execution_duration_seconds` from monotonic elapsed
- `bound_reached_reason ∈ {DURATION_BOUND, CYCLE_BOUND, ABORT, ...}`
- verifier asserts `execution_duration_seconds >= duration_bound_seconds`
  for graceful duration completion **or** documents abort before bound

Until SSOT contains the number, runtime must fail-closed:

```text
CANONICAL_DURATION_BOUND_DEFINED=false → REFUSE_CAMPAIGN_START
```

---

## 6. Autonomy semantics (Peak_Trade-technical)

From Master Runbook §11.1 autonomous loop + §11.12.8 “Long-running autonomous”:

| Question | Answer for §11.12.8 productive campaign |
| --- | --- |
| Must campaign run multiple strategy-evaluation cycles? | **Yes.** Single submit-then-exit is not long-running autonomy. |
| New market snapshot each cycle? | **Yes**, via existing public/private ingestion boundaries already in the autonomous loop (wire existing read paths; do not invent Alpha). If a cycle cannot obtain non-stale data → skip order / abort per failure matrix. |
| Risk re-checked each cycle? | **Yes.** |
| Cycles without order allowed? | **Yes.** Mandatory. |
| One sent order + many evaluation cycles valid? | **Yes**, if duration/cycle bound and autonomy evidence are satisfied. |
| Persist between cycles? | campaign_id, stage, counters, open client/exchange order ids, last risk/kill results, monotonic start, cycle index, evidence cursor |
| After exchange reject? | Continue campaign unless reject class is fatal; evidence reject count++ |
| Null fills entire campaign? | Campaign may still **complete by bound**; but `TESTNET_ORDER_LIFECYCLE_PROVEN` may remain false if lifecycle evidence insufficient — **campaign completion ≠ all PROVEN true** |
| Successful campaign closeout vs successful fill | Closeout requires MR PROVEN set; fill is evidence for lifecycle fields when observed, not a synonym for campaign success |

```text
CAMPAIGN_BOUNDED_COMPLETION ≠ SECTION_11_12_8_CLOSED
SECTION_11_12_8_CLOSED requires ALL TESTNET_*_PROVEN + TESTNET_EVIDENCE_VERIFIED from real evidence
```

---

## 7. Real OKX Testnet response path

### 7.1 Observed one-shot evidence pattern

Local productive run evidence shows:

```text
wire_sent=true
submitted=true
ORDER_ACK_COUNT absent / effectively 0
EXCHANGE_ORDER_ID_OBSERVED=false
```

### 7.2 What the code actually does today

`BoundOkxTestnetHttpClientV1.request` (wire enabled):

1. Builds signed OKX headers (correct shape).
2. Sends HTTP request via `urllib`.
3. Reads response bytes.
4. Returns `{ok: status 2xx, wire_sent:True, http_status, body_bytes:len(raw)}`.
5. **Does not** `json.loads(raw)`.
6. **Does not** inspect OKX top-level `code`.
7. **Does not** parse `data[]`, `ordId`, `clOrdId`, `sCode`, `sMsg`.

`ProductiveTestnetExecutionPortV1.submit_order_v1`:

1. Posts body `{client_order_id, instrument, order_type, side, quantity}` —
   **not** Cap 11.4 venue-native `{clOrdId, instId, side, ordType, sz, tdMode}`.
2. Collapses transport result to wire/stub flags only.
3. Sets `submitted = wire_sent and not stubbed` — **equates wire send with submit success**.

### 7.3 Required semantic distinctions

| State | Meaning | Current |
| --- | --- | --- |
| request prepared | signed locally | yes |
| request sent / wire_sent | bytes left host | yes |
| transport response | HTTP status + body received | status yes, body no |
| exchange accepted | OKX `code=="0"` and item `sCode=="0"` | no |
| exchange rejected | non-zero code/sCode | no |
| order acknowledged | accepted + `ordId` present | no |

### 7.4 Where ACK_COUNT / exchange_order_id must be set

1. HTTP client returns parsed sanitized response object (no secrets).
2. New response mapper (reuse Cap 11.4 field names) classifies ACCEPT/REJECT.
3. Port increments counters and stores ids on lifecycle/evidence.
4. **Never** treat `wire_sent` as ACK.

### 7.5 Fill observation

- Polling via allowlisted `/api/v5/trade/orders-pending` (and/or account reads) may be added under existing endpoint allowlist.
- WebSocket private fills are **not** required to ship the long-running path if REST polling covers observed fills.
- For §11.12.8 closeout, fills are required **only insofar as** `TESTNET_ORDER_LIFECYCLE_PROVEN` evidence demands lifecycle observation; do not fake fills.

### 7.6 Fake-ACK prohibition

```text
FORBIDDEN: synthesize ACK from wire_sent
FORBIDDEN: mark exchange_order_id from client_order_id
FORBIDDEN: close PROVEN fields from stubbed fixtures
```

---

## 8. State machine target design

### 8.1 Target stages

```text
NOT_STARTED
AUTHORIZED
ENABLED
ARMED
CONFIRMED
SECRETS_READY
PRECHECK_PASS
RUNNING
CYCLE_RUNNING
CYCLE_COMPLETE
BOUND_REACHED
COMPLETING
COMPLETED
ABORTING
ABORTED
SEALED
```

Mapping from current durable stages:

| Current | Target |
| --- | --- |
| IDLE | NOT_STARTED |
| GO_CONSUMED/AUTHORIZED | AUTHORIZED |
| ENABLED/ARMED | ENABLED/ARMED |
| CONFIRM_LATCHED | CONFIRMED |
| CREDENTIAL_BOUND | SECRETS_READY |
| PREFLIGHT_PASS | PRECHECK_PASS |
| NETWORK_SESSION_STARTED | (session flag under RUNNING entry) |
| CAMPAIGN_RUNNING | RUNNING (+ CYCLE_*) |
| COMPLETED/ABORTED/SEALED | same family with COMPLETING/ABORTING |

### 8.2 Allowed transitions (campaign)

```text
NOT_STARTED → AUTHORIZED
AUTHORIZED → ENABLED → ARMED → CONFIRMED → SECRETS_READY → PRECHECK_PASS
PRECHECK_PASS → RUNNING
RUNNING → CYCLE_RUNNING → CYCLE_COMPLETE → RUNNING
RUNNING → BOUND_REACHED → COMPLETING → COMPLETED → SEALED
RUNNING|CYCLE_RUNNING|CYCLE_COMPLETE → ABORTING → ABORTED → SEALED
```

### 8.3 Forbidden transitions

```text
CYCLE_COMPLETE → COMPLETED          # FORBIDDEN (one-shot bug class)
CYCLE_COMPLETE → SEALED             # FORBIDDEN
first_submit → COMPLETED            # FORBIDDEN
COMPLETED → RUNNING                 # FORBIDDEN
SEALED → *                          # FORBIDDEN
ANY → LIVE_*                        # FORBIDDEN
```

### 8.4 Persisted fields per transition (minimum)

- All transitions: `stage`, `updated_at_utc`
- RUNNING entry: `campaign_id`, `execution_start_utc`, `monotonic_start`, `duration_bound_seconds`
- CYCLE_RUNNING: `cycle_index`, `cycle_started_at_utc`
- CYCLE_COMPLETE: per-cycle counters + results
- BOUND_REACHED: `bound_reached_reason`
- COMPLETED/ABORTED: terminal reason + end timestamps
- SEALED: evidence seal digest

### 8.5 Current wrong/missing transitions

- Missing: entire CYCLE_* and BOUND_REACHED/COMPLETING chain.
- Wrong: `CAMPAIGN_RUNNING → COMPLETED` immediately after first submit in consumer.

---

## 9. Evidence contract

### 9.1 Required productive evidence schema

| Field | Exists today? | Notes |
| --- | --- | --- |
| campaign_id | NO | add |
| execution_class | partial (`mode`) | standardize `PRODUCTIVE_REAL_TESTNET_CAMPAIGN` |
| execution_start_utc | NO | add |
| execution_end_utc | NO | add |
| execution_duration_seconds | NO | monotonic-derived |
| duration_bound_seconds | NO | from SSOT |
| cycle_bound | NO | optional |
| cycles_started | NO | add |
| cycles_completed | NO | add |
| per-cycle timestamps | NO | add array |
| network_request_count | NO | add |
| order_attempt_count | partial (`submit_attempt_count`) | promote |
| testnet_order_sent_count | NO | wire_sent count |
| transport_response_count | NO | add |
| exchange_ack_count | NO | add |
| exchange_reject_count | NO | add |
| fill_count | NO | add |
| partial_fill_count | NO | add |
| client_order_ids | partial (single hardcoded) | list |
| exchange_order_ids | NO | list |
| risk_gate_results | partial (once) | per-cycle |
| kill_switch_checks | partial | per-cycle |
| emergency_control_checks | partial | per-cycle |
| confirm_consumed | YES | keep |
| confirm_replay_blocked | YES (registry) | evidence explicitly |
| secretref_runtime_proof | YES (digest/handle) | keep; no plaintext |
| testnet_account_binding | YES | keep |
| live_authorized=false | YES | keep |
| live_order_effect=NONE | YES | keep |
| campaign_terminal_status | partial (`completed&#47;aborted`) | expand |
| abort_reason | partial | expand |
| closeout fields | YES structure / always false | bind evidence |
| TESTNET_*_PROVEN fields | constants false | derive from evidence |

### 9.2 Evidence miswire to fix

`evidence_v1.write_productive_execution_evidence_v1` currently hardcodes:

```text
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
STUBBED_ACCEPTANCE=true
```

even when payload contains real wire results. Top-level evidence must reflect
actual mode/effects.

---

## 10. Closeout evaluator forensics

File: `src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/closeout_v1.py`

### 10.1 Per-field status

| Field | Current condition | Evidence source | Why false | Needed runtime evidence | Code change |
| --- | --- | --- | --- | --- | --- |
| TESTNET_ORDER_LIFECYCLE_PROVEN | module constant | none | constant=false | observed submit+ACK(+fill/cancel as required by Cap 11.4 ladder) | derive from evidence |
| TESTNET_RECONCILIATION_PROVEN | constant | none | false | account/order reconcile snapshot vs local | produce+bind |
| TESTNET_RESTART_PROVEN | constant | none | false | restart-with-open-order/position proof during/after campaign | produce+bind |
| TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN | constant | none | false | unknown-submit recovery path evidence | produce+bind |
| TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN | constant | none | false | duplicate client_order_id prevention evidence | produce+bind |
| TESTNET_KILL_SWITCH_PROVEN | constant | none | false | kill-switch trip during campaign with halt evidence | produce+bind |
| TESTNET_AUTONOMOUS_RECOVERY_PROVEN | constant | none | false | autonomous recovery within bounds | produce+bind |
| TESTNET_EVIDENCE_VERIFIED | constant | none | false | sealed evidence + independent verifier PASS | produce+bind |

Today, even with `real_productive_evidence=True`, closeout returns all PROVEN
false and `section_11_12_8_closed=false` because it reads constants, not
artifacts.

### 10.2 Boolean close conditions

```text
SECTION_11_12_8_REQUIREMENT_SATISFIED = ALL of:
  LONG_RUNNING_CAMPAIGN_PATH_EXECUTED=true
  duration/cycle bound semantics satisfied OR documented abort-before-close
  real PRODUCTIVE_REAL evidence sealed
  each TESTNET_*_PROVEN derived true from that evidence
  TESTNET_EVIDENCE_VERIFIED=true
  LIVE_AUTHORIZED=false
  SECTION_11_13_STARTED=false

SECTION_11_12_8_CANONICALLY_CLOSED =
  SECTION_11_12_8_REQUIREMENT_SATISFIED
  AND closeout.section_11_12_8_closed=true
  AND SSOT/progress binding updated only after verifier PASS
```

```text
NOT_SUFFICIENT_ALONE:
  lifecycle.completed=true
  evidence sealed=true
  wire_sent=true
  CAMPAIGN_STATUS=COMPLETED
```

---

## 11. Failure / abort semantics

| Failure | Campaign action |
| --- | --- |
| Risk gate failure | skip order if soft; **abort campaign** if entry blocked / breach class requires halt |
| Kill switch | **abort campaign** (HALT); no new side effects |
| Emergency stop | **abort campaign** after emergency command path |
| Stale market data | skip order this cycle; if persistent beyond policy → abort |
| Network timeout | bounded retry; exhaust → abort or degrade per taxonomy (no fake ACK) |
| OKX transport error | same as timeout/retry class |
| Exchange reject | continue cycle loop; count reject; abort only if fatal class |
| Invalid response | **abort** (cannot safely interpret) |
| SecretRef failure | **hard stop** before/at start; if mid-campaign → abort |
| Confirm failure | **hard stop** at start |
| Confirm replay | **hard stop** |
| Persistence failure | **hard stop / abort** |
| Evidence write failure | **abort**; preserve prior durable state |
| Evidence seal failure | **fail closed**; no closeout true |
| Duration clock anomaly (non-monotonic / rewind) | **hard stop / abort** |
| Uncaught exception | **abort**; capture reason; no PROVEN flips |

---

## 12. Implementation package (single coherent PR)

**Package name (suggested capability id):**

```text
CAPABILITY_11_SECTION_11_12_8_BOUNDED_LONG_RUNNING_AUTONOMOUS_PRODUCTIVE_TESTNET_CAMPAIGN_V1
```

Reuse existing productive entrypoint/unlock/consumer; **do not** create another
wrapper residual. Extend the actual-start + unlock surfaces.

### CHANGE catalog

#### CHANGE_ID=C01

```text
CATEGORY=GOVERNANCE/RUNBOOK
FILE=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
SYMBOL=§11.12.8 campaign bounds subsection
CURRENT_BEHAVIOR=No numeric duration/cycle bound
REQUIRED_BEHAVIOR=Define OWNER-ratified duration_bound_seconds (+ optional max_cycles + cadence + first-reached-wins)
WHY_REQUIRED=Runtime cannot legally invent bound; long-running is undefined without it
DEPENDENCIES=Owner-ratified numbers
TEST_REQUIRED=Docs/token/reference gates + constant binding test that refuses start if unbound
```

#### CHANGE_ID=C02

```text
CATEGORY=CONFIG
FILE=src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/constants_v1.py
SYMBOL=DURATION/CYCLE/CADENCE constants mirroring SSOT
CURRENT_BEHAVIOR=Absent
REQUIRED_BEHAVIOR=Single constants owner mirroring SSOT; fail-closed if unset/non-positive
WHY_REQUIRED=Runtime binding of governance bound
DEPENDENCIES=C01
TEST_REQUIRED=constant presence + refuse-zero/negative
```

#### CHANGE_ID=C03

```text
CATEGORY=STATE_MACHINE
FILE=.../durable_state_v1.py (+ constants stages)
SYMBOL=_FORWARD / ActualStartDurableStateV1
CURRENT_BEHAVIOR=CAMPAIGN_RUNNING → COMPLETED after one shot
REQUIRED_BEHAVIOR=Target stages including CYCLE_* / BOUND_REACHED / COMPLETING; persist cycle+bound fields
WHY_REQUIRED=Prevent one-shot autocomplete; restart-safe campaign state
DEPENDENCIES=C02
TEST_REQUIRED=legal/illegal transition unit tests
```

#### CHANGE_ID=C04

```text
CATEGORY=CAMPAIGN_EXECUTOR / CYCLE_LOOP
FILE=.../campaign_executor_v1.py
SYMBOL=run_campaign_lifecycle_v1 → run_bounded_long_running_campaign_v1 (or replace body)
CURRENT_BEHAVIOR=single submit; completed=True
REQUIRED_BEHAVIOR=monotonic duration loop; multi-cycle; CYCLE_COMPLETE≠COMPLETED; bound-terminated
WHY_REQUIRED=Root cause removal
DEPENDENCIES=C02,C03
TEST_REQUIRED=FIRST_SIDE_EFFECT_MUST_NOT_COMPLETE_CAMPAIGN; ONE_COMPLETED_CYCLE_MUST_NOT_COMPLETE_BEFORE_BOUND
```

#### CHANGE_ID=C05

```text
CATEGORY=COMMAND_CONSUMER
FILE=.../productive_consumer_v1.py
SYMBOL=_execute_productive_real_network_v1
CURRENT_BEHAVIOR=calls one-shot lifecycle then COMPLETED/SEALED
REQUIRED_BEHAVIOR=dispatch long-running executor; keep gates; seal only after terminal
WHY_REQUIRED=Wire productive real path to new loop
DEPENDENCIES=C04
TEST_REQUIRED=offline e2e dry/fixture control-flow proof
```

#### CHANGE_ID=C06

```text
CATEGORY=AUTHORIZATION
FILE=.../owner_go_consumer_v1.py
SYMBOL=consume_actual_start_owner_go_v1
CURRENT_BEHAVIOR=one-time GO consume
REQUIRED_BEHAVIOR=unchanged semantics; ensure per-cycle does not re-consume
WHY_REQUIRED=Preserve auth model
DEPENDENCIES=none
TEST_REQUIRED=replay still forbidden; multi-cycle single consumption
```

#### CHANGE_ID=C07

```text
CATEGORY=CONFIRM
FILE=.../hidden_confirm_v1.py
SYMBOL=latch_and_consume_confirm_digest_v1
CURRENT_BEHAVIOR=one-time digest consume
REQUIRED_BEHAVIOR=campaign-start only; replay blocked for duration of campaign registries
WHY_REQUIRED=SSOT gate
DEPENDENCIES=none
TEST_REQUIRED=confirm replay fail-closed under multi-cycle
```

#### CHANGE_ID=C08

```text
CATEGORY=SECRETREF
FILE=.../secretref_credential_v1.py + unlock vault_resolver
SYMBOL=resolve/release ephemeral material
CURRENT_BEHAVIOR=load once; release at end
REQUIRED_BEHAVIOR=lifetime=campaign; no plaintext in evidence; release on all terminals
WHY_REQUIRED=Safety
DEPENDENCIES=C05
TEST_REQUIRED=SecretRef no-plaintext test
```

#### CHANGE_ID=C09

```text
CATEGORY=RISK
FILE=.../safety_preflight_v1.py (+ cycle recheck helper)
SYMBOL=evaluate_safety_preflight_v1 / evaluate_cycle_risk_v1
CURRENT_BEHAVIOR=once with fixture RiskContext
REQUIRED_BEHAVIOR=per-cycle re-eval with real freshness/position/notional inputs from existing boundaries
WHY_REQUIRED=Autonomy + fail-closed
DEPENDENCIES=C04
TEST_REQUIRED=risk failure test
```

#### CHANGE_ID=C10

```text
CATEGORY=KILL_SWITCH
FILE=safety + campaign loop
SYMBOL=KillSwitch.check_and_block before side effects
CURRENT_BEHAVIOR=once at preflight
REQUIRED_BEHAVIOR=every cycle / before every submit
WHY_REQUIRED=MR kill-switch semantics / Cap 11.5 binding
DEPENDENCIES=C04
TEST_REQUIRED=kill-switch abort test
```

#### CHANGE_ID=C11

```text
CATEGORY=EMERGENCY_CONTROL
FILE=campaign loop
SYMBOL=emergency reaction paths
CURRENT_BEHAVIOR=inject-only flags in one-shot executor
REQUIRED_BEHAVIOR=operational emergency abort during RUNNING
WHY_REQUIRED=§11.12.7 predecessor semantics
DEPENDENCIES=C04
TEST_REQUIRED=emergency-stop test
```

#### CHANGE_ID=C12

```text
CATEGORY=OKX_ADAPTER
FILE=.../productive_execution_port_v1.py
SYMBOL=submit_order_v1 body construction
CURRENT_BEHAVIOR=Peak field names
REQUIRED_BEHAVIOR=venue-native Cap 11.4 mapping (clOrdId/instId/ordType/sz/tdMode); dry_run=false only when authorized wire
WHY_REQUIRED=Exchange accept path currently miswired
DEPENDENCIES=Cap 11.4 reuse
TEST_REQUIRED=serialization mapping unit test
```

#### CHANGE_ID=C13

```text
CATEGORY=RESPONSE_HANDLING
FILE=.../bound_testnet_http_client_v1.py + new response_mapper_v1.py
SYMBOL=request return + parse_okx_order_response_v1
CURRENT_BEHAVIOR=body discarded; wire_sent≈success
REQUIRED_BEHAVIOR=parse JSON; classify transport/exchange accept/reject; capture ordId/clOrdId/sCode/sMsg; never fake ACK
WHY_REQUIRED=ACK_COUNT=0 root cause
DEPENDENCIES=C12
TEST_REQUIRED=accepted/rejected response parse tests; exchange_order_id persistence test
```

#### CHANGE_ID=C14

```text
CATEGORY=PERSISTENCE
FILE=durable_state + optional cycle journal
SYMBOL=write/load transitions
CURRENT_BEHAVIOR=campaign stage only
REQUIRED_BEHAVIOR=persist campaign+cycle counters/ids/bound fields restart-safely
WHY_REQUIRED=TESTNET_RESTART_PROVEN path enablement
DEPENDENCIES=C03
TEST_REQUIRED=persistence roundtrip + illegal transition
```

#### CHANGE_ID=C15

```text
CATEGORY=EVIDENCE
FILE=.../evidence_v1.py
SYMBOL=write_productive_execution_evidence_v1
CURRENT_BEHAVIOR=hardcoded stubbed/none top-level; missing counters/timestamps
REQUIRED_BEHAVIOR=full §9 schema; truthful top-level effects; duration fields
WHY_REQUIRED=Closeout cannot bind lies/omissions
DEPENDENCIES=C04,C13
TEST_REQUIRED=timestamp/duration/counters tests
```

#### CHANGE_ID=C16

```text
CATEGORY=SEAL
FILE=evidence_v1 seal/verify
SYMBOL=seal_evidence_dir_v1
CURRENT_BEHAVIOR=works
REQUIRED_BEHAVIOR=seal only after terminal; verify required for closeout
WHY_REQUIRED=TESTNET_EVIDENCE_VERIFIED
DEPENDENCIES=C15
TEST_REQUIRED=seal verify PASS/FAIL
```

#### CHANGE_ID=C17

```text
CATEGORY=CLOSEOUT
FILE=.../closeout_v1.py
SYMBOL=evaluate_section_11_12_8_closeout_v1
CURRENT_BEHAVIOR=reads false constants; ignores evidence content
REQUIRED_BEHAVIOR=accept sealed evidence artifact; derive each TESTNET_*_PROVEN; closed only if all true
WHY_REQUIRED=§11.12.8 cannot close otherwise
DEPENDENCIES=C15,C16
TEST_REQUIRED=positive + negative closeout tests
```

#### CHANGE_ID=C18

```text
CATEGORY=COMMAND_CONSUMER / WIRING
FILE=scripts/ops/run_section_11_12_8_real_productive_testnet_execute_operator_entrypoint_v1.py
 + unlock_orchestrator_v1.py
SYMBOL=main / execute_unlocked_productive_path_v1
CURRENT_BEHAVIOR=PRODUCTIVE_TESTNET_CAMPAIGN_STARTED forced false; one-shot
REQUIRED_BEHAVIOR=long-running path; truthful campaign started flags for runtime evidence (package constants may remain historical—runtime evidence must be truthful)
WHY_REQUIRED=Operator path is the only Owner execute edge
DEPENDENCIES=C05–C17
TEST_REQUIRED=entrypoint wiring contract test
```

#### CHANGE_ID=C19

```text
CATEGORY=TESTS
FILE=tests/ops/test_section_11_12_8_bounded_long_running_* (new) + extend existing
SYMBOL=suite in §14
CURRENT_BEHAVIOR=tests encode one-shot acceptance
REQUIRED_BEHAVIOR=prove multi-cycle + bound + response + closeout + LIVE block + §11.13 unstarted
WHY_REQUIRED=Prevent merging another one-shot “campaign”
DEPENDENCIES=all runtime changes
TEST_REQUIRED=this change IS the test package
```

#### CHANGE_ID=C20

```text
CATEGORY=RUNBOOK / SPEC DOCS
FILE=docs/ops/specs/<new capability spec>.md + evidence package under docs/evidence/
SYMBOL=capability spec + claims
CURRENT_BEHAVIOR=N/A
REQUIRED_BEHAVIOR=document package claims; explicitly SECTION_11_12_8_CLOSED=false until post-merge productive run
WHY_REQUIRED=governance evidence hygiene
DEPENDENCIES=C01–C19
TEST_REQUIRED=docs reference/token gates
```

```text
TOTAL_REQUIRED_CHANGE_COUNT=20
```

---

## 13. Implementation order (dependency order)

1. **C01** SSOT bound definition (Owner-ratified numbers)
2. **C02** Constants mirror + refuse-if-unbound
3. **C03** State machine + durable fields
4. **C12** Venue-native OKX request mapping
5. **C13** Response parse / ACK-reject semantics
6. **C04** Multi-cycle wallclock campaign executor
7. **C09/C10/C11** Per-cycle risk / kill / emergency
8. **C14** Persistence / cycle journal
9. **C15/C16** Evidence + seal truthfulness
10. **C17** Closeout evaluator binding
11. **C05/C06/C07/C08/C18** Consumer/auth/confirm/secretref/entrypoint wiring
12. **C19** Tests (authored alongside, green before merge)
13. **C20** Capability spec + docs evidence package reconciliation

No organizational PR-splitting: ship as **one** coherent package once green.

---

## 14. Test plan (pre-merge, offline)

Must prove we are **not** merging another one-cycle autocomplete executor.

| Test | Intent |
| --- | --- |
| unit state machine | legal/illegal transitions |
| multi-cycle deterministic executor | N cycles with stub transport |
| duration-bound test | monotonic bound terminates campaign |
| cycle-bound test | if SSOT defines max_cycles |
| no-signal multi-cycle | cycles_completed>1 with order_attempt_count=0 |
| risk failure | abort/skip per matrix |
| kill-switch | abort, no further submits |
| emergency-stop | abort path |
| OKX accepted response parse | sCode=0 → ack++ / ordId stored |
| OKX rejected response parse | reject++ / no fake ack |
| exchange order ID persistence | durable + evidence |
| evidence timestamp/duration | start/end/duration present |
| evidence counters | network/order/ack/reject |
| closeout positive | all PROVEN true only with synthetic real-shaped evidence |
| closeout negative | sealed one-shot evidence does not close |
| confirm replay fail-closed | |
| SecretRef no-plaintext | |
| LIVE hard-block regression | live host/url/mode refused |
| §11.13 remains unstarted | constants + closeout |
| **FIRST_SIDE_EFFECT_MUST_NOT_COMPLETE_CAMPAIGN** | explicit regression |
| **ONE_COMPLETED_CYCLE_MUST_NOT_COMPLETE_LONG_RUNNING_CAMPAIGN_BEFORE_BOUND** | explicit regression |
| offline e2e dry/fixture control-flow | full gate→loop→seal without network |

Separate later: real Owner-GO productive run (out of scope for implementation PR).

---

## 15. Definition of Done for the implementation PR

Merge-ready **only if** all are true on the PR head:

```text
LONG_RUNNING_CAMPAIGN_PATH_PRESENT=true
MULTI_CYCLE_EXECUTOR_WIRED=true
ONE_SHOT_AUTOCOMPLETE_REMOVED=true
CANONICAL_DURATION_BOUND_DEFINED=true
PRODUCTIVE_REAL_PATH_WIRED=true
OKX_TESTNET_RESPONSE_PATH_WIRED=true
ACK_REJECT_SEMANTICS_PRESENT=true
EXCHANGE_ORDER_ID_CAPTURE_PRESENT=true
EVIDENCE_TIMESTAMPS_PRESENT=true
EVIDENCE_DURATION_PRESENT=true
CLOSEOUT_EVALUATOR_WIRED=true
LIVE_HARD_BLOCK_PRESERVED=true
SECTION_11_13_STARTED=false
```

And must **also** assert:

```text
SECTION_11_12_8_CANONICALLY_CLOSED=false
SECTION_11_12_8_CLOSED_CLAIM_IN_PR=false
PRODUCTIVE_TESTNET_CAMPAIGN_RUNTIME_EXECUTED_IN_PR=false
NETWORK_EFFECT_IN_PR_TESTS=NONE_OR_STUBBED
ORDER_EFFECT_IN_PR_TESTS=NONE_OR_STUBBED
LIVE_ORDER_EFFECT=NONE
```

Implementation PR proves **path presence**, not §11.12.8 closure.

---

## 16. Post-merge execution proof (separate Owner-GO)

After merge, expected real run:

```text
OWNER_GO EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
→ preflight (gates)
→ authorization + confirm + SecretRef
→ long-running campaign start (campaign_id, start_utc, bound)
→ repeated autonomous cycles (evaluate → maybe order → record)
→ bounded termination (DURATION or CYCLE)
→ evidence materialization (full schema)
→ seal + verify
→ closeout evaluator on real evidence
→ SECTION_11_12_8_CLOSED=true OR fail-closed remains OPEN with reasons
```

Expected runtime artifacts:

- `durable_state&#47;actual_start_durable_state_v1.json` (or successor schema) with RUNNING→…→SEALED
- `execution_evidence&#47;productive_execution_evidence_v1.json` with duration/cycle counters
- `execution_evidence&#47;MANIFEST.sha256`
- operator stdout status block with truthful NETWORK/ORDER effects TESTNET-only
- closeout object with each TESTNET_*_PROVEN derived

If any PROVEN field lacks real evidence → section remains open (fail-closed).

---

## Appendix A — Explicit non-goals of the later implementation package

- No Live unlock / §11.13 start
- No trading-core / Alpha mutation
- No second SSOT
- No new wrapper residual parallel to unlock/actual-start
- No inventing duration numbers outside Owner-ratified SSOT text
- No claiming §11.12.8 closed inside the implementation PR

## Appendix B — One-shot smoking-gun excerpt (current main)

`run_campaign_lifecycle_v1` performs exactly one `submit_order_v1`, synthesizes a
single heartbeat, then sets `completed=True`. The productive consumer then
transitions durable state to `COMPLETED` and `SEALED`. That is the complete
technical reason `LONG_RUNNING_CAMPAIGN_PATH_PRESENT=false` despite a working
PRODUCTIVE_REAL wire path.

## Appendix C — Status snapshot at spec authorship

```text
ORIGIN_MAIN_SHA=35519be2684b65491fbe53b09f82e91370e7cc89
CURRENT_PRODUCTIVE_PATH_CLASS=SINGLE_BOUNDED_ONE_SHOT_PRODUCTIVE_REAL
LONG_RUNNING_PATH_PRESENT=false
ONE_SHOT_AUTOCOMPLETE_ROOT_CAUSE_IDENTIFIED=true
CANONICAL_DURATION_BOUND_PRESENT=false
GOVERNANCE_CHANGE_REQUIRED=true
RUNTIME_CHANGE_REQUIRED=true
STATE_MACHINE_CHANGE_REQUIRED=true
OKX_RESPONSE_CHANGE_REQUIRED=true
EVIDENCE_CHANGE_REQUIRED=true
CLOSEOUT_CHANGE_REQUIRED=true
TEST_CHANGE_REQUIRED=true
TOTAL_REQUIRED_CHANGE_COUNT=20
COMPLETE_END_TO_END_GRAPH_ANALYZED=true
IMPLEMENTATION_PACKAGE_COHERENT=true
SECTION_11_12_8_CLOSED=false
SECTION_11_13_STARTED=false
NEXT_SAFE_STEP=OWNER_GO_IMPLEMENT_BOUNDED_LONG_RUNNING_PACKAGE_PER_THIS_SPEC_INCLUDING_SSOT_DURATION_BOUND
```
