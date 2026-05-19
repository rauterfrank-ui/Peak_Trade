# Peak_Trade — Master Direction Lock & Forensics Briefing v2

Stand: 2026-04-16
Status: Master briefing for Cursor
Mode: Read-only unless explicitly overridden in a later, separate instruction
Purpose: This is the single canonical briefing Cursor should use for the current Peak_Trade clarification work. It consolidates the intended target architecture, the current evidence-based forensics direction, the implementation discipline, the required dataflow and decision-authority analysis, the long-range autonomy goal, and the mandatory naming/boundary rules needed to eliminate ambiguity and interpretation drift.

---

## 1. Binding master instruction

For the current Peak_Trade workstream, Cursor must treat the following as the **only valid target direction**:

```text
Universe Selection
    -> Doubleplay Core
        -> Bull Specialist + Bear Specialist
            -> Strategy Embedding inside each side
                -> Scope / Capital Envelope
                    -> Risk / Exposure Caps
                        -> Safety / Kill-Switches
                            -> staged Execution Enablement
                                -> progressively more autonomous operation
```

This is the intended core architecture.

Cursor must not silently redefine the system as:
- generic regime detection
- generic strategy switching
- generic execution policy wiring
- generic governance hardening
- generic ops visibility
- generic LevelUp manifest work
- generic portfolio orchestration

Those may exist as supporting layers, but they are **not the business core**.

---

## 2. Absolute anti-drift rule

Cursor must understand that this topic is now **direction-locked**.

That means:
- no silent reinterpretation
- no drifting into adjacent concepts because they are easier to explain
- no replacing the intended architecture with whatever is currently most visible in the repo
- no “good enough” approximation that changes the semantics of the intended system

If the repo currently contains drift, fragmentation, overlap, or naming confusion, Cursor must expose that clearly rather than normalizing it.

---

## 3. Mandatory implementation discipline

## 3.1 Reuse and rewire first

This rule is binding.

When clarifying or later implementing the core system, Cursor must **not** build parallel new systems if equivalent, near-equivalent, or reusable building blocks already exist in the repo.

Instead, Cursor must:

1. search for existing building blocks first
2. determine whether they can be reused as-is
3. determine whether they can be minimally adapted
4. determine whether they can be cleanly rewired into the intended architecture
5. only propose genuinely new components where the capability is truly missing

Required bias:
- **reuse over invention**
- **rewire over parallel rebuild**
- **integration over duplication**
- **minimal additive slices over broad replacement**

Disallowed behavior:
- inventing a second competing pipeline when one already exists
- adding a new subsystem beside an overlapping old subsystem
- building “clean room” replacements before mapping reusable repo assets
- keeping ambiguous old and new paths alive without a clear canonical winner

---

## 3.2 No parallel architecture

Cursor must not produce a state where:
- old selection logic remains
- new selection logic is added beside it
- old strategy/regime path remains
- new doubleplay path is added beside it
- old risk/safety path remains
- new risk/safety path is added beside it
- and no single canonical path exists

The goal is always:

> **one canonical architecture**

even if the migration toward it happens incrementally.

---

## 4. Intended core system

## 4.1 Universe Selection / Market Selection

### Purpose
Select a limited candidate set of tradeable futures before directional decisioning begins.

### Expected functional traits
- top-N selection
- liquidity filters
- volume filters
- open interest filters
- ranking / scan / promotion logic
- market quality filters
- data quality filters
- candidate narrowing before Doubleplay

### Likely repo candidates
- `scripts&#47;scan_markets.py`
- `run_market_scan.py`
- `src&#47;experiments&#47;topn_promotion.py`
- `config&#47;risk_liquidity_gate_paper.toml`
- `scripts&#47;run_portfolio_robustness.py`

### Binding interpretation
Universe Selection is a first-class architecture block, not a utility and not an optional pre-step.

---

## 4.2 Doubleplay Core

### Purpose
Doubleplay is the directional decision center.

