<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Configuration Wiring

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

| id | key | source | default | consumers | runtime_effect | status |
| --- | --- | --- | --- | --- | --- | --- |
| CFG:exchange_okx_europe_eea | exchange.okx_europe_eea | config/config.toml | enabled=false validate_only=true (as historically observed on origin/main) | OKX EEA adapter / testnet bindings | Venue enablement; does not confer LIVE_AUTHORIZED | CURRENT_NONCANONICAL |
| CFG:live_authorized | LIVE_AUTHORIZED | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md | false | all execution/canary paths | standing fail-closed deny of live orders | CURRENT_CANONICAL |
| CFG:max_positions | CURRENT_MAX_POSITIONS | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md | 1 | GATE:max_positions_1 | single-future position cap | CURRENT_CANONICAL |
| CFG:testnet_authorized | TESTNET_AUTHORIZED | docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md | false | testnet execute paths | standing fail-closed unless scoped Owner-GO | CURRENT_CANONICAL |

