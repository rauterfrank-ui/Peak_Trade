# F1/M9 REAL Campaign Activation and Production Wiring (Normative V1)

## Scope

Closes the three adjudicated runtime blockers after enablement (#6799):

1. `REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS` process activation for the authorized REAL entry only.
2. Production public-MD adapter bound to `CANONICAL_VOLATILITY_PREREGISTERED_PUBLIC_MD_SOURCE_V1`.
3. Canonical REAL CLI bootstrap via `import trading` before `src.*` imports.

## Non-goals (this slice)

- No campaign execution, authorization issuance, or authorization consumption in CI/tests of this slice.
- No FakeRealPublicMdSessionAdapterV1 on the production entry path.
- No productive apply, promotion, private API, credentials, or orders.

## Production entry

Script: `scripts/run_f1_m9_prospective_real_authorized_campaign_execution_v1.py`

Wires `build_production_real_public_md_session_adapter_v1()` and requires a fresh issued runtime authorization file.

After merge: issue new authorization → run REAL CLI → REAL public MD → terminal campaign verdict. No further code change required for that run.

Optional CLI flags (production REAL run typically omits both):

- `--isolated-real-campaign-root` — hermetic smoke only; production uses canonical durable root.
- Env `F1_M9_PRODUCTION_ENTRY_HERMETIC_PUBLIC_MD_BOUNDARY_V1=1` + marker path — smoke only; production uses real HTTPS fetcher.

## Verification

- `tests/governance/test_f1_m9_real_campaign_activation_and_production_wiring_v1.py`
- `tests/governance/test_f1_m9_production_real_cli_entry_execution_smoke_v1.py`
