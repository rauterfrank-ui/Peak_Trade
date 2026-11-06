---
title: "Strategy ECM/Armstrong Wiring Inventory Read Model v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-25"
docs_token: "DOCS_TOKEN_STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0"
---

# Strategy ECM/Armstrong Wiring Inventory Read Model v0

## 1) Title

This document is a **read-only inventory** of observed ECM- and Armstrong-related **naming and wiring surfaces** in the repository snapshot at authoring time. It **does not** resolve wiring, add aliases, or change registry, TOML, or code.

## 2) Purpose

- Make **coexisting** module paths, loader keys, config section names, and documentation labels **visible** in one place.
- Give reviewers a **factual** follow-on to [STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md](STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md) §6 (*needs deeper audit*) without inferring a technical conclusion.
- **Park-retain:** historical and research material remains valid to keep; this inventory does **not** call for deletion.

## 3) Non-authority boundary

This read model is **docs-only** and **non-authorizing**. It is **not** evidence, signoff, a gate, or a live/First-Live/Master V2/Double Play approval. If this inventory appears to conflict with a contract, **the contract and code win**; this file is a **map**, not a **decision**.

## 4) Observed ECM / Armstrong surfaces inventory

| Surface | Observed path or key (snapshot) | Observed naming | What it does **not** authorize |
|--------|---------------------------------|-----------------|-------------------------------|
| Central `strategy_id` (catalog) | `armstrong_cycle` in `src/strategies/registry.py` → `StrategySpec` with `config_section="strategy.armstrong_cycle"` | Registered **Armstrong** implementation (`ArmstrongCycleStrategy`) | Live readiness, promotion, Double Play, or MV2 handoff (see [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md), dual-source table) |
| **No** `ecm_cycle` in central `_STRATEGY_REGISTRY` | `src/strategies/registry.py` has **no** `ecm_cycle` `strategy_id` in this pass | `ecm_cycle` is **not** a first-class `StrategySpec` key here | A registry `ecm_cycle` key, an alias to `armstrong_cycle`, or “ECM = Armstrong registry identity” |
| Legacy dynamic loader map | `src/strategies/__init__.py` → `STRATEGY_REGISTRY` maps `"ecm_cycle"` to module `"ecm"` (comment: *Strategie-Name != Modul-Name*) | Separate from `_STRATEGY_REGISTRY` in `registry.py` | That both maps are identical, merged, or deprecated — **not** decided here |
| ECM module (code) | `src/strategies/ecm.py` | Docstring: ECM/Armstrong-style **cycle** math and helpers; cites external **Armstrong/ECM** doc pointers in module prose (path targets **not** verified as present in-repo here) | A second registry key; proof the module is the “same strategy” as `armstrong_cycle` |
| Armstrong implementation module | e.g. `src/strategies/armstrong/` (see central registry `cls=ArmstrongCycleStrategy`) | **Armstrong**-branded R&D strategy path | That ECM naming in `ecm.py` and Armstrong in registry are interchangeable without a dedicated design |
| Config — `ecm_cycle` section | `config/config.toml` includes `[strategy.ecm_cycle]` and related metadata blocks (e.g. `strategies.metadata.ecm_cycle`, lists referencing `"ecm_cycle"`) | Config **name** `strategy.ecm_cycle` | That this section creates or matches a `strategy_id` in `registry.py` |
| Config — `armstrong_cycle` section | `config/config.toml` includes `[strategy.armstrong_cycle]` with `key` / `class_path` style entries | Ties **config** naming to Armstrong class path | Production approval or that config alone satisfies tiering or MV2 |
| Tiering TOML | `config/strategy_tiering.toml` → `[strategy.armstrong_cycle]` (e.g. `tier`, tags including `ecm`) | Operational tiering for **armstrong** key; **no** `[strategy.ecm_cycle]` block in this file (snapshot) | That `ecm_cycle` is tiered the same way, or that tags imply go-live |
| Docs — overview / examples | `docs/strategies_overview.md`, `docs/PEAK_TRADE_OVERVIEW.md` (and authority notes there) | Historical/example and R&D table cells | Registry completeness, live go, or current wiring truth |

