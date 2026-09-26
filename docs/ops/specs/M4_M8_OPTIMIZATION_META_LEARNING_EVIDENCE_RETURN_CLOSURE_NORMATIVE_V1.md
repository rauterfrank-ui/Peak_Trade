---
docs_token: DOCS_TOKEN_M4_M8_OPTIMIZATION_META_LEARNING_EVIDENCE_RETURN_CLOSURE_NORMATIVE_V1
status: active
scope: Canonical M4–M8 optimization/meta-learning evidence return loop closure upstream of P5
capability: M4_M8_OPTIMIZATION_META_LEARNING_EVIDENCE_RETURN_CLOSURE
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-26
---

# M4–M8 Optimization / Meta-Learning Evidence Return Closure

```text
WORKPACKAGE_ID=M4_M8_OPTIMIZATION_META_LEARNING_EVIDENCE_RETURN_CLOSURE
BOUND_ORIGIN_MAIN_SHA=4d8f3f1d80cd47ace4aa61d946241bf9f0cf3ed2
CONCEPT_ADDENDUM=Peak_Trade_Meta_Learning_Optimization_Universe_Concept_v3_4 (pages 23–27)
P5_FINAL_CLOSURE_IN_SCOPE=false
META_EVIDENCE_AUTHORITY=NONE
OPTIMIZATION_PRODUCTIVE_AUTHORITY=NONE
EXPERIMENT_SELECTION_NOT_TRADING_SELECTION=true
NO_SELF_DEPLOY=true
```

## Purpose

Close the governed research/evidence loop **M4→M5→M6→M7→M8** on CURRENT main using existing
canonical owners. This package proves mechanical lineage and deterministic replay. It does **not**
equate M5 artifacts to P2 `optimization_envelope_evidence_v1` or M6 artifacts to P2
`meta_learning_routed_evidence_v1` (separate P5 final closure).

## Owners

| Phase | Module |
| --- | --- |
| M4 | `src/experiments/canonical_optimization_universe_experiment_plane_v1.py` |
| M5 evidence | `src/experiments/canonical_optimization_experiment_evidence_v1.py` |
| M5 return ack | `src/experiments/canonical_self_learning_optimization_return_input_v1.py` |
| M6 | `src/experiments/canonical_meta_learning_ingest_v1.py` |
| M6 schema | `src/learning/deterministic_decision_outcome_v0/meta_learning_evidence_v1.py` |
| M7 | `src/experiments/canonical_meta_to_optimization_feedback_v1.py` |
| M8 | `src/experiments/canonical_deterministic_multi_cycle_offline_replay_v1.py` |
| WP loop | `src/experiments/canonical_m4_m8_evidence_return_loop_v1.py` |
| Adjudication | `src/governance/m4_m8_optimization_meta_learning_evidence_return_closure_v1.py` |

Decision: `config/governance/m4_m8_optimization_meta_learning_evidence_return_closure_v1_decision_v1.json`

## Required loop

```text
CYCLE N: Learning evidence → M4 plane → M5 experiment evidence → M5 return ack
         → M6 meta-learning evidence → M7 bounded research feedback
RETURN:  M5/M6 artifacts are evidence-only (authority=NONE)
CYCLE N+1: M7 feedback may bound next research experiment/search choice only
M8:      ≥2 cycles deterministic offline replay reproduces identities/digests
```

## Mechanical field rule

Target fields on M6 export use **EXACT_SOURCE** from M5 slices or documented
**MECHANICAL_TRANSFORM** without new decision semantics. Missing instrument/epoch/time
fields remain `UNKNOWN_UNAVAILABLE` or offline-context tokens — never fabricated.

## Non-goals

P5 producer ingress into Evidence Adjudicator A, promotion, trading selection, productive
parameter mutation, order/execution/external effects, `optimization_envelope_evidence_v1`
emitter, `meta_learning_routed_evidence_v1` emitter.
