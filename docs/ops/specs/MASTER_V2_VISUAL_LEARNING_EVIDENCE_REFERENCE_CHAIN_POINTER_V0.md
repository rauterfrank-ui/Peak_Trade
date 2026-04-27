---
docs_token: DOCS_TOKEN_MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0
status: draft
scope: docs-only, non-authorizing reference-chain pointer
last_updated: 2026-04-27
---

# Master V2 Visual, Learning, and Evidence Reference Chain Pointer V0

## 1. Executive Summary

This document is a slim **pointer** and **crosswalk** for the recent Master V2 **visual**, **strategy**, **Knowledge Base**, **Registry**, **Evidence**, **Learning Loop**, and **evidence-navigation** references.

It is a **reading-order** guide only. It **does not** replace the referenced specs, **does not** modify runtime behavior, **does not** **approve** strategy readiness, **does not** **complete** **signoff**, **does not** assert a **gate** **passed**, **does not** **authorize** live trading, and **does not** establish **autonomy** **readiness** or **autonomous-ready** status.

Use this pointer when a future slice needs to decide which reference to consult first before changing docs, reports, dashboards, strategy surfaces, evidence surfaces, or Learning Loop surfaces.

## 2. Purpose and Non-Goals

**Purpose:**

- Reduce fragmentation across the visual, strategy, learning, and evidence **reference** **chain**.
- Provide a **recommended** **reading** **order**.
- Clarify which doc answers which kind of question.
- Preserve **authority** **boundaries** while supporting **future** **safe** **planning**.

**Non-goals:**

- No code, runtime, config, or workflow change.
- No evidence **schema** implementation change.
- **No** edit to the **body** of [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) in the same change set as introducing this file.
- No strategy promotion.
- No live enablement.
- No **signoff** **complete**, **gate** **passed**, **approval**, or **externally** **authorized** claim from this pointer alone.
- No claim that this file is **production-ready** documentation of live operations.

## 3. Recommended Reading Order

| Read order | Anchor | Read when | Primary purpose | Not a replacement for |
| ---: | --- | --- | --- | --- |
| 1 | [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) | You need the visual system compass, no-touch frame, and long-term autonomy **target** (not current authorization). | Establish the shared visual and **authority** model. | Runtime source of truth or live **authorization**. |
| 2 | [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) | You need broad system, dataflow, AI-layer, and consumer context. | Map major layers, flows, AI **boundaries**, outputs, and consumers. | Detailed strategy or evidence **catalogs** or every entrypoint trace. |
| 3 | [MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) | You need strategy, model, or indicator **family** placement and output types. | Map strategies to repo surfaces and **non-authorizing** output roles. | Strategy **readiness** or live **approval** from map presence. |
| 4 | [MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) | You need terminology for Knowledge Base, Registry, Evidence, reports, handoffs, and audit trail. | Define vocabulary and **non-authority** **boundaries**. | Evidence **schema** text or runtime implementation. |
| 5 | [MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) | You need hypothesis-to-backtest-to-evidence-to-handoff **flow** as **path** **hints**. | Map Learning Loop steps to repo-path concepts. | **Autonomous** **execution** or strategy **promotion** by learning alone. |
| 6 | [MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md](./MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md) | You need evidence **packet**, evidence **index**, **readiness** **packet**, **handoff** **packet**, and provenance **navigation**. | Explain how evidence **review** **surfaces** **point** to each other. | [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) **body** or **signoff** **completion**. |

## 4. Reference Chain Crosswalk

| Question | Start here | Then read | Why |
| --- | --- | --- | --- |
| "What is the overall system picture?" | [Visual Reference](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) | [System Dataflow](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) | The visual reference gives the **mental** **model**; the dataflow overview adds **repo-layer** detail. |
| "Where do strategies fit?" | [Strategy Surface Map](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) | [Visual Reference](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) | Strategy outputs are **upstream** **candidate** or **context** **surfaces**, not **authority**. |
| "What is the Knowledge Base?" | [KB / Registry / Evidence Taxonomy](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) | [Learning Loop Map](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) | The taxonomy defines **terms**; the Learning Loop shows **flow**. |
| "How does learning feed future decisions?" | [Learning Loop Map](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) | [Strategy Surface Map](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) | Learning **refines** **candidates** and **context**, then **controlled** **handoff**—not automatic live use. |
| "Where do evidence packets and indexes fit?" | [Evidence Packet / Index Navigation](./MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md) | [KB / Registry / Evidence Taxonomy](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md) | The **navigation** **map** shows **relationships**; the taxonomy defines **vocabulary**. |
| "How does this relate to full autonomy?" | [Visual Reference](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) §7–8 | [Learning Loop Map](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md) | Full autonomy is a **future** **target**, not current **authorization**; learning supports **staged** **maturity** only as **governed** elsewhere. |
| "What must not be touched casually?" | [Visual Reference](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md) | [Strategy Surface Map](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md) | **No-touch** and strategy **posture** are summarized there; this pointer does not add new no-touch rules. |

