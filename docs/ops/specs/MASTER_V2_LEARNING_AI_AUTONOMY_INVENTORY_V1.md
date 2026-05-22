# MASTER V2 — Learning AI Autonomy Inventory v1 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-05-22
owner: Peak_Trade
purpose: Canonical docs-only inventory of learning, AI, and autonomy surfaces for Master V2 clarification
docs_token: DOCS_TOKEN_MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1

## 1) Executive Summary

This specification materializes a compact, repo-evidenced inventory of learning, AI, and autonomy surfaces adjacent to Master V2.

It is mapping-only and non-authorizing. Its purpose is readability and auditability of boundaries and gaps, not runtime enablement.

## 2) Scope and Non-Goals

In scope:

- repo-visible learning, AI, autonomy, evidence, and approval surfaces
- explicit distinction between advisory behavior, authoritative decisions, and veto boundaries
- explicit marking of unclear or partial materialization

Out of scope:

- runtime rewiring or implementation changes
- live authorization
- model release by assertion
- online-learning activation

## 3) Canonical Inventory Categories

This inventory uses the following canonical categories:

- learning triggers
- training loops
- offline learning and retraining
- online learning and adaptation
- knowledge base and memory-like layer
- AI-layer orchestration
- model orchestration and routing
- approval logic for updated models
- decision authority for model and policy changes
- feedback loops from outcomes to learning
- evidence, audit, and replay trail for learning and model changes

## 4) Inventory Table

