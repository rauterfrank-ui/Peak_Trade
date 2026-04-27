---
docs_token: DOCS_TOKEN_MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0
status: draft
scope: docs-only, non-authorizing Backtest Robustness / Statistical Validation surface inventory
last_updated: 2026-04-27
---

# Master V2 Backtest Robustness / Statistical Validation Surface Inventory V0

## 1. Executive Summary

This document **inventories** **repo** **surfaces** **related** to **backtesting**, **simulation**, **robustness**, **stress** **framing**, **walk-forward**-style **review** **where** **documented**, **statistical** **validation**, **calibration** **discussion**, **performance** **metrics**, **VaR**-style **backtest** **theory** **and** **tests**, and **strategy** / **regime** / **portfolio**-**level** **review** **context**.

It is a **docs-only** **pointer** and **inventory** **surface**. **Backtest** and **validation** **outputs** are **evidence**, **review**, and **learning** **inputs**. They are **not** **strategy** **readiness**, **not** **live** **readiness**, **not** **signoff** **completion**, **not** **gate** **passage**, **not** **external** **authority** **completion**, and **not** **autonomy** **readiness**.

This document **does** **not** **modify** **backtest** **code**, **strategy** **code**, **tests**, **configs**, **runtime** **behavior**, **generated** **artifacts**, **registry** **behavior**, **evidence** **schema** **behavior**, **paper**/**test** **data**, or **Master** **V2** / **Double** **Play** **semantics**.

## 2. Purpose and Non-Goals

**Purpose:**

- Make **backtest** and **validation** **surfaces** **discoverable** for **reviewers** and **operators**.
- **Separate** **robustness** **evidence** from **trading** **authority**.
- **Connect** **statistical** **validation** and **metrics** to **Learning** **Loop**, **Registry**/**Evidence**, and **Session** **Review** **Pack** **navigation** (non-substitutive).
- **Anchor** a **conservative** **map** for **future** read-only **hardening** (optional **follow-on**; **out** of **scope** for **this** **file** **alone**).

**Non-goals:**

- **No** **code** **changes**, **no** **test** **changes**, **no** **workflow** **changes**, **no** **config** **changes**.
- **No** **backtest** or **runtime** **behavior** **change** **by** **this** **document** **alone**.
- **No** **EVIDENCE_INDEX** **body** **edit** **by** **this** **file** **alone**.
- **No** **live** **enablement** and **no** **strategy**-**readiness** **claim** **by** **inventory** **presence** **alone**.

## 3. Inventory Method

This **inventory** is **pattern-driven** and **path-based** (read-only). Representative **search** and **read** **areas** **included**:

