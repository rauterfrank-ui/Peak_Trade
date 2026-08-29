```text
AUTHORITY=NONE
PURPOSE=FORENSIC_HISTORICAL_REFERENCE
MUTABILITY=IMMUTABLE_CONTENT_ADD_ONLY_CORRECTIONS
CANONICAL_SELECTION=false
RUNTIME_SELECTION=false
TRADING_AUTHORITY=false
REPO_PRESERVATION != CANONICAL_PROMOTION
```

# Historical forensic reference (SHA-256 bound)

Preservation id: `peak_trade_historical_reference_a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212_v1`

This package is an immutable historical forensic reference. Storing it in git
does not make it canonical working authority. The current system remains the
only future mutation target.

## Source blob

Byte-identical copy (gated ingress path):

`forensic/evidence/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md`

SHA-256: `a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212`

## How to use

1. Treat `MANIFEST.yaml` as the root identity of this package.
2. Resolve every preserved object through `SOURCE_LINE_RANGE` against the blob.
3. Do not import this tree from runtime code.
4. Do not copy these obligations into the Master Runbook without a separate
   conservation / compatibility Owner-GO.

## Layers

- `provenance&#47;` source identity, ranges, commit/PR tokens
- `master_v2&#47;` and `double_play&#47;` derived indexes over source anchors
- `containers&#47;` T3 SRC-000001..088 plus required-container index
- `obligation_families&#47;` token families and non-proven lineage edges
- `conservation&#47;` historical child ledger and SSOT-transition mentions
- `schemas&#47;EPISTEMIC_SCHEMA.yaml` source-declared T5 schema copy
- `sidecar_structural_v1_20260825T100541Z&#47;` small structural sidecar files
- `LOSS_REGISTER.yaml` intentionally excluded derived blobs
