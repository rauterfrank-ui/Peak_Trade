# INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1

```text
status: ACTIVE
capability: INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1
owner: ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
economic_gate_effect: NONE
```

> **Successor to PR #5591 / #5592 — still not an automatic session grant.**
> PR #5592 alone was **not** real-startfähig: CLI `run` hard-blocked with
> `REAL_NETWORK_CLI_PATH_NOT_ENABLED_IN_THIS_PR`, no productive issuance
> producers existed, and transport required an injected fetcher.
> This capability adds productive Session-Preregistration / Confirm-Token /
> Operator-GO / Authorization issuance and a canonical real public MD HTTPS
> transport for `https://eea.okx.com` only.
> **Merge of this capability does not authorize a session.**
> Each real session still requires a separate, explicit Operator-GO issuance.
> Orders, Paper-Execution, Testnet, Live, credentials, private APIs, and
> auto-promotion remain forbidden. Economic Validity is evaluated only from
> completed observation evidence and is not changed by session start.

## Pipeline position

```text
… → PAPER_SHADOW_OBSERVATION_READINESS_PASS
  → OPERATOR_PAPER_SHADOW_OBSERVATION_GO   # productive issuance owned here
  → INTEGRATED_PAPER_SHADOW_OBSERVATION    # wallclock runtime from #5592 + real MD here
  → INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE
  → …
```

## Hard invariants

```text
orders_authorized=false
testnet_authorized=false
live_authorized=false
auto_promotion_authorized=false
credentials_authorized=false
paper_execution_authorized=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_PASS=false
fixture_non_authoritative rejected for productive authorize/run
PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1 never sufficient alone
network_scope=okx_eea_futures_public_md_observe_v1
session_execution_scope=paper_shadow_observation_wallclock_v1
host=eea.okx.com
instrument=ETH-USD_UM_XPERP-310404
max_session_duration_seconds=21600
consumption BEFORE any DNS/socket/HTTP/transport-open
```

## CLI

```bash
python scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py preflight
python scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py preregister ...
python scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py issue-confirm-token ...
python scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py authorize ...
python scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py verify-authorization ...
python scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py run ...

# Wallclock CLI run now delegates to the productive path (fixtures rejected):
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py run ...
```

Confirm-token plaintext is written only to a 0600 `--token-out` / `--mint-token-out`
file and is never persisted inside authorization artifacts or logs.

## Reuse

Reuses without duplication: consumption, state machine, evidence writer, session
lock, killstate, observation cycle adapter, and wallclock bundle verifier from
`INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1`.
Reuses prereg/GO/confirm-token/authorization schemas and builders from
`PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1`.

## Explicit non-goals

- Automatic productive issuance on merge
- Automatic session start
- Orders / Paper-Execution / Testnet / Live
- Private APIs / credentials
- Economic Validity PASS / Promotion
- Notion updates
- Real network inside CI or capability tests (fake transport/clock only)

## Productive 6h session technical evidence closeout (2026-07-30)

Documentation Anchor:
`docs&#47;ops&#47;EVIDENCE_INDEX.md#ev-20260730-integrated-paper-shadow-productive-6h-technical-runtime-evidence-closeout`.

Session `pso_wallclock_prod_69ffce43e0bba94f176d3aa22db7cf17` completed with
`TECHNICAL_PASS_ECONOMIC_EVIDENCE_NOT_PRODUCED`. Technical / MD / safety /
lifecycle evidence PASS; `ECONOMIC_EVIDENCE_COMPLETE=false`;
`ECONOMIC_VALIDITY_PASS=false`; `PROMOTION_ELIGIBLE=false`. HOLD / quantity=0
is not economic evidence. Next capability:
`INTEGRATED_PAPER_SHADOW_STRATEGY_INTENT_AND_PORTFOLIO_ECONOMICS_EVIDENCE_V1`.
