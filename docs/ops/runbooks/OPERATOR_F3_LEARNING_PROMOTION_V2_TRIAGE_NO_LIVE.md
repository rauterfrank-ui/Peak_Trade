---
title: Operator F3 Learning Promotion v2 Triage — NO-LIVE
status: DRAFT
last_updated: 2026-04-24
scope: docs-only F3 triage note
repo_ref: main@7b0a087fac5f
---

# Operator F3 Learning Promotion v2 Triage — NO-LIVE

## 1. Purpose

This runbook gives operators a compact triage surface for the F3 / Learning Promotion v2 area.

It translates the v2 enhancement list into reviewable planning categories without changing runtime behavior, promotion gates, evidence flows, or live readiness.

Primary architecture reference:

- [LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](../../LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)

Roadmap references:

- [PEAK_TRADE_V1_KNOWN_LIMITATIONS.md — §2: Live-Trading & order execution](../../PEAK_TRADE_V1_KNOWN_LIMITATIONS.md#2-live-trading--order-execution)
- [SAFETY_POLICY_TESTNET_AND_LIVE.md](../../SAFETY_POLICY_TESTNET_AND_LIVE.md)
- [CURRENT_FOCUS.md](../roadmap/CURRENT_FOCUS.md)
- [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md)
- [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](RUNBOOK_CHAT_LED_OPEN_FEATURES.md)

## 2. Non-authorization

This runbook does not authorize:

- live trading
- broker or exchange orders
- paper state mutation
- shadow state mutation
- evidence mutation
- automatic promotion
- auto-apply behavior
- production readiness claims
- gate changes
- Master-V2 expansion
- required-checks hygiene changes

Any F3 implementation must start from a separate approved single-topic slice.

## 3. Triage interpretation

Terms such as `Learning`, `Promotion`, `v2`, `Auto-Apply`, `Production-Ready`, `Gate`, or `Readiness` are interpreted here as **planning labels only**.

They do not imply runtime enablement, live authorization, automatic model adoption, automatic strategy promotion, or evidence mutation.

## 4. F3 v2 enhancement triage table

| Enhancement area | Operator interpretation | Safe next action |
|---|---|---|
| Learning loop improvements | Planning surface for improving how learning outputs are reviewed. | Read-only inventory |
| Promotion logic | Candidate decision-support vocabulary, not automatic promotion. | Docs/spec clarification |
| Auto-apply language | High-risk wording; treat as non-authorized until separately approved. | Boundary note before code |
| Production-ready wording | Review label only, not live readiness. | Define evidence expectations |
| Gate/readiness language | Planning category; no gate changes here. | Map existing gates read-only |
| Evidence interactions | Must not write or mutate evidence in this triage slice. | Inventory only |

## 5. Operator checklist before any F3 implementation

Before creating an F3 implementation slice, confirm:

- Is the work docs-only, test-only, or runtime-changing?
- Could it alter promotion behavior, model selection, strategy selection, or operator decisions?
- Could it write or mutate evidence, registry, Paper, or Shadow state?
- Does it change any gate, readiness label, or release decision path?
- Does it introduce automatic behavior where only review support is intended?
- Is the proposed slice single-topic and independently reviewable?

If any answer is uncertain, keep the work as read-only analysis or docs-only boundary clarification.

## 6. Recommended first F3 implementation shape

The first non-triage F3 slice should be one of:

1. A docs-only contract for a single v2 enhancement area.
2. A read-only inventory of existing learning/promotion artifacts.
3. A test-only assertion around an existing non-mutating surface.

Do not combine multiple v2 enhancement areas in one PR.

## 7. Explicit non-scope

Do not use this runbook to:

- change `src/`
- change runtime configs
- change scripts
- change tests
- write to `out/`
- generate evidence artifacts
- modify workflows
- change Master-V2 semantics
- alter required checks
- claim live or production readiness

## 8. Change discipline

This runbook is a triage note. It should remain conservative.

Future updates should either refine the triage vocabulary or point to a separately approved F3 implementation slice.
