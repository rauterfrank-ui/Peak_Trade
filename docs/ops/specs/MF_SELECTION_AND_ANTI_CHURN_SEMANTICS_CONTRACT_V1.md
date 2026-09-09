---
docs_token: DOCS_TOKEN_MF_SELECTION_AND_ANTI_CHURN_SEMANTICS_CONTRACT_V1
status: active
scope: Docs-only persist of adjudicated isolated MF selection and anti-churn mechanism semantics; OD01 closed as Owner-policy ceiling N=5 under AT_MOST_N; OD06 closed as ALLOW permission for non-authoritative membership-context artifact persistence while G13 remains closed; permission is not artifact existence; membership-context artifact semantic identity bound as information classes only; artifact existence class bound as required durable non-authoritative membership-context artifact; instance existence unproven; instance-existence decision class persisted as NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED; UNPROVEN is not ABSENT; creation not authorized; no schema, writer, reader, or artifact instance; no host adapter; no Cap-2.3/2.4 join; hygiene numerics unratified; OD07 unclosed
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
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY_V1
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_EXISTENCE_CLASS=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_EXISTENCE_CLASS_V1
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_INSTANCE_EXISTENCE_CENSUS_PERSIST=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_INSTANCE_EXISTENCE_CENSUS_PERSIST_V1
BOUND_ORIGIN_MAIN_SHA=a430bd3837a833d56a8029d3c0d5e8c5380708a1
BOUND_ORIGIN_MAIN_SHA_THIS_IDENTITY_SLICE=c58d8c5a8a7268af74c989aa0fb166f8f6df40b1
BOUND_ORIGIN_MAIN_SHA_THIS_EXISTENCE_CLASS_SLICE=b364d1a26d927eeb5d143028afd687f6d3183042
BOUND_ORIGIN_MAIN_SHA_THIS_INSTANCE_CENSUS_SLICE=81bd848c7054f2dafe1965b899b79ca809d4c278
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
N_VALUE=5
N_CEILING_RATIFIED=true
SSF_SEMANTICS_IMPORTED=false
MF_SCORING_RATIFIED=false
ROTATION_POLICY_RATIFIED=false
MEMBERSHIP_STATE_MACHINE_RATIFIED=false
MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY=BOUND_INFORMATION_CLASSES_ONLY
ARTIFACT_EXISTENCE_CLASS=BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
CREATION_AUTHORIZED=false
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=UNPROVEN
INSTANCE_IDENTITY_STATUS=UNBOUND
TEMPORAL_IDENTITY_STATUS=UNBOUND
PRIOR_REFERENCE_STATUS=UNBOUND
CAP22_PROVENANCE_STATUS=UNBOUND
PRIOR_MEMBERSHIP_LISTING_STATUS=UNPROVEN
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
TEMPORAL_SCHEMA=UNBOUND
INSTANCE_ID_SCHEMA=UNBOUND
PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=UNBOUND
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
ROTATION_DELTAS_STATUS=UNRESOLVED
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
OD07_STATUS=UNCLOSED
OPEN_DECISION_07_CLOSED=false
```

This file persists **already adjudicated** isolated-domain selection and
anti-churn **mechanism semantics** for the graph bounded by
`MF_SELECTION_CONTEXT_BOUNDARY_CONTRACT_V1`.

It does **not** replace §4.5, §4.5.1, §4.5.2, the parent boundary class
`NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY`, or the parent ownership
contract. Ownership of selector consumption and anti-churn remains in
[`MF_SELECTOR_CONSUMPTION_AND_ANTI_CHURN_OWNERSHIP_CONTRACT_V1.md`](MF_SELECTOR_CONSUMPTION_AND_ANTI_CHURN_OWNERSHIP_CONTRACT_V1.md).
This file does **not** re-persist those ownership tables as a second
authority. Isolated ranking-universe family isolation and the
single-egress **invariant** are persisted in
[`MF_RANKING_UNIVERSE_AND_SINGLE_EGRESS_BOUNDARY_CONTRACT_V1.md`](MF_RANKING_UNIVERSE_AND_SINGLE_EGRESS_BOUNDARY_CONTRACT_V1.md).
This file does **not** replace that boundary.

Master Runbook SSOT pointer: §4.5 / §4.5.1 / §4.5.2 / §4.5.3 / §4.5.4.

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
ACTIVE_SET_N_STATUS=CEILING_N5_OWNER_POLICY
N_VALUE=5
N_EQUALS_5=OWNER_POLICY_CEILING_NOT_EXACTLY_5
SILENCE_IS_NOT_N_EQUALS_5=true
TOP5_PRODUCT_CREATED=false
```

`TOP5` is **not** normalized to `ACTIVE_SET_N`. `ACTIVE_SET_N` is **not**
normalized to `TOP5`. Owner-GO
`OWNER_GO_MF_OD01_CLOSE_NUMERIC_CEILING_N5_V1` closes `N_VALUE=5` as an
`AT_MOST_N` ceiling in §1.3. That close does **not** create a `TOP5`
product.

### 1.1 Isolated Active-Set cardinality mode (OPEN_DECISION_02)

Owner-GO
`OWNER_POLICY_CLOSE_MF_OD02_AT_MOST_N_AND_OD03_CONSUME_CAP22_ORDERING_V1`
closes `OPEN_DECISION_02` as `AT_MOST_N`. It does **not** itself ratify
`N_VALUE`. Numeric ceiling `N_VALUE=5` is closed separately in §1.3.
This section does **not** import `TOP5` and does **not** import Cap 2.3
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
N_VALUE=5
OPEN_DECISION_01_STATUS=CLOSED_NUMERIC_CEILING_N5
TOP5_VS_ACTIVE_SET_N=NOT_EQUIVALENT
CAP23_EXACTLY1_IMPORTED=false
CAP04_N5_IMPORTED=false
CAP22_TOP20_LIMIT_IS_NOT_ACTIVE_SET_CARDINALITY=true
CANDIDATE_COUNT_VS_N_WHILE_N_UNRESOLVED=OPERATIVE_AFTER_OD01_CLOSE
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=false
EMPTY_SET_POLICY=NON_AUTHORITY
SILENCE_STALE_UNBOUND_POLICY=NON_AUTHORITY
```

Current authority:

| Mode | Current isolated-domain authority | Epistemic class |
|---|---|---|
| `EXACTLY_N` | `NONE` | `CANONICAL_AUTHORITY` that this mode is **not** selected |
| `AT_MOST_N` | `OWNER_POLICY_CLOSE` | `CANONICAL_AUTHORITY` |

`N` is an **upper bound**, not a target or fill cardinality. After the
§1.3 OD01 close, `0 < membership_count <= 5` from the same valid
candidate context is cardinality-conformant. Comparisons against `N`
are **operative**. This section does **not** own that numeric close.

Negative constraints (must not be violated; not a later fit-target):

```text
TOP5_IS_NOT_ACTIVE_SET_N=true
CAP_2_3_EXACTLY_1_IS_NOT_MF_CARDINALITY_MODE=true
CAP_0_4_N_EQUALS_5_REMINDER_IS_NOT_AUTHORITY=true
CAP_2_2_TOP20_CANDIDATE_CONTEXT_LIMIT_IS_NOT_ACTIVE_SET_CARDINALITY=true
N_EQUALS_5_IS_CEILING_NOT_EXACTLY_5=true
FILL_FROM_UNIVERSE_DASHBOARD_ALLOWLIST_OR_CAP23=FORBIDDEN
EMPTY_SET_IS_NOT_AT_MOST_N_AUTHORIZATION=true
NO_PADDING=true
```

Candidate-count cases after the §1.3 OD01 close. The **mode** is
`AT_MOST_N`. `N_VALUE=5`. Numeric comparison against `N` is operative.

| Case | Operative? | Bound semantics |
|---|---|---|
| Candidate count &lt; `N` | `OPERATIVE` | Underfill from the same valid candidate context may be cardinality-conformant without padding. Does **not** fill from universe, dashboard, allowlist, or Cap 2.3. Does **not** expand `N`. Does **not** authorize an empty set. |
| Candidate count = `N` | `OPERATIVE` | Equality is allowed under `AT_MOST_N`. It does **not** prove `EXACTLY_N` or `EXACTLY_5`. |
| Candidate count &gt; `N` | `OPERATIVE` | Overfill is cut by consuming Cap-2.2 membership order as a numeric prefix of at most 5. That prefix is **not** a second ranker and is **not** a `TOP5` product. Does **not** expand `N` to the candidate count. |

Selector silence (absent, stale, or unbound context) must **not** infer:

```text
SILENCE_IS_NOT_N=true
SILENCE_IS_NOT_MEMBERSHIP_OF_FIVE=true
SILENCE_IS_NOT_TOP5=true
SILENCE_IS_NOT_EMPTY_SET_AUTHORIZATION=true
SILENCE_IS_NOT_FULL_UNIVERSE_AUTHORIZATION=true
SILENCE_IS_NOT_CAP23_SELECTION=true
SILENCE_DOES_NOT_REOPEN_EXACTLY_N=true
```

`OPEN_DECISION_01=N_VALUE` is closed in §1.3 as Owner-policy ceiling
`N=5`. This OD02 section does **not** re-close that decision.

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
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=false
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
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=false
```

