# Adjudicated findings (curated index, not a second SSOT)

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_ADJUDICATED_FINDINGS
ARTIFACT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
NOT_CANONICAL=true
NEW_FACTS_ADJUDICATED_IN_THIS_COLLECTION=false
epistemic_class=ADJUDICATED_FINDING
```

Each row is a **pointer** into bound raw evidence. Full records:
`manifests/adjudicated_findings.json`. This collection did not reopen
U1/U2 and did not invent new mechanism classes.

How established: identity remeasurement and/or closed operation
transcripts listed under Sources. What it does not prove is mandatory
reading; see also `12_what_this_collection_does_not_prove.md`.

## Identity / structure

**F_TARGET_IDENTITY.** TARGET SHA256 `08ffe7bc…5092`, SIZE 1421764, CR=0,
LF=30870, FINAL_LF=true, NFC identity true, NFKC false.
Sources: TARGET. Does not prove authority or U_P07 completeness.

**F_PRODUCT_A_EIGHT_ROOTS.** Eight unfused roots in stored order:
PRODUCT_A_ENVELOPE, PREVIEW_ENVELOPE, CANDIDATE_ENVELOPE,
CLOSED_TYPE_ROSTER, CATALOG_RECORDS, LINE_ENTRIES,
KR8_KR9_SOURCE_BYTE_CARRIER_INDEX, OCCUPANCY_INDEX.
Sources: PRODUCT_A, DISCOVERY.

**F_CATALOG_23961.** n=23961; seq unique; `SEQ_EQ_ARRAY_INDEX=0`;
seq descents=1193; `authority_status=NONE` for all. Seq is identity,
not physical order.

**F_JSON_FILE_EQ_DUMPS_PLUS_LF.** PRODUCT_A file bytes equal
`json.dumps(..., ensure_ascii=False, sort_keys=False, allow_nan=False)+LF`.

**F_ENVELOPE_LABELS.** PRODUCT_A_ENVELOPE:
`TARGET_AUTHORITY=NONE`, `ARTIFACT_AUTHORITY=NONE`, `SECOND_SSOT=false`,
`MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true`, U1/U2 `OPEN_UNCHANGED`,
`NEXT_WRITE_AUTHORIZED=false`.

## Reconstruction limits

**F_OFFSETS_INSUFFICIENT.** Offsets present 1101/23961; 22860 without;
raw_text==slice 1099; raw_text!=slice 2 (`DeclaredVerbatimBody` seq 1100
and 1101); JSON_NULL raw_text 99. Offset-only catalog REJECT.

**F_PRODUCT_A_INSUFFICIENT_ALONE.** `PRODUCT_A_ALONE_CAN_RECONSTRUCT_ALL_EVIDENCE=false`.
U_P05 UNPROVEN_AND_INSUFFICIENT. I11 requires TARGET identity copy.

**F_CARRIER_4856.** 4856 carriers, `SOURCE_FILE_IDENTITY_COPY`,
synthesis false, SHA match 4856/4856 against TARGET slices.

**F_P19_493.** STEP15 P19: `reason in {KR-8,KR-9}` AND
`model_has_independent_bytes=true` count=493 (153 NestedStructuralChild
+ 340 MarkedVerbatimRegion). Must not be moved into the carrier index.
Broader PARENT_SPAN recon count is 4105; that is a **different** class
and must not be fused with 493.

## Occupancy, duplicates, sentinels, roster

**F_OCCUPANCY.** 30870 lines; hist `{1:4831,2:10417,3:14423,4:1189,5:10}`;
non-monotone occupying_seq first-descent-per-line 17854. Do not collapse
to a tree.

**F_DUP_FUSION_LOSS.** raw_text fusion would drop 8642 records.

**F_SENTINELS.** None=518458, `"NULL"`=46, `""`=23841, false=74251, 0=27.
Do not normalize.

**F_UNRESOLVED_19.** 19 UNRESOLVED status and classification. Do not
synthesize `UnresolvedRelation`.

**F_ROSTER_ABSENT_26.** 37 roster types, 11 present, 26 absent including
`UnresolvedRelation`, `EnvelopeRecord`, `OpenIssue`. Absent stays absent.

## Representation / parser / unicode

**F_UNICODE_NORM_NOT_HARMLESS.** NFD encoded len 1422196; NFKC 1421762.

**F_PARSER_BASELINE.** `markdown_it.MarkdownIt('commonmark')`: 14754
tokens; headings 1315 (83/882/350); 1132 fences markup only ` ``` `;
html_block=0; hr=681; bullet=133; ordered=38; MATCHES_STEP31_BASE.
Does not prove other parser families (U_P01 / U_S31_04).

**F_SORT_KEYS_FORBIDDEN.** `sort_keys=true` changes root and record key
order. STEP15 `FORBID_SORT_KEYS_ON_STORED_OBJECTS`.

**F_I06_JSON_EMBED_FAIL.** Embedding TARGET as a JSON string can recover
bytes but requires escaping → I06 FAIL as blob transport.

## Markdown materialization (negative)

**F_NO_LOSSLESS_MD.** `LOSSLESS_MARKDOWN_MATERIALIZATION_FOUND=false`.
C01/C02/C03/C04/C06 rejected or blocked. C03B byte unwrap is not
semantic Markdown round-trip. C02B showed html_block / list / blank-line
interference. U_P10 / U_P14 remain open.

**F_C07_C05_HOLDING_ONLY.** In-RAM holding beside unaltered TARGET is
not a write license and not serialization.

**F_JSONL_CATALOG_ONLY_REJECT.** M05A drops seven roots.

## M06 / CASE_A / sequence

**F_M06_TWO_LAYER.** Selected mechanism: Layer 1 = exact TARGET bytes;
Layer 2 = complete eight-root PRODUCT_A. RAM length-prefixed envelope
round-trip PASS, leftover=0, ENV_LEN=38221963. `READY_FOR_FILE_WRITE=false`.
M06 is **not** a substitute for STEP30/31/32/Discovery/Pre-Write
transcripts.

**F_LEFTOVER_GATE_REQUIRED.** Extra trailing byte leftover=1;
concatenated envelopes leftover=38221963 unless leftover==0 is mandatory.

**F_CASE_A.** Pre-write contract complete enough for a **separate**
Owner-GO to execute a controlled non-markdown write *validation*.
This collection is not that GO. Write not tested. T17 not executed.
VOL_CAP unprobed. Dest must not be TARGET or the original seven Desktop
files.

**F_SEQUENCE_CLOSED_STEP32.** Numbered forensic sequence closed at
STEP32. STEP33 not defined.

**F_HANDOVER_NOT_EVIDENCE.** Owner handover is not SSOT and not complete
evidence.

**F_FORENSIC_TRUTH_SHA_LAG.** Master Runbook field
`CURRENT_FORENSIC_TRUTH_SHA=22d7d423…` vs origin/main `652c2cd4…`.
OPEN / NOT_REPAIRED. Not repaired by this collection.
