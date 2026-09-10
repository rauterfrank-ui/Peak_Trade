---
docs_token: DOCS_TOKEN_MF_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_CONTRACT_V1
status: active
scope: Isolated PDF-Step-3 ownership bind for authoritative Next Active Set inside ranking/selection domain; rotation fail-closed until PDF Step 5; no Cap-2.3/2.4 join; no G13 unlock
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

# MF Authoritative Next Active Set Ownership Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_ISOLATED_ACTIVE_SET_OWNERSHIP
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_PDF_STEP_3_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_V1
OWNER_GO_PDF_STEP_4_CENSUS_CLOSE=OWNER_GO_PDF_STEP_4_ANTI_CHURN_CENSUS_CANONICAL_CLOSE_V1
WORKPACKAGE_PDF_STEP_5_DECISION_PACKAGE=PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION_DECISION_PACKAGE_V1
BOUND_ORIGIN_MAIN_SHA=d6143e552986f0fc70c73b73f3f8313cdcef1918
CONTRACT_ID=MF_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_CONTRACT_V1
PARENT_BOUNDARY_CONTRACT=MF_SELECTION_CONTEXT_BOUNDARY_CONTRACT_V1
HANDOFF_CONTRACT=MF_CANONICAL_SINGLE_EGRESS_AUTHORITY_HANDOFF_CONTRACT_V1
OWNER=ops.mf_membership_rotation_controller_v1
MEMBERSHIP_ROTATION_CONTROLLER_OWNER=ops.mf_membership_rotation_controller_v1
MEMBERSHIP_STATE_OWNER=ops.mf_membership_rotation_controller_v1
NEXT_ACTIVE_SET_AUTHORITY_OWNER=ops.mf_membership_rotation_controller_v1
NEXT_ACTIVE_SET_AUTHORITY_CLASS=AUTHORITATIVE_SELECTED_MEMBERSHIP_INSIDE_RANKING_SELECTION_DOMAIN
NEXT_ACTIVE_SET_STATUS=AUTHORITATIVE_OWNERSHIP_BOUND_ROTATION_FAIL_CLOSED
ROTATION_DECISION_AUTHORITY_BOUND=true
ONE_ACTIVE_SET_STATE_OWNER=true
ACTIVE_SET_SELECTION_AUTHORITY=true
MF_MEMBERSHIP_CONTEXT_SELECTION_AUTHORITY=false
SELECTION_DOMAIN_AUTHORITY_EFFECT=ISOLATED_ACTIVE_SET_OWNERSHIP_ONLY
EXECUTION_AUTHORITY_INSIDE_SELECTION_DOMAIN=false
EXECUTION_AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
G13_UNLOCK=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
SELECTION_AUTHORITY=false
PRODUCTIVE_SELECTION_AUTHORITY=false
CAP23_REMAINS_SOLE_PRODUCTIVE_SELECTION_OWNER=true
CAP23_IMPORTED=false
CAP23_REWIRED=false
CAP24_REWIRED=false
PRODUCTIVE_CONSUMER_CREATED=false
HOST_JOIN=false
CARDINALITY_MODE=AT_MOST_N
N_VALUE_POINTER=5
N_VALUE_REOWNED=false
NO_PADDING=true
NO_PREFIX_SELECTION=true
NO_DOWNSTREAM_SELECTION=true
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET=UNRATIFIED
POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY=true
ACTIVE_SET_POLICY_ADOPTION=UNPROVEN
ACTIVE_SET_POLICY_RATIFIED=false
CENSUS_CLASS=INVENTORY_ONLY_NO_POLICY_CHOICE
COOLDOWN_RATIFIED=false
TURNOVER_RATIFIED=false
EGRESS_ID=MF_SINGLE_EGRESS_V1
HANDOFF_INTENDED_SEMANTIC_OBJECT=AUTHORITATIVE_NEXT_ACTIVE_SET
HANDOFF_CURRENT_ENVELOPE_CLASS=BOUND_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_REFERENCE
HANDOFF_ENVELOPE_IS_NOT_YET_ACTIVE_SET_DTO=true
EXECUTING_MODEL_HANDOFF_CONSUMER=UNBOUND
PDF_STEP_3_MEMBERSHIP_ROTATION_OWNERSHIP=CLOSED
PDF_STEP_4_ANTI_CHURN_CENSUS=CLOSED
PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=UNRESOLVED
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=false
OWNER_DECISION_SURFACE_STATUS=PREPARED_NOT_RATIFIED
OWNER_DECISION_COUNT=3
OWNER_DECISION_IDS=AS05-D01,AS05-D02,AS05-D03
NEXT_CANONICAL_DECISION=NOT_NAMED_HERE
THIS_PERSIST_DOES_NOT_CLOSE_PDF_STEP_5=true
```

Owner-GO
`OWNER_GO_PDF_STEP_3_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_V1`
binds PDF-Step-3 ownership of the authoritative Next Active Set inside
the isolated ranking/selection domain. This file does **not** replace
§4.5–§4.5.5, does **not** ratify anti-churn, does **not** re-own
`N_VALUE`, does **not** apply isolated POLICY_A to this Active Set,
does **not** join a host, does **not** rewire Cap 2.3 or Cap 2.4, and
does **not** unlock G13. Workpackage
`PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION_DECISION_PACKAGE_V1`
adds only the non-operative §7 decision surface. PDF Step 5 remains
`UNRESOLVED`.

Master Runbook SSOT pointer: §4.5 / §4.5.6.

Typed validator:
`src&#47;ops&#47;mf_authoritative_next_active_set_ownership_contract_v1.py`.

