# Peak_Trade – Risk Register (Ops/Docs Governance v0)

**Scope:** Minimal risk register for docs/ops governance and process artifacts—NOT a compliance or live trading risk register.  
**Purpose:** Track operational risks related to documentation drift, policy inconsistency, and ops tooling gaps.  
**Owner:** ops  
**Status:** v0 (Living document)

---

## Risk Assessment Scales

### Likelihood
- **Low:** Unlikely to occur (< 10% probability)
- **Med:** May occur occasionally (10-50% probability)
- **High:** Likely to occur (> 50% probability)

### Impact
- **Low:** Minor friction, easily resolved
- **Med:** Moderate friction, requires coordination
- **High:** Blocks workflow, requires escalation

### Status
- **Open:** Risk identified, no mitigation yet
- **Mitigating:** Mitigation in progress
- **Accepted:** Risk accepted (cost of mitigation > impact)
- **Closed:** Risk resolved or no longer applicable

---

## Risk Registry

| Risk ID | Description | Likelihood | Impact | Mitigation | Detection | Owner | Status | Evidence Link |
|---------|-------------|------------|--------|------------|-----------|-------|--------|---------------|
| R-001 | CI/Policy Drift: Neue Docs-Checks oder Gates werden nicht in Policy/Contracts dokumentiert → divergence zwischen Source-of-Truth und Implementation | Med | Med | Required Checks Drift Guard (active), periodic audit of `.github/workflows/` vs. docs | Drift Guard CI check, ops doctor | ops | Mitigating | [Required Checks Drift Guard v1](REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md) |
| R-002 | Placeholder-Standard Inkonsistenzen: Teams nutzen unterschiedliche Marker (TODO vs. FIXME vs. TBD) → Review-Friktion, unklare Ownership | Low | Low | Placeholder Policy v0 (docs-only), periodic reports via `generate_placeholder_reports.py` | Local inventory reports (`.ops_local/inventory/`) | ops | Mitigating | [Placeholder Policy](PLACEHOLDER_POLICY.md) |
| R-003 | Ops-Dokumente werden fälschlich als "Compliance Claim" interpretiert: Docs beschreiben Prozess-Artefakte, aber externe Stakeholder könnten dies als Audit-Readiness-Claim missverstehen | Low | High | Explicit disclaimers in Ops docs ("NOT a compliance claim", "process artifact only"), vetting of doc wording pre-merge | PR review, ops QA gate | ops | Open | [TBD] |

---

## High Priority Risks (Score ≥ 6)

> No high-priority risks currently. R-003 has High impact but Low likelihood → Medium priority.

---

## Closed Risks

| Risk ID | Description | Date Closed | Resolution |
|---------|-------------|-------------|------------|
| [TBD] | Placeholder for closed risks | [TBD] | [TBD] |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-07 | v0 Initial — 3 seed risks (CI drift, placeholder standards, compliance misinterpretation) | ops |

---

**Version:** v0  
**Maintained by:** ops  
**Last Updated:** 2026-01-07  
**Review Frequency:** [TBD] (recommend monthly or before major phase gates)