## 5. Which Doc to Read for Which Question

- For **no-touch** and **authority** **framing**, read the **Visual Architecture and Strategy Reference** first.
- For **system-wide** **dataflow** and **AI** **placement**, read the **System Dataflow and AI-Layer Overview**.
- For **strategy** **families** and **strategy** **output** **types**, read the **Strategy Visual Map to Repo Surface Map**.
- For **Knowledge Base**, **Registry**, **Evidence**, and **audit** **vocabulary**, read the **KB / Registry / Evidence Taxonomy**.
- For **hypothesis**, **backtest**, **validation**, **evidence**, **learning**, and **controlled** **handoff** **paths**, read the **Learning Loop to Repo Path Map**.
- For **Evidence Index**, **evidence** **packet**, **readiness** **packet**, **handoff** **packet**, and **provenance** **navigation**, read the **Evidence Packet and Index Navigation Map**.

## 6. Related Catalogs and Contracts

Related but **separate** anchors (not part of the six-spec **chain**, but often used next in **review** **slices**):

- [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) — catalog of evidence **records**; **not** **approval** by **inclusion**.
- [../EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md) — schema **for** **evidence** **claims**; **not** **live** **authorization**.
- [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](./MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md) — **replay** and **trace** **expectations**.
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_EVIDENCE_INDEX_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_EVIDENCE_INDEX_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_READINESS_VERDICT_PACKET_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_READINESS_VERDICT_PACKET_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md](./MASTER_V2_FIRST_LIVE_PRE_LIVE_SIGNOFF_HANDOFF_PACKET_CONTRACT_V1.md)

This pointer **does not** **replace** those **contracts** or the **index** **body**.

## 7. Authority Boundaries

This pointer **does not** **grant** **authority**.

| Surface | Boundary |
| --- | --- |
| Visual references | **Planning** **aids** only. |
| Strategy maps | Strategy **presence** **does** **not** **imply** **readiness** or **approval**. |
| Knowledge Base (concept) | **Learning** **context**, **not** **trade** **permission**. |
| Registry | **Indexing** and **pointers**, **not** **approval**. |
| Evidence | **Review** **input**, **not** **signoff** **by** **itself**. |
| Learning Loop | **Candidate** **refinement**, **not** **current** **autonomous** **execution**. |
| Evidence packets | **Review** **bundles**, **not** **live** **authority**. |
| Handoff packets | **Inputs** to **downstream** **review**, **not** **external** **authority** **completion** in-repo alone. |
| AI summaries | **Explanation** and **comparison**, **not** **trade** **approval**. |
| Dashboard or cockpit | **Observer** and **operator** **view**, **not** **order** **authority** **by** **display** **alone**. |

Master V2 and Double Play, Scope or Capital, Risk or KillSwitch, and Execution or Live Gates remain **protected** **downstream** **boundaries** described in code and **runbooks**, not in this pointer.

## 8. Safe Follow-Up Use

**Safe** uses of this pointer:

- Choose which **reference** to read before a **docs-only** slice.
- Keep **future** **docs** **consistent** in **wording**.
- **Link** **related** **specs** **without** **rewriting** them in every new file.
- Plan **read-only** or **docs-only** follow-ups.

**Unsafe** uses (do **not** do this from this pointer **alone**):

- Treating this pointer as an **approval** **map** or **gate** **pass** list.
- Treating the **visual** **chain** as **live** **readiness** or **production-ready** proof.
- Treating **evidence** **navigation** as **signoff** **complete**.
- Treating Learning Loop **maturity** as **autonomous** **trading** **enablement**.
- Treating strategy **presence** as **authorization**.

## 9. Known Ambiguities

- Some **referenced** **surfaces** are **contracts** rather than **generated** **artifacts** on disk.
- Some **visual** **references** are **external** **local** PDFs rather than **tracked** **repo** **files**; see the **Visual** **Reference** for posture.
- **Knowledge** **Base** **concepts** may remain **distributed** across **registries**, **evidence** **specs**, **reports**, and **output** **conventions** (e.g. `out&#47;ops&#47;` per runbook).
- **Autonomy-ladder** **vocabulary** **beyond** the **visual** **reference** may be **future** **work**.
- **Dashboard** or **cockpit** **observer** **mapping** may need a **separate** **read-only** **inventory** spec.

## 10. Validation Notes

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

Fix **only** this file if validation **fails**. This document is **docs-only** and **non-authorizing**; passing **validators** **does** **not** **imply** **live** **readiness** or **external** **signoff**.

**Primary** **six** **anchor** **chain** (also **listed** in §3):

- [MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md](./MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md)
- [MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md](./MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md)
- [MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md](./MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md)
- [MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md](./MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md)
- [MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md](./MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md)
- [MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md)
