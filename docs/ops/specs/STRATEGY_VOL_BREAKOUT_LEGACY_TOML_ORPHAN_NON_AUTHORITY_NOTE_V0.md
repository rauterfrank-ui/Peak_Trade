---
title: "Strategy vol_breakout Legacy TOML Orphan Non-Authority Note v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-24"
docs_token: "DOCS_TOKEN_STRATEGY_VOL_BREAKOUT_LEGACY_TOML_ORPHAN_NON_AUTHORITY_NOTE_V0"
---

# Strategy `vol_breakout` Legacy TOML Orphan Non-Authority Note v0

## 1) Purpose

This note documents the authority boundary for the `vol_breakout` *legacy surface* where tiering configuration and a Python module can be visible, while **`vol_breakout` is not a `strategy_id` in `src/strategies/registry.py`**.

The goal is to prevent TOML presence, `VolBreakoutStrategy.KEY`, or historical documentation references from being misread as:

- registry authority
- strategy promotion
- live, testnet, paper, or shadow readiness
- Master V2 handoff, approval, or compatibility proof
- Double Play selection, approval, or execution authority
- evidence approval or out-of-band go signals

**Park-retain:** this note is not a call to delete code, config, or research material. It keeps drift visible and labels it *non-authorizing*.

## 2) Observed Surfaces

The following are observed as **separate** surfaces. Their coexistence is documentation of drift, not a resolution.

| Surface | What is observed | Authority boundary |
|---|---|---|
| Tiering TOML | `[strategy.vol_breakout]` exists with `tier = "legacy"`, `allow_live = false`, and operator-facing notes. | TOML fields describe operational tiering; they are not a registry `strategy_id` and not automatic promotion. |
| Strategy registry | `_STRATEGY_REGISTRY` in `src/strategies/registry.py` has **no** key `"vol_breakout"` in the current snapshot. | Absence in the registry is not a silent deletion instruction; it is a **separation of catalog authority** from legacy configuration. |
| Python module | `src/strategies/vol_breakout.py` defines `VolBreakoutStrategy` with `KEY = "vol_breakout"`. | Module presence is not registry enrollment and not readiness proof. |
| Reconciliation read-model | The reconciliation table lists TOML strategy sections that lack a matching registry key, including this case. | The table is read-only; it does not authorize wiring changes. |
| Other docs | `docs/strategies_overview.md` and research-phase materials may name `vol_breakout`. | History and examples are not the current strategy catalog. |

Governance and reconciliation context (read alongside this note, not as overrides):

- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md)
- [STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md)
- [STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md](STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md)
- [STRATEGY_REGISTRY_SOURCE_COMMENT_DISCORD_NON_AUTHORITY_NOTE_V0.md](STRATEGY_REGISTRY_SOURCE_COMMENT_DISCORD_NON_AUTHORITY_NOTE_V0.md)
- [STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md](STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md)

This table is a reading aid. It is not a registry correction, not a TOML edit, and not a wiring fix.

## 3) Non-Authority Boundaries

This note does **not** create or imply:

- a `vol_breakout` `strategy_id` in `src/strategies/registry.py`
- an alias to another `strategy_id`
- a change to `config/strategy_tiering.toml`
- a change to `src/strategies/vol_breakout.py`
- a promotion or demotion in strategy tier
- a Master V2 or Double Play outcome
- permission to run, arm, or validate trading

Any future enrollment, removal, or rename requires a **separately** reviewed implementation design, tests, and governance alignment.

## 4) Master V2 and Double Play Boundary

Master V2 and Double Play remain the **top** execution and handoff frame.

Even if a future audit concludes that `vol_breakout` should be wired, retired, or replaced, that conclusion does not transfer authority from this note. **Adapt-to-Master-V2** work remains a distinct slice.

`vol_breakout` must not be read as:

- Master-V2-approved
- Double-Play-selected
- live-capable
- testnet-blessed
- paper or shadow *ready by mention*

## 5) Registry, TOML, and Module Drift Interpretation

A safe way to read the current split:

- **Registry** answers: *which `strategy_id` values are defined in the central catalog* (`_STRATEGY_REGISTRY`).
- **TOML** answers: *how tiering policy keys sections when they exist* (`[strategy.<key>]`).
- **Module** answers: *whether runnable code exists* under a `KEY` string.

All three can disagree for legacy and research material. **Disagreement is expected** until a dedicated audit or adapt-to-Master-V2 effort reconciles them.

**Misreads to avoid:**

- "`[strategy.vol_breakout]` exists, so it must be in the registry under the same name."
- "`VolBreakoutStrategy` exists, so it is automatically registered and live-gated the same as production catalog entries."
- "`legacy` means harmless; ignore tiering and registry entirely." (Unsafe: *legacy* is still a policy-labeled surface, not a Master V2 skip.)

## 6) Safe Future Audit Path

A future, explicitly scoped read-only or implementation slice can:

1. Map call sites, loaders, and any registration glue that still references `vol_breakout` or `strategy.vol_breakout`.
2. Compare against the dual-source contract and the reconciliation table.
3. Propose a **separate** decision: keep parked, document-only alias, or remove with tests — **not** in this note.

Until then, **preserve** the mismatch visibly (park-retain) and do not treat absence from `_STRATEGY_REGISTRY` as "safe to delete without review."

`docs/strategies_overview.md` remains historical and non-authority; it does not override the integration contract or the dual-source table.

## 7) Explicit Non-Scope

This note does not:

- edit `src/strategies/registry.py`
- edit `config/strategy_tiering.toml`
- edit `src/strategies/vol_breakout.py`
- add aliases, renames, or registry keys
- change runtime, backtest, or execution code paths
- change paper, shadow, testnet, or live behavior
- create or change `out/` or evidence outputs
- change workflows, CI, or strategy promotion mechanics
- claim that `vol_breakout` is recommended, complete, or Master-V2-compatible

## 8) Validation Note

For documentation-only changes to this file, from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project’s documented Python environment to run the same commands.
