---
title: C1 Namespace Clarification v1
status: DRAFT
last_updated: 2026-04-24
repo_ref: main@8e29c4f1d87d
scope: docs-only terminology and safety clarification
docs_token: DOCS_TOKEN_C1_NAMESPACE_CLARIFICATION_V1
---

# C1 Namespace Clarification v1

## 1. Purpose

This document clarifies that `C1` is not a single global feature namespace in Peak_Trade.

Different docs and runbooks use `C1` for different historical or local contexts. Those meanings must not be merged into one implementation scope without an explicit operator decision.

This is a docs-only clarification. It does not change runtime behavior, order execution, broker adapters, testnet paths, Paper or Shadow behavior, Evidence, Master V2, Double Play, or gates.

## 2. C1 meanings observed in the repo

| C1 meaning | Safe interpretation | Unsafe interpretation |
|---|---|---|
| Order / live-exchange C1 | A live/order/exchange execution gap or stub area requiring strict NO-LIVE boundaries. | A permission to implement or enable live order execution. |
| TASK_C1 / VaR C1 | A local task label in risk/VaR context. | Equivalent to live/order C1. |
| FINISH_C1 / broker-adapter C1 | A finish-plan or broker-adapter scoped label. | Equivalent to a general execution enablement track. |

## 3. Non-merge rule

Do not merge C1 meanings across docs, runbooks, tests, or code by name alone.

A future C1 follow-up must first state:

- which C1 namespace it touches
- which files define that namespace
- whether the scope is docs-only, test-only, read-only, or runtime-changing
- whether it touches live, testnet, broker, exchange, order, Paper, Shadow, Evidence, Master V2, or Double Play
- which safety and authority contract applies

If the namespace is unclear, classify the item as `Needs deeper audit`.

## 4. ExchangeOrderExecutor naming risk

The C1 I/O and stub inventory identified a naming-risk pattern around `ExchangeOrderExecutor`.

There can be multiple similarly named classes or surfaces with different semantics, including:

- a Paper/stub-style executor surface
- a unified exchange-oriented executor surface

Do not infer authority or implementation status from the class name alone.

A future audit or implementation proposal must identify the exact file path, import path, constructor behavior, and failure mode before making claims about execution readiness.

## 5. NO-LIVE rule

C1 terminology does not grant:

- live trading authority
- broker or exchange order authority
- testnet execution authority
- Paper or Shadow mutation authority
- Evidence mutation authority
- promotion authority
- gate authority
- Master V2 readiness authority
- Double Play decision authority

C1-related work remains blocked from runtime expansion unless explicitly governed.

## 6. Safe next actions

Safe follow-ups are limited to:

1. read-only C1 namespace inventory
2. docs-only link or terminology clarification
3. test-only contract that proves an existing stub fails closed
4. operator-facing NO-LIVE wording
5. explicit Master-V2-compatible scope decision

## 7. Unsafe next actions

Do not:

1. implement live order execution from a C1 label
2. connect a stub executor to broker/exchange calls
3. treat broker-adapter C1 as general live enablement
4. treat VaR TASK_C1 as execution C1
5. add testnet behavior without an explicit NO-LIVE/Testnet contract
6. use C1 as a shortcut around Master V2 / Double Play authority
7. mutate Paper, Shadow, Evidence, or gates from a C1 clarification

## 8. Decision checklist

Before working on any C1 item, answer:

- Which C1 namespace is this?
- What is the source path?
- Is the work docs-only, test-only, read-only, or runtime-changing?
- Does it touch order, broker, exchange, testnet, live, Paper, Shadow, or Evidence?
- Does it affect Master V2 or Double Play?
- Is there a fail-closed behavior?
- Is there a canonical NO-LIVE statement?
- Is the deliverable small and single-topic?

## 9. Recommended follow-up

After this clarification, the next safe action is a read-only classification table that maps C1 references to their namespace.

Do not implement C1 runtime behavior from this document.
