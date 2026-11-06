---
docs_token: DOCS_TOKEN_MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0
status: draft
scope: docs-only, non-authorizing KB, registry, and evidence taxonomy
last_updated: 2026-04-27
---

# Master V2 KB, Registry, and Evidence Taxonomy V0

## 1. Executive Summary

This document defines a non-authorizing taxonomy for Peak_Trade **Knowledge Base**, **Registry**, **Evidence**, **Experiment Memory**, **Learning Loop**, **read models**, **report surfaces**, **handoff packets**, **runtime artifacts**, and **audit-trail** concepts.

The taxonomy supports visual planning and future safe slice decisions. It does not change runtime behavior, approve strategy readiness, enable live trading, complete external or operator signoff, or grant autonomy. Evidence can **inform** review and evidence-informed staged progression; evidence does **not** by itself **approve** progression or substitute for governance.

**Master V2 / Double Play** remains the protected trading architecture. Knowledge, registry, evidence, AI, strategy, dashboard, and operator-facing surfaces must not bypass Master V2 or Double Play, Scope or Capital, Risk or KillSwitch, Execution or Live Gates, or external or operator authority boundaries.

## 2. Purpose and Non-Goals

**Purpose:**

- Clarify shared vocabulary for learning, evidence, registry, and review surfaces.
- Connect the visual architecture and strategy maps to repository-path concepts.
- Separate learning and review artifacts from trade authority.
- Support future staged autonomy without implying current authorization.

**Non-goals:**

- No code changes.
- No runtime changes.
- No config changes.
- No workflow changes.
- No evidence-schema implementation change.
- No registry implementation change.
- No Knowledge Base product hardening claim by this file alone.
- No strategy promotion.
- No live enablement.
- No approval, signoff, or gate closure claim.
- No assertion that the repository is **autonomous-ready** or that external authority is **completed** here.

## 3. Taxonomy Overview

| Term | Meaning | Possible surfaces | Consumer | Non-authority boundary |
| --- | --- | --- | --- | --- |
| Knowledge Base | Conceptual memory for lessons, priors, unsafe zones, and evidence-derived context. | Specs, registries, evidence indexes, reports; output paths may follow `out&#47;ops&#47;` style conventions in procedures | operator, Learning Loop, future automation | Does not authorize trades. |
| Registry | Structured index of runs, sessions, artifacts, evidence, or operational entries. | [../registry/](../registry/), `scripts/ops/`, `config/` (where registries are configured) | reports, operators, CI review | Indexing is not approval. |
| Evidence | Data or artifact supporting a claim, review, test result, or readiness narrative. | Evidence specs, JSON payloads, reports, CI output | review surfaces, handoffs | Evidence informs; it does not by itself **authorize**. |
| Evidence Index | Navigation catalog of evidence reference records. | [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) | reviewers, operators | **Indexed does not mean approved** or gate-closed. |
| Evidence Packet | Contract-defined or bundle-like evidence shape for a slice. | First-live and signoff family contracts, generated artifacts | review and handoff consumers | A packet existing is not signoff. |
| Experiment Memory | Settings, outcomes, failures, and lessons for experiments. | registries, reports, experiment outputs | Learning Loop, strategy review | Does not override gates. |
| Learning Loop | Iteration from hypothesis through tests, evidence, registry or Knowledge Base, and refinement. | Visual refs, specs, `src/research/`, reports | research, review, future automation | Learning is not live order authority. |
| Read Model | Read-only projection of state or evidence (often docs or report JSON). | Specs, operator reports, read-model docs under `docs/ops/specs/` | operator, CI, review | Read-only, not execution authority. |
| Report Surface | Human or machine-readable summary or snapshot. | `scripts/ops/`, `src/reporting/`, `docs/ops/merge_logs/` (where used) | operators, dashboards, reviewers | A report is not a gate pass. |
| Handoff Packet | Contract-shaped package for another process or authority holder. | [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md) and related | external or operator process | **Handoff is not, by itself, signoff** by an external body. |
| Operator Review Surface | Runbooks, checklists, dashboards, and reports meant for people. | `docs/ops/runbooks/`, WebUI, JSON routes per contracts | operator | Review does not auto-authorize orders. |
| External Authority Surface | Artifacts and procedures that **support** external decision-making, not a substitute for it. | first-live signoff family under `docs/ops/specs/` | process outside the repo as defined by operators | The repo does **not** **complete** external authority by documentation alone. |
| Runtime Artifact | Emitted output from runs, probes, or sessions. | `out&#47;ops&#47;` convention (if used on disk), session logs, JSONL, manifests in procedures | audit, reports, diagnostics | Existence is not retroactive **approval** of a trade or mode. |
| Audit Trail | Traceable chain of steps, inputs, and artifacts. | [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](./MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md), logs, registries | review, incident follow-up | Traceability is not permission. |

## 4. Knowledge Base Concept

In the visual architecture, the **Knowledge Base** is a conceptual memory layer for:

- what worked or failed;
- where failures clustered;
- which contexts mattered;
- which parameters looked unsafe;
- which backtest, validation, or runtime evidence should influence **future** review.

The Knowledge Base may improve **candidate** ranking, test selection, dashboard explanation, comparison, and **future** experiment design.

It must not:

- approve trades;
- assert strategy maturity by presence in memory;
- override Risk or KillSwitch;
- override Execution or Live Gates;
- replace Master V2 or Double Play;
- replace external or operator decision processes.

## 5. Registry Surfaces

Registry surfaces are structured indexes or durable references to operational or evidence-related data. Helpful entry points include:

- [../registry/INDEX.md](../registry/INDEX.md) and sibling registry docs
- `scripts/ops/` (validation, snapshot, or packaging helpers, when present)
- [../registry/README.md](../registry/README.md) for how registry **truth** and pointers are described in-repo

A registry entry means **this was recorded or pointed to**; it does **not** mean **this is safe to trade** or that a gate is **closed** out of band.

## 6. Evidence Surfaces

Evidence surfaces include document contracts, generated payloads, test outputs, run outputs, and linked artifacts for review. Illustrative first-live and signoff-family anchors include:

- [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_EVIDENCE_INDEX_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_EVIDENCE_INDEX_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_READINESS_VERDICT_PACKET_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_READINESS_VERDICT_PACKET_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md)
- [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](./MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md)
- [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) and [../EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md)

**Evidence** can support readiness review, failure analysis, reproducibility, and external or operator decision **processes**. **Evidence** must not be read as: **signoff** complete, **live-ready** as a product claim from this file, **autonomous-ready**, blanket **approval**, a claim that a **gate passed** out of band, or execution **authority** for the trading stack.

## 7. Experiment Memory and Learning Loop Surfaces

**Experiment Memory** records what was tried, under which constraints, and what was learned.

A safe **Learning Loop** is informational only; it is **not** a substitute for the trading loop. A coarse illustration:

```text
hypothesis
  -> backtest or simulation
  -> validation
  -> evidence
  -> registry and Knowledge-Base style records
  -> lessons and priors
  -> refined candidate
  -> controlled handoff to review (not a trade path by itself)
```

**Controlled handoff** may feed Master V2 or Double Play **context** only as separately governed by those layers. The Learning Loop does **not** place orders, arm live sessions, or close governance gates on its own.

## 8. Reports, Read Models, and Operator Handoffs

- **Report surfaces** aggregate metrics, hashes, decisions, or snapshots for humans or machines. They remain **non-authorizing** unless a **separate** operational process and code path state otherwise; this document does not state that.
- **Read models** in `docs/ops/specs/` describe **what may be read** in navigation; see also [../../architecture/](../../architecture/) where cross-linked.
- **Handoff packets** are shaped for the next review step. They are **structural** and **evidence-bearing**, not a substitute for external authority where that process applies. Compare [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md). **A packet is not, by itself, that external signoff.**

## 9. Relation to Strategy Surface Map

[MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) places strategies as **upstream** producers. This taxonomy places **evidence, registry, and learning** as parallel **review and memory** layers. None of these layers grant strategy **authority**; together they help operators and automation **not confuse** “present in a map or index” with “cleared to trade.”

## 10. Relation to Master V2 / Double Play

[MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) describes information paths; [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) sets visual-posture. **Master V2 and Double Play** stay the **governance boundary** for trading semantics. **Knowledge Base**, **registry rows**, and **evidence** entries are **not** a bypass around Master V2 or Double Play, Risk or KillSwitch, or live eligibility unless an **explicit** separate process and code path (not this doc) so states.

## 11. Relation to Autonomy Ladder

**Long-term** autonomy may be a **target** operating mode in which the operator **reviews** trades, PnL, evidence, and gate behavior, as in the visual reference. This taxonomy does **not** state that that mode is **active**, **autonomous-ready**, or **authorized** today. Staged, evidence-informed progression requires **explicit** governance; **this document does not approve** movement up any ladder. See the staged ladder framing in [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) §7–8.

## 12. Authority Boundaries

| Layer | May do (informational) | Must not do |
| --- | --- | --- |
| Knowledge Base, registry, evidence | record, point, inform review, support reproducibility | **authorize** live trading or arm sessions by index presence |
| Master V2 / Double Play | apply protected trading and specialist context | be replaced by a **single** report or **single** index row as **authority** |
| Risk, KillSwitch | block or constrain where wired | be overridden by evidence narrative alone without process |
| Execution, Live Gates | enforce modes and policy | be treated as **passed** because a doc exists |
| External authority surface | support traceability to **external** process | **complete** that process inside the repository by documentation alone |

**AI** and **orchestration** may summarize, rank, or explain; this taxonomy does not grant them trade **authority** (see dataflow overview §6–7). **Strategies** remain non-authorizing producers per the strategy surface map.

## 13. Known Ambiguities

- A single “Knowledge Base” may be **distributed** across registries, indexes, and reports; there is not necessarily one database row.
- **Evidence** and **registry** overlap when an evidence pointer is also in a registry; safe reading is **not** a single “green” signal.
- Operator-local paths such as `out&#47;ops&#47;` may or may not exist on every machine; follow runbooks, not this file, for your layout.
- **First-live** and **signoff** contract families are **large**; this taxonomy does not enumerate every file.

## 14. Safe Follow-Up Candidates

- **Docs-only** Learning Loop to repo path map, scoped to **pointers** and “not duplicated in dataflow overview” deltas.
- **Tight** cross-link maintenance when new **signoff** or **verdict** contracts land (separate, mechanical docs PRs).
- **Read-only** inventory script for registries (separate slice; likely touches code and tests).
- **Observer-only** dashboard map (separate doc; keep non-authority language).

## 15. Validation Notes

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

This file was written to pass those checks; fix **only** this file if a subsequent edit breaks validation. **Inline** references to `src/`, `config/`, `scripts/ops/`, and `out&#47;ops&#47;` are path citations, not product guarantees.

**Related anchor specs (non-exhaustive):**

- [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md)
- [MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md)
- [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md)
