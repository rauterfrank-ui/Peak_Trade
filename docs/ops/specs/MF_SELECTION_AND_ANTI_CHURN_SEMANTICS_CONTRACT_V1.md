---
docs_token: DOCS_TOKEN_MF_SELECTION_AND_ANTI_CHURN_SEMANTICS_CONTRACT_V1
status: active
scope: Docs-only persist of adjudicated isolated MF selection and anti-churn mechanism semantics; no host adapter; no Cap-2.3/2.4 join; no numerics
capability: NONE
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-09
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
G13_UNLOCK: false
HARD_STOP: true
---

# MF Selection and Anti-Churn Semantics Contract V1

```text
DOCUMENT_CLASS=DOCS_ONLY_NON_AUTHORIZING_SUBORDINATE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_MF_SELECTION_AND_ANTI_CHURN_SEMANTICS_PERSIST_V1
BOUND_ORIGIN_MAIN_SHA=a430bd3837a833d56a8029d3c0d5e8c5380708a1
CONTRACT_ID=MF_SELECTION_AND_ANTI_CHURN_SEMANTICS_CONTRACT_V1
PARENT_BOUNDARY_CONTRACT=MF_SELECTION_CONTEXT_BOUNDARY_CONTRACT_V1
PARENT_OWNERSHIP_CONTRACT=MF_SELECTOR_CONSUMPTION_AND_ANTI_CHURN_OWNERSHIP_CONTRACT_V1
CONTRACT_CLASS=NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
CONTEXT_ONLY=true
SELECTION_AUTHORITY=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
ALPHA_ALLOWED=false
G13_UNLOCK=false
CAP23_REMAINS_SOLE_SELECTION_OWNER=true
CAP24_REWIRED=false
CAPABILITY_CREATED=false
PRODUCTIVE_SCHEMA_CREATED=false
RUNTIME_IMPLEMENTATION_CREATED=false
INTEGRATION_STATUS=NOT_IN_SCOPE
HOST_ADAPTER_STATUS=NOT_DESIGNED
HOST_CONSUMER_STATUS=NONE
AUTHORITY_HANDOFF_STATUS=NOT_DESIGNED
ISOLATION_INVARIANT=HARD_DOMAIN_END
NEW_EDGE_TO_PRODUCTIVE_SYSTEM=false
POLICY_RATIFIED=false
NUMERICS_RATIFIED=false
SSF_SEMANTICS_IMPORTED=false
MF_SCORING_RATIFIED=false
ROTATION_POLICY_RATIFIED=false
MEMBERSHIP_STATE_MACHINE_RATIFIED=false
```

This file persists **already adjudicated** isolated-domain selection and
anti-churn **mechanism semantics** for the graph bounded by
`MF_SELECTION_CONTEXT_BOUNDARY_CONTRACT_V1`.

It does **not** replace §4.5, §4.5.1, §4.5.2, the parent boundary class
`NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY`, or the parent ownership
contract. Ownership of selector consumption and anti-churn remains in
[`MF_SELECTOR_CONSUMPTION_AND_ANTI_CHURN_OWNERSHIP_CONTRACT_V1.md`](MF_SELECTOR_CONSUMPTION_AND_ANTI_CHURN_OWNERSHIP_CONTRACT_V1.md).
This file does **not** re-persist those ownership tables as a second
authority.

Master Runbook SSOT pointer: §4.5 / §4.5.1 / §4.5.2 / §4.5.3.

```text
PURPOSE=PERSIST_ADJUDICATED_ISOLATED_MF_SELECTION_AND_ANTI_CHURN_MECHANISM_SEMANTICS
NOT_PURPOSE=INVENT_POLICY_CLOSE_OPEN_QUESTIONS_IMPORT_SSF_IMPLEMENT_SCORE_ROTATE_AUTHORIZE_OR_JOIN_HOST
EPISTEMIC_CLASS=ADJUDICATED_CONCLUSION_PERSISTED_AS_SUBORDINATE_CONTRACT
```

## 1. Domain boundary

```text
DOMAIN_BOUNDARY=ISOLATED_MF_MEMBERSHIP_CONTEXT_GRAPH
ISOLATED_DOMAIN_ORIGIN=CAP_2_2_TOP20_CANDIDATE_CONTEXT_ONLY
BOUNDARY_CLASS=NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY
ISOLATION_INVARIANT=HARD_DOMAIN_END
INTEGRATION_STATUS=NOT_IN_SCOPE
```

Isolated domain (topology; not a runtime path; not a host join):

```text
TOP20_CANDIDATE_CONTEXT
→ MF_SELECTOR
→ ACTIVE_SET_N
→ MEMBERSHIP_ROTATION
→ NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY
→ HARD DOMAIN END
```

```text
TOP5_VS_ACTIVE_SET_N=NOT_EQUIVALENT
TOP5_STATUS=POSSIBLE_CONFIGURATION_ONLY
ACTIVE_SET_N_STATUS=UNRATIFIED
N_VALUE=UNRESOLVED
N_EQUALS_5=NOT_RATIFIED
SILENCE_IS_NOT_N_EQUALS_5=true
```

`TOP5` is **not** normalized to `ACTIVE_SET_N`. `ACTIVE_SET_N` is **not**
normalized to `TOP5`. A later first ratified configuration **may** use
`N=5`; that remains unratified.

### 1.1 Isolated Active-Set cardinality mode (OPEN_DECISION_02)

Owner-GO
`OWNER_POLICY_CLOSE_MF_OD02_AT_MOST_N_AND_OD03_CONSUME_CAP22_ORDERING_V1`
closes `OPEN_DECISION_02` as `AT_MOST_N`. It does **not** ratify
`N_VALUE`, does **not** import `TOP5`, and does **not** import Cap 2.3
exactly-1.

Prior fail-closed non-inference (neither mode was default; silence did
not select a mode) remains historical provenance from
`OWNER_GO_MF_OPEN_DECISION_02_EXACTLY_N_VS_AT_MOST_N_SEMANTICS_V1`.
That provenance is **not** a second close and does **not** reopen this
decision.

