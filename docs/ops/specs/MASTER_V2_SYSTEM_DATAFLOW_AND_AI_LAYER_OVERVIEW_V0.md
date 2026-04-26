---
title: "Master V2 System Dataflow and AI-Layer Overview v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-27"
docs_token: "DOCS_TOKEN_MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0"
---

# Master V2 System Dataflow and AI-Layer Overview v0

## 1. Executive Summary

This document is a **canonical, information-only** overview of Peak_Trade **system dataflows**, **information paths**, the **AI-layer** (models, agents, evals, automation, advisory outputs), **major consumers**, and **authority and safety boundaries**, as they appear from **current repository evidence**.

It is **docs-only** and **non-authorizing**. It does **not** approve live trading, testnet, bounded-pilot, or operator signoff. It does **not** pass gates, assert production readiness, or treat specs, runbooks, gate indexes, JSON, reports, machine summaries, or AI outputs as permission to trade, arm sessions, or bypass risk, KillSwitch, dry-run, paper, shadow, or live gating. **Master V2 / Double Play** is the **primary** trading-logic architecture in this slice; other layers are described in support.

A coarse flow (five steps) appears in the evidence:

1. **Inputs** — market, config, research, operator, CI, evidence, and (where present) model or eval configuration.
2. **Transformation** — research, backtest, strategy, `master_v2` Double Play decision-support, risk and scope where wired, and AI or automation layers that **summarize, score, or gate in CI**, not that **authorize live orders** by this document.
3. **Constraint** — `ExecutionOrchestrator` and `src/execution/pipeline.py` provide **separate, evidence-backed** execution and governance semantics; **KillSwitch** and **live eligibility** act as **blocking or annotating** layers where the code and docs state.
4. **Outputs** — reports, registries, execution events, JSON snapshots, runbooks, specs, **CI** results, and operator handoff **surfaces**.
5. **Consumers** — runtime modules, tests, CI, operators, external review, and **future** automation; none of which are granted authority by this file.

**Review correction (repo-evidence):** In `src/execution/orchestrator.py`, `ExecutionOrchestrator.__init__` defaults to `execution_mode=ExecutionMode.PAPER`. The enum also includes `ExecutionMode.LIVE_BLOCKED` for **explicit** governance block semantics; that is **not** the same as the constructor default. `src/execution/pipeline.py` documents that **live** order execution is governance-locked and that `env="live"` can raise `GovernanceViolationError` (see module docstring). **Do not** read this overview as a substitute for those modules or for operator process.

**Related, non-substitutive specs:** [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md); [../../architecture/INTEGRATION_SUMMARY.md](../../architecture/INTEGRATION_SUMMARY.md); [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md); [../EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md).

## 2. Purpose and Non-Goals

**Purpose**

- Summarize data and information **flows** and **where** in the tree they are implemented or specified.
- Place the **AI-layer** (orchestration, registry, policy checks, evals, automation) **without** elevating it to trade authority.
- Keep **Double Play** (Bull or Bear specialist selection on one instrument) as the **stated** strategy-side anchor; deeper semantics live in the Double Play manifest.
- Support architects and operators **reviewing** the repo, not **unlocking** runtime.

**Non-goals**

- No code, test, workflow, or config change (this file alone).
- No live enablement, gate relaxation, or KillSwitch bypass.
- No claim that AI, agents, or LLM outputs **approve** orders or **override** risk.
- No replacement of detailed contracts, runbooks, or L1–L5 pointer disciplines.
- No assertion that a path is **complete** end-to-end in production; see §14.

## 3. System Layers Overview

