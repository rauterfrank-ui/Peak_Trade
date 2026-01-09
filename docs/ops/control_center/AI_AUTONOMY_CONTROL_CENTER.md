# AI Autonomy Control Center (v0)

Status: Draft v0  
Scope: Docs-only Control Center for AI Autonomy Operations  
Guardrails: NO-LIVE, evidence-first, determinism, SoD

## 1. Purpose
This page is the single "Start Here" entry point for AI Autonomy operations:
- Current operational posture and guardrails
- Where to find runbooks, evidence, and CI gates
- What to do next (and what is explicitly out-of-scope)

## 2. Current Status
- Latest milestone: Phase 4B Milestone 3 (Control Center Dashboard/Visual) — runbook available
- Operating mode: Governance-locked / No-live

## 3. Operator Quick Nav
See: [CONTROL_CENTER_NAV.md](CONTROL_CENTER_NAV.md)

## 4. Runbooks (Authoritative)
- Phase 4B M2 (Cursor Multi-Agent): [RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md](../runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md)
- Phase 4B M3 Control Center (Cursor Multi-Agent): [RUNBOOK_AI_AUTONOMY_4B_M3_CURSOR_CONTROL_CENTER.md](../runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CURSOR_CONTROL_CENTER.md)

## 5. Evidence (Authoritative)
- Evidence index: [EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md)
- Evidence schema: [EVIDENCE_SCHEMA.md](../EVIDENCE_SCHEMA.md)
- Evidence entry template: [EVIDENCE_ENTRY_TEMPLATE.md](../EVIDENCE_ENTRY_TEMPLATE.md)
- Evidence packs: Defined in M2 Runbook (Section 3: Artefakte & Outputs)
  - Python implementation: `src/ai_orchestration/evidence_pack.py`
  - Validator: `scripts/ops/validate_evidence_index.py`

## 6. CI Gates (Operator View)
This control center does not redefine gates; it points to the authoritative references.
- Branch Protection Required Checks: [BRANCH_PROTECTION_REQUIRED_CHECKS.md](../BRANCH_PROTECTION_REQUIRED_CHECKS.md)
- CI Policy Enforcement: [CI_POLICY_ENFORCEMENT.md](../../ci/CI_POLICY_ENFORCEMENT.md)
- P0 Guardrails Milestone: [P0_GUARDRAILS_MILESTONE.md](../../P0_GUARDRAILS_MILESTONE.md)

**Primary Gates (7 required checks):**
- Lint Gate (`lint_gate.yml`)
- Audit Gate (`audit.yml`)
- Policy Critic Gate (`policy_critic_gate.yml`)
- Docs Reference Targets Gate (`docs_reference_targets_gate.yml`)
- Tests (3.11) (`ci.yml`)
- Strategy Smoke (`ci.yml`)
- CI Contract (`ci.yml`)

**Docs-only changes:** Lint/Audit/Policy/Tests/Strategy gates skip gracefully. Docs Reference Targets gate must pass.

## 7. Standard Workflow (Minimal)
1) Choose the correct runbook (M2 for general ops, M3 for control center/dashboard work)
2) Freeze scope + acceptance criteria
3) Implement minimal docs changes
4) Run local verification checklist
5) PR → CI → merge
6) Post-merge: merge log + evidence entry (if required by the workflow)

## 8. Out of Scope (Hard)
- Any live trading enablement or strategy switching
- Any runtime execution changes unless explicitly gated and planned
- Any changes that introduce non-deterministic outputs in operational artifacts

## 9. Change Log
- v0: initial docs-only control center skeleton (2026-01-09)
