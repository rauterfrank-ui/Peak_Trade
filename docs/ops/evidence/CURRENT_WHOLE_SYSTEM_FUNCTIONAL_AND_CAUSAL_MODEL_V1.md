# CURRENT Whole-System Functional and Causal Model V1

docs_token: DOCS_TOKEN_CURRENT_WHOLE_SYSTEM_FUNCTIONAL_AND_CAUSAL_MODEL_V1

```text
DOCUMENT_CLASS=DESCRIPTIVE_SYSTEM_MODEL
AUTHORITY=NONE
NAVIGATION_AND_UNDERSTANDING_ONLY=true
NOT_OPERATIONAL_SSOT=true
NOT_RUNTIME_AUTHORIZATION=true
GRAPH_LOSES_TO_CANONICAL_CURRENT_CODE=true
CANONICAL_OPERATIONAL_SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CANONICAL_BASELINE_SHA=6422bfde79fd5aa45d2939a821980abf9aa4e3df
STATIC_CARTOGRAPHY_COMPLETE=true
STATIC_COHERENCE_READY=true
RUNTIME_PROOF_COMPLETE=false
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

This document explains Peak_Trade as **one coherent machine** for operators and
agents. It does **not** override the Master Runbook, `origin/main` code, contracts,
or sealed evidence. When this document and code disagree, **code + Master Runbook
win**.

Cartography index (counts only; machine truth in evidence JSON):

```text
DOMAIN_COUNT=31
NODE_COUNT=120
EDGE_COUNT=396
CONFIG_POINT_COUNT=145
```

Index: [`WHOLE_SYSTEM_EXHAUSTIVE_REPOSITORY_CARTOGRAPHY_FIXPOINT_V1.md`](WHOLE_SYSTEM_EXHAUSTIVE_REPOSITORY_CARTOGRAPHY_FIXPOINT_V1.md).

------------------------------------------------------------------------

## 1. What Peak_Trade is CURRENTLY

Peak_Trade is a **governed, fail-closed** futures trading stack bounded at
**PRE_EXTERNAL** for the current authorized proof phase. It ingests public (and
scoped private read) market/account context, maintains universe and selection
state, evaluates Master V2 / Double Play decision semantics on a productive path,
admits capital/risk, constructs order intent/envelope artifacts, and terminates
at PRE_EXTERNAL unless explicit scoped Owner-GO authorizes a narrower or wider
boundary.

**Not claimed here:** profitable trading, optimal strategy, production Natural
Enter success, or runtime liveness — those require productive evidence classes
defined in §9.

------------------------------------------------------------------------

## 2. Decision and authority semantics (CURRENT code)

| Function | CURRENT owner / producer (productive path) |
| --- | --- |
| Observations (Live C1, marks) | `LiveFreshC1ContinuousObservationSourceV1`; public MD GET surfaces on poll |
| Economic / eligible universe | Cap21–Cap23 persist chain (EEA inventory, economic MD, ranking inputs) |
| Ranking / preselection | Cap22 productive ranking producer; optional Top20 evaluation residency |
| **Selection** | **Cap2.3 — SOLE_SELECTION_OWNER** (`CAP23_SOLE_SELECTION_OWNER=true`) |
| **Binding** | **Cap2.4 — BIND_ONLY** (`CAP24_BIND_ONLY=true`; no selection) |
| G17 typed-vol context | Per-run LANE_1 producer from mark history; per-cycle CMC bind on MV2 and F1/M9 paths |
| **Base geometry magnitude (GGE)** | **`GoldenGeometryEngineV1`** — sole productive owner of `CanonicalBaseGeometryMagnitudeV1` (`GGE_OWNER=trading.master_v2.golden_geometry_engine_v1`; D=σ×mark); no Scope/SideState/position inputs |
| **Scope / Layer-C geometry** | `canonical_scope_initialization_v1` + `layer_c_scope_event_distance_binding_v1` — consumes GGE magnitude; **no second base-geometry authority** |
| Cycle gate / threshold consumer | F1/M9 productive runtime threshold consumer (INJ-001 via M01 `_build_f1_m9_evaluator`) |
| Trading decision (MV2/DP) | `run_current_productive_master_v2_runtime_cycle_v1` after S7 T2 compose (post GGE→Scope on MV2 path) |
| Confirmation / candidate | Sidestate confirmation cursor + policy iteration gate (`require_f1_m9_each_cycle`) |
| Capital / risk admissibility | Full-Core capital/risk modules (see Master Runbook § risk) |
| Intent / plan / envelope | Full-Core order-intent owners; envelope ≠ POST authorization |
| Governed cycle disposition | S5 orchestrator → **PRE_EXTERNAL** terminal class |
| N5 multi-future autonomy | **Orchestration/compose-only** where proven — **not** standalone trading decision authority |
| DDO / Learning / OPT / MI | Capture, research, offline evidence — **no implicit productive trading authority** |
| WebUI / operator | Read-only / operator surfaces — **no trading authority** |

```text
N5_AUTONOMY_TRADING_DECISION_AUTHORITY=false
DDO_PRODUCTIVE_TRADING_AUTHORITY=false
LEARNING_TRADING_AUTHORITY=false
OPTIMIZATION_TRADING_AUTHORITY=false
MI_TRADING_AUTHORITY=false
WEBUI_TRADING_AUTHORITY=false
MAX_POSITIONS_ONE_INVARIANT=true
```

------------------------------------------------------------------------

## 3. Productive causal path (machine order)

Entry (Owner-GO bounded; **Full-Core GHV carrier**):  
`scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py`  
(composition root: `src/ops/full_core_live_path_composition_root_v1/`)

**STATICALLY_PROVEN** wiring (PR #7029 cartography, PR #7030 M01 regression lock,
PR #7064 GGE wiring, deterministic tests):

1. Cap21→Cap23 productive persist (universe, economic MD, residency where configured)
2. Cap2.3 selection → Cap2.4 bind-only → S8 occupied lane / cursor
3. Per-**run** G17 producer: mark-history GET → prepare LANE_1 typed-vol hot path
4. Live Fresh C1 continuous observation source
5. Cold bootstrap via S7 compose when cursor absent
6. Policy-governed persistent Natural Enter live C1 continuous run (S6)
7. Each cycle: iteration gate → F1/M9 (G17 CMC bind → threshold consumer)
8. Parallel N1/S5 runner → S7 T2 compose → MV2 cycle: market context (mark + vol) → **GGE** → scope init / Layer-C distances → typed-vol gate → **MV2/Double Play**
9. Capital/risk admissibility → intent/envelope → S5 disposition → **PRE_EXTERNAL**

**RUNTIME_PROOF_REQUIRED** (do not label as static defects; Master Runbook register
remains `RUNTIME_PROOF_DEBT=OPEN`):

- Fresh PT1M mark ingestion vs duplicate/no-op producer cycles on gate path
- Observation generation alignment (F1/M9 scaffold vs S7/MV2 CMC)
- `confirmation_epochs=2` on contiguous valid live C1 only
- Natural Enter disposition reaching PRE_EXTERNAL under bounded productive observation

**Bounded convergence evidence (navigation; `AUTHORITY=NONE`):**

- Historical #7068 manifest
  `evidence&#47;research&#47;current_productive_ghv_input_readiness_and_convergence_v1&#47;durable&#47;current_productive_ghv_bounded_runtime_convergence_proof_v1.json`
  remains sealed navigation for an earlier baseline.