Prefix-N from the Cap-2.2 membership order is the overfill cut under
`AT_MOST_N` after the §1.3 OD01 close (`N_VALUE=5`). It is **not** a
second ranker, **not** a `TOP5` product, and **not** an `N`
inference from silence. This OD03 close does **not** itself set `N`.

### 1.3 Isolated Active-Set `N_VALUE` (OPEN_DECISION_01)

This subsection follows `OPEN_DECISION_02` on purpose. Owner-GO
`OWNER_GO_MF_OD01_CLOSE_NUMERIC_CEILING_N5_V1`
closes `OPEN_DECISION_01=N_VALUE` as Owner-policy numeric ceiling
`N_VALUE=5` under already-closed `AT_MOST_N`. Prior unblock from
`OWNER_POLICY_CLOSE_MF_OD02_AT_MOST_N_AND_OD03_CONSUME_CAP22_ORDERING_V1`
remains historical provenance. That provenance is **not** a second
close and does **not** reopen this decision.

This close is **Owner policy**, not forensic inference from Cap 0.4,
Top5 labels, Cap 2.2 Top-20, Cap 2.3 exactly-1, or a prior
decision-support recommendation. It does **not** import the Cap 0.4
`N=5` reminder as authority. It does **not** equate `TOP5` with
`ACTIVE_SET_N`. It does **not** prove `EXACTLY_5`. It does **not**
authorize padding. It does **not** bind a membership artifact, writer,
persistence, restore/reload, listing existence, rotation identity,
anti-churn numerics, G13 unlock, or host join. OD04 and OD05 remain
unchanged. OD01 did **not** close OD06 or OD07. OD06 is closed
separately in §1.7 as permission-only. OD07 remains unclosed.

```text
OPEN_DECISION_01=N_VALUE
OPEN_DECISION_01_CLOSED=true
OPEN_DECISION_01_CLOSE_CLASS=CLOSED_NUMERIC_CEILING_N5
N_VALUE=5
CARDINALITY_MODE=AT_MOST_N
N_IS_CEILING_NOT_FILL_TARGET=true
NO_PADDING=true
OWNER_POLICY_NOT_FORENSIC_INFERENCE=true
CAP04_N_EQUALS_5_REMINDER_USED_AS_AUTHORITY=false
CAP04_N_EQUALS_5_IS_NOT_N_AUTHORITY=true
TOP5_VS_ACTIVE_SET_N=NOT_EQUIVALENT
TOP5_IS_NOT_ACTIVE_SET_N=true
TOP5_PRODUCT_CREATED=false
EXACTLY_5=false
CAP22_TOP20_LIMIT_IS_NOT_ACTIVE_SET_CARDINALITY=true
CAP23_EXACTLY1_IMPORTED=false
NUMERIC_PREFIX_FROM_CAP22_ORDER_FOR_OVERFILL_CUT=ALLOWED
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=false
MEMBERSHIP_ARTIFACT_ADJUDICATED=false
EMPTY_SET_IS_NOT_AT_MOST_N_AUTHORIZATION=true
SILENCE_IS_NOT_MEMBERSHIP_OF_FIVE=true
OPEN_DECISION_04_CHANGED=false
OPEN_DECISION_05_CHANGED=false
OPEN_DECISION_06_CHANGED=false
OPEN_DECISION_06_CLOSED=true
OPEN_DECISION_07_CLOSED=false
```

Bound meaning: `0 < membership_count <= 5` from the same valid Cap-2.2
candidate context is cardinality-conformant when membership is
otherwise authorized. Underfill does **not** pad. Equality does
**not** prove `EXACTLY_5`. Overfill is cut by consuming Cap-2.2
membership order as a numeric prefix of at most 5. That prefix is
**not** a second ranker and is **not** a `TOP5` product. Empty, stale,
or unbound selector context remains non-authority.

### 1.4 Isolated selector state (OPEN_DECISION_04)

Owner-GO
`OWNER_POLICY_CLOSE_MF_OD04_MEMBERSHIP_LISTING_IDENTITY_NOT_SELECTOR_OWNED_STATE_V1`
closes `OPEN_DECISION_04=SELECTOR_STATE` as an **ownership principle
only**. Prior fail-closed **boundaries** from
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
remain historical provenance. That provenance is **not** a second
close and does **not** reopen this decision.

This close does **not** ratify a membership artifact, a writer, commit
semantics, persistence, restore/reload, a bound listing input, prior
listing existence, a rotation stage, a handoff, a runtime consumer, or
a membership state machine.

```text
OPEN_DECISION_04=SELECTOR_STATE
OPEN_DECISION_04_CLOSED=true
OPEN_DECISION_04_CLOSE_CLASS=OWNERSHIP_PRINCIPLE_ONLY
MEMBERSHIP_IDENTITY_OWNER_CLASS=ACTIVE_SET_NON_AUTHORITATIVE_MEMBERSHIP_COMPOSITION
MEMBERSHIP_IDENTITY_SEMANTIC_NAME=membership_state
SELECTOR_OWNS_MEMBERSHIP_IDENTITY=false
SELECTOR_STATE_OWNER=NONE_FOR_MEMBERSHIP_IDENTITY
DURABLE_SELECTOR_OWNED_MEMBERSHIP_STORE=NOT_AUTHORIZED
MEMBERSHIP_STATE_IS_NOT_SELECTOR_OWNED_STATE=true
HYGIENE_CONCEPTS_DO_NOT_FORCE_DURABLE_SELECTOR_STATE=true
SELECTOR_ROLE=PROPOSE_MEMBERSHIP_FROM_TOP20_CANDIDATE_CONTEXT
ANTI_CHURN_OWNER=SELECTOR
ANTI_CHURN_IS_RATIFIED_POLICY=false
PROVEN_SELECTOR_INPUT_IDENTITY=CAP_2_2_TOP20_ORDERED_CANDIDATE_CONTEXT
SELECTOR_MAY_CONSUME_MEMBERSHIP_LISTING_IDENTITY=true
MEMBERSHIP_LISTING_IDENTITY_BOUND=false
MEMBERSHIP_LISTING_IDENTITY_IS_NOT_PROVEN_INPUT=true
ROTATION_ROLE=MEMBERSHIP_DIFF_ONLY
MEMBERSHIP_STATE_MACHINE_RATIFIED=false
ALLOWED_STATE_TRANSITIONS=UNBOUND
SSF_SEMANTICS_IMPORTED=false
OPEN_DECISION_05_CLOSED=true
OPEN_DECISION_05_CLOSE_CLASS=NO_INDEPENDENT_PENDING_STATE_REQUIRED
OPEN_DECISION_06_CLOSED=true
OPEN_DECISION_06_CLOSE_CLASS=CLOSED_ALLOW_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED
OPEN_DECISION_07_CLOSED=false
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
```

Current / prior Active-Membership **identity class** is the existing
non-authoritative Active-Set composition identity. Boundary
`membership_state` remains that semantic name. Schema, type, and
authority stay `UNBOUND` / `NONE`. The selector does **not** own that
identity and must **not** hold a durable private membership store.

