# Peak_Trade Canonical Presentation Implementation Runbook

## Ratification Status

| Field | Ratified value |
|---|---|
| Document status | **CANONICAL — PRESENTATION CAPABILITY ONLY** |
| Repository document path | `docs/runbooks/canonical/PEAK_TRADE_CANONICAL_PRESENTATION_IMPLEMENTATION_RUNBOOK.md` |
| Document class | `CANONICAL_PRESENTATION_IMPLEMENTATION_RUNBOOK` |
| Authority scope | `PRESENTATION_CAPABILITY_ONLY` / `MARKET_DASHBOARD_PRESENTATION_CAPABILITY` |
| Authority effect | `PRESENTATION_CAPABILITY_SEMANTIC_AUTHORITY_ONLY` |
| Runtime authorization effect | **NONE** |
| Trading SSOT role | **NOT SSOT** — productive trading authority chain remains the only business SSOT |
| Dashboard role | **PURE_CONSUMER** |
| Dashboard authority effect | **NONE** |
| External reference source (import provenance only) | `/Users/frnkhrz/Desktop/Presentation_Implementation_Runbook_Canonical_v5_Reviewed.md` |
| External reference SHA-256 | `ea21303a1f68a3248e1842705c3823064ab2bf0371ebde86c1531924e48f1184` |
| Initial repository import authorized by Owner | **YES** (`OWNER_GO_INITIAL_PRESENTATION_RUNBOOK_REPO_IMPORT_AND_RATIFICATION`) |
| Import base SHA / origin/main SHA | `6a9a3f10b81ab8d870245dc10ea74433e1f5365b` |
| Family-plan discovery SHA | `6a9a3f10b81ab8d870245dc10ea74433e1f5365b` |
| Import date (UTC) | `2026-08-04T20:18:40Z` |
| Imported content digest SHA-256 | `7bbf035ec8dac90cf3db675bfdd81165ca93a57cd2582302d91a9c9237d2db3e` |
| Prior family-matrix HEAD (historical) | `8c02f8793411939149eb7f33d6877a68a23a727f` (`#5710`) |
| Durable inventory artifact | `docs/ops/market_dashboard/market_dashboard_missing_source_not_bound_inventory_v1/INVENTORY.json` |
| Inventory generated at | `2026-08-04T18:30:57.619368Z` |
| Inventory presentation elements | `73` |
| Inventory `MISSING_SOURCE` count | `50` |
| Inventory `NOT_BOUND` count | `18` (baseline; B2 live-DOM recount after `#5710` recorded `17`) |
| Ratified family count | `18` |
| Families analyzed (projection octet) | `8` |
| Octet materializers present (library entrypoints) | **8** (non-authoritative) |
| Non-test AST call-sites for all eight materializers | **0** |
| Materializer invocation paths | **TEST_ONLY_PATH** for all eight |
| Active archive source siblings absent | **7** |
| Active archive presentation projections absent | **8** |
| Materializers executed | **false** |
| Active archive written | **false** |
| Runtime changed | **false** |
| Producer changed | **false** |
| Canonical read-model changed | **false** |
| Trading logic changed | **false** |
| Family-plan status | `READ_ONLY_BOUNDED_FAMILY_PLAN_COMPLETE` |
| Family-plan verdict | `MIXED_BLOCKERS_FAMILY_PLAN_READY_NO_IMPLEMENTATION_AUTHORIZED` |
| B3 authorized | **false** |
| Trading-system mutation authorized | **NO** |
| Implementation authorized by this document | **NO** |

Discovery / archive evidence owners (reuse; not parallel SSOT):

- `docs/ops/market_dashboard/market_dashboard_projection_octet_runtime_verify_v1/` (B2; `#5711`)
- `docs/ops/market_dashboard/market_dashboard_projection_octet_materialization_path_discovery_v1/` (path discovery; `#5712`)

### Authority boundary (immutable)

``` text
PRODUCTIVE_TRADING_SSOT
→ AUTHORIZED_READMODEL_OR_PRESENTATION_PROJECTION
→ PURE_CONSUMER_DASHBOARD

DASHBOARD_ROLE=PURE_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
```

This document is canonical exclusively for the **Market Dashboard Presentation capability**.

It is not a trading SSOT, runtime SSOT, producer SSOT, canonical-readmodel SSOT, risk/safety/execution authority, or business decision authority.

It does not ratify, replace, reinterpret, or modify any trading, decision, risk, safety, execution, economic, runtime, producer, read-model, or authority contract.

After import, this repository file is fully self-contained. No runtime dependence on the external Desktop reference remains.

The numerical `MISSING_SOURCE` and `NOT_BOUND` baseline remains an inventory snapshot. While all eight required projection artifacts remain absent, a further live-DOM reconcile is not a useful next implementation step; the existing `MISSING_SOURCE` display is correct.

---

# 0. Absolute Consumer Contract

This section has the highest architectural authority within this runbook and supersedes every implementation detail below it.

## 0.1 Single Source of Truth

The productive trading system is the only business authority.

All trading truth originates exclusively from the productive trading architecture.

The Dashboard is never a business authority.



### 0.1.1 Immutable SSOT and Authority Chain

For Peak_Trade, the Single Source of Truth (SSOT) is exclusively the productive trading authority chain.

The SSOT includes only authoritative components required for the trading lifecycle, including:
- Universe selection and the canonical selected future;
- the ranking process (e.g. Top-20 → Top-5) insofar as it is part of the productive trading pipeline;
- the currently authorized selected future passed into the downstream trading pipeline;
- Bull/Bear regime;
- Double Play;
- Dynamic Scope;
- Confirmation;
- Canonical Decision;
- Risk, Safety, Position, Execution, Reconciliation and Exit;
- other explicitly authorized productive authority components.

The current implementation may operate on a single selected future. Future expansion to multiple concurrently tradable futures does not change this authority model.

Presentation projections, Dashboard code, serializers, presenters, templates, JavaScript, DOM state, caches and browser state are never part of the SSOT. They are read-only presentation artifacts.

Data flow is strictly one-way:

Trading SSOT → Authorized Read Model / Presentation Projection → Dashboard.

Reverse authority is permanently forbidden.

## 0.2 Dashboard Role

The Dashboard is a pure consumer.

Its permitted responsibilities are limited to:

- consuming already authorized canonical information;
- loading authorized durable presentation projections;
- binding existing canonical fields;
- serializing display payloads without changing meaning;
- formatting and visualizing canonical values;
- honestly displaying unavailable information.

Nothing else is permitted.

## 0.3 Absolute Prohibitions

