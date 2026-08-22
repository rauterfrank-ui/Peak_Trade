# M06 preservation / recovery contract (implementation candidate)

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_TRANSFORMATION_OR_IMPLEMENTATION_CONTRACT
ARTIFACT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
NOT_CANONICAL=true
READY_FOR_FILE_WRITE=false
M06_DISK_WRITE_EXECUTED_IN_THIS_COLLECTION=false
DESKTOP_M06_WRITE_EXECUTED=false
epistemic_class=TRANSFORMATION_OR_IMPLEMENTATION_CONTRACT
```

Sources (raw): DISCOVERY_CASE_2 transcript, PRIOR_PREWRITE transcript,
independent CASE_A revalidation in the collection chat. This file is
curated contract text, not a replacement of those transcripts.

## What M06 is

```text
M06 =
  LAYER_1 exact ORIGINAL_TARGET_BYTES
  +
  LAYER_2 complete eight-root PRODUCT_A
```

```text
M06 != complete substitute for STEP30/31/32/Discovery/Pre-Write evidence
PRODUCT_A_ALONE_CAN_RECONSTRUCT_ALL_EVIDENCE=false
```

In this worktree, Layer 1 and Layer 2 are already present as **separate
identity copies** under `evidence&#47;…&#47;desktop&#47;`. That is collection, not
the length-prefixed envelope write validation.

## What M06 is not

- not markdown materialization
- not TARGET mutation
- not SSOT
- not STEP33
- not a write authorization
- not proven disk-atomic (T17 unexecuted)

## Envelope candidate (RAM only; magic not ratified)

```text
MAGIC = b"PTF1IDX\n"
u64be TARGET_LEN
TARGET_BYTES          # raw identity; NEVER JSON string embed (I06)
u64be INDEX_LEN
INDEX_BYTES           # json.dumps(PRODUCT_A, ensure_ascii=False, sort_keys=False, allow_nan=False)
leftover MUST be 0
section_count = 2
```

Measured in CASE_A revalidation (RAM): ENV_LEN=38221963; target
identity PASS; leftover=0; extra-trailing leftover=1; concat leftover
equals second envelope size.

## Forbidden transports / transforms

JSON embed TARGET as string (I06 FAIL). `sort_keys`. Seq-sort.
Duplicate fusion. Offset-only catalog. Envelope fusion / JSONL
catalog-only. Unicode NFC/NFKC/NFD. Moving 493 P19 lines into carrier
index. Synthesizing absent types.

## Recovery

Payload recovery source = blob TARGET bytes.
Structure recovery source = decoded index object (key order preserved).
Fail closed if AIM-only or PRODUCT_A-only reconstruction is claimed.

## T17 (specified, not executed)

Failure partial write is FAIL. TARGET must remain
`08ffe7bc…5092` / 1421764. Single-file exclusive rename on same
filesystem; `rename(2)` without `RENAME_EXCL` can destroy dest.
`VOL_CAP_INT_RENAME_EXCL` unprobed; `F_FULLFSYNC` / dir fsync
untested. Python `os.RENAME_EXCL` absent on the measured interpreter.

Two-file blob+index is not a POSIX transaction and remains rejected as
T17-complete.

## Relation to the previously proposed Desktop write

A Desktop destination
`…&#47;PEAK_TRADE_FORENSIC_POST_STEP32_M06_LENGTH_PREFIXED_ENVELOPE_…ptf1idx`
was **proposed** under a separate Write-GO. This collection **did not**
perform that write. Worktree-local identity copies of TARGET and
PRODUCT_A are sufficient for inspectability in this phase.

A future write validation still requires its own Owner-GO, dest
ENOENT, and write-time gates.