```text
OPEN_DECISION_02=EXACTLY_N_VS_AT_MOST_N
OPEN_DECISION_02_CLOSED=true
CARDINALITY_MODE=AT_MOST_N
N_IS_CEILING_NOT_FILL_TARGET=true
EXACTLY_N_AUTHORITY=NONE
AT_MOST_N_AUTHORITY=OWNER_POLICY_CLOSE
N_VALUE=UNRESOLVED
OPEN_DECISION_01_STATUS=UNRESOLVED
TOP5_VS_ACTIVE_SET_N=NOT_EQUIVALENT
CAP23_EXACTLY1_IMPORTED=false
CAP04_N5_IMPORTED=false
CAP22_TOP20_LIMIT_IS_NOT_ACTIVE_SET_CARDINALITY=true
CANDIDATE_COUNT_VS_N_WHILE_N_UNRESOLVED=NON_OPERATIVE
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=true
EMPTY_SET_POLICY=NON_AUTHORITY
SILENCE_STALE_UNBOUND_POLICY=NON_AUTHORITY
```

Current authority:

| Mode | Current isolated-domain authority | Epistemic class |
|---|---|---|
| `EXACTLY_N` | `NONE` | `CANONICAL_AUTHORITY` that this mode is **not** selected |
| `AT_MOST_N` | `OWNER_POLICY_CLOSE` | `CANONICAL_AUTHORITY` |

`N` is an **upper bound**, not a target or fill cardinality. After a
later `OPEN_DECISION_01` close, `0 < membership_count <= N` from the
same valid candidate context is cardinality-conformant. Until that
numeric close, comparisons against `N` remain `NON_OPERATIVE`.

Negative constraints (must not be violated; not a later fit-target):

```text
TOP5_IS_NOT_ACTIVE_SET_N=true
CAP_2_3_EXACTLY_1_IS_NOT_MF_CARDINALITY_MODE=true
CAP_0_4_N_EQUALS_5_REMINDER_IS_NOT_AUTHORITY=true
CAP_2_2_TOP20_CANDIDATE_CONTEXT_LIMIT_IS_NOT_ACTIVE_SET_CARDINALITY=true
N_EQUALS_5_UNLESS_SEPARATELY_RATIFIED=false
FILL_FROM_UNIVERSE_DASHBOARD_ALLOWLIST_OR_CAP23=FORBIDDEN
EMPTY_SET_IS_NOT_AT_MOST_N_AUTHORIZATION=true
```

Candidate-count cases after this close. The **mode** is `AT_MOST_N`.
Numeric comparison against `N` stays non-operative until OD01.

| Case | Operative? | Bound semantics |
|---|---|---|
| Candidate count &lt; `N` | `NON_OPERATIVE` while `N_VALUE=UNRESOLVED`; underfill **policy** is set | After OD01: underfill from the same valid candidate context may be cardinality-conformant without padding. Does **not** fill from universe, dashboard, allowlist, or Cap 2.3. Does **not** set `N`. |
| Candidate count = `N` | `NON_OPERATIVE` while `N_VALUE=UNRESOLVED` | After OD01: equality is allowed under `AT_MOST_N`. It does **not** prove `EXACTLY_N`. |
| Candidate count &gt; `N` | `NON_OPERATIVE` while `N_VALUE=UNRESOLVED` | Overfill requires the closed membership-order policy in §1.2. Numeric prefix selection remains forbidden until OD01. Does **not** expand `N` to the candidate count. |
| `N` itself unresolved | current numeric state | No candidate-count comparison may authorize a numeric `N`, `N=5`, or `TOP5`. |

Selector silence (absent, stale, unbound, or unratified `N`) must
**not** infer:

```text
SILENCE_IS_NOT_N=true
SILENCE_IS_NOT_N_EQUALS_5=true
SILENCE_IS_NOT_TOP5=true
SILENCE_IS_NOT_EMPTY_SET_AUTHORIZATION=true
SILENCE_IS_NOT_FULL_UNIVERSE_AUTHORIZATION=true
SILENCE_IS_NOT_CAP22_PREFIX_N=true
SILENCE_IS_NOT_CAP23_SELECTION=true
SILENCE_DOES_NOT_REOPEN_EXACTLY_N=true
```

`OPEN_DECISION_01=N_VALUE` remains `UNRESOLVED` and is **not** this
section. This close unblocks OD01 for a **separate** Owner numeric
policy. It does **not** choose that number.

Existing productive system, cited **only** as negative constraint:

```text
Cap 2.2
→ Cap 2.3 SINGLE_SELECTED_FUTURE
→ Cap 2.4
→ Recon / Master V2 / Double Play / Risk / Safety / Intent / Execution
```

Out of this contract:

```text
STRATEGY_SIGNAL_SELECTION=OUT_OF_DOMAIN
MASTER_V2_DOUBLE_PLAY_TRADE_LOGIC=OUT_OF_DOMAIN
INSTRUMENT_BINDING_OUTSIDE_THIS_GRAPH=OUT_OF_DOMAIN
EXECUTION_RISK_SIZING=OUT_OF_DOMAIN
PRODUCTIVE_VENUE_LOGIC=OUT_OF_DOMAIN
CAP23_SINGLE_SELECTED_FUTURE_POLICY=NEGATIVE_CONSTRAINT_ONLY
CAP04_ROTATION_REMINDER=DEFERRED_REQUIRED_CAPABILITY_NOT_RATIFIED_HERE
```

### 1.2 Isolated consume vs own-scoring fork (OPEN_DECISION_03)

Owner-GO
`OWNER_POLICY_CLOSE_MF_OD02_AT_MOST_N_AND_OD03_CONSUME_CAP22_ORDERING_V1`
closes `OPEN_DECISION_03` as
`CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER`. It does **not** create a
second ranker, does **not** ratify an MF scoring contract, and does
**not** invent scores, weights, features, or an MF-own tie-break.