| Layer (informal) | Primary evidence in repo | Role (informational) |
|------------------|--------------------------|------------------------|
| **Operator and architecture docs** | `docs/ops/specs/`, `docs/ops/runbooks/`, `docs/architecture/`, [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) | Read models, runbooks, ladders, **non-authorizing** maps. |
| **Master V2 / Double Play** | `src/trading/master_v2/`, `src/ops/double_play/`, [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) | Decision packets, **specialist** and switch-gate **annotation**; manifest defines **state-switch** (side change) vs **Kill-All** and **no hot-path heavy AI** per manifest. |
| **Execution** | `src/execution/` | `ExecutionOrchestrator` (`orchestrator.py`) with modes including `LIVE_BLOCKED`; `pipeline.py` for strategy-to-order path with **live** governance lock as documented. |
| **Live / session** | `src/live/` (e.g. `live_gates.py`, shadow session modules) | Eligibility, **double_play** hook-in, **R&amp;D tier** blocks for non-research modes where defined. |
| **Risk and KillSwitch** | `src/risk_layer/kill_switch/`, `docs/risk/`, `src/ops/gates/risk_gate.py` | **Fail-closed** and operational risk semantics; see `docs/risk/KILL_SWITCH.md` for **ExecutionGate** and CLI. |
| **AI / orchestration / evals** | `src/ai_orchestration/`, `config/model_registry.toml`, `config/capability_scopes/`, `evals/aiops/`, `src/governance/policy_critic/`, related workflows under `.github/workflows/` | **Advisory**, CI, or research-facing layers unless a **separate** code path shows otherwise. |
| **WebUI and reporting** | `src/webui/app.py`, `src/reporting/` | Read-only or gated surfaces per module documentation. |
| **CI and tests** | `.github/workflows/`, `tests/` | Regression, **policy** gates, and contract tests — **not** live approval. |

## 4. End-to-End Data and Information Flow

A simplified **information** flow (not a promise of a single deployable hot path) appears as:

```text
External and internal sources (market, config, operator, CI, evidence)
  -> ingest and strategy research layers (e.g. src/data/, src/research/, src/strategies/)
  -> Master V2 / Double Play packet and specialist logic (src/trading/master_v2/, src/ops/double_play/)
  -> live eligibility and feature gates (src/live/live_gates.py) where invoked
  -> execution pipeline and orchestration (src/execution/pipeline.py, src/execution/orchestrator.py)
  -> risk hook and KillSwitch checks (e.g. risk_hook, risk_gate, src/risk_layer/kill_switch/)
  -> events, ledgers, replay, telemetry, reports, WebUI JSON, and ops registries
  -> consumers: runtime, tests, CI, operators, external signoff, future automation
```

**Unclear from current repository evidence without line-by-line runtime tracing:** the full **ordered** call chain from every entrypoint (CLI, WebUI, scheduled job) through to exchange adapters in all deployment shapes.

## 5. Inputs and Entry Points

- **Market and data** — e.g. `src/data/`, `src/data/providers/`, `src/ingress/` (orchestrated intake patterns appear under `src/ingress/orchestrator/`).  
- **Configuration** — `config/config.toml`, `config/live_policies.toml`, `config/bounded_live.toml` (evidence and claims in [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md)), `config/strategy_tiering.toml`, `config/portfolio_presets/`, `config/model_registry.toml`, and `config/capability_scopes/` (per-file TOML scopes in that directory).  
- **Master V2 Double Play read models and contracts** — see `docs/ops/specs/` (e.g. [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)); related futures input, readiness maps, and **read-only** WebUI route contracts in the same directory.  
- **Runtime and session** — `src/live/`; environment and safety patterns documented in runbooks; CI workflows set **non-live** defaults in some jobs (e.g. `PEAK_TRADE_LIVE_ENABLED` / `PEAK_TRADE_LIVE_ARMED` in scheduled probes — see `.github/workflows/class-a-shadow-paper-scheduled-probe-v1.yml` if present in tree).  
- **Operator and evidence** — [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md), [../EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md), [../../ops/runbooks/](../../ops/runbooks/) (as linked from the index). **Pointer records** in First-Live and bounded-pilot specs are **not** in-repo signoff.  
- **AI and evaluation** — `src/ai_orchestration/`, `evals/aiops/` (e.g. `evals/aiops/README.md`, `evals/aiops/promptfooconfig.yaml`), workflows such as `aiops-promptfoo-evals.yml`, `ai-model-cards-validate.yml`, `market_outlook_automation.yml` under `.github/workflows/`.  
- **Tests** — e.g. `tests/trading/master_v2/`, `tests/webui/`, `tests/ai_orchestration/`, and other packages under the `tests` tree as **specification of behavior**, not **approval**.  