The selector may consume that listing identity together with the Cap-2.2
ranking origin **when later bound**. That consumption relation is
**not** a proven input, **not** a bound producer, and **not** a
consumer implementation. The only proven selector input identity
remains Cap 2.2 ordered Top-20 candidate context.

Hysteresis and minimum holding remain selector-owned **concepts**, not
ratified rules. Their ownership does **not** authorize durable
selector-owned membership state.

OD04 closes **ownership only**. It does **not** prove a membership
artifact, a writer, persistence, restore/reload, prior-listing
existence, a rotation stage, a handoff, or a runtime consumer.

### 1.5 Isolated membership-only transition-pending (OPEN_DECISION_05)

Owner-GO
`OWNER_POLICY_CLOSE_MF_OD05_NO_INDEPENDENT_PENDING_STATE_REQUIRED_V1`
closes `OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED` as
`CLOSED_NO_INDEPENDENT_PENDING_STATE_REQUIRED` for the **current
isolated MF model**. Prior fail-closed **boundaries** from
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
remain historical provenance. That provenance is **not** a second
close and does **not** reopen this decision.

This close means the current isolated MF ranking / selection model does
**not** require an independent Membership-Pending state class. Current
membership identity (when later bound), the selector membership
proposal, and selector-owned anti-churn admission / non-admission
already represent deferral of a proposed change. Rotation remains
membership-diff-only after admission.

This close does **not** mean a pending analog can never exist. It does
**not** ratify hysteresis, minimum holding, confirmation, cooldown, or
any anti-churn numeric or behavioral rule. A later introduction of an
independent pending class requires separate governed evidence and
policy. Cap 2.3 `REPLACEMENT_PENDING` remains not imported. Cap 0.4
`MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0` remains an
unconsumed reminder. This close does **not** bind a membership
artifact, writer, persistence, rotation identity, or a membership
state machine.

```text
OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED
OPEN_DECISION_05_CLOSED=true
OPEN_DECISION_05_CLOSE_CLASS=NO_INDEPENDENT_PENDING_STATE_REQUIRED
OPEN_DECISION_05_SCOPE=CURRENT_ISOLATED_MF_MODEL
NO_INDEPENDENT_MEMBERSHIP_PENDING_STATE_REQUIRED=true
MEMBERSHIP_ONLY_ANALOG_REQUIRED=false
MEMBERSHIP_ONLY_ANALOG_REQUIRED_SCOPE=CURRENT_ISOLATED_MF_MODEL
CURRENT_PROPOSED_ADMIT_REJECT_REMAINS_SUFFICIENT=true
TRANSITION_PENDING_NODE=OUT_OF_CORE_MODEL
SSF_REPLACEMENT_PENDING_IMPORTED=false
SSF_REPLACEMENT_PENDING_IS_OUT_OF_DOMAIN=true
REPLACEMENT_PENDING_IS_NOT_MEMBERSHIP_ROTATION=true
PENDING_IS_NOT_ANTI_CHURN=true
MEMBERSHIP_STATE_MACHINE_RATIFIED=false
INVENTION_OF_PENDING_STATE_MACHINE_FROM_PLAUSIBILITY=FORBIDDEN
OVERREAD_AS_PENDING_ANALOG_NEVER_NEEDED=FORBIDDEN
OVERREAD_AS_ANTI_CHURN_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_HYSTERESIS_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_MIN_HOLDING_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_CONFIRMATION_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_COOLDOWN_NOT_NEEDED=FORBIDDEN
```

Cap 2.3 `REPLACEMENT_PENDING` remains strictly out of this domain. The
isolated graph has no position semantics. Isolated-MF evidence for an
additional pending object is `NONE`. The productive SSF pending class
exists only in the forbidden position / exactly-one / alpha-block
domain. A durable pending class would prejudge an unratified membership
state machine and OD06 persistence. Those are **not** authorized here.

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
unbound; OD04 does not prove listing existence). Silence must **not**
infer a rotation engine, a stage owner, or a derived close.

### 1.7 Isolated persistence while G13 closed (OPEN_DECISION_06)

Owner-GO
`OWNER_GO_OD06_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED_V1`
closes `OPEN_DECISION_06=CONTEXT_PERSISTENCE_WHILE_G13_CLOSED` as
Owner-policy **permission**: a non-authoritative membership-context
artifact **may** persist while G13 remains an
`INTENTIONAL_SAFETY_BARRIER`. Prior fail-closed **boundaries** from
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
remain historical provenance. That provenance is **not** a second
close and does **not** reopen this decision.

This close is **permission only**. Permission to persist is **not**
existence of a persisted artifact. It does **not** bind a schema, DTO,
writer, reader, store, lifecycle, restore/reload, listing existence, or
prior-membership listing. It does **not** implement the selector. It
does **not** unlock G13, create a host join, activate runtime, or grant
execution or handoff authority. It does **not** close
`OPEN_DECISION_07`, ratify a rotation stage, or ratify anti-churn
policy or numerics. It does **not** equate Top-20 with Active Set, does
**not** create a `TOP5` product, and does **not** prove `EXACTLY_5`.
OD01, OD04, and OD05 remain unchanged.

```text
OPEN_DECISION_06=CONTEXT_PERSISTENCE_WHILE_G13_CLOSED
OPEN_DECISION_06_CLOSED=true
OPEN_DECISION_06_CLOSE_CLASS=CLOSED_ALLOW_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED
NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED=ALLOWED
NON_AUTHORITATIVE_ONLY=true
PERMISSION_TO_PERSIST_IS_NOT_EXISTENCE_OF_PERSISTED_ARTIFACT=true
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=UNPROVEN
MEMBERSHIP_LISTING_IDENTITY_BOUND=false
MEMBERSHIP_LISTING_IDENTITY_IS_NOT_PROVEN_INPUT=true
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
DOC_CONTRACT_PERSISTENCE=PRESENT_AUTHORITY_EFFECT_NONE
DOC_CONTRACT_PERSISTENCE_IS_NOT_MEMBERSHIP_ARTIFACT_PERSISTENCE=true
HOST_JOIN=NOT_DESIGNED
HOST_JOIN_AUTHORIZED=false
G13_UNLOCK=false
G13_REMAINS_CLOSED=true
RUNTIME_AUTHORITY=NONE
RUNTIME_AUTHORIZED=false
EXECUTION_AUTHORITY_EFFECT=NONE
PERSISTENCE_IS_NOT_G13_UNLOCK=true
PERSISTENCE_IS_NOT_HOST_JOIN=true
PERSISTENCE_IS_NOT_RUNTIME_ACTIVATION=true
OD07_EFFECT=NONE
OPEN_DECISION_07_CLOSED=false
ANTI_CHURN_POLICY_EFFECT=NONE
ROTATION_STAGE_RATIFIED=false
NAMED_GRAPH_NODE_IS_NOT_STAGE_RATIFICATION=true
OPEN_DECISION_01_CHANGED=false
OPEN_DECISION_04_CHANGED=false
OPEN_DECISION_05_CHANGED=false
```

Docs-only contract persistence already exists and has
`AUTHORITY_EFFECT=NONE`. That remains **not** membership-context
artifact persistence, **not** a producer, and **not** runtime
authority. This close allows a later non-authoritative
membership-context artifact to persist while G13 remains closed. It
does **not** create that artifact.

Fail-closed after this close:

```text
DOC_PERSIST_MUST_NOT_BE_READ_AS_ARTIFACT_PERSIST=true
ARTIFACT_PERMISSION_MUST_NOT_BE_READ_AS_ARTIFACT_EXISTENCE=true
ARTIFACT_PERSIST_MUST_NOT_BE_READ_AS_G13_UNLOCK=true
ARTIFACT_PERSIST_MUST_NOT_BE_READ_AS_HOST_JOIN=true
ARTIFACT_PERSIST_MUST_NOT_BE_READ_AS_RUNTIME_AUTHORITY=true
OVERREAD_AS_SCHEMA_OR_WRITER_BOUND=FORBIDDEN
OVERREAD_AS_OD07_CLOSE=FORBIDDEN
```

