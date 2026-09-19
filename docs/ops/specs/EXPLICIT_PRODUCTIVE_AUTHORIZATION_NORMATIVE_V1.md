---
docs_token: DOCS_TOKEN_EXPLICIT_PRODUCTIVE_AUTHORIZATION_NORMATIVE_V1
status: active
scope: M10 Slice A — explicit productive authorization from governance review admission
workpackage_id: M10_PRODUCTIVE_PARAMETER_LINEAGE_CLOSURE_V1
last_updated: 2026-09-19
---

# Explicit Productive Authorization V1

```text
SLICE=A_EXPLICIT_PRODUCTIVE_AUTHORIZATION_V1
PREDECESSOR_EDGE=ADMITTED_FOR_GOVERNANCE_REVIEW
SUCCESSOR_EDGE=GOVERNED_PRODUCTIVE_CONFIGURATION_V1 (NOT IN THIS SLICE)
AUTHORIZATION_CONTRACT=peak_trade.governance.explicit_productive_authorization.v1
```

Owner: `src/governance/explicit_productive_authorization_v1.py`

Decision: `config/governance/explicit_productive_authorization_v1_decision_v1.json`

Owner boundary: `config/governance/explicit_productive_authorization_v1_owner_boundary_v1.json`

## Chain (this slice)

```text
Proposal (PROPOSAL_ONLY)
  → Governance/Risk Review Admission (ADMITTED_FOR_GOVERNANCE_REVIEW)
  → Explicit Productive Authorization (AUTHORIZATION_ONLY)
  → STOP
```

## Implemented successor edge (Slice B)

```text
AUTHORIZED_FOR_PRODUCTIVE_CONFIGURATION_BOUNDARY
  → governed_productive_configuration_v1
  → MATERIALIZED_GOVERNED_PRODUCTIVE_CONFIGURATION | DENIED_FAIL_CLOSED
```

Normative: `docs/ops/specs/GOVERNED_PRODUCTIVE_CONFIGURATION_NORMATIVE_V1.md`

## Semantics

- `AUTHORIZED_FOR_PRODUCTIVE_CONFIGURATION_BOUNDARY` means the bound candidate may enter the **next** governed materialization boundary only.
- It does **not** mean: materialized, threshold globally ratified, policy changed, enforcement on, deployment, or external effect.
- `ADMITTED_FOR_GOVERNANCE_REVIEW != AUTHORIZED_FOR_PRODUCTIVE_CONFIGURATION_BOUNDARY`.
- Positive authorization requires an **explicit Owner authorization input record**; admission PASS alone never authorizes.

## Registered productive target (exact)

`peak_trade.governance.productive_target.m9_volatility_numeric_max_age_seconds&#47;v1`

Parameter mapping: `max_age_seconds` → `numeric_max_age_seconds` (SECONDS); value identified by digest, not applied.

## Non-goals (this slice)

- Governed productive configuration
- Threshold value Owner ratification
- Policy mutation or parameter seam apply
- Candidate apply, enforcement, M11, external effect
