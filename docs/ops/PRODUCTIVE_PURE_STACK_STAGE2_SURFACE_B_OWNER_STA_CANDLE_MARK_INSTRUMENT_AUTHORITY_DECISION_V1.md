# Stage-2 Surface B — Owner/STA Candle, Mark & InstrumentBinding Authority Decision v1

```text
DOCUMENT_TYPE=OWNER_STA_AUTHORITY_DECISION
DOCUMENT_VERSION=1
CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION
STATUS=OWNER_STA_DECISION_SURFACE_OPEN_INSTANCE_VALUES_NULL
BASELINE_ORIGIN_MAIN_SHA=3b6b75bc4fa4b3ba6887ed055fa7fb88dd3d87b7
PARENT_RAW_INPUT_PACK=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md
PARENT_SURFACE_B=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md
MACHINE_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISIONS_V1.json
SCHEMA=docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decisions_v1.schema.json
VALIDATOR=src/ops/productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decision_v1/
CYBERSECURITY_MIRROR=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_CYBERSECURITY_MIRROR_V1.md

AUTHORITY_SURFACE=B
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
STA_PRODUCER_ID=sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1
STA_PRODUCER_IS_RAW_SOURCE_AUTHORITY=false
O4_UNCHANGED=true
O4_PT1H_AS_PT1M_FORBIDDEN=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_ROLE=READ_ONLY_CONSUMER
NOTION_SSOT=false
REPOSITORY_IS_SSOT=true

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CANDLE_AUTHORITY_RATIFIED=false
MARK_AUTHORITY_RATIFIED=false
INSTRUMENT_BINDING_RATIFIED=false
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED

LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
CORE_LOGIC_CHANGE=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 0. Binding effect

This document is the Owner/STA **decision surface** that prepares the three
missing authority ratifications required before any Surface-B raw PT1M input
pack may later be Owner-bound:

1. venue-native finalized PT1M candle source authority;
2. separate venue-native PT1M bucket mark source authority;
3. complete `InstrumentBindingV1`.

It:

1. inventorizes repo-discovered producers, OKX public market-data ingest paths,
   finality semantics, competing instrument IDs, and join rules;
2. proposes fail-closed candidate `source_ref` values and an Owner decision
   table;
3. keeps all Owner values `null` / `OPEN` until explicit Owner ratification;
4. keeps `INPUT_AUTHORITY=false`, `RUNTIME_IMPLEMENTED=false`,
   `RAW_INPUT_PACK_CREATED=false`, and `CAMPAIGN_STARTED=false`.

It does **not**:

- load raw market data or materialize an input pack;
- start a shadow campaign;
- silently select an instrument ID;
- treat fixtures, evidence artifacts, dashboard, Notion, or STA producer
  existence as raw-source authority;
- authorize orders, credentials, testnet, live, paper exchange, or capital
  movement;
- set productive numeric calibration values.

```text
OWNER_STA_DECISION_SURFACE_CREATED=true
CANDLE_AUTHORITY_RATIFIED=false
MARK_AUTHORITY_RATIFIED=false
INSTRUMENT_BINDING_RATIFIED=false
INSTANCE_FIELD_VALUES_INVENTED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
```

## 1. Non-negotiable invariants

```text
INV_AUTHORITY_SURFACE_B_ONLY=true
INV_CANDLE_AND_MARK_ARE_SEPARATE_AUTHORITIES=true
INV_CANDLE_CLOSE_NEVER_SUBSTITUTES_MARK=true
INV_O4_PT1H_FORBIDDEN_FOR_THIS_PT1M_SURFACE=true
INV_DASHBOARD_NOTION_CONSUMER_ONLY=true
INV_FIXTURES_EVIDENCE_NOT_RAW_AUTHORITY=true
INV_TECHNICAL_PRODUCER_EXISTENCE_NOT_RAW_AUTHORITY=true
INV_NO_SILENT_INSTRUMENT_ID_SELECTION=true
INV_BTC_TEST_BINDINGS_EXCLUDED=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_RUNTIME_IMPLEMENTED_REMAINS_FALSE=true
INV_NO_PACK_MATERIALIZATION=true
INV_NO_CAMPAIGN_START=true
INV_NO_PRODUCTIVE_NUMERIC_VALUES=true
INV_REGIME_COVERAGE_REMAINS_SEMANTICALLY_UNRESOLVED_UNTIL_PRODUCER_EXISTS=true
```

## 2. Discovery summary (reuse-before-new)

### Candle / OHLCV paths

| Path | Role | Authority for this surface? |
|---|---|---|
| `/api/v5/market/history-candles` `bar=1m` + confirm=1 | Historical venue-native finalized OHLCV | **Candidate** raw candle authority |
| `/api/v5/market/candles` | Recent candles; may include open tip | Forbidden as historical finalized authority |
| O4 / PT1H public-MD bar producer | Separate canonical PT1H authority | Forbidden substitution for PT1M Surface B |
| `sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1` | STA consumer/producer of already-supplied candles+marks | Technical producer ≠ raw source authority |
| Dashboard / Notion / fixtures / Cap evidence packs | Consumer / mirror / test / historical evidence | Never raw-source authority |

### Mark paths

| Path | Role | Authority for this surface? |
|---|---|---|
| `/api/v5/market/history-mark-price-candles` `bar=1m` + confirm=1 | Historical venue-native mark series | **Candidate** raw mark authority |
| `/api/v5/public/mark-price` | Live/public snapshot markPx | Not historical series authority |
| Previous / coincident candle close | Staging asof heuristic elsewhere | **Forbidden** mark substitute for Surface B |
| Trade / last / index as mark | Non-mark fields | Forbidden |

### Finality / join

- OKX confirm field `1` maps to `venue_finalized=true` / `open_tip=false`.
- Event-time identity is `PT1M_BUCKET_OPEN_EVENT_TIME` (minute-aligned bucket open).
- Candle and mark join exclusively on that bucket-open key.
- Missing mark, duplicate bucket, open tip, or unfinalized candle fail closed.

### Competing instrument IDs (no silent choice)

See machine manifest `instrument_binding.competing_candidates`:

- `CAND_ETH_USDT_SWAP_RESEARCH_STAGING` — `inst-eth-usdt-perp` / `ETH-USDT-SWAP`
- `CAND_ADA_USDT_SWAP_CAP24_EVIDENCE` — Cap-2.4 evidence selection
- `CAND_SOL_USDT_SWAP_RANKING_EVIDENCE` — ranking/pre-activation evidence
- `CAND_ETH_USD_XPERP_OKX_EUROPE_BINDING` — `ETH-USD_UM_XPERP-310404`
- `EXCL_BTC_USDT_SWAP_TEST_FIXTURE` — excluded test binding (`BTC=FORBIDDEN`)

## 3. A. Candle Source Authority (structure)

Proposed (not ratified) `source_ref`:

```text
venue://okx/public/rest/v5/market/history-candles?bar=1m&confirm=1
```

Bound semantics:

- Venue: OKX public REST v5
- Endpoint/dataset: historical trade OHLCV candles
- PT1M bar: `bar=1m`
- Event time: `PT1M_BUCKET_OPEN_EVENT_TIME`
- `venue_finalized` mapping: confirm=`1` only
- Open tip: excluded (`open_tip_bars=false`)
- Pagination: `after` = oldest page ts
- Dedup: by ts, last wins
- Ordering: ascending event time
- Gaps: fail closed when continuity required
- PIT / no-lookahead: no bar after exclusive tip; no open bucket at as-of
- Immutable raw provenance + rebuild requires new `dataset_id` + digest
- Rejection conditions: listed in machine manifest

`owner_ratified_source_ref=null` until Owner fills the decision table.

## 4. B. Mark Source Authority (structure)

Proposed (not ratified) `source_ref` — **must differ** from candle:

```text
venue://okx/public/rest/v5/market/history-mark-price-candles?bar=1m&confirm=1
```

Bound semantics:

- Separate historical venue-native mark series (not snapshot endpoint)
- PT1M bucket semantics with join key `PT1M_BUCKET_OPEN_EVENT_TIME`
- No previous-candle-close fallback
- Missing / duplicate / late / non-final marks fail closed or require explicit revision
- PIT / no-lookahead identical to candle exclusive-tip rules
- Immutable separate raw mark provenance bound into pack digest
- Rejection conditions: listed in machine manifest

## 5. C. InstrumentBindingV1 (structure)

All seven required fields remain Owner-open:

```text
venue
canonical_instrument_id
venue_instrument_id
contract_type
market_type
quote_currency
settlement_currency
```

Owner must select from documented competing candidates or explicitly reject and
supply a new Owner ID. Silent defaulting is forbidden. BTC test bindings remain
excluded.

## 6. D. Regime Coverage

```text
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
```

No canonical Surface-B regime recorder producer was found. Structural label
slots exist under parent Surface B, but counts/labels must not be invented and
no new classifier is implemented by this decision surface.

## 7. E. Owner decision table

The machine-readable, fillable table lives in:

`docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISIONS_V1.json`
→ `owner_decision_table[]`

Each row has:

- `decision_id`
- `field`
- `allowed_options`
- `recommended_option` (only when repo-side uniquely justifiable; instrument IDs intentionally `null`)
- `rationale`
- `safety_semantic_consequences`
- `owner_value` (null)
- `status` (`OPEN` | later `RATIFIED` / `REJECTED`)

## 8. Explicitly null instance / numeric fields

```text
campaign_id=null
dataset_id=null
scenario_id=null
seed=null
partition_boundaries=null
fold_ids=null
bootstrap_seeds=null
purge=null
embargo=null
fold_sizes=null
all_productive_numeric_calibration_values=unset
```

## 9. Fail-closed ratification guards

Validator package
`src/ops/productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decision_v1/`
rejects ratification claims that lack:

- separate candle and mark `source_ref` values;
- complete seven-field `InstrumentBindingV1`;
- explicit Owner values while this surface remains `OPEN`;
- or that attempt candle=mark substitution, previous-candle-close mark fallback,
  O4/PT1H substitution, BTC test bindings, pack materialization, campaign start,
  or `INPUT_AUTHORITY` / runtime flips.

## 10. Explicit non-effects

```text
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CANDLE_AUTHORITY_RATIFIED=false
MARK_AUTHORITY_RATIFIED=false
INSTRUMENT_BINDING_RATIFIED=false
RAW_INPUT_PACK_CREATED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
CAMPAIGN_STARTED=false
CAMPAIGN_START_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
TRADING_LOGIC_CHANGED=false
ORDERS_TESTNET_LIVE_PAPER_EFFECTS=false
EXCHANGE_CREDENTIAL_EFFECTS=false
NOTION_CHANGED=false
```

## 11. Canonical next step

Owner fills `owner_decision_table[].owner_value` and the seven
`InstrumentBindingV1` fields, then issues a **separate** Owner GO to move status
from `OWNER_STA_DECISION_SURFACE_OPEN_INSTANCE_VALUES_NULL` to an
authorities-ratified state — still without pack materialization or campaign
start unless an additional explicit GO is issued.