## 1. Purpose

Fill the previously unbound PDF-Step-3 decision: the Membership /
Rotation Controller **may** own the authoritative Next Active Set
inside the ranking/selection domain.

```text
PURPOSE=BIND_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_WITHOUT_ROTATION_POLICY_OR_JOIN
NOT_PURPOSE=RATIFY_ANTI_CHURN_WIRE_CAP23_WIRE_CAP24_UNLOCK_G13_OR_NAME_CONSUMER
EPISTEMIC_CLASS=OWNER_DECISION_PERSISTED_AS_SUBORDINATE_CONTRACT
```

## 2. Object classes that must not collapse

```text
RANKED_CANDIDATE_CONTEXT
≠ NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT
≠ AUTHORITATIVE_NEXT_ACTIVE_SET
```

| Class | Owner | Selection authority | Notes |
|---|---|---|---|
| Ranked candidate context | Cap 2.2 productive ranking | false | Top-20 candidate context only |
| Non-authoritative membership context | isolated membership-context artifact | false | `MF_MEMBERSHIP_CONTEXT_V1`; not renamed |
| Authoritative Next Active Set | `ops.mf_membership_rotation_controller_v1` | true inside isolated domain | this contract; rotation fail-closed |

Existing `MF_MEMBERSHIP_CONTEXT_V1` artifacts are **not** this Active
Set. This persist does **not** silently rename them.

## 3. Controller ownership

```text
MEMBERSHIP_ROTATION_CONTROLLER_MAY_OWN_AUTHORITATIVE_NEXT_ACTIVE_SET=true
CONTROLLER_OWNS=INCUMBENT_VS_CHALLENGER_RECONCILIATION_AUTHORITY
CONTROLLER_OWNS=NEXT_ACTIVE_SET_DETERMINATION_AUTHORITY
CONTROLLER_OWNS=AUTHORITATIVE_SELECTED_MEMBERSHIP_STATE_INSIDE_ISOLATED_DOMAIN
CONTROLLER_MUST_NOT_OWN=ORDERS_POSITIONS_VENUE_RISK_SIZING_PRETRADE_LIVE_CANARY
```

Reconciliation **authority** is bound. Reconciliation **behavior**
remains fail-closed until PDF Step 5 ratifies rotation/anti-churn for
this Active Set. Isolated POLICY_A remains the policy of the
non-authoritative membership selector. It is **not** automatically the
policy of this Active Set.

## 4. Handoff alignment

`MF_SINGLE_EGRESS_V1` remains the unique egress identity.

The current WP-MF-05 envelope **cannot** represent this Active Set
(`selection_authority=false`; payload class remains non-authoritative
membership-context reference). Smallest compatible evolution without
a second egress:

