---
title: "Master V2 Double Play Strategy Suitability Projection Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-26"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0"
---

# Master V2 Double Play Strategy Suitability Projection Contract v0

## 1. Purpose

This contract defines how strategy metadata, names, registry entries, config hints, Instrument Intelligence, and Arithmetic Sequence Survival Envelope status may be **projected** into Master V2 / Double Play **strategy suitability** context.

The purpose is to prepare a future pure `double_play_suitability.py` model (name illustrative) without allowing names, registry labels, AI summaries, dashboards, or configs to become trading authority.

**Suitability projection** is a classification and side-compatibility layer only. It is not a trading signal, not Master V2 approval, and not Testnet or Live authorization.

## 2. Non-authority note

This file is docs-only and non-authorizing. It does not:

- implement a strategy router, strategy registry, suitability model, State-Switch runtime, Arithmetic Kernel, Sequence Survival Layer, dashboard, or exchange adapter
- grant order placement, execution, or session permission
- authorize Testnet, Live, or bounded real-money operation
- grant Double Play selection authority, Master V2 handoff acceptance, or operator signoff
- assert PRE_LIVE completion, First-Live readiness, or production readiness
- replace Risk/Safety, governance, evidence authorities, or the canonical [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)

## 3. Scope

**In scope:**

- vocabulary for projecting existing strategy surfaces into suitability and side-compatibility metadata
- Long/Bull and Short/Bear projection rules (as candidates only)
- both-side, neutral, disabled, and unknown handling
- Instrument Intelligence and AI context as inputs (with strict limits)
- Arithmetic Sequence Survival Envelope as blocker or gate on consumption
- Double Play consumption boundary, dashboard display boundary, and fail-closed semantics

**Out of scope:**

- strategy activation, order routing, backtests, or execution sessions
- mutating `out/`, Paper, Shadow, Evidence, S3, or registry artifacts at runtime by this document alone

## 4. Current repo baseline

At authoring time, the read-only strategy suitability audit found at least:

- strategy implementations under `src&#47;strategies&#47;**`
- registry and name surfaces such as `src/strategies/registry.py` and `src/strategies/__init__.py`
- config surfaces under `config&#47;*.toml`
- Double Play pure models: `src/trading/master_v2/double_play_state.py`, `src/trading/master_v2/double_play_survival.py`
- ops Double Play and switch-gate surfaces that are not the manifest state machine
- ECM/Armstrong name-surface non-authority documentation

No dedicated `double_play_suitability` implementation is required or implied by this contract’s existence.

## 5. Strategy source surfaces

Future suitability projection may inspect or consume metadata derived from (non-exhaustive):

- strategy `id` / `key` (opaque identifier, not a permission)
- strategy family or archetype labels (catalog only unless elevated elsewhere)
- strategy implementation path (discovery and provenance only)
- declared risk mode where present (e.g. long-only/short-only in strategy code) as a hint, not as Double Play authority
- declared signal direction, regime targets, mean-reversion vs trend wording as metadata only
- tests or fixtures that describe intended behavior as supporting context only

These inputs are metadata and context only. The projection model (when implemented) must not instantiate strategies, run strategies, fetch data, call exchanges, run backtests, or start sessions from this layer alone.

Strategy registry entries and names are metadata only. Strategy implementations under `src&#47;strategies&#47;**` are not automatically Double Play eligible by existence alone. Config labels and registry labels do not authorize trading.

## 6. Strategy registry / name-surface boundary

Registry keys, TOML sections, ECM/Armstrong names, dashboard labels, and free-text descriptions are not authority.

They do not prove (non-exhaustive):

- strategy suitability for a side
- futures readiness
- Long/Bull or Short/Bear eligibility as operational permission
- Testnet or Live readiness, or Master V2 approval

ECM, Armstrong, and other name surfaces remain non-authority per [STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md](STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md) and [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md). Any future model must preserve this boundary explicitly.

Suitability projection converts metadata and context into side-compatibility status and classes only — not into order or activation authority.

## 7. Suitability projection model

