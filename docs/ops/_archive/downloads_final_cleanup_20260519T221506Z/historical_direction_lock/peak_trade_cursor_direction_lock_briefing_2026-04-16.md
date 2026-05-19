# Peak_Trade — Cursor Direction Lock Briefing

Stand: 2026-04-16
Status: Binding directional briefing for future Cursor work
Mode: Read-only unless explicitly overridden in a later, separate instruction

---

## 1. Non-negotiable direction lock

This briefing is intentionally strict.

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
```

This is the target architecture.

Cursor must **not** silently drift toward any alternative interpretation.

In particular, Cursor must **not** redefine the target as merely:

- regime detection
- strategy switching
- generic execution policy wiring
- generic governance hardening
- generic ops visibility
- generic levelup manifest work
- generic portfolio orchestration

Those may remain supporting elements, but they are **not the core target**.

---

## 2. What this means in plain terms

The intended Peak_Trade core is:

1. A **market selection layer** that preselects candidate futures.
2. A **Doubleplay decision core** that determines LONG / SHORT / FLAT.
3. Two directional specialist lanes:
   - Bull / Long specialist
   - Bear / Short specialist
4. **Strategies embedded inside those directional lanes**, not used as a replacement for Doubleplay.
5. A **Scope / Capital Envelope** that limits how much capital is even allowed into the active trading domain.
6. A strict **Risk / Exposure Cap** layer.
7. Hard **Safety / Kill-Switch / Live Gate** protection.
8. A staged progression toward execution, never a direct implicit jump.

---

## 3. Binding design intent

## 3.1 Universe Selection is mandatory

Cursor must assume that Peak_Trade is not supposed to trade the full universe blindly.

A preselection layer is required.

Likely functional traits:
- top-N style selection
- liquidity filters
- volume / open interest filters
- ranking / scan / promotion logic

Likely repo candidates:
- `scripts&#47;scan_markets.py`
- `run_market_scan.py`
- `src&#47;experiments&#47;topn_promotion.py`
- `config&#47;risk_liquidity_gate_paper.toml`

Cursor must treat this as a first-class architecture block, not as a nice-to-have utility.

---

## 3.2 Doubleplay is the center of the system

Cursor must treat **Doubleplay** as the intended decision center.

Doubleplay means:
- directional evaluation
- Bull vs. Bear specialist logic
- a switch-gate / meta-controller
- final directional state: LONG / SHORT / FLAT

Doubleplay is **not** just:
- a regime label
- a policy if/else
- a generic strategy switch
- a cosmetic naming layer

Likely roadmap evidence:
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence.md`
- `docs&#47;roadmap&#47;PeakTrade_LevelUp_Roadmap_Evidence_20260211_doubleplay_leverage50.md` <!-- pt:ref-target-ignore -->

Cursor must preserve this interpretation unless later evidence clearly proves otherwise.

---

## 3.3 Strategy Embedding must follow Variant B

Current directional preference is explicit:

> **Variant B is preferred.**

Meaning:
- Bull specialist contains / uses long-side strategies
- Bear specialist contains / uses short-side strategies

Strategies are therefore subordinate to the directional specialists.

Cursor must **not** flip the hierarchy and make Doubleplay a thin wrapper around generic strategy switching unless explicitly instructed later.

Allowed interpretation:
- strategies as internal engines of each directional lane

Disallowed interpretation:
- strategy switching replaces Doubleplay

---

## 3.4 Scope / Capital Envelope is a core system block

This is critical.

Cursor must treat capital scope semantics as a **first-class architectural requirement**.

Example target behavior:
- account has 1000 EUR
- system may only be allowed to deploy 300 EUR
- that deployable portion may then be further constrained
- per market, per side, per signal, per trade, per portfolio

This is not a tiny risk parameter.
This is not a footnote.
This is not optional.

It is a distinct system block:

```text
Account Equity
    -> Tradable Scope
        -> Deployable Scope
            -> Per-Market / Per-Side / Per-Signal Allowance
```

Cursor must actively search for this logic or its remnants and must not collapse it into generic risk limits without explicit proof.

---

## 3.5 Risk / Exposure Caps remain downstream

Risk caps are still essential, but they are downstream of Scope.

Examples:
- max notional
- max position
- leverage cap
- max order size
- drawdown cap
- daily / session loss cap
- correlation / portfolio caps

Likely repo candidates:
- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;execution&#47;pipeline.py`

Cursor must not confuse:
- capital envelope
with
- downstream risk caps

They are related, but not identical.

---

## 3.6 Safety / Kill-Switches are hard constraints

Cursor must assume:
- fail-closed
- deny-by-default
- no implicit live enablement
- kill-switch remains authoritative
- stale-data and safety blocks remain valid
- enabled / armed / confirm-token semantics remain hard boundaries

This safety layer is not in conflict with Doubleplay.
It is the protective outer shell around it.

