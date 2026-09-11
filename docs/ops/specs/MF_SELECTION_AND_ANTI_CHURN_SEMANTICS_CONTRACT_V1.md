---
docs_token: DOCS_TOKEN_MF_SELECTION_AND_ANTI_CHURN_SEMANTICS_CONTRACT_V1
status: active
scope: Docs persist of adjudicated isolated MF selection and anti-churn mechanism semantics; OD01 closed as Owner-policy ceiling N=5 under AT_MOST_N; OD06 closed as ALLOW permission for non-authoritative membership-context artifact persistence while G13 remains closed; permission is not artifact existence; membership-context artifact semantic identity bound as information classes only; artifact existence class bound as required durable non-authoritative membership-context artifact; schema, writer, reader, durability, provenance, and lifecycle bound in §1.18; first valid bootstrap instance proven; instance existence PROVEN; isolated selector and membership-diff rotation bound in §1.19; deterministic previous-to-current replay bound in §1.20; isolated MF target complete; productive integration not complete; RUNTIME_AUTHORIZED remains false; creation-authorization predicate bound as PERMISSION_BIT_ONLY; named decision class MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1 closed as SET_CREATION_AUTHORIZED_TRUE; CREATION_AUTHORIZED is true as permission-bit only; named decision class MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1 closed as SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE; MATERIALIZATION_AUTHORITY_GRANTED is true as grant only; OPEN_DECISION_07 closed as CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY; rotation_deltas derived not durable canonical state; anti-churn POLICY_A ratified; this persist does not name a next canonical decision; no host adapter; no Cap-2.3/2.4 join; cooldown/turnover unratified
capability: NONE
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-10
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
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_CREATION_AUTHORIZATION_PREDICATE=OWNER_GO_MF_CREATION_AUTHORIZATION_PREDICATE_AND_PRECONDITION_MEMBERSHIP_V1
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_CLASS=OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_CLASS_V1
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION=OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_CLASS=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_CLASS_V1
OWNER_GO_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN=OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1
OWNER_GO_WP_MF_02_ARTIFACT_CONTRACT_AND_FIRST_DURABLE_INSTANCE=OWNER_GO_WP_MF_02_ARTIFACT_CONTRACT_AND_FIRST_DURABLE_INSTANCE_V1
OWNER_GO_WP_MF_03_ISOLATED_SELECTOR_AND_MEMBERSHIP_DIFF_ROTATION_RUNTIME=OWNER_GO_WP_MF_03_ISOLATED_SELECTOR_AND_MEMBERSHIP_DIFF_ROTATION_RUNTIME_V1
OWNER_GO_WP_MF_04_DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_PROOF=OWNER_GO_WP_MF_04_DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_PROOF_V1
OWNER_GO_WP_MF_05_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_DEFINITION=OWNER_GO_WP_MF_05_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_DEFINITION_V1
BOUND_ORIGIN_MAIN_SHA=a430bd3837a833d56a8029d3c0d5e8c5380708a1
BOUND_ORIGIN_MAIN_SHA_THIS_IDENTITY_SLICE=c58d8c5a8a7268af74c989aa0fb166f8f6df40b1
BOUND_ORIGIN_MAIN_SHA_THIS_EXISTENCE_CLASS_SLICE=b364d1a26d927eeb5d143028afd687f6d3183042
BOUND_ORIGIN_MAIN_SHA_THIS_INSTANCE_CENSUS_SLICE=81bd848c7054f2dafe1965b899b79ca809d4c278
BOUND_ORIGIN_MAIN_SHA_THIS_CREATION_AUTHORIZATION_PREDICATE_SLICE=d5a68a8b1a4c60fc194c8dfe3426c1de047d8a45
BOUND_ORIGIN_MAIN_SHA_THIS_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_CLASS_SLICE=56ebdb35cae207c96b8115346e77372cb10e0993
BOUND_ORIGIN_MAIN_SHA_THIS_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_SLICE=874d86df88b3ef6cd7762078e11b4c571033ad55
BOUND_ORIGIN_MAIN_SHA_THIS_MATERIALIZATION_AUTHORITY_DECISION_CLASS_SLICE=36e74cbf219d378a6f2225019a2d0589b38bb989
BOUND_ORIGIN_MAIN_SHA_THIS_MATERIALIZATION_AUTHORITY_DECISION_SLICE=e51f1a08744bbabc8e7f911f8fc59606764f9348
BOUND_ORIGIN_MAIN_SHA_THIS_OD07_AND_ANTI_CHURN_SLICE=0f335b4c5b0dcac41d60a1e057de946d7ab4791c
BOUND_ORIGIN_MAIN_SHA_THIS_WP_MF_02_SLICE=1cfd2e7d70b6ae43262439e07d17851985e4701a
BOUND_ORIGIN_MAIN_SHA_THIS_WP_MF_03_SLICE=a7182814b8dddf49e34ef1f3c408404364f0e691
BOUND_ORIGIN_MAIN_SHA_THIS_WP_MF_04_SLICE=d7609eae1805cde68202e9a00027960c7018e804
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
AUTHORITY_HANDOFF_STATUS=DEFINED_CONSUMER_UNBOUND
ISOLATION_INVARIANT=HARD_DOMAIN_END
NEW_EDGE_TO_PRODUCTIVE_SYSTEM=false
POLICY_RATIFIED=false
NUMERICS_RATIFIED=false
ANTI_CHURN_POLICY_A_NUMERICS_RATIFIED=true
COOLDOWN_TURNOVER_NUMERICS_RATIFIED=false
N_VALUE=5
N_CEILING_RATIFIED=true
SSF_SEMANTICS_IMPORTED=false
MF_SCORING_RATIFIED=false
ROTATION_POLICY_RATIFIED=false
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_ARE_NOT_DURABLE_CANONICAL_STATE=true
ROTATION_DELTAS_DURABLE_STAGE_FORBIDDEN=true
MEMBERSHIP_STATE_MACHINE_RATIFIED=false
MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY=BOUND_INFORMATION_CLASSES_ONLY
ARTIFACT_EXISTENCE_CLASS=BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT
ARTIFACT_INSTANCE_EXISTENCE=PROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=BOOTSTRAP_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
CREATION_AUTHORIZED=true
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
CLOSED_DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
CLOSED_DECISION_CLASS_REMAINS=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
PRIOR_CLASS_REMAINS_CLOSED=true
OWNER_DECISION=SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE
DECISION_CLASS_BIND_DOES_NOT_SET_CREATION_AUTHORIZED_TRUE=true
DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
DECISION_SCOPE=OWNER_DECIDES_MATERIALIZATION_AUTHORITY_GRANTED_TRUE_OR_FALSE_UNDER_EXISTING_PERMISSION_BIT_ONLY_SEMANTICS
DECISION_CLASS_BOUND=true
DECISION_CLASS_CLOSED=true
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
CLASS_BIND_IS_NOT_SUBSTANCE_CLOSE=true
CLASS_BIND_DOES_NOT_SET_MATERIALIZATION_AUTHORITY_TRUE=true
MATERIALIZATION_AUTHORITY_GRANTED=true
GRANT_IS_NOT_MATERIALIZATION=true
GRANT_IS_NOT_ARTIFACT_CREATION=true
GRANT_IS_NOT_INSTANCE_PROOF=true
GRANT_DOES_NOT_BIND_SCHEMA_WRITER_READER=true
GRANT_DOES_NOT_CLOSE_OD07=true
GRANT_DOES_NOT_RATIFY_ANTI_CHURN=true
GRANT_DOES_NOT_AUTHORIZE_RUNTIME=true
GRANT_DOES_NOT_AUTHORIZE_EXECUTION=true
ARTIFACT_INSTANCE_CREATED=true
SCHEMA_BOUND_UNCHANGED=false
WRITER_BOUND_UNCHANGED=false
READER_BOUND_UNCHANGED=false
OD07_STATUS_UNCHANGED=false
ANTI_CHURN_POLICY_STATUS_UNCHANGED=false
OD07_CLOSE_DOES_NOT_MATERIALIZE=true
OD07_CLOSE_DOES_NOT_BIND_SCHEMA=true
OD07_CLOSE_DOES_NOT_AUTHORIZE_RUNTIME=true
ANTI_CHURN_CLOSE_DOES_NOT_MATERIALIZE=true
ANTI_CHURN_CLOSE_DOES_NOT_BIND_SCHEMA=true
ANTI_CHURN_CLOSE_DOES_NOT_AUTHORIZE_RUNTIME=true
SCHEMA_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
WRITER_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
READER_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
OD07_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
ANTI_CHURN_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=PROVEN
INSTANCE_IDENTITY_STATUS=BOUND
TEMPORAL_IDENTITY_STATUS=BOUND
PRIOR_REFERENCE_STATUS=BOUND
CAP22_PROVENANCE_STATUS=BOUND
PRIOR_MEMBERSHIP_LISTING_STATUS=BOOTSTRAP_PROVEN
SCHEMA_BOUND=true
WRITER_BOUND=true
READER_BOUND=true
TEMPORAL_SCHEMA=BOUND
INSTANCE_ID_SCHEMA=BOUND
PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=BOUND
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=BOOTSTRAP_PROVEN
CANONICAL_DURABILITY_BOUND=true
CANONICAL_PROVENANCE_BOUND=true
ARTIFACT_LIFECYCLE_BOUND=true
ARTIFACT_INSTANCE_ID=mca_bf0255a6007432e2
ARTIFACT_TYPE=MF_MEMBERSHIP_CONTEXT_V1
BOOTSTRAP_DIRECT_PREFIX_FILL_IS_CANONICALLY_AUTHORIZED=true
SELECTOR_RUNTIME_IMPLEMENTED=true
MEMBERSHIP_DECISION_RUNTIME_IMPLEMENTED=true
ROTATION_RUNTIME_IMPLEMENTED=true
DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED=true
MF_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED=true
MF_DETERMINISTIC_REPLAY_PROVEN=true
ISOLATED_MF_TARGET_COMPLETE=true
PRODUCTIVE_MF_INTEGRATION_COMPLETE=false
NEXT_STEP_IS_AUTOMATIC=false
RUNTIME_AUTHORIZED=false
ROTATION_DELTAS_STATUS=DERIVED
ANTI_CHURN_POLICY_STATUS=RATIFIED
ANTI_CHURN_OWNER=SELECTOR
HYSTERESIS_IS_RATIFIED_RULE=true
HYSTERESIS_MODE=RANK_IMPROVEMENT_VS_DISPLACED_INCUMBENT
CHALLENGER_MARGIN_TYPE=RANK
CHALLENGER_MARGIN_VALUE=1
MINIMUM_HOLDING_UNIT=RANKING_OBSERVATIONS
MINIMUM_HOLDING_VALUE=2
MINIMUM_HOLDING_IS_NOT_POSITION_HOLDING=true
CONSECUTIVE_CONFIRMATION_COUNT=1
MULTIPLE_REPLACEMENTS_PER_CYCLE=true
TIE_BREAK=CAP22_ORIGIN_CONSUMED_AS_MEMBERSHIP_ORDER
BOOTSTRAP_RULE=PREFIX_FILL_FROM_CAP22_ELIGIBLE_NO_ANTI_CHURN_NO_PADDING
FORCED_REMOVAL_RULE=ABSENT_OR_INELIGIBLE_BYPASSES_ANTI_CHURN
COOLDOWN_RATIFIED=false
TURNOVER_POLICY_RATIFIED=false
OD07_STATUS=CLOSED
OPEN_DECISION_07_CLOSED=true
OPEN_DECISION_07_CLOSE_CLASS=CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
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
separately in §1.7 as permission-only. OD07 is closed separately in
§1.6 as `CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY`.

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
ANTI_CHURN_IS_RATIFIED_POLICY=true
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

Hysteresis and minimum holding are selector-owned **POLICY_A rules**
in §7 / §8 / §1.17. Their ownership does **not** authorize durable
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
`OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1`
closes `OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY`
as `CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY`. Prior fail-closed
**boundaries** from
`OWNER_GO_MF_OPEN_DECISIONS_01_THROUGH_07_BOUNDED_ADJUDICATION_WORKPACKAGE_V1`
remain historical provenance. That provenance is **not** a second
close and does **not** reopen this decision.

This close does **not** ratify a rotation engine, does **not** invent
a stage owner, does **not** persist retained / entered / exited as
durable canonical state, does **not** bind schema, writer, or
reader, does **not** prove prior-listing existence, does **not**
materialize an artifact, does **not** unlock G13, and does **not**
grant runtime or execution authority. Anti-churn POLICY_A is
ratified separately in §1.17 by the same Owner-GO.