It determines:
- LONG
- SHORT
- FLAT

### Required structure
Doubleplay must be understood as:
- Bull / Long specialist lane
- Bear / Short specialist lane
- a Switch-Gate / Meta-Controller above them

### Expected mechanics
- directional evaluation
- conflict handling
- hysteresis
- cooldown
- min-hold
- sideways / no-trade band
- fail-closed behavior

### Likely roadmap evidence
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence.md`
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence_20260211_doubleplay_leverage50.md` <!-- pt:ref-target-ignore -->

### Binding interpretation
Doubleplay is not merely:
- a regime label
- a strategy switch
- a generic policy if/else
- a naming variation of existing strategy switching

---

## 4.3 Strategy Embedding

### Current preferred direction
This is explicit and binding for the current clarification work:

> **Variant B is preferred.**

Meaning:
- Bull specialist contains / uses long-side strategies
- Bear specialist contains / uses short-side strategies

### Binding interpretation
Strategies are embedded **inside** the directional lanes.

Allowed interpretation:
- strategies as internal engines / evidence providers / submodels of each directional specialist

Disallowed interpretation:
- strategy switching replaces Doubleplay
- Doubleplay becomes a thin wrapper around generic strategy switching

### Likely relevant repo families
- `docs&#47;REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28.md`
- `tests&#47;test_regime_integration.py`
- `src&#47;backtest&#47;engine.py`
- `src&#47;execution&#47;pipeline.py`

These may contain useful material, but they are not automatically the same thing as the intended Doubleplay core.

---

## 4.4 Scope / Capital Envelope

### Purpose
Only a deliberately limited portion of account capital may become actively deployable.

### Example intent
If the account has 1000 EUR, the system may only be allowed to deploy 300 EUR.

### Required semantics
The architecture must distinguish:

```text
Account Equity / Wallet Balance
    -> Tradable Scope
        -> Deployable Scope
            -> Per-Market / Per-Side / Per-Signal allowance
```

### Binding interpretation
This is a first-class core system block.

It is not:
- a tiny parameter
- an afterthought
- merely one field in risk limits

### Likely relevant repo candidates
- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `tests&#47;test_environment_and_safety.py`

### Important caution
Cursor must not collapse Scope / Capital Envelope into downstream generic risk caps unless evidence explicitly proves they are already the same.

---

## 4.5 Risk / Exposure Caps

### Purpose
Even within deployable capital, further hard caps apply.

### Typical examples
- max notional
- max position
- leverage cap
- max order size
- drawdown cap
- daily / session loss cap
- correlation cap
- per-market cap
- per-side cap
- portfolio cap

### Likely repo candidates
- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;execution&#47;pipeline.py`

### Binding interpretation
Risk / Exposure Caps remain essential, but are conceptually downstream of Scope / Capital Envelope.

---

## 4.6 Safety / Kill-Switches

### Purpose
Fail-closed protection shell around the capital path.

### Expected properties
- enabled
- armed
- confirm token
- kill switch
- stale data blocking
- deny-by-default
- no hidden override path
- no implicit live enablement

### Likely repo candidates
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;live&#47;risk_limits.py`
- `docs&#47;risk&#47;KILL_SWITCH_RUNBOOK.md`
- `docs&#47;LIVE_OPERATIONAL_RUNBOOKS.md`

### Binding interpretation
This layer is authoritative and remains non-negotiable.

---

## 4.7 Staged Execution Enablement

### Purpose
No direct uncontrolled jump to live execution.

### Expected progression
- research
- backtest
- shadow / paper
- testnet
- live only via explicit gated promotion

### Likely repo candidates
- `src&#47;execution&#47;pipeline.py`
- `docs&#47;LIVE_OPERATIONAL_RUNBOOKS.md`
- `tests&#47;test_live_shadow_session.py`
- `tests&#47;test_live_session_registry.py`
- `src&#47;webui&#47;ops_cockpit.py`

