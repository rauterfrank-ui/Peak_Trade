---
title: Strategy Registry / Tiering Dual-Source Contract v1
status: DRAFT
last_updated: 2026-04-24
repo_ref: main@fb55b5107b05
scope: docs-only strategy governance clarification
docs_token: DOCS_TOKEN_STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1
---

# Strategy Registry / Tiering Dual-Source Contract v1

## 1. Purpose

This contract clarifies the relationship between strategy registry metadata and strategy tiering metadata.

It exists because some research-oriented strategies can appear `production` or `live`-compatible in one metadata surface while being blocked or R&D-only in another.

This is a **docs-only clarification**. It does not change registry entries, tiering config, runtime behavior, live gates, Master V2, Double Play, evidence, tests, or execution paths.

## 2. Canonical references

- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [double_play.md](../runbooks/double_play.md)

## 3. Dual-source rule

Strategy registry metadata and strategy tiering metadata are separate surfaces.

They must not be collapsed into a single authority signal.

| Source | Safe interpretation | Unsafe interpretation |
|---|---|---|
| `src/strategies/registry.py` / `StrategySpec` | Catalog, discoverability, constructor/config compatibility, soft metadata. | Standalone live permission or Master V2 readiness proof. |
| `config/strategy_tiering.toml` | Operational/tiering policy input for live-gate style checks. | Complete strategy governance proof by itself. |
| Master V2 contracts | Governance boundary for readiness, authority, veto, promotion, and future Double Play usage. | Optional documentation that can be bypassed by registry/tiering fields. |

## 4. Non-authority rule

No single metadata source grants:

- live trading authority
- broker or exchange order authority
- testnet execution authority
- Paper or Shadow mutation authority
- Evidence mutation authority
- promotion authority
- gate authority
- Master V2 readiness authority
- Double Play decision authority

A strategy can only become operationally stronger through an explicit Master-V2-compatible governance path.

## 5. Known P0 drift pattern

The following drift pattern is high-risk:

1. Registry metadata says or implies `production`, `is_live_ready=True`, or `allowed_environments` includes `live`.
2. Tiering config says R&D, blocked, or `allow_live=false`.
3. Strategy module/docs describe research-only behavior.
4. Operators or automation could misread the registry as live authority.

This contract classifies that pattern as **P0 Safety / Authority Risk** until a separate approved slice resolves or explicitly documents the intended semantics.

## 6. Current high-attention strategy families

| Strategy family | Safe reading for now | Why |
|---|---|---|
| `armstrong_cycle` | Research-only / blocked from live authority | Registry/tiering/module wording can diverge; treat as non-authorizing until resolved. |
| `el_karoui*` | Research-only / blocked from live authority | Volatility-model family must not become live-ready via registry wording alone. |
| `ehlers_cycle_filter` | Research-only unless separately governed | Cycle-filter research strategy; no standalone authority. |
| `meta_labeling` | Research-only decision-support candidate | Must not become automatic promotion authority. |
| `bouchaud_microstructure` | Research-only | Microstructure context; no execution authority. |
| `vol_regime_overlay` | Candidate / context-only | May support regime context after review; not a standalone gate. |
| `ma_crossover` and baseline strategies | Candidate / baseline comparison | Baseline status still requires Master V2 readiness before operational use. |

## 7. Required reconciliation fields for any future fix

Any future metadata correction or test-only contract should explicitly account for:

- `strategy_id`
- source module
- registry `tier`
- registry `is_live_ready`
- registry `allowed_environments`
- tiering config category
- tiering `allow_live`
- module/doc wording
- current tests
- max allowed operational stage
- Master V2 classification
- Double Play eligibility, if any
- veto or blocked reason
- provenance of the decision

## 8. Safe next actions

Safe follow-ups are limited to:

1. read-only registry-vs-tiering classification table
2. docs-only classification map
3. test-only non-authority assertion
4. registry semantics contract test
5. later metadata correction after explicit approval

Do not change metadata first.

## 9. Unsafe next actions

Do not:

1. flip `allow_live`
2. edit registry `is_live_ready`
3. edit `allowed_environments`
4. reinterpret `tier=production` as live-ready
5. feed raw registry metadata into Double Play authority
6. treat strategy tiering config as sufficient Master V2 readiness
7. activate research strategies in Paper, Shadow, Testnet, or Live
8. run backtests as evidence mutation from this contract
9. create any execution or broker path

## 10. Operator checklist

Before any strategy metadata or governance change, confirm:

- Is this read-only, docs-only, test-only, or runtime-changing?
- Does the change preserve Master V2 as the authority boundary?
- Does it preserve Double Play as non-authorizing unless separately governed?
- Does it avoid Paper, Shadow, Evidence, Testnet, and Live mutation?
- Does it avoid broker/exchange actions?
- Does it distinguish registry metadata from tiering policy?
- Does it provide a blocked/vetoed state where semantics are contradictory?
- Does it include a rollback or park decision?

## 11. Non-scope

This contract does not edit:

- `src/strategies/registry.py`
- `config/strategy_tiering.toml`
- strategy modules
- live gates
- Master V2 code
- Double Play code
- tests
- evidence artifacts
- workflows

## 12. Recommended next slice

After this contract is accepted, the next safe slice is a read-only or test-only reconciliation of registry keys against tiering config and Master V2 classification.

That follow-up must still avoid metadata changes unless separately approved.
