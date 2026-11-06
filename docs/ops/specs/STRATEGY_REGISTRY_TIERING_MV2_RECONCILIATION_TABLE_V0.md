---
title: Strategy Registry / Tiering / Master V2 Reconciliation Table v0
status: DRAFT
last_updated: 2026-04-24
repo_ref: main@0c7f5f66901e
scope: docs-only read-model reconciliation; non-authorizing
docs_token: DOCS_TOKEN_STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0
---

# Strategy Registry / Tiering / Master V2 Reconciliation Table v0

## 1) Purpose

This document is a **read-only reconciliation** of every `strategy_id` registered in `src/strategies/registry.py` against:

- `config/strategy_tiering.toml` (operational tiering / `allow_live` policy for live-gate style logic), and
- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) §8 (*Initial strategy matrix* — governance classification labels).

It is **not** a live authorization, production approval, or Master V2 readiness sign-off. It does **not** change registry entries, TOML, code, or tests. See [STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md) for the dual-source rule and non-authority constraints.

**Related:** [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) · [STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md)

## 2) How to read this table

| Column | Source |
|--------|--------|
| **Reg. tier** | `StrategySpec.tier` in `registry.py` (default `production` if omitted in table). |
| **Reg. `is_live_ready`** | `StrategySpec.is_live_ready` (default `True` if omitted in table). |
| **Reg. `live` in `allowed_environments`** | `yes` if the tuple includes `live`. |
| **TOML?** | `y` = `[strategy.<key>]` section exists; `n` = no dedicated section. |
| **TOML tier** | `tier` in `strategy_tiering.toml` when `TOML?` is `y`. |
| **TOML `allow_live`** | `allow_live` in TOML when `TOML?` is `y`. |
| **MV2 §8** | Textual classification from the Initial strategy matrix, or `not named` if that key is not on its own row in §8. |
| **Drift / attention** | Inconsistency between sources that operators/reviewers should not interpret as **authority**; `P0` = high risk of misread per dual-source contract. |

## 3) Reconciliation (all current registry keys)

*Snapshot of registry as of `repo_ref` above. `default` = field uses `StrategySpec` default (`tier=production`, `is_live_ready=True`, default `allowed_environments` includes `live` unless specified).*

| strategy_id | Reg. tier | Reg. `is_live_ready` | Reg. `live` in envs | TOML? | TOML tier | TOML `allow_live` | MV2 §8 (contract) | Drift / attention |
|-------------|----------|----------------------|--------------------|--------|-----------|-------------------|-------------------|-------------------|
| `ma_crossover` | `production` | `True` | yes | y | `core` | `false` | `candidate` (with core baselines) | TOML blocks live story; not registry authority — expected dual-source. |
| `rsi_reversion` | default | `True` | yes | y | `core` | `false` | *not named* in §8 | See §8 row for *ma_crossover* / baseline; still non-authorizing. |
| `breakout_donchian` | default | `True` | yes | y | `legacy` | `false` | *not named* | — |
| `momentum_1h` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `bollinger_bands` | default | `True` | yes | y | `core` | `false` | *not named* | — |
| `macd` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `trend_following` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `mean_reversion` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `my_strategy` | default | `True` | yes | y | `legacy` | `false` | *not named* | — |
| `breakout` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `vol_regime_filter` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `composite` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `regime_aware_portfolio` | default | `True` | yes | y | `aux` | `false` | *not named* | — |
| `armstrong_cycle` | `production` | `True` | yes | y | `r_and_d` | `false` | `research-only` | **P0:** Registry *R&D* wording in `description` but `tier=production`, `is_live_ready=True`, `live` allowed — vs. TOML `r_and_d` + `allow_live=false` + `research-only` in §8. |
| `el_karoui_vol_model` | `production` | `True` | yes | y | `r_and_d` | `false` | `research-only` (covers `el_karoui*`) | **P0:** Same pattern as `armstrong_cycle`. |
| `el_karoui_vol_v1` | `production` | `True` | yes | **n** | — | — | *same family as* `el_karoui_vol_model` / `el_karoui*` in §8 | **P0 + alias:** No dedicated TOML section; treat as same family as `el_karoui_vol_model` for policy; registry still has production/live-ready + `live` in envs. |
| `ehlers_cycle_filter` | `r_and_d` | `False` | no | y | `r_and_d` | `false` | `research-only` | Aligned: restrictive registry + TOML + §8. |
| `meta_labeling` | `r_and_d` | `False` | no | y | `r_and_d` | `false` | `research-only` | Aligned. |
| `bouchaud_microstructure` | `r_and_d` | `False` | no | y | `r_and_d` | `false` | `research-only` | Aligned. |
| `vol_regime_overlay` | `r_and_d` | `False` | no | y | `r_and_d` | `false` | `candidate` (§8) | **P1 (semantic):** §8 *candidate* vs. registry `r_and_d` / not live; **not** a contradiction in authority (both non-authorizing) — resolve wording in a future **docs** slice if needed. |

### Registry keys not in TOML

- **`el_karoui_vol_v1` only:** `strategy_tiering.toml` has no `[strategy.el_karoui_vol_v1]`; policy for live-style checks is applied via the primary key `el_karoui_vol_model` in the same file and the alias semantics described in `registry.py` comments.

### TOML strategy sections without a matching `registry` key in this pass

- **`vol_breakout`:** present in `strategy_tiering.toml` as `legacy` but **not** an entry in `_STRATEGY_REGISTRY` in this snapshot. Out of scope for *this* table, which is **registry-key driven**; may warrant a separate inventory if legacy wiring still references it.

## 4) P0 / P1 summary (governance, not “fix it now”)

| Level | strategy_id(s) | What diverges | Safe reading (non-authority) |
|-------|----------------|---------------|--------------------------------|
| **P0** | `armstrong_cycle`, `el_karoui_vol_model`, `el_karoui_vol_v1` | Registry can read as production/live-capable; TOML and MV2 §8 read as research / no live. | None of these fields grant live, promotion, or Master V2 proof — see [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) §4 and [STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md) §3–5. |
| **P1** | `vol_regime_overlay` | `candidate` in §8 vs. `r_and_d` in registry/TOML. | Labeling nuance; not an execution or gate override. |
| *None* | Remaining named rows | TOML and registry are broadly consistent (dual-source still applies: default `production` in registry is catalog semantics, not MV2 go). | — |

## 5) Non-scope and refresh

- This file does not edit `registry.py`, `strategy_tiering.toml`, or runtime behavior.
- Refresh after registry or TOML changes (same PR as those changes, or a dedicated docs PR).
- `Christoffersen tests` and `El Kouri&#47;Elkouri` rows in §8 are not strategy `strategy_id` rows in the registry; they remain documented only in the integration contract.

## 6) Validation (when changing this file)

- `uv run python scripts/ops/validate_docs_token_policy.py` (for changed docs as appropriate)
- `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`
- `bash scripts/ops/pt_docs_gates_snapshot.sh` as required by the repo workflow
