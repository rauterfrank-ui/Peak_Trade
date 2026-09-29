# WP-1 — Double-Play OLD→CURRENT Contract Diff / Forensic Adjudication V1

```text
MODE=READ_ONLY_FORENSICS
IMPLEMENTATION=false
RUNTIME_EXECUTION=false
REPOSITORY_MUTATED=false
```

## 1. Baselines

| Field | Value |
| --- | --- |
| `CURRENT_ORIGIN_MAIN_SHA` | `8475ebb948d246efd0c70a1cf4101fd3bf1b54db` |
| `CURRENT_ORIGIN_MAIN_TREE` | `db42efb40cc3a335d221646dc00b9a063fd0cf8e` |
| `HISTORICAL_SHA` | `23dccab71eac79c8d39498bbe5bfc84bd54ebf9d` (2026-09-26 23:50:10 +0200) |
| `HISTORICAL_TREE` | `700f0264f62e62a028597787dea00de284617294` |
| `HISTORICAL_ENTER_EVIDENCE_SHA` | `34e0f887f351137a3566fe73c400b2fa570ff668` |
| `FIRST_POST_TARGET_DP_WIRING` | `d590b8142210680805f8dc159c5a2fb684e87737` (#6889 F1/M9 consumer wiring) |
| `WORKTREE_STATUS` | Clean; `main` = `origin/main`; no checkout/reset performed |

## 2. Evidence method

- Read-only `git diff 23dccab71..8475ebb`, `git show`, and targeted `rg` on CURRENT worktree and historical blobs.
- No runtime, no mutation, no census regeneration.
- `config/governance/current_system_census_graph_v1/source_v1.json` **not** used as authority (`AUTHORITY=NONE`).
- CURRENT claims tagged `PROVEN_CURRENT` only with file/commit evidence; no plausibility fill-in.

## 3. Verified CURRENT Double-Play entry / owner

**PROVEN_CURRENT**

| Role | Symbol / path |
| --- | --- |
| Integrated DP orchestrator | `trading.master_v2.integrated_offline_trading_logic_replay_v1.run_integrated_offline_trading_logic_replay_v1` |
| Productive one-shot host | `src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py` → `run_current_productive_master_v2_runtime_cycle_v1` |
| Sole trading authority constant | `docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json` → `run_integrated_offline_trading_logic_replay_v1` |

Historical target used the **same** integrated replay symbol; verified at `23dccab71`.

## 4. OLD→CURRENT contract matrix (decision-effective)

Full machine rows: `WP_DOUBLE_PLAY_OLD_CURRENT_CONTRACT_DIFF_V1.json` (`contracts[]`).

Summary table (abbreviated):

| contract_id | layer | semantic_role | classification | decision_effect |
| --- | --- | --- | --- | --- |
| DP-OWNER-01 | K | integrated orchestrator | EXACT_MATCH | none |
| POLICY-CANONICAL-01 | F | distances / confirmation_epochs | EXACT_MATCH | none |
| POLICY-DIRECTIONAL-01 | E | 0.001 / 0.005 / 0.01 | EXACT_MATCH | none |
| CMC-PRICE-01 | A | mark/index provenance | ADAPTER_REQUIRED | admission fail-closed |
| G17-CMC-BIND-01 | G | typed vol → CMC | ADAPTER_REQUIRED | estimate presence timing |
| F1M9-PRESENCE-GATE-01 | G | underlying presence eval | CURRENT_EQUIVALENT | none when wired |
| F1M9-CONSUMER-PATH-01 | G | post-d590b8142 wiring | ADAPTER_REQUIRED | seam/admission |
| F1M9-MAX-AGE-ENFORCEMENT-01 | G | 600s stale enforcement | SEMANTIC_CONFLICT | extra alpha block |
| F1M9-PRESENCE-GATE-NONE-01 | G | null gate fail-closed | SEMANTIC_CONFLICT | hard replay block |
| C1-DISTINCT-DUPLICATE-01 | C | observation acceptance | EXACT_MATCH | none |
| C1-HOST-BINDING-01 | C | productive C1 host | EXACT_MATCH | none |
| SCOPE-CONFIRM-01 | B | scope generator / epochs | EXACT_MATCH | none |
| SINGLE-LANE-LIFECYCLE-01 | C | Cap-61 lane routing | SEMANTIC_CONFLICT | confirmation path |
| C3-INTEGRATION-WIRING-01 | E | persist prior_carrier | SEMANTIC_CONFLICT | carrier merge |
| C3-PURE-EVAL-01 | E | C3 progress math | EXACT_MATCH | none |
| SIDESTATE-TRANSITION-01 | D | `transition_state` owner | EXACT_MATCH | none |
| RUNTIME-SCOPE-01 | D | RuntimeScopeState in replay | EXACT_MATCH | none |
| LAYERED-CORE-OBS-INIT-01 | L | episode obs seeding | SEMANTIC_CONFLICT | cold-start C1 |
| CURSOR-PERSIST-01 | L | sidestate cursor file | EXACT_MATCH | none |
| RECON-REPLAY-ENUM-01 | H | ReconciliationState enum | ADAPTER_REQUIRED | same when admitted |
| RECON-ADMISSION-GATE-01 | H | upstream recon witness | ADAPTER_REQUIRED | fail-closed wrapper |
| POSITION-FLAT-01 | H | flat / position inputs | EXACT_MATCH | none |
| SURVIVAL-01 / SUITABILITY-01 | I | admission gates | EXACT_MATCH | none |
| COMPOSITION-01 | J | CONFIRMED admissibility | EXACT_MATCH | none |
| ENTRY-EXIT-01 | K | entry/exit policy core | EXACT_MATCH | none |
| EXIT-PRODUCERS-01 | K | host exit binding | EXACT_MATCH | none |
| OUTGOING-CARRIER-01 | L | t+1 confirmation carrier | SEMANTIC_CONFLICT | persistence |
| PRODUCTIVE-TYPED-VOL-FLAG-01 | G | require presence gate | EXACT_MATCH | none |
| RUNTIME-ADMISSION-F1M9-01 | G | F1/M9 surface admission | ADAPTER_REQUIRED | gate before DP |

**Counts:** total **30** — EXACT_MATCH **17**, CURRENT_EQUIVALENT **1**, ADAPTER_REQUIRED **8**, SEMANTIC_CONFLICT **6**, MISSING **0**, UNKNOWN **0**.

## 5. Authority / boundary matrix

| Boundary | WHO OWNS | WHO PRODUCES | WHO CONSUMES | AUTHORITY TRANSFER? |
| --- | --- | --- | --- | --- |
| CMC / MD | `canonical_market_context_v1` binders | productive host + G17 join | integrated replay | Data only |
| Typed vol presence | `double_play_runtime_typed_volatility_presence_gate_v1` | F1/M9 consumer path | integrated replay (pre-scope) | Gate only; no selection |
| F1/M9 seam | governance ledgers + seam join | host `_resolve_f1_m9_governed_seam_*` | consumer wiring | Transport; `RECONCILIATION_AUTHORITY_TRANSFER=false` |
| C1 acceptance | `distinct_market_observation_acceptor_v1` | Cap-6.1 host binding | integrated replay via `_resolve_c3_confirmation_binding_v1` | None |
| Scope confirmation | `deterministic_scope_event_generator_v1` | integrated replay | C3 / SideState inputs | None |
| C3 status | `directional_assessment_confirmation_integration_v1` | integrated replay selected lane | Survival/Suitability (non-confirming) | Sole confirm→status |
| Composition | `double_play_composition_matrix_v1` | integrated replay | `transition_state` input | Sole CONFIRMED admissibility |
| SideState | `double_play_state.transition_state` | integrated replay | entry/exit + persistence | Sole directional FSM writer |
| Reconciliation enum | entry/exit policy consumer | **OLD:** host constant **CURRENT:** `ProductiveMasterV2ReconciliationAdmissionV1` | `evaluate_double_play_entry_exit_policy_v0` | Witness only; no recon ownership transfer |
| Productive host | `current_productive_master_v2_runtime_cycle_v1` | venue GET inputs | calls integrated replay | Orchestration only |

**Post-historical shifts (proven):**

1. Typed-vol **admission stack** expanded (F1/M9 consumer + max-age enforcement + seam bootstrap).
2. Reconciliation **witness** required at host; no longer implicit constant.
3. Single-lane **carrier threading** moved from `prior_presence` decode to `prior_carrier` + `carrier_after_lifecycle`.
4. Layered-core bind **observation seed** source changed (CMC mark vs finalized closes grid).

No evidence that `transition_state`, composition matrix, or entry/exit policy **modules** changed ownership.

## 6. State / persistence / replay diff

| Carrier | OLD productive path | CURRENT productive path | Classification |
| --- | --- | --- | --- |
| SideState + direction | From cursor restore + replay output | Same cursor module (zero diff) | EXACT_MATCH |
| RuntimeScopeState | Integrated replay `_resolve_runtime_scope_state_for_cycle_v1` | Unchanged core logic | EXACT_MATCH |
| Cap-61 dual carrier | persist without lifecycle carrier | persist with `prior_carrier=lifecycle.carrier_after_lifecycle` | SEMANTIC_CONFLICT |
| Layered core episode | Close-based obs candidates | CMC-mark / multi-close grid + carryforward flag | SEMANTIC_CONFLICT |
| F1/M9 ledgers | Seam optional via presence join | Canonical apply/threshold ledgers + bootstrap | ADAPTER_REQUIRED |

Reload/replay: cursor restore owner unchanged; layered-core store restore path extended (not removed).

## 7. F1 / M9 / typed-vol adjudication

| Aspect | OLD (`23dccab71`) | CURRENT (`8475ebb`) |
| --- | --- | --- |
| Producer into CMC | G17 scaffold + bind join | Same + **DUPLICATE_NOOP reuse** (`G17-CMC-BIND-01`) |
| Presence evaluation | Direct `evaluate_double_play_runtime_typed_volatility_presence_gate_v1` after `resolve_governed_runtime_seam_for_presence_gate_v1` | Same evaluator inside `evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1` |
| Alpha boundary | `presence_gate.alpha_scope_entry_authority_allowed` | Same baseline then **`apply_bounded_enforcement_to_double_play_alpha_v1`** (600s ratified stale → block) |
| Fail-closed | Missing estimate → demote gate | Additional: consumer deny, `presence_gate is None` → full replay block |
| Core module diff | `double_play_runtime_typed_volatility_presence_gate_v1.py` | **Zero diff** H..CURRENT |

**Adjudication:** Lossless OLD→CURRENT mapping **without** boundary adapter is **CONFLICTING_CURRENT** (stale enforcement + null-gate path). Mapping **with** host/boundary adapter and **without** DP core edits is **principally ADAPTER_REQUIRED** (not yet behaviorally proven — WP-2).

## 8. Reconciliation / position / flat adjudication

| Aspect | OLD | CURRENT |
| --- | --- | --- |
| Replay input | `reconciliation_state=ReconciliationState.RECONCILED` hardcoded in runtime cycle | `master_v2_reconciliation_admission.integrated_replay_reconciliation_state_v1()` |
| Upstream gate | None in host | `ProductiveMasterV2ReconciliationAdmissionV1` with `gate_ok`, `alpha_enabled`, digest |
| Entry/exit consumer | `double_play_entry_exit_policy_v0` | Unchanged module (zero diff) |
| Position / flat | `venue_flat`, `existing_position_side`, `position_state` wired into replay | Same fields; no proven semantic change in diff |

When admission validates productive upstream gate, replay still receives **`ReconciliationState.RECONCILED`**. Fail-closed admission is **host-only** delta.

**Mapping without DP core change:** **PROVEN_CURRENT** (host must supply valid admission witness equivalent to historical implicit trust).

## 9. C1 / cursor / confirmation adjudication

- **C1 acceptor + Cap-6.1 host:** zero diff H..CURRENT → DISTINCT/DUPLICATE semantics **EXACT_MATCH**.
- **Single-lane lifecycle (`single_lane_confirmation_activation_v1.py`):** large diff; integrated replay callsite changed from `prior_presence=prior_presence_from_dual_carrier_v1(prior_carrier)` to `prior_carrier=prior_carrier`.
- **Historical dual-slot decode:** both bull and bear authoritative → fail-closed inactive.
- **CURRENT decode:** requires explicit lane from elementary direction; adds `SWITCH_RESUME_PERSISTENT_LANE`.

**Exactly-one advance per accepted DISTINCT observation:** **CONFLICTING_CURRENT** at the Cap-61 routing boundary (pure C3 math unchanged). WP-2 must prove per-cycle epoch counters.

**Reset / double-advance / stagnation:** **CONFLICTING_CURRENT** — CURRENT may **reduce** stagnation (resume path) or **change** discard rules; static proof insufficient for net behavior → WP-2.

## 10. Core equivalence proof

**CORE_UNCHANGED_PROOF (git diff empty H..CURRENT):**

- `double_play_state.py` (`transition_state`)
- `double_play_entry_exit_policy_v0.py`
- `double_play_composition_matrix_v1.py`
- `double_play_survival.py`
- `deterministic_scope_event_generator_v1.py`
- `directional_assessment_v1.py`
- `directional_assessment_confirmation_integration_v1.py`
- `post_confirmation_survival_suitability_composition_binding_v1.py`

Integrated replay **orchestration** differs (F1/M9 path, single-lane wiring); **decision modules invoked** for scope/survival/suitability/composition/entry-exit/state transition are unchanged.

## 11. Boundary delta set

1. F1/M9 consumer + runtime admission + seam/ledger bootstrap  
2. Bounded 600s max-age enforcement overlay on alpha  
3. G17 CMC bind reuse on DUPLICATE_NOOP  
4. Productive canonical price provenance gate  
5. Master V2 reconciliation admission witness  
6. Single-lane lifecycle + C3 persist carrier threading  
7. Layered-core episode observation initialization  

## 12. Minimal divergence set (WP-2 focus)

1. `F1M9-MAX-AGE-ENFORCEMENT-01`  
2. `F1M9-PRESENCE-GATE-NONE-01` / `F1M9-CONSUMER-PATH-01`  
3. `G17-CMC-BIND-01`  
4. `SINGLE-LANE-LIFECYCLE-01` + `C3-INTEGRATION-WIRING-01` + `OUTGOING-CARRIER-01`  
5. `LAYERED-CORE-OBS-INIT-01`  
6. `RECON-ADMISSION-GATE-01` (fail-closed only; enum mapping when pass)  

## 13. Blast radius

| Zone | Radius |
| --- | --- |
| DP pure core (state, composition, entry/exit, survival, suitability, scope math) | **Unchanged** — no merge required for restore |
| Integrated replay shell | **Low** — 38 lines net; wiring only |
| Productive host | **High** — reconciliation, F1/M9, provenance, G17 bind, layered core |
| Governance F1/M9 plane | **New since H** — consumer module + decisions (authorized on CURRENT main) |

## 14. Pflichtfragen (1–10)

1. **CURRENT zentraler DP Core decision-äquivalent?** → **PROVEN_CURRENT** (zero diff on core modules; orchestration boundary deltas listed).  
2. **F1/M9 typed-vol verlustfrei ohne Core-Änderung?** → **CONFLICTING_CURRENT** (stale enforcement + fail-closed consumer paths not present on OLD). Boundary adapter may suffice; not lossless on identity mapping alone.  
3. **Reconciliation/position/flat verlustfrei ohne Core?** → **PROVEN_CURRENT** (same replay enum when admission passes; position/flat wiring unchanged).  
4. **C1 + cursor + scope confirmation: one advance per DISTINCT?** → **CONFLICTING_CURRENT** (single-lane lifecycle delta).  
5. **Reset/double-advance/stagnation path?** → **CONFLICTING_CURRENT** (lifecycle + layered init; needs WP-2 traces).  
6. **SideState / RuntimeScopeState owner/persist/reload äquivalent?** → **CONFLICTING_CURRENT** (core owners unchanged; **layered init + carrier persist** differ).  
7. **C3 carrier + directional thresholds äquivalent?** → **PROVEN_CURRENT** (policy values + C3 integration module unchanged).  
8. **Survival/suitability/composition/entry-exit im Core äquivalent?** → **PROVEN_CURRENT**.  
9. **WP-2 test deltas:** see JSON `pflichtfragen.q9_wp2_named_deltas`.  
10. **Core-Änderung für OLD-effective restore nötig?** → **PROVEN_NO** — deltas isoliert vor Core; `transition_state`, composition matrix, entry/exit policy modules unchanged.

## 15. Blockers / unknowns

```text
BLOCKER=NONE
MISSING_EVIDENCE=[]
AFFECTED_CONTRACTS=SINGLE-LANE-LIFECYCLE-01,LAYERED-CORE-OBS-INIT-01
WHY_STATIC_EVIDENCE_IS_INSUFFICIENT=Cycle-level confirmation counters and cold-start epoch seeding require differential replay.
NEXT_REQUIRED_PROOF=WP-2 golden vector (shared fixture sequence, cycle-by-cycle)
```

## 16. WP-2 input contract

WP-2 SHALL hold **DP core modules** fixed at CURRENT (`8475ebb`) and vary only:

- Host/boundary inputs aligned to OLD effective contract (or explicit adapter flags per delta ID).  
- Compare: scope event, confirmation epochs, SideState, C3 status, survival/suitability, composition, entry/exit outcome, outgoing cursor/carrier **per cycle**.  
- Mandatory delta IDs: minimal divergence set §12.  
- Success: behavioral equivalence at DP boundary OR isolated failure pinned to a named `contract_id`.

## 17. Final adjudication

Restoration strategy **RESTORE_OLD_EFFECTIVE_DP_CONTRACT_ON_CURRENT_HOST** remains supported: **core unchanged**, proven divergence **concentrated in host wiring and F1/M9/Cap-61/layered-init boundaries**. No repository rollback required for WP-2 design. Implementation **not** authorized by this WP.

---

### Key git evidence (integrated replay wiring delta)

Post-`d590b8142`, integrated replay replaces direct presence evaluation with F1/M9 consumer path and adds fail-closed when `presence_gate is None`; single-lane call uses `prior_carrier=` instead of `prior_presence_from_dual_carrier_v1`.

Historical productive host set `reconciliation_state=ReconciliationState.RECONCILED` inline; CURRENT requires `ProductiveMasterV2ReconciliationAdmissionV1`.