### 1.8 Cross-decision DAG (semantic; not a runtime path)

This subsection records the **semantic** dependency order among the
seven decisions. It is **not** a runtime path, **not** a host
join, and does **not** itself close any decision.

```text
DECISION_DAG_CLASS=SEMANTIC_DEPENDENCY_NOT_RUNTIME
CLOSED_DECISIONS=OPEN_DECISION_01,OPEN_DECISION_02,OPEN_DECISION_03,OPEN_DECISION_04,OPEN_DECISION_05,OPEN_DECISION_06
```

```text
TOP20_CANDIDATE_CONTEXT
→ CAP22_ORDER_CONSUMED_AS_MEMBERSHIP_ORDER
→ MF_SELECTOR
→ AT_MOST_N
→ OD01_CLOSED_NUMERIC_CEILING_N5
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

Current dispositions (this Owner-GO; not a later close of remaining
nodes):

| Decision | Disposition | Closed |
|---|---|---|
| `OPEN_DECISION_03` | `CLOSED_CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER` | `true` |
| `OPEN_DECISION_02` | `CLOSED_AT_MOST_N` | `true` |
| `OPEN_DECISION_01` | `CLOSED_NUMERIC_CEILING_N5` | `true` |
| `OPEN_DECISION_04` | `CLOSED_OWNERSHIP_PRINCIPLE_ONLY` | `true` |
| `OPEN_DECISION_05` | `CLOSED_NO_INDEPENDENT_PENDING_STATE_REQUIRED` | `true` |
| `OPEN_DECISION_07` | `UNRESOLVED_BUT_BOUNDARIES_SHARPENED` | `false` |
| `OPEN_DECISION_06` | `CLOSED_ALLOW_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED` | `true` |

A later close of one node does **not** close a neighbor by inference.
This persist closes `OPEN_DECISION_06` as Owner-policy permission
`ALLOWED` under `NON_AUTHORITATIVE_ONLY` while G13 remains closed.
It does **not** prove artifact existence, does **not** close
`OPEN_DECISION_07`, does **not** reopen `OPEN_DECISION_01`,
`OPEN_DECISION_04`, or `OPEN_DECISION_05`, does **not** create a
`TOP5` product, and does **not** prove `EXACTLY_5`.

Semantic identity of a later membership-context artifact is bound in
§1.9 as **information classes only**. That bind is **not** an
`OPEN_DECISION_*` close, **not** artifact existence, and **not** an
OD07 close. Artifact existence **class** is bound in §1.10 as
`BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT`.
That class bind is **not** instance existence, **not** schema, writer,
or reader, **not** prior-listing existence, and **not** an OD07 close.

```text
OPEN_DECISION_06
→ MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY_BOUND_INFORMATION_CLASSES_ONLY
→ ARTIFACT_EXISTENCE_CLASS_BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT
→ ARTIFACT_INSTANCE_EXISTENCE_UNPROVEN
→ INSTANCE_DECISION_CLASS_NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
→ PRIOR_MEMBERSHIP_LISTING_UNPROVEN
→ OD07_UNRESOLVED
```

After the §1.11 census persist, instance existence remains `UNPROVEN`.
That status is **not** `ABSENT`. Creation is **not** authorized.
Schema, writer, reader, prior listing, and OD07 remain later
unresolved dependencies and are **not** auto-next. This persist does
**not** name a next canonical decision. A later Owner-GO must name it.

```text
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
CREATION_AUTHORIZED=false
NEXT_STEP_IS_AUTOMATIC=false
SCHEMA_NOT_AUTO_NEXT=true
WRITER_NOT_AUTO_NEXT=true
READER_NOT_AUTO_NEXT=true
PRIOR_LISTING_NOT_AUTO_NEXT=true
OD07_NOT_AUTO_NEXT=true
```

### 1.9 Isolated membership-context artifact semantic identity

Owner-GO
`OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY_V1`
binds the **semantic identity** of a later non-authoritative
membership-context artifact at **information-class** level. Prior
fail-closed **boundaries** from OD06 §1.7 remain binding. That
permission close is **not** re-owned here and is **not** artifact
existence.

This bind does **not** create an artifact, does **not** bind a schema,
DTO, field, type, encoding, version, ID, epoch, timestamp, store,
writer, reader, or lifecycle, does **not** prove listing existence,
does **not** close `OPEN_DECISION_07`, does **not** unlock G13, and
does **not** grant runtime, host-join, or execution authority.

```text
OWNER_GO=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY_V1
MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY=BOUND_INFORMATION_CLASSES_ONLY
SEMANTIC_IDENTITY_CLOSE_CLASS=INFORMATION_CLASSES_ONLY
ARTIFACT_CLASS=NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY
SEMANTIC_OWNER_CLASS=ACTIVE_SET_NON_AUTHORITATIVE_MEMBERSHIP_COMPOSITION
CURRENT_MEMBERSHIP_SEMANTIC_PAYLOAD=ORDERED_ACTIVE_SET_MEMBERSHIP
CURRENT_MEMBERSHIP_SEMANTIC_PAYLOAD_NAME=ordered_instrument_ids
MEMBERSHIP_IDENTITY_SEMANTIC_NAME=membership_state
ORDERING_PROVENANCE=CAP_2_2_TOP20_ORDERED_CANDIDATE_CONTEXT
ORDERING_RULE=CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER
MF_RERANKING_ALLOWED=false
MF_OWN_TIE_BREAK_REQUIRED=false
CARDINALITY_MODE=AT_MOST_N
N_VALUE=5
EXACTLY_5=false
NO_PADDING=true
TEMPORAL_IDENTITY_INFORMATION_CLASS=REQUIRED
TEMPORAL_SCHEMA=UNBOUND
AS_OF_FRESHNESS_IDENTITY_NAMED=true
AS_OF_FRESHNESS_SCHEMA=UNBOUND
ARTIFACT_INSTANCE_IDENTITY_INFORMATION_CLASS=REQUIRED
INSTANCE_ID_SCHEMA=UNBOUND
ARTIFACT_TYPE_VERSION_STORE_IDENTITY=UNBOUND
PRIOR_MEMBERSHIP_REFERENCE_INFORMATION_CLASS=REQUIRED
PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=UNBOUND
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
SOURCE_PROVENANCE_INFORMATION_CLASS=REQUIRED
SOURCE_PROVENANCE_CAP22_FIELD_MAPPING=UNBOUND
REPLAY_MEMBERSHIP_ORDER_DETERMINISM=RECOGNIZED
PREVIOUS_TO_CURRENT_ARTIFACT_REPLAY=UNBOUND
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=UNPROVEN
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
OPEN_DECISION_07_CLOSED=false
OD07_EFFECT=NONE
G13_UNLOCK=false
RUNTIME_AUTHORIZED=false
EXECUTION_AUTHORITY_EFFECT=NONE
```

Bound meaning: if a later Owner-GO ratifies existence and schema of a
non-authoritative membership-context artifact, that artifact **must**
carry these information classes. This persist does **not** name new
fields. Existing parent-boundary semantic names
(`ordered_instrument_ids`, `membership_state`, `provenance`,
`as_of`) remain **names of information classes**. Their schema, type,
and authority remain `UNBOUND` / `NONE`.

Current membership payload is the ordered Active-Set membership
already named `ordered_instrument_ids`. That listing is **not**
Top-20 candidate context. Ordering provenance is Cap 2.2 ordered
Top-20 candidate context. Ordering rule remains consume-Cap-2.2
ordering; MF re-ranking and an MF-own tie-break remain forbidden.
Cardinality remains `AT_MOST_N` with ceiling `N_VALUE=5`.
`EXACTLY_5` remains false. Padding remains forbidden.

Temporal identity is a **required information class**. Concrete
epoch, snapshot, or `as_of` schema remains `UNBOUND`. Artifact
instance identity is a **required information class**. Concrete ID,
type, version, and store identity remain `UNBOUND`. Prior membership
reference is a **required information class** for prior/current
referability and previous→current replay. Concrete reference schema
remains `UNBOUND`. Actual prior-listing existence remains `UNPROVEN`.
Source provenance is a **required information class**. Concrete
Cap-2.2 field mapping remains `UNBOUND`. Cap-2.2 ranking-snapshot
identity fields remain Cap-2.2 identity and are **not** rebound as a
membership schema.

Deterministic membership-order is **recognized** via the already-closed
consume-Cap-2.2 policy. Previous→current artifact replay remains
`UNBOUND` until instance identity, temporal identity, and prior
reference identity exist as bound schemas **and** a prior listing is
proven. This persist does **not** prove those.

Negative boundary (this identity; not a schema):

```text
MEMBERSHIP_ARTIFACT_IS_NOT_CAP23_SSF_SNAPSHOT=true
MEMBERSHIP_ARTIFACT_IS_NOT_R6_SHADOW_SIM_EVIDENCE=true
MEMBERSHIP_ARTIFACT_IS_NOT_DOC_CONTRACT_PERSISTENCE=true
MEMBERSHIP_ARTIFACT_IS_NOT_TOP20_CANDIDATE_CONTEXT=true
TOP20_ROLE=CANDIDATE_CONTEXT_ONLY
TOP5_VS_ACTIVE_SET_N=NOT_EQUIVALENT
TOP5_IS_NOT_ACTIVE_SET_AUTHORITY=true
SCORES_RANKS_REMAIN_CAP22_CANDIDATE_CONTEXT=true
SCORES_RANKS_ARE_NOT_MEMBERSHIP_AUTHORITY=true
RETAINED_ENTERED_EXITED_PERSISTED_STAGE=NOT_RATIFIED
ROTATION_DELTAS_STAGE_VS_DERIVED=UNRESOLVED
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
OPEN_DECISION_07_CLOSED=false
ANTI_CHURN_POLICY_RATIFIED=false
HYSTERESIS_IS_RATIFIED_RULE=false
MIN_HOLDING_IS_RATIFIED_RULE=false
REPLACEMENT_MARGIN=UNRESOLVED
HYSTERESIS_CONFIRMATION_COUNT=UNRESOLVED
REPLACEMENT_PENDING_INDEPENDENT_STATE=FORBIDDEN_UNDER_CURRENT_OD05
SSF_REPLACEMENT_PENDING_IMPORTED=false
EXECUTION_FIELDS_INSIDE_MEMBERSHIP_ARTIFACT_IDENTITY=FORBIDDEN
ORDER_POSITION_VENUE_FIELDS_INSIDE_MEMBERSHIP_ARTIFACT_IDENTITY=FORBIDDEN
G13_UNLOCK=false
EXECUTION_AUTHORITY_EFFECT=NONE
```

`rotation_deltas` remains membership-change-only as **named**
isolated-domain semantics. Stage versus derived remains OD07 /
`UNRESOLVED`. Retained / entered / exited are **not** ratified as a
persisted stage. They are **not** declared derivable: prior listing
existence is `UNPROVEN`, durable artifact existence is `UNPROVEN`,
and OD07 remains unclosed.

Anti-churn, hysteresis, minimum holding, replacement margin, and
consecutive confirmation remain unratified **concepts**. OD05 remains
`NO_INDEPENDENT_PENDING_STATE_REQUIRED` for the current isolated MF
model. Cap 2.3 `REPLACEMENT_PENDING` remains not imported.

Fail-closed after this bind:

```text
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_ARTIFACT_EXISTENCE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_SCHEMA=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_PRIOR_LISTING_EXISTENCE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_RETAINED_ENTERED_EXITED_NOW_DERIVABLE=FORBIDDEN
OVERREAD_AS_FIELD_OR_DTO_INVENTION=FORBIDDEN
OVERREAD_AS_CAP22_SNAPSHOT_FIELDS_REBOUND_AS_MEMBERSHIP_SCHEMA=FORBIDDEN
```

### 1.10 Isolated membership-context artifact existence class

Owner-GO
`OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_EXISTENCE_CLASS_V1`
adjudicates the **existence class** of a non-authoritative
membership-context artifact. Prior fail-closed **boundaries** from
OD06 §1.7 and semantic identity §1.9 remain binding. Those binds are
**not** re-owned here and are **not** instance existence.

This persist classifies a **required durable artifact class**. It does
**not** claim that any concrete artifact instance exists. It does
**not** bind a storage format, path, schema, ID, version, epoch,
writer, reader, lifecycle, or retention mechanism. It does **not**
prove prior-listing existence, does **not** close `OPEN_DECISION_07`,
does **not** unlock G13, and does **not** grant runtime, host-join, or
execution authority.

```text
OWNER_GO=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_EXISTENCE_CLASS_V1
ARTIFACT_EXISTENCE_CLASS=BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT
INSTANCE_EXISTENCE_STATUS=UNPROVEN
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
SEMANTIC_IDENTITY=BOUND_INFORMATION_CLASSES_ONLY
INSTANCE_IDENTITY_SCHEMA=UNBOUND
TEMPORAL_IDENTITY_SCHEMA=UNBOUND
PRIOR_REFERENCE_SCHEMA=UNBOUND
CAP22_PROVENANCE_FIELD_MAPPING=UNBOUND
PRIOR_MEMBERSHIP_LISTING_STATUS=UNPROVEN
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=UNPROVEN
OPEN_DECISION_07_CLOSED=false
OD07_EFFECT=NONE
G13_UNLOCK=false
RUNTIME_AUTHORIZED=false
EXECUTION_AUTHORITY_EFFECT=NONE
ATLAS_AUTHORITY=NONE
```

Bound meaning: the isolated architecture now **requires** that a
durable non-authoritative membership-context artifact class exist
before downstream prior/current replay semantics may rely on it. This
is an existence **requirement / classification** only. No concrete
artifact instance is claimed to exist.

Semantic identity remains `BOUND_INFORMATION_CLASSES_ONLY` in §1.9.
Instance-identity schema, temporal-identity schema, prior-reference
schema, and Cap-2.2 provenance field mapping remain `UNBOUND`.
Prior-membership listing remains `UNPROVEN`. Schema, writer, and
reader remain unbound.

Negative existence boundary (this class; not an instance):

```text
OD06_PERMISSION_ALONE_DID_NOT_PROVE_EXISTENCE=true
SEMANTIC_IDENTITY_BIND_6373_DID_NOT_PROVE_EXISTENCE=true
DOC_SPEC_RUNBOOK_ATLAS_RECORDS_ARE_NOT_THE_MEMBERSHIP_ARTIFACT=true
ATLAS_REMAINS_AUTHORITY_NONE=true
CAP22_RANKING_SNAPSHOTS_ARE_UPSTREAM_PROVENANCE_NOT_THIS_ARTIFACT=true
CAP23_SSF_SNAPSHOTS_OUT_OF_DOMAIN_FOR_MF_ARTIFACT_EXISTENCE=true
R6_EVIDENCE_OUT_OF_DOMAIN_FOR_MF_ARTIFACT_EXISTENCE=true
EMPTY_PLACEHOLDER_FILE_DTO_OR_CLASS_IS_NOT_DURABLE_INSTANCE_EXISTENCE=true
REQUIRED_ARTIFACT_CLASS_DOES_NOT_PROVE_PRIOR_LISTING_EXISTENCE=true
DOC_CONTRACT_PERSISTENCE_IS_NOT_MEMBERSHIP_ARTIFACT_PERSISTENCE=true
PERMISSION_TO_PERSIST_IS_NOT_EXISTENCE_OF_PERSISTED_ARTIFACT=true
SEMANTIC_CLASS_BOUND_IS_NOT_INSTANCE_EXISTS=true
DURABLE_ARTIFACT_CLASS_IS_NOT_SCHEMA_WRITER_OR_READER=true
```

OD06 permission `ALLOWED` did **not** prove existence. The #6373
semantic-identity bind did **not** prove existence. Docs, spec,
runbook, and Atlas records are **not** the membership artifact. Atlas
remains `AUTHORITY=NONE`. Cap-2.2 ranking snapshots remain upstream
provenance, not this artifact. Cap-2.3 SSF snapshots and R6 evidence
remain out-of-domain for MF artifact existence. No empty placeholder
file, DTO, or class definition may count as durable instance existence
unless a later Owner-GO binds canonical durability and provenance
semantics. No prior-listing existence may be inferred from the
required artifact class.

Tracked origin/main census for an actual MF membership-context
artifact, store, manifest, ledger, or snapshot that could already
prove instance existence: **none proven**. Name collision is **not**
proof.

| Hit | Classification | Why not instance proof |
|---|---|---|
| This file; parent boundary; ownership; ranking-universe/egress; Master Runbook §4.5–§4.5.4 | `CURRENT_AUTHORITY` | Docs-contract persistence; not membership-artifact persistence |
| Map of Truth MF rows | `NAVIGATION_ONLY` | Navigation; no semantics; not an artifact |
| Atlas catalog / relations / generated graph | `NAVIGATION_ONLY` | `ATLAS_AUTHORITY=NONE`; not an artifact |
| `docs&#47;forensics&#47;persistence&#47;inventories&#47;P6_5189_HISTORICAL_SOURCE_SET_UNIVERSE_AND_POSITIVE_MEMBERSHIP_LEDGER_AND_THREE_HASH_NON_INFERENCE_OBSERVATION_V1.json` | `FORENSIC_RAW_EVIDENCE` / `HISTORICAL_ONLY` | Historical source-set universe membership ledger; name collision; `AUTHORITY=NONE`; not this class |
| Cap-2.2 `productive_futures_ranking_snapshot_v1.json` evidence | `OUT_OF_DOMAIN` | Upstream ranking provenance; not this artifact |
| Cap-2.3 `single_selected_future_selection_v1.json` / selection evidence | `OUT_OF_DOMAIN` | SSF selection; not imported as MF membership |
| `src&#47;ops&#47;canonical_r6_s3_multi_future_runtime_architecture_v1&#47;active_set_v1.py` | `OUT_OF_DOMAIN` | R6 S3 Phase-8 architecture; excluded by parent boundary |
| R6 S4 `ordered_instrument_ids` observation | `OUT_OF_DOMAIN` | Shadow/sim evidence; not promoted |
| `src&#47;research&#47;pit_futures_universe_manifest_v1.py` `MembershipStatus` | `OUT_OF_DOMAIN` | Research universe panel membership; name collision |
| `tests&#47;research&#47;test_fetch_cross_sectional_bound_period_panel_membership_filter_v0.py` | `OUT_OF_DOMAIN` | Research panel filter; name collision |

