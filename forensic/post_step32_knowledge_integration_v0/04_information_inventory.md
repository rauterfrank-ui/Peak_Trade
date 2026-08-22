# Information inventory

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_INFORMATION_INVENTORY
ARTIFACT_AUTHORITY=NONE
PRODUCT_A_ALONE_CAN_RECONSTRUCT_ALL_EVIDENCE=false
epistemic_class=NAVIGATION_INDEX
```

Machine twin: `manifests&#47;information_inventory.json`.

Rule used while building this tree: every material item has either
(1) a curated finding that points at raw evidence, or
(2) an identity-bound raw copy whose *existence* is the representation
(used for historical STEP8/9/13/17, where a new curated “finding” would
falsely promote them to current structure).

No item was dropped because it was duplicated, awkward, historical,
unresolved, or absent from PRODUCT_A.

## Mapping (abbreviated; full records in JSON)

| Item | Source | Class | Worktree representation |
|---|---|---|---|
| TARGET bytes, LF, NFC/NFKC | TARGET | RAW | desktop identity copy |
| 8 PRODUCT_A roots, 23961 catalog, occupancy, carriers, roster | PRODUCT_A | RAW + measured findings | desktop identity copy + `05_` |
| STEP15 FORBIDs / P19 | STEP15 | CONTRACT | identity copy; `10_` is navigation only |
| STEP8/9/13/17 bytes | those files | HISTORICAL | identity copies; `06_` |
| I/T/R spec, U_P openings | STEP30 tx | RAW | transcript copy |
| C02B/C03B FAILs, parser baseline, C07/C05 holding | STEP31 tx | RAW / ADJUDICATED | transcript + `05_` |
| T17, PRE_WRITE gates, sequence closed | STEP32 tx | RAW / CONTRACT | transcript + `09_` |
| MD write not ready | POST32_READINESS | ADJUDICATED | transcript + `05_` / `12_` |
| M06 CASE_2 empirics, rejected M05A | DISCOVERY | ADJUDICATED | transcript + `09_` |
| CASE_A pre-write contract | PRIOR_PREWRITE + this chat | CONTRACT | transcripts + `09_` |
| Open U1/U2/U_P*/U_S31*/lag | multiple | OPEN | `07_` + JSON |
| Master Runbook / Map | repo at SHA | CANONICAL / NAV | **not** copied into `forensic/` |

If PRODUCT_A were kept and TARGET plus transcripts discarded, at least
the following would be lost: original glyphs (I11/U_P05), post-STEP21
negative tests, M06 measurements, CASE_A contract, STEP15 FORBID full
text, STEP9 chrome not present in later previews.
