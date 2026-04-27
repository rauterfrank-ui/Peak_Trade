---
docs_token: DOCS_TOKEN_MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0
status: draft
scope: docs-only, non-authorizing visual reference
last_updated: 2026-04-27
---

# Master V2 Visual Architecture and Strategy Reference V0

## 1. Executive Summary

This document records the current visual reference set for Peak_Trade architecture, strategy surfaces, Learning Loop, Knowledge Base, and safety and authority boundaries.

The referenced visuals are planning and understanding aids. They are not runtime artifacts, approvals, signoffs, live-readiness claims, or gate passes. They do not modify code, strategy behavior, Master V2 / Double Play, Risk or KillSwitch, Scope or Capital, execution gates, dashboards, workflows, configs, or tests.

The long-term target may include fully autonomous, self-improving trade execution. That target is a future operating mode, not a current authorization state. Any movement toward autonomy must remain staged, evidence-backed, monitored, auditable, and constrained by Master V2 / Double Play, Bull or Bear specialist logic, Scope or Capital, Risk or KillSwitch, Execution or Live Gates, and operator-defined safety boundaries.

## 2. Purpose and Non-Goals

**Purpose:**

- Preserve the visual architecture and strategy maps as non-authorizing planning references.
- Provide a shared decision checklist before future slices.
- Make the long-term autonomy target explicit without implying current live authorization.
- Keep Master V2 / Double Play, Bull or Bear, Scope or Capital, Risk or KillSwitch, and Live Gates protected.

**Non-goals:**

- No code changes.
- No runtime changes.
- No config changes.
- No workflow changes.
- No strategy promotion.
- No AI authority.
- No dashboard or cockpit authority.
- No live enablement.
- No approval, signoff, or gate-pass claim.
- No change to Master V2 / Double Play trading semantics.

## 3. Visual Reference Set

The current external visual reference aids are local operator artifacts (not tracked in this repository):

- `PEAK_TRADE_VISUAL_ARCHITECTURE_PACK_V3.pdf` (typically under `Downloads&#47;`)
- `PEAK_TRADE_STRATEGY_VISUAL_MAP_V2_1.pdf` (typically under `Downloads&#47;`)

These files are not treated as runtime source of truth. They can be used to guide discussion, review, and safe slice selection. This document does **not** claim that those PDF filenames exist on every machine; operators store them locally.

## 4. How to Use the Visuals for Future Decisions

Before a future slice starts, use the visual references as a planning checklist:

1. Identify which visual block the slice touches.
2. Decide whether the block is informational, strategy-related, AI-related, dashboard-related, governance-related, or safety-critical.
3. Check whether the slice touches a protected no-touch surface.
4. Check whether the slice would convert a non-authorizing output into authority.
5. Prefer read-only or docs-only work unless the change is explicitly approved and test-backed.
6. Keep any implementation slice narrow, reversible, and validated.

If a slice changes Master V2 / Double Play, Bull or Bear, Scope or Capital, Risk or KillSwitch, Execution or Live Gates, or dashboard or cockpit authority semantics, it must not proceed as an incidental follow-up.

## 5. Visual Architecture Pack V3 Mapping

The architecture visual pack provides these planning blocks:

| Visual block | Meaning | Authority posture |
| --- | --- | --- |
| Legend / color meaning | Explains inputs, validation, knowledge, Master V2, specialists, governance, risk, gates, dashboard, and trade zones. | Non-authorizing. |
| Overall pyramid | Shows movement from inputs toward possible trade execution. | A possible trade sits after all gates; no shortcut implied. |
| Learning Loop | Shows inputs, backtests, validation, Evidence, Registry or Knowledge Base, AI or Analyst layer, Lessons Learned, refinement, and promotion stages. | Learning improves candidates; it does not authorize live trades. |
| Knowledge Base | Stores evidence, lessons, priors, unsafe zones, runtime observations, and operator-facing summaries. | Context only; no direct trade bypass. |
| Christoffersen / statistical validation | Places coverage, independence, and exception-clustering checks as evidence. | Validation or evidence only; not a trading signal. |
| Learning Loop vs Trading Loop | Separates knowledge improvement from actual trading flow. | Controlled handoff only. |
| Trade checkpoint chain | Candidate to research or backtest to Knowledge Base to Master V2 to Double Play to Scope or Capital to Risk to KillSwitch to Execution Gate to Operator or Confirm to possible trade. | Any failed checkpoint blocks progression. |
| Authority matrix / No-Touch zone | Shows what AI, Knowledge Base, Dashboard, Docs, Master V2, Scope or Capital, Risk or KillSwitch, and Execution Gates may and may not do. | No implicit authority transfer. |