```text
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
OPEN_DECISION_07_CLOSED=true
OPEN_DECISION_07_CLOSE_CLASS=CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_ARE_NOT_DURABLE_CANONICAL_STATE=true
ROTATION_DELTAS_DURABLE_STAGE_FORBIDDEN=true
STORED_ROTATION_DELTA_IS_CANONICAL_AUTHORITY=false
ROTATION_ROLE=MEMBERSHIP_DIFF_ONLY
ROTATION_IS_NOT_ANTI_CHURN=true
ROTATION_IS_NOT_PENDING=true
NAMED_GRAPH_NODE_IS_NOT_STAGE_RATIFICATION=true
ROTATION_ENGINE=NOT_AUTHORIZED
ROTATION_POLICY_RATIFIED=false
STAGE_VS_DERIVED=CLOSED_DERIVED
PRIOR_MEMBERSHIP_REFERENCE_INFORMATION_CLASS=REQUIRED
PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=UNBOUND
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=UNPROVEN
DERIVED_DIFF_INPUTS=CURRENT_ORDERED_MEMBERSHIP_PLUS_PRIOR_MEMBERSHIP_REFERENCE
DERIVED_DIFF_OUTPUTS=ENTERED_EXITED_RETAINED
BOOTSTRAP_DIFF=ENTERED_EQUALS_CURRENT_EXITED_EMPTY_WHEN_NO_PRIOR
PRIOR_UNAVAILABLE=ROTATION_DELTA_UNREADABLE_FAIL_CLOSED_MEMBERSHIP_REMAINS
OD07_CLOSE_DOES_NOT_MATERIALIZE=true
OD07_CLOSE_DOES_NOT_BIND_SCHEMA=true
OD07_CLOSE_DOES_NOT_AUTHORIZE_RUNTIME=true
```

The named graph node `Membership Rotation` remains topology, not a
ratified stage. Rotation remains membership-diff-only. `rotation_deltas`
are the deterministic set-diff of current ordered membership versus the
prior membership referenced by the required prior-membership
information class. Durable stored deltas are **not** canonical
authority. If a later schema materializes a derived view, that view
must not become a second membership truth.

Bootstrap: when no prior artifact exists, the derived diff is
entered=current, exited=empty, retained=empty. That is derivation
against an empty prior, **not** a stage.

If the prior reference is unavailable or unreadable, the rotation
delta is `UNREADABLE` / fail-closed. Current membership remains valid when
the current artifact is otherwise integer. Silence must **not** infer
a rotation engine or a persisted stage.

Operative previous→current derived reading remains unavailable until
instance identity, temporal identity, and prior-reference schemas are
bound **and** a prior listing is proven. This close does **not** prove
those.

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
CLOSED_DECISIONS=OPEN_DECISION_01,OPEN_DECISION_02,OPEN_DECISION_03,OPEN_DECISION_04,OPEN_DECISION_05,OPEN_DECISION_06,OPEN_DECISION_07
```

```text
TOP20_CANDIDATE_CONTEXT
→ CAP22_ORDER_CONSUMED_AS_MEMBERSHIP_ORDER
→ MF_SELECTOR
→ AT_MOST_N
→ OD01_CLOSED_NUMERIC_CEILING_N5
→ ACTIVE_SET_N
→ OD07_CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
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
| `OPEN_DECISION_07` | `CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY` | `true` |
| `OPEN_DECISION_06` | `CLOSED_ALLOW_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_PERSISTENCE_WHILE_G13_CLOSED` | `true` |

