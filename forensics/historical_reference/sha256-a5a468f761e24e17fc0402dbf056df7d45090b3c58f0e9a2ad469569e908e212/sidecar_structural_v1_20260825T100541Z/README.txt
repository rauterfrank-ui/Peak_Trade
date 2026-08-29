# Structural Sidecar v1 (non-authoritative)

```text
TARGET_AUTHORITY=NONE
SIDECAR_AUTHORITY=NONE
MAP_OF_TRUTH_ROLE=NAVIGATION_ONLY
CANONICAL_REPO_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
OWNER_GO=PEAK_TRADE_TEMPORARY_FORENSIC_RUNBOOK_LOSSLESS_STRUCTURAL_SIDECAR_TRANSFORMATION_V1
PREEXISTING_DERIVED_ARTIFACTS_USED_AS_INPUT=false
HEURISTIC_RULE_COUNT=0
LOGICAL_CONTAINER_AMBIGUITY_COUNT=5
```

This sidecar is navigation / evidence index only. It is not authority.

It:

- preserves the source byte-for-byte (`R0_LF_LINE_RECORD`);
- indexes syntactic structure (`PARTITION_RULESET_V1` overlay);
- canonicalizes nothing;
- does not adjudicate the five Layer-2 container ambiguities;
- replaces neither the source file nor the Master Runbook;
- invents no new Peak_Trade gate or dependency semantics.

README must not replace original evidence. Reconstruct bytes from
`records.jsonl` decoded `raw_text` fields ordered by `seq_index`.

Source:

- path: `/Users/frnkhrz/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md`
- sha256: `a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212`
- bytes: `8639369`
- lines: `121930`
- newline: `LF`
- trailing_newline: `true`

Output root:

`/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/structural-v1-20260825T100541Z`

Level-2 / epistemic safety: the following remain `UNRESOLVED` as
`LOGICAL_CONTAINER_AMBIGUITY` and were not decided by this GO:

1. Continuation-H1 as Pass-Container
2. other H1 as Persist-Container
3. SRC-heading as region until next SRC
4. BEGIN/END as logical container versus line+relation
5. H2 PRESERVED_REPORT / PASS= as wrapper-/pass-container

Desktop/Downloads locators in the source body are historical data and
were not rewritten.

A preexisting derived sidecar under the same sha256 directory was not
read as input and was not overwritten.
