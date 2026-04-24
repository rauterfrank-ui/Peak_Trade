---
title: Operator C1 Execution Boundary — NO-LIVE
status: DRAFT
last_updated: 2026-04-24
scope: docs-only operator boundary note
repo_ref: main@bcf445a762aa
---

# Operator C1 Execution Boundary — NO-LIVE

## 1. Purpose

This runbook gives operators a compact boundary note for C1 / execution-facing language.

It separates **dry-run**, **paper**, **testnet**, and **live** meanings so Chat-led, roadmap, and runbook work does not accidentally imply live authorization.

This document is **NO-LIVE** and does not change runtime behavior.

## 2. Non-authorization

This runbook does not authorize:

- live trading
- broker or exchange orders
- testnet order placement
- paper state mutation
- shadow state mutation
- evidence mutation
- gate bypass
- Master-V2 expansion
- required-checks hygiene changes

Any implementation, promotion, or execution step needs its own approved workflow and explicit operator decision.

## 3. Boundary table

| Term | Meaning in this runbook | Allowed by this note? |
|---|---|---|
| Dry-run | Local or simulated command path that does not place orders and does not mutate Paper/Shadow/Evidence state. | Documentation only |
| Paper | Paper-trading mode or paper-like stateful behavior. | Not authorized |
| Shadow | Shadow-observation or shadow-decision behavior. | Not authorized |
| Testnet | Exchange/broker sandbox or testnet order path. | Not authorized |
| Live | Real broker/exchange order path or live enablement. | Not authorized |
| C1 | Execution-facing roadmap area that may discuss order/execution boundaries. | Discussion only |

## 4. Common confusion risks

1. A `dry-run` flag is not a live-readiness claim.
2. A passing smoke test is not a permission to run paper, testnet, or live workflows.
3. A C1 roadmap item can discuss execution boundaries without enabling execution.
4. Testnet language is still execution-facing and remains blocked by this note.
5. Operator documentation can clarify vocabulary without changing gates.

## 5. Operator checklist

Before treating any C1 / execution-facing item as actionable, confirm:

- Is the requested step docs-only, test-only, or runtime-changing?
- Does it create, update, or rely on Paper/Shadow/Evidence state?
- Does it contact a broker, exchange, or testnet endpoint?
- Does it alter gates, safety policy, or enablement state?
- Is there an explicit approved workflow for the requested mode?

If any answer is uncertain, treat the step as **No-Go for execution** and reduce scope to read-only analysis or documentation.

## 6. Related references

- [CURRENT_FOCUS.md](../roadmap/CURRENT_FOCUS.md)
- [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](RUNBOOK_CHAT_LED_OPEN_FEATURES.md)
- [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md)
- [WORKFLOW_FRONTDOOR.md](../../WORKFLOW_FRONTDOOR.md)
- [CLI_CHEATSHEET.md](../../CLI_CHEATSHEET.md)

## 7. Change discipline

Keep this runbook as a boundary note.

Do not use it to:

- promote C1 scope into implementation
- claim readiness for broker, testnet, paper, shadow, or live modes
- modify safety gates
- replace a required operator approval
- write local evidence or runtime artifacts

Future C1 implementation work should begin with a separate read-only inventory and an explicitly approved single-topic slice.