A later close of one node does **not** close a neighbor by inference.
This persist records that `OPEN_DECISION_06` is closed as Owner-policy
permission `ALLOWED` under `NON_AUTHORITATIVE_ONLY` while G13 remains
closed. `OPEN_DECISION_07` is closed in §1.6 as
`CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY`. A later close of one node
does **not** close a neighbor by inference. The OD06 permission close
does **not** prove artifact existence, does **not** reopen
`OPEN_DECISION_01`, `OPEN_DECISION_04`, or `OPEN_DECISION_05`, does
**not** create a `TOP5` product, and does **not** prove `EXACTLY_5`.

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
→ CREATION_AUTHORIZED_SEMANTICS_PERMISSION_BIT_ONLY
→ NEXT_CANONICAL_DECISION_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
→ DECISION_CLASS_CLOSED_SET_CREATION_AUTHORIZED_TRUE_PERMISSION_BIT_ONLY
→ NEXT_CANONICAL_DECISION_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
→ DECISION_CLASS_CLOSED_SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE
→ PRIOR_MEMBERSHIP_LISTING_UNPROVEN
→ OD07_CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
```

After the §1.12 predicate persist, `CREATION_AUTHORIZED` remained `false`.
That bit was **not** set true there. Creation-authorization **semantics**
are bound as `PERMISSION_BIT_ONLY`. Schema, writer, reader, OD07, and
anti-churn are **not required** before `CREATION_AUTHORIZED=true`. That
membership is **not** a bind of those items. Bootstrap, identity schemas,
prior listing, provenance mapping, durability semantics, provenance
semantics, and lifecycle remain unbound and are **not** decided here.
Instance existence remains `UNPROVEN`. That status is **not** `ABSENT`.
Permission-bit semantics are **not** materialization authority. OD06
`ALLOWED` is **not** `CREATION_AUTHORIZED`. The §1.12 persist did **not**
name a next canonical decision. Owner-GO
`OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_CLASS_V1`
named that later decision in §1.13 as
`MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1`. Naming the class
did **not** set `CREATION_AUTHORIZED=true` and was **not** an automatic
next step. Owner-GO
`OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1`
closes that class in §1.14 as `SET_CREATION_AUTHORIZED_TRUE`.
`CREATION_AUTHORIZED` is `true` as permission-bit only. That true is
**not** materialization, **not** artifact instance, **not** create-now,
and **not** an automatic next step. The §1.14 persist did **not** name
a next canonical decision. Owner-GO
`OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_CLASS_V1`
names that later decision in §1.15 as
`MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1`.
Naming the class does **not** grant materialization authority, does
**not** create an artifact, and is **not** an automatic next step.
Owner-GO
`OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1`
closes that class in §1.16 as `SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE`.
`MATERIALIZATION_AUTHORITY_GRANTED` is `true` as grant only. That grant
is **not** materialization, **not** artifact creation, **not**
instance proof, and **not** an automatic next step. The §1.16 persist
does **not** name a next canonical decision.

```text
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
CREATION_AUTHORIZED=true
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
NEXT_STEP_IS_AUTOMATIC=false
SCHEMA_NOT_AUTO_NEXT=true
WRITER_NOT_AUTO_NEXT=true
READER_NOT_AUTO_NEXT=true
PRIOR_LISTING_NOT_AUTO_NEXT=true
OD07_NOT_AUTO_NEXT=true
SCHEMA_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
WRITER_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
READER_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
OD07_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
ANTI_CHURN_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
CLOSED_DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
CLOSED_DECISION_CLASS_REMAINS=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
PRIOR_CLASS_REMAINS_CLOSED=true
OWNER_DECISION=SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE
DECISION_CLASS_BIND_DOES_NOT_SET_CREATION_AUTHORIZED_TRUE=true
DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
DECISION_SCOPE=OWNER_DECIDES_MATERIALIZATION_AUTHORITY_GRANTED_TRUE_OR_FALSE_UNDER_EXISTING_PERMISSION_BIT_ONLY_SEMANTICS
DECISION_CLASS_BOUND=true
DECISION_CLASS_CLOSED=true
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
CLASS_BIND_IS_NOT_SUBSTANCE_CLOSE=true
CLASS_BIND_DOES_NOT_SET_MATERIALIZATION_AUTHORITY_TRUE=true
MATERIALIZATION_AUTHORITY_GRANTED=true
GRANT_IS_NOT_MATERIALIZATION=true
GRANT_IS_NOT_ARTIFACT_CREATION=true
GRANT_IS_NOT_INSTANCE_PROOF=true
GRANT_DOES_NOT_BIND_SCHEMA_WRITER_READER=true
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
OPEN_DECISION_07_CLOSED=true
OD07_EFFECT=CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
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
RETAINED_ENTERED_EXITED_PERSISTED_STAGE=FORBIDDEN_AS_DURABLE_CANONICAL_STATE
ROTATION_DELTAS_STAGE_VS_DERIVED=CLOSED_DERIVED
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_ARE_NOT_DURABLE_CANONICAL_STATE=true
ROTATION_DELTAS_DURABLE_STAGE_FORBIDDEN=true
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
OPEN_DECISION_07_CLOSED=true
OPEN_DECISION_07_CLOSE_CLASS=CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
ANTI_CHURN_POLICY_RATIFIED=true
ANTI_CHURN_POLICY_STATUS=RATIFIED
HYSTERESIS_IS_RATIFIED_RULE=true
MIN_HOLDING_IS_RATIFIED_RULE=true
CHALLENGER_MARGIN_TYPE=RANK
CHALLENGER_MARGIN_VALUE=1
HYSTERESIS_CONFIRMATION_COUNT=1
CONSECUTIVE_CONFIRMATION_COUNT=1
REPLACEMENT_PENDING_INDEPENDENT_STATE=FORBIDDEN_UNDER_CURRENT_OD05
SSF_REPLACEMENT_PENDING_IMPORTED=false
EXECUTION_FIELDS_INSIDE_MEMBERSHIP_ARTIFACT_IDENTITY=FORBIDDEN
ORDER_POSITION_VENUE_FIELDS_INSIDE_MEMBERSHIP_ARTIFACT_IDENTITY=FORBIDDEN
G13_UNLOCK=false
EXECUTION_AUTHORITY_EFFECT=NONE
```

`rotation_deltas` remains membership-change-only as **named**
isolated-domain semantics. Stage versus derived is closed in §1.6 as
`DERIVED`. Retained / entered / exited are **not** a persisted stage
and **must not** be durable canonical state. They are the derived
diff outputs of current ordered membership versus prior membership.
Operative derivation still requires a proven prior listing and bound
prior-reference schema. Prior listing existence remains `UNPROVEN`.
Durable artifact instance existence remains `UNPROVEN`.

Anti-churn POLICY_A is ratified in §1.17. Hysteresis, minimum holding,
rank margin, and consecutive confirmation are selector-owned
**rules** under that policy. OD05 remains
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
OVERREAD_AS_RETAINED_ENTERED_EXITED_PERSISTED_STAGE=FORBIDDEN
OVERREAD_AS_RETAINED_ENTERED_EXITED_NOW_OPERATIVELY_DERIVABLE_WHILE_PRIOR_UNPROVEN=FORBIDDEN
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

### 1.12 Isolated membership-context artifact creation-authorization predicate and precondition membership

Owner-GO
`OWNER_GO_MF_CREATION_AUTHORIZATION_PREDICATE_AND_PRECONDITION_MEMBERSHIP_V1`
binds the **creation-authorization predicate** and **precondition
membership** as Owner-policy principle only. Prior fail-closed
**boundaries** from OD06 §1.7, semantic identity §1.9, existence class
§1.10, and instance census §1.11 remain binding. Those binds are **not**
re-owned here.

This persist does **not** set `CREATION_AUTHORIZED=true`. It does
**not** create an artifact instance. It does **not** bind a schema,
writer, or reader. It does **not** prove prior-listing existence, does
**not** close `OPEN_DECISION_07`, does **not** ratify anti-churn policy,
does **not** bind durability or provenance semantics, does **not**
unlock G13, and does **not** grant runtime, execution, or
materialization authority.

Owner decision:
`PERMISSION_BIT_WITHOUT_SCHEMA_WRITER_READER_OD07_ANTI_CHURN_PRECONDITION`.

```text
OWNER_GO=OWNER_GO_MF_CREATION_AUTHORIZATION_PREDICATE_AND_PRECONDITION_MEMBERSHIP_V1
OWNER_DECISION=PERMISSION_BIT_WITHOUT_SCHEMA_WRITER_READER_OD07_ANTI_CHURN_PRECONDITION
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
CREATION_AUTHORIZED=false
CREATION_AUTHORIZED_TRUE_MEANS=LATER_MATERIALIZATION_OF_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT_IS_PERMITTED_SUBJECT_TO_SEPARATE_MATERIALIZATION_AUTHORITY
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=ARTIFACT_INSTANCE_EXISTS
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=CREATE_NOW
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=SCHEMA_BOUND
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=WRITER_BOUND
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=READER_BOUND
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=OD07_CLOSED
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=ANTI_CHURN_RATIFIED
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=RUNTIME_AUTHORIZED
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=EXECUTION_AUTHORITY_GRANTED
SCHEMA=NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE
WRITER=NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE
READER=NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE
OD07=NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE
ANTI_CHURN=NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE
BOOTSTRAP=REMAINS_UNBOUND_NOT_DECIDED_HERE
INSTANCE_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
TEMPORAL_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_REFERENCE_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_MEMBERSHIP_LISTING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CAP22_PROVENANCE_MAPPING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_DURABILITY_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_PROVENANCE_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
LIFECYCLE=REMAINS_UNBOUND_NOT_DECIDED_HERE
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
UNPROVEN_IS_NOT_ABSENT=true
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
OD07_STATUS=UNCLOSED
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
G13_UNLOCK=false
RUNTIME_AUTHORIZED=false
EXECUTION_AUTHORITY_EFFECT=NONE
NEXT_STEP_IS_AUTOMATIC=false
```

`CREATION_AUTHORIZED` remains `false`. Binding the predicate is **not**
setting the permission bit true. OD06 `ALLOWED` is **not**
`CREATION_AUTHORIZED`. Permission-bit semantics are **not**
materialization authority. Required class is **not** instance and
**not** create-now. `UNPROVEN` is **not** `ABSENT`. Selector-owned
durable membership store remains `NOT_AUTHORIZED`.

Schema, writer, reader, OD07, and anti-churn are **not required**
before a later Owner-GO may set `CREATION_AUTHORIZED=true`. That
membership is **not** a bind of those items and is **not** an
auto-next. Bootstrap, instance-identity schema, temporal-identity
schema, prior-reference schema, prior membership listing, Cap-2.2
provenance mapping, canonical durability semantics, canonical
provenance semantics, and lifecycle remain unbound and are **not**
decided here. Existing tokens `INSTANCE_ID_SCHEMA=UNBOUND`,
`TEMPORAL_SCHEMA=UNBOUND`, `PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=UNBOUND`,
and `PRIOR_MEMBERSHIP_LISTING_STATUS=UNPROVEN` remain unchanged.

This persist does **not** name a next canonical decision. A later
Owner-GO must name it.

Fail-closed after this predicate persist:

```text
OVERREAD_AS_PREDICATE_EQUALS_CREATION_AUTHORIZED_TRUE=FORBIDDEN
OVERREAD_AS_PERMISSION_BIT_EQUALS_MATERIALIZATION=FORBIDDEN
OVERREAD_AS_PERMISSION_BIT_EQUALS_INSTANCE_EXISTS=FORBIDDEN
OVERREAD_AS_PERMISSION_BIT_EQUALS_CREATE_NOW=FORBIDDEN
OVERREAD_AS_PERMISSION_BIT_EQUALS_SCHEMA_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_PERMISSION_BIT_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_PERMISSION_BIT_EQUALS_ANTI_CHURN_RATIFICATION=FORBIDDEN
OVERREAD_AS_OD06_ALLOWED_EQUALS_CREATION_AUTHORIZED=FORBIDDEN
OVERREAD_AS_NOT_REQUIRED_BEFORE_EQUALS_BOUND=FORBIDDEN
OVERREAD_AS_NOT_REQUIRED_BEFORE_EQUALS_DECIDED=FORBIDDEN
OVERREAD_AS_UNPROVEN_EQUALS_ABSENT=FORBIDDEN
OVERREAD_AS_REQUIRED_CLASS_EQUALS_CREATE_NOW=FORBIDDEN
OVERREAD_AS_PREDICATE_EQUALS_G13_UNLOCK=FORBIDDEN
```

### 1.13 Isolated membership-context artifact creation-authorized permission-bit decision class

Owner-GO
`OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_CLASS_V1`
names the **next canonical decision class** for the later Owner
decision whether `CREATION_AUTHORIZED` remains `false` or is set
`true` under the already-bound `PERMISSION_BIT_ONLY` semantics.
Prior fail-closed **boundaries** from OD06 §1.7, semantic identity
§1.9, existence class §1.10, instance census §1.11, and creation-
authorization predicate §1.12 remain binding. Those binds are **not**
re-owned here.

This persist does **not** set `CREATION_AUTHORIZED=true`. It does
**not** choose true or false. It does **not** grant materialization
authority. It does **not** create an artifact instance. It does **not**
bind a schema, writer, or reader. It does **not** close
`OPEN_DECISION_07`, does **not** ratify anti-churn policy, does **not**
bind bootstrap, durability, or provenance semantics, does **not**
unlock G13, and does **not** grant runtime or execution authority.

The §1.12 persist did **not** name a next canonical decision. This
Owner-GO names it.

```text
OWNER_GO=OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_CLASS_V1
NEXT_CANONICAL_DECISION=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
DECISION_SCOPE=OWNER_DECIDES_CREATION_AUTHORIZED_TRUE_OR_FALSE_UNDER_EXISTING_PERMISSION_BIT_ONLY_SEMANTICS
DECISION_CLASS_BOUND=true
DECISION_CLASS_BIND_DOES_NOT_SET_CREATION_AUTHORIZED_TRUE=true
MATERIALIZATION_AUTHORITY_GRANTED=false
ARTIFACT_INSTANCE_CREATED=false
SCHEMA_BOUND_UNCHANGED=true
WRITER_BOUND_UNCHANGED=true
READER_BOUND_UNCHANGED=true
OD07_STATUS_UNCHANGED=true
ANTI_CHURN_POLICY_STATUS_UNCHANGED=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
EXECUTION_AUTHORITY_EFFECT=NONE
NEXT_STEP_IS_AUTOMATIC=false
CREATION_AUTHORIZED=false
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
UNPROVEN_IS_NOT_ABSENT=true
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
OD07_STATUS=UNCLOSED
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
G13_UNLOCK=false
RUNTIME_AUTHORIZED=false
BOOTSTRAP=REMAINS_UNBOUND_NOT_DECIDED_HERE
INSTANCE_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
TEMPORAL_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_REFERENCE_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_MEMBERSHIP_LISTING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CAP22_PROVENANCE_MAPPING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_DURABILITY_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_PROVENANCE_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
LIFECYCLE=REMAINS_UNBOUND_NOT_DECIDED_HERE
```

Naming the class is **not** setting the permission bit true. The
already-bound `PERMISSION_BIT_ONLY` semantics are **not** re-bound
here. Schema, writer, reader, OD07, and anti-churn remain **not
required** before a later Owner-GO may set `CREATION_AUTHORIZED=true`.
That membership is **not** a bind of those items. The nine
`REMAINS_UNBOUND_NOT_DECIDED_HERE` items from §1.12 remain unbound and
are **not** decided here. Instance existence remains `UNPROVEN`.
`UNPROVEN` is **not** `ABSENT`. Permission-bit semantics remain **not**
materialization authority.

A later Owner-GO that actually sets `CREATION_AUTHORIZED` true or
leaves it false must name this class. That later GO is **not**
authorized here. `NEXT_STEP_IS_AUTOMATIC` remains `false`.

Fail-closed after this decision-class bind:

```text
OVERREAD_AS_DECISION_CLASS_EQUALS_CREATION_AUTHORIZED_TRUE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_TRUE_OR_FALSE_CHOICE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_MATERIALIZATION=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_ARTIFACT_INSTANCE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_SCHEMA_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_ANTI_CHURN_RATIFICATION=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_BOOTSTRAP_OR_DURABILITY=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_NAMING_EQUALS_AUTO_NEXT=FORBIDDEN
```

### 1.14 Isolated membership-context artifact creation-authorized permission-bit decision

Owner-GO
`OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1`
closes the named decision class
`MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1` as Owner-policy
`SET_CREATION_AUTHORIZED_TRUE` under the already-bound
`PERMISSION_BIT_ONLY` semantics. Prior fail-closed **boundaries** from
OD06 §1.7, semantic identity §1.9, existence class §1.10, instance
census §1.11, creation-authorization predicate §1.12, and decision-class
bind §1.13 remain binding. Those binds are **not** re-owned here.

This persist sets `CREATION_AUTHORIZED=true` as permission-bit only.
It does **not** grant materialization authority. It does **not** create
an artifact instance. It does **not** prove instance existence. It does
**not** bind a schema, writer, or reader. It does **not** bind
bootstrap, durability, provenance, or lifecycle. It does **not** close
`OPEN_DECISION_07`, does **not** ratify anti-churn policy, does **not**
change numeric `N`, does **not** unlock G13, and does **not** grant
runtime, execution, live, or canary authority. It does **not** name a
next canonical decision. `NEXT_STEP_IS_AUTOMATIC` remains `false`.

The §1.13 persist named the class and did **not** choose true or false.
This Owner-GO names that class and chooses `true`.

```text
OWNER_GO=OWNER_GO_MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
DECISION_CLASS=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
CLOSED_DECISION_CLASS=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
DECISION_CLASS_BOUND=true
DECISION_CLASS_CLOSED=true
OWNER_DECISION=SET_CREATION_AUTHORIZED_TRUE
DECISION_SCOPE=OWNER_DECIDES_CREATION_AUTHORIZED_TRUE_OR_FALSE_UNDER_EXISTING_PERMISSION_BIT_ONLY_SEMANTICS
CREATION_AUTHORIZED=true
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
DECISION_CLASS_BIND_DOES_NOT_SET_CREATION_AUTHORIZED_TRUE=true
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
MATERIALIZATION_AUTHORITY_GRANTED=false
ARTIFACT_INSTANCE_CREATED=false
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
SCHEMA_BOUND_UNCHANGED=true
WRITER_BOUND_UNCHANGED=true
READER_BOUND_UNCHANGED=true
OD07_STATUS=UNCLOSED
OPEN_DECISION_07_CLOSED=false
OD07_STATUS_UNCHANGED=true
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
ANTI_CHURN_POLICY_STATUS_UNCHANGED=true
RUNTIME_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EXECUTION_AUTHORITY_EFFECT=NONE
NEXT_STEP_IS_AUTOMATIC=false
G13_UNLOCK=false
CREATION_AUTHORIZED_TRUE_MEANS=LATER_MATERIALIZATION_OF_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT_IS_PERMITTED_SUBJECT_TO_SEPARATE_MATERIALIZATION_AUTHORITY
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=ARTIFACT_INSTANCE_EXISTS
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=CREATE_NOW
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=SCHEMA_BOUND
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=WRITER_BOUND
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=READER_BOUND
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=OD07_CLOSED
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=ANTI_CHURN_RATIFIED
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=RUNTIME_AUTHORIZED
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=EXECUTION_AUTHORITY_GRANTED
CREATION_AUTHORIZED_TRUE_DOES_NOT_MEAN=MATERIALIZATION_AUTHORITY_GRANTED
BOOTSTRAP=REMAINS_UNBOUND_NOT_DECIDED_HERE
INSTANCE_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
TEMPORAL_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_REFERENCE_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_MEMBERSHIP_LISTING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CAP22_PROVENANCE_MAPPING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_DURABILITY_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_PROVENANCE_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
LIFECYCLE=REMAINS_UNBOUND_NOT_DECIDED_HERE
```

`CREATION_AUTHORIZED=true` is permission-bit only. Permission-bit
semantics remain **not** materialization authority. Required class is
**not** instance and **not** create-now. Instance existence remains
`UNPROVEN`. `UNPROVEN` is **not** `ABSENT`. The §1.11 census persist
remains the instance-existence census (`NO_INSTANCE_PROOF_FOUND`).
That census class name is **not** the current permission bit. Schema,
writer, reader, OD07, and anti-churn remain unbound / unclosed /
unratified and are **not** decided here. The nine
`REMAINS_UNBOUND_NOT_DECIDED_HERE` items from §1.12 remain unbound.
A later materialization Owner-GO is **not** authorized here.

Fail-closed after this permission-bit close:

```text
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_MATERIALIZATION=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_ARTIFACT_INSTANCE=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_CREATE_NOW=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_INSTANCE_EXISTS=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_SCHEMA_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_ANTI_CHURN_RATIFICATION=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_BOOTSTRAP_OR_DURABILITY=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_RUNTIME=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_EXECUTION=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_AUTO_NEXT=FORBIDDEN
OVERREAD_AS_CENSUS_CLASS_NAME_EQUALS_CURRENT_BIT_FALSE=FORBIDDEN
OVERREAD_AS_THIS_CLOSE_NAMES_A_NEXT_CANONICAL_DECISION=FORBIDDEN
```

### 1.15 Isolated membership-context artifact materialization-authority decision class

Owner-GO
`OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_CLASS_V1`
names the **next canonical decision class** for the later Owner
decision whether `MATERIALIZATION_AUTHORITY_GRANTED` remains `false`
or is set `true` under the already-true `PERMISSION_BIT_ONLY`
semantics. Prior fail-closed **boundaries** from OD06 §1.7, semantic
identity §1.9, existence class §1.10, instance census §1.11,
creation-authorization predicate §1.12, permission-bit decision-class
bind §1.13, and permission-bit close §1.14 remain binding. Those binds
are **not** re-owned here.

This persist does **not** set `MATERIALIZATION_AUTHORITY_GRANTED=true`.
It does **not** choose true or false. It does **not** create an
artifact instance. It does **not** prove instance existence. It does
**not** bind a schema, writer, or reader. It does **not** close
`OPEN_DECISION_07`, does **not** ratify anti-churn policy, does **not**
bind bootstrap, durability, or provenance semantics, does **not**
unlock G13, and does **not** grant runtime or execution authority.
`CREATION_AUTHORIZED` remains `true` as permission-bit only. The
named class `MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1`
remains closed as `SET_CREATION_AUTHORIZED_TRUE`.

The §1.14 persist did **not** name a next canonical decision. This
Owner-GO names it.

```text
OWNER_GO=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_CLASS_V1
DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
DECISION_SCOPE=OWNER_DECIDES_MATERIALIZATION_AUTHORITY_GRANTED_TRUE_OR_FALSE_UNDER_EXISTING_PERMISSION_BIT_ONLY_SEMANTICS
DECISION_CLASS_BOUND=true
DECISION_CLASS_CLOSED=false
NEXT_CANONICAL_DECISION=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
THIS_PERSIST_NAMES_A_NEXT_CANONICAL_DECISION=true
NEXT_STEP_IS_AUTOMATIC=false
CLASS_BIND_IS_NOT_SUBSTANCE_CLOSE=true
CLASS_BIND_DOES_NOT_SET_MATERIALIZATION_AUTHORITY_TRUE=true
CLASS_BIND_DOES_NOT_MATERIALIZE=true
CLASS_BIND_DOES_NOT_CREATE_ARTIFACT=true
CLASS_BIND_DOES_NOT_BIND_SCHEMA_WRITER_READER=true
CLASS_BIND_DOES_NOT_CLOSE_OD07=true
CLASS_BIND_DOES_NOT_RATIFY_ANTI_CHURN=true
PRIOR_CLASS_REMAINS_CLOSED=true
CLOSED_DECISION_CLASS=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
OWNER_DECISION=SET_CREATION_AUTHORIZED_TRUE
DECISION_CLASS_BIND_DOES_NOT_SET_CREATION_AUTHORIZED_TRUE=true
CREATION_AUTHORIZED=true
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
MATERIALIZATION_AUTHORITY_GRANTED=false
ARTIFACT_INSTANCE_CREATED=false
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
SCHEMA_BOUND_UNCHANGED=true
WRITER_BOUND_UNCHANGED=true
READER_BOUND_UNCHANGED=true
OD07_STATUS=UNCLOSED
OPEN_DECISION_07_CLOSED=false
OD07_STATUS_UNCHANGED=true
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
ANTI_CHURN_POLICY_STATUS_UNCHANGED=true
RUNTIME_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EXECUTION_AUTHORITY_EFFECT=NONE
G13_UNLOCK=false
BOOTSTRAP=REMAINS_UNBOUND_NOT_DECIDED_HERE
INSTANCE_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
TEMPORAL_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_REFERENCE_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_MEMBERSHIP_LISTING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CAP22_PROVENANCE_MAPPING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_DURABILITY_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_PROVENANCE_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
LIFECYCLE=REMAINS_UNBOUND_NOT_DECIDED_HERE
```

Naming the class is **not** granting materialization authority. The
already-true `PERMISSION_BIT_ONLY` semantics are **not** re-bound
here. Permission-bit true remains **not** materialization, **not**
create-now, and **not** instance existence. Schema, writer, reader,
OD07, and anti-churn remain unbound / unclosed / unratified and are
**not** decided here. The nine `REMAINS_UNBOUND_NOT_DECIDED_HERE`
items from §1.12 remain unbound. Instance existence remains `UNPROVEN`.
`UNPROVEN` is **not** `ABSENT`.

A later Owner-GO that actually sets `MATERIALIZATION_AUTHORITY_GRANTED`
true or leaves it false must name this class. That later GO is **not**
authorized here. `NEXT_STEP_IS_AUTOMATIC` remains `false`.

Fail-closed after this decision-class bind:

```text
OVERREAD_AS_DECISION_CLASS_EQUALS_MATERIALIZATION_AUTHORITY_TRUE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_TRUE_OR_FALSE_CHOICE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_CREATE_NOW=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_ARTIFACT_INSTANCE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_SCHEMA_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_ANTI_CHURN_RATIFICATION=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_BOOTSTRAP_OR_DURABILITY=FORBIDDEN
OVERREAD_AS_DECISION_CLASS_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_NAMING_EQUALS_AUTO_NEXT=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_THIS_CLASS_GRANT=FORBIDDEN
OVERREAD_AS_PRIOR_CLASS_REOPENED=FORBIDDEN
```

### 1.16 Isolated membership-context artifact materialization-authority decision

Owner-GO
`OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1`
closes the named decision class
`MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1`
as Owner-policy `SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE` under
the already-true `PERMISSION_BIT_ONLY` semantics. Prior fail-closed
**boundaries** from OD06 §1.7, semantic identity §1.9, existence class
§1.10, instance census §1.11, creation-authorization predicate §1.12,
permission-bit decision-class bind §1.13, permission-bit close §1.14,
and decision-class bind §1.15 remain binding. Those binds are **not**
re-owned here.

This persist sets `MATERIALIZATION_AUTHORITY_GRANTED=true` as grant
only. It does **not** materialize. It does **not** create an artifact
instance. It does **not** prove instance existence. It does **not**
bind a schema, writer, or reader. It does **not** bind bootstrap,
durability, provenance, or lifecycle. It does **not** close
`OPEN_DECISION_07`, does **not** ratify anti-churn policy, does **not**
change numeric `N`, does **not** unlock G13, and does **not** grant
runtime, execution, live, or canary authority. It does **not** name a
next canonical decision. `NEXT_STEP_IS_AUTOMATIC` remains `false`.
`CREATION_AUTHORIZED` remains `true` as permission-bit only. The
named class `MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1`
remains closed as `SET_CREATION_AUTHORIZED_TRUE`.

The §1.15 persist named the class and did **not** choose true or false.
This Owner-GO names that class and chooses `true`.

```text
OWNER_GO=OWNER_GO_MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
OWNER_DECISION=SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE
DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
DECISION_SCOPE=OWNER_DECIDES_MATERIALIZATION_AUTHORITY_GRANTED_TRUE_OR_FALSE_UNDER_EXISTING_PERMISSION_BIT_ONLY_SEMANTICS
DECISION_CLASS_BOUND=true
DECISION_CLASS_CLOSED=true
CLOSED_DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
CLOSED_DECISION_CLASS_REMAINS=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
PRIOR_CLASS_REMAINS_CLOSED=true
MATERIALIZATION_AUTHORITY_GRANTED=true
CREATION_AUTHORIZED=true
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
DECISION_CLASS_BIND_DOES_NOT_SET_CREATION_AUTHORIZED_TRUE=true
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
NEXT_STEP_IS_AUTOMATIC=false
GRANT_IS_NOT_MATERIALIZATION=true
GRANT_IS_NOT_ARTIFACT_CREATION=true
GRANT_IS_NOT_INSTANCE_PROOF=true
GRANT_DOES_NOT_BIND_SCHEMA_WRITER_READER=true
GRANT_DOES_NOT_CLOSE_OD07=true
GRANT_DOES_NOT_RATIFY_ANTI_CHURN=true
GRANT_DOES_NOT_AUTHORIZE_RUNTIME=true
GRANT_DOES_NOT_AUTHORIZE_EXECUTION=true
ARTIFACT_INSTANCE_CREATED=false
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=NO_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
SCHEMA_BOUND_UNCHANGED=true
WRITER_BOUND_UNCHANGED=true
READER_BOUND_UNCHANGED=true
OD07_STATUS=UNCLOSED
OPEN_DECISION_07_CLOSED=false
OD07_STATUS_UNCHANGED=true
ANTI_CHURN_POLICY_STATUS=UNRATIFIED
ANTI_CHURN_POLICY_STATUS_UNCHANGED=true
RUNTIME_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EXECUTION_AUTHORITY_EFFECT=NONE
G13_UNLOCK=false
GRANT_TRUE_MEANS=SEPARATE_MATERIALIZATION_AUTHORITY_GRANTED_UNDER_EXISTING_PERMISSION_BIT_ONLY
GRANT_TRUE_DOES_NOT_MEAN=ARTIFACT_INSTANCE_EXISTS
GRANT_TRUE_DOES_NOT_MEAN=CREATE_NOW
GRANT_TRUE_DOES_NOT_MEAN=SCHEMA_BOUND
GRANT_TRUE_DOES_NOT_MEAN=WRITER_BOUND
GRANT_TRUE_DOES_NOT_MEAN=READER_BOUND
GRANT_TRUE_DOES_NOT_MEAN=OD07_CLOSED
GRANT_TRUE_DOES_NOT_MEAN=ANTI_CHURN_RATIFIED
GRANT_TRUE_DOES_NOT_MEAN=RUNTIME_AUTHORIZED
GRANT_TRUE_DOES_NOT_MEAN=EXECUTION_AUTHORITY_GRANTED
BOOTSTRAP=REMAINS_UNBOUND_NOT_DECIDED_HERE
INSTANCE_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
TEMPORAL_IDENTITY_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_REFERENCE_SCHEMA=REMAINS_UNBOUND_NOT_DECIDED_HERE
PRIOR_MEMBERSHIP_LISTING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CAP22_PROVENANCE_MAPPING=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_DURABILITY_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
CANONICAL_PROVENANCE_SEMANTICS=REMAINS_UNBOUND_NOT_DECIDED_HERE
LIFECYCLE=REMAINS_UNBOUND_NOT_DECIDED_HERE
```

`MATERIALIZATION_AUTHORITY_GRANTED=true` is grant only. Grant remains
**not** materialization and **not** create-now. Required class is
**not** instance. Instance existence remains `UNPROVEN`. `UNPROVEN`
is **not** `ABSENT`. The §1.11 census persist remains the
instance-existence census (`NO_INSTANCE_PROOF_FOUND`). Schema,
writer, reader, OD07, and anti-churn remain unbound / unclosed /
unratified and are **not** decided here. The nine
`REMAINS_UNBOUND_NOT_DECIDED_HERE` items from §1.12 remain unbound.
A later materialization or create Owner-GO is **not** authorized here.

Fail-closed after this grant close:

```text
OVERREAD_AS_GRANT_EQUALS_MATERIALIZATION=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_ARTIFACT_INSTANCE=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_CREATE_NOW=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_INSTANCE_EXISTS=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_SCHEMA_WRITER_OR_READER=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_OD07_CLOSE=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_ANTI_CHURN_RATIFICATION=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_BOOTSTRAP_OR_DURABILITY=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_RUNTIME=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_EXECUTION=FORBIDDEN
OVERREAD_AS_GRANT_EQUALS_AUTO_NEXT=FORBIDDEN
OVERREAD_AS_THIS_CLOSE_NAMES_A_NEXT_CANONICAL_DECISION=FORBIDDEN
OVERREAD_AS_PRIOR_CLASS_REOPENED=FORBIDDEN
```

### 1.17 Isolated anti-churn POLICY_A persist

Owner-GO
`OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1`
ratifies isolated-MF anti-churn **POLICY_A** as selector-owned
admission rules. The same Owner-GO closes `OPEN_DECISION_07` in §1.6.
Prior fail-closed **boundaries** from OD05 §1.5, OD06 §1.7, semantic
identity §1.9, and the materialization-authority grant §1.16 remain
binding. Those binds are **not** re-owned here.

This persist does **not** materialize an artifact. It does **not**
bind schema, writer, or reader. It does **not** implement the
selector. It does **not** import Cap 2.3 / SSF numerics or state
machines. It does **not** ratify cooldown or turnover. It does
**not** unlock G13 and does **not** grant runtime or execution
authority. It does **not** name a next canonical decision.
`NEXT_STEP_IS_AUTOMATIC` remains `false`.

```text
OWNER_GO=OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1
SELECTED_ANTI_CHURN_POLICY=POLICY_A
ANTI_CHURN_POLICY_STATUS=RATIFIED
ANTI_CHURN_OWNER=SELECTOR
HYSTERESIS_IS_RATIFIED_RULE=true
HYSTERESIS_MODE=RANK_IMPROVEMENT_VS_DISPLACED_INCUMBENT
CHALLENGER_MARGIN_TYPE=RANK
CHALLENGER_MARGIN_VALUE=1
MINIMUM_HOLDING_UNIT=RANKING_OBSERVATIONS
MINIMUM_HOLDING_VALUE=2
MINIMUM_HOLDING_IS_NOT_POSITION_HOLDING=true
CONSECUTIVE_CONFIRMATION_COUNT=1
MULTIPLE_REPLACEMENTS_PER_CYCLE=true
TIE_BREAK=CAP22_ORIGIN_CONSUMED_AS_MEMBERSHIP_ORDER
BOOTSTRAP_RULE=PREFIX_FILL_FROM_CAP22_ELIGIBLE_NO_ANTI_CHURN_NO_PADDING
FORCED_REMOVAL_RULE=ABSENT_OR_INELIGIBLE_BYPASSES_ANTI_CHURN
CARDINALITY_MODE=AT_MOST_N
N_VALUE=5
EXACTLY_5=false
NO_PADDING=true
TOP20_IS_CANDIDATE_CONTEXT_ONLY=true
MF_RERANKING_ALLOWED=false
MF_SCORING_RATIFIED=false
NO_INDEPENDENT_REPLACEMENT_PENDING_STATE_REQUIRED=true
REPLACEMENT_PENDING_INDEPENDENT_STATE=FORBIDDEN_UNDER_CURRENT_OD05
COOLDOWN_RATIFIED=false
TURNOVER_POLICY_RATIFIED=false
SSF_SEMANTICS_IMPORTED=false
FORCED_REMOVAL_PRECEDENCE=1
CARDINALITY_CEILING_PRECEDENCE=2
MIN_HOLDING_PRECEDENCE=3
CHALLENGER_QUALIFICATION_PRECEDENCE=4
RANK_HYSTERESIS_PRECEDENCE=5
CONSECUTIVE_CONFIRMATION_PRECEDENCE=6
DERIVED_ROTATION_DIFF_PRECEDENCE=7
UNDERFILLED_ACTIVE_SET_BEHAVIOR=PREFIX_FILL_TO_AT_MOST_N_FROM_ELIGIBLE_CAP22_ORDER
UNDERFILL_IS_NOT_REPLACEMENT=true
UNDERFILL_DOES_NOT_REQUIRE_REPLACEMENT_HYSTERESIS=true
CHALLENGER_REPLACEMENT_REQUIRES=ELIGIBLE_CHALLENGER_PLUS_UNPROTECTED_INCUMBENT_PLUS_RANK_MARGIN_PLUS_HOLD_RULE
FORCED_REMOVAL_BYPASSES_MIN_HOLD=true
FORCED_REMOVAL_BYPASSES_MARGIN=true
FORCED_REMOVAL_BYPASSES_CONFIRMATION=true
TIES_REQUIRE_NO_MF_TIE_BREAK=true
CAP22_TOTAL_ORDER_IS_CONSUMED=true
BOOTSTRAP_IS_NOT_ROTATION=true
CREATION_AUTHORIZED=true
MATERIALIZATION_AUTHORITY_GRANTED=true
ARTIFACT_INSTANCE_CREATED=false
ARTIFACT_INSTANCE_EXISTENCE=UNPROVEN
SCHEMA_BOUND=false
WRITER_BOUND=false
READER_BOUND=false
G13_UNLOCK=false
RUNTIME_AUTHORIZED=false
EXECUTION_AUTHORITY_EFFECT=NONE
HOST_JOIN=NOT_DESIGNED
HANDOFF_NOT_DESIGNED=true
DOES_NOT_IMPORT_CAP23=true
DOES_NOT_AUTHORIZE_MULTI_FUTURE_RUNTIME=true
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
NEXT_STEP_IS_AUTOMATIC=false
ANTI_CHURN_CLOSE_DOES_NOT_MATERIALIZE=true
ANTI_CHURN_CLOSE_DOES_NOT_BIND_SCHEMA=true
ANTI_CHURN_CLOSE_DOES_NOT_AUTHORIZE_RUNTIME=true
```

Bound meaning: a challenger in the current Cap-2.2 Top-20 candidate
context may replace an unprotected incumbent when rank-margin 1 and
minimum holding of 2 ranking observations are satisfied.
`CONSECUTIVE_CONFIRMATION_COUNT=1` means the current ranking
observation is sufficient; one-cycle oscillation is blocked by
minimum holding, not by a confirmation counter. Multiple qualifying
replacements may occur in one cycle. Underfill is prefix-fill from
eligible Cap-2.2 order, not replacement, and does not apply
replacement hysteresis. Forced ineligibility or absence from Top-20
removes the member and bypasses min-hold, margin, and confirmation.
Bootstrap prefix-fill is not rotation. Cooldown and turnover remain
unratified. Cap 2.3 values such as `hysteresis_rank_improvement=1`
and `min_holding_period_seconds=3600.0` remain Cap-2.3
`CANONICAL_AUTHORITY` / `HISTORICAL_STATE` and are **not** this
policy.

Fail-closed after this persist:

```text
OVERREAD_AS_POLICY_A_EQUALS_CAP23_IMPORT=FORBIDDEN
OVERREAD_AS_POLICY_A_EQUALS_RUNTIME=FORBIDDEN
OVERREAD_AS_POLICY_A_EQUALS_SCHEMA_OR_WRITER=FORBIDDEN
OVERREAD_AS_POLICY_A_EQUALS_ARTIFACT_INSTANCE=FORBIDDEN
OVERREAD_AS_POLICY_A_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_POLICY_A_EQUALS_SCORE_MARGIN=FORBIDDEN
OVERREAD_AS_POLICY_A_EQUALS_COOLDOWN_OR_TURNOVER=FORBIDDEN
OVERREAD_AS_CONFIRMATION_COUNT_1_EQUALS_NO_MIN_HOLD=FORBIDDEN
OVERREAD_AS_THIS_CLOSE_NAMES_A_NEXT_CANONICAL_DECISION=FORBIDDEN
OVERREAD_AS_PADDING_TO_EXACTLY_5=FORBIDDEN
```

### 1.18 Isolated membership-context artifact contract and first durable instance

Owner-GO
`OWNER_GO_WP_MF_02_ARTIFACT_CONTRACT_AND_FIRST_DURABLE_INSTANCE_V1`
binds the membership-context artifact **schema**, **canonical
durability**, **provenance mapping**, **minimal lifecycle**, **writer**,
and **reader**, and materializes the first valid bootstrap instance.
Prior OD06 permission, existence class, creation-authorized bit,
materialization grant, OD07 derived identity, and POLICY_A remain
binding. Those binds are **not** re-owned here.

This persist does **not** implement selector runtime, does **not**
implement rotation runtime, does **not** apply anti-churn replacement,
does **not** re-rank, does **not** unlock G13, and does **not** grant
host-join, execution, or runtime authority. It does **not** name a next
canonical decision. `rotation_deltas` remain derived and are **not**
durable canonical state.

```text
OWNER_GO=OWNER_GO_WP_MF_02_ARTIFACT_CONTRACT_AND_FIRST_DURABLE_INSTANCE_V1
ARTIFACT_TYPE=MF_MEMBERSHIP_CONTEXT_V1
ARTIFACT_SCHEMA_VERSION=mf_membership_context.v1
INSTANCE_ID_SCHEMA=deterministic_content_addressed_mca_plus_16_hex
TEMPORAL_IDENTITY_SCHEMA=cap22_ranking_snapshot_id_plus_event_time_plus_integrity_digest
PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=null_only_for_canonical_bootstrap_else_exact_prior_instance_id
CAP22_PROVENANCE_MAPPING=ranking_snapshot_id_schema_integrity_event_time_universe_policy_source_path_source_sha256
POLICY_IDENTITY=AT_MOST_N_N5_OD07_DERIVED_ANTI_CHURN_POLICY_A
ORDERED_MEMBERSHIP_RULE=CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER
CARDINALITY_RULE=0_LE_LEN_LE_5_NO_PADDING_NO_DUPLICATES
BOOTSTRAP_RULE=PREFIX_FILL_FROM_CAP22_ELIGIBLE_NO_ANTI_CHURN_NO_PADDING
BOOTSTRAP_DIRECT_PREFIX_FILL_IS_CANONICALLY_AUTHORIZED=true
CANONICAL_DURABILITY_BOUND=true
CANONICAL_PROVENANCE_BOUND=true
ARTIFACT_LIFECYCLE_BOUND=true
SCHEMA_BOUND=true
WRITER_BOUND=true
READER_BOUND=true
CANONICAL_STORE=docs&#47;ops&#47;mf&#47;membership_context&#47;canonical
INSTANCE_COUNTS_ONLY_IF=SCHEMA_VALID_AND_CANONICAL_LOCATION_AND_DURABLE_WRITE_COMPLETE_AND_PROVENANCE_VALID_AND_IDENTITY_VALID
LIFECYCLE_COUNTS_ONLY_IF=DURABLE_VALID
FIRST_VALID_INSTANCE_IS_BOOTSTRAP=true
ARTIFACT_INSTANCE_CREATED=true
ARTIFACT_INSTANCE_EXISTENCE=PROVEN
ARTIFACT_INSTANCE_ID=mca_bf0255a6007432e2
PRIOR_MEMBERSHIP_REFERENCE=null
PRIOR_MEMBERSHIP_LISTING_STATUS=BOOTSTRAP_PROVEN
CAP22_CONSUMED_SNAPSHOT_ID=pfr_evidence_cap22_v1
CAP22_CONSUMED_EVENT_TIME=2023-11-14T22:13:20Z
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_CANONICAL_STAGE_CREATED=false
SELECTOR_RUNTIME_IMPLEMENTED=false
ROTATION_RUNTIME_IMPLEMENTED=false
RUNTIME_AUTHORIZED=false
G13_UNLOCK=false
EXECUTION_AUTHORITY_EFFECT=NONE
HOST_JOIN=NOT_DESIGNED
HANDOFF_NOT_DESIGNED=true
CAP23_REWIRED=false
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
```

Bound meaning: the writer accepts an already-decided ordered membership
payload and must **not** rank, select, or apply anti-churn. The reader
loads by exact instance identity, validates schema, provenance, identity,
lifecycle, and durable completeness, and fail-closes on malformed,
missing, empty, or partial artifacts. Bootstrap membership is the
eligible Cap-2.2 Top-20 prefix of at most 5. That prefix-fill is the
ratified `BOOTSTRAP_RULE` and is **not** a selector runtime. The first
canonical instance has `PRIOR_MEMBERSHIP_REFERENCE=null`. Derived
bootstrap delta is entered=current, exited=empty, retained=empty.
Stored `rotation_deltas` remain forbidden.

Fail-closed after this persist:

```text
OVERREAD_AS_WRITER_EQUALS_SELECTOR_RUNTIME=FORBIDDEN
OVERREAD_AS_BOOTSTRAP_EQUALS_ANTI_CHURN_REPLACEMENT=FORBIDDEN
OVERREAD_AS_BOOTSTRAP_EQUALS_MF_RERANK=FORBIDDEN
OVERREAD_AS_ROTATION_DELTAS_NOW_CANONICAL_STAGE=FORBIDDEN
OVERREAD_AS_PARTIAL_OR_PLACEHOLDER_EQUALS_INSTANCE=FORBIDDEN
OVERREAD_AS_EVIDENCE_COPY_EQUALS_CANONICAL_INSTANCE=FORBIDDEN
OVERREAD_AS_THIS_CLOSE_NAMES_A_NEXT_CANONICAL_DECISION=FORBIDDEN
OVERREAD_AS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_RUNTIME_OR_EXECUTION=FORBIDDEN
OVERREAD_AS_HOST_JOIN=FORBIDDEN
```

### 1.19 Isolated selector and membership-diff rotation runtime

Owner-GO
`OWNER_GO_WP_MF_03_ISOLATED_SELECTOR_AND_MEMBERSHIP_DIFF_ROTATION_RUNTIME_V1`
binds the isolated MF membership selector, POLICY_A evaluator, ranking-
observation holding reconstruction, and membership-diff rotation
controller. Prior WP-MF-02 schema, writer, reader, bootstrap instance
`mca_bf0255a6007432e2`, OD07 derived identity, and POLICY_A remain
binding. Those binds are **not** re-owned here.

This persist does **not** join a host, does **not** unlock G13, does
**not** rewire Cap 2.3 or Cap 2.4, does **not** emit execution intent,
and does **not** persist `rotation_deltas` as durable canonical state.
It does **not** name a next canonical decision. Replay of the identical
Cap-2.2 snapshot identity as the prior artifact writes **no** new
instance. Distinct snapshot identities write a new observation instance
through the existing WP-MF-02 writer even when membership is unchanged,
so holding age remains reconstructable from the artifact chain.

```text
OWNER_GO=OWNER_GO_WP_MF_03_ISOLATED_SELECTOR_AND_MEMBERSHIP_DIFF_ROTATION_RUNTIME_V1
SELECTOR_RUNTIME_IMPLEMENTED=true
MEMBERSHIP_DECISION_RUNTIME_IMPLEMENTED=true
ROTATION_RUNTIME_IMPLEMENTED=true
ROTATION_CONTROLLER_ROLE=MEMBERSHIP_DIFF_ONLY
ROTATION_CONTROLLER_OWNER_BOUND=true
CURRENT_MEMBERSHIP_INPUT_DEFINED=true
RANKED_CHALLENGER_INPUT_DEFINED=true
INCUMBENT_VS_CHALLENGER_RECONCILIATION_DEFINED=true
NEXT_ACTIVE_SET_OUTPUT_DEFINED=true
HOLDING_STATE_DERIVABLE_FROM_EXISTING_ARTIFACTS=true
HOLDING_STATE_IMPLEMENTATION=ARTIFACT_CHAIN_DISTINCT_SNAPSHOT_COUNT
UNCHANGED_MEMBERSHIP_WRITE_POLICY=WRITE_NEW_OBSERVATION_INSTANCE_IF_DISTINCT_SNAPSHOT_ELSE_NO_NEW_INSTANCE
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_SEMANTICS_BOUND=true
ROTATION_DELTAS_DURABLE_STAGE_CREATED=false
ANTI_CHURN_POLICY_STATUS=RATIFIED
HYSTERESIS_MODE=RANK_IMPROVEMENT_VS_DISPLACED_INCUMBENT
CHALLENGER_MARGIN_TYPE=RANK
CHALLENGER_MARGIN_VALUE=1
MINIMUM_HOLDING_UNIT=RANKING_OBSERVATIONS
MINIMUM_HOLDING_VALUE=2
CONSECUTIVE_CONFIRMATION_COUNT=1
MULTIPLE_REPLACEMENTS_PER_CYCLE=true
BOOTSTRAP_INSTANCE_ID=mca_bf0255a6007432e2
NEW_CANONICAL_ARTIFACT_INSTANCE_CREATED=false
RUNTIME_AUTHORIZED=false
HOST_JOIN=false
HANDOFF_NOT_DESIGNED=true
G13_UNLOCK=false
CAP23_REWIRED=false
CAP24_REWIRED=false
EXECUTION_AUTHORITY_EFFECT=NONE
FULL_CORE_LIVE_AUTHORITY_EFFECT=NONE
CANARY_AUTHORITY_EFFECT=NONE
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
```

Fail-closed after this persist:

```text
OVERREAD_AS_SELECTOR_EQUALS_HOST_JOIN=FORBIDDEN
OVERREAD_AS_SELECTOR_EQUALS_CAP23=FORBIDDEN
OVERREAD_AS_ROTATION_DIFF_EQUALS_EXECUTION=FORBIDDEN
OVERREAD_AS_REPLAY_EQUALS_NEW_OBSERVATION=FORBIDDEN
OVERREAD_AS_HOLDING_EQUALS_WALL_CLOCK=FORBIDDEN
OVERREAD_AS_THIS_CLOSE_NAMES_A_NEXT_CANONICAL_DECISION=FORBIDDEN
```

### 1.20 Deterministic previous-to-current replay proof

Owner-GO
`OWNER_GO_WP_MF_04_DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_PROOF_V1`
binds the isolated previous→current replay proof over the WP-MF-03
selector/POLICY_A path and the WP-MF-02 artifact chain. Replay
reconstructs holding age from distinct Cap-2.2 snapshot identities,
reuses the existing selector, and derives entered/exited/retained
without a durable rotation-delta stage. Replay is read-only and
creates **no** new canonical membership-context instance.

This persist completes the **isolated** MF target. It does **not**
complete productive integration, does **not** join a host, does
**not** unlock G13, does **not** rewire Cap 2.3 or Cap 2.4, and does
**not** authorize execution. Cooldown/turnover remain unratified and
are **outside** the isolated target. This persist does **not** name a
next canonical decision and does **not** start a successor slice.

```text
OWNER_GO=OWNER_GO_WP_MF_04_DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_PROOF_V1
DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED=true
OBSERVATION_AGE_RECONSTRUCTION_DETERMINISTIC=true
REPLAY_RESULT_DIGEST_STABLE=true
REPLAY_CANONICAL_MUTATION_FORBIDDEN=true
REPLAY_CANONICAL_MUTATION_OBSERVED=false
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_REPLAYABLE=true
ROTATION_DELTAS_DURABLE_STAGE_CREATED=false
MF_ARTIFACT_CONTRACT_COMPLETE=true
MF_BOOTSTRAP_INSTANCE_PROVEN=true
MF_SELECTOR_RUNTIME_IMPLEMENTED=true
MF_ROTATION_RUNTIME_IMPLEMENTED=true
MF_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED=true
MF_DETERMINISTIC_REPLAY_PROVEN=true
ROTATION_RUNTIME_TESTED=true
ROTATION_REPLAY_PROVEN=true
ISOLATED_MF_TARGET_COMPLETE=true
PRODUCTIVE_MF_INTEGRATION_COMPLETE=false
NEXT_STEP_IS_AUTOMATIC=false
EXPECTED_REMAINING_ISOLATED_MF_WORKPACKAGES=NONE
BOOTSTRAP_INSTANCE_ID=mca_bf0255a6007432e2
NEW_CANONICAL_ARTIFACT_INSTANCE_CREATED=false
RUNTIME_AUTHORIZED=false
HOST_JOIN=false
HANDOFF_NOT_DESIGNED=true
G13_UNLOCK=false
CAP23_REWIRED=false
CAP24_REWIRED=false
EXECUTION_AUTHORITY_EFFECT=NONE
FULL_CORE_LIVE_AUTHORITY_EFFECT=NONE
CANARY_AUTHORITY_EFFECT=NONE
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
```

Fail-closed after this persist:

```text
OVERREAD_AS_ISOLATED_COMPLETE_EQUALS_PRODUCTIVE_INTEGRATION=FORBIDDEN
OVERREAD_AS_REPLAY_EQUALS_CANONICAL_WRITE=FORBIDDEN
OVERREAD_AS_REPLAY_EQUALS_HOST_JOIN=FORBIDDEN
OVERREAD_AS_REPLAY_EQUALS_G13_UNLOCK=FORBIDDEN
OVERREAD_AS_THIS_CLOSE_NAMES_A_NEXT_CANONICAL_DECISION=FORBIDDEN
```

### 1.21 Canonical single-egress authority-handoff definition

Owner-GO
`OWNER_GO_WP_MF_05_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_DEFINITION_V1`
closes `HANDOFF_NOT_YET_CANONICALLY_DEFINED` in the subordinate handoff
contract. This persist does **not** re-own that close. Isolated MF
target remains complete. Productive integration remains incomplete.
Consumer identity remains `UNBOUND`. Host join remains false. Cap 2.3
and Cap 2.4 remain unre-wired. G13 remains closed. This persist does
**not** name a next canonical decision.

```text
OWNER_GO=OWNER_GO_WP_MF_05_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_DEFINITION_V1
HANDOFF_DEFINITION_OWNER=MF_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_CONTRACT_V1
AUTHORITY_HANDOFF_STATUS=DEFINED_CONSUMER_UNBOUND
CURRENT_HANDOFF_STATUS=CANONICALLY_DEFINED
HANDOFF_PAYLOAD_STATUS=BOUND_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_REFERENCE
CONSUMER_IDENTITY_STATUS=UNBOUND
HOST_JOIN=false
PRODUCTIVE_CONSUMER_CREATED=false
CAP23_REWIRED=false
CAP24_REWIRED=false
G13_UNLOCK=false
PRODUCTIVE_MF_INTEGRATION_COMPLETE=false
NEXT_STEP_IS_AUTOMATIC=false
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
```

Fail-closed after this persist:

```text
OVERREAD_AS_HANDOFF_DEFINITION_EQUALS_HOST_JOIN=FORBIDDEN
OVERREAD_AS_HANDOFF_DEFINITION_EQUALS_CAP23_REWIRE=FORBIDDEN
OVERREAD_AS_THIS_FILE_OWNING_THE_HANDOFF_DEFINITION=FORBIDDEN
OVERREAD_AS_THIS_CLOSE_NAMES_A_NEXT_CANONICAL_DECISION=FORBIDDEN
```

### 1.22 Authoritative Next Active Set ownership

Owner-GO
`OWNER_GO_PDF_STEP_3_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_V1`
binds authoritative Next Active Set ownership in the subordinate
ownership contract. This persist does **not** re-own that bind.
Isolated POLICY_A in this file remains the policy of the
non-authoritative membership selector. Owner-GO
`PEAK_TRADE_PDF_STEP_5_AS05_D01_AUTHORITATIVE_ACTIVE_SET_POLICY_ADOPTION_DOCS_ONLY_V1`
closes AS05-D01 in the subordinate ownership contract as
`ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET`. This file does **not**
re-own that close. Policy reuse does **not** transfer ownership.
Owner-GO
`PEAK_TRADE_AS05_D02_PURE_POLICY_A_EVALUATOR_RATIFICATION_DOCS_ONLY_V1`
closes AS05-D02 in the subordinate ownership contract as
`NAME_EVALUATE_POLICY_A_V1_AS_PURE_ANTI_CHURN_EVALUATOR_FOR_AUTHORITATIVE_NEXT_ACTIVE_SET`.
This file does **not** re-own that close. Evaluator reuse does **not**
transfer ownership. Selector owner identity is **not** Active Set
evaluator authority. AS05-D03 remains the next unresolved Owner
decision. PDF Step 5 remains `UNRESOLVED`. Rotation behavior remains
fail-closed. PDF Step 7 remains forbidden.
Owner-GO
`OWNER_GO_PDF_STEP_4_ANTI_CHURN_CENSUS_CANONICAL_CLOSE_V1`
closes PDF Step 4 as an inventory census in the subordinate ownership
contract. This persist does **not** re-own that close. Workpackage
`PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION_DECISION_PACKAGE_V1`
prepared a non-operative Owner decision surface in the subordinate
ownership contract. This file does **not** re-own that surface and
does **not** close PDF Step 5.

```text
OWNER_GO=OWNER_GO_PDF_STEP_3_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_V1
OWNER_GO_PDF_STEP_4_CENSUS_CLOSE=OWNER_GO_PDF_STEP_4_ANTI_CHURN_CENSUS_CANONICAL_CLOSE_V1
OWNER_GO_AS05_D01=PEAK_TRADE_PDF_STEP_5_AS05_D01_AUTHORITATIVE_ACTIVE_SET_POLICY_ADOPTION_DOCS_ONLY_V1
OWNER_GO_AS05_D02=PEAK_TRADE_AS05_D02_PURE_POLICY_A_EVALUATOR_RATIFICATION_DOCS_ONLY_V1
ACTIVE_SET_OWNERSHIP_CONTRACT=MF_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_CONTRACT_V1
MEMBERSHIP_ROTATION_CONTROLLER_OWNER=ops.mf_membership_rotation_controller_v1
NEXT_ACTIVE_SET_AUTHORITY_OWNER=ops.mf_membership_rotation_controller_v1
ROTATION_DECISION_AUTHORITY_BOUND=true
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY=true
POLICY_REUSE_DOES_NOT_TRANSFER_AUTHORITY=true
ACTIVE_SET_POLICY_ADOPTION=ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET
ACTIVE_SET_POLICY_RATIFIED=true
ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET=ADOPTED_POLICY_A_UNCHANGED
AS05_D01_STATUS=CLOSED
AS05_D01_DECISION=ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET
AS05_D02_STATUS=CLOSED
AS05_D02_DECISION=NAME_EVALUATE_POLICY_A_V1_AS_PURE_ANTI_CHURN_EVALUATOR_FOR_AUTHORITATIVE_NEXT_ACTIVE_SET
AS05_D03_STATUS=UNRESOLVED
THIS_FILE_IS_NOT_AS05_D01_CLOSE_OWNER=true
THIS_FILE_IS_NOT_AS05_D02_CLOSE_OWNER=true
CENSUS_CLASS=INVENTORY_ONLY_NO_POLICY_CHOICE
N_VALUE_REOWNED=false
EXECUTING_MODEL_HANDOFF_CONSUMER=UNBOUND
HOST_JOIN=false
PRODUCTIVE_CONSUMER_CREATED=false
CAP23_REWIRED=false
CAP24_REWIRED=false
G13_UNLOCK=false
PDF_STEP_3_MEMBERSHIP_ROTATION_OWNERSHIP=CLOSED
PDF_STEP_4_ANTI_CHURN_CENSUS=CLOSED
PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=UNRESOLVED
OWNER_DECISION_SURFACE_STATUS=D01_D02_RATIFIED_D03_UNRESOLVED
OWNER_DECISION_COUNT=3
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=false
NEXT_CANONICAL_DECISION=AS05-D03
THIS_PERSIST_DOES_NOT_CLOSE_PDF_STEP_5=true
```

Fail-closed after this persist:

```text
OVERREAD_AS_POLICY_A_EQUALS_ACTIVE_SET_POLICY=FORBIDDEN
OVERREAD_AS_THIS_FILE_OWNING_AS05_D01=FORBIDDEN
OVERREAD_AS_THIS_FILE_OWNING_AS05_D02=FORBIDDEN
OVERREAD_AS_D01_EQUALS_STEP_5_CLOSE=FORBIDDEN
OVERREAD_AS_MEMBERSHIP_CONTEXT_RENAME=FORBIDDEN
OVERREAD_AS_THIS_FILE_OWNING_ACTIVE_SET_OWNERSHIP=FORBIDDEN
OVERREAD_AS_THIS_FILE_CLOSING_STEP_4=FORBIDDEN
OVERREAD_AS_PDF_STEP_5_CLOSE=FORBIDDEN
OVERREAD_AS_CENSUS_CLOSE_EQUALS_POLICY_RATIFICATION=FORBIDDEN
OVERREAD_AS_DECISION_PACKAGE_EQUALS_POLICY_RATIFICATION=FORBIDDEN
OVERREAD_AS_THIS_FILE_CLOSING_AS05_D02=FORBIDDEN
```

## 2. Owner by mechanism

Owners below are **cited from** the parent ownership contract. This file
does **not** re-own them.

| Mechanism | Owner (from parent ownership contract) | Epistemic class |
|---|---|---|
| Cap 2.2 origin ordering / origin tie-break | Cap 2.2 ranking producer (outside isolated selector) | `CANONICAL_AUTHORITY` at Cap 2.2; consumed as membership order after OD03 close |
| MF-own tie-break | `NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY` | `ADJUDICATED_CONCLUSION` of OD03 close |
| Hysteresis | `SELECTOR` | `ADJUDICATED_CONCLUSION` of ownership; this file adds POLICY_A ratified-rule semantics in §7 / §1.17 |
| Minimum holding | `SELECTOR` | `ADJUDICATED_CONCLUSION` of ownership; this file adds POLICY_A ratified-rule semantics in §8 / §1.17 |
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
`rotation_deltas` is a derived identity (`OPEN_DECISION_07` closed
in §1.6). Stored deltas are not canonical authority.

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
HYSTERESIS_SEMANTICS=SELECTOR_OWNED_RATIFIED_RULE_POLICY_A
HYSTERESIS_CORE_OWNER=SELECTOR
HYSTERESIS_ROLE=MEMBERSHIP_STICKINESS_AND_ADMISSION_OF_A_PROPOSED_CHANGE
HYSTERESIS_IS_RATIFIED_RULE=true
HYSTERESIS_MODE=RANK_IMPROVEMENT_VS_DISPLACED_INCUMBENT
CHALLENGER_MARGIN_TYPE=RANK
CHALLENGER_MARGIN_VALUE=1
HYSTERESIS_NUMERICS_RATIFIED=true
SSF_HYSTERESIS_IMPORTED=false
REUSE_STATUS=POLICY_A
```

