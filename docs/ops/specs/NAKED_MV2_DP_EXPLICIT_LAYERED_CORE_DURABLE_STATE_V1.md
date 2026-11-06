# Naked MV2+DP explicit layered core — durable state v1 (P3)

```text
OWNER=P3_DURABLE_L1_L10_STATE_V1
CORE_VERSION=naked_mv2_dp_explicit_layered_core/v1
SNAPSHOT_SCHEMA=naked_mv2_dp_explicit_layered_core_durable_state.v1
PRODUCTIVE_BINDING_AUTHORIZED=false
AUTHORITY_CUTOVER_OCCURRED=false
EXTERNAL_EFFECT_AUTHORIZED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
LEGACY_SEMANTIC_FALLBACK=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Persisted fields are L1–L10-native only (`durable_state_v1.py`). Restore rejects
integrated SideState, canonical scope, runtime scope anchor, and other legacy keys.

Atomic persist: `naked_layered_core_episode_v1.json` + `MANIFEST.sha256` via temp + `os.replace`.
