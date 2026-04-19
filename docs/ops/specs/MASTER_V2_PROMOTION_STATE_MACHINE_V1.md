# MASTER V2 — Promotion State Machine v1 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-19
owner: Peak_Trade
purpose: Canonical docs-only state-machine mapping for staged promotion visibility in the Master V2 path
docs_token: DOCS_TOKEN_MASTER_V2_PROMOTION_STATE_MACHINE_V1

## 1) Executive Summary

This specification materializes one compact, canonical promotion and state-machine view for Master V2.

It is mapping-only and non-authorizing. It improves readability of staged progression and transition boundaries, but it does not grant runtime permission or live authorization.

## 2) Scope and Non-Goals

In scope:

- canonical state-machine view for promotion across research-to-live stages
- explicit transition requirements, blockers, evidence needs, and authority boundaries
- explicit marking of unclear and partial transitions

Out of scope:

- runtime rewiring or implementation changes
- live authorization decisions
- gate closure by assertion

## 3) Canonical States

This state-machine uses the following states:

- `research`
- `backtest`
- `shadow-paper`
- `testnet`
- `live-gated`
- `live-authorized`

State semantics are interpretation and governance visibility only. They are not runtime activation semantics.

## 4) State Machine Table

| state | entry condition | exit condition | promotion requirement | blocking condition | required evidence | required authority | nearest repo evidence | current clarity |
|---|---|---|---|---|---|---|---|---|
| `research` | strategy or hypothesis exploration begins | reproducible backtest package is available | reproducibility and documented assumptions | missing reproducibility or unclear assumptions | strategy assumptions, dataset provenance, reproducible run references | research and governance review posture | [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md), [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md) | partial |
| `backtest` | reproducible historical evaluation exists | staged non-live execution posture is prepared | conservative pass criteria and stability posture | unstable evidence or unresolved risk interpretation | backtest outputs, stability checks, evidence continuity | governance and operator progression review | [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md), [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) | partial |
| `shadow-paper` | non-live execution surfaces are active | testnet-eligible preconditions are explicitly met | bounded behavior visibility and safe-posture continuity | ambiguity about gates, policy, or safety posture | runbook-aligned non-live session traces and operator review notes | governance and operator progression review | [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md), [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) | partial |
| `testnet` | sandboxed exchange-like flow is prepared | readiness-gate posture for bounded live candidate is explicit | acceptable interpretation across readiness and safety constraints | unresolved gate blockers or weak evidence chain | candidate-scoped readiness evidence bundle and incident readiness references | governance, safety, and operator review authority | [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | unclear |
| `live-gated` | readiness posture is visible and promotion gating is interpreted | explicit live authorization is separately granted by external authority | promotion interpretation with explicit non-authorization lock | conflation of promotion visibility with live permission | gate-status evidence and authority-boundary evidence | governance plus operator authority outside this spec | [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | partial |
| `live-authorized` | external authoritative live approval is explicitly present | revoke, expiry, emergency stop, or hard blocker triggers exit | explicit approval chain, lease constraints, and veto readiness | missing explicit approver chain or missing active safeguards | signed approval evidence, lease and budget evidence, veto readiness evidence | external governance and safety authority chain | [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | unclear |

## 5) Transition Notes

- `research -> backtest`: confirmed as intent-level progression, but one compact canonical transition contract is not materialized.
- `backtest -> shadow-paper`: progression semantics are visible through readiness framing, while explicit promotion criteria remain partial.
- `shadow-paper -> testnet`: adjacent evidence exists, but one consolidated testnet promotion contract is unclear.
- `testnet -> live-gated`: gate-oriented visibility is strong, but transition permission remains external and partial.
- `live-gated -> live-authorized`: this is the highest ambiguity boundary; readiness visibility is not equivalent to authorization.
- `live-authorized -> rollback states`: fail-closed and emergency-stop logic is evidenced, but one compact cross-state rollback map is still partial.

## 6) Relationship to Existing Master V2 Artifacts

- [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md): canonical readiness framing and stage anchor.
- [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md): compact gate visibility and conservative status posture.
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md): authority topology and unresolved approval-chain nodes.
- [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md): upstream scope and capital semantics adjacent to promotion logic.
- [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md): non-equality and authority-boundary language lock.

This specification only cross-links these artifacts and does not modify them.

## 7) Ambiguity, Confusion, and Interpretation Risk Map

- staged execution enablement versus live authorization: readiness staging does not imply permission grant.
- live-gated versus live-authorized: gate visibility and explicit authorization must remain separate.
- gate-status visibility versus transition permission: status reporting is not a promotion command.
- promotion authority versus runtime trading authority: promotion interpretation and execution authority remain distinct.
- paper or testnet success versus authorization eligibility: successful pre-live stages are insufficient without explicit approval chain.

## 8) Non-Authorizing Constraint

This specification authorizes nothing.

It only makes the promotion and state-machine view visible for review and audit.

`Verified` or clarified transition wording in this document is not equivalent to live authorized.

## 9) Evidence and Closure Criteria

Confirmed by this specification:

- one compact promotion-state visibility layer now exists for Master V2.
- state boundaries and transition ambiguity are explicitly marked.
- relationships to gate-status, authority, scope, and vocabulary surfaces are explicit.

Still open:

- one consolidated canonical approver chain for `live-authorized` entry and revocation
- one compact canonical transition contract for the full pre-live sequence
- one explicit rollback-state mapping artifact tied to authority evidence

Potential follow-up slice (separate topic):

- focused approval-chain closure slice for live-authorization transitions only, without runtime changes

## 10) Cross-References

- [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md)
- [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md)
- [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md)
- [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md)
- [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)