Hysteresis is part of the isolated MF selection universe as a
**ratified rule** located at the selector under Owner-GO
`OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1` POLICY_A. It affects
admission of a proposed challenger replacement and thereby suppresses
churn. It does **not** own rotation. It is **not** a replacement
state. Forced removal bypasses hysteresis.

The ratified rank margin is `CHALLENGER_MARGIN_VALUE=1`: a challenger
must improve on the displaced incumbent by at least one Cap-2.2 rank
position. This is **not** Cap 2.3 `hysteresis_rank_improvement`. Cap 2.3
values remain **not imported**. Master-V2 / Double-Play / strategy
switch-gate hysteresis remains `OUT_OF_DOMAIN`. Score-margin is
**not** used while consume-Cap-2.2-order policy holds.

## 8. Minimum-holding semantics

```text
MIN_HOLDING_SEMANTICS=SELECTOR_OWNED_RATIFIED_RULE_POLICY_A
MINIMUM_HOLDING_CORE_OWNER=SELECTOR
MINIMUM_HOLDING_ROLE=MEMBERSHIP_TENURE_BEFORE_PROPOSED_DROP_OR_REPLACE
MINIMUM_HOLDING_IS_RATIFIED_RULE=true
MINIMUM_HOLDING_UNIT=RANKING_OBSERVATIONS
MINIMUM_HOLDING_VALUE=2
MINIMUM_HOLDING_NUMERICS_RATIFIED=true
MINIMUM_HOLDING_IS_NOT_POSITION_HOLDING=true
SSF_MIN_HOLDING_IMPORTED=false
REUSE_STATUS=POLICY_A
```

