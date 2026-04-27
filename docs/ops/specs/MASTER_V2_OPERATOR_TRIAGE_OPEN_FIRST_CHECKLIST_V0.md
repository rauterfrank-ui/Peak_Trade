---
docs_token: DOCS_TOKEN_MASTER_V2_OPERATOR_TRIAGE_OPEN_FIRST_CHECKLIST_V0
status: draft
scope: docs-only, non-authorizing operator triage open-first checklist
last_updated: 2026-04-27
---

# Master V2 Operator Triage Open-First Checklist V0

## 1. Executive Summary

This document is a concise **operator** or **reviewer** triage checklist for the Master V2 visual, strategy, learning, evidence, handoff, and observer reference chain. It answers: which file to open first, what to check, when to continue, and when to stop.

It is **docs-only** and **non-authorizing**. It does **not** replace referenced specs or runbooks, does **not** modify runtime behavior, and does **not** imply **signoff** complete, **gate** pass, **live** **authorization**, **externally** **authorized**, **production-ready**, or **autonomy** **readiness**. Full autonomy is a **future operating target** in other docs, not a current permit stated here.

Use this checklist with the [Reference Chain Pointer](./MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md); it is a **synthesis** aid, not a second encyclopedia.

## 2. Purpose and Non-Goals

**Purpose:**

- Give a practical **open-first** path for inspection and review.
- Reduce uncertainty about **which** reference to read first.
- Provide explicit **stop** conditions (**§4**).
- Preserve **authority** boundaries while supporting review.

**Non-goals:**

- No code, test, workflow, or config change.
- No edit to the **body** of [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md).
- No claim of **signoff** complete, **gate** passed, **live-ready**, or **autonomous-ready** from this file alone.
- **Not** a replacement for [../runbooks/README.md](../runbooks/README.md) or a named operator procedure for live or testnet actions.

## 3. Open-First Checklist

| Step | Open first | Check | Continue if | Stop if |
| ---: | --- | --- | --- | --- |
| 1 | [`MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md`](./MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md) | Which reference family matches the question? | The question maps to a suggested read order. | The ask is for code change, **approval**, or **live** decision using docs alone (**§4**). |
| 2 | [`MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md`](./MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md) | Handoff, verdict, evidence, runbook, or review order. | The work is staged pre-live or first-live **docs** navigation. | **Signoff** **complete**, **gate** **passed**, or **external** authority is treated as proven in-repo only. |
| 3 | [`MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md`](./MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md) | Dashboard, cockpit, report, read-model, or path-level observer context. | The issue is read-only display, summary, explanation, or navigation. | The UI or report is treated as order authority or **live** **enablement**. |
| 4 | [`MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md`](./MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md) | Evidence packet, [EVIDENCE_INDEX](../EVIDENCE_INDEX.md), readiness or handoff-shaped bundles, or provenance. | You only need to relate evidence and review surfaces. | Evidence or a row is treated as **approval** or **live** **permission** by itself. |
| 5 | [`MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md`](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) | KB, Registry, Evidence, or audit-adjacent vocabulary. | The ask is naming, classification, or shared terms. | Vocabulary is treated as a permit to trade. |
| 6 | [`MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md`](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) | Learning Loop, hypothesis, backtest, evidence, or staged refinement. | The ask is path-shaped learning flow (not current **authorization**). | Learning output is treated as autonomous trading or **autonomy** **readiness** as **authorization**. |
| 7 | [`MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md`](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) | Strategy or model family, output type, or consumer. | The ask is where a strategy family sits (map presence is **not** **readiness**). | Map presence is treated as strategy **live** **authorization** or **approval**. |
| 8 | [`MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md`](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) | System dataflow, AI-layer placement, or broad consumer or output context. | The ask is architectural or dataflow-oriented (overview only). | AI or summary output is treated as AI **trade** **approval**. |
| 9 | [`MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md`](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) | No-touch framing, long-term autonomy as a **future** **target** (not current **authorization**), visual or strategy compass. | You need orientation before or after the pointer (**row** **1**). | The visual is treated as runtime SSoT, **live** permit, or bypass of protected surfaces (**§4**). |
| 10 | **No** further **doc** in this list | Any ask for “go **live**,” “**autonomous-ready**,” or “**signoff** **complete**” as a **docs**-only answer. | N/A — do not answer with a spec alone. | Always **stop** and use **§4** plus governed process. |

