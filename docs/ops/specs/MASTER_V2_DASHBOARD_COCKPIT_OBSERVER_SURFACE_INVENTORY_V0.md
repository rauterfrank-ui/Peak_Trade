---
docs_token: DOCS_TOKEN_MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0
status: draft
scope: docs-only, non-authorizing dashboard and cockpit observer surface inventory
last_updated: 2026-05-04
---

# Master V2 Dashboard / Cockpit / Observer Surface Inventory V0

## 1. Executive Summary

This document is a **path-cited**, **read-only** inventory of **observer-oriented** **surfaces**: dashboard and cockpit code, read-model and readiness **docs**, report **scripts**, WebUI read-only JSON **routes** (as specified in separate contracts), evidence and registry **navigation**, and selected runbooks. It is **docs-only**. It does **not** change code, **report** behavior, **dashboard** or **cockpit** **wiring**, **workflows**, the **body** of [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md), or **/tmp** **reports** **.**

This file does **not** **imply** **signoff** **complete** **,** **gate** **passed** **,** **live-ready** **,** **production-ready** **,** **externally** **authorized** **,** or **autonomous-ready** from **publishing** **it** **alone** **. Full **autonomy** is a **future** **operating** **target** in **other** **docs** **;** **it** is **not** a **current** **authorization** **state** **here** **.**

## 2. Purpose and Non-Goals

**Purpose:**

- **Answer** (at a **gross** path level) **which** **paths** act as **observers** for **dashboard** **,** **cockpit** **,** **report** **,** **read-model** **,** **readiness** / **gate** **,** and **evidence**-related work **,** and **for** **whom** **(consumer) **.**
- **Tie** **rows** to **Master** **V2** / **Double** **Play** **,** **Risk** / **KillSwitch** **,** **Execution** / **Live** **Gates** **,** **evidence** **,** and **operator** **handoff** (when applicable) without **redefining** **those** **surfaces** **.**
- **Reinforce** that **read-only** and **summary** **surfaces** do **not** **confer** **order** **authority** **.**

**Non-goals:**

- **No** **code** **,** **test** **,** **workflow** **,** or **config** **change** **.**
- **No** **dashboard** **,** **cockpit** **,** **or** **HTML** / **API** **behavior** **change** **.**
- **No** **EVIDENCE_INDEX** **body** **change** **.**
- **Not** an **exhaustive** list of every path containing **"report"** or **"overview"**; **§4** is **excerpted** and **curated** **.**

## 3. Observer Surface Definition

For this inventory, an **observer** **surface** is a read, **display** **,** **summary** **,** or **navigation** artifact that **helps** a **human** **,** **CI** **,** or **downstream** process **understand** **state** **,** **evidence** **,** **readiness** **,** **session**-related **reports** **,** or **procedures** **,** and **is** **not** **(by** **itself) **a** **trading** or **gate** **authority** **source** **.**

**Observer** **surfaces** may **observe** **,** **explain** **,** **summarize** **,** or **navigate** **. They** **do** **not** **authorize** **trades** **,** **bypass** **Risk** / **KillSwitch** **,** **bypass** **Execution** / **Live** **Gates** **,** or **replace** **operator** or **externally** **governed** **decisions** where **they** **apply** **.**

## 4. Inventory Table

