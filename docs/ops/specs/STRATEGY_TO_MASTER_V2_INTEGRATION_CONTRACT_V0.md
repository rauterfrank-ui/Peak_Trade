---
title: Strategy to Master V2 Integration Contract v0
status: DRAFT
last_updated: 2026-04-24
repo_ref: main@fcec89f760d6
scope: docs-only strategy governance contract
docs_token: DOCS_TOKEN_STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0
---

# Strategy to Master V2 Integration Contract v0

## 1. Purpose

This contract defines how strategy modules, strategy registry metadata, research strategies, and future Double Play usage may relate to Master V2.

It is a **docs-only governance contract**. It does not change runtime behavior, registry metadata, strategy code, execution paths, readiness gates, evidence flows, or Double Play behavior.

## 2. Core rule

Strategies may be present, discoverable, researched, tested, and prepared for later Master V2 usage.

Strategies must not independently grant:

- live trading authority
- broker or exchange order authority
- testnet execution authority
- Paper or Shadow mutation authority
- Evidence mutation authority
- promotion authority
- gate authority
- Master V2 readiness authority
- Double Play decision authority

Master V2 remains the governance boundary for readiness, gating, veto, promotion, and any future operational use.

## 3. Canonical references

- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [double_play.md](../runbooks/double_play.md)
- [OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md](OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md)

## 4. Registry metadata interpretation

Strategy registry fields are catalog and compatibility metadata unless explicitly elevated by a separate Master V2 contract.

| Field / concept | Safe interpretation | Unsafe interpretation |
|---|---|---|
| `strategy_id` | Stable identifier for discovery, tests, reports, configs, and docs. | Authority to trade. |
| `tier` | Classification or maturity label. | Live-readiness proof. |
| `is_live_ready` | Historical or catalog signal requiring Master V2 validation. | Standalone live enablement. |
| `allowed_environments` | Compatibility hint for tooling and validation. | Permission to execute in those environments. |
| `research` wording | Review and experimentation status. | Production authorization. |
| `production` wording | Maturity label requiring contextual validation. | Broker/exchange order permission. |
| `double-play` wording | Potential future observation or candidate input. | Double Play authority. |

## 5. Master V2 compatible strategy classification

Every strategy intended for Master V2 / Double Play visibility should be classifiable into one of these non-authorizing categories:

| Classification | Meaning | Allowed next action |
|---|---|---|
| `research-only` | Strategy exists for research, docs, experiments, or offline analysis. | Read-only inventory, tests, docs, backtest review. |
| `candidate` | Strategy may be evaluated for future governance. | Define evidence and robustness requirements. |
| `paper-observable` | Strategy output may be observed in paper context after separate approval. | Display only; no mutation from this contract. |
| `shadow-observable` | Strategy output may be observed in shadow context after separate approval. | Display only; no mutation from this contract. |
| `testnet-blocked` | Strategy must not be used for testnet execution yet. | Gap analysis only. |
| `live-blocked` | Strategy must not be used for live execution. | Remains blocked. |
| `double-play-observable` | Strategy metadata may be shown as context for Double Play review. | Non-authorizing display only. |
| `double-play-candidate` | Strategy may later be considered by Double Play governance. | Requires explicit Master V2 readiness contract. |
| `vetoed` | Strategy is blocked by risk, evidence, governance, or quality concerns. | Display block reason only. |
| `deprecated` | Strategy should not receive new work except archival cleanup. | Archive/read-only docs. |
| `unknown` | Insufficient information. | Read-only audit before any implementation. |

## 6. Strategy-to-Double-Play rule

Double Play must not consume raw strategy registry metadata as authority.

A future Double Play integration may consume strategy information only through a Master V2 compatible layer that provides:

- strategy identity
- source module
- classification
- readiness state
- evidence requirements
- robustness requirements
- known vetoes
- max allowed operational stage
- non-authority label
- provenance
- test coverage status
- review status