- `src&#47;backtest&#47;` — backtest **engine** and **module** **tree** (e.g. `src&#47;backtest&#47;engine.py`, `src&#47;backtest&#47;walkforward.py`, `src&#47;backtest&#47;stats.py`, `src&#47;backtest&#47;registry_engine.py`, phase modules `src&#47;backtest&#47;p*&#47;`).
- `src&#47;risk_layer&#47;var_backtest&#47;` — **VaR** **backtest** **suite** (e.g. **Kupiec** POF, **Christoffersen**-style **tests**, **rolling** **evaluation**, **traffic** **light**).
- `src&#47;risk&#47;validation&#47;` — e.g. `src&#47;risk&#47;validation&#47;backtest_runner.py` where present.
- `src&#47;strategies&#47;` — **strategy** **candidates** and **regime**/**portfolio**-related **helpers** (e.g. `regime_aware_portfolio.py`).
- `src&#47;reporting&#47;` — e.g. `src&#47;reporting&#47;backtest_report.py` where used for **reporting** **surfaces**.
- `tests&#47;backtest` / `tests&#47;risk` / `tests&#47;risk_layer` — **regression** and **statistical** **test** **areas** (examples: `tests&#47;risk_layer&#47;var_backtest&#47;test_christoffersen.py`).
- `docs&#47;` — top-level [`docs&#47;BACKTEST_ENGINE.md`](../../BACKTEST_ENGINE.md) and risk theory docs (e.g. [`docs&#47;risk&#47;KUPIEC_POF_THEORY.md`](../../risk/KUPIEC_POF_THEORY.md), [`docs&#47;risk&#47;PORTFOLIO_VAR_PHASE1.md`](../../risk/PORTFOLIO_VAR_PHASE1.md)); **also** `docs&#47;project_docs&#47;` where integration notes exist.
- `config&#47;` — **configuration** **surfaces** **only** as **cited** in **separate** **governance**; this **file** does **not** **assert** a **canonical** **config** **set**.
- `out&#47;ops&#47;` (where used as **convention** for **operator**-visible **outputs**) — **not** **read** or **implied** as **authoritative** **by** this **inventory** **alone**.

A **path** or **term** **listed** **here** means “**review**-relevant** **surface**”, **not** “**validator** is **green** so **trading** is **approved**”.

## 4. Backtest / Simulation Surfaces

| Surface | Path | Type | Observes / validates | Consumer | Not used for |
| --- | --- | --- | --- | --- | --- |
| **Backtest** **engine** **narrative** | [`docs&#47;BACKTEST_ENGINE.md`](../../BACKTEST_ENGINE.md) | **Doc** | **Backtest** **assumptions** and **mechanics** (review) | **reviewer** / **researcher** | **Not** **live** **authorization**. |
| **Backtest** **core** | `src&#47;backtest&#47;` | **Source** **tree** | **Simulation** **and** **engine** **behavior** (implementation) | **developer** / **CI** | **Not** **strategy** **readiness** **alone**. |
| **Walk-forward** | `src&#47;backtest&#47;walkforward.py` | **Source** | **Walk-forward**-style **structure** (implementation) | **researcher** / **CI** | **Not** **gate** **passage**. |
| **Backtest** **registry** / **ops** | `src&#47;backtest&#47;registry_engine.py` | **Source** | **Backtest** **registry** / **wiring** (implementation) | **developer** | **Not** **approval** **by** **wiring** **alone**. |
| **Integration** **notes** | [`docs&#47;project_docs&#47;BACKTEST_INTEGRATION.md`](../../project_docs/BACKTEST_INTEGRATION.md) | **Doc** | **Integration** **posture** (if applicable) | **reviewer** | **Not** **production-ready** by **narrative** **alone**. |
| **Snapshot** **evidence** (example) | [`backtest_correctness_20251230.md` (audit snapshot)](../../audit/evidence/snapshots/backtest_correctness_20251230.md) | **Doc** (audit) | **Historical** **review** **artifact** (example **link**) | **auditor** | **Not** **current** **authority**. |

*If that snapshot is renamed, update the link in a small docs-only follow-up. Existence in this table is **not** a proof that the file is the latest audit state.*

| **Backtest** **result** / **core** | `src&#47;backtest&#47;result.py` | **Source** | **Result** **abstractions** (implementation) | **developer** | **Not** **signoff** **complete** **by** **itself** |

## 5. Robustness / Stress / Walk-Forward Surfaces

| Surface | Path | Type | Observes / validates | Consumer | Not used for |
| --- | --- | --- | --- | --- | --- |
| **Robustness**-**related** **runbooks** / **ops** | `docs&#47;ops&#47;runbooks&#47;` (discover) | **Docs** | **Operator**-**relevant** **review** **narrative** (where **present**) | **operator** / **reviewer** | **Not** **trading** **permission**. |
| **Backtest** **stats** / **ops** | `src&#47;backtest&#47;stats.py` | **Source** | **Stats**-**shaped** **helpers** (implementation) | **CI** / **researcher** | **Not** **autonomy** **readiness**. |
| **CI** **/** **docs** **safety** **pointer** (adjacent) | [`MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md`](./MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md) | **Pointer** **spec** | **Engineering** **validation** **entry** **points** | **reviewer** / **dev** | **Not** **live** **enablement** |

## 6. Statistical Validation / Calibration Surfaces

| Surface | Path | Type | Observes / validates | Consumer | Not used for |
| --- | --- | --- | --- | --- | --- |
| **Kupiec** / **theory** | [`docs&#47;risk&#47;KUPIEC_POF_THEORY.md`](../../risk/KUPIEC_POF_THEORY.md) | **Doc** | **POF** / **independence** **and** **Phase** **roadmap** **talk** (theory) | **quant** / **reviewer** | **Not** **approval** **by** **theory** **alone** |
| **VaR** **Phase** **narrative** | [`docs&#47;risk&#47;PORTFOLIO_VAR_PHASE1.md`](../../risk/PORTFOLIO_VAR_PHASE1.md) | **Doc** | **What** is / **is** **not** in **phase** **scope** | **reviewer** | **Not** **externally** **authorized** in-repo only |
| **Christoffersen**-style **tests** | `src&#47;risk_layer&#47;var_backtest&#47;christoffersen_tests.py` | **Source** | **IND** / **CC**-style **backtest** **helpers** (implementation) | **CI** / **quant** | **Not** **Risk** /**KillSwitch** **override** |
| **Kupiec** **POF** | `src&#47;risk_layer&#47;var_backtest&#47;kupiec_pof.py` | **Source** | **POF**-style **logic** (implementation) | **CI** / **quant** | **Not** **strategy** **readiness** **alone** |
| **Test** **suite** | `tests&#47;risk_layer&#47;var_backtest&#47;` | **Tests** | **Unit** / **integration** **behavior** for **var_backtest** | **CI** | **Not** **production** **approval** **alone** |
| **Golden** / **suite** **harness** | `tests&#47;risk&#47;validation&#47;` (e.g. `test_suite_golden.py`) | **Tests** | **Reported** **test** **results** (fixtures) | **CI** / **auditor** | **Not** **gate** **passed** in **trading** **sense** |

## 7. Metrics / Performance Surfaces

| Surface | Path | Type | Observes / validates | Consumer | Not used for |
| --- | --- | --- | --- | --- | --- |
| **Backtest** **metrics** (example) | `src&#47;backtest&#47;p31&#47;metrics_v1.py` | **Source** | **Metrics**-**shaped** **output** (implementation) | **researcher** / **CI** | **Not** **live** **authorization** |
| **Backtest** **reporting** (example) | `src&#47;backtest&#47;p32&#47;report_v1.py` | **Source** | **Report** **surface** (implementation) | **operator** (when run) | **Not** **signoff** **complete** |
| **Backtest** **report** (bridge) | `src&#47;reporting&#47;backtest_report.py` | **Source** | **Reporting** **bridge** (if used in runs) | **reviewer** | **Not** **capital** **authority** |
| **Docs**-**stated** **fees** / **slippage** (where any) | `docs&#47;` (search) + `config&#47;` (as governed elsewhere) | **Doc** / **config** | **Assumption** **posture** for **backtests** | **researcher** | **Not** **execution** **guarantee** |

## 8. Strategy / Regime / Portfolio Validation Surfaces

| Surface | Path | Type | Observes / validates | Consumer | Not used for |
| --- | --- | --- | --- | --- | --- |
| **Strategy** **/** **visual** **map** | [`MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md`](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) | **Spec** | **Non-authority** **mapping** **of** **strategy** **outputs** to **repo** | **reviewer** | **Not** **strategy** **approval** |
| **Visual** / **reference** (adjacent) | [`MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md`](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) | **Spec** | **Planning** **/** **posture**; **separate** from **runtime** | **planner** / **reviewer** | **Not** **Double** **Play** **replacement** |
| **Strategies** **package** | `src&#47;strategies&#47;` | **Source** | **Strategy** **candidates** and **composites** (implementation) | **researcher** / **CI** | **Not** **live** **trading** **authority** |
| **Regime** / **portfolio** (examples) | `src&#47;strategies&#47;regime_aware_portfolio.py`, `src&#47;strategies&#47;wrappers&#47;` | **Source** | **Regime**-**aware** **or** **wrapper**-**level** **logic** (implementation) | **researcher** / **CI** | **not** **Scope**/**Capital** **override** by **file** **presence** **alone** |