```text
EGRESS_ID=MF_SINGLE_EGRESS_V1
HANDOFF_INTENDED_SEMANTIC_OBJECT=AUTHORITATIVE_NEXT_ACTIVE_SET
HANDOFF_CURRENT_ENVELOPE_CLASS=BOUND_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_REFERENCE
HANDOFF_ENVELOPE_IS_NOT_YET_ACTIVE_SET_DTO=true
EXECUTING_MODEL_HANDOFF_CONSUMER=UNBOUND
HANDOFF_TO_SINGLE_EXECUTION_SELECTION=UNRESOLVED
PARALLEL_HANDOFFS=FORBIDDEN
```

No productive consumer is named.

## 5. Non-claims

```text
ANTI_CHURN_POLICY_CHANGED=false
POLICY_A_IMPORTED_AS_ACTIVE_SET_POLICY=false
ACTIVE_SET_POLICY_ADOPTION=UNPROVEN
ACTIVE_SET_POLICY_RATIFIED=false
CENSUS_CLASS=INVENTORY_ONLY_NO_POLICY_CHOICE
NUMERIC_N_CHANGED=false
CAP23_REWIRED=false
CAP24_REWIRED=false
G13_UNLOCK=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
PRODUCTIVE_INTEGRATION_STARTED=false
HOST_JOIN=false
OVERREAD_AS_PDF_STEP_5_CLOSE=FORBIDDEN
OVERREAD_AS_POLICY_A_ADOPTION=FORBIDDEN
OVERREAD_AS_CENSUS_CLOSE_EQUALS_POLICY_RATIFICATION=FORBIDDEN
OVERREAD_AS_DECISION_PACKAGE_EQUALS_POLICY_RATIFICATION=FORBIDDEN
OVERREAD_AS_MEMBERSHIP_CONTEXT_RENAME=FORBIDDEN
OVERREAD_AS_CAP23_IMPORT=FORBIDDEN
```

## 6. Hard stop

```text
PDF_STEP_3_MEMBERSHIP_ROTATION_OWNERSHIP=CLOSED
PDF_STEP_4_ANTI_CHURN_CENSUS=CLOSED
CENSUS_CLASS=INVENTORY_ONLY_NO_POLICY_CHOICE
ACTIVE_SET_POLICY_ADOPTION=UNPROVEN
ACTIVE_SET_POLICY_RATIFIED=false
PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=UNRESOLVED
OWNER_DECISION_SURFACE_STATUS=PREPARED_NOT_RATIFIED
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=false
NEXT_IMPLEMENTATION_AUTHORIZED=false
HARD_STOP_AFTER_THIS_CONTRACT=true
```

Owner-GO
`OWNER_GO_PDF_STEP_4_ANTI_CHURN_CENSUS_CANONICAL_CLOSE_V1`
closes PDF Step 4 as an **inventory census** only. That persist does
**not** ratify anti-churn for the authoritative Next Active Set, does
**not** adopt isolated POLICY_A, and does **not** import Cap 2.3.

Workpackage
`PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION_DECISION_PACKAGE_V1`
persists the **non-operative** Owner decision surface in §7. This
persist does **not** close PDF Step 5, does **not** choose a policy,
does **not** set `ACTIVE_SET_POLICY_RATIFIED=true`, and does **not**
allow PDF Step 7 runtime implementation.

## 7. PDF Step 5 Owner Decision Package (not ratification)

```text
DOCUMENT_EFFECT=NON_OPERATIVE_OWNER_DECISION_SUPPORT_ON_EXISTING_OWNER_SURFACE
EPISTEMIC_CLASS=OWNER_DECISION_SURFACE_PREPARED_NOT_RATIFIED
OWNER_DECISION_SURFACE_STATUS=PREPARED_NOT_RATIFIED
PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=UNRESOLVED
ACTIVE_SET_POLICY_RATIFIED=false
ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET=UNRATIFIED
POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY=true
ACTIVE_SET_POLICY_ADOPTION=UNPROVEN
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=false
EXECUTION_AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
NUMERIC_N_REOPENED=false
N_VALUE_REOWNED=false
PDF_CANONICAL_AUTHORITY=false
PDF_DEFAULTS_IMPORTED=false
```

This section names the **smallest** Owner-policy questions that the
Step-4 census and current canonical constraints actually require
before rotation/anti-churn for the authoritative Next Active Set can
leave fail-closed. It does **not** answer them. Isolated POLICY_A
remains the policy of the non-authoritative membership selector only.