Prior fail-closed non-inference (neither fork was authorized) remains
historical provenance from
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`.
That provenance is **not** a second close and does **not** reopen this
decision.

```text
OPEN_DECISION_03=CONSUME_CAP22_ORDERING_VS_LATER_OWN_MF_SCORING
OPEN_DECISION_03_CLOSED=true
MEMBERSHIP_ORDER_POLICY=CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER
CAP22_MEMBERSHIP_ORDER_AUTHORIZED=true
SECOND_RANKER=FORBIDDEN
MF_RERANKING_ALLOWED=false
OWN_MF_SCORING_CONTRACT=ABSENT
OWN_MF_SCORING_AUTHORITY=NONE
MF_SCORING_CONTRACT_REQUIRED=false
RANKING_RESPONSIBILITY=CAP_2_2_PRODUCER
ORIGIN_TIE_BREAK_OWNER=CAP_2_2
MF_OWN_TIE_BREAK_REQUIRED=false
MF_OWN_TIE_BREAK_KEYS=NOT_AUTHORIZED
MF_SCORING_WEIGHTS_FEATURES=NOT_AUTHORIZED
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=true
```

Proven input identity is Cap 2.2 ordered Top-20 **candidate context**.
Cap 2.2 remains the ranking producer. That existing origin ordering is
now expressly authorized as the isolated selector's **membership
order**. The selector must **not** re-rank.

Current fork authority:

| Fork | Current isolated-domain authority | Epistemic class |
|---|---|---|
| Consume Cap 2.2 ordering as membership order | `OWNER_POLICY_CLOSE` | `CANONICAL_AUTHORITY` |
| Later own MF scoring as membership rank | `ABSENT` / `NOT_REQUIRED` | `CANONICAL_AUTHORITY` that no MF scoring contract is required while this policy holds |

Negative constraints:

```text
CONSUME_ORDER_IS_NOT_A_SECOND_RANKER=true
ABSENT_MF_SCORING_IS_NOT_A_DEFAULT_RANK=true
INVENTION_OF_MF_SCORING_WEIGHTS_OR_FEATURES=FORBIDDEN
INVENTION_OF_MF_OWN_TIE_BREAK_FROM_PLAUSIBILITY=FORBIDDEN
IMPORT_OF_CAP23_TIE_BREAK_AS_MF_POLICY=FORBIDDEN
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=true
```

Prefix-N was forbidden while OD01/OD02/OD03 were open. OD02 and OD03
are now closed; OD01 remains open. Therefore numeric prefix selection
from the Cap-2.2 order remains forbidden until a separate OD01 close.
This close does **not** infer `N`.

### 1.3 Isolated Active-Set `N_VALUE` (OPEN_DECISION_01)

This subsection follows `OPEN_DECISION_02` on purpose. Owner-GO
`OWNER_POLICY_CLOSE_MF_OD02_AT_MOST_N_AND_OD03_CONSUME_CAP22_ORDERING_V1`
unblocks `OPEN_DECISION_01=N_VALUE` for a **separate** Owner numeric
policy because OD02 is now closed as `AT_MOST_N`. It does **not**
ratify a numeric `N`, does **not** import Cap 0.4 `N=5`, and does
**not** equate `TOP5` with `ACTIVE_SET_N`.

```text
OPEN_DECISION_01=N_VALUE
OPEN_DECISION_01_CLOSED=false
N_VALUE=UNRESOLVED
OD01_UNBLOCKED_FOR_OWNER_NUMERIC_POLICY=true
N_VALUE_NOT_DECIDABLE_WHILE_OD02_UNCLOSED=false
NUMERIC_N_AUTHORITY=NONE
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=true
CAP04_N_EQUALS_5_IS_NOT_N_AUTHORITY=true
SILENCE_IS_NOT_N=true
SILENCE_IS_NOT_N_EQUALS_5=true
TOP5_IS_NOT_ACTIVE_SET_N=true
```

After this persist, `N` is policy-decidable as a **ceiling** under
`AT_MOST_N`. This workpackage does **not** choose that ceiling.

### 1.4 Isolated selector state (OPEN_DECISION_04)

Owner-GO
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
persists fail-closed **boundaries** for
`OPEN_DECISION_04=SELECTOR_STATE`. It does **not** close that
decision, does **not** ratify durable selector-owned state, and does
**not** invent a state machine.

```text
OPEN_DECISION_04=SELECTOR_STATE
OPEN_DECISION_04_CLOSED=false
SELECTOR_STATE_OWNER=UNPROVEN
SELECTOR_STATE_NOT_RATIFIED=true
HYGIENE_CONCEPTS_DO_NOT_FORCE_DURABLE_SELECTOR_STATE=true
MEMBERSHIP_STATE_IS_NOT_SELECTOR_OWNED_STATE=true
MEMBERSHIP_STATE_MACHINE_RATIFIED=false
ALLOWED_STATE_TRANSITIONS=UNBOUND
```

Hysteresis and minimum holding remain selector-owned **concepts**, not
ratified rules. Their ownership does **not** prove that the isolated
selector requires durable selector-owned state.

Boundary `membership_state` remains an unbound schema field. It is
**not** selector-owned state and is **not** a ratified membership
state machine.

### 1.5 Isolated membership-only transition-pending (OPEN_DECISION_05)

Owner-GO
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
persists fail-closed **boundaries** for
`OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED`. It does
**not** close that decision as needed or as never-needed.

```text
OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED
OPEN_DECISION_05_CLOSED=false
MEMBERSHIP_ONLY_ANALOG_REQUIRED=UNPROVEN
TRANSITION_PENDING_NODE=OUT_OF_CORE_MODEL
SSF_REPLACEMENT_PENDING_IMPORTED=false
SSF_REPLACEMENT_PENDING_IS_OUT_OF_DOMAIN=true
REPLACEMENT_PENDING_IS_NOT_MEMBERSHIP_ROTATION=true
PENDING_IS_NOT_ANTI_CHURN=true
INVENTION_OF_PENDING_STATE_MACHINE_FROM_PLAUSIBILITY=FORBIDDEN
```

Cap 2.3 `REPLACEMENT_PENDING` remains strictly out of this domain. The
isolated graph has no position semantics. Absence of a membership-only
pending analog is **not** proof that none will later be needed.
Presence of SSF pending is **not** proof that an analog is needed
here. Closing this item as needed remains blocked unless
`OPEN_DECISION_04` and independent isolated-domain evidence later
carry that need.

### 1.6 Isolated rotation identity (OPEN_DECISION_07)

Owner-GO
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
persists fail-closed **boundaries** for
`OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY`. It does
**not** close that identity, does **not** ratify a rotation engine,
and does **not** invent a stage owner.

```text
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
OPEN_DECISION_07_CLOSED=false
ROTATION_ROLE=MEMBERSHIP_DIFF_ONLY
ROTATION_IS_NOT_ANTI_CHURN=true
ROTATION_IS_NOT_PENDING=true
NAMED_GRAPH_NODE_IS_NOT_STAGE_RATIFICATION=true
ROTATION_ENGINE=NOT_AUTHORIZED
ROTATION_POLICY_RATIFIED=false
STAGE_VS_DERIVED=UNRESOLVED
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
```

The named graph node `Membership Rotation` is topology, not a
ratified stage and not a derived-identity close. Rotation remains
membership-diff-only. A derived reading would need a prior membership
listing; that prior is **not** proven here (`membership_state`
unbound; selector state unproven). Silence must **not** infer a
rotation engine, a stage owner, or a derived close.

### 1.7 Isolated persistence while G13 closed (OPEN_DECISION_06)

Owner-GO
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
persists fail-closed **boundaries** for
`OPEN_DECISION_06=CONTEXT_PERSISTENCE_WHILE_G13_CLOSED`. It does
**not** close that decision, does **not** unlock G13, does **not**
create a host join, and does **not** activate runtime.

```text
OPEN_DECISION_06=CONTEXT_PERSISTENCE_WHILE_G13_CLOSED
OPEN_DECISION_06_CLOSED=false
DOC_CONTRACT_PERSISTENCE=PRESENT_AUTHORITY_EFFECT_NONE
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=UNPROVEN
HOST_JOIN=NOT_DESIGNED
G13_UNLOCK=false
RUNTIME_AUTHORITY=NONE
PERSISTENCE_IS_NOT_G13_UNLOCK=true
PERSISTENCE_IS_NOT_HOST_JOIN=true
PERSISTENCE_IS_NOT_RUNTIME_ACTIVATION=true
DOC_CONTRACT_PERSISTENCE_IS_NOT_MEMBERSHIP_ARTIFACT_PERSISTENCE=true
```

Docs-only contract persistence already exists and has
`AUTHORITY_EFFECT=NONE`. That is **not** membership-context artifact
persistence, **not** a producer, and **not** runtime authority.
Whether a non-authoritative membership-context artifact may persist
while G13 remains an `INTENTIONAL_SAFETY_BARRIER` stays `UNPROVEN`.

Fail-closed while this item is open:

```text
DOC_PERSIST_MUST_NOT_BE_READ_AS_ARTIFACT_PERSIST=true
ARTIFACT_PERSIST_MUST_NOT_BE_READ_AS_G13_UNLOCK=true
ARTIFACT_PERSIST_MUST_NOT_BE_READ_AS_HOST_JOIN=true
ARTIFACT_PERSIST_MUST_NOT_BE_READ_AS_RUNTIME_AUTHORITY=true
```

### 1.8 Cross-decision DAG (semantic; not a runtime path)

This subsection records the **semantic** dependency order among the
seven open decisions. It is **not** a runtime path, **not** a host
join, and **not** a close of any decision.

```text
DECISION_DAG_CLASS=SEMANTIC_DEPENDENCY_NOT_RUNTIME
CLOSED_DECISIONS=OPEN_DECISION_02,OPEN_DECISION_03
```

```text
TOP20_CANDIDATE_CONTEXT
→ CAP22_ORDER_CONSUMED_AS_MEMBERSHIP_ORDER
→ MF_SELECTOR
→ AT_MOST_N
→ OD01_N_VALUE_UNRESOLVED
→ ACTIVE_SET_N
→ OD07_UNRESOLVED
→ MEMBERSHIP_ROTATION
→ NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY
→ HARD DOMAIN END
```

```text
OPEN_DECISION_04
→ OPEN_DECISION_05
```

```text
OPEN_DECISION_06=INDEPENDENT_OF_HOST_JOIN
OPEN_DECISION_06_DOES_NOT_UNLOCK_G13=true
```

Current dispositions (this workpackage; not a later close of remaining
nodes):

| Decision | Disposition | Closed |
|---|---|---|
| `OPEN_DECISION_03` | `CLOSED_CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER` | `true` |
| `OPEN_DECISION_02` | `CLOSED_AT_MOST_N` | `true` |
| `OPEN_DECISION_01` | `UNBLOCKED_FOR_OWNER_NUMERIC_POLICY` / parameter | `false` |
| `OPEN_DECISION_04` | `UNRESOLVED_BUT_BOUNDARIES_SHARPENED` | `false` |
| `OPEN_DECISION_05` | `UNRESOLVED_BUT_BOUNDARIES_SHARPENED` / `INSUFFICIENT_EVIDENCE` to close needed vs never-needed | `false` |
| `OPEN_DECISION_07` | `UNRESOLVED_BUT_BOUNDARIES_SHARPENED` | `false` |
| `OPEN_DECISION_06` | `UNRESOLVED_BUT_BOUNDARIES_SHARPENED` | `false` |

A later close of one node does **not** close a neighbor by inference.
This persist does **not** close `OPEN_DECISION_04`–`07` and does
**not** choose `N`.

## 2. Owner by mechanism

Owners below are **cited from** the parent ownership contract. This file
does **not** re-own them.

| Mechanism | Owner (from parent ownership contract) | Epistemic class |
|---|---|---|
| Cap 2.2 origin ordering / origin tie-break | Cap 2.2 ranking producer (outside isolated selector) | `CANONICAL_AUTHORITY` at Cap 2.2; consumed as membership order after OD03 close |
| MF-own tie-break | `NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY` | `ADJUDICATED_CONCLUSION` of OD03 close |
| Hysteresis | `SELECTOR` | `ADJUDICATED_CONCLUSION` of ownership; this file adds concept-vs-rule semantics only |
| Minimum holding | `SELECTOR` | `ADJUDICATED_CONCLUSION` of ownership; this file adds concept-vs-rule semantics only |
| Cooldown / turnover | `SELECTOR` concept-family; unratified | `UNRESOLVED` as a ratified mechanism |
| Cap 2.3 `REPLACEMENT_PENDING` | Cap 2.3; **not imported** | `CANONICAL_AUTHORITY` of Cap 2.3; `OUT_OF_DOMAIN` here |
| Membership-only transition-pending | `UNRESOLVED`; node `OUT_OF_CORE_MODEL` | `UNRESOLVED` |
| Rotation | membership-diff-only; **not** anti-churn owner | `ADJUDICATED_CONCLUSION` |
| Freshness / fail-closed integrity | `BOUNDARY` | `ADJUDICATED_CONCLUSION` of ownership |

```text
OWNER_BY_MECHANISM_AUTHORITY=PARENT_OWNERSHIP_CONTRACT
ANTI_CHURN_OWNER=SELECTOR
ROTATION_IS_NOT_ANTI_CHURN_OWNER=true
SELECTOR_CARDINALITY_OWNER=ACTIVE_SET
```

## 3. Inputs

```text
SELECTOR_CONSUMES=CAP_2_2_TOP20_ORDERED_CANDIDATE_CONTEXT
TOP20_ROLE=CANDIDATE_CONTEXT_ONLY
INPUT_IS_NOT_SELECTION_AUTHORITY=true
INPUT_IS_NOT_HOST_INPUT=true
MF_SCORING_INPUT=ABSENT
N_INPUT=UNRATIFIED
SELECTOR_STATE_INPUT=UNPROVEN
SSF_SELECTION_SNAPSHOT_INPUT=FORBIDDEN
DASHBOARD_ALLOWLIST_MANUAL_OVERRIDE_INPUT=FORBIDDEN
```

Cap 2.2 already produces a deterministic ordered Top-20 candidate
context. That ordered listing is the **only** proven input identity for
the isolated selector. Owner-GO
`OWNER_POLICY_CLOSE_MF_OD02_AT_MOST_N_AND_OD03_CONSUME_CAP22_ORDERING_V1`
authorizes consuming that origin order as membership order. This
contract still does **not** authorize a second ranking input.

## 4. Outputs

```text
SELECTOR_OUTPUT=NON_AUTHORITATIVE_MEMBERSHIP_PROPOSAL_CONSTRAINED_BY_ACTIVE_SET_N
ANTI_CHURN_OUTPUT=ADMISSION_OR_NON_ADMISSION_OF_A_PROPOSED_MEMBERSHIP_CHANGE
ROTATION_OUTPUT=MEMBERSHIP_CHANGE_ONLY_DIFF
BOUNDARY_OUTPUT=NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY
TERMINUS=HARD_DOMAIN_END
OUTPUT_IS_NOT_SELECTION=true
OUTPUT_IS_NOT_ALPHA=true
OUTPUT_IS_NOT_MULTI_FUTURE_RUNTIME=true
OUTPUT_IS_NOT_HOST_INPUT=true
OUTPUT_IS_NOT_POSITION_ROTATION=true
```

Anti-churn is **not** a graph node. It is selector-side admission of a
proposed membership change. Rotation remains membership-diff-only.
Whether `rotation_deltas` is a stage versus a derived identity remains
`OPEN_DECISION_07` / `UNRESOLVED`.

## 5. Allowed state transitions

```text
ALLOWED_STATE_TRANSITIONS=UNBOUND
MEMBERSHIP_STATE_MACHINE_RATIFIED=false
SSF_SELECTION_STATES_NOT_IMPORTED=true
TRANSITION_PENDING_NODE=OUT_OF_CORE_MODEL
MEMBERSHIP_ONLY_ANALOG_REQUIRED=UNPROVEN
OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED
```

No isolated-domain membership state machine is ratified. Cap 2.3 states
`SELECTED_ACTIVE | SELECTED_DEGRADED | SELECTED_EXIT_ONLY |
REPLACEMENT_PENDING | NO_SELECTION` are **not** imported.

Forbidden equivalences (adjudicated; not a state machine):

```text
REPLACEMENT_PENDING_IS_NOT_MEMBERSHIP_ROTATION=true
HYSTERESIS_IS_NOT_MEMBERSHIP_ROTATION=true
MIN_HOLDING_IS_NOT_MEMBERSHIP_ROTATION=true
TIE_BREAK_IS_NOT_MEMBERSHIP_ROTATION=true
MIN_HOLDING_IS_NOT_POSITION_HOLDING=true
ANTI_CHURN_IS_NOT_A_GRAPH_NODE=true
```

## 6. Tie-break semantics

```text
TIE_BREAK_SEMANTICS=CAP22_ORIGIN_CONSUMED_AS_MEMBERSHIP_ORDER
TIE_BREAK_PROVEN_ORIGIN=CAP_2_2_TOP20_ORDERING
TIE_BREAK_CORE_OWNER=CAP_2_2_ORIGIN_WHILE_CONSUME_POLICY
MF_OWN_TIE_BREAK_OWNER=NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY
MF_OWN_TIE_BREAK_REQUIRED=false
SELECTOR_MUST_NOT_DERIVE_RE_RANKING_FROM_THIS_PERSIST=true
MF_RERANKING_ALLOWED=false
MF_TIE_BREAK_ALGORITHM=NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY
MF_TIE_BREAK_NUMERICS=NOT_AUTHORIZED
```

Epistemic split:

| Claim | Class |
|---|---|
| Cap 2.2 ranking applies a deterministic tie-break when producing Top-20 candidate context | `CANONICAL_AUTHORITY` of Cap 2.2; `FORENSIC_FACT` as input property of this graph |
| Cap 2.2 evidence records origin `tie_break_order` as `total_score_desc`, `venue_native_id_asc`, `canonical_instrument_id_asc` | `FORENSIC_FACT` of Cap 2.2 ranking identity; **not** MF selector policy |
| Isolated selector must not derive a second ranking from this persist | `ADJUDICATED_CONCLUSION` |
| Selector consumes Cap 2.2 ordering as membership order | `CANONICAL_AUTHORITY` (`OPEN_DECISION_03` closed) |
| An MF-own tie-break algorithm, key order, or numeric rule | `NOT_REQUIRED` while consume-Cap-2.2-order policy holds; still `NOT_AUTHORIZED` to invent |
| Cap 2.3 `tie_break_order` (`ranking_rank_asc`, then ids) | `HISTORICAL_STATE` / Cap-2.3 `CANONICAL_AUTHORITY`; **not imported** |

Fail-closed for this mechanism:

```text
ABSENT_OR_AMBIGUOUS_ORDERING=FAIL_CLOSED_NON_AUTHORITY
ABSENT_ORDERING_IS_NOT_MEMBERSHIP_AUTHORIZATION=true
INVENTION_OF_MF_TIE_BREAK_ALGORITHM_FROM_PLAUSIBILITY=FORBIDDEN
IMPORT_OF_CAP23_TIE_BREAK_AS_MF_POLICY=FORBIDDEN
IMPORT_OF_RESEARCH_OR_STRATEGY_TIE_BREAK=FORBIDDEN
```

Deterministic / fail-closed **can** be required as a later ratification
constraint. It **cannot** be specified as an MF selector algorithm in
this persist. If a later own MF scoring contract is ratified, that
contract must itself define a deterministic fail-closed tie-break; this
file does not pre-write it.

## 7. Hysteresis semantics

```text
HYSTERESIS_SEMANTICS=SELECTOR_OWNED_CONCEPT_NOT_RATIFIED_RULE
HYSTERESIS_CORE_OWNER=SELECTOR
HYSTERESIS_ROLE=MEMBERSHIP_STICKINESS_AND_ADMISSION_OF_A_PROPOSED_CHANGE
HYSTERESIS_IS_RATIFIED_RULE=false
HYSTERESIS_NUMERICS_RATIFIED=false
SSF_HYSTERESIS_IMPORTED=false
REUSE_STATUS=PARTIAL
```

Hysteresis is part of the isolated MF selection universe as a **concept**
located at the selector. It may affect admission of a proposed
membership change and thereby suppress churn. It does **not** own
rotation. It is **not** a replacement state.

It is **not** a ratified rule. No MF-domain threshold, rank-improvement,
dead-band, confirmation count, or duration is canonical.

Cap 2.3 `hysteresis_rank_improvement` is Cap-2.3 policy and is **not**
imported. Cap 0.4 lists hysteresis as an open policy decision for later
ratification; that reminder is **not** this domain's numeric authority.
Master-V2 / Double-Play / strategy switch-gate hysteresis is
`OUT_OF_DOMAIN`.

## 8. Minimum-holding semantics

```text
MIN_HOLDING_SEMANTICS=SELECTOR_OWNED_CONCEPT_NOT_RATIFIED_RULE
MINIMUM_HOLDING_CORE_OWNER=SELECTOR
MINIMUM_HOLDING_ROLE=MEMBERSHIP_TENURE_BEFORE_PROPOSED_DROP_OR_REPLACE
MINIMUM_HOLDING_IS_RATIFIED_RULE=false
MINIMUM_HOLDING_NUMERICS_RATIFIED=false
MINIMUM_HOLDING_IS_NOT_POSITION_HOLDING=true
SSF_MIN_HOLDING_IMPORTED=false
REUSE_STATUS=PARTIAL
```

Minimum holding is part of the isolated MF selection universe as a
**concept** located at the selector. It may delay a proposed drop or
replace until membership tenure exists, and thereby suppress churn. It
does **not** own rotation. It is **not** a replacement state. It is
**not** position holding, order holding, or paper-shadow hold-binding.

It is **not** a ratified rule. No MF-domain duration, bar count, or
residence threshold is canonical.

Cap 2.3 `min_holding_period_seconds` is Cap-2.3 policy and is **not**
imported. Cap 0.4 lists minimum active/candidate duration as an open
policy decision; that reminder is **not** this domain's numeric
authority.

## 9. Replacement-pending semantics

```text
REPLACEMENT_PENDING_SEMANTICS=SSF_STATE_NOT_IMPORTED_MEMBERSHIP_ANALOG_UNPROVEN
CAP23_REPLACEMENT_PENDING_IMPORTED=false
SSF_REPLACEMENT_STATE_MACHINE_IMPORTED=false
TRANSITION_PENDING_CORE_OWNER=UNRESOLVED
TRANSITION_PENDING_NODE=OUT_OF_CORE_MODEL
MEMBERSHIP_ONLY_ANALOG_REQUIRED=UNPROVEN
REPLACEMENT_PENDING_IS_NOT_MEMBERSHIP_ROTATION=true
```

Cap 2.3 `REPLACEMENT_PENDING` is a **productive single-selection state**
used while an open position exists: no silent instrument switch; no
alpha for a replacement instrument; replacement persisted only as that
state. That state machine is **outside** this isolated graph.

A membership-only analog is **not** proven necessary and is **not** a
core-model node. This persist does **not** invent one.

Adjudicated non-equivalence:

```text
REPLACEMENT_PENDING_IS_NOT_ROTATION=true
ROTATION_IS_MEMBERSHIP_DIFF_ONLY=true
A_PENDING_REPLACEMENT_STATE_IS_DEFERRAL_NOT_DIFF=true
```

Even if a later Owner-GO ratifies a membership-only pending analog, that
analog would still not **be** rotation. Rotation emits membership-change
differences. A pending state would hold or defer a change. Those are
distinct semantic identities.

## 10. Rotation relation

```text
ROTATION_RELATION=MEMBERSHIP_DIFF_AFTER_SELECTOR_ADMISSION_NOT_ANTI_CHURN_OWNER
ROTATION_ROLE=MEMBERSHIP_DIFF_ONLY
ROTATION_IS_MEMBERSHIP_ONLY=true
ROTATION_IS_NOT_ANTI_CHURN_OWNER=true
ROTATION_POLICY_RATIFIED=false
ROTATION_NUMERICS_RATIFIED=false
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
```

| Mechanism | Influences membership proposal | Allows/prevents rotation | Suppresses churn only | Is a replacement state |
|---|---|---|---|---|
| Origin tie-break (Cap 2.2) | Orders the candidate context; after OD03 close this order is the membership order; does not itself admit membership | No | No | No |
| MF-own tie-break | `NOT_REQUIRED` while consume-Cap-2.2-order policy holds | No | No | No |
| Hysteresis | Yes, as admission/non-admission of a proposed change (**concept**) | May prevent a diff from being admitted; does **not** own rotation | Yes, as concept | No |
| Minimum holding | Yes, as tenure before proposed drop/replace (**concept**) | May prevent a diff from being admitted; does **not** own rotation | Yes, as concept | No |
| Cap 2.3 `REPLACEMENT_PENDING` | Out of domain | Out of domain | Out of domain | Cap 2.3 only; not imported |
| Membership-only pending analog | `UNPROVEN` | `UNPROVEN`; would still not **be** rotation | `UNPROVEN` | `UNPROVEN` / not core model |

Cap 0.4 `MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0` remains
`DEFERRED_REQUIRED_CAPABILITY`. This contract does **not** consume that
reminder and does **not** ratify rotation or anti-churn numerics.

## 11. Fail-closed behavior

```text
FAIL_CLOSED_BEHAVIOR=ABSENT_STALE_UNBOUND_AMBIGUOUS_MUST_NOT_AUTHORIZE
ABSENT_CONTEXT=NOT_EMPTY_SET_AUTHORIZATION
ABSENT_CONTEXT=NOT_FULL_UNIVERSE_AUTHORIZATION
ABSENT_CONTEXT=NOT_CAP23_SELECTION
ABSENT_CONTEXT=NOT_CAP24_INPUT
ABSENT_CONTEXT=NOT_HOST_INPUT
PRESENT_CONTEXT=NOT_SELECTION
PRESENT_CONTEXT=NOT_ALPHA
PRESENT_CONTEXT=NOT_MULTI_FUTURE_RUNTIME
PRESENT_CONTEXT=NOT_G13_UNLOCK
PRESENT_CONTEXT=NOT_HOST_INPUT
STALE_OR_UNBOUND_CONTEXT=FAIL_CLOSED_NON_AUTHORITY
ABSENT_OR_AMBIGUOUS_ORDERING=FAIL_CLOSED_NON_AUTHORITY
UNRATIFIED_HYSTERESIS_OR_MIN_HOLDING_NUMERICS=NOT_A_DEFAULT
UNPROVEN_PENDING_ANALOG=NOT_A_STATE_MACHINE
OVERREAD_AS_SELECTION_OR_RUNTIME=FORBIDDEN
OVERREAD_AS_FUTURE_HOST_INPUT=FORBIDDEN
OVERREAD_AS_N_EQUALS_5=FORBIDDEN
OVERREAD_AS_EXACTLY_N=FORBIDDEN
OVERREAD_AS_AT_MOST_N_EQUALS_EMPTY_SET=FORBIDDEN
OVERREAD_AS_SSF_STATE_MACHINE=FORBIDDEN
OVERREAD_AS_ROTATION_POLICY=FORBIDDEN
OVERREAD_AS_TOP5_EQUALS_ACTIVE_SET_N=FORBIDDEN
OVERREAD_AS_CAP22_TOP20_LIMIT_AS_ACTIVE_SET_N=FORBIDDEN
OVERREAD_AS_CAP23_EXACTLY1_AS_MF_CARDINALITY_MODE=FORBIDDEN
OVERREAD_AS_SECOND_RANKER=FORBIDDEN
OVERREAD_AS_OWN_MF_SCORING=FORBIDDEN
OVERREAD_AS_MF_OWN_TIE_BREAK_ALGORITHM=FORBIDDEN
OVERREAD_AS_NUMERIC_PREFIX_UNTIL_OD01=FORBIDDEN
OVERREAD_AS_N_VALUE=FORBIDDEN
OVERREAD_AS_DURABLE_SELECTOR_STATE=FORBIDDEN
OVERREAD_AS_MEMBERSHIP_STATE_EQUALS_SELECTOR_STATE=FORBIDDEN
OVERREAD_AS_PENDING_ANALOG_NEEDED=FORBIDDEN
OVERREAD_AS_PENDING_ANALOG_NEVER_NEEDED=FORBIDDEN
OVERREAD_AS_ROTATION_STAGE_RATIFICATION=FORBIDDEN
OVERREAD_AS_ROTATION_DERIVED_CLOSE=FORBIDDEN
OVERREAD_AS_ROTATION_ENGINE=FORBIDDEN
OVERREAD_AS_DOC_PERSIST_EQUALS_ARTIFACT_PERSIST=FORBIDDEN
OVERREAD_AS_PERSISTENCE_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_PERSISTENCE_EQUALS_HOST_JOIN=FORBIDDEN
INVENTION_OF_THRESHOLDS_FROM_PLAUSIBILITY=FORBIDDEN
CANDIDATE_COUNT_VS_UNRESOLVED_N=FAIL_CLOSED_NON_AUTHORITY
UNDERFILL_DOES_NOT_PAD=true
UNDERFILL_DOES_NOT_SET_N=true
UNDERFILL_DOES_NOT_AUTHORIZE_EMPTY_SET=true
EXACT_FILL_DOES_NOT_PROVE_EXACTLY_N=true
OVERFILL_DOES_NOT_AUTHORIZE_N_EXPANSION=true
OVERFILL_NUMERIC_CUT_BLOCKED_UNTIL_OD01=true
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=true
```

## 12. Unresolved parameters

No isolated-domain numeric, duration, rank delta, confirmation count,
cooldown, turnover bound, or tie-break key-order for an MF-own scoring
contract is canonical.

```text
UNRESOLVED_PARAMETERS=ALL_MF_DOMAIN_NUMERICS_AND_ALGORITHMS_BELOW
N_VALUE=UNRESOLVED
EXACTLY_N_VS_AT_MOST_N=CLOSED_AT_MOST_N
CARDINALITY_MODE=AT_MOST_N
MF_TIE_BREAK_ALGORITHM=NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY
MF_TIE_BREAK_KEY_ORDER=NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY
HYSTERESIS_THRESHOLD=UNRESOLVED
HYSTERESIS_RANK_IMPROVEMENT=UNRESOLVED
HYSTERESIS_DEAD_BAND=UNRESOLVED
HYSTERESIS_CONFIRMATION_COUNT=UNRESOLVED
MIN_HOLDING_DURATION=UNRESOLVED
MIN_HOLDING_BARS=UNRESOLVED
MIN_ACTIVE_DURATION=UNRESOLVED
MIN_CANDIDATE_DURATION=UNRESOLVED
COOLDOWN=UNRESOLVED
TURNOVER_BOUND=UNRESOLVED
REPLACEMENT_MARGIN=UNRESOLVED
MEMBERSHIP_ONLY_PENDING_STATE_MACHINE=UNRESOLVED
```

Cap 2.3 evidence values such as `hysteresis_rank_improvement=1` and
`min_holding_period_seconds=3600.0` remain Cap-2.3
`CANONICAL_AUTHORITY` / `HISTORICAL_STATE` for single-selected-future
policy. Citing them here is **negative constraint** only:
`SSF_SEMANTICS_IMPORTED=false`.

Open decisions remaining after this Owner-policy close. Fail-closed
**boundaries** for still-open items remain in §1.3–§1.7. OD02 and OD03
are closed in §1.1–§1.2.

```text
OPEN_DECISION_01=N_VALUE
OPEN_DECISION_01_CLOSED=false
OD01_UNBLOCKED_FOR_OWNER_NUMERIC_POLICY=true
OPEN_DECISION_02=EXACTLY_N_VS_AT_MOST_N
OPEN_DECISION_02_CLOSED=true
CARDINALITY_MODE=AT_MOST_N
OPEN_DECISION_03=CONSUME_CAP22_ORDERING_VS_LATER_OWN_MF_SCORING
OPEN_DECISION_03_CLOSED=true
MEMBERSHIP_ORDER_POLICY=CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER
OPEN_DECISION_04=SELECTOR_STATE
OPEN_DECISION_04_CLOSED=false
OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED
OPEN_DECISION_05_CLOSED=false
OPEN_DECISION_06=CONTEXT_PERSISTENCE_WHILE_G13_CLOSED
OPEN_DECISION_06_CLOSED=false
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
OPEN_DECISION_07_CLOSED=false
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=true
MF_OWN_TIE_BREAK_REQUIRED=false
```

## 13. Forensic census (bound; not a second SSOT)

| Mechanism | Current authority | Existing contract | Historical evidence | Current runtime existence | Unresolved |
|---|---|---|---|---|---|
| Tie-break | Cap 2.2 origin ordering is membership order after OD03 close; MF-own not required while consume policy holds | Ownership §5.1; this file §6 | Cap 2.2 ranking evidence `tie_break_order`; Cap 2.3 different order **not imported**; research/strategy tie-breaks `OUT_OF_DOMAIN` | Isolated MF selector unimplemented; Cap 2.2 producer exists as TOP20 origin | Numeric `N` (`OPEN_DECISION_01`); hygiene numerics |
| Hysteresis | Ownership locates concept at selector; no MF rule authority | Ownership §5.2; this file §7 | Cap 2.3 SSF hysteresis **not imported**; Cap 0.4 open decision; MV2/strategy hysteresis `OUT_OF_DOMAIN` | Isolated MF selector unimplemented | All numerics; concept-vs-rule remains concept |
| Min holding | Ownership locates concept at selector; no MF rule authority | Ownership §5.3; this file §8 | Cap 2.3 SSF min holding **not imported**; Cap 0.4 open decision | Isolated MF selector unimplemented | All numerics; residence duration unbound |
| Replacement-pending | Cap 2.3 only; **not** MF authority | Ownership §5.5 forbids SSF import; this file §9 | Cap 2.3 `REPLACEMENT_PENDING` state machine | Cap 2.3 producer exists **outside** this graph; no MF pending runtime | Whether a membership-only analog is needed (`OPEN_DECISION_05`) |

```text
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MF_SELECTOR=false
CURRENT_RUNTIME_EXISTENCE_ISOLATED_ANTI_CHURN=false
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MEMBERSHIP_ROTATION_POLICY=false
HISTORICAL_EXISTENCE_IS_NOT_TODAYS_MF_AUTHORITY=true
```

## 14. Authority effect

```text
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
CONTEXT_ONLY=true
SELECTION_AUTHORITY=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
G13_UNLOCK=false
NEW_RUNTIME_POLICY=false
NEW_EDGE_TO_PRODUCTIVE_SYSTEM=false
```

Presence of this contract does **not** authorize multi-future runtime,
alpha, G13 unlock, productive-host consumption, scoring, `N`, or
hygiene numerics.

## 15. Governance / Atlas

```text
MASTER_RUNBOOK_AUTHORITY=SSOT
SUBORDINATE_CONTRACT=THIS_FILE
PARENT_BOUNDARY_REMAINS=MF_SELECTION_CONTEXT_BOUNDARY_CONTRACT_V1
PARENT_OWNERSHIP_REMAINS=MF_SELECTOR_CONSUMPTION_AND_ANTI_CHURN_OWNERSHIP_CONTRACT_V1
MAP_OF_TRUTH_ROLE=NAVIGATION_ONLY
ATLAS_AUTHORITY=NONE
ATLAS_ROLE=NAVIGATION_INDEX_ONLY
ATLAS_MUST_NOT_CREATE_AUTHORITY=true
NO_NEW_PRODUCTIVE_OWNER_FROM_ATLAS=true
NO_ATLAS_EDGE_TO_CAP23_OR_CAP24=true
```

## 16. Hard stop

```text
RUNTIME_IMPLEMENTATION_CREATED=false
SRC_PATHS_CHANGED_BY_THIS_CONTRACT=false
CAP23_REWIRED=false
CAP24_REWIRED=false
G13_UNLOCK=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
INTEGRATION_STATUS=NOT_IN_SCOPE
HOST_ADAPTER_STATUS=NOT_DESIGNED
HOST_CONSUMER_STATUS=NONE
AUTHORITY_HANDOFF_STATUS=NOT_DESIGNED
NEXT_IMPLEMENTATION_AUTHORIZED=false
NEXT_SLICE_AUTHORIZED=false
HARD_STOP_AFTER_THIS_CONTRACT=true
```

Any later `N` value, selector state, hygiene numerics, membership-only
pending-state, own MF scoring, or persistence while G13 closed requires
a **new** Owner-GO and remains isolated. This contract does **not**
authorize, specify, or prepare host integration.