## 9. Evidence / Registry / Session Review Pack Relevance

**Backtest** and **statistical** **validation** **results** can **support** **evidence** **and** **review** **paths**; they **do** **not** **finish** **signoff** **or** **create** **live** **authority** **by** **themselves**.

**Non-substitutive** **navigation** **anchors** (read **these** for **“where to look”**, **not** for **enabling** **trades**):

- [`MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md`](./MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md)
- [`MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md`](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [`MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md`](./MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md)

## 10. Learning Loop Relevance

**Primary** **anchor** (path **map**; **not** a **trading** **loop** by **itself**):

- [`MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md`](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md)

**Backtest** and **validation** **outputs** may **feed** the **learning** **loop** as **inputs** to **review**, **compare**, and **refine** **hypotheses** — **not** as **permissions** to **bypass** **Master** **V2** / **Double** **Play**, **Scope**/**Capital**, **Risk**/**KillSwitch**, **Execution**/**Live** **gates**, or **operator**/**external** **authority**.

## 11. Authority Boundaries

| Surface | **May** (informational) | **Must** **not** (by this **inventory**) |
| --- | --- | --- |
| **Backtest** **result** | **Support** **evidence** **and** **simulation** **review** | **Authorize** **live** **trading** |
| **Robustness** / **stress** **finding** | **Flag** **fragility** or **stressed** **regimes** in **review** | **Complete** **signoff** **alone** |
| **Statistical** **validation** (VaR, etc.) | **Support** **model**-**risk** **review** | **Prove** **strategy**-**readiness** **or** **external** **approval** **alone** |
| **Metrics** / **report** | **Summarize** **simulated** **or** **backtested** **performance** | **Override** **Risk**/**KillSwitch** |
| **Learning** **Loop** | **Clarify** **where** **review** **touches** **the** **repo** | **Grant** **autonomy** or **bypass** **gates** |

## 12. Known Ambiguities

- The **backtest** **tree** and **strategies** **tree** are **broad**; this **file** is **not** a **complete** **file-by-file** **listing**.
- **Some** **docs** may **use** “**validation**” for **governance** **or** **CI** **senses** that **differ** from **var_backtest** **statistics** — **triage** with **this** **inventory** and **the** **linked** **specs**.
- **Out-of-repo** or **untracked** **run** **artifacts** are **out** of **scope** for **this** **navigation** **aid**.

## 13. Safe Follow-Up Candidates

1. **Tests-only** **characterization** of **a** **small** **allowlist** of **CLI** **help** / **import** **surfaces** for **var_backtest** and **backtest** (fixtures **only**).
2. **Narrower** **docs** **glossary** for **metric** **names** **vs** **risk** **layer** **terms** (add-only, **separate** **PR**).
3. **Avoid** **as** **premature** **follow-ons** **in** the **same** **intent** as **this** **doc**: using **real** **paper**/**live** **artifacts** as **unscoped** **inputs**; treating **outputs** **under** **the** **repository** **out** **tree** **as** **signoff** **by** **themselves**; **changing** **backtest** **defaults** to **suggest** “**readiness**” **without** **governance** **elsewhere**.

## 14. Validation Notes

**Validate** this **docs**-**only** **file** with:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

- **read-only** **validation** of **documentation** only — **not** a **trading** or **gate** **result**.