**Important (dual registry maps):** The repository exposes **both** a legacy `STRATEGY_REGISTRY` dict in `src/strategies/__init__.py` and the central `_STRATEGY_REGISTRY` in `src/strategies/registry.py`. Their **contents differ** (e.g. `ecm_cycle` appears in the **former**, not the **latter**). This inventory **records** that observation; it does **not** pick a canonical load path for all callers.

## 5) Registry / TOML / module / docs interpretation

- **Registry vs. TOML vs. MV2 §8:** [STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md](STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md) rows (e.g. `armstrong_cycle`) remain the **governance read-model** for **dual-source** interpretation; the inventory does **not** add rows or change Drift labels.
- **Dual-source contract:** [STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md) still governs how registry fields and tiering are read **together** — this inventory does not relax that rule.
- **Docs vs. code:** Name surfaces in `docs/` may **lag** or **diverge** from code; treat divergence as **visible drift**, not authorization.

## 6) Master V2 / Double Play boundary

ECM/Armstrong **naming** and **wiring** clarity does **not** imply:

- Master V2 acceptance, Double Play selection, or execution authority
- live, testnet, paper, or shadow **go**
- research promotion or R&D “graduation”

Any future **adapt-to-Master-V2** or wiring-unification work is a **separate** implementation and review slice, with its own tests and governance.

## 7) Drift risks and safe reading rules

| Risk | Safe reading |
|------|----------------|
| “`ecm_cycle` appears in config and legacy loader, so it must be a central registry `strategy_id`.” | **Read** `registry.py` for actual `StrategySpec` keys; absence is an observed **split**, not an instruction to delete config. |
| “`ecm.py` and Armstrong both mention ECM, so they are the same live strategy.” | Treat as **related math/naming** until a design ties loader, registry, and config **explicitly**. |
| “Tags in tiering say `ecm`, so ECM is live.” | Tags are **metadata**; [reconciliation + MV2](STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md) govern authority. |
| “Overview tables list Armstrong as R&D-only row — done.” | Overview is **not** a substitute for **contracts** and **runtime** policy readers. |

## Live-readiness metadata tension note

There is an observed **source-level tension** between registry-facing metadata for `armstrong_cycle` in `src/strategies/registry.py` (for example `StrategySpec` fields such as `is_live_ready`, `tier`, and `allowed_environments`) and **counter-surfaces** including `config/strategy_tiering.toml` (for example `allow_live = false`), class-level R&D / no-live indicators on `ArmstrongCycleStrategy`, and tests that describe a non-live or research-oriented posture. This section records an **inventory / interpretation risk** only; it is **not** a claim about runtime behavior having changed and **not** an instruction to alter code, configuration, or execution paths from this read model.

Registry metadata alone must not be read as Master V2 approval, Double Play authority, live readiness, first-live readiness, operator authorization, or permission to route ECM / Armstrong behavior into any live capital path. Observed counter-surfaces — including `allow_live = false`, class-level R&D / no-live indicators, and the relevant tests — remain material and must be read **alongside** registry fields, not discarded.

This note does not resolve the tension, does not change registry or TOML behavior, and does not create aliases, renames, promotion, Live permission, or strategy authority. Any future alignment of registry metadata, tiering, class constants, tests, or Master V2 strategy surfaces must be a **separately governed** implementation slice. It must not be inferred from this read model and must not be bundled with this docs-only clarification.

## 8) Safe future audit path

1. Enumerate call sites that use `load_strategy("ecm_cycle")` vs `create_strategy_from_config("armstrong_cycle", …)` / API paths — in a **read-only** or **separate** code audit slice, if needed.
2. **Align naming** (alias, rename, or explicit dual-path documentation) only in an **approved** implementation design — **not** from this inventory.
3. **Refresh** this inventory when registry, TOML, or primary docs change (same PR as those changes, or a dedicated small docs PR).

## 9) Explicit non-scope

This read model does **not**:

- edit `src/`, `tests/`, `config/`, `registry.py`, TOML, or workflows
- add or remove `strategy_id` keys, aliases, or promotions
- assert correctness, incorrectness, redundancy, or “unused” for any path
- change [STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md](STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md) or other strategy specs in this slice
- edit `docs/INDEX.md`

## 10) Validation note

From the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project’s documented Python environment to run the same commands.