The Dashboard shall never:

- create business truth;
- infer business truth;
- derive trading decisions;
- introduce business semantics;
- compensate for missing upstream information;
- generate substitute values;
- invent projections;
- reinterpret canonical states;
- select a more convenient source;
- discover or choose “latest” evidence implicitly;
- bypass an authorized durable projection;
- autoload live authority state where the contract requires a presentation projection;
- become an authority for any field;
- mutate productive runtime state;
- affect trading behavior.

If canonical truth does not exist or an authorized durable projection is absent, the Dashboard shall display the applicable unavailable state.

## 0.4 Immutable Consumer Boundary

The permitted architecture is:

**Trading Authority  
→ Canonical Runtime State  
→ Canonical Read Model or explicitly authorized source artifact  
→ Authorized Durable Presentation Projection  
→ Dashboard Producer Binding  
→ Presenter and Serializer  
→ Dashboard Visualization**

A family may consume a canonical read model directly only where the ratified family contract explicitly permits direct read-model binding.

No shortcut may be inferred from UI proximity or implementation convenience.

## 0.5 Upstream Ownership

Missing business information is always an upstream concern.

Presentation shall never solve upstream architectural gaps.

Creation, activation, scheduling, or modification of an upstream producer, runtime materializer, canonical read model, business projection, authority, or business field requires a separate explicit Owner-GO outside this capability.

## 0.6 Conflict Resolution

Whenever any proposal conflicts with this contract:

1. this contract prevails;
2. implementation stops;
3. no presentation workaround is introduced;
4. the unresolved point is recorded;
5. an explicit Owner decision is required before any upstream change.

This contract remains in force unless explicitly superseded by a later Owner-ratified architecture document.

---

# 1. Operator Directives

## 1.1 Real Local Repository Only

All repository work shall be performed exclusively in the real local repository with its real `.git` directory.

The Cursor Sandbox and ChatGPT Sandbox shall not be used for Git operations.

## 1.2 Real Terminal Only

Repository, Git, build, test, verification, runtime, archive, and discovery commands shall be executed through the operator’s real local macOS terminal or a real local Cursor terminal attached to the repository.

No emulated Git environment may be treated as repository evidence.

## 1.3 Next Command Policy

After each Cursor result, provide the next bounded Cursor command when a concrete next action is supported.

Do not replace an executable next step with general recommendations.

## 1.4 Immediate Merge Policy

When all required checks are green, the pull request is mergeable, and no blocker exists, proceed directly with Owner squash merge and post-merge closeout.

Do not add redundant review-only loops after merge readiness has been established.

## 1.5 Small, Bounded Pull Requests

Each pull request shall implement one clearly defined presentation objective.

No unrelated improvement, opportunistic refactor, upstream behavior change, or semantic expansion is allowed.

## 1.6 Evidence Before Claim

A path, field, family, projection, PR number, archive artifact, or live state shall be described as present only when repository or runtime evidence supports that claim.

Unknown values remain unknown.

---

# 2. Trading Logic Protection

The productive trading system is outside the scope of this capability.

Presentation work must not alter:

- trading logic;
- signal generation;
- the Decision Engine;
- Bull/Bear logic;
- Double Play logic;
- Dynamic Scope behavior;
- confirmation logic;
- risk management;
- safety mechanisms;
- exit logic;
- position management;
- order intent or order logic;
- execution behavior;
- runtime behavior;
- producer semantics;
- canonical read-model semantics;
- authority chains;
- promotion or autonomy semantics;
- economic policy.

The Dashboard may only consume and visualize authorized output from these domains.

---

# 3. Honest Availability Semantics

The following availability concepts are distinct and shall not be conflated.

## 3.1 `MISSING_SOURCE`

Use when the required canonical read model, authorized source artifact, or durable presentation projection is absent or cannot be loaded.

## 3.2 `NOT_BOUND`

Use when the surface is intentionally not connected, no authorized binding exists, or the field is explicitly retained as unbound.

## 3.3 Empty Display Value

An empty or em-dash display is permitted only where the presentation contract explicitly defines it. It shall not conceal a missing authoritative source.

## 3.4 Implemented Binding Does Not Prove Runtime Availability

A family may have:

- a projection schema;
- a materializer implementation;
- an autobind loader;
- presenter support;
- tests;

and still show `MISSING_SOURCE` because the durable projection artifact is absent from the active archive.

Therefore:

**presentation path implemented** and **runtime artifact available** are separate states.

---

# 4. Mission

The mission is to complete and operate the canonical Market Dashboard Presentation Layer while preserving the productive trading architecture unchanged.

The capability may:

- inventory presentation surfaces;
- classify source families;
- discover existing canonical sources and authorized projections;
- bind existing authorized information;
- correct presentation-only mappings and labels;
- validate rendering and availability behavior;
- record unresolved upstream dependencies.

The capability may not create the upstream truth required to populate the Dashboard.

---

# 5. Canonical Inventory Baseline

## 5.1 Ratified Counts

The repository discovery establishes the following canonical family inventory:

- `18` presentation families;
- `73` presentation elements in the durable inventory;
- `50` `MISSING_SOURCE` elements in the durable inventory snapshot;
- `18` `NOT_BOUND` elements in the durable inventory snapshot;
- `68` unique template `data-mdl-field` values as an additional surface metric.

The 18 families consist of:

- 16 families recorded in the durable `INVENTORY.json`;
- `market_instrument`, additionally proven in the owner registry and producer binding;
- `okx_selected_instrument_ohlcv`, additionally proven across archive binding, presenter, API, JavaScript, and chart tests.

## 5.2 Snapshot Limitation

The counts `50` and `18` were not re-measured from a new live-DOM capture at HEAD `8c02f879...`.

They remain the canonical **inventory baseline**, not a post-`#5710` live-browser assertion.

## 5.3 Inventory Integrity Rule

Exactly 18 families shall remain tracked unless a later repository-backed inventory proves a deliberate family split, merge, addition, or removal.

Any count change must identify:

- the changed inventory artifact;
- the repository SHA;
- the reason;
- the affected family;
- the old and new classification;
- the Owner authorization where architecture is affected.

---

# 6. Canonical Classification Model

Each family shall be assigned exactly one primary roadmap classification:

1. `PRESENTATION_BOUND`
2. `PRESENTATION_BINDABLE_AFTER_EXISTING_PROJECTION_DISCOVERY`
3. `BLOCKED_NO_DURABLE_CANONICAL_PROJECTION`
4. `LABEL_OR_SEMANTIC_CORRECTION_ONLY`
5. `INTENTIONALLY_UNAVAILABLE`
6. `UNRESOLVED_REQUIRES_MORE_REPOSITORY_EVIDENCE`