| Surface / Path | Category | Observes | Consumer | Output Type | Authority Boundary |
| --- | --- | --- | --- | --- | --- |
| `src/webui/double_play_dashboard_display_json_route_v0.py` | Dashboard / Cockpit | Double Play **GET** JSON **route** **+** static **fixture** **helpers** **;** **`snapshot_to_jsonable`** **canonical** **`→`** **`src/trading/master_v2/double_play_dashboard_display.py`** **(route** **imports** / **re-exports**) | **operator** / **reviewer** | read-only **JSON** **route** | **Does** not place **orders**; not **live** **authorization**; not **signoff** |
| `src/webui/ops_cockpit.py` | Dashboard / Cockpit | ops **truth** / limits / run state, **Double** **Play** as read-only **context** | **operator** | **HTML** + **payload** | **Observation**-first; not **control** **authority** |
| `src/webui/app.py` | Dashboard / Cockpit | **Route** **graph** (cockpit + **Double** **Play** read-only **JSON** **+** **others) **| **operator** / **dev** | **Python** | **Wiring** is **not** **trading** **permission** **by** **itself** **. |
| `src/trading/master_v2/double_play_dashboard_display.py` | Dashboard / Cockpit | **pure** **Double** **Play** **dashboard** **DTOs** **;** **`snapshot_to_jsonable`** (**JSON v2**) | **webui** / **tests** | **Python** | DTOs are **not** an **order** path; **authority** in **execution** / **gate** code |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md` | Dashboard / Cockpit | **GET** read-only **JSON** **route** **(contract) **| **author** / **reviewer** | **Markdown** | **Contract**; **not** **proof** of **wiring** or **live** **readiness** **alone** **. |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md` | Dashboard / Cockpit | **pure** **stack** **vs** **display** **mapping** (Double **Play) **| **author** / **planning** | **Markdown** | **Map**; not **runtime** **signoff** **. |
| `docs/ops/specs/OPS_SUITE_DASHBOARD_VNEXT_SPEC.md` | Dashboard / Cockpit | **ops**-**suite** **dashboard** (vNext **plan) **| **operator** / **author** | **Markdown** | **Planning**; not **production**-**ready** from **text** **alone** **. |
| `docs/ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md` | Dashboard / Cockpit | futures read-only market dashboard (contract) | **author** / **reviewer** | **Markdown** | read-only framing; not a permit by itself |
| `src/r_and_d/experiments_read_model.py` | Read Model | R&D **experiment** **JSON** on **disk** | R&D / **api** / **reviewer** | **Python** | **Filesystem** read**;** not a **gate** **. |
| `src/webui/r_and_d_api.py` | Read Model | **experiment** **read**-path by **API** | **operator** / **dev** | **Python** | **Serves** read**-**shaped data**;** not **trading** **approval** **. |
| `docs/ops/specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md` | Read Model | pre**-**live **navigation** read **model** | **operator** / **reviewer** | **Markdown** | **Not** **signoff**; not **live** **authorization** **. |
| `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md` | Read Model | **readiness** read **model** (first-**live** **family) **| **operator** / **reviewer** | **Markdown** | **Not** a **gate** **pass** from **this** **doc** **. |
| `docs/ops/GATES_OVERVIEW.md` | Gate / Readiness Surface | **gate** **catalog** in **SSoT**-style | **operator** / **CI** / **author** | **Markdown** | **Describes** **gates**; **not** a **passed** **seal** from **reading** **. |
| `scripts/report_live_sessions.py` | Report Script | **session** / **pilot**-**related** **reporting** (including some **gate**-**shaped** **index** **payloads) **| **operator** / **CI** | **text** / **script** **output** | **Report**; not **approval** or **enablement** by **itself** **. |
| `tests/ops/test_report_live_sessions_gate_index.py` | Test / Fixture Surface | **report_live_sessions** **gate** **index** and **conflict** **cases** | **CI** / **dev** | **Python** | **Test** only; not **production** **signoff** **. |
| `docs/ops/EVIDENCE_INDEX.md` | Evidence / Registry Surface | **evidence** **row** **catalog** | **reviewer** / **author** | **Markdown** | **Inclusion** not **signoff** **complete**; not **gate** **passed** because a **row** **exists** **. |
| `docs/ops/EVIDENCE_SCHEMA.md` | Evidence / Registry Surface | **evidence** **claim** **shapes** | **author** / **tools** | **Markdown** | **Not** a **trading** **permit** **. |
| `docs/ops/specs/MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md` | Evidence / Registry Surface | **KB** / **registry** / **evidence** **terms** | **author** / **learning** | **Markdown** | **Vocabulary**; not **approval** path **. |
| `docs/ops/specs/MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md` | Evidence / Registry Surface | **evidence** **index** and **packet** **navigation** | **operator** / **reviewer** | **Markdown** | **Navigation**; not **approval** **. |
| `docs/ops/specs/MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md` | Evidence / Registry Surface | **Learning** **Loop** to **repo** **path** **hints** | **author** / **planning** | **Markdown** | **Not** **autonomous** **trading**; not **autonomy** **readiness** as **current** **authorization** **. |
| `docs/ops/specs/MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md` | Operator Overview | **strategy** **families** and **repo** **surfaces** | **planning** / **author** | **Markdown** | **Map**; not **strategy** **live** **promotion** **. |
| `docs/ops/specs/MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md` | Operator Overview | **visual** / **strategy** **reference**; **autonomy** as **future** **target** | **planning** / **author** | **Markdown** | **Not** current **autonomy** **authorization** **. |
| `docs/ops/specs/MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md` | Operator Overview | **system** / **AI**-**layer** **overview** | **author** / **planning** | **Markdown** | **Overview**; not **signoff** **. |
| `docs/ops/specs/MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md` | Runbook / Procedure Surface | **operator** **reading** order for **verdict** / **handoff** / **runbooks** | **operator** / **reviewer** | **Markdown** | **Handoff** path**;** not **signoff** or **external** **authority** in-repo only |
| `docs/ops/specs/MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md` | Runbook / Procedure Surface | **reference**-**chain** **reading** order | **author** / **planning** | **Markdown** | **Pointer**; not **gate** result |
| `docs/ops/RUNBOOK_INDEX.md` | Runbook / Procedure Surface | **runbook** **index** | **operator** | **Markdown** | **Index**; not **approval** **. |
| `docs/ops/runbooks/double_play_specialists.md` | Runbook / Procedure Surface | **Double** **Play** **specialist** **procedure** | **operator** | **Markdown** | **Runbook**; **read** is **not** **live** **enablement** **. |
| `docs/ops/runbooks/webui_ops_cockpit_v2_8_truth_first.md` | Runbook / Procedure Surface | **cockpit** **truth**-**first** **procedure** | **operator** | **Markdown** | **Procedure**; not **order** **authority** on **its** own |
| `docs/ops/runbooks/closeout_index.md` | Runbook / Procedure Surface | **closeout** / **export**-**related** **index** | **operator** / **reviewer** | **Markdown** | **Index**; not **signoff** **complete** **. |
| `docs/ops/runbooks/live_readiness_scorecard.md` | Runbook / Procedure Surface | **readiness** / **go**-**no**-**go** (live **family) **| **operator** / **reviewer** | **Markdown** | **Not** **live**-**ready** from **doc** **text** **alone** **. |
| `scripts/ops/validate_docs_token_policy.py` | Report Script | **docs** **token** / **path** **policy** in **Markdown** (local / **CI) **| **CI** / **author** | **Python** | **Policy** **output**; not **trading** or **gate** **verdict** **. |
| `scripts/ops/verify_docs_reference_targets.sh` | Report Script | **markdown** **link** and **path** **existence** | **CI** / **author** | **shell** + **text** | **Link** check**;** not **approval** **. |
| `tests/webui/test_double_play_dashboard_display_json_route.py` | Test / Fixture Surface | read-only **Double** **Play** **JSON** **route** (Test**Client) **| **CI** / **dev** | **Python** | **Test**; not **operational** **signoff** **. |
| `tests/webui/test_ops_cockpit.py` | Test / Fixture Surface | **ops** **cockpit** **HTML** / **API** (many **cases) **| **CI** / **dev** | **Python** | **Test**; not **live** **permission** **. |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_RUNTIME_PRODUCER_DASHBOARD_PREREQUISITE_PARKING_MAP_V0.md` | Unclear / Needs Review | **producer** / **dashboard** **parking** (non-**authorizing** **map) **| **author** / **planning** | **Markdown** | **Navigation**; not a **wiring** or **signoff** **seal** **. |

**Note:** **§4** is **an** **excerpt** (curated), **not** every **git**-**tracked** path that matches generic **vocabulary** **.**

## 5. Surface Categories

- **Dashboard / Cockpit** — `src/webui/`-related **and** **WebUI** **read-only** **contract** **rows**; **read**-**only** or **truth**-**first** **observation** **(see** [MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md) **).**
- **Operator Overview** — high**-**level **system** / **strategy** / **readiness** **maps** in **this** **specs** **tree** **.**
- **Report Script** — `scripts/` **rows** that **emit** **text** or **data** for **CI** or **operator** use **.**
- **Read Model** — read-shaped code and pre-live or R and D docs (for example `src/r_and_d/experiments_read_model.py` and the navigation and readiness spec rows in **§4**).
- **Gate / Readiness Surface** — **GATES** **SSoT**-style **(see** [GATES_OVERVIEW.md](../GATES_OVERVIEW.md) **).**
- **Evidence / Registry Surface** — **index** **,** **schema** **,** **vocabulary** **,** and **path** **maps** for **evidence** **,** **registry** **,** and **learning** **.**
- **Runbook / Procedure Surface** — **`docs/ops/runbooks/`** and **operator** **-**facing **indices** in **`docs/ops/`** **.**
- **Test / Fixture Surface** — **CI** and **dev** **tests** **(not** **production** **signoff** on **its** own **).**
- **Unclear / Needs Review** — **parking** / **planning** **maps**; **treat** as **context** only **.**

## 6. What Each Surface Observes

| **§4** "Observes" **theme** | **Meaning** (informational) |
| --- | --- |
| **Master** **V2** / **Double** **Play** | **Context** and **DTO**-**shaped** **work** in **`src/trading/master_v2/`**; **illustrative** **: [**double_play_composition.py**](../../../src/trading/master_v2/double_play_composition.py) **(this** file **is** only an **inventory) **. |
| **Risk** / **KillSwitch** / **Gates** | **Risk** **,** **session** **,** or **readiness**-**shaped** **data** the **UI** or **docs** can **show** **,** not **redefining** **`src/risk_layer/`** **,** **`src/execution/`** **,** **`src/live/`** (see [§8](#8-relationship-to-risk--killswitch--execution-gates) **).** |
| **Evidence** / **Registry** / **Learning** | **Index** **,** **schema** **,** **vocabulary** **,** **and** **path** **maps**; **not** **approval** from a **row** **alone** **. |
| **Operator** **handoff** / **verdict** | **Staged** **read** of **verdict** and **handoff** **(see** [**MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0**](./MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md) **),** not **external** **signoff** **. |

## 7. Relationship to Master V2 / Double Play

- **Core** **Double** **Play** **display** **code** lives in **`src/trading/master_v2/`** **(including** **`snapshot_to_jsonable`** **in **`double_play_dashboard_display.py`**)** **and** **`src/ops/double_play/`** **(for** **operator**-**facing** **helpers)** **.** **The** **WebUI** **read-only** **JSON** **router** [**double_play_dashboard_display_json_route_v0.py**](../../../src/webui/double_play_dashboard_display_json_route_v0.py) **hosts** **the** **GET** **handler** **and** **static** **fixture** **helpers** **and** **imports** / **re-exports** **`snapshot_to_jsonable`** **from **`trading.master_v2`** **.**
- **Read-only** **contract** **: [**MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0**](./MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md) **.**
- **Bull** / **Bear** **specialist** and **protected** **Double** **Play** **semantics** are **not** **changed** **by** **this** **inventory** **.**

## 8. Relationship to Risk / KillSwitch / Execution Gates

- **Enforcement** **stays** in **`src/risk_layer/`** **,** **`src/execution/`** **,** **`src/live/`** **,** and **governed** **procedures** **(see** [**GATES_OVERVIEW**](../GATES_OVERVIEW.md) for **SSoT** **;** **reading** a **summary** is **not** a **"passed"** **claim) **.**
- **Cockpit** and **report** **scripts** may **show** **posture** or **index**-**shaped** **data**; **they** **do** **not** **bypass** **Risk** / **Execution** **authority** **.**

## 9. Relationship to Evidence / Registry / Learning Loop

- **Evidence** **,** **registry** **,** and **Learning** **Loop** are **covered** **in** [**MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0**](./MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md) **,** [**MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0**](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) **,** and [**MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0**](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) **. **Observer** **surfaces** **do** **not** **turn** those **layers** into **trade** or **signoff** **approval** by **themselves** **.**

## 10. Relationship to Operator Handoff

- **Operator** **handoff** **reading** **order** is in [**MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0**](./MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md) **. **Dashboard** **,** **cockpit** **,** and **report** **outputs** can **support** **that** **review** **(they** do **not** **complete** **signoff** **or** **external** **authority) **.**

## 11. Authority Boundaries

| If **a** **surface** **resembles** | It **may** | It **does** **not** (by **itself) **) |
| --- | --- | --- |
| **Dashboard** / **cockpit** | **show** or **explain** **state** | **authorize** **orders** **,** **arm** **live** **,** or **bypass** **Risk** / **Gates** **. |
| **Read-only** **JSON** / **HTML** | **project** **or** **summarize** **DTOs** and **fixtures** | **mean** a **gate** **passed** or **signoff** **complete** **. |
| **Report** / **runbook** | **guide** or **score** for **review** | **replace** **operator** or **external** **decisions** where **they** **apply** **. |
| **Tests** | **guard** **shape** and **invariants** | **serve** as **sufficient** **live** **evidence** **on** their **own** **. |

## 12. Known Ambiguities

- **`src/webui/app.py`** is **a** **large** **router** **;** the **row** in **§4** is a **gross** **pointer** only **.**
- **`report_live_sessions.py`** has **multiple** **modes** **;** **"** **observes** **"** is **necessarily** **coarse** **.**
- **Some** “**parking**” or **vNext** **rows** are **planning**-**only** **.**
- **Generated** **or** **untracked** **under** `out/` (not **listed** **here) **can** still **matter** to **ops** **;** **out**-**of**-**scope** for **this** **path**-**cited** table **.**
- **This** file is **draft** and **excerpted** **;** **it** is **not** a **full** **catalog** **.**

## 13. Safe Follow-Up Candidates

- A future append-only sweep for more operator-oriented scripts and runbooks (still non-exhaustive; see the [runbook index](../runbooks/README.md) and the ops script entrypoints you already use locally, without treating this bullet as a path catalog).
- **A** **docs**-**only** **list** of **documented** **HTTP** **routes** **(from** **existing** **contracts) **,** if **a** **trigger** **appears** **(no** **route** **behavior** **change) **.**
- **Re**-**triage** **"** **Unclear** / **Needs** **Review**" **rows** if **related** **producer** **/ dashboard** **slices** **land** **.**

**Avoid** (unless **a** **separate** **governed** **change**): **modifying** **cockpit** **,** **reports** **,** **Risk** / **KillSwitch** **,** or **Execution** / **Live** **Gates** **.**

## 14. Validation Notes

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

A **passing** **docs** **gate** on **this** file does **not** **mean** **readiness** **,** **signoff** **,** or **live** **authorization** **.**
