# Acquisition architecture (plan only — no execution)

## Pipeline

```text
discover
→ snapshot instrument metadata
→ acquire immutable raw partitions
→ verify checksums
→ normalize
→ validate
→ build PIT universe
→ register manifest
→ run read-only dataset qualification
→ (separate GO) economic reevaluation
```

Each stage is a separate fail-closed job with its own audit log. Downstream stages must refuse inputs that failed upstream digests.

## Stage contracts

### 1. discover

- Enumerate candidate native instrument IDs from:
  - sealed local universe manifest members
  - public instruments snapshots over time (periodic)
  - optional delisting recovery list (operator-curated file; never invent)
- Output: `discovery_manifest.json` + digest
- Fail if BTC &#47; spot leak into candidate set

### 2. snapshot instrument metadata

- Persist as-of snapshots (`instruments`, contract specs) into `raw&#47;meta&#47;asof=YYYY-MM-DD&#47;`
- Atomic write: write temp → fsync → rename
- Never overwrite prior asof partitions

### 3. acquire immutable raw partitions

- Partition key: `venue=okx&#47;market=linear_usdt&#47;inst=...&#47;date=YYYY-MM-DD&#47;kind={candles_1h|funding}`
- Idempotent: skip if partition digest already registered and bytes match
- Resume &#47; retry with exponential backoff respecting rate limits
- On persistent failure: write `quarantine&#47;...` + reason code; do not mark complete
- **No silent repair** of vendor payloads

### 4. verify checksums

- sha256 per file; compare to expected if re-fetch
- Mismatch → quarantine + FAIL partition

### 5. normalize

- Map native IDs → canonical `instrument_id` via existing canonicalization owner
- Enforce UTC PT1H close-exclusive semantics
- Emit typed bars; drop non-final open candle at acquisition frontier
- Schema version field required on every normalized object

### 6. validate

- Run panel validation codes from `pit_okx_pt1h_panel_ohlcv_dataset_v1` (+ extensions in gates doc)
- Coverage report per instrument × month
- Fail-closed on bitcoin presence, future leakage, forward fill detection

### 7. build PIT universe

- Use `pit_futures_universe_manifest_*` owners
- Membership per score epoch from lifecycle registry only
- Survivorship backfill forbidden

### 8. register manifest

- Append-only dataset registry entry for `..._chrono_3y_v1`
- Must not mutate `..._research_v1` digests
- Publish all digests listed in target contract

### 9. read-only dataset qualification

- Execute acceptance gates (separate doc)
- Emit `qualification_verdict.json` ∈ {PASS, PARTIAL, FAIL}
- Economic reevaluation **blocked** unless PASS (or operator-GO PARTIAL with reduced claims)

## Cross-cutting rules

| Rule | Requirement |
|---|---|
| Idempotency | Same partition key + same bytes → no-op |
| Atomic writes | temp + rename only |
| Quarantine | immutable; disposition logged |
| Schema versioning | bump on breaking normalize changes; dual-run until digests compared |
| Audit logging | command, sha, timestamps UTC, rate-limit sleep stats |
| Secrets | none; public endpoints only on default path |
| Authority | research-only; `AUDIT_RUNTIME_EFFECT=NONE` |
| No overwrite | existing dataset versions immutable |
| Unknown states | FAIL-CLOSED |

## What this PR does **not** implement

No new productive downloader code is shipped here. Implementation belongs to a later bounded execution PR after:

1. this plan merges, and
2. a **bounded history-depth probe** (no bulk) records reachable periods.