`PRESENTATION_BOUND` means the repository contains the authorized presentation path. It does not guarantee that the required durable runtime artifact exists in the active archive.

The following states are distinct and must not be conflated:

| State | Meaning |
|---|---|
| `PRESENTATION_BOUND` | Repository path, loader, binder, presenter, or materializer exists. |
| `RUNTIME_ARTIFACT_ABSENT` | The authorized durable projection artifact is not present in the active archive. |
| `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED` | No authorized non-test caller and no authorized active-archive write exist. |
| `UPSTREAM_SOURCE_BLOCKED` | The Presentation capability must not create the missing source sibling itself. |

Additional secondary runtime states that may be recorded:

- `RUNTIME_ARTIFACT_AVAILABLE`
- `RUNTIME_ARTIFACT_ABSENT`
- `RUNTIME_ARTIFACT_NOT_REVERIFIED` (historical only; **not** current for the eight projection families below)
- `DIRECT_READMODEL_AVAILABLE`
- `INTENTIONALLY_NO_ARTIFACT`
- `BLOCKED_MISSING_CANONICAL_SOURCE`
- `FAMILY_SPECIFIC_ADAPTER_REQUIRED`

For the eight projection families listed in Section 7.1 and Section 10A, repository- and archive-backed ratification at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b` supersedes the former unverified-runtime-presence status. Those eight families are now ratified as archive-absent under the family-plan evidence.

---

# 7. Canonical Family Matrix

## 7.1 Summary Matrix

| # | Family | Primary classification | Ratified implementation state | Runtime or remaining blocker |
|---:|---|---|---|---|
| 1 | `market_instrument` | `PRESENTATION_BOUND` | Universe/market identity binding implemented | No binding blocker proven |
| 2 | `universe_selection_rail_facts` | `PRESENTATION_BOUND` | Bound at HEAD by PR `#5710` | No blocker |
| 3 | `okx_selected_instrument_ohlcv` | `PRESENTATION_BOUND` | Chart, volume, live mark, API and JS binding implemented | Depends on durable OHLCV read model |
| 4 | `dynamic_scope` | `PRESENTATION_BOUND` | Projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH` | `RUNTIME_ARTIFACT_ABSENT`; source sibling absent; `BLOCKED_MISSING_CANONICAL_SOURCE`; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`; `UPSTREAM_SOURCE_BLOCKED` |
| 5 | `regime_bull_bear_switch` | `PRESENTATION_BOUND` | Projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH` | `RUNTIME_ARTIFACT_ABSENT`; source sibling absent; `BLOCKED_MISSING_CANONICAL_SOURCE`; legacy route `NON_SOURCE`; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`; `UPSTREAM_SOURCE_BLOCKED` |
| 6 | `canonical_decision` | `PRESENTATION_BOUND` | Projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH` | `RUNTIME_ARTIFACT_ABSENT`; source sibling absent; `BLOCKED_MISSING_CANONICAL_SOURCE`; no decision recomputation; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`; `UPSTREAM_SOURCE_BLOCKED` |
| 7 | `double_play` | `PRESENTATION_BOUND` | Projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH` | `RUNTIME_ARTIFACT_ABSENT`; source sibling absent; `BLOCKED_MISSING_CANONICAL_SOURCE`; `B3_AUTHORIZED=false`; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`; `UPSTREAM_SOURCE_BLOCKED` |
| 8 | `decision_strip_blockers_unbound` | `PRESENTATION_BINDABLE_AFTER_EXISTING_PROJECTION_DISCOVERY` | Presenter already carries blockers; template remains hardcoded `NOT_BOUND` | Requires verified Double Play projection and bounded frontend mapping |
| 9 | `decision_strip_confidence_intentional_unbound` | `INTENTIONALLY_UNAVAILABLE` | Deliberately unbound | No canonical confidence field |
| 10 | `safety_authority` | `PRESENTATION_BOUND` | Projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH`; no source-sibling loader | `RUNTIME_ARTIFACT_ABSENT`; `FAMILY_SPECIFIC_ADAPTER_REQUIRED`; productive KillSwitch state files forbidden as source; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED` |
| 11 | `risk_sizing_capital` | `PRESENTATION_BOUND` | Projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH` | `RUNTIME_ARTIFACT_ABSENT`; source sibling absent; `BLOCKED_MISSING_CANONICAL_SOURCE`; no sizing/evaluator execution; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`; `UPSTREAM_SOURCE_BLOCKED` |
| 12 | `execution_reconciliation` | `PRESENTATION_BOUND` | Projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH` | `RUNTIME_ARTIFACT_ABSENT`; source sibling absent; `BLOCKED_MISSING_CANONICAL_SOURCE`; no order-intent or mutation APIs; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`; `UPSTREAM_SOURCE_BLOCKED` |
| 13 | `economic_summary` | `PRESENTATION_BOUND` | Evidence-only projection, materializer and autobind implemented; materializer `TEST_ONLY_PATH` | `RUNTIME_ARTIFACT_ABSENT`; source sibling absent; `BLOCKED_MISSING_CANONICAL_SOURCE`; explicit evidence selection required; latest/registry/filesystem discovery forbidden; `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`; `UPSTREAM_SOURCE_BLOCKED` |
| 14 | `diagnostics_summary_intentional_unbound` | `INTENTIONALLY_UNAVAILABLE` | Owner registry ratifies `NOT_BOUND` | Authority unresolved; implementation not authorized |
| 15 | `autonomy_stage_intentional_unbound` | `INTENTIONALLY_UNAVAILABLE` | Owner registry ratifies `NOT_BOUND` | No canonical productive authority |
| 16 | `source_health_aggregate` | `PRESENTATION_BOUND` | Derived aggregator implemented | Health depends on required member-slot availability |
| 17 | `repository_sha_no_canonical_payload_field` | `BLOCKED_NO_DURABLE_CANONICAL_PROJECTION` | Optional poll-side field exists, but no canonical Market Truth source is proven | Router supplies `None`; no authorized durable field |
| 18 | `timeline_intentional_unbound` | `INTENTIONALLY_UNAVAILABLE` | Hardcoded empty `NOT_BOUND` timeline | No authorized timeline source |

## 7.2 Ratified Classification Counts