---

## 3.7 Staged Execution Enablement remains mandatory

Cursor must assume:
- research
- backtest
- shadow / paper
- testnet
- live only under explicit gated promotion

Any architectural interpretation that shortcuts this progression is invalid.

---

## 4. What Cursor must NOT do

Until explicitly told otherwise, Cursor must not:

- reinterpret the system as “just regime detection”
- reinterpret the system as “just strategy switching”
- claim the current execution pipeline already fully implements Doubleplay
- claim current risk limits already fully implement Scope / Capital Envelope
- treat LevelUp manifest work as the main business logic
- silently optimize around whatever code is currently most visible
- replace the intended architecture with repo-local convenience

Cursor must not choose the path of least resistance.
Cursor must choose the path of intended architecture.

---

## 5. Current evidence-based working view

Read-only forensics currently suggest:

### Likely still alive in some form
- Universe / market scan / top-N / liquidity gate family
- Risk / Safety / staged release / execution gates

### Likely incomplete or not canonically materialized
- Doubleplay as end-to-end runtime center
- explicit Bull / Bear specialist lanes
- explicit Scope / Capital Envelope semantics
- clean integration path from selection -> doubleplay -> strategy embedding -> scope -> risk -> execution

Therefore Cursor must assume:
- the target architecture is valid
- the current repo may only contain fragments of it
- reconstruction must be faithful to the target, not submissive to current drift

---

## 6. Required interpretation of existing repo families

## 6.1 Selection / crawler family
Likely relevant:
- `scripts&#47;scan_markets.py`
- `run_market_scan.py`
- `src&#47;experiments&#47;topn_promotion.py`
- `config&#47;risk_liquidity_gate_paper.toml`
- `scripts&#47;run_portfolio_robustness.py`

Required interpretation:
These are candidates for the **Universe Selection** block or its descendants.

---

## 6.2 Regime / strategy switching family
Likely relevant:
- `docs&#47;REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28.md`
- `tests&#47;test_regime_integration.py`
- `src&#47;backtest&#47;engine.py`

Required interpretation:
These are useful evidence and possible integration material, but **not automatically the same thing as Doubleplay**.

---

## 6.3 Risk / safety / execution family
Likely relevant:
- `src&#47;live&#47;risk_limits.py`
- `src&#47;live&#47;safety.py`
- `src&#47;live&#47;live_gates.py`
- `src&#47;execution&#47;pipeline.py`
- `docs&#47;risk&#47;KILL_SWITCH_RUNBOOK.md`
- `docs&#47;LIVE_OPERATIONAL_RUNBOOKS.md`

Required interpretation:
These are candidates for:
- Scope remnants
- Risk caps
- Safety shell
- staged execution enablement

But they do not by themselves define the Doubleplay core.

---

## 7. Required working rules for Cursor

## 7.1 Read-only first
All near-term work remains read-only unless a later explicit instruction says otherwise.

## 7.2 Mark evidence quality explicitly
For every claim, Cursor must tag findings as:
- Ist
- Teilweise
- Soll
- Fehlt
- Unklar

## 7.3 No silent concept merging
Cursor must not silently merge:
- Doubleplay
- regime switching
- strategy switching
- scope
- risk caps
- live gates

These concepts must be kept separate unless evidence proves an intentional merge.

## 7.4 No convenience architecture
If the repo currently makes a weaker architecture easier to explain, Cursor must still prioritize the intended target architecture.

---

## 8. Immediate mission for follow-up work

Cursor's near-term mission is **not** to code first.

It is to clarify, with high confidence, the following:

1. What exactly the current selection / scan / top-N family does.
2. Whether remnants of Scope / Capital Envelope semantics still exist.
3. Which current strategy/regime components could support Variant B.
4. Which parts of Doubleplay remain only in roadmap/docs.
5. Where the clean integration boundaries should be drawn.

---

## 9. Output standard for future Cursor reports

Any future Cursor report on this topic must clearly answer:

- Where is Universe Selection today?
- Where is Doubleplay today?
- Where is Strategy Embedding today?
- Where is Scope / Capital Envelope today?
- Where are Risk / Exposure Caps today?
- Where are Safety / Kill-Switches today?
- Where is staged Execution Enablement today?

And for each:
- Ist / Teilweise / Soll / Fehlt / Unklar

If a report does not answer those seven points explicitly, it is incomplete.

---

## 10. Final directional lock

Cursor must treat the following as binding:

> Peak_Trade is to be understood and further clarified around a **Doubleplay-centered futures architecture** with **Universe Selection**, **directional specialist lanes**, **strategy embedding inside those lanes**, a **distinct Scope / Capital Envelope**, downstream **Risk / Exposure Caps**, hard **Safety / Kill-Switches**, and **staged Execution Enablement**.

Any future investigation, reconstruction, or design clarification must stay on that path and not drift into a different system definition without explicit user approval.
