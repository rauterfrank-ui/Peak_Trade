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
```

Authoring GO prepares the surface only. The prior one-shot
`OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE` is **CONSUMED** after the first
canary POST HTTP 401. A later execute requires a **new** one-shot Owner-GO
after merge and must not reuse the consumed execute GO. Do not treat analog
GET `50113` as the proven incident body.

## Required Owner inputs (future execute)

| Field | Required | Notes |
|-------|----------|-------|
| venue/entity/region/host/account | yes | Reuse proven LIVE binding (OKX EEA / `eea.okx.com` / `856964404452495999`) |
| instrument_id | yes | Canonical `BTC-USDT-SWAP` unless Owner rebinds |
| instrument minSz/lotSz/ctVal/tickSz | yes | From venue instruments metadata at execute; not invented here |
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
