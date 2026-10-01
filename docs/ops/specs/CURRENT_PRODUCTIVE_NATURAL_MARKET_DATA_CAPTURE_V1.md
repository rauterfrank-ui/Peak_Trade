---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_NATURAL_MARKET_DATA_CAPTURE_V1
status: active
scope: Append-only natural market-data GET capture for CURRENT Golden Happy Vector observation runs; no trading authority; no replay authority
capability: CURRENT_PRODUCTIVE_NATURAL_MARKET_DATA_CAPTURE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-01
---

# CURRENT Productive Natural Market Data Capture V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
REPLAY_PRODUCTIVE_AUTHORITY=NONE
POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## 1. Purpose

Persist **verbatim** OKX read-only GET responses already acquired by
`FullCoreProductiveReadOnlyGetTransportV1` during the CURRENT policy-governed
Golden Happy Vector product entry, for later **read-only** signal-liveness
adjudication via `InjectedContinuousObservationV1` reconstruction.

Capture is **observation-only**. It must not alter GET semantics, cache policy,
request-count fuse, Fresh-C1 poll logic, or any downstream decision stack.

## 2. Insertion point

```text
PRODUCT_ENTRY=scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py
TRANSPORT=FullCoreProductiveReadOnlyGetTransportV1
WRAPPER=ProductiveNaturalMarketDataCaptureTransportV1
LIVE_OBSERVATION_OWNER=LiveFreshC1ContinuousObservationSourceV1 (unchanged)
FIRST_SHARED_LIVE_OFFLINE_SYMBOL=InjectedContinuousObservationV1
FIRST_SHARED_DECISION_SYMBOL=map_injected_candles_payload_to_current_productive_c1_observation_v1
```

Wrapper is applied only when explicitly enabled on the product entry CLI.

## 3. Ledger

```text
EVIDENCE_RELATIVE_PATH=natural_market_data_get_capture_v1.jsonl
SCHEMA_VERSION=natural_market_data_get_capture.v1
APPEND_ONLY=true
EVIDENCE_ROOT_SCOPE=per-run --evidence-root only
```

### 3.1 Required fields (successful GET rows)

| Field | Semantics |
|-------|-----------|
| `schema_version` | `natural_market_data_get_capture.v1` |
| `run_id` | Continuous run id |
| `capture_sequence` | Monotonic 0-based per run |
| `captured_at_utc` | Wall time at append |
| `native_id` | Cap24-bound venue native id for the run |
| `get_kind` | `CANDLES` \| `MARK` \| `INDEX` \| `OTHER` (path-based) |
| `request_path` | Path from transport `endpoint` |
| `request_query` | Parsed query map or `UNAVAILABLE` |
| `payload` | Exact delegate JSON object |
| `body_sha256` | From `FreshPretradeGetTransportResultV1` |
| `auth_required` | As passed to `get()` |
| `get_cache_policy` | As passed to `get()` |
| `pretrade_decision_id` | Caller correlation hint when provided |

Fields not provable from the transport result remain `UNAVAILABLE`; they must
not be invented.

## 4. Correlation limits

```text
CORRELATION_STATUS=PARTIAL
COMPLETE_POLL_BUNDLE_CAPTURE_PROVEN=false
```

Per-row `get_kind` distinguishes candles, mark, index, and other shared-transport
GETs. **No** claim that N candle ledger lines equal N complete
`InjectedContinuousObservationV1` bundles. Bundle reconstruction is out of scope
for this capture slice.

## 5. Passthrough invariants

1. Exactly **one** delegate `get()` per wrapper `get()`.
2. Returned `FreshPretradeGetTransportResultV1` is **unchanged** (including
   `payload`, `body_sha256`, `get_performed`, cache behavior).
3. No extra venue GETs; no retries; no cache-policy changes.
4. Delegate exceptions propagate unchanged.

## 6. Capture write failure policy

Aligned with `append_fresh_c1_get_owner_go_consumption_v1` (filesystem append on
the evidence root): persistence failures **propagate** as exceptions.

```text
CAPTURE_WRITE_FAILURE_POLICY=FAIL_CLOSED_PROPAGATE
SILENT_SWALLOW_FORBIDDEN=true
```

When capture is **disabled**, behavior is identical to the pre-capture product
entry. When capture is **enabled**, a write failure aborts the run explicitly
rather than silently omitting evidence.

## 7. Activation default

```text
CAPTURE_DEFAULT_ENABLED=false
CLI_FLAG=--enable-natural-market-data-capture-v1
```
