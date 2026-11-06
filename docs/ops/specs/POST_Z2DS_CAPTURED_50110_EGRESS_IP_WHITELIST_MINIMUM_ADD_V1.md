---
docs_token: DOCS_TOKEN_POST_Z2DS_CAPTURED_50110_EGRESS_IP_WHITELIST_MINIMUM_ADD_V1
status: active
scope: Management-plane minimum add of captured 50110 IPv4; no GET; no trading POST
capability: POST_Z2DS_CAPTURED_50110_EGRESS_IP_WHITELIST_MINIMUM_ADD_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# Post-Z2DS Captured 50110 Egress IP Whitelist Minimum Add V1

## Goal

Add exactly `176.5.200.177` to the bound OKX EEA live-canary API-key
whitelist. The IPv4 is bound only to capture pack `20260903T171133Z`.
No private GET. No public GET. No trading POST. No P08 close.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
WHITELIST_MUTATION_PERFORMED=true
ORDER_PERFORMED=false
POSITION_CREATION_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
PREREQUISITE_08_CLOSED=false
RUNTIME_50110_CLEARANCE=NOT_TESTED
PRIVATE_API_AUTH_SUCCESS=UNPROVEN
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Management-plane only. Target
`secretref:&#47;&#47;vault&#47;peak-trade&#47;live-canary-minimum-exposure&#47;okx`.
Supersedes, and must not separately execute,
`PEAK_TRADE_OWNER_GO_OKX_EEA_EXTERNAL_IP_WHITELIST_MINIMUM_ADD_CURRENT_50110_EGRESS_V1`.

## Out of scope

- Private or public GET
- Trading POST / order submit / position creation / flatten
- Key rotation / permission change / SecretRef change
- P08 / funding / live / canary unlock

## Productive owners

| Surface | Owner |
| --- | --- |
| SSOT persist | `docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md` |
| Forensic pack | `evidence&#47;ops&#47;section_11_13_5_post_z2ds_50110_whitelist_add_from_capture_v1&#47;20260903T175654Z&#47;` |
| Source 50110 pack | `evidence&#47;ops&#47;section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1&#47;20260903T171133Z&#47;` |

## Observed management-plane state

```text
TARGET_UI_KEY_NAME=PeakTrade-Live-Canary-MinExp
WHITELIST_PRE_STATE=84.140.105.223,2.161.34.181,84.141.69.36
WHITELIST_POST_STATE=84.140.105.223,2.161.34.181,84.141.69.36,176.5.200.177
EXISTING_WHITELIST_IPS_PRESERVED=true
READ_PERMISSION=true
TRADE_PERMISSION=true
WITHDRAW_PERMISSION=false
```
