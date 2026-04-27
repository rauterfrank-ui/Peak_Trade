---
docs_token: DOCS_TOKEN_MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0
status: draft
scope: docs-only, non-authorizing strategy surface map
last_updated: 2026-04-27
---

# Master V2 Strategy Visual Map to Repo Surface Map V0

## 1. Executive Summary

This document maps the Strategy Visual Map V2.1 concept to current Peak_Trade repository surfaces.

The map is informational and non-authorizing. Strategy presence in code, config, docs, tests, or visual references does **not** imply maturity, live-readiness, production-readiness, signoff, gate closure, or authorization. Strategy and model surfaces remain upstream producers of candidate, context, signal, score, state, volatility estimate, evidence, or dashboard explanation.

Master V2 / Double Play remains the protected trading architecture. Strategies do not bypass Master V2 / Double Play, Scope or Capital, Risk or KillSwitch, Execution or Live Gates, operator boundaries, or external authority boundaries.

Long-term autonomy remains a future operating target, not a current authorization state.

## 2. Purpose and Non-Goals

**Purpose:**

- Provide a concise repo-facing map for the Strategy Visual Map V2.1.
- Group strategy, model, indicator, and helper surfaces by functional family.
- Clarify status lanes as evidence type, not maturity approval.
- Clarify output types and consumers.
- Preserve Master V2 / Double Play and all safety boundaries.

**Non-goals:**

- No code changes.
- No strategy implementation changes.
- No strategy promotion.
- No config changes.
- No workflow changes.
- No dashboard or cockpit behavior changes.
- No Risk or KillSwitch changes.
- No Execution or Live Gate changes.
- No live enablement.
- No AI authority.
- No claim that any strategy is autonomous-ready.
- No copy of large external inventory dumps into this repository.

## 3. Strategy Visual Map V2.1 Reference

The Strategy Visual Map V2.1 is an external visual planning aid (for example `PEAK_TRADE_STRATEGY_VISUAL_MAP_V2_1.pdf` under operator `Downloads&#47;`). It groups strategy and model surfaces into:

- Cycle / Timing
- Volatility / Risk
- Mean-Reversion / Oscillator
- Regime / Context
- Core / Research Strategies
- Trend / Momentum
- Feature or Helper surfaces
- Unclear / Needs Review

The visual map is not a runtime artifact or source of authority. It should be used as a discussion and planning aid only. Operator-local curated lists or CSV extracts (for example maintained outside the repo for review) are external aids only and are not source-of-truth here.

Related repo docs:

- [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md)
- [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md)

## 4. Strategy Families to Repo Surfaces

The examples below are discovered surfaces or representative names consistent with inventory-style review. They are **example surfaces**, not completeness or maturity claims.

| Family | Example surfaces | Likely repo areas | Non-authorizing role |
| --- | --- | --- | --- |
| Cycle / Timing | `armstrong_cycle`, `ArmstrongCycleStrategy`, `ehlers_cycle_filter`, `EhlersCycleFilterStrategy`, `ecm_cycle` (legacy registry key) | `src/strategies/`, `config/`, `tests/`, docs and spec surfaces | Timing state, cycle phase, filter context, candidate context. |
| Volatility / Risk | `el_karoui_vol_model`, `ElKarouiVolatilityStrategy`, `ElKarouiVolModel`, `bouchaud_microstructure`, `BouchaudMicrostructureStrategy`, `vol_regime_overlay`, `vol_regime_filter` | `src/strategies/`, `config/`, `tests/`, risk-adjacent docs | Volatility estimate, risk context, overlay, evidence input. |
| Mean-Reversion / Oscillator | `rsi_reversion`, `mean_reversion`, `mean_reversion_channel`, `MeanReversionStrategy`, `MeanReversionChannelStrategy` | `src/strategies/`, `config/`, `tests/` | Reversion signal, oscillator state, filter context. |
| Regime / Context | `regime_aware_portfolio`, `RegimeAwarePortfolioStrategy`, `regime_strategy` | `src/strategies/`, `config/`, `tests/` | Regime or market-context label, portfolio context, dashboard explanation. |
| Core / Research Strategies | `BollingerBandsStrategy`, `BreakoutStrategy`, `CompositeStrategy`, `DonchianBreakoutStrategy`, `MACDStrategy`, `MACrossoverStrategy` | `src/strategies/`, `tests/`, research or docs surfaces | Candidate signal, score, research evidence, comparison baseline. |
| Trend / Momentum | `MomentumStrategy`, `TrendFollowingStrategy`, trend or momentum config keys | `src/strategies/`, `config/`, `tests/` | Directional filter, momentum score, candidate context. |
| Feature or Helper surfaces | helper functions or feature builders such as RSI, momentum, or regime helpers | code and tests | Feature production only; not strategy authority. |
| Unclear / Needs Review | any discovered name without clear canonical role | mixed | Must not be promoted without review. |

## 5. Strategy Status Lanes

Status lanes describe where evidence appears in the repository. They are **not** approval levels.

| Status lane | Meaning | Not implied |
| --- | --- | --- |
| Code-backed | A class or concrete code surface appears to exist. | Not live-ready; not authorized. |
| Code surface | Code references or helper logic exist. | Not necessarily a canonical strategy. |
| Config-backed | A config key or config surface exists. | Not enabled or safe by default. |
| Feature or Helper | A helper or feature-producing surface exists. | Not a standalone strategy. |
| Test evidence | A test fixture or test surface references the name. | Not runtime readiness. |
| Docs or R&amp;D | A docs or research reference exists. | Not production status. |
| Unclear | Evidence is ambiguous. | Must not be used as authority. |