Minimum holding is part of the isolated MF selection universe as a
**ratified rule** located at the selector under Owner-GO
`OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1` POLICY_A. It delays a
proposed drop or replace until membership tenure of two consecutive
ranking observations exists, and thereby suppresses one-cycle
oscillation. It does **not** own rotation. It is **not** a replacement
state. It is **not** position holding, order holding, or paper-shadow
hold-binding. Forced removal bypasses minimum holding.

Tenure is counted in Cap-2.2 ranking observations consumed by the
selector while the instrument was an admitted member. It is
reconstructable from the membership-artifact chain and prior
reference. Cap 2.3 `min_holding_period_seconds` is Cap-2.3 policy and
is **not** imported. Cap 0.4 lists minimum active/candidate duration as
an open policy decision; that reminder is **not** this domain's
numeric authority.

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
OPEN_DECISION_07_CLOSED=true
OPEN_DECISION_07_CLOSE_CLASS=CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_ARE_NOT_DURABLE_CANONICAL_STATE=true
ROTATION_DELTAS_DURABLE_STAGE_FORBIDDEN=true
```

| Mechanism | Influences membership proposal | Allows/prevents rotation | Suppresses churn only | Is a replacement state |
|---|---|---|---|---|
| Origin tie-break (Cap 2.2) | Orders the candidate context; after OD03 close this order is the membership order; does not itself admit membership | No | No | No |
| MF-own tie-break | `NOT_REQUIRED` while consume-Cap-2.2-order policy holds | No | No | No |
| Hysteresis | Yes, as admission/non-admission of a proposed change (**POLICY_A rule**) | May prevent a diff from being admitted; does **not** own rotation | Yes | No |
| Minimum holding | Yes, as tenure before proposed drop/replace (**POLICY_A rule**) | May prevent a diff from being admitted; does **not** own rotation | Yes | No |
| Cap 2.3 `REPLACEMENT_PENDING` | Out of domain | Out of domain | Out of domain | Cap 2.3 only; not imported |
| Membership-only pending analog | Not required in the current isolated MF model (`OPEN_DECISION_05` closed) | Still would not **be** rotation | Not a second membership identity | No; node remains `OUT_OF_CORE_MODEL` |

Cap 0.4 `MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0` remains
`DEFERRED_REQUIRED_CAPABILITY`. This contract does **not** consume that
reminder as rotation-engine authority. Anti-churn POLICY_A numerics
are ratified in §1.17. Cooldown and turnover remain unratified.

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
UNRATIFIED_COOLDOWN_OR_TURNOVER_NUMERICS=NOT_A_DEFAULT
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
OVERREAD_AS_ROTATION_DERIVED_EQUALS_DURABLE_STAGE=FORBIDDEN
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
OVERREAD_AS_PREDICATE_EQUALS_CREATION_AUTHORIZED_TRUE=FORBIDDEN
OVERREAD_AS_PERMISSION_BIT_EQUALS_MATERIALIZATION=FORBIDDEN
OVERREAD_AS_OD06_ALLOWED_EQUALS_CREATION_AUTHORIZED=FORBIDDEN
OVERREAD_AS_NOT_REQUIRED_BEFORE_EQUALS_BOUND=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_MATERIALIZATION=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_ARTIFACT_INSTANCE=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_CREATE_NOW=FORBIDDEN
OVERREAD_AS_CREATION_AUTHORIZED_TRUE_EQUALS_AUTO_NEXT=FORBIDDEN
OVERREAD_AS_CENSUS_CLASS_NAME_EQUALS_CURRENT_BIT_FALSE=FORBIDDEN
OVERREAD_AS_RETAINED_ENTERED_EXITED_PERSISTED_STAGE=FORBIDDEN
OVERREAD_AS_RETAINED_ENTERED_EXITED_NOW_OPERATIVELY_DERIVABLE_WHILE_PRIOR_UNPROVEN=FORBIDDEN
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

Cooldown, turnover, and any MF-own scoring/tie-break algorithm remain
unratified. Numeric ceiling `N_VALUE=5` is closed in §1.3 as Owner
policy under `AT_MOST_N`. Anti-churn POLICY_A numerics are ratified
in §1.17. `OPEN_DECISION_07` is closed in §1.6 as derived identity.

```text
UNRESOLVED_PARAMETERS=COOLDOWN_TURNOVER_AND_MF_OWN_SCORING_ALGORITHMS
N_VALUE=5
EXACTLY_N_VS_AT_MOST_N=CLOSED_AT_MOST_N
CARDINALITY_MODE=AT_MOST_N
MF_TIE_BREAK_ALGORITHM=NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY
MF_TIE_BREAK_KEY_ORDER=NOT_REQUIRED_WHILE_CONSUME_CAP22_ORDER_POLICY
HYSTERESIS_MODE=RANK_IMPROVEMENT_VS_DISPLACED_INCUMBENT
CHALLENGER_MARGIN_TYPE=RANK
CHALLENGER_MARGIN_VALUE=1
HYSTERESIS_THRESHOLD=NOT_USED_UNDER_POLICY_A
HYSTERESIS_DEAD_BAND=NOT_USED_UNDER_POLICY_A
HYSTERESIS_CONFIRMATION_COUNT=1
CONSECUTIVE_CONFIRMATION_COUNT=1
MINIMUM_HOLDING_UNIT=RANKING_OBSERVATIONS
MINIMUM_HOLDING_VALUE=2
MIN_HOLDING_DURATION=NOT_USED_UNDER_POLICY_A
MIN_HOLDING_BARS=NOT_USED_UNDER_POLICY_A
MIN_ACTIVE_DURATION=NOT_USED_UNDER_POLICY_A
MIN_CANDIDATE_DURATION=NOT_USED_UNDER_POLICY_A
COOLDOWN=UNRESOLVED
TURNOVER_BOUND=UNRESOLVED
REPLACEMENT_MARGIN=RANK_1
MEMBERSHIP_ONLY_PENDING_STATE_MACHINE=NOT_REQUIRED_IN_CURRENT_ISOLATED_MF_MODEL
```

Cap 2.3 evidence values such as `hysteresis_rank_improvement=1` and
`min_holding_period_seconds=3600.0` remain Cap-2.3
`CANONICAL_AUTHORITY` / `HISTORICAL_STATE` for single-selected-future
policy. Citing them here is **negative constraint** only:
`SSF_SEMANTICS_IMPORTED=false`. POLICY_A rank-margin 1 is **not**
an import of that Cap-2.3 value.

Owner-GO `OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1` closes
`OPEN_DECISION_07` in §1.6 and ratifies anti-churn POLICY_A in §1.17.
OD01 is closed in §1.3 as Owner-policy ceiling `N_VALUE=5`. OD02 and
OD03 are closed in §1.1–§1.2. OD04 is closed in §1.4 as ownership
principle only. OD05 is closed in §1.5 as
`NO_INDEPENDENT_PENDING_STATE_REQUIRED` for the current isolated MF
model. OD06 is closed in §1.7 as permission-only `ALLOWED` while G13
remains closed. Permission is not artifact existence. Membership-context
artifact semantic identity is bound in §1.9 as information classes
only. That bind is not artifact existence, not schema, not writer,
and not prior-listing existence. Artifact existence class is bound in
§1.10 as
`BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT`.
Owner-GO
`OWNER_GO_WP_MF_02_ARTIFACT_CONTRACT_AND_FIRST_DURABLE_INSTANCE_V1`
binds schema, writer, reader, durability, provenance, and lifecycle
in §1.18 and proves the first bootstrap instance. Selector runtime
and rotation runtime remain unimplemented. The §1.16 persist does not
name a next canonical decision. This persist does **not** name a next
canonical decision.

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
MF_MEMBERSHIP_CONTEXT_ARTIFACT_PERSISTENCE=PROVEN
MEMBERSHIP_CONTEXT_ARTIFACT_SEMANTIC_IDENTITY=BOUND_INFORMATION_CLASSES_ONLY
ARTIFACT_EXISTENCE_CLASS=BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT
ARTIFACT_INSTANCE_EXISTENCE=PROVEN
INSTANCE_DECISION_CLASS=NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED
INSTANCE_CENSUS_VERDICT=BOOTSTRAP_INSTANCE_PROOF_FOUND
UNPROVEN_IS_NOT_ABSENT=true
CREATION_AUTHORIZED=true
CREATION_AUTHORIZED_SEMANTICS=PERMISSION_BIT_ONLY
CREATION_AUTHORIZATION_PREDICATE_BOUND=true
PRECONDITION_MEMBERSHIP_BOUND=true
CLOSED_DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
CLOSED_DECISION_CLASS_REMAINS=MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1
PRIOR_CLASS_REMAINS_CLOSED=true
OWNER_DECISION=SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE
DECISION_CLASS_BIND_DOES_NOT_SET_CREATION_AUTHORIZED_TRUE=true
DECISION_CLASS=MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1
DECISION_SCOPE=OWNER_DECIDES_MATERIALIZATION_AUTHORITY_GRANTED_TRUE_OR_FALSE_UNDER_EXISTING_PERMISSION_BIT_ONLY_SEMANTICS
DECISION_CLASS_BOUND=true
DECISION_CLASS_CLOSED=true
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_NAME_A_NEXT_CANONICAL_DECISION=true
CLASS_BIND_IS_NOT_SUBSTANCE_CLOSE=true
CLASS_BIND_DOES_NOT_SET_MATERIALIZATION_AUTHORITY_TRUE=true
MATERIALIZATION_AUTHORITY_GRANTED=true
GRANT_IS_NOT_MATERIALIZATION=true
GRANT_IS_NOT_ARTIFACT_CREATION=true
GRANT_IS_NOT_INSTANCE_PROOF=true
GRANT_DOES_NOT_BIND_SCHEMA_WRITER_READER=true
SCHEMA_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
WRITER_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
READER_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
OD07_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
ANTI_CHURN_NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE=true
INSTANCE_IDENTITY_STATUS=BOUND
TEMPORAL_IDENTITY_STATUS=BOUND
PRIOR_REFERENCE_STATUS=BOUND
CAP22_PROVENANCE_STATUS=BOUND
PRIOR_MEMBERSHIP_LISTING_STATUS=BOOTSTRAP_PROVEN
TEMPORAL_SCHEMA=BOUND
INSTANCE_ID_SCHEMA=BOUND
PRIOR_MEMBERSHIP_REFERENCE_SCHEMA=BOUND
PRIOR_MEMBERSHIP_LISTING_FOR_DERIVED_READING=BOOTSTRAP_PROVEN
SCHEMA_BOUND=true
WRITER_BOUND=true
READER_BOUND=true
CANONICAL_DURABILITY_BOUND=true
CANONICAL_PROVENANCE_BOUND=true
ARTIFACT_LIFECYCLE_BOUND=true
ARTIFACT_INSTANCE_CREATED=true
ARTIFACT_INSTANCE_ID=mca_bf0255a6007432e2
SELECTOR_RUNTIME_IMPLEMENTED=true
ROTATION_RUNTIME_IMPLEMENTED=true
RUNTIME_AUTHORIZED=false
ROTATION_DELTAS_STATUS=DERIVED
ROTATION_DELTAS_ARE_NOT_DURABLE_CANONICAL_STATE=true
ROTATION_DELTAS_DURABLE_STAGE_FORBIDDEN=true
ANTI_CHURN_POLICY_STATUS=RATIFIED
ANTI_CHURN_OWNER=SELECTOR
HYSTERESIS_MODE=RANK_IMPROVEMENT_VS_DISPLACED_INCUMBENT
CHALLENGER_MARGIN_TYPE=RANK
CHALLENGER_MARGIN_VALUE=1
MINIMUM_HOLDING_UNIT=RANKING_OBSERVATIONS
MINIMUM_HOLDING_VALUE=2
CONSECUTIVE_CONFIRMATION_COUNT=1
MULTIPLE_REPLACEMENTS_PER_CYCLE=true
OD07_STATUS=CLOSED
OPEN_DECISION_07=ROTATION_DELTAS_STAGE_VS_DERIVED_IDENTITY
OPEN_DECISION_07_CLOSED=true
OPEN_DECISION_07_CLOSE_CLASS=CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY
NO_NUMERIC_PREFIX_SELECTION_UNTIL_OD01_CLOSE=false
MF_OWN_TIE_BREAK_REQUIRED=false
```