## 6. Transformations and Decision-Support Flow

- **Feature and signal construction** — `src/analytics/`, `src/regime/`, `src/research/`, `src/research/ml/` (e.g. classifiers in `meta_labeling.py` for **research** paths — **not** a standalone proof of live execution wiring).  
- **Master V2** — input adaptation and decision packet construction in `src/trading/master_v2/` (e.g. `input_adapter_v1.py`, `local_evaluator_v1.py`, `decision_packet_v1.py`); **validation** and **critic** steps as implemented in code.  
- **Double Play specialist choice** — `src/ops/double_play/specialists.py` implements `evaluate_double_play`; the module docstring states it **does not execute trades** and is used for **selection or annotation** with **switch-gate** state. Integrated from `src/live/live_gates.py` (import present in repository).  
- **Pre-trade and execution** — `src/execution/pipeline.py` and `src/execution/orchestrator.py` with `RiskHook` and `kill_switch_should_block_trading` import in `orchestrator.py` (as of current tree).  
- **Policy and governance code** — e.g. `src/governance/policy_critic/`, `src/governance/validate_ai_matrix_vs_registry.py` (matrix vs registry check — **tooling**, not external signoff).  
- **Docs and operator** — runbooks and specs transform **knowledge** into **procedure**; they **do not** execute orders.

## 7. AI-Layer Logic

| Surface (evidence) | Role (informational) | Authority |
|--------------------|----------------------|-----------|
| `config/model_registry.toml` | Model catalog and **layer** mapping in governance docs. | **Config only**; not a trade permit. |
| `config/capability_scopes/L0_ops_docs.toml` (and sibling scope files) | Scoped capabilities per layer in architecture docs. | **Constraint** documentation; not live gate closure. |
| `src/ai_orchestration/` | Clients, orchestration, **SOD**-related patterns in code and tests. | **Advisory** or **automation** unless a dedicated execution path is proven; appears from current repo evidence as **separate** from order placement. |
| `docs/architecture/INTEGRATION_SUMMARY.md` | Maps **Execution Orchestrator** to L6 in the **AI autonomy** matrix and states **EXEC (forbidden)** in that table row for the orchestration component listed there. | **Document** semantics; do not conflate with a single “autonomy parser” in runtime without further evidence. |
| `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` | Authoritative **matrix** in that doc’s own terms. | **Not** a trading permit. |
| `src/governance/policy_critic/` | Policy checks; outputs feed **CI** and review. | **Not** a substitute for human governance on live. |
| `src/knowledge/vector_db.py` | Vector search backing; WebUI documents **gated** POST for some knowledge APIs in `src/webui/app.py` docstring. | **Information retrieval**; not order authority. |
| `src/obs/ai_telemetry.py` (import in `orchestrator.py`) | Optional **telemetry** hooks. | **Observability**; not a trading decision. |
| `evals/aiops/` | Prompt and scenario **evals** for tooling (see `evals/aiops/README.md`). | **Test and CI** surfaces. |
| Workflows: `aiops-promptfoo-evals.yml`, `aiops-trend-*.yml`, `market_outlook_automation.yml` | Automation and **NO-LIVE** patterns per linked runbook language where applicable. | **CI and docs**, not live approval. |

**Non-authority (explicit):** The Double Play manifest [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) states that **no** selector, **no** AI dashboard, and **no** strategy registry **takes trading authority** (see manifest “Repository safety note” and §21). This overview **repeats** that **documentation** constraint; it does not add a new one.

**Consumers of AI-layer outputs (typical, non-exhaustive):** operators reading reports, **CI** gates, research notebooks, and documentation pipelines — **not** automatic live order enablement from this file.

## 8. Master V2 / Double Play Flow

