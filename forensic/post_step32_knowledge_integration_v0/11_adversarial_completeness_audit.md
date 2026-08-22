# Adversarial completeness audit

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_COMPLETENESS_AUDIT
ARTIFACT_AUTHORITY=NONE
epistemic_class=INTERPRETATION
NOT_NEW_ADJUDICATION=true
```

This audit checks the **worktree model**, not the Desktop sources.
Defects are corrected only inside the worktree. Sources were not altered.

## For every bound source: loss if the original chat/transcript vanished?

| Source | If only chat vanished | If Desktop also vanished |
|---|---|---|
| TARGET | worktree identity copy remains | worktree copy remains |
| PRODUCT_A | worktree copy remains | worktree copy remains |
| STEP15/17/13/9/8 | worktree copies remain | worktree copies remain |
| STEP30–32, POST32, DISCOVERY, PRIOR_PREWRITE | worktree transcript copies remain | same |
| Master / Map | already in git at bound SHA | same |
| This collection chat | copied at end of materialization | same |

Without TARGET copy, PRODUCT_A cannot reconstruct glyphs (U_P05/I11).
That limitation is explicit in `05_` and `09_`.

## For every worktree finding: provenance without guessing?

Each `F_*` has sources in `manifests/adjudicated_findings.json` and
`finding_to_evidence_map.json`. Open points have statuses copied from
bound transcripts, not inferred closures.

## For every relationship: established or inferred?

`source_to_finding_map.json` marks
`ESTABLISHED_FROM_BOUND_OPERATIONS_NOT_INFERRED_TREE`.
Empty finding lists for STEP8/9/13/17 are **explained**, not filled
with invented findings.

Directory grouping is INTERPRETATION (layout), labeled as such in `01_`.

## For every duplicate: would dedup destroy meaning?

STEP8/9/13/17 vs PRODUCT_A: yes, chronology and STEP9 chrome.
Two CASE_A transcripts: yes, independent revalidation vs first report.
FORBID lines listed in JSON vs STEP15 copy: the copy is the evidence;
the JSON is navigation. Deduplicating away STEP15 would lose
non-FORBID contract prose.

## For every historical statement: could a reader take it as current authority?

Mitigations: labels on every file; `03_chronology.md`;
`HISTORICAL_IS_NOT_CURRENT`; STEP15 heading-currentness FORBID cited;
Master Runbook not copied into `forensic/`.

Residual risk: a reader ignoring labels. That is why
`12_what_this_collection_does_not_prove.md` exists.

## For every navigation artifact: semantic authority misread?

A25-class risk remains for any Markdown in `docs/`-like locations.
This tree lives under `forensic/post_step32_knowledge_integration_v0/`
with `ARTIFACT_AUTHORITY=NONE` on every file. Map of Truth is unchanged
and still navigation-only.

## Structural defects found during this audit and corrected in-tree

None requiring rewrite of raw copies. One modeling choice kept explicit:
U_S31_05 is **not** closed even though Discovery JSON-RT exists, because
that RT was PRODUCT_A object transport, not a re-execution of STEP31 C05.

## MATERIAL_INFORMATION_WITHOUT_WORKTREE_REPRESENTATION

Intended empty after end-of-run capture of this chat transcript.
If the live transcript SHA cannot be frozen until the last write, the
exception is the still-growing chat log — captured once at the end.