- CURRENT canonical closure for Natural Enter → PRE_EXTERNAL on
  `origin&#47;main@6ed52d01` is
  [`CURRENT_NATURAL_ENTER_PRE_EXTERNAL_CANONICAL_CLOSURE_V1.md`](CURRENT_NATURAL_ENTER_PRE_EXTERNAL_CANONICAL_CLOSURE_V1.md)
  (`NATURAL_ENTER_TO_PRE_EXTERNAL_PROVEN=true`,
  `CURRENT_FUNCTIONAL_PATH_PROVEN_THROUGH_PRE_EXTERNAL=true`).
- Explicitly preserved: `PRODUCTIVE_RUNTIME_PROOF_COMPLETE=false`,
  `CURRENT_FUNCTIONAL_PATH_PROVEN_BEYOND_PRE_EXTERNAL=false`,
  `POST_ALLOWED=false`, `EXTERNAL_EFFECT_AUTHORIZED=false`.

------------------------------------------------------------------------

## 4. Golden Happy Vector (GHV) role

```text
GHV_FORENSIC_PROBE=true
GHV_IS_NOT_THE_WHOLE_SYSTEM=true
GHV_IS_NOT_PROFIT_PROOF=true
GHV_IS_NOT_RUNTIME_LIVENESS_WITHOUT_PRODUCTIVE_EVIDENCE=true
GHV_CURRENT_FULL_SYSTEM_CARRIER=FULL_CORE_PRODUCTIVE_GHV_CONVERGENCE_AND_STARTABILITY
PAPER_SHADOW_247_NOT_CURRENT_FULL_SYSTEM_CARRIER=true
```

