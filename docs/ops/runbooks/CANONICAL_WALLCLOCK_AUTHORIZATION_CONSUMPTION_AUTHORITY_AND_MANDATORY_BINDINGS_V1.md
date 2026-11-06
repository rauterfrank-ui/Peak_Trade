# CANONICAL_WALLCLOCK_AUTHORIZATION_CONSUMPTION_AUTHORITY_AND_MANDATORY_BINDINGS_V1

```text
status: ACTIVE
capability: CANONICAL_WALLCLOCK_AUTHORIZATION_CONSUMPTION_AUTHORITY_AND_MANDATORY_BINDINGS_V1
owner: ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
economic_gate_effect: NONE
```

> `authorization_artifact_v2` is the **only** productive wallclock consumption authority.
> `AuthorizationArtifactV1` is `LEGACY_PRODUCTIVE_AUTHORITY_RETIRED` and never consumable.
> Merge does **not** create preregistration/authorization and does **not** start a 1h run.

## Authority matrix (call-graph)

| AUTHORITY_PATH | SCHEMA | WRITER | PARSER | CONSUMER | SESSION_START_REACHABLE | PRODUCTIVE | LEGACY | QUARANTINED | ACTION_REQUIRED |
|---|---|---|---|---|---|---|---|---|---|
| canonical_v2_gatekeeper | authorization_artifact_v2 | authorization_writer_v2 | parse_authorization_artifact_v2 | consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1 | after_atomic_v2_consume | true | false | false | KEEP_SOLE_AUTHORITY |
| wallclock_session_runtime.run | authorization_artifact_v2 | n/a | via gatekeeper | gatekeeper only | after_atomic_v2_consume | true | false | false | BOUND_TO_GATEKEEPER |
| productive_run_entrypoint | authorization_artifact_v2 | n/a | parse_authorization_artifact_v2 | delegates to session_runtime | after_atomic_v2_consume | true | false | false | BOUND_TO_GATEKEEPER |
| consume_authorization_for_wallclock_start_v1 | AuthorizationArtifactV1 | build_authorization_artifact_v1 | parse_authorization_artifact_v1 | REJECT | false | false | true | true | QUARANTINED |
| formal_authorization_v1 | formal_authorization_v1 | historical | legacy classifier | REJECT | false | false | true | true | HISTORICAL_ONLY |

## Mandatory bindings

Parser and gate reject missing/null/wrong-type/unsafe values for:

- identity: authorization_id, schema/schema_version, preregistration_id/digest, repository_sha, runbook_sha256, capability, session_config_digest, created_at/expires_at
- safety_boundaries (exact bools): wallclock_mode=true, public_market_data_only=true, analytical_simulated_execution=true, external_paper_order_execution=false, real_order_routing=false, private_api=false, forced_wiring_fixture_mode=false, no_implicit_resume=true
- session_duration_seconds=3600
- config: `session_config_digest` must equal `config_digests.effective_session_config`

No silent coercion (`"false"`/0/1/missing→default).

## Explicit non-goals

- Preregistration / authorization issuance
- Authorization consumption outside tests
- 1h wallclock run
- Private API / Orders / Testnet / Live
- Notion / external cybersecurity mutation
