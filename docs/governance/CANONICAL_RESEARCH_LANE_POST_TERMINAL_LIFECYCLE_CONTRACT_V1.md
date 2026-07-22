---
docs_token: DOCS_TOKEN_CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1
STATUS: DEFINITION_ONLY_SHARED_LIFECYCLE_CONTRACT
scope: research, offline-only, non-authorizing, conceptual governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Canonical research-lane post-terminal lifecycle contract v1

Shared conceptual and machine-readable grammar for research-lane behavior after
the active hypothesis becomes terminal and both open and preregistered candidate
inventories may be empty.

This slice defines the lifecycle model only. It does **not** migrate
Entry-Eligibility or Exit-Efficiency backlog SSOTs.

## Binding

- Contract ID: `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`
- SSOT: `config&#47;research&#47;canonical_research_lane_post_terminal_lifecycle_contract_v1.json`
- Validator: `src&#47;research&#47;canonical_research_lane_post_terminal_lifecycle_contract_v1.py`
- Tests: `tests&#47;research&#47;test_canonical_research_lane_post_terminal_lifecycle_contract_v1.py`

## Design questions resolved

### 1) Three conceptual lane postures

| Posture | Canonical state | Meaning |
|---|---|---|
| Backlog actively open with candidates | `OPEN_BACKLOG` | At least one open unpreregistered candidate and&#47;or at least one preregistered hypothesis exists. |
| Lane awaiting an explicitly named successor hypothesis | `AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS` | Inventories empty; all existing hypotheses terminal; operator explicitly declared waiting semantics; no successor identity yet. |
| Lane intentionally closed | `LANE_CLOSED_NO_FURTHER_RESEARCH` | Explicit closeout decision recorded; no further research action; reopen requires a new explicit hypothesis identity. |

Holding state when terminalization empties inventory before an operator chooses
awaiting vs closeout vs successor creation:

- `POST_TERMINAL_OPERATOR_DECISION_REQUIRED`

### 2) Is `OPEN_BACKLOG` valid when inventories are empty?

**No.**

`OPEN_BACKLOG` is valid only when:

- `open_unpreregistered_candidates` count &gt; 0, and&#47;or
- `preregistered_hypotheses` count &gt; 0

If open count = 0, preregistered count = 0, and all existing hypotheses are
terminal, `OPEN_BACKLOG` is invalid
(`OPEN_LANE_EMPTY_INVENTORY_WITHOUT_WAITING_SEMANTICS`).

### 3) Exhaustive post-terminal transitions for PASS and FAIL

Shared for `PASS` and `FAIL` (and infrastructure-failure result classes mapped
onto the FAIL empty-inventory operator path):

1. Seal historical artifacts (immutable).
2. If inventory remains non-empty → deterministic next: remain&#47;enter `OPEN_BACKLOG`.
3. If inventory is empty → deterministic next is **not** close or await.
   Required state: `POST_TERMINAL_OPERATOR_DECISION_REQUIRED`.
   Enumerated operator decisions only:
   - `DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS`
   - `CLOSE_LANE_NO_FURTHER_RESEARCH`
   - `CREATE_SUCCESSOR_HYPOTHESIS` (requires `hypothesis_id` + mechanism)

PASS alone does not imply holdout, promotion, or runtime.
FAIL alone does not authorize retuning the same hypothesis identity.

### 4) Operator-decision contract

- GO alone is never executable without a concrete target.
- Successor creation requires explicit `hypothesis_id` and mechanism definition.
- Lane closeout requires an explicit closeout decision.
- Reopening a closed lane requires a new explicit hypothesis identity
  (`REOPEN_CLOSED_LANE_WITH_NEW_HYPOTHESIS_IDENTITY`).

### 5) Historical immutability and live-mirror policy

Immutable after seal:

- preregistration economic contracts and digests
- evaluation evidence, metrics, run-slot claims, result digests
- executed authorization&#47;ratification snapshots
- executed operator-clarification authority snapshots

Mutable only on live lane surfaces:

- lane backlog status
- lane next canonical step
- lane operator decision records

Live authority and ratification objects **must not** be mutated after execution
to mirror live next-step changes.

Authorization summaries are
`HISTORICAL_SNAPSHOT_NOT_LIVE_MIRROR`.

### 6) Ownership

| Concern | Owner |
|---|---|
| Canonical status vocabulary &#47; transition legality | this shared lifecycle contract |
| Current lane status value | lane-specific backlog SSOT |
| Post-terminal transition application | lane backlog SSOT under this contract |
| Successor identity | explicit operator decision + new preregistration artifact |
| Closeout &#47; reopen decisions | explicit operator decision on lane backlog SSOT |

### 7) TOTALITY_INVARIANT

Every reachable canonical lane state has exactly one of:

1. a deterministic canonical next transition, or
2. an explicitly enumerated operator decision set, or
3. a terminal closed state.

Mapping:

- `OPEN_BACKLOG` → deterministic&#47;enumerated within inventory
- `POST_TERMINAL_OPERATOR_DECISION_REQUIRED` → enumerated operator decision
- `AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS` → enumerated operator decision
- `LANE_CLOSED_NO_FURTHER_RESEARCH` → terminal closed state

### 8) Invalid states

- executable GO with no target
- auto-created successor
- open lane with empty inventory and no explicit waiting&#47;closed semantics
- closed lane with an implicit successor
- mutation of historical evaluation evidence
- awaiting without explicit waiting decision
- closed without explicit closeout decision

## Allowed transitions

- `OPEN_BACKLOG` → `OPEN_BACKLOG` (inventory remains non-empty after terminal)
- `OPEN_BACKLOG` → `POST_TERMINAL_OPERATOR_DECISION_REQUIRED` (terminal + empty)
- `POST_TERMINAL_OPERATOR_DECISION_REQUIRED` → `AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS`
- `POST_TERMINAL_OPERATOR_DECISION_REQUIRED` → `LANE_CLOSED_NO_FURTHER_RESEARCH`
- `POST_TERMINAL_OPERATOR_DECISION_REQUIRED` → `OPEN_BACKLOG` via `CREATE_SUCCESSOR_HYPOTHESIS`
- `AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS` → `OPEN_BACKLOG` via `CREATE_SUCCESSOR_HYPOTHESIS`
- `AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS` → `LANE_CLOSED_NO_FURTHER_RESEARCH`
- `LANE_CLOSED_NO_FURTHER_RESEARCH` → `OPEN_BACKLOG` via reopen + new hypothesis identity

## Forbidden transitions &#47; actions

- auto-create successor
- executable GO without target
- `OPEN_BACKLOG` with empty inventory
- closed lane with implicit successor
- mutate historical evaluation evidence or preregistration digests
- auto-close or auto-await on terminal

## Migration deferred

Migration deferred (`migrate_in_this_slice: false`):

- Entry-Eligibility backlog currently uses `OPEN_BACKLOG` with empty inventory
  and a non-canonical cross-lane token `CLOSED_NO_OPEN_CANDIDATES`.
- Exit-Efficiency backlog currently uses `OPEN_BACKLOG` with empty inventory
  after V8 `TERMINAL_PASS`.

Both are compatibility consequences identified by this contract and require
separate operator-authorized migration slices. Historical V8 economic,
evaluation, run-slot, and preregistration artifacts remain immutable.

## Safety

- `LIVE_AUTHORIZED=false`
- `ORDERS_ALLOWED=false`
- `SCHEDULER_RUNTIME_ALLOWED=false`
- No runner, run slot, holdout, promotion, shadow, testnet, or capital activation
  in this slice.