A future pure projection model should map strategy metadata and candidate context into a suitability classification and compatibility record (shape illustrative; not binding code).

**Allowed suitability classes:**

| Suitability class | Meaning |
| --- | --- |
| `long_only_candidate` | Candidate for the Long/Bull side pool only (non-authority). |
| `short_only_candidate` | Candidate for the Short/Bear side pool only. |
| `both_sides_candidate` | Candidate for both sides, with explicit evidence (e.g. symmetric behavior or separate long/short behavior documented). |
| `neutral_range_candidate` | Candidate for range, neutral, or mean-reversion context; not forced into directional pools. |
| `disabled_for_candidate` | Explicit blockers for the candidate class. |
| `unknown_suitability` | Insufficient evidence; fail closed (see section 15). |

Illustrative projection output should include (non-exhaustive):

- strategy id
- strategy family (if known)
- suitability class
- side compatibility (long / short / both / neither / unknown) as metadata only
- reason codes and human-readable explanations, including AI-assisted text as explanation only
- blockers and missing inputs
- authority flags: this layer must not assert live authorization; any struct should default `live_authorization` (or equivalent) to false unless a separate governed contract authorizes otherwise

Suitability is not a trading signal. Suitability is not Master V2 approval. Suitability is not Testnet or Live authorization. This layer does not grant live authorization.

## 8. Long/Bull suitability

A strategy may be projected into the Long/Bull layer only if the projection has explicit evidence that the strategy is compatible with long or rising-price conditions as modeled by governed metadata and context — not from name alone.

Examples of possible evidence (illustrative, non-binding):

- declared long-only or asymmetric long-biased behavior in implementation or config
- trend-following, breakout long, or similar semantics where documented in metadata
- candidate instrument regime (from Instrument Intelligence) compatible with long exposure per governed rules
- no applicable blocker from the Arithmetic Sequence Survival Envelope for consuming projection for that side

A Long/Bull projection must not be inferred from a positive-sounding name alone. The Long/Bull and Short/Bear layers must remain explicit in Double Play semantics (see the manifest).

## 9. Short/Bear suitability

A strategy may be projected into the Short/Bear layer only with explicit evidence of compatibility with short or falling-price conditions — not from name alone.

Examples of possible evidence (illustrative):

- declared short-only or short-biased behavior
- breakdown, bearish momentum, or short trend semantics where documented
- instrument regime compatible with short exposure per governed rules
- no survival-envelope blocker for that side where applicable

A Short/Bear projection must not be inferred from a negative-sounding name alone.

## 10. Both-side / neutral / disabled / unknown suitability

- `both_sides_candidate` requires explicit evidence that the strategy can operate symmetrically or has separate governed long and short behavior.
- `neutral_range_candidate` must not be forced into Long/Bull or Short/Bear pools without separate governed rules; it labels non-directional or range-bound intent as metadata.
- `disabled_for_candidate` applies when explicit blockers exist (governance, missing models, operator veto, survival envelope, and similar).
- `unknown_suitability` applies when required metadata or context is missing or conflicts remain unresolved.

Rules:

- `unknown_suitability` must fail closed.
- `both_sides_candidate` must not bypass side-specific arithmetic or survival blockers; each side may be blocked independently.
- Disabled strategies must not enter active side pools.
- A strategy can only enter a side pool if suitability is explicit and no applicable blocker exists.

## 11. Inputs from Instrument Intelligence and AI context

Instrument Intelligence may provide non-authoritative context such as: volatility, liquidity, spread, funding, and open interest profiles (where available); freshness and completeness warnings; trend/chop heuristics; risk and missing-data flags.

AI context may summarize or re-order these inputs for operators and readers. AI, selectors, and dashboards must not become strategy activation authority. They must not:

- activate a strategy for trading, arm a side, or place orders
- override suitability blockers, Master V2, Risk/Safety, or the Survival Envelope
- authorize Testnet or Live

AI output is explanation and context only.

## 12. Inputs from Arithmetic Sequence Survival Envelope

Suitability projection must respect [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) and related futures arithmetic and path survival status.

