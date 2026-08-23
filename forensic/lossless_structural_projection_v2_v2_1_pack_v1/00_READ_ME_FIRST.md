```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_NAVIGATION_INDEX
DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS
ARTIFACT_AUTHORITY=NONE
NOT_CANONICAL=true
SECOND_SSOT=false
FILE_PLACEMENT_IS_NOT_AUTHORITY_PROMOTION=true
MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
PACK_ID=peak_trade_lossless_structural_projection_v2_v2_1_pack
PACK_VERSION=v1
STORAGE_STRATEGY=HYBRID_SOURCE_DIRECT_GIT_JSON_EXTERNAL_SHA_REFERENCE
PRESERVATION_CHECKPOINT_STATUS=LOCAL_WRITTEN_NOT_COMMITTED
```

This directory is a **local preservation checkpoint** of the already
adjudicated V2 / V2.1 lossless structural projection decision set.

It is not a second SSOT. It is not canonicalization. It is not the
V2 / V2.1 implementation. It does not authorize trading, Testnet, Live,
orders, credentials, commit, push, PR, or merge.

The Master Runbook remains the sole canonical SSOT at
`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`.
The Map of Truth remains navigation-only at
`docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`.
Neither file is copied into this pack.

## What this pack preserves

The bound adjudicated state from
`V2_1_REPO_INTEGRATION_FINAL_DECISION_RECONCILIATION_REPORT`
(`FINAL_DECISION_RECONCILIATION_STATUS=PASS`), persisted here so that
the decision set does not depend on chat history, Cursor context, `/tmp`,
or Downloads metadata alone.

Machine index: `manifests/pack_manifest_v1.json`.

Full preservation record of the passed reconciliation (AUTHORITY=NONE):
`manifests/final_decision_reconciliation_v1.md`.

## What is in git in this leaf

- this navigation index (authored; not an identity copy)
- `manifests/pack_manifest_v1.json` (authored; AUTHORITY=NONE)
- `manifests/final_decision_reconciliation_v1.md` (authored preservation record; AUTHORITY=NONE)
- byte-identical copies of SOURCE, V2_MD, V2_1_MD under
  `evidence/raw_verbatim_identity_copies_authority_none/`
- byte-identical copy of the generator harness under `generator/`

## What is not in git

V2_JSON and V2_1_JSON are **logical pack members** but
`storage_class=EXTERNAL_REFERENCE`, `GIT_COPY=false`, `LFS=false`,
`repo_path=null`. SHA256 and size are bound in the manifest.
Operator custody is required. Durable store is not proven.

Downloads is provenance only, not a durable store.
`/tmp/peak_trade_v21_gen.py` is volatile provenance for the harness
original; the git copy is the identity copy of that original.

No placeholder file, symlink, or LFS pointer stands in for the JSON
blobs.

## Harness and path identity

The harness is generator implementation / `TEST_HARNESS_BEHAVIOR`.
It is **not** source-evidence.

V2.1 basenames use a **dot** (`…_V2.1.json`, `…_V2.1.md`).
An underscore basename (`…_V2_1.json` / `…_V2_1.md`) does not exist
and must not be invented.

`forensic/post_step32_knowledge_integration_v0/` uses the same SOURCE
basename as this pack, but it is a **different object** (different
SHA256 / size). Do not mix the two trees. This pack does not mutate
post_step32.

## Authority containment

```text
PRESERVATION_AUTHORITY=NONE
SECOND_SSOT=false
CANONICALIZATION_PERFORMED=false
FILE_PLACEMENT_IS_NOT_AUTHORITY_PROMOTION=true
GIT_TRACKED_NE_CANONICAL=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
V2_1_IMPLEMENTATION_AUTHORIZED=false
```

Historical Owner GOs of this forensic lane are consumed. This
checkpoint does not revive them as live write or trading authority.

## Process note (no technical re-adjudication)

A separate `PRESERVATION_SPECIFICATION_READ_ONLY_ONLY` step was skipped
by a new Owner process decision. Effect: process-only; technical
V2 / V2.1 adjudications are unchanged. This local write is authorized
only by
`OWNER_GO_TO_V2_1_FINAL_RECONCILIATION_LOCAL_PRESERVATION_WRITE_ONLY`.

```text
PRESERVATION_CHECKPOINT_STATUS=LOCAL_WRITTEN_NOT_COMMITTED
GIT_ADD_ALLOWED=false
COMMIT_ALLOWED=false
```