The five PDF-named mechanism titles (hysteresis, minimum holding,
challenger margin, consecutive confirmation, replacement-pending) are
**not** automatically required independent Owner fields. Numeric N
is a separate already-closed track and is **not** reopened here.

### 7.1 Binding matrix (census classes; not a policy choice)

| Mechanism | Canonical bind today | Historical / non-authority | PDF Leitzielbild only | Open or contradictory | Independent Step-5 field? |
|---|---|---|---|---|---|
| Hysteresis | Isolated POLICY_A rank-improvement vs displaced incumbent; `CHALLENGER_MARGIN_VALUE=1`; selector-owned; **not** Active Set policy | Cap 2.3 `hysteresis_rank_improvement=1` (N=1 SSF; not imported); Master-V2 / switch-gate hysteresis `OUT_OF_DOMAIN`; pre-#6381 unratified MF numerics | Named by Owner PDF as a target-architecture concern | Active Set bind `UNRATIFIED`; R6 `MF_ROTATION_HYSTERESIS_POLICY_RATIFIED=false` is a different graph | No; consequence of AS05-D01 |
| Minimum holding | Isolated POLICY_A `MINIMUM_HOLDING_VALUE=2` ranking observations; not position holding | Cap 2.3 `min_holding_period_seconds=3600.0` not imported; Cap 0.4 reminder not numeric authority | Named by Owner PDF | Active Set bind `UNRATIFIED` | No; consequence of AS05-D01 |
| Challenger-vs-incumbent score/rank margin | Isolated POLICY_A rank margin 1; score-margin forbidden while consume-Cap-2.2-order holds | Cap 2.3 rank-improvement 1 is not an import proof | PDF names challenger/incumbent margin as a concern | Score-margin remains forbidden unless OD03 is separately reopened (not this package) | No; rank-margin rides with AS05-D01; score-margin is not admissible here |
| Consecutive ranking confirmation | Isolated POLICY_A `CONSECUTIVE_CONFIRMATION_COUNT=1` (current observation sufficient; min-hold blocks one-cycle oscillation) | none proven as a second MF confirmation engine | Named by Owner PDF as a distinct lever | Active Set bind `UNRATIFIED` | No; rides with AS05-D01 |
| Replacement-pending state | OD05 `NO_INDEPENDENT_PENDING_STATE_REQUIRED` for `CURRENT_ISOLATED_MF_MODEL`; Cap 2.3 `REPLACEMENT_PENDING` not imported | Cap 2.3 open-position pending is productive-SSF historical/current outside this graph | Named by Owner PDF | OD05 scope does **not** automatically cover the Active Set object class | Yes; AS05-D03 (scope only, not a pending-machine design) |
| Tie / equality | OD03: consume Cap-2.2 origin order as membership order; MF-own tie-break `NOT_REQUIRED` | Cap 2.3 tie-break order not imported | none proven as PDF-numeric default in this persist | Inventing an MF tie-break is forbidden | No; not a Step-5 field |
| Admission / replacement ordering | Isolated POLICY_A precedence 1–7 including forced-removal bypass and underfill prefix-fill | none as Active Set law | PDF does not become ordering authority | Active Set ordering unbound until a policy is adopted | No; consequence of AS05-D01 |
| Deterministic replay / explanation | Isolated previous→current replay proven for membership-context + POLICY_A; `RUNTIME_AUTHORIZED=false` | execution/host replay packs `OUT_OF_DOMAIN` | PDF Step 7 is later runtime | Active Set rotation has no ratified behavior to replay | Constraint on any later close; not an independent policy choice |
| State ownership / temporal identity | Step 3: controller owns Active Set state; isolated selector `SELECTOR_STATE_OWNER=NONE_FOR_MEMBERSHIP_IDENTITY`; membership-context temporal identity bound | Isolated selector is a forbidden Active Set owner | PDF controller-owns-reconciliation is already bound as authority, not behavior | Who **evaluates** anti-churn for Active Set is not derivable from current binds | Yes; AS05-D02 |
| Interaction with `AT_MOST_N` | `CARDINALITY_MODE=AT_MOST_N`; `N_VALUE_POINTER=5`; `N_VALUE_REOWNED=false`; no padding; no exact-N | Cap 0.4 reminder is not this N authority | PDF N=5 is Leitzielbild only and is **not** re-adjudicated | Underfill prefix-fill is POLICY_A semantics, not an N reopen | No; pointer only; Numeric-N track stays closed |

