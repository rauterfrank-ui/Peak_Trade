# Evidence Surface Reuse-Before-New Guardrail V0

Status: DRAFT / REVIEW GUARDRAIL  
Last updated: 2026-04-28  
Scope: Evidence, readiness, map, index, handoff, package, pointer, and operator-review surfaces  
Authority: Non-authorizing repository review guardrail

## 1. Purpose

This guardrail prevents parallel evidence, readiness, map, index, handoff, package, and pointer surfaces from being created without first checking whether an existing surface can be reused, rewired, extended, or consolidated.

The default posture is:

> Reuse or rewire existing surfaces before creating a new one.

A new surface is acceptable only when the existing surfaces cannot safely express the required read-only view, contract, or handoff semantics.

## 2. Non-Goals

This guardrail does not:

- authorize Live trading,
- authorize Paper/Testnet promotion,
- close GLB-018,
- mutate registries,
- mutate `out/ops`,
- certify evidence,
- change Master V2 / Double Play logic,
- change strategy logic,
- change Risk/KillSwitch logic,
- change Execution/Live Gates,
- grant dashboard authority,
- grant AI authority.

## 3. Affected Surface Types

Before adding or materially changing any of the following, reviewers should perform the reuse-before-new check:

| Surface family | Examples |
|---|---|
| Evidence surfaces | evidence index, evidence packet, evidence bundle, evidence pointer |
| Readiness surfaces | readiness map, readiness status, readiness summary |
| Gap surfaces | gap map, blocker map, missing-evidence matrix |
| Handoff surfaces | operator handoff, external handoff, decision packet |
| Package surfaces | package index, deliverable manifest, submission bundle |
| Pointer surfaces | registry pointer, artifact pointer, session-scoped pointer |
| CLI read models | additive read-only JSON reports that expose one of the above |
| Tests/contracts | tests that define a new evidence/readiness/handoff contract |

## 4. Required Reuse-Before-New Questions

Before creating a new surface, answer these questions in the PR body, design note, or commit-local implementation note:

1. What existing evidence/readiness/map/index/handoff/package/pointer surfaces already exist?
2. Which existing surface is the closest canonical owner?
3. Can the new need be handled by:
   - adding a pointer,
   - adding a section,
   - extending a read-only contract,
   - adding a view over existing data,
   - linking to an existing index,
   - or documenting interpretation without adding a parallel surface?
4. Why is a new surface necessary, if one is proposed?
5. What duplicate-risk does the new surface introduce?
6. How will the new surface avoid becoming a competing source of truth?
7. What is the maximum authority claim of the surface?
8. Which surfaces remain canonical after this change?

## 5. Default Decision Rules

### 5.1 Prefer reuse

If an existing canonical surface can express the information with a bounded extension, reuse it.

### 5.2 Prefer read-only views over copied truth

If a new CLI/report is needed, it should read or derive from existing sources rather than copy status manually.

### 5.3 Prefer pointers over duplication

If the same evidence is needed in multiple places, link or point to the original artifact/index instead of duplicating the content.

### 5.4 Prefer one canonical owner

Each evidence or readiness concept should have one canonical owner and any number of non-authorizing pointers.

### 5.5 New surfaces must declare their relationship

A new surface must explicitly state whether it is:

- canonical owner,
- derived view,
- pointer/index,
- operator handoff,
- temporary `/tmp` scratch artifact,
- test-only contract,
- or non-authorizing documentation.

### 5.6 Temporary `/tmp` artifacts are not canonical

Temporary `/tmp` inventories, scans, candidate maps, and handoffs may help review, but they do not become canonical repo surfaces unless consciously promoted through a docs-only or read-only-contract PR.

## 6. Required Header for New Surfaces

New evidence/readiness/map/index/handoff/package/pointer docs should include a short relationship block:

```text
Surface relationship:
- surface_type: <canonical_owner|derived_view|pointer|handoff|temporary_scratch|test_contract|read_only_report>
- canonical_owner: <path or NONE>
- derives_from: <paths or NONE>
- supersedes: <paths or NONE>
- duplicate_risk: <LOW|MEDIUM|HIGH>
- authority: non_authorizing
```
