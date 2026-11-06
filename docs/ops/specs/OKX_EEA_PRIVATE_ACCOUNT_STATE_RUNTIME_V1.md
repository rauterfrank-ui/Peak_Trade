# OKX_EEA_PRIVATE_ACCOUNT_STATE_RUNTIME_V1

```text
DOCUMENT_CLASS=IMPLEMENTATION_SPEC
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
OWNER=ops.okx_eea_private_account_state_runtime_v1
BASELINE_SHA=150ddb069e75263e995bafd4e2edbead9a0d563a
```

Observation-only OKX EEA Private State Plane: ratified Private REST GET baseline/recovery,
authenticated Private WebSocket observation (login/subscribe/heartbeat only),
normalized account/balance/position/order/fill state, quality/provenance/reconciliation,
durable readmodel/restart, and thin adapters into existing governed pretrade seams.

Policy ratification: `config/governance/okx_eea_private_account_state_runtime_v1_policy_v1.json`.

Credential class: `OKX_EEA_PRIVATE_OBSERVATION_READ_V1` (GET + WS observation only; no POST;
no WS order send/amend/cancel; no trade-credential fallback).

Does not modify Cap 2.3 selection, MV2/DP, Pretrade fresh-GET authority, Execution POST/wire,
account-equity sizing authority, or external-effect authorization.

Local recovery integrity extension, 2026-11-03: restart consumers now require an
explicit trusted boundary and CURRENT quality without a reconciliation requirement.
Journal schema/digests and complete line framing are checked before restoration;
unproven legacy/raw/torn records are preserved and rejected. The journal is fsynced
before rebuildable indexes are updated, and fill deduplication reads its validated
records. Required REST rows/identities/numbers must be present; malformed positions
and fills are not converted into zero values. REST/WS comparisons bind instrument,
position side and order identity, with one existing order-state normalization.

After journal restore, only an exact known ReconciliationSnapshotV1 metadata shape
can be superseded automatically by a newly collected valid REST baseline. Actual
position/order/balance state or unknown/extended records still require canonical
reconciliation. This is private observation readiness, not full account identity,
pagination, freshness, custody, reservation restoration or trading admission proof.
