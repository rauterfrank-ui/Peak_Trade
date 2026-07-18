# Tick Provenance Contract

**Owner:** `trading.master_v2.offline_double_play_scenario_replay_v0.OfflineScenarioTickProvenanceV1`

## Required fields

| Field | Rule |
|-------|------|
| `provenance_version` | must be `v1` |
| `source_kind` | one of `offline_scenario_fixture`, `testnet_bounded_observation`, `synthetic_offline_validation` |
| `source_id` or `fixture_id` | at least one non-empty |
| `tick_index` | int >= 0; must match tick.tick_index |
| `sequence_number` | int >= 0 |
| `event_time_ms` | int > 0 |

## Authorization rules

- Injection requires `allow_test_scope_event_injection is True` (exact bool) AND offline execution surface AND validated provenance on every tick AND `scope_event_provenance=TEST_INJECTION`.
- Missing / partial / invalid provenance → injection blocked.
- Provenance does not create Direction, Side, Scope, or Switch decisions.
- Canonical switch authority remains `transition_state`; scope state remains `RuntimeScopeState`.
