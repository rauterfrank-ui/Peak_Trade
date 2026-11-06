# Audit Findings

This directory contains individual finding documents identified during the audit process.

## Naming Convention

Findings are numbered sequentially: `FND-0001.md`, `FND-0002.md`, etc.

## Finding Template

Each finding document should follow this structure:

```markdown
# FND-XXXX: [Short Title]

## Metadata
- **Severity:** P0 / P1 / P2 / P3
- **Subsystem:** [Data / Strategy / Backtest / Risk / Execution / Ops / Security / CI]
- **Discovered:** [Date]
- **Status:** [Open / In Progress / Fixed / Accepted]

## Description
[Detailed description of the issue]

## Impact
[Why this matters - what failure mode does it enable?]

## Evidence
- Evidence ID: [EV-XXXX from EVIDENCE_INDEX.md]
- Location: [File paths, line numbers, config sections]
- Reproduction: [Steps to reproduce if applicable]

## Remediation Plan

### Proposed Fix
[Specific steps to address the finding]

### Owner
[Name/Role]

### Due Date
[Target date]

### Verification
[How to verify the fix works]

## Related Items
- Related Findings: [FND-YYYY, FND-ZZZZ]
- Related Risks: [RISK-NNN from RISK_REGISTER.md]

## Revision History
| Date | Author | Changes |
|------|--------|---------|
| | | |
```

## Severity Guidelines

- **P0 Blocker:** Can lead to uncontrolled loss, unauthorized trades, or secret leaks. Must be fixed before GO.
- **P1 High:** Can lead to significant misbehavior in stress scenarios. Must be fixed or have compensating controls before GO.
- **P2 Medium:** Improvements/hardening. Can be addressed after launch in bounded mode.
- **P3 Low:** Documentation, hygiene, nice-to-have improvements.

## Status Workflow

1. **Open:** Finding identified, not yet addressed
2. **In Progress:** Actively being remediated
3. **Fixed:** Remediation complete, awaiting verification
4. **Accepted:** Risk formally accepted with compensating controls (requires sign-off)
5. **Closed:** Verified fixed and no longer a concern