Cooldown and turnover remain an unratified selector concept-family
even inside isolated POLICY_A. They are **not** promoted into this
minimal Step-5 surface, because no repo-supported numeric alternative
exists and invention is forbidden.

### 7.2 Minimal Owner decisions

#### AS05-D01 — Adopt isolated POLICY_A for the authoritative Active Set?

```text
DECISION_ID=AS05-D01
STATUS=UNRESOLVED
NOT_DERIVABLE_FROM_EXISTING_AUTHORITY=true
PRECISE_SEMANTIC_QUESTION=Shall isolated-MF POLICY_A be adopted as the anti-churn admission policy of the authoritative Next Active Set object class, or shall that object class remain fail-closed without a ratified anti-churn policy?
```

Admissible alternatives (repo-/evidence-supported only):

| Alternative | Support | Meaning |
|---|---|---|
| `DO_NOT_ADOPT_REMAIN_FAIL_CLOSED` | Current canonical state: `ACTIVE_SET_POLICY_RATIFIED=false`; `ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5` | No Active Set rotation behavior; later Step 7 remains forbidden |
| `ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET` | Isolated POLICY_A is ratified in semantics §1.17 for the **other** object class | Would be a **new** bind of an existing rule set onto `AUTHORITATIVE_NEXT_ACTIVE_SET`; not automatic |

Not admissible in this package:

- Cap 2.3 / SSF hysteresis, min-hold, or `REPLACEMENT_PENDING` import
- Double-Play / switch-gate / research cooldown import
- Score-margin while OD03 consume-Cap-2.2-order holds
- PDF numeric defaults
- Invented custom numerics, subset-policies, or a second selection owner

Canonical constraints:

```text
POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY=true
OVERREAD_AS_POLICY_A_EQUALS_ACTIVE_SET_POLICY=FORBIDDEN
SSF_SEMANTICS_IMPORTED=false
MF_RERANKING_ALLOWED=false
SECOND_SELECTION_DECISION_DOWNSTREAM=false
CARDINALITY_MODE=AT_MOST_N
N_VALUE_REOWNED=false
```

Consequences / tradeoffs:

- `DO_NOT_ADOPT` keeps rotation fail-closed; PDF Step 7 stays false.
- `ADOPT_POLICY_A_UNCHANGED` would import hysteresis rank-margin 1,
  min-hold 2 ranking observations, confirmation count 1, multiple
  replacements per cycle, forced-removal bypass, and underfill
  prefix-fill **as Active Set admission rules**. That still would not
  unlock G13, host join, Cap-2.3/2.4 rewire, or execution.
- AS05-D02 remains unresolved if AS05-D01 is adopt, because selector
  vs controller ownership must not collapse.

Unresolved dependencies: AS05-D02 if adopt; AS05-D03 scope
confirmation either way. Cooldown/turnover stay unratified unless a
later separate Owner-GO names numerics.

Forbidden implications: this row is not a ratification; choosing
here is reserved for a later Owner-GO that closes PDF Step 5.

Evidence pointers:

- Master Runbook §4.5.3 / §4.5.6
- Semantics §1.17 / §1.22 / §7 / §8
- This file header + §3 + §5
- Step-4 census close: `CENSUS_CLASS=INVENTORY_ONLY_NO_POLICY_CHOICE`

#### AS05-D02 — Who evaluates anti-churn for the authoritative Active Set?

```text
DECISION_ID=AS05-D02
STATUS=UNRESOLVED
NOT_DERIVABLE_FROM_EXISTING_AUTHORITY=true
PRECISE_SEMANTIC_QUESTION=If and only if a later Owner-GO adopts an anti-churn policy for the authoritative Next Active Set, which already-bound owner may evaluate admission or non-admission of Active Set membership changes without creating a second selection owner and without making rotation the anti-churn owner?
```

Admissible alternatives (constraints only; no default):

| Alternative | Support | Caveat |
|---|---|---|
| Keep evaluation unbound while AS05-D01 remains `DO_NOT_ADOPT` | Current fail-closed; no evaluator needed until a policy exists | Compatible with today |
| Name an evaluator only after AS05-D01 adopt | Step 3 binds controller **authority**; isolated selector owns isolated anti-churn; isolated selector is a **forbidden Active Set owner** | No currently named evaluator identity is already legal for this object class |

