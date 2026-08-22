# Established relationships

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_RELATIONSHIP_MAP
ARTIFACT_AUTHORITY=NONE
epistemic_class=NAVIGATION_INDEX
NO_INVENTED_RELATIONSHIPS=true
```

Machine twins:

- `manifests&#47;source_to_finding_map.json`
- `manifests&#47;finding_to_evidence_map.json`
- `manifests&#47;dependency_map.json`

## source → finding

Only where a bound operation actually used that source for the claim.
STEP8/9/13/17 have **empty curated-finding lists** on purpose: their
material information is the historical identity copy itself. Empty ≠
unused. See notes in the JSON map.

## finding → evidence

Every `F_*` in `05_adjudicated_findings.md` lists sources. Traceability
is: curated statement → finding id → source id → SHA256 path in
`02_provenance_source_registry.md` / identity copy.

## finding → superseded historical state

| Current | Historical not to confuse with current |
|---|---|
| PRODUCT_A | STEP8, STEP9, STEP13, STEP17 |
| M06 two-layer | C01–C06 markdown candidates; M05A JSONL catalog-only |
| CASE_A contract (revalidated) | PRIOR_PREWRITE transcript remains a separate historical report |

## finding → unresolved dependency

| Finding / claim | Open blocker |
|---|---|
| index-only TARGET recovery | U_P05, U_P06, I11 |
| model completeness | U_P07 |
| markdown write | U_P10, U_P14, F_NO_LOSSLESS_MD |
| M06 disk write | VOL_CAP, F_FULLFSYNC, separate Owner-GO, dest ENOENT |
| parser-family safety | U_P01, U_S31_04 |

## index/navigation → object

This tree and `manifests&#47;*.json` are navigation. They are not semantic
authority. Map of Truth remains the repo navigation SSOT-pointer
document and still defines no semantics.

## derived → original

| Derived | Original |
|---|---|
| `10_step15_forbid_index.md` / `step15_forbid_index.json` | STEP15 identity copy SHA `63829882…` |
| curated `F_*` | transcripts + PRODUCT_A/TARGET copies |
| M06 contract prose | DISCOVERY + PRIOR_PREWRITE + CASE_A revalidation transcripts |

## preservation artifact → source identity

See `manifests&#47;raw_evidence_preservation_map.json`. Each copy records
source path, dest path, SHA256, size, `byte_identical=true`,
`normalization=NONE`.
