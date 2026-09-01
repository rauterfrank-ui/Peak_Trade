# Offline Observation / Proposal Contract Fences v1

status: ACTIVE
last_updated: 2026-09-02
owner: Peak_Trade
purpose: Inventory and fail-closed fence for existing offline observation, comparison, proposal, and promotion-eligibility contracts. Not a learning, promotion, trading, selection, runtime, or live authority.
docs_token: DOCS_TOKEN_OFFLINE_OBSERVATION_PROPOSAL_CONTRACT_FENCES_V1

```text
OWNER_GO=PEAK_TRADE_OWNER_GO_WP_02_OFFLINE_OBSERVATION_PROPOSAL_CONTRACT_FENCES_MAX_SAFE_LEVERAGE_V1
THIS_DOCUMENT_IS_INVENTORY_AND_FENCE_POINTER_NOT_RUNTIME_AUTHORITY=true
PRODUCTIVE_LEARNING_AUTHORITY=NONE
PRODUCTIVE_PROMOTION_AUTHORITY=NONE
CAN_GRANT_AUTHORITY=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
TESTNET_AUTHORIZED=false
ORDERS_ALLOWED=false
```

Machine owner:

[`src/governance/offline_observation_proposal_contract_fences_v1.py`](../../src/governance/offline_observation_proposal_contract_fences_v1.py)

This document does **not** authorize Live, Testnet, Canary, orders, credentials, auto-apply, or productive learning&#47;promotion.

## 1. Contract layers

The fence keeps these layers distinct and fail-closed:

1. `OBSERVATION`
2. `COMPARISON`
3. `PROPOSAL`
4. `PROMOTION_ELIGIBILITY`
5. `PRODUCTIVE_MUTATION` — unreachable without a separate Owner-GO
6. `PRODUCTIVE_PROMOTION` — unreachable without a separate Owner-GO

## 2. Surface roles

| Surface | Role | Authority effect |
|---|---|---|
| [`src/meta/learning_loop/runtime_observation_feedback_v1.py`](../../src/meta/learning_loop/runtime_observation_feedback_v1.py) | Offline observation, comparison, and proposal contracts only | NONE |
| Surface O (`feedback_learning_boundary_*`) | Observation only | NONE |
| Surface M (`promotion_economic_gate_v1`) | Promotion-gate evaluate only | NONE |
| Legacy promotion engine | Proposal / manual-only, default-off, ungranted | NONE |
| DDO ([`src/learning/deterministic_decision_outcome_v0/authority_v0.py`](../../src/learning/deterministic_decision_outcome_v0/authority_v0.py)) | Offline observation only; parallel to learning_loop | NONE |

Surface M `PASS` remains candidate-eligibility evaluation. It does not grant deployment, runtime, activation, or execution.

DDO capture-hook presence is **not** an authority grant. DDO does not replace `learning_loop`.

## 3. Ledger families remain distinct

- DDO ledger envelope `ddo_ledger_envelope`
- execution accounting ledger
- aiops trend ledger
- Atlas historical child ledger
- research trade ledger

## 4. Out of scope

WP-03 observability projection, WP-04 decision-map work, Atlas mutation, Landscape authority, Cap 2.3 selection ownership, MV2&#47;Double Play core, CanonicalOrderIntent, SimulatedExecutionPort, Cap 7.2 host activation, live&#47;testnet&#47;canary&#47;order submit.