```text
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MEMBERSHIP_CONTEXT_ARTIFACT=false
NAME_COLLISION_IS_NOT_INSTANCE_PROOF=true
PLACEHOLDER_IS_NOT_INSTANCE_PROOF=true
```

Fail-closed after this class bind:

```text
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_INSTANCE_EXISTENCE=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_SCHEMA=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_PRIOR_LISTING_EXISTENCE=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_OD06_PERMISSION_EQUALS_INSTANCE_EXISTENCE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_INSTANCE_EXISTENCE=FORBIDDEN
OVERREAD_AS_DOC_CONTRACT_EQUALS_MEMBERSHIP_ARTIFACT=FORBIDDEN
OVERREAD_AS_ATLAS_RECORD_EQUALS_MEMBERSHIP_ARTIFACT=FORBIDDEN
OVERREAD_AS_CAP22_SNAPSHOT_EQUALS_MEMBERSHIP_ARTIFACT=FORBIDDEN
OVERREAD_AS_CAP23_OR_R6_EQUALS_MEMBERSHIP_ARTIFACT=FORBIDDEN
OVERREAD_AS_EMPTY_PLACEHOLDER_EQUALS_DURABLE_INSTANCE=FORBIDDEN
OVERREAD_AS_SCHEMA_WRITER_READER_OR_OD07_AUTO_NEXT=FORBIDDEN
```

