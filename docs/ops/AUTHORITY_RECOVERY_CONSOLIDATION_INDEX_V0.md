---
title: "Authority Recovery Consolidation Index v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-25"
docs_token: "DOCS_TOKEN_AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0"
---

# Authority Recovery Consolidation Index v0

## 1) Title

This document is a **consolidation index** for **docs-only** authority-boundary and misread-guard work delivered under the **P0-A / P0-B / P0-C / P0-D (partial) / P0-E** labels in the `Peak_Trade` documentation track. It is **not** a completion certificate, go decision, or evidence pack.

## 2) Purpose

- Give reviewers and re-onboarders a **single navigation table** to the **key** files that **bound** what CI, runbooks, strategy metadata, and overview text **may** and **may not** imply.
- Make the **operating model** of that workstream explicit: **read-model first**, **small single-topic** documentation slices, **park-retain** (retain, do not drop) for historical or research context.
- **Not** to assert that all governance goals are met, that all P0 work is “done”, or that any live, First-Live, PRE_LIVE, Master V2, or Double Play bar is satisfied.

## 3) Non-authority boundary

This index is **docs-only** and **non-authorizing**. It does **not**:

- grant live, testnet, paper, or shadow **go**
- grant Master V2 handoff, Double Play selection, or execution authority
- substitute for [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md), the [dual-source contract](specs/STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md), or [PRE_LIVE](specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) / enablement [ladder](specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) **substance**
- reference `/tmp` or out-of-repo paths as **canonical** sources of truth

If this index ever conflicts with a **named contract** or the **codebase**, the **contract / code** wins.

## 4) Operating workflow preserved from the consolidation

The following process characteristics are **preserved** as **intent** (not a process gate):

- **Read-only / read-model first** before sweeping edits; prefer **clarify boundaries** over **implying authority**.
- **One topic, one small slice** (one PR or clearly scoped file set), avoiding **Sammel-PRs** that mix unrelated authority topics.
- **Park-retain:** historical, research, or legacy surfaces stay **visible** in docs or config until an **explicit** implementation decision — **not** “delete to hide drift”.
- **Docs-audit slices** in this index **did not** change `src/`, `registry.py`, TOML, workflows, or runtime; future **code** work remains **separate** and **explicitly** scoped.

## 5) Consolidated index table