- `PRESENTATION_BOUND`: **12**
- `PRESENTATION_BINDABLE_AFTER_EXISTING_PROJECTION_DISCOVERY`: **1**
- `BLOCKED_NO_DURABLE_CANONICAL_PROJECTION`: **1**
- `LABEL_OR_SEMANTIC_CORRECTION_ONLY`: **0**
- `INTENTIONALLY_UNAVAILABLE`: **4**
- `UNRESOLVED_REQUIRES_MORE_REPOSITORY_EVIDENCE`: **0** family-level classifications

The unresolved evidence items in Section 14 do not change the family classifications.

For the eight projection families, archive verification is complete at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`: all eight authorized durable projections are `RUNTIME_ARTIFACT_ABSENT`; seven source siblings are absent; `safety_authority` has no durable sibling loader.

---

# 8. Family Contracts

## 8.1 `market_instrument`

**Purpose:** Selected-instrument identity for the Global System Strip and primary chart identity.

**Authority:** `CanonicalMarketContextV1`, with authorized Dashboard identity projection from Universe `selected_future`.

**Authorized direct source:** `readmodels&#47;universe_selection_readmodel.v1.json` for the selected identity.

**Projection/binding evidence:**

- `src/webui/market_dashboard_landscape_v2/projections.py` — `project_market_instrument_snapshot_v1`
- `src/webui/market_dashboard_landscape_producer_binding_v2.py` — `_market_from_universe_selected`
- `src/webui/market_dashboard_landscape_producer_binding_v2.py` — `bind_market_universe_slots`
- `src/webui/market_dashboard_landscape_v2/presenter.py` — `present_market_landscape_v2`
- `src/webui/market_dashboard_landscape_v2/serialization.py` — `serialize_projection`

**Contract:** Identity may be displayed only from the authorized market or universe-selected snapshot. Missing identity remains unavailable.

## 8.2 `universe_selection_rail_facts`

**Purpose:** Watchlist count, selected rank, selection reason, session/source run identity.

**Canonical source:** `readmodels&#47;universe_selection_readmodel.v1.json`.

**Binding evidence:**

- `_bind_universe_ranking`
- `project_universe_ranking_snapshot_v1`
- `try_load_universe_selection_for_dashboard`
- PR `#5710`
- `tests/webui/test_market_landscape_universe_selection_rail_facts_presentation_bind_v1.py`

**Contract:** Values are copied exactly from the durable universe-selection read model. No rank, reason, membership, or session inference is permitted.

## 8.3 `okx_selected_instrument_ohlcv`

**Purpose:** Candles, volume, live mark, connection state, interval, revision, timestamps, and chart chrome.

**Canonical source:** `readmodels&#47;okx_selected_instrument_ohlcv_readmodel.v1.json`.

**Binding evidence:**

- `load_bound_okx_ohlcv_readmodel_v1`
- `build_ohlcv_poll_response_v1`
- `serialize_ohlcv_browser_payload_v1`
- `GET &#47;api&#47;market&#47;landscape&#47;ohlcv`
- `static/js/market_dashboard_landscape_v2.js`
- PRs `#5702`, `#5703`, `#5704`, `#5705`, `#5707`, `#5708`

**Contract:** The OHLCV family is presentation-bound but remains dependent on the selected-instrument identity and the durable OHLCV read model. Blank chart or `MISSING_SOURCE` is correct when the source cannot be loaded.

## 8.4 `dynamic_scope`

**Authority:** `CanonicalScopeLifecycleState`.

**Source sibling:** `readmodels&#47;dynamic_scope_state_v1.json`.

**Authorized durable projection:** `readmodels&#47;dynamic_scope_presentation_projection.v1.json`.

**Implementation evidence:** materializer, loader, autobind, owner-registry slot, tests, PR `#5692`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source sibling: **absent**
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `BLOCKED_MISSING_CANONICAL_SOURCE`
- `UPSTREAM_SOURCE_BLOCKED=true`
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:** The Dashboard may load only the authorized presentation projection. It shall not derive current or next scope from trading runtime objects. Presentation must not create the missing source sibling.

## 8.5 `regime_bull_bear_switch`

**Authority:** `SideState`, `TransitionDecision`, and authorized regime fields.

**Authorized durable projection:** `readmodels&#47;bull_bear_regime_presentation_projection.v1.json`.

**Implementation evidence:** materializer, loader, autobind, owner-registry slot, tests, PR `#5691`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source sibling: **absent** (`readmodels&#47;regime_bull_bear_switch.v1.json`)
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `BLOCKED_MISSING_CANONICAL_SOURCE`
- legacy route: `NON_SOURCE` (must not be used as source)
- `UPSTREAM_SOURCE_BLOCKED=true`
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:** The Dashboard shall not calculate regime, side, switch state, transition eligibility, or transition decisions. Presentation must not create the missing source sibling.

## 8.6 `canonical_decision`

**Authority:** `CanonicalTradingDecisionEvidenceV1`.

**Authorized durable projection:** `readmodels&#47;canonical_decision_presentation_projection.v1.json`.

**Implementation evidence:** materializer, loader, autobind, owner-registry slot, tests, PRs `#5687` and `#5689`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source sibling: **absent** (`readmodels&#47;canonical_trading_decision_evidence.v1.json`)
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `BLOCKED_MISSING_CANONICAL_SOURCE`
- no decision recomputation
- `UPSTREAM_SOURCE_BLOCKED=true`
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:** Decision, reason codes, and direction must come from the authorized projection. No decision confidence may be inferred. No decision recomputation is permitted. Presentation must not create the missing source sibling.

## 8.7 `double_play`

**Authority:** `DoublePlayDashboardDisplaySnapshot`.

**Authorized durable projection:** `readmodels&#47;double_play_presentation_projection.v1.json`.

**Implementation evidence:** materializer, loader, autobind, owner-registry slot, tests, PRs `#5688` and `#5690`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source sibling: **absent** (`readmodels&#47;double_play_dashboard_display.v1.json`)
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `BLOCKED_MISSING_CANONICAL_SOURCE`
- `B3_AUTHORIZED=false`
- `UPSTREAM_SOURCE_BLOCKED=true`
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:** This is a display-only snapshot. The Dashboard shall not recreate Double Play state from lower-level fields. Decision-strip blockers mapping remains a separate unauthorized workstream.

## 8.8 `decision_strip_blockers_unbound`

**Source dependency:** `double_play_presentation_projection.v1` and its display blockers.

**Current state:** The presenter carries blocker data, but the template hardcodes `NOT_BOUND`.

**Authorized work:** A bounded presentation-only mapping may be implemented only after the existing durable Double Play projection is proven available and its blocker field contract is verified.