## 6. Strategy Visual Map V2.1 Mapping

The strategy visual map provides the current strategy, model, and indicator planning view.

| Strategy family | Example surfaces from visual map | Output type | Authority posture |
| --- | --- | --- | --- |
| Cycle / Timing | Armstrong, Ehlers, ECM-related surfaces | Cycle phase, timing state, filter context | Candidate or context only; no live authority. |
| Volatility / Risk | El Karoui, Bouchaud, Vol Regime surfaces | Volatility estimate, risk context, overlay | Evidence or risk input only; no order path. |
| Mean-Reversion / Oscillator | RSI and mean-reversion surfaces | Reversion signal, oscillator state, filter | Signal or filter only; no gate bypass. |
| Regime / Context | Regime-aware portfolio and regime context surfaces | Regime state, environment label, portfolio context | Context only; no Double Play replacement. |
| Core / Research Strategies | Classical or composite strategy surfaces | Candidate signal, score, evidence | No promotion by presence. |
| Trend / Momentum | Trend and momentum surfaces | Directional filter, momentum score | No independent live path. |

The status lanes in the strategy visual map are evidence categories, not maturity approvals:

- Code-backed
- Code surface
- Config-backed
- Docs or R&amp;D
- Feature or Helper
- Test evidence
- Unclear

A strategy appearing in any lane does **not** imply that it is approved, live-ready, production-ready, or compatible with Master V2 / Double Play without further review.

## 7. Long-Term Autonomy Target

Peak_Trade may ultimately target a fully autonomous, self-improving trading system where the operator mainly reviews:

- executed trades;
- realized and unrealized PnL or loss;
- strategy and Double Play side rationale;
- evidence and confidence context;
- Risk or KillSwitch or gate behavior;
- dashboard or cockpit summaries;
- Learning Loop feedback and lessons learned.

**Long-term autonomy is a target operating mode, not a current authorization state.**

Autonomy must not mean bypassing safety. A mature autonomous system must still be:

- staged;
- evidence-backed;
- auditable;
- monitored;
- bounded by Scope or Capital;
- blockable by Risk or KillSwitch;
- constrained by Execution or Live Gates;
- aligned with Master V2 / Double Play;
- explainable through dashboard or operator surfaces;
- reviewable after execution.

## 8. Staged Autonomy Ladder

| Level | Stage | Meaning | Authority posture |
| ---: | --- | --- | --- |
| 1 | Research | Ideas, indicators, models, candidate concepts. | No execution authority. |
| 2 | Backtest | Historical simulation with fees, slippage, stops, and metrics. | Evidence only. |
| 3 | Evidence / Registry / Knowledge Base | Results and lessons are recorded and compared. | Context only. |
| 4 | Shadow | Observes live-like conditions without placing orders. | No execution authority. |
| 5 | Paper | Simulated execution path. | No real-money authority. |
| 6 | Testnet | Exchange-like non-real-money execution where supported. | No real-money authority. |
| 7 | Bounded Live Pilot | Strictly bounded real-money pilot if separately authorized. | Limited and gated. |
| 8 | Restricted Autonomy | System can act within narrow pre-approved envelopes. | Still gated and monitored. |
| 9 | Supervised Autonomy | Broader autonomy with monitoring, audit, and stop controls. | Revocable and bounded. |
| 10 | Full Autonomy | Mature self-executing operation. | Future target only; not implied now. |

Progression between levels requires explicit evidence and governance. This document does not approve progression.

## 9. No-Touch / Protected Surfaces

Protected surfaces include:

