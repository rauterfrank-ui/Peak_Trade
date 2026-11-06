# PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1

---
docs_token: DOCS_TOKEN_PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1
STATUS: CAPABILITY_AVAILABLE
scope: Deferred-Work Recovery Register and Rotation-Policy resubmission (Capability 0.4); governance recovery only
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
IMPLEMENTATION_AUTHORIZED: false
ACTIVATION_AUTHORIZED: false
CORE_LOGIC_CHANGE: false
ACTIVATION_STATE: BOUND_NOT_ACTIVATED
HARD_STOP: true
DOCUMENT_CLASS: CURRENT_RUNTIME_TRUTH
---

```text
REGISTER_ID=PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1
CAPABILITY_RECOVERY_ID=CAPABILITY_0_4_DEFERRED_WORK_RECOVERY_REGISTER_ROTATION_POLICY_RESUBMISSION_V1
MACHINE_READABLE_SSOT=docs/governance/deferred_work_recovery_register_v1.json
AUTHORITY_OWNER=ops.deferred_work_recovery_register_contract_v1
PARALLEL_REGISTER_FORBIDDEN=true
CURRENT_RUNTIME_CHANGED=false
```

## Purpose

Canonical Deferred-Work Recovery Register for Peak Trade.

This surface formally re-admits forgotten or reminder-only required capabilities into the active trading roadmap with owner, dependencies, review trigger, and target phase — without authorizing implementation or activation.

## Semantic guards (must remain true)

```text
TOP20_IS_CONTEXT_ONLY=true
SINGLE_SELECTED_FUTURE_IS_CURRENT_AUTHORITY=true
TOP_N_ACTIVE_SET_IS_DEFERRED=true
TOP5_PRODUCTIVE=false
TOP5_REGRESSED=false
MULTI_FUTURE_IMPLEMENTED=false
MULTI_FUTURE_AUTHORIZED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
PHASE_1_SELECTION=SINGLE_SELECTED_FUTURE
PHASE_1_MAX_POSITIONS=1
ROTATION_POLICY_RATIFIED=false
ROTATION_IMPLEMENTATION_STARTED=false
CURRENT_RUNTIME_CHANGED=false
DASHBOARD_RANKING_IS_RUNTIME_AUTHORITY=false
```

## Registered deferred required capability

### MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0

| Field | Value |
|---|---|
| CLASSIFICATION | `DEFERRED_REQUIRED_CAPABILITY` |
| CURRENT_STATE | `POLICY_NOT_RATIFIED_IMPLEMENTATION_NOT_AUTHORIZED` |
| TARGET_STATE | `ROTATION_POLICY_RATIFIED_READY_FOR_SEPARATE_IMPLEMENTATION_GO` |
| TARGET_PHASE | `PHASE_6` |
| IMPLEMENTATION_AUTHORIZED | `false` |
| ACTIVATION_AUTHORIZED | `false` |
| CURRENT_RUNTIME_EFFECT | `NONE` |
| PHASE_1_SELECTION | `SINGLE_SELECTED_FUTURE` |
| PHASE_1_MAX_POSITIONS | `1` |
| MULTI_FUTURE_RUNTIME_AUTHORIZED | `false` |

**Owner requirement (summary):** dynamically evaluated futures universe; ranking as context; later controlled promotion/demotion; replacement hysteresis; state retention for open positions (no hard removal with open position); global risk/capital allocation; per-instrument state isolation; restart/recovery semantics; Top-N-capable target architecture; a later first ratified configuration may use `N=5`; Top-5 is currently neither productive nor activated.

**Trading-path value:**

```text
Universe
→ Ranking
→ spätere Active-Set Selection
→ per-instrument Market State
→ Master V2
→ Double Play
→ Global Risk
→ Global Safety
→ Intent Arbitration
→ Execution
```

This Capability 0.4 registration only prevents the required later work from being forgotten again. It does **not** change the current trading path.

**Blocking dependencies:** Productive Reconciliation Runtime Closure; Governed Futures Universe Authority; Productive Ranking Authority; Single Selected Future Persistence; Single Selected Future Restart Recovery; Futures Accounting Runtime Closure; Per-Instrument State Isolation Design; Global Portfolio Risk Design; Global Safety Arbitration; Single Global Execution Writer; Canonical Runtime Pre-Activation Closure.

**Review trigger (event-based):** Review immediately after successful closure and merge of (1) Productive Reconciliation, (2) Single Selected Future Authority and Runtime Binding, (3) Futures Accounting Runtime Wiring, (4) Canonical Runtime Pre-Activation Closure.

**Open policy decisions for later ratification** (not decided here): `active_set_size`, `candidate_set_size`, ranking refresh cadence, promotion/demotion thresholds, replacement margin, distinct-observation confirmation, hysteresis, cooldown, minimum active/candidate duration, data-quality disqualification, stale/invalid instrument behavior, open-position demotion semantics, instrument lifecycle states (`ACTIVE_ALPHA`, `ACTIVE_POSITION_ONLY`, `DEMOTION_PENDING`, `EXIT_ONLY`, `RETIRED`), capital allocation, correlation budget, concentration limits, gross/net exposure, maximum concurrent positions, liquidity-adjusted sizing, state persistence, restart reconstruction, per-instrument reconciliation, deterministic replay, evidence and verifier requirements.

## Reminder surface (non-authority)

`docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md` remains `REMINDER_ONLY`. Authority for deferred registration is this register.

## Related surfaces

- Capability closure runbook: `docs/governance/Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md` (Capability 0.4 / Phase 6)
- Runtime Truth Map: `docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md`
- Capability spec: `docs/ops/specs/DEFERRED_WORK_RECOVERY_REGISTER_ROTATION_POLICY_RESUBMISSION_V1.md`
- Contract owner: `src/ops/deferred_work_recovery_register_contract_v1.py`
- Tests: `tests/governance/test_deferred_work_recovery_register_v1.py`
