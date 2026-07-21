# Provisional V7 artifact classification (Phase 1)

> **IMPLEMENTATION_ONLY / NOT_EVALUATED.** Classification of wiring artifacts only.
> No evaluation executed. No economic-pass verdict, promotion, holdout, or runtime claim.

| Artifact | Classification | Note |
|---|---|---|
| `constants_v7.py` | KEEP_AND_HARDEN | Authority IDs/digests; B3 infra token |
| `cooldown_state_v7.py` | KEEP_AND_HARDEN | B4/B5/B6/B8 fields; no provisional caveat |
| `reentry_cooldown_gate_v7.py` | KEEP_AND_HARDEN | Entry-eligibility only |
| `decision_v7.py` | KEEP_AND_HARDEN | Full B1–B8 decision order |
| `measurement_validity_preflight_v7.py` | KEEP_AND_HARDEN | B1 reentry divergence; identical exits |
| `panel_runner_v7.py` | KEEP_AND_HARDEN | Authority gates before data/slot |
| `hypothesis_dispatch_v7.py` | KEEP_AND_HARDEN | Dispatch retained |
| `__init__.py` | KEEP_AND_HARDEN | Package marker |
| CLI `run_evaluate_..._v7.py` | KEEP_AND_HARDEN | Fail-closed evaluate without auth |
| Evaluation tests | KEEP_AND_HARDEN | Updated for clarification |
| `EXECUTION_MAP.md` | KEEP_AND_HARDEN | Blockers closed by authority |
| `EVIDENCE_CONTRACT.md` | KEEP_AND_HARDEN | B3 terminal clarified |
| Eval governance MD | KEEP_AND_HARDEN | Authority binding |
| Owner-map eval entry | KEEP_AND_HARDEN | Note updated |
| Wiring-auth eval paths | KEEP_AND_HARDEN | Paths retained |
| `__pycache__&#47;` | NOT_RELEVANT | Generated |
| New clarification authority JSON/module/docs/tests | KEEP (new canonical) | Operator-authorized overlay |

No provisional artifact was promoted unchanged as SSOT without hardening.