### Binding interpretation
Any interpretation that bypasses staged progression is invalid.

---

## 5. Long-range system goal

This must be explicit.

Beyond the core architecture, the broader intended direction of Peak_Trade is:

> a self-learning, self-decision-capable, fully autonomous day trading system for trading futures

This is the long-range target.

### Important nuance
This does **not** mean:
- unsafe autonomy now
- live authority without evidence
- uncontrolled online learning on the capital path
- bypassing governance or deterministic risk

It means the system should evolve toward:
- progressively more autonomous decision support
- progressively more autonomous decision formation
- progressively more autonomous orchestration
- under strict evidence, gating, control, auditability, and operator readability

---

## 6. Learning / AI / autonomy layer must be investigated

Cursor must explicitly investigate and map:
- learning triggers
- training loops
- offline learning
- online learning
- knowledge base
- AI-layer orchestration
- model orchestration
- approval logic for updated models
- decision authority for model changes
- feedback loops from outcomes to learning

The user states these themes were already worked out in the past.

Therefore Cursor must assume:
- relevant material may still exist in docs, code, tests, scripts, config, or runbooks
- those capabilities may be fully implemented, partially implemented, unimplemented, fragmented, drifted, or wrongly wired

Cursor must not ignore this layer just because the safety shell is easier to find.

---

## 7. Required dataflow analysis

Cursor must reconstruct an explicit **dataflow map**.

This is mandatory.

For the intended system, Cursor must identify:
1. where data enters the system
2. what form the data takes
3. which layer receives it first
4. how it is transformed
5. which component forwards what to whom
6. which component evaluates what
7. which component decides what
8. which component may approve / deny / block
9. what outputs leave each layer
10. what telemetry / evidence / audit outputs are produced

Cursor must not stop at keyword overlap.
Cursor must produce a real flow map.

---

## 8. Required decision-authority analysis

Cursor must reconstruct an explicit **decision authority map**.

For each major stage, Cursor must answer:
- who receives the input
- who computes a signal / score / recommendation
- who aggregates competing signals
- who decides LONG / SHORT / FLAT
- who decides market eligibility
- who decides deployable capital
- who decides per-market / per-side allowance
- who decides whether risk caps are exceeded
- who decides whether live gates remain blocked
- who decides whether training / learning loops may run
- who is advisory only
- who is authoritative
- who is veto-capable
- who is fail-closed

If the repo does not currently make this clear, Cursor must mark that explicitly as:
- unclear
- fragmented
- wrongly wired
- missing

---

## 9. Required implementation-state inventory

Before giving any implementation instruction, Cursor must produce an evidence-based inventory of what is:

- already implemented
- partially implemented
- not implemented
- implemented but wrongly wired
- implemented but semantically drifted
- implemented under a different name
- only documented as Soll
- unclear / unverifiable from current repo evidence

This inventory is required for at least:
1. Universe Selection
2. Doubleplay Core
3. Bull Specialist
4. Bear Specialist
5. Strategy Embedding
6. Scope / Capital Envelope
7. Risk / Exposure Caps
8. Safety / Kill-Switches
9. staged Execution Enablement
10. learning triggers
11. training loops
12. offline learning
13. online learning
14. knowledge base
15. AI-layer orchestration
16. model orchestration
17. decision authority / veto structure
18. evidence / audit trail for model and trading decisions

---

## 10. Evidence / acceptance / exit criteria

This section is mandatory.

Cursor must not stop at “interesting architecture” or “likely direction.”
Every major clarification step must define:

- what was investigated
- what evidence was used
- what was confirmed
- what remains unconfirmed
- what would count as sufficient evidence for closure
- what exit criterion would justify moving to the next slice

### Minimum expectation
For each major target block, Cursor must aim to provide:
- evidence sources used
- explicit confidence level
- unresolved questions
- what would close the gap

### No unsupported closure
Cursor must not declare a block “understood” or “ready” without explicit supporting evidence.

