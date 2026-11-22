---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 8 typed MI forecast/outcome/calibration export into learning evidence path
capability: UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_V1
last_updated: 2026-09-26
---

# Unified Blueprint Phase 8 — MI→Learning Integration Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Machine-readable closure:
`config/governance/unified_blueprint_phase_8_mi_to_learning_integration_v1.json`

Code owner:
`src/governance/unified_blueprint_phase_8_mi_to_learning_integration_v1.py`

## Purpose

Close inter-loop edge `d02_mi_to_learning` by composing governed MI
`ForecastEvidence`, normative N_BARS realized outcomes, and
`CalibrationEvidence` into typed MI learning evidence exported onto the
existing offline learning evidence path without mutating productive DDO
reducers, MV2/Double-Play, Cap 2.3, or promotion authority.

## Verification

- `tests/learning/test_unified_blueprint_phase_8_mi_to_learning_integration_v1.py`
- `tests/governance/test_unified_blueprint_phase_8_mi_to_learning_integration_v1.py`
- `tests/governance/test_unified_blueprint_d01_d02_topology_adjudication_v1.py`

## Original MI content and optional DDO reference — 2026-11-21

The existing MI record validator now recomputes the original canonical
reproducibility digest before Store append, cold read or export. An unchanged
MI ID cannot retain changed outcome, horizon, price specification, instrument
or conditioned behavior bindings. The existing digest formula and record IDs
are unchanged; historical records are not rewritten.

If an MI export declares a legacy DDO record reference and supplies that
record, the two identities must agree. Reference-only, payload-only and
MI-only exports retain their existing meanings. A reference alone does not
set legacy DDO compatibility. MI evidence and DDO evidence remain different
record types; this does not turn forecast calibration into a PnL/quality label
or a productive DDO state update.

## Exact native join and typed learning time admission — 2026-11-21

The existing native forecast/outcome join compares the forecast end with the
original last bar close through the public-fact source clock decoder, retaining
all admitted fractional digits. Equivalent zero-fraction UTC representations
remain equal; a different nanosecond cannot alias the original outcome window.
A later observation evaluation time does not replace that last-close target.

The existing typed learning bridge uses the same exact ordering for its original
temporal relations, including forecast creation no later than horizon start.
Its UTC-Z input requirement is unchanged. Contradictions reject before the
native calibration helper or learning-store append; the ingest entry consumes
the same bridge. This adds no new learning consumer, timestamp default, model
inference, scoring rule or productive write.

Original timestamp strings, calibration methods, original-calibration comparison,
digest/ID formulas and exported record types remain unchanged. Missing outcomes
and insufficient support retain their typed non-evaluation/abstention meanings.
Existing records are not migrated or retroactively time-certified by cold read.
The separate forecast constructor, conditioned-context clocks and other owners
retain their own admission boundaries; this is not whole-system time closure.

## Native learning-record state admission — 2026-11-22

At baseline `c4394351f3551c0636a7165899d2addfa7e2d413`, the original bridge,
store, export, conditioned P5 adapter and optional M4 export are connected.
The bridge already distinguishes missing outcomes from finalized observations
and calibration support. These branches are also present in the frozen import
`9397d04a3`; the September Phase-8 contract above documents their intended
evidence-only boundary. Earlier construction history is not independently
recovered by this check.

The common record validator now enforces those declared state relationships
at native admission and cold read. INCOMPLETE requires OUTCOME_MISSING, absent
observation/outcome references, NOT_EVALUABLE and method NONE. FINALIZED requires
OK and explicit opaque observation/outcome references. Finalization does not
imply sufficient calibration support: insufficient or non-evaluable receipts
retain method NONE; sufficient receipts declare one of the existing calibration
methods. Evaluability is checked on the receipt, not inferred from forecast
support. The original information-set identity and positive integer n_bars
grammar are reused. Creation must precede the horizon end, with real calendar
validation and the existing exact nanosecond clock. UTC-Z syntax is retained.

The corrected original-source regression baseline has 89 unblocked admissions
and eight passing controls. Seventeen contradictory declarations are exercised
through validation, export, append and fresh get/list; four further cases reach
the existing conditioned P5 adjudicator or optional M4 intake. Original-source
native probes confirm three persisted/read-back/exported contradictions, two
P5 ADMIT results and two accepted M4 intakes. No experiment plane is started by
these probes. The initial diagnostic additionally tried a float n_bars that
the existing canonical JSON digest already rejects; that variant is excluded
from the missing-admission count and retained as a separate failed diagnostic.

Verification: `tests/learning/test_mi_learning_record_semantic_admission_v1.py`.
Eight complete original valid receipt/export/adapter packets and eight stored
files remain byte-identical, including missing outcomes, insufficient support,
original calibration provenance, equivalent zero fractions, later evaluation,
and conditioned records with present or missing realized behavior. Native JSON
readback and idempotent replay remain supported. All evidence uses synthetic
data, temporary stores and denied networking.

Only the common admission owner changes; existing readers/writers and consumers
inherit it. No historical file is rewritten or deleted. Rejected cold records
require source investigation, not automatic repair. Digest/ID formulas, method
numbers, units and evidence-only authority remain unchanged. BRIER_SCORE_V1
retains its documented linear 1-p meaning. The receipt contains references,
not the complete original forecast, observation or calibration. This gate
therefore establishes declared coherence and creation/end ordering, not the
authenticity or numerical correctness of referenced evidence, full temporal
digest reconstruction, source label truth, forecast quality, account PnL,
numeric learning, productive apply or whole-system operation. Conditioned
behavior snapshots retain their separate source-validation boundary.