## 4. Stop Conditions

Stop triage in this file and use a governed operator, org, or regulatory process where it applies, or the protected code surfaces where they apply, if any request would:

- change Master V2 / Double Play, Bull/Bear specialists, Scope/Capital, Risk/KillSwitch, or Execution/Live Gates;
- treat dashboard, cockpit, or report as order **authority**;
- treat AI or strategy output as **live** **trade** **permission**;
- treat evidence as **signoff** **complete** or a catalog row as a **gate** result;
- treat a handoff packet as full **external** **signoff** in-repo only;
- treat Learning Loop output as current **autonomous** **execution**;
- request or imply **live** **enablement** from this checklist alone.

## 5. Triage Paths by Question

| Question type | Open-first path |
| --- | --- |
| What should I read first? | [Reference Chain Pointer](./MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md), then **§3** **row** **1**. |
| Which handoff / verdict / runbook order? | [Operator Handoff Map](./MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md) → [Evidence Packet / Index Nav](./MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md). |
| Which dashboard, cockpit, or report path? | [Observer Surface Inventory](./MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md) → [System Dataflow / AI Overview](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) if broad. |
| Where is evidence packaged or indexed? | [Evidence Packet / Index Nav](./MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md) → [EVIDENCE_INDEX](../EVIDENCE_INDEX.md) and [EVIDENCE_SCHEMA](../EVIDENCE_SCHEMA.md) as appropriate. |
| What is KB / Registry / Evidence vocabulary? | [KB / Registry / Evidence Taxonomy](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) → [Learning Loop Map](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) if flow-shaped. |
| How does backtest or validation connect to learning? | [Learning Loop Map](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) → [KB Taxonomy](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md). |
| Where do strategy families or outputs sit? | [Strategy Visual Map](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) → [Visual Architecture and Strategy Reference](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) for orientation. |
| Where does AI fit in the stack? | [System Dataflow / AI Overview](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) → [Reference Pointer](./MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md) for reading order. |
| Can this become fully autonomous? | [Visual Architecture / Strategy Reference](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) (future **target**, not current **authorization**) + [Learning Loop Map](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md); then **stop** for separate maturity or governance process. |
| Can this trade live? | **Stop** (**§4**). No doc in this chain answers that by itself. |

## 6. What Not To Infer

| Surface | Do not infer |
| --- | --- |
| Reference pointer | Runtime SSoT, **gate** result, or “done” because you read a row. |
| Handoff / verdict / readiness docs | **Signoff** **complete**, **live-ready**, or **externally** **authorized** from packet shape alone. |
| Observer inventory | Cockpit or JSON as trading **permission**. |
| Evidence nav / index | That a **row** **exists** means a **gate** **passed**. |
| KB / evidence taxonomy | A word list as **approval**. |
| Learning Loop map | **Autonomous** trading or current **autonomy** **readiness** as permit. |
| Strategy map | **Readiness**, promotion, or **live** **authorization** from map presence. |
| System / AI overview | AI as trade approver. |
| Visual / strategy reference | **Live** **authorization** or bypass of no-touch rules; see that spec for framing (this checklist does **not** add new no-touch rules). |
| [Runbook index](../runbooks/README.md) | That reading a runbook alone is **permission** to act on live or testnet without a separate check. |

## 7. Protected Surfaces

Triage does **not** authorize code or config changes. Illustrative protected areas (non-exhaustive):

- `src/trading/master_v2/` — core Master V2 / Double Play trading logic.
- `src/ops/double_play/` — Double Play operator-adjacent helpers.
- `src/risk_layer/`, `src/execution/`, `src/live/` — risk, execution, live.
- Dashboard, cockpit, and report **runtimes** — not changed by this doc.

Triage routes the question; it does **not** approve changes, merge PRs, or enable live use.

## 8. Validation Notes

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

A passing docs **gate** on this file does **not** mean **readiness**, **signoff**, or **live** **authorization**.