### 1.11 Isolated membership-context artifact instance-existence census persist

Owner-GO
`OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_INSTANCE_EXISTENCE_CENSUS_PERSIST_V1`
persists the already-adjudicated **instance-existence decision class**.
Prior fail-closed **boundaries** from OD06 §1.7, semantic identity §1.9,
and existence class §1.10 remain binding. Those binds are **not**
re-owned here.

This persist does **not** create an artifact instance. It does **not**
bind a schema, writer, reader, path, ID, epoch, or temporal schema.
It does **not** prove prior-listing existence, does **not** close
`OPEN_DECISION_07`, does **not** ratify anti-churn policy, does **not**
adjudicate `rotation_deltas`, does **not** unlock G13, and does **not**
grant runtime or execution authority.

```text
OWNER_GO=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_INSTANCE_EXISTENCE_CENSUS_PERSIST_V1
ARTIFACT_EXISTENCE_CLASS=BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
CREATION_AUTHORIZED=false
INSTANCE_IDENTITY_STATUS=UNBOUND
TEMPORAL_IDENTITY_STATUS=UNBOUND
PRIOR_REFERENCE_STATUS=UNBOUND
CAP22_PROVENANCE_STATUS=UNBOUND
PRIOR_MEMBERSHIP_LISTING_STATUS=UNPROVEN
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
ROTATION_DELTAS_STATUS=UNRESOLVED
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
OD07_STATUS=UNCLOSED
G13_UNLOCK=false
RUNTIME_AUTHORIZED=false
EXECUTION_AUTHORITY_EFFECT=NONE
NEXT_STEP_IS_AUTOMATIC=false
```

`UNPROVEN` is **not** `ABSENT`. The required artifact class in §1.10 is
**not** create-now authorization. The §1.10 tracked origin/main census
remains the cited instance-census authority: no instance proof found.
Name collision is **not** proof. Empty placeholder is **not** instance
proof. Prior membership listing remains `UNPROVEN` and is **not**
claimed existent. Schema, writer, and reader remain unbound.

Fail-closed after this census persist:

```text
OVERREAD_AS_UNPROVEN_EQUALS_ABSENT=FORBIDDEN
OVERREAD_AS_REQUIRED_CLASS_EQUALS_CREATE_NOW=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_INSTANCE_EXISTS=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_CREATION_AUTHORIZED=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_SCHEMA=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_PRIOR_LISTING_EXISTENCE=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_ANTI_CHURN_RATIFICATION=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_ROTATION_DELTAS_ADJUDICATION=FORBIDDEN
OVERREAD_AS_CENSUS_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_SCHEMA_WRITER_READER_PRIOR_LISTING_OR_OD07_AUTO_NEXT=FORBIDDEN
```

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
| Membership-only transition-pending | `NONE_FOR_CURRENT_ISOLATED_MF_MODEL`; node `OUT_OF_CORE_MODEL` | `ADJUDICATED_CONCLUSION` of OD05 close; not never-needed |
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
SELECTOR_STATE_INPUT=NOT_A_MEMBERSHIP_STORE
MEMBERSHIP_LISTING_IDENTITY_BOUND=false
MEMBERSHIP_LISTING_IDENTITY_IS_NOT_PROVEN_INPUT=true
SSF_SELECTION_SNAPSHOT_INPUT=FORBIDDEN
DASHBOARD_ALLOWLIST_MANUAL_OVERRIDE_INPUT=FORBIDDEN
```

Cap 2.2 already produces a deterministic ordered Top-20 candidate
context. That ordered listing is the **only** proven input identity for
the isolated selector. Owner-GO
`OWNER_POLICY_CLOSE_MF_OD02_AT_MOST_N_AND_OD03_CONSUME_CAP22_ORDERING_V1`
authorizes consuming that origin order as membership order. This
contract still does **not** authorize a second ranking input.
`SELECTOR_MAY_CONSUME_MEMBERSHIP_LISTING_IDENTITY=true` is an ownership
relation for a later-bound listing identity. It is **not** a proven
input and does **not** bind a listing consumer.

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
MEMBERSHIP_ONLY_ANALOG_REQUIRED=false
MEMBERSHIP_ONLY_ANALOG_REQUIRED_SCOPE=CURRENT_ISOLATED_MF_MODEL
OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED
OPEN_DECISION_05_CLOSED=true
OPEN_DECISION_05_CLOSE_CLASS=NO_INDEPENDENT_PENDING_STATE_REQUIRED
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
REPLACEMENT_PENDING_SEMANTICS=SSF_STATE_NOT_IMPORTED_NO_INDEPENDENT_MF_PENDING_STATE_REQUIRED
CAP23_REPLACEMENT_PENDING_IMPORTED=false
SSF_REPLACEMENT_STATE_MACHINE_IMPORTED=false
TRANSITION_PENDING_CORE_OWNER=NONE_FOR_CURRENT_ISOLATED_MF_MODEL
TRANSITION_PENDING_NODE=OUT_OF_CORE_MODEL
MEMBERSHIP_ONLY_ANALOG_REQUIRED=false
MEMBERSHIP_ONLY_ANALOG_REQUIRED_SCOPE=CURRENT_ISOLATED_MF_MODEL
NO_INDEPENDENT_MEMBERSHIP_PENDING_STATE_REQUIRED=true
REPLACEMENT_PENDING_IS_NOT_MEMBERSHIP_ROTATION=true
```

