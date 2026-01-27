# RUNBOOK_D4_OPS_GOVERNANCE_POLISH

Status: PLANNED (stub for reference-targets gate)

## Purpose
Governance polish checklist for Ops workflows (docs gates, merge hygiene, evidence templates, and operator guardrails).

## Scope
- Docs gates / token policy / reference targets
- Merge log hygiene
- Evidence pack conventions

## Operator Steps (high level)
1. Run docs gates snapshot (PR-mode).
2. Fix token-policy violations (use code fences for commands; token-safe paths in prose).
3. Fix missing reference targets (correct paths or add stub placeholders).
4. Re-run gates until PASS.

## Outputs
- Updated docs/runbooks
- Evidence file under docs&#47;ops&#47;evidence&#47;...