## 13. Forensic census (bound; not a second SSOT)

| Mechanism | Current authority | Existing contract | Historical evidence | Current runtime existence | Unresolved |
|---|---|---|---|---|---|
| Tie-break | Cap 2.2 origin ordering is membership order after OD03 close; MF-own not required while consume policy holds | Ownership §5.1; this file §6 | Cap 2.2 ranking evidence `tie_break_order`; Cap 2.3 different order **not imported**; research/strategy tie-breaks `OUT_OF_DOMAIN` | Isolated MF selector bound in §1.19; Cap 2.2 producer exists as TOP20 origin | Hygiene numerics |
| Hysteresis | Selector-owned POLICY_A rule: rank-improvement vs displaced incumbent; margin 1 | Ownership §5.2; this file §7 / §1.17 / §1.19 | Cap 2.3 SSF hysteresis **not imported**; Cap 0.4 reminder not numeric authority; MV2/strategy hysteresis `OUT_OF_DOMAIN` | Isolated MF selector bound in §1.19 | Cooldown/turnover |
| Min holding | Selector-owned POLICY_A rule: 2 ranking observations; not position holding | Ownership §5.3; this file §8 / §1.17 / §1.19 | Cap 2.3 SSF min holding **not imported**; Cap 0.4 reminder not numeric authority | Isolated MF selector bound in §1.19 | Cooldown/turnover |
| Replacement-pending | Cap 2.3 only; **not** MF authority | Ownership §5.5 forbids SSF import; this file §9 / §1.5 | Cap 2.3 `REPLACEMENT_PENDING` state machine | Cap 2.3 producer exists **outside** this graph; no MF pending runtime | Independent MF pending class **not required** in the current isolated model (`OPEN_DECISION_05` closed); not never-needed |
| Membership-context artifact identity | Information classes bound in §1.9; schema, writer, reader, durability, provenance, and lifecycle bound in §1.18; class `NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY`; OD07 closed as derived in §1.6 | This file §1.9 / §1.18 / §1.19 / §1.20 | R6 `ordered_instrument_ids` observation **not promoted**; Cap-2.3 snapshots **not imported**; docs-contract persist **not** membership artifact | Isolated selector bound in §1.19; replay bound in §1.20; membership-context artifact schema/writer/reader bound; bootstrap instance `mca_bf0255a6007432e2` proven | Cooldown/turnover (deferred; outside isolated MF target) |
| Membership-context artifact existence class | Class bound in §1.10 as `BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT`; instance `PROVEN` after §1.18 | This file §1.10 / §1.18 | OD06 permission **not** existence; #6373 identity **not** existence; Cap-2.2 snapshots upstream provenance only; Cap-2.3/R6 `OUT_OF_DOMAIN`; P6_5189 ledger name-collision `HISTORICAL_ONLY`; Atlas `AUTHORITY=NONE` | Canonical bootstrap instance proven at `docs/ops/mf/membership_context/canonical/mca_bf0255a6007432e2.json`; empty placeholder **not** instance | Cooldown/turnover (deferred; outside isolated MF target) |
| Membership-context artifact instance-existence census | Historical §1.11 class remains `NO_INSTANCE_PROOF_FOUND_BUT_CREATION_NOT_YET_AUTHORIZED`; current census verdict `BOOTSTRAP_INSTANCE_PROOF_FOUND`; instance `PROVEN`; `UNPROVEN` is not `ABSENT` | This file §1.11 / §1.18 | §1.10 tracked origin/main census was no instance proof found before WP-MF-02 | Bootstrap instance proven; `CREATION_AUTHORIZED=true` remains permission-bit; isolated selector bound in §1.19; replay bound in §1.20 | Cooldown/turnover (deferred; outside isolated MF target) |
| Isolated selector and membership-diff rotation runtime | Selector, POLICY_A, holding reconstruction, and membership-diff rotation bound in §1.19; writer/reader reused from §1.18; replay of identical snapshot writes no instance | This file §1.19; `src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py` | Cap-2.2 eligible Top-20 consumed as order; Cap-2.3 **not imported** | Isolated selector/rotation implemented; `RUNTIME_AUTHORIZED=false`; no host join | Cooldown/turnover (deferred; outside isolated MF target) |
| Deterministic previous-to-current replay | Replay of WP-MF-03 selector/POLICY_A over the WP-MF-02 artifact chain bound in §1.20; holding age reconstructed from distinct Cap-2.2 snapshot identities; rotation deltas derived and replayable; no canonical write | This file §1.20; `src/ops/mf_membership_previous_to_current_replay_contract_v1.py` | Cap-2.2 eligible Top-20 consumed as order; Cap-2.3 **not imported**; execution/host replay packs `OUT_OF_DOMAIN` | Isolated previous→current replay proven; canonical store unchanged; `RUNTIME_AUTHORIZED=false` | Productive integration; host join; G13; Cap-2.3 rewire (all deferred; outside isolated MF target) |
| Membership-context artifact creation-authorization predicate | Predicate bound in §1.12 as `PERMISSION_BIT_ONLY`; that persist left `CREATION_AUTHORIZED=false`; schema/writer/reader/OD07/anti-churn `NOT_REQUIRED_BEFORE_CREATION_AUTHORIZED_TRUE`; permission-bit is not materialization | This file §1.12 | OD06 permission **not** `CREATION_AUTHORIZED`; census persist **not** predicate | Isolated membership artifact unimplemented; no materialization | Schema; writer; reader; prior listing; OD07; materialization authority; durability/provenance semantics |
| Membership-context artifact creation-authorized permission-bit decision class | Decision class named in §1.13 as `MF_CREATION_AUTHORIZED_PERMISSION_BIT_DECISION_V1`; class bind is not true/false choice; that persist left `CREATION_AUTHORIZED=false`; materialization not granted; artifact not created | This file §1.13 | §1.12 persist **not** a named next decision; this Owner-GO names it | Isolated membership artifact unimplemented | Schema; writer; reader; OD07; anti-churn; bootstrap/durability/provenance; materialization authority |
| Membership-context artifact creation-authorized permission-bit decision | Class closed in §1.14 as `SET_CREATION_AUTHORIZED_TRUE`; `CREATION_AUTHORIZED=true` as `PERMISSION_BIT_ONLY`; true is not materialization; artifact not created; that persist did not name a next decision | This file §1.14 | §1.13 named the class and did **not** choose; this Owner-GO chooses `true` | Isolated membership artifact unimplemented; bit true; no instance | Schema; writer; reader; OD07; anti-churn; bootstrap/durability/provenance; materialization authority |
| Membership-context artifact materialization-authority decision class | Decision class named in §1.15 as `MF_MEMBERSHIP_CONTEXT_ARTIFACT_MATERIALIZATION_AUTHORITY_DECISION_V1`; class bind is not true/false choice; that persist left `MATERIALIZATION_AUTHORITY_GRANTED=false`; artifact not created | This file §1.15 | §1.14 persist **not** a named next decision; this Owner-GO names it | Isolated membership artifact unimplemented; bit true; grant remains false until §1.16 | Schema; writer; reader; OD07; anti-churn; bootstrap/durability/provenance; materialization-authority true/false |
| Membership-context artifact materialization-authority decision | Class closed in §1.16 as `SET_MATERIALIZATION_AUTHORITY_GRANTED_TRUE`; `MATERIALIZATION_AUTHORITY_GRANTED=true` as grant only; grant is not materialization; artifact not created; that persist did not name a next decision | This file §1.16 | §1.15 named the class and did **not** choose; this Owner-GO chooses `true` | Isolated membership artifact unimplemented; grant true; no instance | Schema; writer; reader; OD07; anti-churn; bootstrap/durability/provenance; later materialization/create GO |

