# HARD_FACTS_SYSTEM_CLOSURE_V1

## Baseline

| Field | Value |
|-------|-------|
| BASELINE_SHA (origin/main) | `5b606f6daf322995a7f26a7208bba70a43cdd392` |
| CLOSURE_BRANCH | `feat/hard-facts-system-closure-v1` |
| DESKTOP_EVIDENCE_ROOT | `/Users/frnkhrz/Desktop/WHOLE_SYSTEM_FITNESS_MATRIX_V1:Peak_Trade_WHOLE_SYSTEM_FITNESS_MATRIX_V1.` |

## Desktop Evidence Inventory (forensic input only)

- `Peak_Trade_CURRENT_TRADING_CRITICAL_QUALIFICATION_GUARDRAIL_VETO_STACK_FORENSIC_CLOSURE_V1.md`
- `Peak_Trade_CURRENT_MF_N5_MEMBERSHIP_ROTATION_LANE_REPLACEMENT_FORENSIC_PROOF_V1.md`
- `Peak_Trade_CURRENT_TREASURY_CAPITAL_EQUITY_RESERVATION_SETTLEMENT_FORENSIC_CLOSURE_V1.md`
- `Peak_Trade_WHOLE_SYSTEM_FITNESS_MATRIX_V1/` (authority_matrix.json, README, graphs)
- Additional golden-vector / matrix markdown siblings in the same Desktop folder

Epistemic labels: **PROVEN_CURRENT | UNKNOWN_CURRENT | CONFLICTING_CURRENT | VIOLATED_CURRENT** — adjudicated against CURRENT code in this branch.

## Case-Switch Adjudication

| Forensic memory | CURRENT equivalent | Status |
|-----------------|-------------------|--------|
| Monolithic "Case-Switch" | Composite: `trading_gate`, `safety_mode`, `HostExitPolicyBindingV1`, durable kill-switch file, typed-vol presence gate, S5 terminal guards | **PROVEN_CURRENT** (distributed stack) |
| Kill-switch → MV2 | Was default `killstate_active=false` in MV2 cycle | **VIOLATED_CURRENT → CLOSED** via `durable_kill_switch_mv2_binding_v1` + MV2 cycle wiring |
| Lane purge on instrument change | Cursor restore checks `instrument_id`; full purge | **PARTIAL → instrument epoch + RESET adjudication** in `instrument_sensitive_identity_v1` |

## Authority Matrix (enforced constants)

- Cap22 = ranking context only
- Cap23 = sole selection authority (unchanged owners)
- Cap24 = bind-only
- MV2 = orchestration / qualification framework
- Double Play = SideState + composition + entry/exit semantics
- Intelligence / learning / optimization / meta = zero productive trading decision authority
- PRE_EXTERNAL terminal; POST forbidden (`POST_ALLOWED=false`)

## Changed Components

| Component | Change |
|-----------|--------|
| `src/ops/hard_facts_system_closure_v1/*` | New closure package: handoff, identity, health feedback, rotation, treasury/restart guards, kill-switch binding, authority proof |
| `current_productive_master_v2_runtime_cycle_v1.py` | Durable kill-switch → `killstate_active` / `killstate_trigger` on exit producers |
| `control_plane_v1.py` | Optional `hard_facts_cap22_handoff` → Cap22 → POLICY_A → topology before orchestrator |
| `tests/ops/test_hard_facts_system_closure_v1.py` | Proof matrix (16 cases) |

## Wiring Before / After

**Before:** Cap22 ranking consumed manually; selector isolated; MV2 host ignored durable kill-switch file; lane health not formalized for membership feedback.

**After:** `execute_hard_facts_cap22_to_mf_n5_handoff_v1` chains Cap22 (productive-real gate) → POLICY_A selector → topology consumer; staged control plane may invoke via `hard_facts_cap22_handoff`; MV2 reads durable kill state through single binding owner.

## Remaining UNKNOWN / BLOCKERS

| Item | Label | Notes |
|------|-------|-------|
| Post-trade PnL → Treasury → 29P closed loop | **UNKNOWN_CURRENT** | No canonical productive settlement owner (Desktop forensic confirms) |
| Global kill-switch blocking mandatory exit | **UNKNOWN_CURRENT** | Safety exit armed; dedicated global "block exit" KS not proven |
| Full instrument purge on lane reuse (all subsystems) | **CONFLICTING_CURRENT** | Cursor id check PROVEN; G17/CMC/scope purge per lane root PROVEN in addressing join tests; not all states re-keyed in one owner |

## OUT OF SCOPE (unchanged)

Ranking quality, weights, tuning, autonomy supervisor, N>1 enablement, POST, live venue writes, Law-Map rebuild.

## Signal-Semantics / Autonomy Phase Blockers

1. Settlement / realized PnL productive owner absent → treasury recycle not provable end-to-end.
2. Ranking feature quality and score semantics not in scope of this closure.
3. Continuous daemon / autonomous runtime supervisor explicitly out of scope.

## Test / Proof Matrix

See `tests/ops/test_hard_facts_system_closure_v1.py` — covers authority invariants, Cap22 handoff, synthetic rejection, instrument identity RESET/SAFE_CARRY, open-position rotation custody, HOLD/global HALT non-churn, lane-fatal replacement when flat, durable KS → trading_gate BLOCKED, treasury stale fail-closed, reservation epoch guard, restart confirmation guard, PRE_EXTERNAL/POST flags.