- **Primary spec** — [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md): **Long/Bull** vs **Short/Bear** layers around one selected future; **state-switch** (normal side change) is **not** the same as **Kill-All**; **dynamic scope** is bounded by governance and static limits.  
- **Bull and Bear as specialists** — `src/ops/double_play/specialists.py` returns an **active specialist** label (`"bull"` or `"bear"`) from **switch-gate** state when `double_play_enabled` is true.  
- **Meta-switch and scope** — switch-gate **score** and **hysteresis** / **hold** / **cooldown** appear in the same module as `SwitchGateConfig` and `step_switch_gate` (from `src/ops/gates/switch_gate.py`). **Scope and capital** envelope semantics are **specified** in Double Play **capital** and **readiness** contracts in `docs/ops/specs/` (e.g. capital slot contract, **pure stack** maps); they appear from current repo evidence as **governance and risk** boundaries, **not** a separate unbounded “strategy brain.”  
- **Code modules** — `src/trading/master_v2/` (e.g. `double_play_state.py`, `double_play_futures_input.py`, `local_evaluator_v1.py`, `decision_packet_v1.py`); tests in `tests/trading/master_v2/`.  
- **No live authorization** — this section does not grant Testnet, Live, or **armed** session permission.

## 9. Execution, Risk, KillSwitch, and Live-Gating Boundaries

- **`ExecutionOrchestrator`** — `src/execution/orchestrator.py`: default **`ExecutionMode.PAPER`** on `__init__` (repo evidence). Modes include **`LIVE_BLOCKED`**; routing treats **live-blocked** as a **governance** rejection path (see class and routing comments in file). **Do not** describe **PAPER** as **LIVE_BLOCKED**.  
- **Pipeline** — `src/execution/pipeline.py`: **live** execution described as **locked**; `GovernanceViolationError` for disallowed **live** path per module documentation. This is a **separate** surface from the orchestrator default mode.  
- **KillSwitch and execution gate** — `src/risk_layer/kill_switch/`, `docs/risk/KILL_SWITCH.md`, `src/risk_layer/kill_switch/execution_gate.py` (cited in risk docs), CLI under `src/risk_layer/kill_switch/cli.py`, helper script `scripts/ops/kill_switch_ctl.sh` referenced from documentation. **Runtime state** paths are described in `KILL_SWITCH.md` and may not exist in a clean checkout.  
- **Live gates** — `src/live/live_gates.py` and `config/live_policies.toml`; **R&amp;D** tier cannot run in `live`, `paper`, `testnet`, or `shadow` as enumerated in that module (`BLOCKED_MODES_FOR_R_AND_D`).  
- **Double Play** — eligibility integration via `evaluate_double_play` in `live_gates.py` (import path in repository). **Annotation**, not a substitute for full execution and broker checks.  
- **CI safety patterns** — some workflows set `PEAK_TRADE_LIVE_ENABLED` / `PEAK_TRADE_LIVE_ARMED` to false and preflight `config` **paper** mode for class schedules; see `.github/workflows/class-a-shadow-paper-scheduled-probe-v1.yml` for a **concrete** example in tree.

## 10. Outputs, Registries, Reports, and Operator Surfaces

- **Reporting and HTML** — `src/reporting/`, R&amp;D and dashboard routes described in `src/webui/app.py`.  
- **JSON and DTOs** — e.g. `src/live/web/`; display-route tests under `tests/webui/` (e.g. `test_double_play_dashboard_display_json_route.py`) — **contract tests** for payloads, not authority.  
- **Replay and ledger** — `src/execution/replay_pack/`, `src/execution/ledger/`.  
- **Evidence and merge logs** — [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md), [../merge_logs/](../merge_logs/) (if present in tree as indexed). **Evidence** entries are **records of claims** with metadata, not automatic approval.  
- **Operator runbooks** — `docs/ops/runbooks/`. **Handoff** and **closeout** semantics appear in runbooks; they remain **procedural** and **external** where those runbooks say so.  
- **Model cards and AI validation** — workflow `ai-model-cards-validate.yml` — **CI** validation, not trading permission.

## 11. Consumers of Information Products

