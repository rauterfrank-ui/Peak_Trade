---
docs_token: DOCS_TOKEN_G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT_V1
status: active
scope: Offline additive G12 delayed posId-zero conjunction contract; no GET; no POST; no merge; G12 remains open
capability: G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# G12 Delayed PosId Zero Row Full Conjunction Proof Contract V1

## Goal

Add an offline evaluator that can bind a delayed explicit `posId` zero
row to the existing authorized flatten lineage **without** weakening
zero, pending, related, or no-flip semantics. Do not close `G12`. Do
not GET. Do not POST. Do not treat `data=[]` as zero. Do not treat
`.ops_local` captures as canonical evidence.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=false
PRIVATE_AUTH_USED=false
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN
TARGET_POSITION_ZERO_PROVEN=false
LIVE_FLATTEN_PROVABILITY_PROVEN=false
EMPTY_DATA_IS_ZERO=false
DELAYED_ZERO_DOES_NOT_IMPLY_LIVE_FLATTEN_PROVEN=true
POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS=true
FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL=true
SECTION_11_14_AUTHORIZED=false
RETRY_ALLOWED=false
MERGE_AUTHORIZED_BY_THIS_PERSIST=false
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT
EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY_IF_NOT_PROVEN
NEXT_OWNER_GO_REQUIRED=PEAK_TRADE_OWNER_GO_G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Semantics

P1..P10 remain distinct. Delayed explicit zero satisfies only the
target-zero proposition (Z2CM unique explicit `pos==0` row). It does
not replace same-session post-readback identity. Causal lineage is
`posId` plus instrument plus temporal order, not identity equality.

Pending-empty requires `GET &#47;api&#47;v5&#47;trade&#47;orders-pending`
at or after the delayed zero observation. Related-nonzero completeness
requires unfiltered `GET &#47;api&#47;v5&#47;account&#47;positions`
(non-zero-oriented). A `posId` or `instId` filter cannot prove related
completeness. Historical recovery pending is not current pending.

No-flip is the existing pairwise pre-versus-observed-post predicate
applied to the delayed explicit zero row. Intermediate-path flip over
the delay window is outside current G12 semantics and is not invented
here.

The same-session CHOICE_B evaluator is unchanged. This contract is
additive. Fixture `full_conjunction_proven=true` is not canonical SSOT
and does not close `G12`.