GHV traversals expose configuration propagation, state propagation, ownership,
authority, gates, joins, branches, transitions, and terminal boundaries. The
**CURRENT** full-system productive proof carrier is the **Full-Core** policy-governed
Natural Enter / PRE_EXTERNAL convergence path (§3 entry script) plus GHV
startability/readiness evaluators under
`src/ops/full_core_live_path_composition_root_v1/`. Historical **Paper-Shadow-247**
charter/daemon surfaces remain separate governed lanes — not the primary CURRENT
whole-system runtime carrier.

**Branch vocabulary (navigation; not separate SSOTs):**

| Branch | Role |
| --- | --- |
| GHV_MAIN_PATH / ON_GHV_CRITICAL_ROUTE | Cap21–Cap24 → C1/cursor → GGE→Scope → MV2+DP → admission → S5 → PRE_EXTERNAL |
| GHV_SIDE_BRANCH / PARALLEL_GHV_SECTOR | F1/M9 typed-vol consumer; parallel N1/S5 lane |
| GHV_CONTROL_BRANCH | Policy iteration gates, confirmation cursor, continuous-run policy |
| GHV_EVIDENCE_BRANCH | Sealed ops evidence, cartography JSON, adjudication reports, bounded convergence manifest (§3) |
| GHV_SHADOW_BRANCH | Shadow treasury, offline replay, Paper-Shadow research lanes — not primary Full-Core carrier |
| INDEPENDENT_CURRENT_SUBSYSTEM | Public-MD runtime, private read, WebUI, learning loops — integrated but not collapsed into GHV |

Static GHV-relevant path: **coherent** at static closure. Remaining GHV transitions
depend on **runtime measurement** (§9.A).

Evidence: [`WHOLE_SYSTEM_FORENSIC_CARTOGRAPHY_GHV_FIXPOINT_V1.md`](WHOLE_SYSTEM_FORENSIC_CARTOGRAPHY_GHV_FIXPOINT_V1.md), BWP-02/03 injection record.

------------------------------------------------------------------------

## 5. Freshness model (six notions; no single canonical epoch)

```text
CANONICAL_FRESHNESS_CONTRACT_FOUND=false
FRESHNESS_CONTRACT_COUNT=6
```

Relevant distinct freshness notions (from static closure evidence; not merged):

1. Live C1 observation freshness / poll cadence
2. Public mark/index GET recency on observation poll
3. G17 mark-history window and typed-vol sample binding
4. G17 CMC bind generation vs prior bound value (`g17_cmc_bind_produced_only` config semantics)
5. Cap2.3/Cap2.4 selection/bind epoch handoff
6. Confirmation/candidate sidestate epoch vs observation stream

**Known CURRENT static behavior:**

```text
PRODUCER_CREATED_PER_RUN=true
PRODUCER_CREATED_PER_CYCLE=false
PRODUCER_STATEFUL=true
PRODUCER_CAN_RETURN_DUPLICATE_NOOP=true
CAN_F1M9_CONSUME_UNBOUND_G17_CONTEXT=true
UNBOUND_PATH_FAILS_CLOSED=true
CAN_PREVIOUS_BOUND_VALUE_SURVIVE=false
```

**Stale semantics (static; live correlation unproven):**

| Claim | Static status |
| --- | --- |
| STALE_OBJECT_CAN_SURVIVE | possible (stateful producer) |
| STALE_VALUE_CAN_SURVIVE | bounded by bind-only produced semantics |
| STALE_VALUE_CAN_BE_CONSUMED | gate path may see duplicate/no-op cycles |
| STALE_VALUE_CAN_AUTHORIZE_ADMISSION | fail-closed unless proven otherwise at runtime |

Do not treat live C1/confirmation correlation gaps as **STATIC_REPAIR_DEBT** without
fail-closed proof.

------------------------------------------------------------------------

## 6. Superseded static repair (not CURRENT debt)

```text
WSRC-V1-ORD-001=SUPERSEDED_BY_INJ_001_ON_MAIN
REP-WSRC-001=ALREADY_CLOSED_BY_INJ_001_ON_MAIN
F1_M9_PRODUCTIVE_G17_CONTEXT_BOUND=true
F1_M9_TEST_FIXTURE_ON_PRODUCTIVE_PATH=false
```

