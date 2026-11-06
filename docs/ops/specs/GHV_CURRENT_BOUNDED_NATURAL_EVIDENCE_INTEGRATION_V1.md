# GHV_CURRENT_BOUNDED_NATURAL_EVIDENCE_INTEGRATION_V1

Additive forensic integration only. CURRENT Product Runtime remains authoritative; GHV is reference-only (`GHV_AUTHORITY=NONE`).

## Phase 1 — CURRENT inventory

| Component | Owner path |
|-----------|------------|
| Bounded Natural Evidence launcher | `scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py` |
| Owner-GO / continuous authorization | `current_productive_governed_continuous_cycle_orchestrator_v1` (`RUNTIME_OWNER_GO`, fresh C1 GET consumptions) |
| Persistent `lane_state` | `current_productive_persistent_natural_enter_convergence_v1.build_s8_occupied_lane_pairs_v1` |
| Fresh-C1 observation | `run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1` |
| Natural Enter evidence | `scripts/ops/pre_external_convergence_natural_enter_reporting_v1.py` → `PRE_EXTERNAL_CONVERGENCE_REPORT.json` |
| S5 decision evidence | S6 cycle records + `S5_CYCLE_SUMMARIES` in convergence report |
| PRE_EXTERNAL reports | `PRE_EXTERNAL_CONVERGENCE_REPORT.json` |
| GHV forensic harness | `productive_golden_happy_vector_forensic_observability_v1` (optional flags on launcher) |
| GHV graph traversal | `ghv_pre_external_whole_cycle_causal_observability_v1.build_whole_cycle_observability_v1` |
| GHV flight recorder | `ghv_pre_external_runtime_flight_recorder_v1` |
| Runtime duration transparency | `pre_external_convergence_runtime_duration_transparency_v1` |

## Phase 2 — Integration design

```text
CURRENT BOUNDED RUNTIME (optional, Owner-GO gated)
        |
        v
CANONICAL EVIDENCE (PRE_EXTERNAL_CONVERGENCE_REPORT.json + ledgers)
        |
        v
GHV FORENSIC ANALYSIS (offline materialization from flight record)
        |
        v
GHV_CURRENT_BOUNDED_NATURAL_EVIDENCE_COMBINED_REPORT_V1.json
```

WP runner: `scripts/ops/run_ghv_current_bounded_natural_evidence_integration_v1.py`  
Forensic adapter: `src/ops/full_core_live_path_composition_root_v1/ghv_current_bounded_natural_evidence_forensic_adapter_v1.py`

## Phase 3 — Bounded execution contract

Product defaults preserved when executing CURRENT path via this WP:

- `MAX_CYCLES=4`
- `MAX_RUN_DURATION_SECONDS=180`
- Duration scope: `S6_OBSERVATION_SEQUENCER_ONLY`
- Reuses existing persistent `lane_state` (caller-supplied `--lane-state-root`)
- No automatic scheduling
- Productive execution requires `--execute-bounded-current-run` and `--owner-run-go-acknowledged`

## Phase 5 — Combined report

Written as `GHV_CURRENT_BOUNDED_NATURAL_EVIDENCE_COMBINED_REPORT_V1.json` under the evidence root. Key fields include `CURRENT_AUTHORITY_SHA`, `GHV_AUTHORITY`, runtime status, cycle accounting, duration transparency passthrough, S5 dispositions, GHV causal status, evidence completeness, POST/order safety counters, and `NEXT_RECOMMENDED_ACTION`.

Hold-closed explanations distinguish `FACT` (CURRENT disposition), `INFERENCE` (GHV observability rows), and `HYPOTHESIS` (no defect claim without contract evidence).

## Phase 6 — Governance impact

| Area | Impact |
|------|--------|
| Trading semantics | **NONE** — adapter is read-only on evidence |
| Productive authority | **NONE** — no new Owner-GO surfaces; reuses existing launcher |
| POST / orders | **NONE** — no new capability; safety checks flag unexpected POST |
| Credentials | **NONE** |
| Budget enforcement | **NONE** — defaults delegated to existing budget module |
| Historical evidence | **IMMUTABLE** — integration reads only |
| Existing consumers | **COMPATIBLE** — additive artifacts |

Regression owner: `tests/ops/test_ghv_current_bounded_natural_evidence_integration_v1.py`
