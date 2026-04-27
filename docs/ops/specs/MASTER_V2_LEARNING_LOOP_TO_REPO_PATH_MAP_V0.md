---
docs_token: DOCS_TOKEN_MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0
status: draft
scope: docs-only, non-authorizing Learning Loop to repo-path map
last_updated: 2026-04-27
---

# Master V2 Learning Loop to Repo Path Map V0

## 1. Executive Summary

This document maps the **Visual Architecture Pack V3** **Learning Loop** to concrete Peak_Trade repository surfaces.

The Learning Loop is a **learning**, **review**, **evidence**, and **refinement** pathway. It is **not** current autonomous execution, live authorization, **live-ready** status, a **gate pass**, **production-ready** proof, or **externally** completed authority. Its outputs may **inform** research, review, Knowledge Base style context, **candidate** refinement, dashboards, and **future** staged autonomy work, but they must **not** bypass Master V2 or Double Play, Scope or Capital, Risk or KillSwitch, Execution or Live Gates, operator review, or **external** authority processes.

**Long-term** full autonomy remains a **future** operating target, not a current authorization state. This map helps operators and architects **see** where learning artifacts live; it does **not** grant authority.

## 2. Purpose and Non-Goals

**Purpose:**

- Connect the visual Learning Loop to **path-cited** repo and docs surfaces.
- Clarify where hypothesis, backtest, validation, evidence, registry, Knowledge Base, and **controlled** handoff concepts appear.
- Keep learning outputs **separate** from **trade** authority and from **implying** that any strategy is **strategy-ready** without separate governance.
- Support **safe** future docs-only or read-only work.

**Non-goals:**

- No code, strategy implementation, or backtest behavior change.
- No registry or evidence **implementation** change.
- No dashboard or cockpit behavior change.
- No Risk or KillSwitch, execution, or live-gate change.
- No live enablement.
- No claim that **autonomy** is **currently** enabled or that the repo is **autonomous-ready**.

## 3. Learning Loop Reference Model

The **reference** Learning Loop (visual-pack style) is:

```text
Hypothesis / Strategy Idea
  -> Backtest / Simulation
  -> Validation / Stress / Statistical Tests
  -> Evidence Packet / Evidence Index
  -> Registry / Knowledge Base / Experiment Memory
  -> Lessons Learned / Priors / Unsafe Zones
  -> Candidate Refinement
  -> Controlled Handoff
  -> Master V2 / Double Play Context
  -> Scope or Capital, Risk or KillSwitch, Execution or Live Gates
```

The **trading** path (order flow, gating, execution) is **governed elsewhere**; see [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) §3–6 for **system** layers and E2E **information** flow. **This** document focuses on the **learning** path and **where** it touches the tree, without **replacing** that overview.

**Related posture:** [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) (Learning Loop vs trading loop); [MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) (terms and boundaries).

## 4. Step-to-Repo Path Map

| Step | Meaning | Possible repo surfaces | Typical output | Consumer | Non-authority boundary |
| --- | --- | --- | --- | --- | --- |
| 1. Hypothesis / idea | Research question or strategy concept | `src/research/`, `src/strategies/`, `docs/`, `config/` | design notes, **candidate** parameters | author, backtester | **Not** an order. |
| 2. Backtest / simulation | Historical or synthetic exercise | `src/research/`, `tests/`, `scripts/ops/`, strategy packages under `src/strategies/` | metrics, logs, **candidate** signals | research, review | **Not** **live-ready**; **not** **production-ready** from presence alone. |
| 3. Validation / stress / stats | Checks on robustness, coverage, or independence | `tests/`, `src/governance/`, CI under `.github/workflows/`, research modules | test results, policy critic output, statistical summaries | CI, operator, Learning Loop | **Not** a **signoff**; **not** **gate passed** for live. |
| 4. Evidence packet / index | Durable **review** or pointer records | [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md), [../EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md), first-live family specs in `docs/ops/specs/`, e.g. [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_EVIDENCE_INDEX_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_EVIDENCE_INDEX_CONTRACT_V1.md) | indexed rows, JSON or markdown evidence | review, handoff | **Indexed** is **not** **approved** or **externally** closed by the index alone. |
| 5. Registry / Knowledge Base / experiment memory | Where runs and evidence **persist** and are **found** | [../registry/](../registry/), [../registry/INDEX.md](../registry/INDEX.md), specs, `scripts/ops/`, `out&#47;ops&#47;` style output per runbooks | pointers, ledgers, hashes | operator, audit, automation | **Not** **authorization** to trade. |
| 6. Lessons / priors / unsafe | Captured **learning** for **future** work | `docs/ops/specs/`, `docs/ops/runbooks/`, [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](./MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md) | narrative priors, warnings | next experiment, review | **Not** a veto or permit without process. |
| 7. Candidate refinement | Tighter **candidate** or parameters | `src/strategies/`, `config/`, `docs/`, `tests/` | revised **candidate** | research, **controlled** handoff | **Not** Master V2 **readiness** by file edit alone. |
| 8. Controlled handoff | Explicit package to next review step | signoff and handoff contracts, e.g. [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md) | structured handoff | operator or **external** process | **Handoff** is **not** **signoff** **complete** for **external** authority by itself. |
| 9. Master V2 / Double Play **context** | **Decision** packet and specialist path | `src/trading/master_v2/`, `src/ops/double_play/`, [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](./MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) | packets, annotation, selection context | live path when separately wired and gated | **Does not** receive **raw** “learning” as **order** **authority** from this map. |
| 10. Scope, Risk, execution gates | **Constraints** on real activity | `src/execution/`, `src/live/`, `src/risk_layer/`, `config/`, `docs/risk/` | blocks, modes, limits | all downstream paths | **Not** **bypassed** by evidence or **dashboard** text. |