Blockers may include (illustrative; align to the survival contract and future implementations): missing arithmetic fingerprint or side-specific arithmetic, missing funding for perpetuals, missing liquidation model, incomplete venue constraints, low path survival, high early-loss toxicity, low margin buffer, high sequence fragility, high liquidation near-miss, governance breach frequency, or insufficient Double Play pair survival per governed definitions.

A strategy may be “directionally” suitable in narrative terms but still blocked for consuming suitability projection into Double Play pools until survival-envelope requirements are met, or the candidate is explicitly quarantined as `disabled_for_candidate` or `unknown_suitability` with reasons. Arithmetic/sequence survival can block suitability projection consumption — treat it as a strong fail-closed input, not a suggestion.

## 13. Double Play consumption boundary

Double Play may consume suitability projection as metadata only:

```text
strategy_suitability_projection
  -> long_bull_candidate_pool
  -> short_bear_candidate_pool
  -> neutral_candidate_pool
  -> blocked_strategy_pool
  -> unknown_strategy_pool
```

- Pool membership is non-authority: it does not arm sides, open positions, or replace the `double_play_state` state machine.
- A strategy can only enter a side pool if suitability is explicit and no blocker applies (including survival-envelope and governance blockers as applicable).
- The Long/Bull and Short/Bear layers must remain explicit; `both_sides_candidate` does not collapse into a single undifferentiated pool without separate per-side evidence where the manifest requires it.

## 14. Dashboard display boundary

- Dashboards, operator UIs, and selectors may display suitability classes and reasons as read-only context.
- Display must not become strategy activation authority, order routing, or override of Master V2, Risk/Safety, or the Survival Envelope.
- AI-generated labels or summaries are explanatory only; they do not promote a strategy to active side pools.
- “Green” or “eligible” UI must not be read as Testnet or Live permission.

## 15. Fail-closed semantics

- `unknown_suitability` and any missing required input for a governed projection step fail closed (for example, quarantine in `unknown_strategy_pool` only; exact runtime mapping is a future implementation concern).
- Suitability projection does not grant live authorization; any future struct in this layer should keep live and testnet execution permission out of band and default to no authorization.
- If the Arithmetic Sequence Survival Envelope (or its inputs) blocks consumption, suitability projection must not be treated as actionable for that candidate until unblocked per governed rules or explicitly labeled blocked or unknown with reasons.
- Conflicts between metadata sources resolve fail closed to `unknown_suitability` or `disabled_for_candidate` with explicit reasons, not to optimistic classes.

## 16. Validation / future tests

Future tests (out of scope for this docs file) may include (non-exhaustive):

- golden vectors: fixed metadata and envelope snapshot to expected class and blockers
- invariants: projection never implies Master V2 approval or order permission from this layer alone
- registry/name fuzz: positive-sounding names do not promote without non-name evidence
- no test may imply live go or session start from suitability alone

When this file changes, run the repository docs validation scripts (for example `validate_docs_token_policy`, `verify_docs_reference_targets`, and `pt_docs_gates_snapshot`) as used for companion ops specs.

## 17. Implementation staging

1. Docs — this contract and minimal cross-links in a governed slice unless otherwise approved.
2. Pure model (future) — possible I/O-free module colocated with the existing `double_play_state` / `double_play_survival` pure models in `src&#47;trading&#47;master_v2&#47;` (illustrative filename: `double_play_suitability.py`), aligned with [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md).
3. Adapters (future) — read-only metadata projection; no direct exchange calls from suitability.
4. Wiring (future) — only after Master V2 and Double Play governance explicitly allow non-authoritative consumption.

## 18. References

- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) — strategy and registry non-authority; Master V2 boundary.
- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play State-Switch, Long/Bull vs Short/Bear.
- [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) — arithmetic and sequence survival envelope; blockers.
- [STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md](STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0.md) — ECM/Armstrong name surfaces.
- [OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md](OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md) — ops cockpit and dashboard non-authority (read for alignment).
- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md) — Futures Input Snapshot mapping toward instrument intelligence **presence** fields (docs-only; not scanner or Live).
