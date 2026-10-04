# Paper-Shadow Bounded Run Settings Digest v1

## Authority

- **Manifest owner:** `src/ops/paper_shadow_bounded_orchestrator_v1/run_settings_manifest_v1.py`
- **Digest owner:** same module (`compute_run_settings_digest_v1`)
- **Spec ID:** `paper_shadow_bounded_run_settings_manifest.v1`
- **Spec version:** `1`

## Identity separation

| Identity | Binding |
|----------|---------|
| Code fixpoint | `FIXPOINT_SHA` + `FIXPOINT_TREE` on run contract (git HEAD at run time) |
| Run settings | `RUN_SETTINGS_DIGEST` (this spec) |
| Run bounds | `RUN_CONTRACT` fields + explicit Owner-GO `BOUND_TO` numeric fields |
| Authorization | Run-specific Owner-GO artifact (not consumed in preflight) |

Fixpoint SHA/tree are **excluded** from the settings digest payload.

## Digest input

Deterministic JSON object (`DIGEST_PAYLOAD`):

- `DOMAIN_SEPARATOR`: `PEAK_TRADE|PAPER_SHADOW_RUN_SETTINGS|V1`
- `SPEC_ID`, `SPEC_VERSION`
- `SETTINGS`: sorted by `SETTING_ID`, each entry `{SETTING_ID, VALUE}` only

Serialization: `canonical_json_text_v1` (see `archive_sibling_export_contract_v1&#47;canonical_digest.py`).

Hash: SHA-256 hex over UTF-8 canonical JSON text (no trailing newline).

## Included settings

Cartography-backed productive/shadow/safety/operator settings from CURRENT main, plus operational Run-001 runtime bindings:

- observation host, instrument, venue, transport
- `RUN_001_POLL_INTERVAL_SECONDS` (wallclock canonical constant; operational loop sleep owner)
- `RUN_001_MAX_STALE_SECONDS` (wallclock canonical constant; public MD fetch owner)
- `OBSERVATION_SOURCE`, `EXECUTION_SINK` (from run contract)
- orchestrator safety pins (`POST_ALLOWED`, `LIVE_*`, `TESTNET_*`, etc.)

Run duration and max observation/cycle/simulation counts are **not** in the settings digest; they are bound via run contract and Owner-GO.

## Historical digests

Historical `SETTINGS_DIGEST` values from pre-spec evidence have **no authority** for CURRENT main.