```text
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MF_SELECTOR=true
CURRENT_RUNTIME_EXISTENCE_ISOLATED_ANTI_CHURN=true
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MEMBERSHIP_ROTATION_POLICY=true
CURRENT_RUNTIME_EXISTENCE_ISOLATED_MEMBERSHIP_CONTEXT_ARTIFACT=true
CURRENT_RUNTIME_EXISTENCE_ISOLATED_SELECTOR_RUNTIME=true
CURRENT_RUNTIME_EXISTENCE_ISOLATED_PREVIOUS_TO_CURRENT_REPLAY=true
ISOLATED_MF_TARGET_COMPLETE=true
PRODUCTIVE_MF_INTEGRATION_COMPLETE=false
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
alpha, G13 unlock, productive-host consumption, scoring, or a
rotation engine. Hygiene cooldown/turnover remain unratified.

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
RUNTIME_IMPLEMENTATION_CREATED=true
SELECTOR_RUNTIME_IMPLEMENTED=true
MEMBERSHIP_DECISION_RUNTIME_IMPLEMENTED=true
ROTATION_RUNTIME_IMPLEMENTED=true
DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED=true
ISOLATED_MF_TARGET_COMPLETE=true
PRODUCTIVE_MF_INTEGRATION_COMPLETE=false
NEXT_STEP_IS_AUTOMATIC=false
SRC_PATHS_CHANGED_BY_WP_MF_04=true
CAP23_REWIRED=false
CAP24_REWIRED=false
G13_UNLOCK=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
INTEGRATION_STATUS=NOT_IN_SCOPE
HOST_ADAPTER_STATUS=NOT_DESIGNED
HOST_CONSUMER_STATUS=NONE
AUTHORITY_HANDOFF_STATUS=DEFINED_CONSUMER_UNBOUND
NEXT_IMPLEMENTATION_AUTHORIZED=false
NEXT_SLICE_AUTHORIZED=false
HARD_STOP_AFTER_THIS_CONTRACT=true
```