---

## 11. Failure taxonomy / safe fallbacks / rollback semantics

Cursor must treat failure behavior as first-class architecture.

For every major block, Cursor must clarify:
- what can fail
- how that failure is named
- who detects it
- who blocks downstream action
- what the safe fallback is
- what fail-closed means in that context
- whether rollback or safe retreat is required

### Required bias
- no undefined failure states
- no implicit fallback logic
- no silent degradation at capital-path boundaries

### Minimum output
A future report must explicitly show, per relevant layer:
- likely failure classes
- blocking/veto point
- safe fallback
- operator-visible consequence

---

## 12. Autonomy boundary contract

This is binding.

Even though the long-range target is a self-learning, self-decision-capable, fully autonomous futures system, Cursor must assume that the following remain **non-autonomous unless explicitly proven and separately approved**:

- final execution authority on live capital
- risk-limit override
- kill-switch override
- hidden config changes affecting capital path
- uncontrolled online learning on the capital path
- unreviewed model-binding changes
- unreviewed policy-binding changes

### Required interpretation
Autonomy may expand only when:
- evidence exists
- controls exist
- review gates exist
- failure handling exists
- authority boundaries are explicit

Cursor must treat this as a hard contract, not as a soft aspiration.

---

## 13. Canonical change governance

Before any implementation phase begins, Cursor must respect the following change-governance rules:

- read-only inventory first
- one clearly bounded topic per slice / PR
- no mixed PRs
- no broad rewrite without prior mapping
- no reopening stabilized blocks without explicit reason
- no mutation of Paper / Shadow / Evidence data
- no implicit runtime authority expansion
- explicit closeout / handoff discipline after each slice

### Required implication
The core recovery effort must happen as a sequence of:
- evidence-first
- reviewable
- tightly scoped
- non-overlapping
- clearly named
changes

---

## 14. Canonical entry points / source hierarchy

To reduce drift, Cursor must prefer the following search order when investigating this topic:

### Strategic entry points
- roadmap / architecture docs
- AI / governance / policy docs
- risk / execution / observability runbooks
- prior reviews / handoffs / closeouts

### Operational entry points
- `docs&#47;execution&#47;`
- `docs&#47;risk&#47;`
- `docs&#47;ops&#47;`
- `src&#47;`
- `tests&#47;`
- `scripts&#47;`
- `config&#47;`

### Required behavior
Cursor must not overfit to whichever file has the loudest keyword density.
Primary sources, implementation touchpoints, tests, configs, and runbooks must be balanced deliberately.

---

## 15. Canonical vocabulary / term registry requirement

This is now mandatory.

Before implementation guidance, Cursor must construct or refine a **canonical term registry** for the topic.

At minimum, Cursor must explicitly distinguish:
- Universe Selection
- Crawler / Scan / Selection
- Doubleplay Core
- Bull Specialist
- Bear Specialist
- Switch-Gate
- Scope / Capital Envelope
- Risk / Exposure Caps
- Safety / Kill-Switches
- Execution Enablement
- Learning Trigger
- Training Loop
- Knowledge Base
- AI Orchestrator
- Advisory
- Authoritative
- Veto
- Fail-Closed

### Purpose
The repo must stop encouraging semantic confusion.

### Required output
Future reports must show:
- canonical term
- current repo aliases / near-synonyms
- confusion risk
- preferred distinction

---

## 16. State machine / promotion contract

Staged execution enablement must be analyzed not only as a list of environments, but as a **state machine**.

For each relevant state, Cursor must identify:
- state name
- entry condition
- exit condition
- promotion requirement
- blocking condition
- evidence required
- authority required for promotion

Example states may include:
- research
- backtest
- shadow / paper
- testnet
- live-gated
- live-authorized

### Required interpretation
Promotion is not merely a label change.
Promotion is a controlled transition with evidence and authority.

---

## 17. Model / policy / strategy change classification