Historical BWP-02 ATOMIC-01 narrative is **superseded** by INJ-001 on main; see
BWP-03 configuration injection evidence.

------------------------------------------------------------------------

## 7. PRE_EXTERNAL safety boundary

```text
PRE_EXTERNAL_TERMINAL_FOR_CURRENT_PROOF_PHASE=true
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

- Envelope creation **≠** authorization to POST
- Capability **≠** standing authorization
- Permit capability **≠** automatic external effect
- Credential availability **≠** trading authority

No document in this set implies real-order authorization.

------------------------------------------------------------------------

## 8. Open debt (documentation-aligned)

| Register | CURRENT |
| --- | --- |
| STATIC_REPAIR_DEBT | 0 |
| RUNTIME_PROOF_DEBT | OPEN (Master Runbook-aligned; bounded convergence manifest is non-authorizing) |
| NAVIGATION_DEBT | residual cross-index (see exhaustive fixpoint) |
| TEST_COVERAGE_DEBT | bounded; M01 closure locked #7030; GGE contract tests `tests/trading/master_v2/test_golden_geometry_engine_v1.py` |

```text
NEXT_AUTHORIZED_PHASE=GHV_DRIVEN_BOUNDED_PRODUCTIVE_PRE_EXTERNAL_RUNTIME_PROOF
```

This section does **not** authorize that phase.

------------------------------------------------------------------------

## 9. TRADING-QUALITY SEMANTIC CONTRACT AUDIT V1 (embedded)

**Audit baseline:** `origin/main` @ `6422bfde79fd5aa45d2939a821980abf9aa4e3df`.  
**Method:** read productive path owners (incl. GGE V1 post-#7064), DDO offline
contract, MV2 runtime cycle dispositions, treasury read-only bindings, sealed
static-closure evidence, and non-authorizing bounded runtime manifests — not prior
narrative prose.

```text
TRADING_QUALITY_SPECIAL_AUDIT_PERFORMED=true
GOOD_BAD_GLOBAL_BOOLEAN_PRESENT=false
REAL_EXECUTION_PERFORMANCE_CLAIMED=false
```

### 9.1 Five quality layers (mandatory; non-collapsing)

| Layer | Token | What it may judge | CURRENT productive proof status |
| --- | --- | --- | --- |
| Q1 | `STRUCTURAL_CORRECTNESS` | Wiring, ownership, fail-closed gates, deterministic regression | Partially **PROVEN_CURRENT** (cartography, M01 lock, static coherence) |
| Q2 | `RUNTIME_SIGNAL_LIVENESS` | Observation progression, freshness, cycle disposition reachability | **RUNTIME_EVIDENCE_REQUIRED** |
| Q3 | `DECISION_QUALITY` | Ex-ante decision vs defined success criteria at declared horizon | **UNDEFINED_CURRENT** as aggregate productive label |
| Q4 | `EXECUTION_QUALITY` | Intended vs executed price, latency, slippage, rejections | **NOT_APPLICABLE_WITH_POST_DISABLED** (real venue); pre-external envelope only |
| Q5 | `ECONOMIC_PERFORMANCE` | Realized/unrealized trading PnL, fees, funding, drawdown | **NOT_YET_MEASURED** on authorized productive proof surface |

**Non-collapse rules (enforced in this document):**

```text
TECHNICALLY_CORRECT != GOOD_DECISION
GOOD_DECISION != PROFITABLE_OUTCOME
LOSING_OUTCOME != SYSTEM_DEFECT
PROFITABLE_OUTCOME != GOOD_DECISION
```

No single global GOOD/BAD boolean is defined for the whole system on `origin/main`.

### 9.2 Decision-time / lookahead boundary

Every Q3 label requires explicit separation:

```text
DECISION_TIMESTAMP=observation/cycle boundary at MV2/DP disposition (productive: current_productive_master_v2_runtime_cycle_v1)
OBSERVATION_CUTOFF=Live C1 + bound context available to that cycle (see §5 freshness)
AVAILABLE_INFORMATION=ex-ante inputs bound before disposition (incl. canonical mark/vol at GGE seam and scope/Layer-C state derived from GGE magnitude)
FUTURE_INFORMATION=marks, exits, funding, fees, and PnL after cutoff — ex-post only
EVALUATION_HORIZON=UNDEFINED_CURRENT for productive Natural Enter quality score
GGE_SCOPE_QUALITY_LAYER=Q1 structural fail-closed only (invalid/missing base geometry blocks downstream scope distance materialization; not a Q3 trade-quality score)
```

**LOOKAHEAD_BIAS / HINDSIGHT_BIAS:** forbidden for Q3 labels unless a **separate**
canonical evaluation contract names horizon, cutoff, and admissible post-decision
fields. Offline DDO (`src/learning/deterministic_decision_outcome_v0/`) binds
`evaluation_horizon` tokens for **capture/export** (`AUTHORITY=NONE`); that is **not**
a productive trading-quality SSOT and does not mint ex-ante GOOD/BAD on the live
path.

Research modules may declare `no_lookahead` / `lookahead_forbidden` in preregistration
contracts; those do not automatically apply to productive MV2 dispositions.

### 9.3 Good entry / bad entry (canonical field audit)

| Field | CURRENT productive canonical status | Evidence / owner hint |
| --- | --- | --- |
| `ENTRY_REFERENCE_TIME` | **UNDEFINED_CURRENT** as unified productive quality field | MV2 emits cycle dispositions; no repo-wide entry-quality SSOT found |
| `ENTRY_REFERENCE_PRICE` | **UNDEFINED_CURRENT** for quality scoring | Reference-price producers exist for sizing/risk; not mapped to entry-quality verdict |
| `EVALUATION_HORIZON` | **UNDEFINED_CURRENT** for productive enter quality | DDO horizon enums are offline contract tokens |
| `FAVORABLE_MOVE` / `ADVERSE_MOVE` | **UNDEFINED_CURRENT** for productive path | Offline backtest computes MFE/MAE (`src/backtest/economic_observability_advanced_capabilities_v1.py`); not productive default |
| `SUCCESS_CRITERION` / `FAILURE_CRITERION` | **UNDEFINED_CURRENT** | Do not infer from post-hoc price direction |
| `NEUTRAL_OR_UNRESOLVED` | **PROVEN_CURRENT** as admissible | Holds, blocks, and non-enter dispositions are first-class MV2 outcomes |
| `BASE_GEOMETRY_MAGNITUDE` (GGE) | **PROVEN_CURRENT** (Q1 owner/wiring); **UNDEFINED_CURRENT** (Q3 enter quality) | Sole owner `golden_geometry_engine_v1`; scope init delegates via `PRODUCTIVE_RAW_SCOPE_DISTANCE_PRODUCER_ID` |
| `SCOPE_GEOMETRY_CONFORMANCE` | **UNKNOWN_CURRENT** productive aggregate | Layer-C / scope init consume GGE; no separate GOOD/BAD scope-quality SSOT |

**Forbidden shortcut (not canonical):** “price later went up ⇒ good LONG entry”.

### 9.4 Exit quality (separated axes)

| Axis | Status |
| --- | --- |
| `EXIT_POLICY_CONFORMANCE` | **UNKNOWN_CURRENT** until exit-policy quality contract bound to productive path |
| `EXIT_DECISION_QUALITY` | **UNDEFINED_CURRENT** (ex-ante criteria not unified) |
| `REALIZED_TRADE_OUTCOME` | **RUNTIME_EVIDENCE_REQUIRED**; **NOT_APPLICABLE_WITH_POST_DISABLED** for real fills |
| `COUNTERFACTUAL_BEST_EXIT` | **NOT_DEFINED_CURRENT** — hindsight-optimal exit is not canonical target |

### 9.5 PnL / accounting firewall

```text
DEPOSIT != TRADING_PROFIT
WITHDRAWAL != TRADING_LOSS
TRANSFER != TRADING_RETURN
EQUITY_CHANGE != AUTOMATICALLY_TRADING_PNL
```

Treasury Phase 2 explicitly types deposit/capital context separately from balance
inference alone (`src/ops/treasury_phase_2_read_only_venue_observation_binding_v1/`).
Productive account-equity producers feed **sizing/risk admissibility**, not strategy
performance attribution on the authorized proof surface.

| Quantity | Productive attribution status |
| --- | --- |
| `REALIZED_TRADING_PNL` | **UNKNOWN_CURRENT** (no real POST proof phase) |
| `UNREALIZED_TRADING_PNL` | **UNKNOWN_CURRENT** |
| `FEES` / `FUNDING` / `SLIPPAGE` | **NOT_YET_MEASURED** productively |
| `DEPOSITS` / `WITHDRAWALS` / `TRANSFERS` | **PROVEN_CURRENT** — non-trading flows; must not score strategy |
| `COLLATERAL_REVALUATION` | **UNKNOWN_CURRENT** |
| `ACCOUNT_EQUITY_CHANGE` | **UNKNOWN_CURRENT** as automatic PnL proxy |

### 9.6 Risk vs return

```text
RISK_CONFORMANCE=admissibility gates, MAX_POSITIONS_ONE_INVARIANT, capital/risk modules
ECONOMIC_OUTCOME=Q5 metrics after explicit execution/realization class
```

A **policy-compliant loss** is not automatically `SYSTEM_BAD`. A **profitable**
action that **violates** canonical risk policy is not automatically `GOOD`. Risk
conformance is Q1/Q4 boundary evidence; economic outcome is Q5.

### 9.7 No-trade is first class

Productive and diagnostic taxonomies include non-enter paths (examples):

```text
NO_SIGNAL / HOLD / NO_ACTION (DDO DECISION_RESULT_V0 offline token)
MV2 zero-trade funnel stages (offline diagnostic only)
REJECTED_BY_CONFIRMATION / REJECTED_BY_POLICY / REJECTED_BY_RISK (conceptual classes — map to concrete disposition codes at runtime)
NO_VALID_ENTRY
```

**MISSED_OPPORTUNITY_QUALITY=UNDEFINED_CURRENT** — no canonical productive
counterfactual methodology on `origin/main`.

Abstention must not be labeled BAD merely because price moved afterward.

### 9.8 Multi-horizon semantics

Horizonless claims (`GOOD_ENTRY`, `BAD_SIGNAL`, `CORRECT_DIRECTION`, etc.) are
**not canonical** unless a named contract defines `EVALUATION_HORIZON`. DDO supports
horizon **tokens** offline; productive MV2 does not publish a single system-wide
horizon for enter quality.

### 9.9 Long / short sign semantics

MV2 productive cycle emits directional dispositions (`enter_long`, `enter_short`,
hold-class outcomes). **Symmetric ex-ante quality evaluation** for LONG vs SHORT is
**UNDEFINED_CURRENT** at whole-system level. Offline MFE/MAE helpers exist for
research/backtest bars; sign conventions there **do not** automatically transfer to
productive Natural Enter quality without a bound contract.

### 9.10 Causal attribution strength

Do not attribute total economic outcome to one upstream owner. Allowed strength
labels only:

```text
DIRECT | SUPPORTED | CORRELATED_ONLY | UNKNOWN
```

Default for cross-layer performance attribution on the productive path: **UNKNOWN**
until measured with explicit methodology.

### 9.11 Learning / optimization firewall

```text
DDO_PRODUCTIVE_TRADING_AUTHORITY=false
LEARNING_TRADING_AUTHORITY=false
OPTIMIZATION_TRADING_AUTHORITY=false
MI_TRADING_AUTHORITY=false
```

Any label consumed offline must record (when present): `LABEL_OWNER`, `LABEL_VERSION`,
`QUALITY_LAYER`, `TIME_HORIZON`, `DATA_SOURCE`, `EX_ANTE_OR_EX_POST`, `AUTHORITY`.
Performance evidence **does not** grant productive trading authority. Learning/OPT/MI
**must not** silently redefine GOOD/BAD.

### 9.12 Statistical validity

Single-cycle, single-trade, or single PRE_EXTERNAL traversal **cannot** establish:
profitability, positive expectancy, robust edge, strategy superiority, regime
robustness, or optimization success.

Aggregate performance methodology fields (sample requirement, OOS, walk-forward,
multiple-testing control, uncertainty): **NOT_DEFINED_CURRENT** for productive proof.

### 9.13 Simulation / reality classes (never merge silently)

| Class | May inform |
| --- | --- |
| `OFFLINE_REPLAY` | Q1/Q3 research only with contract |
| `SYNTHETIC` / `SIMULATED_EXECUTION` | Structural GHV traces; not Q5 productive |
| `PAPER_SHADOW` | Observation-class only unless separately authorized |
| `PRE_EXTERNAL_ONLY` | Q1/Q2 structural + envelope intent; not real execution quality |
| `REAL_EXECUTION` | **NOT ESTABLISHED** (`POST_ALLOWED=false`, `REAL_POST_COUNT=0`) |

### 9.14 GHV quality trace (forensic; not profit proof)

Primary probe path:

```text
observation → ranking/preselection → Cap2.3 → Cap2.4 → C1/G17/F1M9 → confirmation
→ market context → GGE → scope/Layer-C → MV2/DP → candidate/entry disposition
→ capital/risk/admission → intent → PRE_EXTERNAL
```

| Stage | WHAT_IS_KNOWN (static) | WHAT_CAN_BE_JUDGED now | QUALITY_LAYER | FUTURE_EVIDENCE_REQUIRED |
| --- | --- | --- | --- | --- |
| Observation | Wiring + freshness semantics (§5) | Q1 partial | Q1/Q2 | Live mark progression |
| Ranking/selection | Cap2.3 owner, Cap2.4 bind-only | Q1 | Q1 | Runtime selection snapshots |
| G17/F1M9 | INJ-001 bind path proven | Q1 | Q1 | Aligned generations live |
| GGE / Scope | GGE sole base-geometry owner; scope/Layer-C consume magnitude | Q1 partial | Q1 | Runtime geometry input validity under live CMC |
| Confirmation | Cursor/policy gate exists | Q1 | Q1/Q2 | Epoch-2 progression live |
| MV2/DP | Disposition emission proven structurally | Q1 | Q1/Q3 | Ex-ante quality methodology |
| Capital/risk | Admissibility modules present | Q1 | Q1/Q4 | Conformance under load |
| PRE_EXTERNAL | Terminal class proven | Q1 | Q1/Q2 | End-to-end productive arrival |

`LABEL_OWNER=` unset for system-wide GOOD/BAD — **by design**.

### 9.15 Failure taxonomy (do not collapse to “bad trading”)

| Class | Meaning | Evidence class |
| --- | --- | --- |
| `STRUCTURAL_FAILURE` | Wiring/contract violation | Deterministic tests, cartography |
| `DATA_FAILURE` | Missing/invalid observation | Runtime logs |
| `FRESHNESS_FAILURE` | Stale consumption where forbidden | Runtime + config proof |
| `SIGNAL_FAILURE` | Signal producer defect | Stage-local proof |
| `GEOMETRY_FAILURE` | GGE fail-closed or scope/Layer-C distance unavailable | GGE/scope module evidence |
| `SELECTION_FAILURE` | Cap2.3 policy violation | Selection audit |
| `BINDING_FAILURE` | Cap2.4 bind-only violation | Bind audit |
| `CONFIRMATION_FAILURE` | Cursor/epoch gate fail-closed | Runtime trace |
| `DECISION_FAILURE` | MV2/DP disposition contract break | Cycle evidence |
| `RISK_FAILURE` | Admissibility rejection | Risk module evidence |
| `EXECUTION_FAILURE` | POST/fill path (N/A now) | Future POST phase |
| `ACCOUNTING_FAILURE` | PnL/equity mis-attribution | Treasury/recon |
| `ECONOMIC_LOSS` | Q5 outcome | Not confounded with Q1 defect |
| `EXPECTED_VARIANCE` | Q5 under defined hypothesis | Requires stats contract |
| `INSUFFICIENT_EVIDENCE` | Cannot label Q3/Q5 | Default for current phase |

### 9.16 Quality ontology (CURRENT)

| Dimension | Status token |
| --- | --- |
| Structural | PROVEN_CURRENT (partial) / RUNTIME_EVIDENCE_REQUIRED |
| Live-evidence | RUNTIME_EVIDENCE_REQUIRED |
| Decision (Q3) | UNDEFINED_CURRENT |
| Risk-conformance | UNKNOWN_CURRENT productive aggregate |
| Execution (real) | NOT_APPLICABLE_WITH_POST_DISABLED |
| Economic outcome (Q5) | NOT_YET_MEASURED |
| Evidence sufficiency | INSUFFICIENT for profitability claims |

### 9.17 Claim-by-claim audit (trading-quality statements in this document)

| CLAIM_ID | SECTION | CLAIM (abbrev) | LAYER | EX_ANTE/EX_POST | STATUS |
| --- | --- | --- | --- | --- | --- |
| TQ-001 | §1 | Not profitable/optimal/N Enter proven | Q5/Q2 | n/a | PROVEN_CURRENT |
| TQ-002 | §2 | Cap2.3 sole selection; Cap2.4 bind-only | Q1 | ex-ante structure | PROVEN_CURRENT |
| TQ-003 | §2 | DDO/Learning/OPT/MI no trading authority | Q1 | ex-ante | PROVEN_CURRENT |
| TQ-004 | §3 | Static wiring proven; runtime liveness open | Q1/Q2 | mixed | PROVEN_CURRENT |
| TQ-005 | §4 | GHV not profit/liveness proof | meta | n/a | PROVEN_CURRENT |
| TQ-006 | §9.1 | Five layers must not collapse | meta | n/a | PROVEN_CURRENT |
| TQ-007 | §9.3 | Entry quality fields UNDEFINED_CURRENT | Q3 | ex-ante | PROVEN_CURRENT |
| TQ-008 | §9.5 | Deposit≠profit firewall | Q5 | n/a | PROVEN_CURRENT |
| TQ-009 | §9.7 | Missed opportunity undefined | Q3 | ex-post | PROVEN_CURRENT |
| TQ-010 | §9.12 | N=1 cannot prove edge | Q5 | n/a | PROVEN_CURRENT |
| TQ-011 | §9.13 | Real execution performance not established | Q5 | n/a | PROVEN_CURRENT |
| TQ-012 | §2/§3 | GGE sole base-geometry owner; scope consumes; no duplicate authority | Q1 | ex-ante structure | PROVEN_CURRENT |
| TQ-013 | §3/§8 | Bounded GHV convergence manifest exists; runtime debt register still OPEN | Q2 | ex-post bounded | PROVEN_CURRENT |
| TQ-014 | §4 | Full-Core GHV carrier; Paper-Shadow-247 not primary whole-system carrier | meta | n/a | PROVEN_CURRENT |

```text
QUALITY_CLAIM_COUNT=14
UNAUDITED_TRADING_QUALITY_CLAIMS=0
TRADING_QUALITY_UNDEFINED_CURRENT_COUNT=6
TRADING_QUALITY_RUNTIME_EVIDENCE_REQUIRED_COUNT=4
TRADING_QUALITY_CONFLICTING_CURRENT_COUNT=0
```

### 9.18 Hard quality-document gate (this file)

```text
QUALITY_LAYERS_SEPARATED=true
DECISION_TIME_BOUNDARY_DEFINED=true
LOOKAHEAD_RULES_DEFINED=true
PNL_ATTRIBUTION_DEFINED_OR_EXPLICITLY_UNKNOWN=true
TRANSFER_NEUTRALITY_DEFINED=true
RISK_VS_RETURN_SEPARATED=true
SIM_VS_REAL_SEPARATED=true
NO_TRADE_SEMANTICS_DEFINED_OR_EXPLICITLY_UNDEFINED=true
HORIZON_RULES_DEFINED_OR_EXPLICITLY_UNDEFINED=true
STATISTICAL_LIMITATIONS_DEFINED=true
AUTHORITY_BOUNDARIES_PRESERVED=true
GHV_QUALITY_TRACE_COMPLETE=true
GGE_MODEL_CURRENT=true
GHV_MODEL_CURRENT=true
TRADING_QUALITY_MODEL_CURRENT=true
QUALITY_DOCUMENT_HARD_GATE_PASS=true
WHOLE_SYSTEM_MODEL_CURRENT=true
```

------------------------------------------------------------------------

## 10. Cross-references

| Role | Path |
| --- | --- |
| Operational SSOT | [`PEAK_TRADE_MASTER_RUNBOOK.md`](../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) |
| Navigation only | [`PEAK_TRADE_MAP_OF_TRUTH.md`](../../governance/PEAK_TRADE_MAP_OF_TRUTH.md) |
| M01 regression lock | `tests/ops/test_current_productive_m01_f1_m9_g17_production_closure_v1.py` |
| GGE V1 owner | `src/trading/master_v2/golden_geometry_engine_v1.py` |
| GGE contract tests | `tests/trading/master_v2/test_golden_geometry_engine_v1.py` |
| GHV startability (offline) | `src/ops/full_core_live_path_composition_root_v1/current_productive_golden_happy_vector_startability_evaluator_v1.py` |
| Bounded convergence manifest (non-authorizing) | `evidence/research/current_productive_ghv_input_readiness_and_convergence_v1/durable/current_productive_ghv_bounded_runtime_convergence_proof_v1.json` |
| INJ-001 evidence | [`WHOLE_SYSTEM_CONFIGURATION_INJECTION_GHV_BWP03_V1.md`](WHOLE_SYSTEM_CONFIGURATION_INJECTION_GHV_BWP03_V1.md) |
| WSRC adjudication | `evidence&#47;ops&#47;whole_system_radiograph_coherence_adjudication_v1&#47;20261002T233600Z&#47;REP_WSRC_001_PRE_REPAIR_FORENSIC_ADJUDICATION_V1.json` |
