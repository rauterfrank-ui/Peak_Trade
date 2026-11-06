---
title: OPS Cockpit Master V2 Non-Authority Contract v1
status: DRAFT
last_updated: 2026-04-24
repo_ref: main@160085572c30
scope: docs-only safety contract
docs_token: DOCS_TOKEN_OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1
---

# OPS Cockpit Master V2 Non-Authority Contract v1

## 1. Purpose

This contract records the boundary between the OPS Cockpit and Master V2 / Double Play semantics.

The OPS Cockpit is a read-only operator observation and navigation surface. It must not become an independent trading authority, release authority, execution authority, gate authority, or evidence mutation surface.

## 2. Canonical authority references

- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [double_play.md](../runbooks/double_play.md)
- [OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md](OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md)

## 3. Non-authority rule

OPS Cockpit views, cards, banners, tables, API responses, and navigation links are non-authorizing.

They may show status, observations, pointers, coverage, links, missing context, and review hints.

They must not:

- authorize live trading
- authorize broker or exchange orders
- authorize testnet execution
- promote a strategy, portfolio, model, or decision context
- override Master V2 authority semantics
- override Double Play semantics
- modify gates
- mutate Paper state
- mutate Shadow state
- mutate Evidence state
- create release approval
- imply Go/No-Go authority

## 4. Master V2 compatibility labels

Any future OPS Cockpit follow-up touching Master V2, Double Play, readiness, Go/No-Go, live enablement, promotion, veto, or execution language must be classified before implementation:

| Label | Meaning | Allowed in OPS Cockpit? |
|---|---|---|
| `read-only observation` | Displays already-existing status or pointers. | Yes |
| `navigation` | Links to canonical docs, runbooks, reports, or evidence pointers. | Yes |
| `advisory` | Provides non-binding review hints. | Yes, with explicit non-authority wording |
| `partial` | Shows incomplete or candidate state. | Yes, if clearly labeled |
| `veto` | Indicates a block from canonical authority. | Display only; cannot create or clear vetoes |
| `promotion` | Movement toward stronger operational status. | Display only; cannot perform promotion |
| `live-go` | Operational authorization. | No |
| `execution-control` | Starts, stops, arms, or places orders. | No |
| `evidence-mutation` | Creates or updates evidence artifacts. | No |

## 5. Double Play guardrail

Double Play semantics must not be reimplemented inside the OPS Cockpit.

A cockpit follow-up may display a pointer or read-only observation about Double Play only if the source of truth remains outside the cockpit and the UI labels the content as non-authorizing.

## 6. Safe follow-up categories

OPS Cockpit follow-ups are generally safe when they remain within one of these categories:

1. deterministic read-only rendering tests
2. non-authorizing status display
3. pointer or link surfaces
4. missing-context warnings
5. docs-only operator navigation
6. explicit non-authority labels
7. regression tests for existing read-only payload shape

## 7. Unsafe follow-up categories

Do not implement OPS Cockpit follow-ups that:

1. introduce cockpit-side Go/No-Go decisions
2. add cockpit-side live enablement
3. add cockpit-side gate mutation
4. add cockpit-side Paper, Shadow, or Evidence mutation
5. add cockpit-side Double Play control
6. convert advisory observations into authority
7. blur readiness display with execution permission

## 8. Required wording for future M-V2 / Double Play cockpit surfaces

Any future OPS Cockpit view that references Master V2, Double Play, readiness, promotion, veto, execution, or live status must include wording equivalent to:

> This OPS Cockpit view is read-only and non-authorizing. It does not grant live, testnet, paper, shadow, execution, promotion, or evidence authority. Canonical authority remains in the Master V2 decision-authority chain and related runbooks.

## 9. Review checklist

Before implementing an OPS Cockpit follow-up, answer:

- Does this change only display existing information?
- Is the source of truth outside the cockpit?
- Does it avoid writing to Paper, Shadow, Evidence, gates, or runtime state?
- Does it avoid broker, exchange, testnet, or live actions?
- Does it preserve Master V2 and Double Play semantics?
- Is non-authority wording present where needed?
- Is the change testable with deterministic local tests?

If any answer is uncertain, keep the work read-only or docs-only.

## 10. Non-scope

This contract does not implement new cockpit behavior.

It does not change:

- `src&#47;`
- runtime configs
- workflows
- tests
- evidence artifacts
- Paper/Shadow state
- Master V2 semantics
- Double Play semantics
- release gates

## 11. Change discipline

Use this contract as a safety filter before adding OPS Cockpit features.

Future implementation slices should reference this document when they touch Master V2, Double Play, readiness, Go/No-Go, promotion, veto, execution, or live-facing labels.