- **Runtime components** — execution, live, and ops modules **consume** configs and in-memory state; **governance** and **env** still apply.  
- **Backtest and R&amp;D** — `src/backtest/`, `src/experiments/`, `src/r_and_d/`; subject to `live_gates` **tier** rules.  
- **Tests and CI** — `tests/`, `.github/workflows/` **consume** the codebase as **verification**, not as **live** approval.  
- **Operators and reviewers** — read specs, JSON snapshots, and runbooks; **human** processes remain the **authority** for go-live in this model.  
- **External signoff** — L1–L5 style **pointers** in Master V2 / First-Live **docs** point **out** of repo; this overview does not replicate their content.

## 12. Observability and Auditability Surfaces

- **Strategy and risk telemetry** — described in [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) (e.g. EV-20260128, EV-20260129 entries).  
- **Replay pack verification** — evidence entries and `src/execution/replay_pack/`.  
- **AI telemetry** — evidence entries in `EVIDENCE_INDEX.md`; optional hooks via `src/obs/ai_telemetry.py` (orchestrator import).  
- **Ops doctor and readiness** — workflows such as `ops_doctor_dashboard.yml`, `prbd-live-readiness-scorecard.yml` (names in tree under `.github/workflows/`) as **readiness and CI** tools.  
- **Audit logs in execution** — e.g. `src/execution/audit_log.py`, `src/execution/live/audit.py` (paths present in `src/execution/` tree). **KillSwitch** audit paths per `docs/risk/KILL_SWITCH.md`.

## 13. Authority Boundary Summary

| Surface | Stance in this document |
|--------|-------------------------|
| This spec | **Non-authorizing**. |
| [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) | **Docs-only** trading-logic **manifest**; no order or session permission. |
| [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md), [../EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md) | **Catalog** and **schema** for evidence claims; not approvals. |
| Runbooks and gate indexes | **Procedures and visibility**; not substitute for org signoff. |
| JSON, registries, CI green | **Machine-readable** or **automation** outcomes; not live **authorization** here. |
| AI, LLM, agents, evals | **Advisory**, **CI**, or **research** unless a **separate** controlled path and governance prove otherwise; **this file does not** prove that. |
| `ExecutionMode.PAPER` default vs `LIVE_BLOCKED` and pipeline **live** lock | **Distinct** facts; all must be read with source files, not conflated. |

## 14. Known Ambiguities and Follow-Up Candidates

- **End-to-end production trace** from every deployment entry to a single order id — **unclear from current repository evidence** in one diagram without environment-specific config.  
- **Double Play to live order** — how `evaluate_double_play` and strategy intents join in **all** runtime configurations — would need a **dedicated, environment-scoped** sequence doc if required.  
- **Static “no LLM in hot path”** across **all** imports — manifest states intent; a **line-level** import closure analysis is a **separate** read-only follow-up.  
- **S3 and external store** handoffs — may appear in workflows and runbooks; **per-path** truth requires those files; **unclear** as a single global claim here.  
- **Begriffe:** **SwitchGate** (code), **Double Play** (product semantics), **ExecutionGate** (KillSwitch), **live_gates** (eligibility) vs **G1–G12** in First-Live **docs** — readers should use the **glossaries** in the respective specs to avoid conflation.

**Suggested docs-only follow-up (not part of this file’s deliverable):** a single **pointer table** “tick → config → strategy → **gate** → orchestrator **mode**” with **file references only**, and a **Glossary** row for the gate vocabulary above.

## References (non-exhaustive)

- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)  
- [../../architecture/INTEGRATION_SUMMARY.md](../../architecture/INTEGRATION_SUMMARY.md)  
- [../../architecture/ai_autonomy_layer_map_v1.md](../../architecture/ai_autonomy_layer_map_v1.md)  
- [../../governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md](../../governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md)  
- [../EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md)  
- [../EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md)  
- [../../risk/KILL_SWITCH.md](../../risk/KILL_SWITCH.md)  
- [../../ai/AI_TOOLCHAIN_RFC_V1.md](../../ai/AI_TOOLCHAIN_RFC_V1.md)