Before implementation work, Cursor must classify change types.

At minimum, changes should be separated into categories like:
- docs-only
- mapping-only
- read-model-only
- runtime-adjacent
- risk-core
- policy-core
- strategy-core
- model-binding
- blocked without separate governance package

### Purpose
Not all changes are equally safe.
Cursor must not treat all architecture work as one homogeneous category.

---

## 18. Model/data provenance and replayability

This is mandatory for a future autonomous system.

Cursor must investigate and later preserve:
- which data inputs produced which intermediate signals
- which model / strategy / policy version was active
- which capital envelope / risk state applied
- which decision was made
- which evidence / telemetry / registry artifacts were written
- how a decision can later be replayed or reconstructed

### Required interpretation
Any future self-learning or self-decision-capable system must remain reproducible and auditable.

---

## 19. Mandatory anti-ambiguity / anti-assumption rules

This is now a first-class requirement.

The repo must not continue to encourage name confusion, semantic overlap, or interpretation risk.

Cursor must explicitly identify:
- ambiguous names
- overloaded terms
- semantically overlapping modules
- similar concepts with different names
- different concepts with similar names
- documentation names that no longer match runtime names
- competing “almost the same” paths
- areas where future agents could falsely equate one subsystem with another

### Required naming and boundary principle
For the intended future canonical system, every major block must be:
- clearly named
- clearly bounded
- clearly owned
- clearly distinguished from adjacent layers
- hard to misinterpret

### Examples of confusion that must be eliminated
Cursor must treat the following as dangerous ambiguity if found:
- Doubleplay vs regime switching
- Scope / Capital Envelope vs risk limits
- Universe Selection vs generic market scan utilities
- advisory AI vs authoritative decision logic
- learning loops vs runtime decision loops
- model orchestration vs strategy selection
- LevelUp as business logic vs LevelUp as delivery method / manifest work
- safety gates vs strategic switch-gate
- operator status / ops read models vs decision authority

### Required output
Cursor must produce a dedicated section:

> **Ambiguity / Confusion / Interpretation Risk Map**

That section must list:
- confusing names
- confusing boundaries
- confusion risk
- recommended canonical distinction
- whether the issue is doc-only, code-only, test-only, or cross-cutting

---

## 20. Required output structure for future Cursor reports

Any serious follow-up report on this topic must contain:

### A. Executive Summary

### B. Canonical target architecture
Explicitly restate:
- Universe Selection
- Doubleplay
- Bull/Bear specialists
- Strategy Embedding
- Scope / Capital Envelope
- Risk / Exposure Caps
- Safety / Kill-Switches
- staged Execution Enablement
- long-range autonomy target

### C. Reuse-over-invention map
For each target block:
- what existing repo assets may be reused
- what may be rewired
- what may need only minimal adaptation
- what is truly missing

### D. Dataflow map
Show:
- inputs
- transformations
- forwarding paths
- outputs
- telemetry / evidence outputs

### E. Decision authority map
Show:
- advisory components
- aggregators
- authoritative decision points
- veto-capable layers
- fail-closed layers

### F. Current implementation inventory
For each target block:
- Ist / Teilweise / Soll / Fehlt / Unklar / falsch verdrahtet

### G. Learning / autonomy inventory
For:
- learning triggers
- training loops
- offline/online learning
- knowledge base
- AI orchestration
- autonomous decision readiness

### H. Ambiguity / confusion / interpretation risk map
For:
- names
- boundaries
- overlapping semantics
- likely false assumptions
- canonical distinction needed

### I. Evidence / acceptance / exit criteria
For:
- what is confirmed
- what is unconfirmed
- confidence level
- closure criteria

### J. Failure taxonomy / safe fallbacks / rollback semantics

### K. State machine / promotion contract

### L. Change classification
Docs-only / mapping-only / runtime-adjacent / risk-core / policy-core / blocked etc.

### M. Model/data provenance and replayability

