# PR #623 — AI Autonomy Control Center v0

Date: 2026-01-09  
Type: Docs-only  
Risk: Minimal  

## Summary
Adds a docs-only AI Autonomy Control Center v0 entrypoint and navigation index, and links them from the ops README.

## Why
Provide a single "Start Here" hub for AI Autonomy operations with audit-stable navigation across runbooks, evidence, and CI gate references.

## Changes
- New: `docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md`
- New: `docs/ops/control_center/CONTROL_CENTER_NAV.md`
- Update: `docs/ops/README.md` (Control Center section + links)

## Verification
- Docs-only; no runtime code paths changed.
- CI expected: docs-reference-targets PASS; other gates SKIP/PASS depending on workflow.

## Risk
Minimal (documentation-only).

## Operator Notes
Start at `docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md`.
