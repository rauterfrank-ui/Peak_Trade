# PR #766 — Merge Log

## Summary
Doc-fix: Token-Policy + Reference-Targets Issue im Shadow-to-Live Runbook (Illustrative Path Escaping: `/` → `&#47;`).

## Why
CI-Gates (docs-token-policy-gate + docs-reference-targets-gate) waren rot auf derselben Runbook-Stelle; Ziel war ein minimaler, governance-sicherer Fix.

## Changes
- Minimaler Doc-Fix im Runbook: Illustrative Path Escaping angepasst (`/` → `&#47;`).

## Verification
- PR #766: mergeStateStatus=CLEAN, mergeable=MERGEABLE
- Checks: PASS (docs-token-policy-gate, docs-reference-targets-gate, tests 3.9/3.10/3.11, Cursor Bugbot)
- Expected skips: Health Checks (wie policy)

## Risk
Niedrig (Docs-only, additive/minimal, keine Runtime-Änderungen).

## Operator How-To
- Keine Operator-Aktion erforderlich (Dokumentationsfix).

## References
- PR: #766
- Merge: f6c60c57