## 7. Required evidence dimensions before stronger operational classification

Before a strategy can move beyond research/candidate language, the reviewing contract should address:

- deterministic unit or contract tests
- realistic backtest assumptions
- fees and slippage assumptions
- stop/risk behavior
- walk-forward or out-of-sample behavior
- stress or Monte Carlo behavior
- max drawdown and loss behavior
- strategy failure modes
- data-source assumptions
- config reproducibility
- experiment/registry provenance
- operator review outcome
- explicit veto checks

This contract does not perform or require those checks. It only names the dimensions.

## 8. Initial strategy matrix

| Strategy / concept | Current safe classification | Notes |
|---|---|---|
| `ma_crossover` and core baseline strategies | `candidate` | Baseline strategies may be useful for comparison, but still require Master V2 readiness before operational use. |
| `ehlers_cycle_filter` | `research-only` | Research/cycle filter strategy; no live or Double Play authority from registry metadata alone. |
| `armstrong_cycle` | `research-only` | Treat as research-only until registry/docs drift is resolved by an approved governance slice. |
| `el_karoui_vol_model` / `el_karoui*` | `research-only` | Volatility-model family; not equivalent to live readiness. |
| `meta_labeling` | `research-only` | Potential decision-support layer; must not become automatic promotion authority. |
| `bouchaud_microstructure` | `research-only` | Microstructure research context; no execution authority. |
| `vol_regime_overlay` | `candidate` | Can support regime context after governance review; not a standalone gate. |
| Christoffersen tests | `not-a-trading-strategy` | Risk/VaR backtest statistics, not a strategy candidate. |
| El Kouri / Elkouri | `unknown-name-alias` | Repo appears to use El Karoui naming; treat aliases as documentation/search issue until confirmed. |

## 9. Dangerous anti-patterns

Do not implement patterns where:

1. `tier="production"` implies live readiness.
2. `allowed_environments` including `live` implies order permission.
3. `is_live_ready` bypasses Master V2 readiness.
4. Double Play reads raw strategy metadata as final authority.
5. Strategy modules mutate Paper, Shadow, Evidence, gates, or readiness state.
6. Strategy registry changes unlock execution paths.
7. Research-only modules appear in operator UI as actionable live candidates.
8. Backtest success is treated as promotion.
9. Strategy profile output is treated as live approval.
10. A strategy-specific path bypasses global risk, veto, or operator-review gates.

## 10. Safe follow-up categories

Safe next work should stay within one of these categories:

- read-only strategy inventory
- docs-only classification map
- registry semantics tests that assert non-authority wording or exported metadata shape
- strategy profile discoverability
- deterministic unit tests
- offline-only research validation
- Master V2 readiness contract drafts
- Double Play candidate input contracts without runtime consumption
- veto/reason display contracts
- reproducibility metadata review

## 11. Non-scope

This contract does not:

- edit `src/strategies/registry.py`
- change any strategy module
- change any live/testnet/paper/shadow path
- run a backtest
- create evidence
- alter Master V2
- alter Double Play
- alter gates
- alter risk management
- authorize execution
- promote any strategy

## 12. Review checklist for future strategy work

Before implementing strategy-related work, confirm:

- Is the change read-only, test-only, docs-only, or runtime-changing?
- Does it preserve Master V2 as the governance boundary?
- Does it preserve Double Play as non-authorizing unless explicitly governed?
- Does it avoid Paper/Shadow/Evidence mutation?
- Does it avoid broker/exchange/testnet/live actions?
- Does it avoid interpreting registry metadata as authority?
- Is the max allowed operational stage explicit?
- Are vetoes and unknown states representable?
- Are robustness requirements named before promotion language?
- Is there a rollback/park decision if evidence is insufficient?

## 13. Recommended next slice after this contract

After this contract is accepted, the next safe slice is a read-only classification table or test that maps registry entries to non-authorizing Master V2 classifications.

That follow-up should still avoid changing strategy runtime behavior.