| Area | File | Misread / authority risk addressed | What it does **not** authorize |
|------|------|--------------------------------------|----------------------------------|
| **P0-A — Workflow / CI as signal** | [runbooks/RUNBOOK_INFOSTREAM_CI.md](runbooks/RUNBOOK_INFOSTREAM_CI.md) | CI / workflow success vs. product truth | Go-live, evidence completeness, operator **go** on its own |
| P0-A | [runbooks/RUNBOOK_CURSOR_AUTO_AUTOMERGE_CI.md](runbooks/RUNBOOK_CURSOR_AUTO_AUTOMERGE_CI.md) | AutoMerge vs. strategy/live readiness | **Merge** = **not** “live-safe” or strategy-approved by itself |
| P0-A | [runbooks/RUNBOOK_PRJ_SHADOW_PAPER_SMOKE_CI.md](runbooks/RUNBOOK_PRJ_SHADOW_PAPER_SMOKE_CI.md) | Shadow / paper / smoke naming vs. handoff authority | A passing job as **double-play** or **Master V2** proof |
| P0-A | [runbooks/RUNBOOK_PRCD_AWS_EXPORT_WRITE_SMOKE_CI.md](runbooks/RUNBOOK_PRCD_AWS_EXPORT_WRITE_SMOKE_CI.md) | Export / write smoke as operational | Production trade **authorization** or **out** as formal evidence |
| **P0-B — Strategy metadata / naming** | [specs/STRATEGY_REGISTRY_SOURCE_COMMENT_DISCORD_NON_AUTHORITY_NOTE_V0.md](specs/STRATEGY_REGISTRY_SOURCE_COMMENT_DISCORD_NON_AUTHORITY_NOTE_V0.md) | Inline **source** comments as **non-authority** | Registry comment as promotion or live go |
| P0-B | [../strategies_overview.md](../strategies_overview.md) | Overview vs. **registry** / epoch | Complete catalog, live go, or **current** truth |
| P0-B | [specs/STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md](specs/STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md) | ECM/Armstrong **name** surfaces | Single interchangeable strategy or hidden registry key |
| P0-B | [specs/STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md](specs/STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md) | **Observed** paths (loader, registry, config names) | Wiring **decision**, alias, TOML/registry **fix** from the inventory alone |
| P0-B | [specs/STRATEGY_VOL_BREAKOUT_LEGACY_TOML_ORPHAN_NON_AUTHORITY_NOTE_V0.md](specs/STRATEGY_VOL_BREAKOUT_LEGACY_TOML_ORPHAN_NON_AUTHORITY_NOTE_V0.md) | TOML section **without** central registry key in reconciliation snapshot | TOML presence = registry **enrollment** or go |
| **P0-C — Wording (partial)** | [../PEAK_TRADE_OVERVIEW.md](../PEAK_TRADE_OVERVIEW.md) | R&D table “Live-Ready” style labels vs. R&D | Research rows as **operational** live go |
| P0-C | [../BACKTEST_ENGINE.md](../BACKTEST_ENGINE.md) | Post-backtest `validate_for_live_trading` **wording** | Heuristic backtest check = **operational** live signoff |
| P0-C | [../risk/README.md](../risk/README.md) | “Live on main” / “production-ready” in **risk** docs | VCS **merge** = **capital** live; engineering text = handoff go |
| P0-C | [../risk/RISK_LAYER_OVERVIEW.md](../risk/RISK_LAYER_OVERVIEW.md) | “Production-ready” / snapshot closing lines | **Risk** backtest code scope = **exchange** go |
| P0-C | [../STRATEGY_LAYER_VNEXT.md](../STRATEGY_LAYER_VNEXT.md) | vNext **registry** *Production-Ready* / tier **labels** as **documentation catalog** (not an operational status) | **Catalog** phrasing as **Master V2** handoff, **live** go, or **strategy promotion** |
| P0-C | [../STRATEGY_DEV_GUIDE.md](../STRATEGY_DEV_GUIDE.md) | Didactic **StrategySpec** / *Production-Ready* **snippets** as **dev-tutorial** context | Example `StrategySpec` blocks as **operational** go, **gate** pass, **evidence**, or **Double Play** proof |
| P0-C | [STRATEGY_SWITCH_SANITY_CHECK.md](STRATEGY_SWITCH_SANITY_CHECK.md) | **Strategy-switch** *live-ready* / *Live-Trading* wording as **offline** config/registry **sanity** semantics | A passing **local** check as **operational** go, **PRE_LIVE**/**enablement** gate substitute, **signoff**, **evidence**, **promotion**, **Master V2** handoff, or **Double Play** proof |
| P0-C | [../PEAK_TRADE_STATUS_OVERVIEW.md](../PEAK_TRADE_STATUS_OVERVIEW.md) | Live-Track **Alerts & Incident** *Production-Ready* / *2026-ready* / *operative Baseline* as **engineering / documentation / runbook** maturity or **historical** phase **status** language in a **project** overview | **Capital** live go, First-Live / PRE_LIVE approval, signoff, evidence, gate pass, order / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| P0-C | [../shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md](../shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md) | Shadow / Dev **Phase 2** operator runbook *Production-Ready* as **Shadow/Dev operator-runbook** documentation maturity (pipeline tick → OHLCV → quality) | Operational real-money go, First-Live / PRE_LIVE approval, signoff, evidence, gate pass, order / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| P0-C | [../risk/STRESS_GATE_RUNBOOK.md](../risk/STRESS_GATE_RUNBOOK.md) | **Stress Gate** *Production-Ready* / *P1* as **risk-module / operator-runbook** **engineering and documentation** maturity (scenarios, thresholds, operator guidance) | Operational real-money go, First-Live / PRE_LIVE approval, signoff, evidence, gate pass, order / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| P0-C | [runbooks/RUNBOOK_PHASE6_STRATEGY_SWITCH_SANITY_CHECK_CURSOR_MULTI_AGENT.md](runbooks/RUNBOOK_PHASE6_STRATEGY_SWITCH_SANITY_CHECK_CURSOR_MULTI_AGENT.md) | **Phase 6** (Governance) *Production-Ready* / **Cursor** **Multi-Agent** / **PR-** and **merge-adjacent** runbook as **docs / operator** **governance** **sanity-check** **runbook** maturity (live strategy-switch check workflow) | A **stand-alone** **PR** / **CI** / **doc** / **governance** / **merge** workflow as an **operational** real-money or **product-level** go; First-Live / PRE_LIVE approval, signoff, evidence, gate pass, order / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| **P0-D — Bounded / Acceptance (landed, partial)** | [BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md](BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md) | P0-D **frontdoor** / inventory **read-model** for bounded/acceptance/go–no-go/**first_live**-shaped **doc surfaces** (navigation map, not a gate) | A **consolidation index** row or **frontdoor** list as **operational** Echtgeld go, **PRE_LIVE** / First-Live approval, signoff, **Evidence**, gate pass, order/exchange/arming/enablement authority, **Master V2** handoff, or **Double Play** proof |
| P0-D | [reviews/bounded_acceptance_go_no_go_snapshot/GO_NO_GO_SNAPSHOT.md](reviews/bounded_acceptance_go_no_go_snapshot/GO_NO_GO_SNAPSHOT.md) | *Proven Now* / *Allowed Now* / go–no-go **snapshot** as **review labels** and **docs** snapshot context | **Snapshot** / **list** as current **trading** authorization, **product** go, signoff, **Evidence**, or gate pass |
| P0-D | [BOUNDED_ACCEPTANCE_INDEX.md](BOUNDED_ACCEPTANCE_INDEX.md) | *Operators* / *governance* / *operationally credible* on the **documentation chain** index | **Chain index** or **credible** wording as unbounded **live** go or **Master V2** / **Double Play** handoff |
| P0-D | [reviews/bounded_acceptance_index_page/INDEX.md](reviews/bounded_acceptance_index_page/INDEX.md) | *Single entrypoint* / *Current Position* / **operational interpretation** on the **review hub** | **Entrypoint** / **operational** framing as org **signoff** or **override** of **Master V2** / **Double Play** |
| P0-D | [reviews/bounded_acceptance_start_here_page/START_HERE.md](reviews/bounded_acceptance_start_here_page/START_HERE.md) | *Default re-entry* / *operator* / *run path* on the **start-here** page | **Re-entry** / *operator-ready* as routing, **arm**, or **enablement** **authority** from navigation alone |
| P0-D | [runbooks/ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md](runbooks/ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md) | **Acceptance**-oriented **bounded** run **operator** runbook **flow**; operator / review **navigation**; launch / run / **credentials** / **acceptance** / **bounded**-run **semantics** (misread as **operational** authorization) | Operational real-money go, First-Live / **PRE_LIVE** approval, signoff, **Evidence**, gate pass, order / **routing** / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| P0-D | [runbooks/BOUNDED_ACCEPTANCE_OPERATOR_CHEAT_SHEET.md](runbooks/BOUNDED_ACCEPTANCE_OPERATOR_CHEAT_SHEET.md) | **Ultra-compact** bounded/acceptance **operator cheat sheet** around **before-run**, *go/no-go*, **checklist**, *pass*, **bounded** / **acceptance**, and **operator** **navigation** (misread as **operational** authorization) | Operational real-money go, First-Live / **PRE_LIVE** approval, signoff, **Evidence**, gate pass, order / **routing** / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| P0-D | [runbooks/BOUNDED_ACCEPTANCE_OPERATOR_VERIFY_CHECKLIST.md](runbooks/BOUNDED_ACCEPTANCE_OPERATOR_VERIFY_CHECKLIST.md) | **Bounded** / **acceptance** **operator verify checklist** around *pass* / *fail*, *go/no-go*, *evidence*, *closeout*, *checklist*, *bounded* / *acceptance* **review** **semantics** (misread as **operational** authorization) | Operational real-money go, First-Live / **PRE_LIVE** approval, signoff, **Evidence**, gate pass, order / **routing** / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| P0-D | [specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md](specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) | **DRAFT** **bounded** **pilot** **entry** **contract**; *pilot* / *entry* / *real money* and signoff-shaped **contract** language (historical and **governed-**shaped read-model context; in-file DRAFT / **not-**authorization framing) (misread as **present-**tense go) | Proof that **this** run is **currently** within the contract, **operational** Echtgeld go, First-Live / **PRE_LIVE** approval, signoff, **Evidence**, gate pass, order / **routing** / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** **proof** from the **spec** text alone |
| P0-D | [runbooks/LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md](runbooks/LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md) | **Local** **bounded** **secret** **launcher** runbook; *secret* **source**, `KRAKEN`, `.bounded_pilot.env`, *launcher*, *bounded*, *trial*, *run*, *local* **ops** **semantics** (misread as **operational** authorization) | Operational real-money go, First-Live / **PRE_LIVE** approval, signoff, **Evidence**, gate pass, order / **routing** / exchange / arming / enablement authority, **Master V2** handoff, or **Double Play** proof |
| **P0-E — PRE_LIVE navigation** | [specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md](specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) | Many **PRE_LIVE** contract filenames; read order | Gate closure, signoff, evidence, or **read order** = go |
| P0-E | [specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md](specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) + pointer to nav read model in-file | L0–L5 steering vs. **PRE_LIVE** pack map | Ladder or map **alone** = enablement **done** |
| **Anchors (governance, not “done”)** | [specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) | Master V2 integration framing | **Automatic** strategy promotion from doc presence |
| Anchors | [specs/STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](specs/STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md) | Registry vs. TOML **dual** interpretation | **Single-field** go from either source alone |
| Anchors | [specs/STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md](specs/STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md) | Reconciliation **read** model | “Fix it now” or **Drift** as **go** without contracts |

*Rows are illustrative groupings. Each linked file’s **own** non-authority and scope sections remain **binding** for that file.*

## 6) Master V2 / Double Play boundary

- **Master V2** and **Double Play** remain the **top** **trading and handoff** frames for the product. This index does **not** add selection authority, leverage approval, or evidence signoff.
- Strategy authority docs listed here **clarify misreads**; they **do not** add **parallel** execution paths.

## 7) Safe continuation rules

- Prefer **one** new **scope** (one topic) per follow-up **docs** PR unless an explicit program asks otherwise.
- When adding **new** runbooks or overview tables, **inherit** the **non-authority** style of the **referenced** specs — **not** a looser “marketing complete” reading.
- Before **code** changes to registry, TOML, or loaders, use a **separate** technical audit or design with tests — **not** an inference from this index.

## 8) Open next-candidate backlog (non-committing)

The following are **candidates only** — **not** scheduled, **not** approved work here:

- **P0-D — Bounded / Acceptance / First-Live** authority: **landed in-repo (partial):** the **P0-D** table rows above (frontdoor, **GO_NO_GO** snapshot, **bounded** chain **index**, **review** hub **index** page, **START_HERE**, the **acceptance-oriented bounded run operator** runbook row, the **operator cheat sheet** row, the **operator verify checklist** row, the **bounded real-money pilot entry contract (anchor spec)** row, and the **local bounded secret launcher** runbook row) record **docs-only** authority-boundary work **indexed** or **merged** as described; that is **not** a claim that **P0-D** is **complete** or that every bounded/acceptance surface is bounded, and **row-listing the entry contract** or the **local bounded secret launcher** runbook does **not** assert a **current** **activated**, **approved**, or **live-ready** state. **Still open as single-topic candidates** where misread is concrete: e.g. **further** operator runbooks, **other** preflight or trial checklists, and **review** surfaces **not** **yet** **row-** **listed** in this table — each as a **narrow** docs read-model or **single** boundary note when scope is **explicit** (no broad Sammel-audit in one PR).
- **Further P0-C wording:** only **single** files or **tight** clusters with a **concrete** misread (e.g. remaining legacy *production-ready* in clearly scoped docs).
- **Entry links** (e.g. from high-traffic `docs/INDEX.md` or entry pages): only when a pointer is **clearly** orphaned and **link risk** (dead discovery) is **higher** than review noise.
- **Code / TOML / registry** changes: only under a **separate** explicit **implementation** or **wiring** audit with tests — **out of scope** for this consolidation index as authority.

## 9) Explicit non-scope

This file does **not**:

- edit any **existing** runbook, spec, or overview **other than** this new path
- edit `docs/INDEX.md` (unless a **separate** slice does so on purpose)
- create evidence, out/ artifacts, or merge proofs
- assert green CI, all-P0 complete, or **any** “system ready to trade” claim

## 10) Validation note

From the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project’s documented Python environment to run the same commands.