**Prohibited work:** Creating blockers, combining reason codes into blockers, or changing Double Play semantics.

## 8.9 `decision_strip_confidence_intentional_unbound`

No canonical confidence authority or field is proven.

It shall remain `NOT_BOUND`.

No percentage, score, probability, model confidence, strength, or heuristic proxy may be introduced.

## 8.10 `safety_authority`

**Authority:** `src.risk_layer.kill_switch::KillSwitch`.

**Authorized presentation persistence:** `readmodels&#47;safety_authority.v1.json`.

**Implementation evidence:** materializer, projection loader, autobind, tests, commit `737dac557`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source-sibling loader: **none**
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `FAMILY_SPECIFIC_ADAPTER_REQUIRED`
- productive KillSwitch state files: **forbidden as source**
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:** Direct live KillSwitch-state autoload is forbidden. The Dashboard may consume only the authorized presentation projection. A family-specific caller adapter is required; shared sibling-runner assumptions are invalid for this family.

## 8.11 `risk_sizing_capital`

**Authority:** `src.governance.capital_risk_sizing_v1`.

**Source sibling:** `readmodels&#47;risk_sizing_capital.v1.json`.

**Authorized durable projection:** `readmodels&#47;risk_sizing_capital_presentation_projection.v1.json`.

**Implementation evidence:** materializer, loader, autobind, tests, PR `#5693`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source sibling: **absent**
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `BLOCKED_MISSING_CANONICAL_SOURCE`
- no sizing/evaluator execution
- `UPSTREAM_SOURCE_BLOCKED=true`
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:** Quantity, statuses, and reasons are display values only. The Dashboard shall not calculate sizing or capital status. Presentation must not create the missing source sibling.

## 8.12 `execution_reconciliation`

**Authority:** `src.governance.canonical_order_intent_v1`.

**Source sibling:** `readmodels&#47;execution_reconciliation.v1.json`.

**Authorized durable projection:** `readmodels&#47;execution_reconciliation_presentation_projection.v1.json`.

**Implementation evidence:** materializer, loader, autobind, tests, PR `#5694`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source sibling: **absent**
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `BLOCKED_MISSING_CANONICAL_SOURCE`
- no order-intent or mutation APIs
- `UPSTREAM_SOURCE_BLOCKED=true`
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:** Execution and reconciliation values are consumed only. The Dashboard shall not construct order intent or reconcile state. Presentation must not create the missing source sibling.

## 8.13 `economic_summary`

**Authority:** `EconomicViabilityEvidenceV1`.

**Source sibling:** `readmodels&#47;economic_summary.v1.json`.

**Authorized durable projection:** `readmodels&#47;economic_summary_presentation_projection.v1.json`.

**Implementation evidence:** materializer, loader, autobind, tests, PR `#5697`.