## 6. Strategy Output Types and Consumers

| Output type | Possible producers | Possible consumers | Boundary |
| --- | --- | --- | --- |
| Signal | Mean-reversion, trend, core strategy surfaces | Backtests, Learning Loop, candidate handoff | Not direct order authority. |
| Score | strategy or meta-model surfaces | ranking, dashboard, Learning Loop | Not approval. |
| State | cycle, regime, timing surfaces | Master V2 context, dashboard, Knowledge Base | Not Double Play replacement. |
| Volatility estimate | El Karoui, Bouchaud, vol-regime surfaces | risk context, Scope or Capital context, evidence | Not an order path. |
| Risk context | volatility or statistical surfaces | Risk review, Knowledge Base, dashboard | Does not override Risk or KillSwitch. |
| Regime or context label | regime or context surfaces | dashboard, Master V2 context, operator view | Does not replace Bull or Bear specialist logic by itself. |
| Candidate metadata | strategy families or producers | controlled handoff to Master V2 / Double Play | Not live authorization. |
| Evidence | backtest, validation, statistical checks | Registry or Knowledge Base, review surfaces | Not signoff. |
| Dashboard explanation | strategy, AI, and report surfaces | operator or cockpit views | Dashboard does not authorize trades. |

## 7. Relation to Master V2 / Double Play

Strategies are upstream of Master V2 / Double Play.

**Allowed interpretation (informational):**

```text
Strategy or model surface
  -> signal / score / state / volatility estimate / evidence / candidate metadata
  -> controlled handoff
  -> Master V2 / Double Play context
  -> Scope or Capital
  -> Risk or KillSwitch
  -> Execution or Live Gates
  -> operator or confirm where applicable
  -> (possible trade only after all governance; not implied or authorized by this document)
```

**Does not mean:** any strategy name appearing in `src/strategies/`, `config/`, or tests confers Master V2 readiness, Double Play selection authority, or execution permission. For governance classification tables, see [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](./STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) and [STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](./STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md).

## 8. Relation to Learning Loop / Knowledge Base

The Learning Loop and Knowledge Base (as described in the visual architecture reference) are **improvement and evidence** paths. Strategy outputs may feed:

- backtests and experiments;
- results packaging for review;
- evidence or lessons suitable for registries and operator read models.

This document does **not** treat Learning Loop or Knowledge Base as order authority. Registry or evidence entries remain review surfaces, not automatic approvals. See [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) §5–6 and [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) for information paths.

## 9. Relation to Risk / KillSwitch / Execution Gates

- **Risk / KillSwitch:** Volatility, microstructure, or risk-context outputs may inform review or context layers; they do **not** override fail-closed risk semantics. Evidence paths are described under `src/risk_layer/`, `docs/risk/`, and related runbooks.
- **Execution / Live Gates:** Pre-trade and environment gating remain separate from strategy discovery. `src/execution/` and `src/live/` document orchestration, modes, and gates; this map does not substitute those modules.
- **Scope or Capital:** Budget and scope limits apply after Master V2 / Double Play context; strategy output does not bypass them.

## 10. Authority Boundaries

| Layer | May do (informational) | Must not do |
| --- | --- | --- |
| Strategy or model surface | produce candidate, signal, score, state, vol estimate, evidence, explanation | place orders, arm live, bypass Master V2 / Double Play |
| Master V2 / Double Play | apply protected trading packet and specialist context per manifest | be replaced by a raw strategy flag |
| Risk or KillSwitch | block or annotate where wired | be overridden by dashboard or model summary |
| Execution or Live Gates | enforce governance and mode | be treated as “passed” by this document |
| Dashboard or cockpit | observe, explain, display | authorize trades or gates |

AI or orchestration layers may summarize, rank, or explain; they do not authorize live orders by this document. See [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) §6–7.

## 11. Known Ambiguities

- The Strategy Visual Map V2.1 PDF is not versioned in-repo; local filenames may differ.
- Dual or legacy strategy registry entry points can list overlapping names; safe reading follows the dual-source contract, not a single table row.
- A strategy may exist in code while remaining out of scope for a given Master V2 or Double Play slice.
- “Unclear / Needs Review” is a normal state until evidence is collected; it is **not** a failure label for promotion by itself and **not** an approval when cleared elsewhere.

## 12. Safe Follow-Up Candidates

- Tight, docs-only row additions to the registry and tiering reconciliation table (separate spec maintenance), not mixed with this surface map.
- Docs-only Learning Loop to repo-path map, scoped to avoid duplicating the system dataflow overview.
- Read-only report or CLI for inventory listing (separate slice; would touch code and tests).
- Docs-only evidence or registry taxonomy (operator-facing), aligned with [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md).

## 13. Validation Notes

Before merging a change that adds or edits this file in the normal PR flow, run from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

This document was authored under those constraints; fix **only** this file if a validator flags wording or link targets. Inline references to `src/`, `config/`, `tests/`, and `.github/` are path citations, not claims that every subtree is complete for production use.

**Repo evidence anchors (non-exhaustive):**

- `src/strategies/`
- `src/trading/master_v2/`
- `src/ops/double_play/`
- `src/execution/`
- `src/live/`
- `src/risk_layer/`
- `src/ai_orchestration/`
- `config/`
- `tests/`
- `.github/workflows/`