### N. Gaps / drift / wrong wiring
What is:
- missing
- duplicated
- drifted
- wrongly wired
- still recoverable via rewiring

### O. Forbidden assumptions before coding
Explicitly state what must **not** be assumed.

If a report does not contain these sections, it is incomplete.

---

## 21. Current evidence-based working view

Read-only forensics currently suggest:

### Likely still alive in some form
- Universe / market scan / top-N / liquidity gate family
- Risk / Safety / staged execution shell

### Likely incomplete or not canonically materialized
- Doubleplay as the runtime center
- explicit Bull/Bear specialist lanes
- explicit Scope / Capital Envelope semantics
- clean end-to-end integration:
  selection -> doubleplay -> strategy embedding -> scope -> risk -> execution

### Unknown but mandatory to investigate further
- learning triggers
- training loop wiring
- knowledge base integration
- offline vs online learning separation
- AI-layer orchestration and model routing
- authority boundaries for self-learning and autonomous decisioning

---

## 22. Repo families likely relevant

### 22.1 Selection / crawler family
- `scripts&#47;scan_markets.py`
- `run_market_scan.py`
- `src&#47;experiments&#47;topn_promotion.py`
- `config&#47;risk_liquidity_gate_paper.toml`
- `scripts&#47;run_portfolio_robustness.py`

### 22.2 Doubleplay / roadmap family
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence.md`
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence_20260211_doubleplay_leverage50.md` <!-- pt:ref-target-ignore -->

### 22.3 Regime / strategy switching family
- `docs&#47;REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28.md`
- `tests&#47;test_regime_integration.py`
- `src&#47;backtest&#47;engine.py`

### 22.4 Risk / safety / execution family
- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;execution&#47;pipeline.py`
- `docs&#47;risk&#47;KILL_SWITCH_RUNBOOK.md`
- `docs&#47;LIVE_OPERATIONAL_RUNBOOKS.md`
- `tests&#47;test_environment_and_safety.py`
- `tests&#47;test_live_shadow_session.py`
- `tests&#47;test_live_session_registry.py`
- `src&#47;webui&#47;ops_cockpit.py`

### 22.5 Learning / AI / orchestration themes to search next
Cursor must search for and map repo material related to:
- learning triggers
- training loops
- model updates
- offline retraining
- online adaptation
- knowledge base
- AI-layer orchestration
- orchestration agents
- evidence pack / registry / evaluation loops
- self-learning guardrails

---

## 23. What Cursor must NOT do

Until explicitly told otherwise, Cursor must not:
- silently redefine the target system
- code first and investigate later
- create new parallel subsystems when rewiring is possible
- equate current visible code with the intended architecture without proof
- equate regime switching with Doubleplay without proof
- equate risk limits with full Scope / Capital Envelope without proof
- ignore the learning / autonomy layer
- ignore dataflow and decision-authority mapping
- ignore naming ambiguity / interpretation risk
- ignore evidence / acceptance / failure semantics
- give implementation instructions before the implementation-state inventory exists

---

## 24. Final binding instruction

Cursor must treat the following as binding:

> Peak_Trade is to be clarified and eventually evolved toward a Doubleplay-centered futures architecture with Universe Selection, directional specialist lanes, Strategy Embedding inside those lanes, a distinct Scope / Capital Envelope, downstream Risk / Exposure Caps, hard Safety / Kill-Switches, staged Execution Enablement, and a longer-term path toward a self-learning, self-decision-capable, fully autonomous day trading system for futures.

Before any credible implementation guidance is written, Cursor must first establish:
- what can be reused
- what can be rewired
- what data flows where
- who decides what
- what already exists
- what is partial
- what is missing
- what is wrongly wired
- what is ambiguously named
- what is at risk of future misinterpretation
- what belongs to learning/autonomy but is currently unclear
- what evidence would justify closure
- what failure modes and safe fallbacks exist
- what promotion/state transitions are valid
- what provenance/replay guarantees are required