**Archive / activation state (ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`):**

- source sibling: **absent**
- projection: **absent** (`RUNTIME_ARTIFACT_ABSENT`)
- materializer invocation: `TEST_ONLY_PATH`
- candidate classification: `BLOCKED_MISSING_CANONICAL_SOURCE`
- explicit evidence selection: **required**
- implicit latest / registry / filesystem discovery: **forbidden**
- `UPSTREAM_SOURCE_BLOCKED=true`
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`

**Contract:**

- classification remains `EVIDENCE_ONLY`;
- no promotion or activation authority is implied;
- no automatic “latest” evidence discovery is allowed;
- no registry or filesystem pack auto-selection is allowed;
- no binding to `promotion_economic_gate_v1` is implied;
- policy thresholds and metrics must be copied from explicitly authorized evidence;
- Presentation must not create the missing source sibling.

## 8.14 `diagnostics_summary_intentional_unbound`

The owner registry identifies the authority as unresolved and implementation as unauthorized.

It shall remain:

- `NOT_BOUND`;
- `NON_AUTHORITATIVE`;
- owner `UNRESOLVED`.

Presentation work may not create a diagnostics aggregate.

## 8.15 `autonomy_stage_intentional_unbound`

No canonical productive autonomy-stage authority exists.

Documentation vocabulary and shell constants do not constitute canonical runtime truth.

The fields shall remain `NOT_BOUND`.

The Dashboard shall not infer promotion eligibility, activation eligibility, operator-GO state, runtime bridge lock, or governance class.

## 8.16 `source_health_aggregate`

**Type:** Dashboard-derived aggregation only.

**Implementation:** `build_source_health_from_snapshots`.

**Contract:**

- Source Health is presentation-bound.
- It is not intentionally unavailable.
- It is not a domain authority.
- It shall be computed only from the availability of the required owner-registry projection slots.
- It shall never be manually forced to `HEALTHY`.
- It improves only when its required member slots become available under their own contracts.
- An intentionally `NOT_BOUND` member remains represented according to the ratified aggregation contract; it must not be silently promoted.

## 8.17 `repository_sha_no_canonical_payload_field`

The Global Strip repository SHA has no proven canonical Market Truth field in the Universe or OHLCV payload contracts.

The router currently supplies `repository_sha=None` or `git_sha=None` for relevant server-side bindings.

An optional poll payload field does not by itself establish domain authority.

The field shall remain empty or unavailable until a separate authorized durable source contract exists.

Presentation may not invoke Git, inspect the working tree, or synthesize a SHA at render time.

## 8.18 `timeline_intentional_unbound`

No authorized event or decision timeline source exists.

The timeline shall remain:

- `NOT_BOUND`;
- empty;
- non-inferred.

The Dashboard shall not reconstruct history from current snapshots, logs, timestamps, or reason-code changes.

---

# 9. Canonical Dependency Graph

## 9.1 Authority Dependencies

- `market_instrument` → `CanonicalMarketContextV1` or authorized Universe selected identity
- `universe_selection_rail_facts` → `universe_selection_readmodel.v1`
- `okx_selected_instrument_ohlcv` → `okx_selected_instrument_ohlcv_readmodel.v1`
- `dynamic_scope` → `CanonicalScopeLifecycleState`
- `regime_bull_bear_switch` → `SideState`, `TransitionDecision`, authorized regime fields
- `canonical_decision` → `CanonicalTradingDecisionEvidenceV1`
- `double_play` → `DoublePlayDashboardDisplaySnapshot`
- `safety_authority` → `KillSwitch`
- `risk_sizing_capital` → `capital_risk_sizing_v1`
- `execution_reconciliation` → `canonical_order_intent_v1`
- `economic_summary` → `EconomicViabilityEvidenceV1`
- `source_health_aggregate` → no domain authority; aggregation only

The following have no currently authorized authority:

- `decision_strip_confidence_intentional_unbound`
- `autonomy_stage_intentional_unbound`
- `timeline_intentional_unbound`
- `repository_sha_no_canonical_payload_field`

`diagnostics_summary_intentional_unbound` has authority status `UNRESOLVED`.

## 9.2 Projection Dependencies

- `dynamic_scope` → `dynamic_scope_presentation_projection.v1`
- `regime_bull_bear_switch` → `bull_bear_regime_presentation_projection.v1`
- `canonical_decision` → `canonical_decision_presentation_projection.v1`
- `double_play` → `double_play_presentation_projection.v1`
- `safety_authority` → `safety_authority_presentation_projection.v1`
- `risk_sizing_capital` → `risk_sizing_capital_presentation_projection.v1`
- `execution_reconciliation` → `execution_reconciliation_presentation_projection.v1`
- `economic_summary` → `economic_summary_presentation_projection.v1`
- `decision_strip_blockers_unbound` → verified Double Play display blockers

## 9.3 Presentation Dependencies

- `bind_market_universe_slots` orchestrates Universe and selected market identity.
- OHLCV loading depends on selected instrument identity and optional venue.
- `decision_strip_blockers_unbound` depends on Double Play presentation data.
- `source_health_aggregate` depends on required owner-registry slot availability.

## 9.4 Forbidden Dependency Inference

UI adjacency does not establish a domain dependency.

A field appearing beside another field does not authorize:

- source reuse;
- value derivation;
- semantic coupling;
- shared status;
- fallback mapping.

---

# 10. Ratified Implementation Roadmap

## Phase 0 — Canonical Inventory and Consumer Contract

**Status:** Complete.

Required artifacts:

- absolute Consumer Contract;
- 18-family matrix;
- dependency graph;
- classification model;
- repository evidence;
- unresolved evidence list.

## Phase 1 — Existing Direct Read-Model Presentation

### 1.1 Universe Selection Rail

**Status:** Complete at PR `#5710`.

### 1.2 Market Instrument Identity

**Status:** Presentation path implemented.

### 1.3 OKX OHLCV Chart Family

**Status:** Presentation path implemented across PRs `#5702`–`#5708`.

No further implementation is authorized merely to remove unavailable states when the durable source is absent.

## Phase 2 — Existing Projection-Based Presentation Paths

The following presentation paths are already implemented:

1. Canonical Decision
2. Double Play
3. Dynamic Scope
4. Regime / Bull-Bear / Switch
5. Safety Authority
6. Risk / Sizing / Capital
7. Execution / Reconciliation
8. Economic Summary

The next legitimate action for these families is not new UI implementation.

**Archive verification status:** Complete (B2 `#5711`, reconfirmed by path discovery `#5712` and the bounded family plan at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`).

Ratified facts for all eight families:

- eight materializers exist as non-authoritative library entrypoints;
- non-test AST call-sites = `0`;
- invocation path = `TEST_ONLY_PATH`;
- eight presentation projections = absent in the active archive;
- seven source siblings = absent;
- `safety_authority` requires a family-specific caller adapter (no sibling loader);
- `MATERIALIZER_EXECUTED=false`;
- `ACTIVE_ARCHIVE_WRITTEN=false`;
- `PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true`.

Any operation that creates source siblings, executes materializers, writes the active archive, or wires runtime/dashboard/scheduler/LaunchAgent paths is upstream or separately authorized work and is **not** authorized by this repository import.

See Section 10A for the ratified bounded family plan (plan only; not an implementation GO).

## Phase 3 — Remaining Bounded Presentation Mapping

### Decision Strip Blockers

This is the only ratified family with a remaining potential presentation-only mapping.

It may proceed only when all of the following are proven:

- the active Double Play durable projection exists;
- the blocker field is present and schema-valid;
- presenter output preserves the field unchanged;
- changing the template from hardcoded `NOT_BOUND` does not introduce inference;
- focused tests prove honest missing-source behavior.

## Phase 4 — Blocked Canonical Field

### Repository SHA

Remain unavailable until a canonical durable source contract is explicitly authorized.

No presentation-side Git discovery is allowed.

## Phase 5 — Intentionally Unavailable Families

Keep unchanged:

- Diagnostics Summary
- Autonomy Stage
- Decision Confidence
- Timeline

These are not backlog defects.

They are honest unavailable states.

## Phase 6 — Derived Source Health Reconciliation

Source Health requires no independent truth source and no independent materializer.

Reconcile it only after member-slot runtime availability has been verified.

Never close Source Health by forcing its output.

---


# 10A. Ratified Bounded Family Plan (Plan Only)

**STATUS:** `READ_ONLY_BOUNDED_FAMILY_PLAN_COMPLETE`  
**VERDICT:** `MIXED_BLOCKERS_FAMILY_PLAN_READY_NO_IMPLEMENTATION_AUTHORIZED`  
**DISCOVERY_SHA / origin/main:** `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`  
**FAMILIES_ANALYZED:** `8`  
**SOURCE_SIBLINGS_ABSENT:** `7`  
**PROJECTIONS_ABSENT:** `8`  
**NON_TEST_MATERIALIZER_CALL_SITES:** `0`

This section records a planning ratification only. It does **not** authorize implementation, materializer execution, active-archive writes, runtime wiring, producer changes, canonical read-model changes, trading-logic changes, or B3.

## 10A.1 Octet family classifications

| Family | Source sibling | Projection | Classification | Additional constraints |
|---|---|---|---|---|
| `dynamic_scope` | absent | absent | `BLOCKED_MISSING_CANONICAL_SOURCE` | Presentation must not create sibling |
| `regime_bull_bear_switch` | absent | absent | `BLOCKED_MISSING_CANONICAL_SOURCE` | Legacy route is `NON_SOURCE` |
| `canonical_decision` | absent | absent | `BLOCKED_MISSING_CANONICAL_SOURCE` | No decision recomputation |
| `double_play` | absent | absent | `BLOCKED_MISSING_CANONICAL_SOURCE` | `B3_AUTHORIZED=false` |
| `safety_authority` | no sibling loader | absent | `FAMILY_SPECIFIC_ADAPTER_REQUIRED` | Productive KillSwitch state files forbidden as source |
| `risk_sizing_capital` | absent | absent | `BLOCKED_MISSING_CANONICAL_SOURCE` | No sizing/evaluator execution |
| `execution_reconciliation` | absent | absent | `BLOCKED_MISSING_CANONICAL_SOURCE` | No order-intent or mutation APIs |
| `economic_summary` | absent | absent | `BLOCKED_MISSING_CANONICAL_SOURCE` | Explicit evidence selection required; latest/registry/filesystem discovery forbidden |

## 10A.2 Recommended later batch structure

Explicitly **PLAN**, not an implementation GO:

| Batch ID | Families | Rationale |
|---|---|---|
| `R1_STANDARD_SIBLING_FIVE` | `dynamic_scope`, `regime_bull_bear_switch`, `canonical_decision`, `risk_sizing_capital`, `execution_reconciliation` | Shared sibling-path lifecycle after upstream sources exist |
| `R2_ECONOMIC_EXPLICIT` | `economic_summary` | Explicit evidence selection; no latest/registry/filesystem discovery |
| `R3_DOUBLE_PLAY` | `double_play` | Separated because of B3 / decision-strip blockers coupling; `B3_AUTHORIZED=false` |
| `R4_SAFETY_ADAPTER` | `safety_authority` | Family-specific caller adapter; exclude from shared sibling runner |

``` text
RECOMMENDED_BATCH_COUNT=4
MAX_SAFE_BATCH_COUNT=3
SHARED_RUNNER_SAFE=true_with_constraints
```

Shared-runner constraints if a later Owner-GO ever authorizes one:

- Safety is excluded from any shared sibling runner;
- Economic Summary requires explicit evidence selection;
- Double Play remains separate because of B3 coupling;
- no runner may own an active-archive default;
- `archive_root` and `generated_at` must be explicit in any later authorized execution;
- automatic runtime, dashboard, session, scheduler, LaunchAgent, or automatic materializer wiring remains unauthorized.

## 10A.3 Separate Owner-GO boundaries

Later work requires distinct Owner-GOs. **None** of the following is granted by this initial repository import:

- `OWNER_GO_UPSTREAM_SOURCE_SIBLING`
- `OWNER_GO_AUTHORIZED_CALLER_INPUT`
- `OWNER_GO_MANUAL_PRESENTATION_MATERIALIZE`
- `OWNER_GO_SAFETY_PRESENTATION_ADAPTER`
- `OWNER_GO_ACTIVE_ARCHIVE_WRITE`
- `OWNER_GO_B3_DECISION_STRIP_BLOCKERS`

## 10A.4 Productive activation stop

Until those Owner-GOs exist and succeed:

``` text
PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED=true
MATERIALIZER_EXECUTED=false
ACTIVE_ARCHIVE_WRITTEN=false
B3_AUTHORIZED=false
IMPLEMENTATION_STOP=true
```

---
# 11. Next Work Order

The previous work order “read-only active-archive verification” is **complete**.

## 11.1 Ratified current state

- Archive verification completed (B2 + discovery + family plan).
- Eight presentation projections: **absent**.
- Seven source siblings: **absent**.
- `safety_authority`: family-specific caller adapter required; productive KillSwitch state files forbidden as source.
- Productive activation: **blocked** (`PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED`).
- B3 / `decision_strip_blockers_unbound`: **unauthorized** (`B3_AUTHORIZED=false`).
- Eight materializers remain library-only (`TEST_ONLY_PATH`; non-test AST call-sites = `0`).
- `MATERIALIZER_EXECUTED=false`
- `ACTIVE_ARCHIVE_WRITTEN=false`
- Runtime, producer, canonical read models, and trading logic: **unchanged**.

## 11.2 Next technical step

The next technical step first requires **separate upstream source-sibling / authorized caller-input Owner-GOs**.

Until those Owner-GOs are issued and satisfied:

``` text
STOP_FOR_IMPLEMENTATION=true
```

A live-DOM reconcile is **not** a sensible next step while all eight required projection artifacts remain absent. The existing `MISSING_SOURCE` display for those families is correct in this state.

Intentionally unavailable families and the repository-SHA blocker remain unchanged.

This work order does not authorize artifact creation, materialization, producer execution, runtime changes, dashboard autobind-to-materialize, scheduler/LaunchAgent wiring, or trading-system changes.

---

# 12. Acceptance Criteria

## 12.1 Presentation-Bound Family

A family is presentation-bound when repository evidence proves the authorized path relevant to that family:

- canonical source or authorized durable projection contract;
- loader or producer binding;
- presenter mapping;
- serializer or page payload mapping where applicable;
- client refresh mapping where applicable;
- template surface;
- focused tests.

Not every family requires JavaScript refresh. SSR-only families are acceptable when their contract is SSR-only.

## 12.2 Runtime-Available Family

A projection-based family is runtime-available only when:

- the exact authorized durable artifact exists in the active archive;
- its schema and family identity are valid;
- the existing loader resolves it;
- no fallback or source substitution occurs;
- the rendered availability reflects the loaded artifact;
- a live-DOM or equivalent browser verification confirms the intended display.

## 12.3 Completion Prohibition

A family shall not be declared complete merely because:

- labels changed;
- a placeholder disappeared;
- a test fixture supplied an injected snapshot;
- a materializer function exists;
- an autobind loader exists;
- a source-like file was discovered elsewhere;
- a current runtime object could theoretically provide the value.

---

# 13. Progress Accounting

After every merged presentation PR or ratified runtime-verification cycle, update:

- repository HEAD;
- inventory artifact and generation timestamp;
- family count;
- classification counts;
- runtime artifact states;
- `MISSING_SOURCE` count;
- `NOT_BOUND` count;
- completed family objectives;
- remaining bounded presentation objectives;
- unresolved evidence;
- affected tests;
- PR number and merge SHA.

Do not reduce backlog counts by assertion.

Counts must come from a reproducible inventory or live-DOM evidence artifact.

---

# 14. Unresolved Evidence

The following items remain explicitly unresolved and shall not be guessed.

## 14.1 Safety Authority PR Number

Commit `737dac557` is proven for the Safety Authority presentation work.

The exact GitHub PR number is not uniquely proven by the available Git subject history.

Record the commit, not an invented PR number.

## 14.2 Active Archive Projection Presence

**Resolved / ratified at Discovery SHA `6a9a3f10b81ab8d870245dc10ea74433e1f5365b`.**

Repository- and archive-backed verification (B2 `#5711`, path discovery `#5712`, bounded family plan) proves:

- all eight authorized presentation projections are **absent** in the active archive (`RUNTIME_ARTIFACT_ABSENT`);
- all seven defined source siblings are **absent**;
- `safety_authority` has no durable source-sibling loader;
- materializers were not executed;
- the active archive was not written.

The former unverified-runtime-presence status is superseded for these eight families.

## 14.3 Unnamed Timeline Chrome Element

The exact stable template mapping for the inventory’s unnamed Event/Decision Timeline chrome element is not proven.

Do not assign it to a field without new evidence.

## 14.4 Post-`#5710` Live-DOM Counts

B2 recorded a live-DOM recount at HEAD `8c02f879...` with `MISSING_SOURCE=50` and `NOT_BOUND=17`. The durable inventory baseline remains `50` / `18`.

A further live-DOM reconcile is not the next authorized technical step while all eight required projection artifacts remain absent; current `MISSING_SOURCE` for those families is expected and correct.

---

# 15. Verification and Mutation Rules

Every discovery or verification command shall report:

- repository root;
- branch or detached-HEAD state;
- HEAD SHA;
- initial Git status;
- final Git status;
- files modified;
- files created;
- branch change;
- commit creation;
- push;
- PR creation.

For read-only work, all mutation fields must remain false.

External archive inspection must also be read-only unless a separate Owner-GO explicitly authorizes upstream artifact generation or modification.

---

# 16. Pull Request Governance

A Presentation PR must:

- identify exactly one family or tightly coupled presentation batch;
- state the canonical source;
- state the authority effect as `NONE`;
- state whether the work is binding, mapping, serialization, refresh, template, or test-only;
- preserve unavailable behavior;
- include focused tests;
- avoid producer, runtime, read-model, trading, risk, safety, execution, and business-semantic changes;
- include before/after inventory or DOM evidence where counts change.

A PR must stop when the required fix is upstream.

## 16.1 Mandatory Consumer Invariant

Every Presentation PR shall additionally prove:

- `DASHBOARD_ROLE=PURE_CONSUMER`
- `AUTHORITY_EFFECT=NONE`
- `TRADING_LOGIC_CHANGED=false`
- `TRADING_STATE_MUTATION_PATH_ADDED=false`
- `CANONICAL_READMODEL_CHANGED=false`
- `ORDER_OR_COMMAND_PATH_ADDED=false`
- `NONCANONICAL_FALLBACK_ADDED=false`

The Dashboard must remain read-only with respect to the productive trading system.


---

# 17. Canonical Stop Conditions

Stop and request Owner direction when:

- the only available source is noncanonical;
- multiple candidate sources exist without a ratified selection rule;
- the required projection is absent;
- a source sibling is missing;
- no authorized caller-input exists;
- a materializer must be executed or scheduled;
- materializer execution is proposed without explicit Materialize GO and Active-Archive-Write GO;
- a Safety source would be taken from productive KillSwitch state;
- Economic Summary would use latest / registry / filesystem discovery;
- Double Play work would activate B3 without a separate `OWNER_GO_B3_DECISION_STRIP_BLOCKERS`;
- a runner would own an active-archive default;
- runtime, dashboard, session, scheduler, or LaunchAgent autowiring is proposed;
- a canonical read model must be changed;
- a producer must be added or modified;
- a field requires business interpretation;
- a value would need inference;
- a change would affect trading, risk, safety, execution, economics, autonomy, or runtime behavior;
- repository evidence contradicts this runbook.

Stopping is correct behavior. It is not an implementation failure.

---

# 18. Supersession and Change Control

This runbook supersedes the prior Presentation Implementation Runbook baseline that tracked 16 families and treated only Universe Selection as completed.

The following corrections are ratified:

1. canonical family count changes from 16 to 18;
2. `market_instrument` and `okx_selected_instrument_ohlcv` are explicit families;
3. 12 families have repository-proven presentation paths;
4. implemented presentation paths are distinguished from absent runtime artifacts;
5. `source_health_aggregate` is presentation-bound and derived, not intentionally unavailable;
6. `decision_strip_blockers_unbound` is the sole family classified as bindable after existing projection discovery;
7. `repository_sha_no_canonical_payload_field` is blocked by absent canonical durable truth;
8. Diagnostics, Autonomy Stage, Confidence, and Timeline remain intentionally unavailable;
9. the `50` and `18` counts remain durable inventory baselines; B2 live-DOM recount after `#5710` recorded `NOT_BOUND=17` with `MISSING_SOURCE` still `50`;
10. the eight projection families are repository-/archive-ratified as `RUNTIME_ARTIFACT_ABSENT` (seven source siblings absent; Safety adapter required);
11. productive activation remains unauthorized; materializer invocation remains `TEST_ONLY_PATH`; `B3_AUTHORIZED=false`;
12. the bounded family plan in Section 10A is plan-only and grants no implementation GO;
13. this repository file is the sole tracked canonical Presentation Implementation Runbook path after Owner-authorized initial import.

Future changes to this runbook require:

- repository-backed evidence;
- an explicit diff of classifications or contracts;
- preservation of the Absolute Consumer Contract;
- Owner ratification.

---

# 19. Canonical Closeout State

| Dimension | State |
|---|---|
| Consumer boundary | Ratified (`PURE_CONSUMER`, `DASHBOARD_AUTHORITY_EFFECT=NONE`) |
| Trading SSOT | Preserved as sole business SSOT |
| Trading logic protected | Ratified |
| Capability scope | `MARKET_DASHBOARD_PRESENTATION_CAPABILITY` only |
| Family inventory | 18 families ratified |
| Presentation-bound families | 12 |
| Remaining conditional presentation mapping | Decision Strip Blockers (`B3_AUTHORIZED=false`) |
| Canonical-field blocker | Repository SHA |
| Intentionally unavailable families | 4 |
| Octet projection runtime presence | Ratified `RUNTIME_ARTIFACT_ABSENT` (8/8) |
| Source siblings absent | 7 |
| Safety adapter required | true |
| Materializer invocation | `TEST_ONLY_PATH` (non-test AST call-sites = 0) |
| Materializers executed | false |
| Active archive written | false |
| Productive activation | Not authorized |
| Family plan | Ratified as plan-only (`MIXED_BLOCKERS_FAMILY_PLAN_READY_NO_IMPLEMENTATION_AUTHORIZED`) |
| Next authorized activity | Separate upstream source / caller-input Owner-GOs; otherwise `STOP_FOR_IMPLEMENTATION` |
| Upstream / implementation changes authorized by this doc | No |

**Canonical verdict:**

`CANONICAL_PRESENTATION_RUNBOOK_INITIAL_REPO_IMPORT_AND_FAMILY_PLAN_RATIFIED_AT_DISCOVERY_SHA_6A9A3F10_ARCHIVE_ABSENT_PRODUCTIVE_ACTIVATION_BLOCKED_NO_IMPLEMENTATION_AUTHORIZED`