## 5. Hypothesis and Strategy Idea Surfaces

Ideas and **hypotheses** appear as code, **config**, **docs**, and research notebooks or modules under `src/research/` and `src/strategies/`. The [MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) classifies **upstream** strategy families; this step **feeds** those surfaces as **candidates** only.

## 6. Backtest and Simulation Surfaces

Backtests and simulations use strategy implementations, test harnesses, and **ops** or research scripts. Outputs are **evidence** and metrics for **review**, not **execution** on live unless a **separate** governed path and environment say so. Typical paths include `tests/`, `src/research/`, and `scripts/ops/`.

## 7. Validation and Statistical Evidence Surfaces

Validation includes unit and integration `tests/`, **policy** or matrix checks (e.g. `src/governance/`), and CI jobs under `.github/workflows/`. Statistical or robustness ideas appear in the visual reference (e.g. Christoffersen-style framing) as **evidence** posture in [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) §5; in code, see research and test packages per repository layout. **Passing** a test in CI is **regression** signal for **code**, **not** a **live** **approval**.

## 8. Evidence, Registry, and Knowledge Base Surfaces

Use [MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) for term definitions. **Evidence** and **registry** together support **evidence-informed** **staged** progression; neither **authorizes** progression alone.

## 9. Lessons, Priors, Unsafe Zones, and Candidate Refinement

Lessons and priors live in **docs**, **runbooks**, and sometimes **registries** or **reports**. **Unsafe** zones or “do not repeat” notes are **learning** **input** for the next **candidate**, **not** automatic blocks or permits in the execution stack without explicit wiring.

## 10. Controlled Handoff to Master V2 and Double Play

**Controlled** **handoff** means delivering **context** and **candidates** into `src/trading/master_v2/` and `src/ops/double_play/` only through **defined** **interfaces** and **governance** described in the Double Play manifest and related specs. The Learning Loop **does not** **replace** Master V2 or **inject** order **authority** from a report or index row.

## 11. Relationship to Dashboard and Operator Surfaces

Dashboards, WebUI JSON routes, and **operator** runbooks (see [../../ops/runbooks/](../../ops/runbooks/) and `src/webui/`) are **operator** and **explanation** surfaces. They may display Learning Loop or **evidence** **outputs**; they **do not** **authorize** trades or **gates** by display alone, consistent with the dataflow overview and taxonomy.

## 12. Relationship to Long-Term Autonomy

A **future** **autonomy** target may rely on **evidence**, **registry**, and **operator** review of executed behavior; see the staged ladder in [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) §7–8. This map **does not** state that any stage is **active**, **autonomous-ready**, or **externally** **authorized** today.

## 13. Authority Boundaries

| Zone | May do (Learning Loop) | Must not do |
| --- | --- | --- |
| Research and tests | produce **candidates** and **evidence** | **imply** **live** permission from artifacts |
| Evidence and index | support **review** and traceability | **stand in** for **signoff** or **external** process |
| Master V2 / Double Play | consume **governed** **context** | be **bypassed** by “we learned in backtest” alone |
| Risk, execution, live | enforce policy when invoked | be **assumed** **passed** from docs |

**AI** and **orchestration** (`src/ai_orchestration/`, `evals/aiops/`) may assist summarization; they **do not** **authorize** **live** **orders** by this map.

## 14. Known Ambiguities

- The **full** call order from every entrypoint through execution is **not** re-derived here; see [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) §4 and §14.
- **Learning** artifacts may exist without being **wired** to the next **runtime** **slice**.
- Operator-local **output** trees (e.g. under `out&#47;ops&#47;` per runbook) may not exist on every machine.
- **First-live** and **signoff** contract **families** are **large**; this map cites **illustrative** files only.

## 15. Safe Follow-Up Candidates

- **Docs-only** matrix: evidence **packet** type → primary contract file → `EVIDENCE_INDEX` role (illustrative rows only).
- **Read-only** registry or **evidence** listing script (separate slice; touches code and **tests**).
- **Tight** cross-links when new signoff or **readiness** contracts land (mechanical **docs** PRs).
- **Observer-only** double-play or WebUI **JSON** map (separate spec).

## 16. Validation Notes

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

**Deferred canonical narrative:** end-to-end **system** dataflow remains in [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) §3–6. **This** file is a **Learning Loop** companion, not a duplicate **canonical** E2E spec.

**Cross-links (non-exhaustive):**

- [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md)
- [MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md)
- [MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md)

**Inline** references to `src/`, `config/`, `tests/`, `.github/workflows/`, and `out&#47;ops&#47;` are path citations, not **completeness** or **wiring** guarantees.