Owner-GO
`OWNER_GO_WP_MF_05_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_DEFINITION_V1`
binds the single-egress definition in
[`MF_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_CONTRACT_V1.md`](MF_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_CONTRACT_V1.md).
This persist does not name a next canonical decision. OD01 is
closed as Owner-policy ceiling `N_VALUE=5`. OD04 is closed as ownership
principle only. OD06 is closed as permission-only `ALLOWED` while G13
remains closed. Membership-context artifact semantic identity is bound
in §1.9 as information classes only. Artifact existence class is bound
in §1.10 as
`BOUND_REQUIRED_NON_AUTHORITATIVE_DURABLE_MEMBERSHIP_CONTEXT_ARTIFACT`.
Creation-authorization semantics are bound in §1.12 as
`PERMISSION_BIT_ONLY`. `CREATION_AUTHORIZED` is `true` as permission-bit
only. `MATERIALIZATION_AUTHORITY_GRANTED` is `true` as grant only.
Owner-GO `OWNER_GO_WP_MF_01_OD07_AND_ANTI_CHURN_V1` closes
`OPEN_DECISION_07` in §1.6 as `CLOSED_ROTATION_DELTAS_DERIVED_IDENTITY`
and ratifies anti-churn POLICY_A in §1.17. Owner-GO
`OWNER_GO_WP_MF_02_ARTIFACT_CONTRACT_AND_FIRST_DURABLE_INSTANCE_V1`
binds schema, writer, reader, durability, provenance, and lifecycle
in §1.18 and proves bootstrap instance `mca_bf0255a6007432e2`.
Owner-GO
`OWNER_GO_WP_MF_03_ISOLATED_SELECTOR_AND_MEMBERSHIP_DIFF_ROTATION_RUNTIME_V1`
binds isolated selector, POLICY_A, and membership-diff rotation in
§1.19. Owner-GO
`OWNER_GO_WP_MF_04_DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_PROOF_V1`
binds deterministic previous→current replay in §1.20 and completes
the isolated MF target. Productive integration remains incomplete.
Owner-GO
`OWNER_GO_WP_MF_05_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_DEFINITION_V1`
binds the single-egress definition in the handoff contract. Host
join, G13, Cap-2.3 rewire, and execution remain closed.
This persist does not name a next canonical decision.
