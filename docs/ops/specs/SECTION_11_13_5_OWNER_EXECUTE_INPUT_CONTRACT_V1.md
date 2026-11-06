# SECTION_11_13_5 Owner Execute Input Contract V1

```text
DOCUMENT_CLASS=OWNER_EXECUTE_INPUT_CHECKLIST
DOCUMENT_ROLE=NON_SSOT
NO_INVENTED_VALUES=true
LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN=false
LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=false
LIVE_AUTHORIZED=false
LIVE_RECONCILIATION_PROVEN=false
BLOCKS_NEW_ENTRY=true
AUTHORING_GO=OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING
SEPARATE_EXECUTE_GO=OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE
OWNER_GO_EXECUTE_STATUS=CONSUMED
RETRY_SAFE_NOW=false
POST_401_ROOT_CAUSE=UNPROVEN_FAIL_CLOSED
HISTORICAL_FIRST_401_ROOT_CAUSE=UNPROVEN_FAIL_CLOSED
LATEST_50124_CLASSIFICATION=OKX_50124_OBSERVED_ONESHOT_TRADING_POST
HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN=false
ROOT_CAUSE_PROVEN=false
```

Authoring GO prepares the surface only. The prior one-shot
`OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE` is **CONSUMED**. Historical first
POST HTTP 401 remains `UNPROVEN_FAIL_CLOSED`. A later one-shot trading
POST HTTP 401 with parseable OKX `50124` is a separate observed POST
classification (`OKX_50124_OBSERVED_ONESHOT_TRADING_POST`) and must not
be rewritten onto the historical incident, onto instrument GETs (those
were HTTP 200), or onto `account&#47;instruments` (not on the submit
path; empty SWAP list `CAUSAL_RELATION_UNPROVEN`). A later execute requires a **new** one-shot Owner-GO after merge **and**
a **separate** funding GO. Do not treat analog
GET `50113` as the proven historical incident body. Historical `50110`
IP-whitelist clearance is a §11.13.5.I-era fact only and is not the
oneshot `50124`. It is not a current auth attestation. This Owner
execute-input contract does not bind current egress IP, does not bind
current whitelist state, and does not authorize whitelist mutation.
Auth-repair authority is separate from Canary-submit authority.

```text
HISTORICAL_50110_CLEARANCE_REFERENCE=SECTION_11_13_5_I_ONLY
HISTORICAL_50110_CLEARANCE_IS_NOT_CURRENT_AUTH_ATTESTATION=true
OWNER_EXECUTE_INPUT_DOES_NOT_BIND_CURRENT_EGRESS_IP=true
OWNER_EXECUTE_INPUT_DOES_NOT_BIND_CURRENT_WHITELIST_STATE=true
OWNER_EXECUTE_INPUT_DOES_NOT_AUTHORIZE_WHITELIST_MUTATION=true
AUTH_REPAIR_AUTHORITY_SEPARATE_FROM_CANARY_SUBMIT_AUTHORITY=true
IP_WHITELIST_MUTATION_CANONICAL_CONTRACT=NONE_CURRENT
```

The current EEA canary instrument is `SUI-USD_UM_XPERP-310404` &#47; `FUTURES` &#47;
`xperp` &#47; USDC account truth. `BTC-USDT-SWAP` is rejected for this
path. Demo `BTC-USD_UM_XPERP-310328` remains Demo&#47;historical only.
Superseded `BTC-USD_UM_XPERP-310404` is not a current-target fallback.

## Required Owner inputs (future execute)

| Field | Required | Notes |
|-------|----------|-------|
| venue/entity/region/host/account | yes | Reuse proven LIVE binding (OKX EEA / `eea.okx.com` / `856964404452495999`) |
| instrument_id | yes | Canonical live EEA `SUI-USD_UM_XPERP-310404`. `BTC-USDT-SWAP`, Demo `BTC-USD_UM_XPERP-310328`, and superseded `BTC-USD_UM_XPERP-310404` are rejected as current target. No aliasing. |
| inst_type | yes | `FUTURES` (`ruleType=xperp`). `SWAP` is fail-closed for this canary path. |
| settlement truth | yes | Account&#47;UI truth `USDC`. Do not inherit SWAP USDT baseline. |
| instrument minSz/lotSz/ctVal/tickSz | yes | Fresh GET-only `SUI-USD_UM_XPERP-310404` metadata at execute; integer contracts `minSz=1` &#47; `lotSz=1`; not invented; not inherited from SWAP, Demo 310328, or superseded BTC 310404 |
| SecretRef URI | yes | `secretref:&#47;&#47;vault&#47;peak-trade&#47;live-canary-minimum-exposure&#47;okx` |
| `--vault-file` | yes | Local SecretRef JSON map; same §11.13.2/3/4 CLI pattern; no secrets in git |
| credential class | yes | `LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY` |
| permission attestation | yes | READ=true TRADE=true WITHDRAW=false |
| exchange-truth adoption policies | yes | Venue metadata + balances + local portfolio baseline policies |
| enabled/armed/confirm-token | yes | Session gates; confirm token `I_KNOW_WHAT_I_AM_DOING` |
| `--allow-productive-wire-send` | yes | Required for urllib construction; absent fails closed |
| live-canary-cybersecurity-gate | yes | Must be `PASS` |
| separate execute GO | yes | `OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE` (granted unconsumed; one-shot) |

## Hard stops

- Authoring GO cannot authorize submit
- Consumed execute GO cannot authorize submit
- `BLOCKS_NEW_ENTRY=true` blocks submit
- `LIVE_RECONCILIATION_PROVEN=false` blocks submit
- TRADE attestation false blocks submit
- Fixture/demo/testnet cannot satisfy productive LIVE binding
- No credential/vault material in Git
- `--vault-file` required for execute; absence fails closed
- Cap 11.9 remains fixture-only

Machine-readable generator:

`src/ops/section_11_13_5_live_canary_minimum_exposure_v1/owner_input_contract_v1.py`