Cap 2.3 `REPLACEMENT_PENDING` is a **productive single-selection state**
used while an open position exists: no silent instrument switch; no
alpha for a replacement instrument; replacement persisted only as that
state. That state machine is **outside** this isolated graph.

A membership-only analog is **not required** by the current isolated MF
model. Current membership, the selector proposal, and anti-churn
admission / non-admission already represent deferral. This persist does
**not** invent a pending state machine and does **not** mean a later
governed pending class can never exist.

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
| Membership-only pending analog | Not required in the current isolated MF model (`OPEN_DECISION_05` closed) | Still would not **be** rotation | Not a second membership identity | No; node remains `OUT_OF_CORE_MODEL` |

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
NO_INDEPENDENT_MEMBERSHIP_PENDING_STATE_REQUIRED=true
OVERREAD_AS_SELECTION_OR_RUNTIME=FORBIDDEN
OVERREAD_AS_FUTURE_HOST_INPUT=FORBIDDEN
OVERREAD_AS_N5_EQUALS_TOP5_PRODUCT=FORBIDDEN
OVERREAD_AS_EXACTLY_N=FORBIDDEN
OVERREAD_AS_EXACTLY_5=FORBIDDEN
OVERREAD_AS_AT_MOST_N_EQUALS_EMPTY_SET=FORBIDDEN
OVERREAD_AS_SSF_STATE_MACHINE=FORBIDDEN
OVERREAD_AS_ROTATION_POLICY=FORBIDDEN
OVERREAD_AS_TOP5_EQUALS_ACTIVE_SET_N=FORBIDDEN
OVERREAD_AS_CAP22_TOP20_LIMIT_AS_ACTIVE_SET_N=FORBIDDEN
OVERREAD_AS_CAP23_EXACTLY1_AS_MF_CARDINALITY_MODE=FORBIDDEN
OVERREAD_AS_SECOND_RANKER=FORBIDDEN
OVERREAD_AS_OWN_MF_SCORING=FORBIDDEN
OVERREAD_AS_MF_OWN_TIE_BREAK_ALGORITHM=FORBIDDEN
OVERREAD_AS_N5_EQUALS_CAP04_REMINDER_AUTHORITY=FORBIDDEN
OVERREAD_AS_SILENCE_EQUALS_MEMBERSHIP_OF_FIVE=FORBIDDEN
OVERREAD_AS_DURABLE_SELECTOR_STATE=FORBIDDEN
OVERREAD_AS_MEMBERSHIP_STATE_EQUALS_SELECTOR_STATE=FORBIDDEN
OVERREAD_AS_OD04_EQUALS_ARTIFACT_PERSIST=FORBIDDEN
OVERREAD_AS_OD04_EQUALS_BOUND_LISTING_INPUT=FORBIDDEN
OVERREAD_AS_OD04_EQUALS_WRITER_OR_RESTORE=FORBIDDEN
OVERREAD_AS_PENDING_ANALOG_NEEDED=FORBIDDEN
OVERREAD_AS_PENDING_ANALOG_NEVER_NEEDED=FORBIDDEN
OVERREAD_AS_ANTI_CHURN_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_HYSTERESIS_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_MIN_HOLDING_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_CONFIRMATION_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_COOLDOWN_NOT_NEEDED=FORBIDDEN
OVERREAD_AS_OD05_EQUALS_STATE_MACHINE=FORBIDDEN
OVERREAD_AS_OD05_EQUALS_ARTIFACT_PERSIST=FORBIDDEN
OVERREAD_AS_ROTATION_STAGE_RATIFICATION=FORBIDDEN
OVERREAD_AS_ROTATION_DERIVED_CLOSE=FORBIDDEN
OVERREAD_AS_ROTATION_ENGINE=FORBIDDEN
OVERREAD_AS_DOC_PERSIST_EQUALS_ARTIFACT_PERSIST=FORBIDDEN
OVERREAD_AS_PERMISSION_EQUALS_ARTIFACT_EXISTENCE=FORBIDDEN
OVERREAD_AS_PERSISTENCE_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_PERSISTENCE_EQUALS_HOST_JOIN=FORBIDDEN
OVERREAD_AS_OD06_EQUALS_SCHEMA_OR_WRITER=FORBIDDEN
OVERREAD_AS_OD06_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_ARTIFACT_EXISTENCE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_SCHEMA=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_PRIOR_LISTING_EXISTENCE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_SEMANTIC_IDENTITY_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_INSTANCE_EXISTENCE=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_SCHEMA=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_PRIOR_LISTING_EXISTENCE=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_EXISTENCE_CLASS_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_EMPTY_PLACEHOLDER_EQUALS_DURABLE_INSTANCE=FORBIDDEN
OVERREAD_AS_SCHEMA_WRITER_READER_OR_OD07_AUTO_NEXT=FORBIDDEN
OVERREAD_AS_RETAINED_ENTERED_EXITED_NOW_DERIVABLE=FORBIDDEN
INVENTION_OF_THRESHOLDS_FROM_PLAUSIBILITY=FORBIDDEN
CANDIDATE_COUNT_VS_N=OPERATIVE_AT_MOST_N_CEILING_5
UNDERFILL_DOES_NOT_PAD=true
UNDERFILL_DOES_NOT_SET_N=true
UNDERFILL_DOES_NOT_AUTHORIZE_EMPTY_SET=true
EXACT_FILL_DOES_NOT_PROVE_EXACTLY_N=true
EXACT_FILL_DOES_NOT_PROVE_EXACTLY_5=true
OVERFILL_DOES_NOT_AUTHORIZE_N_EXPANSION=true
OVERFILL_NUMERIC_CUT_FROM_CAP22_ORDER=ALLOWED
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=false
```

## 12. Unresolved parameters

No isolated-domain duration, rank delta, confirmation count,
cooldown, turnover bound, or tie-break key-order for an MF-own scoring
contract is canonical. Numeric ceiling `N_VALUE=5` is closed in §1.3
as Owner policy under `AT_MOST_N`. Hygiene numerics remain unresolved.

```text
UNRESOLVED_PARAMETERS=HYGIENE_NUMERICS_AND_MF_OWN_SCORING_ALGORITHMS_BELOW
N_VALUE=5
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
MEMBERSHIP_ONLY_PENDING_STATE_MACHINE=NOT_REQUIRED_IN_CURRENT_ISOLATED_MF_MODEL
```

Cap 2.3 evidence values such as `hysteresis_rank_improvement=1` and
`min_holding_period_seconds=3600.0` remain Cap-2.3
`CANONICAL_AUTHORITY` / `HISTORICAL_STATE` for single-selected-future
policy. Citing them here is **negative constraint** only:
`SSF_SEMANTICS_IMPORTED=false`.

Open decisions remaining after this Owner-policy close. Fail-closed
**boundaries** for still-open OD07 remain in §1.6. OD01 is closed
in §1.3 as Owner-policy ceiling `N_VALUE=5`. OD02 and OD03 are closed
in §1.1–§1.2. OD04 is closed in §1.4 as ownership principle only. OD05
is closed in §1.5 as `NO_INDEPENDENT_PENDING_STATE_REQUIRED` for the
current isolated MF model. OD06 is closed in §1.7 as permission-only
`ALLOWED` while G13 remains closed. Permission is not artifact
existence. Membership-context artifact semantic identity is bound in
§1.9 as information classes only. That bind is not artifact existence,
not schema, not writer, not prior-listing existence, and not an
OD07 close. Artifact existence class is bound in §1.10 as
`BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT`.
That class bind is not instance existence, not schema, not writer,
not prior-listing existence, and not an OD07 close. Instance existence
remains `UNPROVEN`. The instance-existence decision class is persisted
in §1.11 as
`NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED`.
`UNPROVEN` is not `ABSENT`. Creation is not authorized.

```text
OPEN_DECISION_01=N_VALUE
OPEN_DECISION_01_CLOSED=true
OPEN_DECISION_01_CLOSE_CLASS=CLOSED_NUMERIC_CEILING_N5
N_VALUE=5
OPEN_DECISION_02=EXACTLY_N_VS_AT_MOST_N
OPEN_DECISION_02_CLOSED=true
CARDINALITY_MODE=AT_MOST_N
OPEN_DECISION_03=CONSUME_CAP22_ORDERING_VS_LATER_OWN_MF_SCORING
OPEN_DECISION_03_CLOSED=true
MEMBERSHIP_ORDER_POLICY=CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER
OPEN_DECISION_04=SELECTOR_STATE
OPEN_DECISION_04_CLOSED=true
OPEN_DECISION_04_CLOSE_CLASS=OWNERSHIP_PRINCIPLE_ONLY
SELECTOR_STATE_OWNER=NONE_FOR_MEMBERSHIP_IDENTITY
OPEN_DECISION_05=MEMBERSHIP_ONLY_TRANSITION_PENDING_NEEDED
OPEN_DECISION_05_CLOSED=true
OPEN_DECISION_05_CLOSE_CLASS=NO_INDEPENDENT_PENDING_STATE_REQUIRED
OPEN_DECISION_05_SCOPE=CURRENT_ISOLATED_MF_MODEL
MEMBERSHIP_ONLY_ANALOG_REQUIRED=false
OPEN_DECISION_06=CONTEXT_PERSISTENCE_WHILE_G13_CLOSED
OPEN_DECISION_06_CLOSED=true
OPEN_DECISION_06_CLOSE_CLASS=CLOSED_ALLOW_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED
NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED=ALLOWED
PERMISSION_TO_PERSIST_IS_NOT_EXISTENCE_OF_PERSISTED_ARTIFACT=true
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=UNPROVEN
MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY=BOUND_INFORMATION_CLASSES_ONLY
ARTIFACT_EXISTENCE_CLASS=BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
CREATION_AUTHORIZED=false
INSTANCE_IDENTITY_STATUS=UNBOUND
TEMPORAL_IDENTITY_STATUS=UNBOUND
PRIOR_REFERENCE_STATUS=UNBOUND
CAP22_PROVENANCE_STATUS=UNBOUND
PRIOR_MEMBERSHIP_LISTING_STATUS=UNPROVEN
TEMPORAL_SCHEMA=UNBOUND
INSTANCE_ID_SCHEMA=UNBOUND
PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=UNBOUND
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
ROTATION_DELTAS_STATUS=UNRESOLVED
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
OD07_STATUS=UNCLOSED
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
OPEN_DECISION_07_CLOSED=false
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=false
MF_OWN_TIE_BREAK_REQUIRED=false
```

## 13. Forensic census (bound; not a second SSOT)

| Mechanism | Current authority | Existing contract | Historical evidence | Current runtime existence | Unresolved |
|---|---|---|---|---|---|
| Tie-break | Cap 2.2 origin ordering is membership order after OD03 close; MF-own not required while consume policy holds | Ownership §5.1; this file §6 | Cap 2.2 ranking evidence `tie_break_order`; Cap 2.3 different order **not imported**; research/strategy tie-breaks `OUT_OF_DOMAIN` | Isolated MF selector unimplemented; Cap 2.2 producer exists as TOP20 origin | Hygiene numerics |
| Hysteresis | Ownership locates concept at selector; no MF rule authority | Ownership §5.2; this file §7 | Cap 2.3 SSF hysteresis **not imported**; Cap 0.4 open decision; MV2/strategy hysteresis `OUT_OF_DOMAIN` | Isolated MF selector unimplemented | All numerics; concept-vs-rule remains concept |
| Min holding | Ownership locates concept at selector; no MF rule authority | Ownership §5.3; this file §8 | Cap 2.3 SSF min holding **not imported**; Cap 0.4 open decision | Isolated MF selector unimplemented | All numerics; residence duration unbound |
| Replacement-pending | Cap 2.3 only; **not** MF authority | Ownership §5.5 forbids SSF import; this file §9 / §1.5 | Cap 2.3 `REPLACEMENT_PENDING` state machine | Cap 2.3 producer exists **outside** this graph; no MF pending runtime | Independent MF pending class **not required** in the current isolated model (`OPEN_DECISION_05` closed); not never-needed |
| Membership-context artifact identity | Information classes bound in §1.9; class `NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY`; owner-class Active-Set composition | This file §1.9; parent boundary §8 names remain unbound schema | R6 `ordered_instrument_ids` observation **not promoted**; Cap-2.3 snapshots **not imported**; docs-contract persist **not** membership artifact | Isolated membership artifact unimplemented; `MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=UNPROVEN` | Instance existence, schema, writer, reader, temporal/instance/prior-reference schemas, prior listing, OD07 |
| Membership-context artifact existence class | Class bound in §1.10 as `BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT`; instance `UNPROVEN` | This file §1.10 | OD06 permission **not** existence; #6373 identity **not** existence; Cap-2.2 snapshots upstream only; Cap-2.3/R6 `OUT_OF_DOMAIN`; P6_5189 ledger name-collision `HISTORICAL_ONLY`; Atlas `AUTHORITY=NONE` | No durable instance on tracked origin/main; empty placeholder **not** instance | Instance existence; schema; writer; reader; prior listing; OD07 |
| Membership-context artifact instance-existence census | Decision class persisted in §1.11 as `NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED`; census verdict `NO_INSTANCE_PROOF_FOUND`; instance remains `UNPROVEN`; `UNPROVEN` is not `ABSENT`; creation not authorized | This file §1.11; census table in §1.10 | §1.10 tracked origin/main census: no instance proof found | Isolated membership artifact unimplemented; `CREATION_AUTHORIZED=false` | Schema; writer; reader; prior listing; OD07; creation authorization |

```text
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MF_SELECTOR=false
CURRENT_RUNTIME_EXISTENCE_ISOLATED_ANTI_CHURN=false
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MEMBERSHIP_ROTATION_POLICY=false
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MEMBERSHIP_CONTEXT_ARTIFACT=false
HISTORICAL_EXISTENCE_IS_NOT_TODAYS_MF_AUTHORITY=true
NAME_COLLISION_IS_NOT_INSTANCE_PROOF=true
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
RANKING_UNIVERSE_EGRESS_CONTRACT=MF_RANKING_UNIVERSE_AND_SINGLE_EGRESS_BOUNDARY_CONTRACT_V1
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

Any later change to `N`, membership artifact schema, writer, hygiene numerics, membership-only pending-state, own MF
scoring, or rotation-stage identity requires a **new** Owner-GO and
remains isolated. This contract does **not** authorize, specify, or
prepare host integration. OD01 is closed as Owner-policy ceiling
`N_VALUE=5`. OD04 is closed as ownership principle only. OD06 is
closed as permission-only `ALLOWED` while G13 remains closed.
Permission is not artifact existence, schema, writer, or OD07 close.
Membership-context artifact semantic identity is bound in §1.9 as
information classes only. That bind is not artifact existence, not
schema, not writer, not prior-listing existence, and not an OD07
close. Artifact existence class is bound in §1.10 as
`BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT`.
That class bind is not instance existence, not schema, not writer,
not prior-listing existence, and not an OD07 close. Instance existence
remains `UNPROVEN`. The instance-existence decision class is persisted
in §1.11 as
`NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED`.
`UNPROVEN` is not `ABSENT`. Creation is not authorized. Schema, writer,
reader, prior listing, and OD07 are **not** auto-next.
