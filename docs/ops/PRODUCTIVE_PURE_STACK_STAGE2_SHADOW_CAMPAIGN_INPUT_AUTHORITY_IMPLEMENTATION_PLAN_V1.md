# Stage-2 Shadow Campaign Input Authority — Bounded Implementation Plan v1

```text
DOCUMENT_TYPE=BOUNDED_IMPLEMENTATION_PLAN
DOCUMENT_VERSION=1
STATUS=AUTHORIZED_BY_OWNER_RATIFICATION
BASELINE_ORIGIN_MAIN_SHA=55922609182a3166320c0a66a3a0b7cda5c13090
OWNER_RATIFICATION=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md
DECISIONS_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_DECISIONS_V1.json
PACKAGE=src/ops/productive_pure_stack_stage2_shadow_campaign_input_authority_v1/
CLI=scripts/ops/run_productive_pure_stack_stage2_shadow_campaign_input_authority_v1.py
AUTHORITY_SURFACE=B
O4_UNCHANGED=true
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
ORDERS=false
TESTNET=false
LIVE=false
```

## 1. Goal

Deliver the Owner-ratified Surface-B PT1M finalized-OHLCV shadow-calibration
input path so Stage-2 shadow campaigns can bind immutable observation packs and
structural manifests without inventing productive numbers or expanding O4 /
dashboard authority.

## 2. Package layout

```text
src/ops/productive_pure_stack_stage2_shadow_campaign_input_authority_v1/
  __init__.py
  constants_v1.py
  models_v1.py
  boundary_guards_v1.py
  git_sha_loader_v1.py
  pt1m_finalized_ohlcv_producer_v1.py
  observation_pack_v1.py
  campaign_binder_v1.py
  dataset_manifest_builder_v1.py
  partition_manifest_builder_v1.py
  walk_forward_manifest_builder_v1.py
  bootstrap_manifest_builder_v1.py
  stress_manifest_builder_v1.py
  export_api_v1.py
```

Reuse (no parallel models):

- `FinalizedBarV1`, `ShadowCampaignRequestV1`, `ReproducibilityRecordV1`,
  `EmptyCapableManifestV1` from
  `src&#47;ops&#47;productive_pure_stack_numeric_policy_shadow_campaign_v1&#47;`
- Stage-1 observation identity (`PUBLIC_MARKET_FINALIZED_BARS` / `PT1M`)
- Arithmetic kernel candidate path
  `src&#47;execution&#47;paper&#47;futures_accounting.py` (projection authority only;
  not mutated)
- `SequenceSurvivalMetrics` shape in
  `src&#47;trading&#47;master_v2&#47;double_play_survival.py` (shape authority only;
  productive producer remains future-bounded)

## 3. Deliverables mapped to decisions

| Decision | Implementation artifact |
|---|---|
| AUTHORITY_SURFACE=B | `pt1m_finalized_ohlcv_producer_v1.py` + constants |
| PRICE_SEMANTICS | producer fail-closed join of venue candles + separate mark |
| INSTRUMENT_BINDING | `InstrumentBindingV1` single-instrument validation |
| DATASET_IDENTITY | `ObservationPackProvenanceV1` + pack digest |
| FINALITY_CORRECTIONS | bucket-close + finalizer confirmation; no open tip; revision/reject |
| PARTITION_PROTOCOL | structural partition builder; magnitudes null |
| WALK_FORWARD_PROTOCOL | expanding structural fold builder; sizes null |
| BOOTSTRAP_PROTOCOL | block-bootstrap structural builder; length/path-count null |
| STRESS_PROTOCOL | structural stress family entries only |
| SEQUENCE_LAYER_AUTHORITY | constants/guards authorizing future STA producer + futures_accounting projection; no parallel kernel |
| IMPLEMENTATION_BOUNDARY | export API + CLI + tests + boundary guards |

## 4. Explicit non-goals

- No productive calibration run
- No threshold candidates or Owner numeric magnitudes
- No `INPUT_AUTHORITY_*` flips
- No O4 interval/authority expansion
- No dashboard/read-model source authority
- No trading-logic mutation under `src&#47;trading&#47;master_v2&#47;`
- No orders / paper exchange / testnet / live / credentials
- No merge without separate `OWNER_MERGE_GO`

## 5. Test / guard plan

1. Owner-ratification static contract (docs + decisions JSON markers)
2. Producer fail-closed: missing mark, open tip, candle/mark equivalence attempt,
   multi-instrument, incomplete binding
3. Observation pack immutability + digest binding into reproducibility record
4. Semantic-free binder → `FinalizedBarV1` / `ShadowCampaignRequestV1`
5. Structural COMPLETE manifests with unset numeric magnitudes
6. Worktree-safe repository SHA loader
7. Boundary guards asserting forbidden effects remain false

## 6. Activation posture after this PR

```text
BOUNDED_SCAFFOLDING_AND_EXPORT=true
PRODUCTIVE_EMISSION=false
SHADOW_CAMPAIGN_MAY_CONSUME_BOUND_PACKS=true
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
```