| category | canonical meaning | nearest repo evidence | what is confirmed | what remains unclear | authority visibility | confidence | ambiguity and gap |
|---|---|---|---|---|---|---|---|
| learning triggers | events that should start learning-related review or retraining flow | [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md), [BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md](../decisions/BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md) | trigger-like governance conditions and re-entry guardrails are documented | one compact canonical trigger registry for Master V2 is not materialized | partial | partial | trigger semantics are distributed across governance and decision notes |
| training loops | closed-loop training process definitions and control boundaries | [BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md](../decisions/BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | closed self-learning loops are explicitly disallowed in current guardrails | one canonical training-loop contract for Master V2 is not materialized | unclear | partial | boundary is mostly defined by prohibitions, not by one positive loop contract |
| offline learning and retraining | bounded offline model improvement outside live hot path | [BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md](../decisions/BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | offline-only direction is explicit in multiple documents | canonical retraining lifecycle with approval checkpoints is not consolidated | partial | partial | retraining semantics exist, but lifecycle ownership remains distributed |
| online learning and adaptation | live-time adaptation that affects behavior | [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md), [BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md](../decisions/BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md) | online-learning influence on live behavior is explicitly blocked | approved exception path is intentionally absent | clear for prohibition | high | prohibition is strong, but no positive allowed path is specified |
| knowledge base and memory-like layer | documented knowledge surfaces used for context and review continuity | [KNOWLEDGE_BASE_INDEX.md](../../KNOWLEDGE_BASE_INDEX.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | a broad knowledge index and canonical vocabulary layer exist | one Master V2-specific memory contract tied to authority boundaries is not materialized | partial | partial | knowledge indexing exists without one consolidated Master V2 memory contract |
| AI-layer orchestration | AI coordination layer above execution and risk hot path | [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | AI orchestration is documented as advisory and non-execution authority | one compact Master V2 orchestration capability map is not materialized | partial | partial | role boundaries are explicit but spread across governance and vocabulary docs |
| model orchestration and routing | proposer, fallback, critic model assignment and separation of duties | [AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md](../../governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | proposer and critic separation plus model-assignment fields are documented | canonical runtime-routing contract for Master V2 remains outside this inventory | partial | partial | template fields are clear but do not assert one authoritative runtime router |
| approval logic for updated models | process and sign-off requirements before stronger autonomy states | [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md), [AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md](../../governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md), **§10 Stage-7 approval state machine** | evidence pack and sign-off obligations are explicit; **§10 materializes model/policy approval state machine index** | runtime enforcement of transitions remains out of scope | partial | partial | approval chain indexed in §10; runtime router still outside inventory |
| decision authority for model and policy changes | who can approve, veto, or stop changes | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), **§10** | **§10** is canonical Stage-7 approval index (S0–S15); Decision Authority Map stage-10 row cross-references **§10**; operator/external gates indexed | single runtime approver enforcement remains open | partial | partial | docs-index cross-link complete; runtime enforcement out of scope |
| feedback loops from outcomes to learning | how outcomes inform future learning or policy updates | [BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md](../decisions/BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | read-only and offline-first feedback intent is explicit | canonical bounded feedback protocol is not materialized | unclear | partial | distributed references, no single Master V2 feedback contract |
| evidence, audit, and replay trail for learning and model changes | artifacts proving what changed, why, and under which authority | [AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md](../../governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | evidence, replay, provenance, and sign-off fields are strongly documented | one compact Master V2 learning-change evidence index is not materialized | partial to strong | partial to high | evidence primitives are strong; consolidation as one index remains open |

## 5) Advisory, Authoritative, and Approval Boundary Notes

- Advisory AI behavior: documented as analysis and recommendation support, not final execution authority.
- Authoritative trading decisions: remain external to AI orchestration and remain bounded by governance, risk, and safety layers.
- Approval authority for model or policy changes: normative docs index in **§10** with Decision Authority Map cross-reference; runtime enforcement of transitions remains out of scope.
- Veto and fail-closed boundaries: governance and safety veto posture is explicit and dominates advisory outputs.

## 6) Ambiguity, Confusion, and Interpretation Risk Map

- advisory AI versus authoritative execution decisioning: advisory wording can be misread as approval if authority tags are omitted.
- learning loops versus runtime decision loops: learning-oriented updates can be confused with live decision-path logic if boundary language is weak.
- model orchestration versus strategy selection: model routing and strategy switching remain distinct and must not be collapsed.
- offline retraining versus online adaptation: offline allowance exists, online adaptation in live influence remains prohibited.
- evidence and registry artifacts versus actual learning authority: rich artifacts do not automatically prove consolidated authority ownership.

## 7) Non-Authorizing Constraint

This specification authorizes nothing.

It only inventories the currently visible learning, AI, and autonomy surfaces and their boundary posture.

Unclear and partial areas remain explicitly marked as unclear and partial.

Live remains separately gated and separately authorized.

## 8) Evidence and Closure Criteria

Confirmed by this specification:

- one dedicated Master V2 learning, AI, and autonomy inventory surface now exists
- advisory, authority, and veto boundary distinctions are explicitly readable
- evidence and provenance primitives are mapped with conservative confidence labeling

Still open:

- one consolidated learning-change evidence index tied to explicit authority nodes
- runtime enforcement of Stage-7 approval transitions (explicitly out of scope)

Addressed in §10 (docs index only):

- consolidated approval-chain map for model and policy updates at Stage 7

Potential next follow-up slice (separate topic):

- learning-change evidence index consolidation (no new approval spec)

## 9) Cross-References

- [RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md](RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) — §12 autonomy crosswalk; stage 7 row; §12.3 permanent operator-only gates
- [MASTER_V2_GO_LIVE_ROADMAP_V0.md](MASTER_V2_GO_LIVE_ROADMAP_V0.md) — §3.1 stage vocabulary
- [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md) — environment promotion visibility (orthogonal to §10)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md)
- [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md)
- [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
- [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)
- [AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md](../../governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md)
- [POLICY_CRITIC_STATUS.md](../../governance/POLICY_CRITIC_STATUS.md)
- [BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md](../decisions/BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md)
- [KNOWLEDGE_BASE_INDEX.md](../../KNOWLEDGE_BASE_INDEX.md)
- [AI_AUTONOMY_CONTROL_CENTER.md](../control_center/AI_AUTONOMY_CONTROL_CENTER.md)
- [CANARY_LIVE_ENTRY_CRITERIA.md](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md)

## 10) Stage-7 model/policy approval state machine (normative index)

```
STAGE_7_MODEL_APPROVAL_STATE_MACHINE_V0=true
STAGE_7_APPROVAL_STATE_COUNT=16
MODEL_RECOMMENDATION_NON_AUTHORIZING=true
POLICY_CANDIDATE_NON_EXECUTING=true
APPROVAL_PACKET_REVIEW_INPUT_ONLY=true
ONLINE_LEARNING_TO_LIVE_FORBIDDEN=true
MODEL_CHANGE_REQUIRES_REAPPROVAL=true
FORBIDDEN_AUTO_PROMOTION_RECOMMENDATION_TO_LIVE=true
FORBIDDEN_AUTO_PROMOTION_EVIDENCE_PASS_TO_LIVE=true
FORBIDDEN_AUTO_PROMOTION_PACKET_TO_GO_DECISION=true
EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true
GO_DECISION_REQUIRES_EXTERNAL_RECORD=true
AI_L6_EXEC_FORBIDDEN=true
KILLSWITCH_SAFETY_VETO_DOMINATES=true
```

This section is the **normative index** for Stage-7 model/policy change approval near [MASTER_V2_GO_LIVE_ROADMAP_V0.md](MASTER_V2_GO_LIVE_ROADMAP_V0.md) §3.1 stage 7 and [RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md](RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) §12.2 row `7`. It does **not** authorize runtime, live deploy, scheduler unlock, or model release by assertion.

**Reuse-before-new:** Environment promotion visibility remains in [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md). Permanent operator-only gates remain indexed in taxonomy §12.3 — **not re-listed here** (pointer only).

**Critical inequality:** `approval_packet_complete ≠ operator_decision_granted ≠ go_decision_granted ≠ live_deploy_authorized`.

### 10.1 Semantic distinctions

| term | authority | may authorize runtime/live? |
|---|---|---|
| Model recommendation | AI L0–L3 advisory (REC/PROP) | **No** |
| Policy candidate | Versioned proposal artifact | **No** |
| Shadow / paper / testnet evidence | Bounded lanes (taxonomy §10) | **No** |
| Approval packet | [AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md](../../governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md) | **No** (review input only) |
| Governance review outcome | L4 critic + human governance | **No** |
| Operator decision record | `operator_decision_required` | **No** for live; bounded non-live only |
| Canary / pilot gate | Readiness + GLB + LB-APR-001 class | **No** repo auto-clear |
| Live deploy approval | External `go_decision_granted` | **Only** external path to live capital |
| Monitored autonomy (Stage 7) | Locked approved model/policy within prior Go | Model change **re-enters** at `S2` |

### 10.2 State machine table (S0–S15)

| state_id | description | max AI layer | evidence owner (canonical) |
|---|---|---|---|
| `S0_IDLE` | No pending model/policy change | L0–L2 RO/REC | N/A |
| `S1_MODEL_RECOMMENDATION` | AI advisory output captured | L0–L3 max PROP | AI evidence packs; [AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md](../../governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md) |
| `S2_POLICY_CANDIDATE_DRAFT` | Versioned change proposal | L0–L3 | Policy/version refs; artifact hashes |
| `S3_OFFLINE_RETRAIN_COMPLETE` | Offline retrain artifact (non-live) | L0–L3 | Offline run logs; [BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md](../decisions/BAYESIAN_EVIDENCE_LAYER_V0_DECISION.md) |
| `S4_SHADOW_EVIDENCE` | Shadow bounded observation | L0–L2 | Shadow adapter + review (taxonomy §10) |
| `S5_PAPER_EVIDENCE` | Paper bounded observation | L0–L3 | Paper adapter; preflight §2a retention |
| `S6_TESTNET_EVIDENCE` | Optional testnet validation | L0–L3 | Testnet adapter + review (taxonomy §10) |
| `S7_APPROVAL_PACKET_ASSEMBLED` | EVP v2 complete; SoD PASS | L4 review input | `AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2` |
| `S8_GOVERNANCE_REVIEW` | L4 critic + human governance review | L4 RO/REC | [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) |
| `S9_OPERATOR_DECISION_PENDING` | Awaiting operator accept/reject | — | Operator decision record |
| `S10_OPERATOR_ACCEPTED_BOUNDED` | Accepted for **bounded non-live** only | L0–L5 | Decision record + evidence chain |
| `S11_CANARY_PILOT_ELIGIBLE` | Separate Canary/pilot readiness (stage 5) | L0–L4 | Readiness ladder; GLB; [CANARY_LIVE_ENTRY_CRITERIA.md](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) |
| `S12_LIVE_DEPLOY_PENDING_EXTERNAL` | Awaiting external Go (not auto from S10/S11) | — | LB-APR-001 class; Canary manifest |
| `S13_MONITORED_AUTONOMY_LOCKED` | Stage 7 runtime; model/policy version **locked** | L0–L5; L6 forbidden | Session review; this inventory |
| `S14_ROLLBACK_OR_VETO` | KillSwitch, safety, GLB, operator revoke | L5 veto | Incident + stop playbooks |
| `S15_RETIRED` | Policy superseded | — | Archive evidence |

States `S4`–`S6` are **parallel evidence lanes**, not strict serial requirements for every change.

### 10.3 Allowed transitions (index)

- `S0 → S1` — AI recommendation (non-authorizing)
- `S1 → S2` — operator promotes to formal candidate (**not automatic**)
- `S2 → S3` — offline retrain (offline only)
- `S3 → S4|S5|S6` — bounded evidence (Stage-3 gated adapter execute)
- `S4|S5|S6 → S7` — packet assembly (review PASS ≠ execute auth)
- `S7 → S8 → S9` — governance review → operator decision pending
- `S9 → S10` (accept bounded) | `S0` (reject)
- `S10 → S11` (optional Canary readiness)
- `S11 → S12` — external Go still required
- `S12 → S13` — external `go_decision_granted` + Canary + KillSwitch path
- `S13 → S2` — **any** model/policy change (`MODEL_CHANGE_REQUIRES_REAPPROVAL=true`)
- `ANY → S14` — veto / KillSwitch / GLB / operator emergency
- `S14 → S0|S13` — explicit operator closeout only (not automatic)

### 10.4 Forbidden auto-promotions

| forbidden transition | literal / ref |
|---|---|
| Recommendation → live deploy | `FORBIDDEN_AUTO_PROMOTION_RECOMMENDATION_TO_LIVE` |
| Evidence PASS → live | `FORBIDDEN_AUTO_PROMOTION_EVIDENCE_PASS_TO_LIVE`; `EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true` |
| Testnet pass → live | `TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true` |
| Packet/review → Go | `FORBIDDEN_AUTO_PROMOTION_PACKET_TO_GO_DECISION` |
| Skip external Go → monitored live | `GO_DECISION_REQUIRES_EXTERNAL_RECORD=true` |
| Offline retrain → monitored live direct | `ONLINE_LEARNING_TO_LIVE_FORBIDDEN=true` |
| Dashboard/Notion/docs/AI → approval | `FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL` (taxonomy §5) |
| Online learning on live path | taxonomy §12.4; online-learning inventory row |

### 10.5 Vetoes (always dominate)

KillSwitch/safety (GLB-008 class), L5 Risk Gate, **L6 EXEC forbidden**, strategic switch-gate, GLB blockers, scheduler hard-block (taxonomy §7), scope/capital envelope breach — all force or block toward `S14`.

### 10.6 AI may recommend vs gates may authorize

- **L0–L3 AI:** may recommend; **must not** authorize live, Go, promotion, or scheduler unlock.
- **L4 Policy Critic:** governance review on packet only; **not** execution or live.
- **L5 Risk Gate:** deterministic hard-limit checks only.
- **Evidence / readiness / dashboard:** **must not** authorize runtime or live.
- **Operator:** bounded non-live acceptance; live requires external Go.
- **External governance:** sole source of `go_decision_granted`.

### 10.7 Non-goals

- No parallel Stage-7 approval spec
- No new readiness/evidence registry
- No runtime transition enforcement
- No scheduler/live/testnet execute enablement