- `src/trading/master_v2/`
- `src/ops/double_play/`
- `src/execution/`
- `src/live/`
- `src/risk_layer/`
- `docs/risk/`
- `docs/ops/runbooks/`
- `.github/workflows/`
- any dashboard, cockpit, or operator surface that consumes Master V2, Risk, KillSwitch, or live-gate state

Protected concepts include:

- Master V2 trading logic;
- Double Play;
- Bull or Bear specialist logic;
- state or side-switch semantics;
- dynamic scope or trailing concepts where present;
- Scope or Capital;
- Risk or KillSwitch;
- Execution or Live Gates;
- dashboard or cockpit as observer or explanation surface unless a specific approved authority path exists.

## 10. Strategy and AI Authority Boundaries

Strategies may produce:

- signals;
- scores;
- filters;
- cycle states;
- volatility estimates;
- regime or context labels;
- candidate metadata;
- evidence;
- dashboard explanations.

Strategies must not:

- place orders directly;
- bypass Master V2 / Double Play;
- bypass Scope or Capital;
- bypass Risk or KillSwitch;
- bypass Execution or Live Gates;
- become live-ready by being present in code, docs, config, or tests.

AI, model, or agent surfaces may:

- summarize;
- rank;
- compare;
- explain;
- classify;
- help generate evidence metadata.

AI, model, or agent surfaces must not:

- authorize live trades;
- override Risk or KillSwitch;
- override Execution or Live Gates;
- convert dashboard or report outputs into approvals;
- replace external or operator authority boundaries.

## 11. Safe Next-Slice Decision Checklist

Before a slice starts, answer:

| Question | Safe answer |
| --- | --- |
| Does it touch Master V2 / Double Play behavior? | No, unless explicitly approved with preservation tests. |
| Does it touch Bull or Bear specialist semantics? | No, unless explicitly approved. |
| Does it touch Risk or KillSwitch behavior? | No for ordinary follow-ups. |
| Does it touch Live Gates or confirm-token behavior? | No for ordinary follow-ups. |
| Does it make AI, strategy, or dashboard output authoritative? | No. |
| Does it alter dashboard or cockpit authority semantics? | No. |
| Is it docs-only or read-only? | Prefer yes. |
| Are claims path-cited and non-authorizing? | Yes. |
| Are validators defined? | Yes. |
| Is there a rollback path? | Yes for any non-docs change. |

## 12. Repo Evidence Anchors

Current repo anchors relevant to this reference include:

- [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md)
- [Runbooks (docs/ops/runbooks)](../runbooks/)
- [Architecture (docs/architecture)](../../architecture/)
- [Risk docs (docs/risk)](../../risk/)
- `src/trading/master_v2/`
- `src/ops/double_play/`
- `src/execution/`
- `src/live/`
- `src/risk_layer/`
- `src/ai_orchestration/`
- `config/`
- `scripts/ops/`
- `.github/workflows/`
- `tests/`

Some anchors are source-tree paths outside `docs/` and are intentionally written as inline path references rather than Markdown links.

## 13. Known Ambiguities

Known ambiguities:

- The visual maps are external PDFs and not canonical runtime artifacts.
- Strategy readiness or status requires per-strategy review.
- A single canonical Knowledge Base implementation may be distributed across registry, evidence, and experiment surfaces.
- Some strategy names may be config-backed, code-backed, helper surfaces, tests, or docs references rather than active production paths.
- Full autonomy is a future target and requires later governance, evidence, monitoring, and operational maturity.

## 14. Follow-Up Candidates

**Safe follow-up candidates:**

1. Docs-only strategy surface map using the curated strategy visual inventory.
2. Docs-only Knowledge Base, Registry, or Evidence taxonomy.
3. Docs-only Learning Loop to repo-path map.
4. Read-only report that lists strategy or model surfaces without changing behavior.
5. Docs-only autonomy ladder elaboration with explicit no-live-authorization wording.
6. Read-only dashboard or cockpit observer-surface map.

**Avoid as first follow-ups:**

- modifying Master V2 / Double Play behavior;
- modifying strategy execution semantics;
- modifying Risk or KillSwitch;
- modifying live gates;
- adding AI-to-trade authority;
- making dashboard or cockpit a trade-authorizing surface.
