# Merge Log — PR #347 — Docs Reference Targets Guardrail

- PR: #347
- Branch: feat/ops-docs-reference-targets-guardrail
- Merge commit (squash): 6bd7092
- Label: documentation
- Date: 2025-12-25

## Summary
Docs Reference Targets Guardrail eingeführt: CI prüft, dass in Docs referenzierte Pfade/Targets tatsächlich existieren (robust gegen typische False-Positive-Muster).

## Why
Dokumentationsdrift (kaputte Referenzen) ist ein Operator-Pain: Links/Targets in Runbooks/READMEs müssen verlässlich sein. Der Guardrail verhindert "silent rot" und macht Broken-Refs sofort sichtbar (CI required check).

## Changes
- New: `.github/workflows/docs_reference_targets_gate.yml`
  - CI-Job `docs-reference-targets-gate` als Required Check (schnell, docs-fokussiert)
- New: `scripts/ops/verify_docs_reference_targets.sh`
  - Robustes Parsing/Filtering gegen False Positives:
    - Wildcard-Filtering: ignoriert `* ? [ ] < >`
    - Command-Filtering: ignoriert Pfade mit Spaces (z.B. `ops_center.sh doctor`)
    - Directory-Filtering: ignoriert trailing `/`
    - Code-Block-Tracking: ignoriert Referenzen innerhalb von ```bash ... ``` Blocks
- Updated: `scripts/ops/ops_center.sh`
  - Doctor-Integration des neuen Guardrails
- Updated: `docs/ops/README.md`
  - Dokumentation des Checks + Pfad-Korrektur (u.a. `RISK_LAYER_ROADMAP.md` Referenz)

## Verification
CI (Required Checks) grün:
- CI Health Gate
- Docs Diff Guard Policy Gate
- Lint Gate
- Policy Critic Gate
- docs-reference-targets-gate
- strategy-smoke
- tests (3.11)
- audit

## Risk
LOW (docs/ops tooling + CI only). Kein Einfluss auf Trading-Logic, Risk-Engine oder Execution.

## Operator How-To
- Lokal (CI Parity - empfohlen):
  - `./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`
  - `./scripts/ops/ops_center.sh doctor`
- Lokal (Full-Scan Audit - optional): <!-- pt:ref-target-ignore -->
  - `./scripts/ops/verify_docs_reference_targets.sh`
- CI:
  - Job `docs-reference-targets-gate` muss grün sein (Required Check)

## References
- PR #347 (merged): Docs Reference Targets Guardrail
- Scripts:
  - `scripts/ops/verify_docs_reference_targets.sh`
  - `scripts/ops/ops_center.sh`
