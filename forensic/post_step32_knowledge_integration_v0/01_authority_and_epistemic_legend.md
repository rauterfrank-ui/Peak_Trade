# Authority and epistemic class legend

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_NAVIGATION_INDEX
ARTIFACT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true
NOT_CANONICAL=true
```

Classes must not be silently converted.

| Class | Meaning in this collection | Typical location |
|---|---|---|
| CANONICAL_AUTHORITY | Master Runbook at bound SHA. Implementation/ops semantic authority. Runtime authorization effect remains NONE. | `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` |
| RAW_VERBATIM_EVIDENCE | Exact bytes. No cleanup. Identity is SHA256+SIZE. | `evidence&#47;raw_verbatim_identity_copies_authority_none&#47;` |
| ADJUDICATED_FINDING | A claim already established in a bound operation, here only indexed. | `05_adjudicated_findings.md`, `manifests&#47;adjudicated_findings.json` |
| HISTORICAL_INTERMEDIATE_STATE | Earlier artifact or closed operation. Not current structure. Not deleted. | `06_…`, STEP8/9/13/17 copies, closed transcripts |
| NAVIGATION_INDEX | Pointers. No semantics. Map of Truth class. | this tree's markdown indexes, Map of Truth |
| INTERPRETATION | Layout/grouping chosen in this collection. Not an observation. | directory structure, some audit prose |
| HYPOTHESIS | Not introduced here. None newly asserted. | — |
| OPEN_OR_CONTRADICTORY | Must remain open. | `07_unresolved_open_issues.md` |
| TRANSFORMATION_OR_IMPLEMENTATION_CONTRACT | STEP15 FORBIDs; M06 pre-write contract. Not executed by this collection. | STEP15 copy; `09_…`; `10_…` |
| SOURCE_IDENTITY_AND_PROVENANCE | Path, role, SHA256, size, copy method. | `manifests&#47;source_identities.json` |

Forbidden equations:

```text
RAW != ADJUDICATED
HISTORICAL != CURRENT
NAVIGATION != AUTHORITY
INTERPRETATION != OBSERVATION
OPEN != CLOSED
UNPROVEN != PROVEN
PRESERVED != CANONICAL
IMPLEMENTED != ACTIVATED
CONTRACT_PRESENT != READY
FIXTURE_PASS != PRODUCTIVE_EVIDENCE
M06 != COMPLETE_POST_STEP32_EVIDENCE
PRODUCT_A_ALONE != ALL_EVIDENCE
```

A better structure, a worktree path, or a README heading does not create authority (STEP15 `FORBID_IMPLIED_AUTHORITY_FROM_STRUCTURE`, `FORBID_AUTHORITY_PROMOTION`, `FORBID_SECOND_SSOT`).
