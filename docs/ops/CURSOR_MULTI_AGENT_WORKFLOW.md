# Cursor Multi-Agent Workflow

Purpose: Canonical workflow for running multi-agent work in Peak_Trade using Cursor, with clear operator controls and a deterministic handoff to git/PR steps.

## Entry Point
- Frontdoor runbook: `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md`

## Standard Agent Roles
- A1: Implementer (code changes, tests)
- A2: Reviewer (risk, correctness, CI gates)
- A3: Docs/Ops (runbooks, navigation, operator UX)

## Execution Protocol
1. Define scope and constraints (docs-only vs code)
2. Allocate agents and tasks (explicit DoD)
3. Enforce deterministic verification steps
4. Consolidate outputs into one minimal diff
5. Run local verification gates where possible
6. Commit/PR hygiene (clear messages, low-risk diffs)

## Failure Modes and Recovery
- Gate fails (docs-reference-targets): remove/neutralize non-existent targets or create stubs
- Non-deterministic outputs: enforce stable markers and idempotent scripts
- Scope creep: split into smaller PRs, keep one concern per PR

## Operator Checklist
- Working tree clean
- Gates green
- Docs navigation updated (if relevant)
