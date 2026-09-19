---
docs_token: DOCS_TOKEN_OPTIMIZATION_UNIVERSE_EXPERIMENT_PLANE_NORMATIVE_V1
status: active
scope: Optimization universe M4 offline experiment plane; proposal-only; zero productive surfaces
capability: OPTIMIZATION_UNIVERSE_M4_EXPERIMENT_PLANE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# Optimization Universe — Experiment Plane V1 (M4)

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
WORKPACKAGE_ID=OPTIMIZATION_UNIVERSE_M4_EXPERIMENT_PLANE_V1
BOUND_ORIGIN_MAIN_SHA=c889577bef56300f74039d921472f0638cbb8810
LEARNING_PRODUCTIVE_AUTHORITY=NONE
OPTIMIZATION_PRODUCTIVE_AUTHORITY=NONE
AUTHORIZED_PRODUCTIVE_SURFACES=0
ZERO_AUTHORIZED_PRODUCTIVE_TARGETS=true
EXTERNAL_EFFECT_AUTHORIZED=false
PROPOSAL_NOT_AUTHORITY=true
```

Owner: `src/experiments/canonical_optimization_universe_experiment_plane_v1.py`

## Offline chain (M4)

```text
VALID_OPTIMIZATION_INPUT
  → OFFLINE_SYNTHETIC_RESEARCH_CONTEXT
  → EXPERIMENT_IDENTITY
  → SEARCH (RESEARCH_ONLY)
  → CANDIDATE (PROPOSAL_ONLY)
  → CHALLENGER/EVALUATION
  → OOS/ROBUSTNESS/FAILURE_EVIDENCE (EVIDENCE_ONLY)
  → PROPOSAL_ONLY
```

## Reuse (adjudicated)

- Advanced search, champion/challenger, robustness suite, comparison SSOT, experiment identity: **reuse as-is**
- Automated offline research loop, regime evaluation, portfolio learning: **preserve not activate** as executors
- Owner maps / envelope: evidence only; **no** productive surface authorization

## Non-goals

M5–M9, productive search, promotion/apply, trading/selection/execution