Canonical constraints:

```text
ANTI_CHURN_OWNER=SELECTOR
ROTATION_IS_NOT_ANTI_CHURN_OWNER=true
NEXT_ACTIVE_SET_AUTHORITY_OWNER=ops.mf_membership_rotation_controller_v1
ONE_ACTIVE_SET_STATE_OWNER=true
FORBIDDEN_ACTIVE_SET_OWNER_INCLUDES=ops.mf_membership_selector_and_rotation_runtime_contract_v1
SECOND_SELECTION_DECISION_DOWNSTREAM=false
```

This question is **not** derivable from existing authority: the
controller may own Active Set reconciliation authority, and the
selector may own isolated anti-churn, but those binds do not name a
legal Active Set anti-churn evaluator.

Forbidden implications: do not silently reuse the isolated selector
as Active Set owner; do not make rotation an anti-churn owner; do
not create a second ranking/selection owner; do not join execution.

#### AS05-D03 — Does OD05 pending-scope extend to the Active Set?

```text
DECISION_ID=AS05-D03
STATUS=UNRESOLVED
NOT_DERIVABLE_FROM_EXISTING_AUTHORITY=true
PRECISE_SEMANTIC_QUESTION=Does OD05 close-class NO_INDEPENDENT_PENDING_STATE_REQUIRED extend to the authoritative Next Active Set object class, or is a later membership-only pending analog still an open class for this object class?
```

Admissible alternatives:

| Alternative | Support | Caveat |
|---|---|---|
| `EXTEND_OD05_NO_INDEPENDENT_PENDING_TO_ACTIVE_SET` | OD05 is closed for the current isolated MF model; POLICY_A already forbids an independent pending state in that model | Scope text is `CURRENT_ISOLATED_MF_MODEL`; extension is a new bind |
| `LEAVE_PENDING_CLASS_UNBOUND_FOR_ACTIVE_SET` | Active Set currently has no pending state bound; Cap 2.3 pending is not imported | Does not design a pending machine |

Not admissible: importing Cap 2.3 `REPLACEMENT_PENDING`; inventing a
pending state machine in this package.

Canonical constraints:

```text
OPEN_DECISION_05_SCOPE=CURRENT_ISOLATED_MF_MODEL
CAP23_REPLACEMENT_PENDING_IMPORTED=false
REPLACEMENT_PENDING_IS_NOT_MEMBERSHIP_ROTATION=true
```

This is a **scope** question, not a runtime design. It is required
because OD05 does not automatically cover this object class.

### 7.3 Explicitly out of this minimal surface

```text
NOT_AN_INDEPENDENT_STEP_5_FIELD=HYSTERESIS_NUMERICS
NOT_AN_INDEPENDENT_STEP_5_FIELD=MINIMUM_HOLDING_NUMERICS
NOT_AN_INDEPENDENT_STEP_5_FIELD=SCORE_MARGIN
NOT_AN_INDEPENDENT_STEP_5_FIELD=CONFIRMATION_COUNT
NOT_AN_INDEPENDENT_STEP_5_FIELD=COOLDOWN_TURNOVER_NUMERICS
NOT_AN_INDEPENDENT_STEP_5_FIELD=NUMERIC_N
NOT_AN_INDEPENDENT_STEP_5_FIELD=CAP23_IMPORT
NOT_AN_INDEPENDENT_STEP_5_FIELD=PDF_DEFAULT_NUMERICS
NOT_AN_INDEPENDENT_STEP_5_FIELD=STEP_7_RUNTIME
```

Fail-closed after this persist:

```text
OVERREAD_AS_PDF_STEP_5_CLOSE=FORBIDDEN
OVERREAD_AS_DECISION_PACKAGE_EQUALS_POLICY_RATIFICATION=FORBIDDEN
OVERREAD_AS_AS05_D01_CHOICE=FORBIDDEN
OVERREAD_AS_POLICY_A_ADOPTION=FORBIDDEN
OVERREAD_AS_PDF_FIVE_MECHANISMS_ARE_REQUIRED_FIELDS=FORBIDDEN
OVERREAD_AS_STEP_7_ALLOWED=FORBIDDEN
```
