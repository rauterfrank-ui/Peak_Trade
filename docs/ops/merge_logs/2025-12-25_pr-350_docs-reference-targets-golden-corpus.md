# Merge Log — PR #350 — Docs Reference Targets Guardrail: Golden Corpus

- PR: #350
- Squash commit: ca71cfa
- Commit: 53d0db4 — test(ops): add golden corpus fixtures for docs reference targets guardrail
- Date: 2025-12-25

## Summary
Golden-Corpus-Fixtures + Script-Normalisierung für `verify_docs_reference_targets.sh` erweitert, um Edge Cases in Markdown robust zu behandeln (Links `[]()`, Angle-Brackets `<...>`, Anchors/Queries, relative Pfade).

## Why
Docs-Targets sind "drift-prone": Markdown-Syntax, URLs, relative Links sowie `#anchor`/`?query` erzeugen schnell False Positives oder echte Misses. Ein kleiner Fixture-Corpus + deterministische Normalisierung macht den Guardrail stabil und regressionssicher.

## Changes
- Updated: `scripts/ops/verify_docs_reference_targets.sh`
  - `normalize_target()`:
    - Strip `?query` + improved punctuation trimming
    - Relative paths `./` und `../` erkannt
  - `resolve_target()`:
    - Relative paths werden relativ zur jeweiligen Markdown-Datei resolved
    - Nur Targets innerhalb `repo-root` werden geprüft
  - `REPO_ROOT`/`DOCS_ROOT` als absolute Pfade (robust gegen cwd)
  - Git-root detection + find fallback für fixture repos
- New: Golden corpus fixtures (PASS):
  - `tests/fixtures/docs_reference_targets/pass/edge_cases_links.md`
  - `tests/fixtures/docs_reference_targets/pass/edge_cases_angle_brackets.md`
- New: isolated fixture repo:
  - `tests&#47;fixtures&#47;docs_reference_targets&#47;relative_repo&#47;…`
- Updated: `tests/ops/test_verify_docs_reference_targets_script.py`
  - +1 Test für relative repo-root/docs-root (3/3 Tests)

## Verification
CI Required Checks grün inkl.:
- docs-reference-targets-gate
- tests (3.11)
- audit
- Lint/Policy/Smoke Gates

## Risk
LOW (Docs/Tests + robustere Target-Normalisierung). Keine Trading-/Risk-/Execution-Logik betroffen.

## Operator How-To
- Lokal:
  - `scripts/ops/verify_docs_reference_targets.sh`
- Golden Corpus (Regression):
  - `scripts&#47;ops&#47;verify_docs_reference_targets.sh --docs-root tests&#47;fixtures&#47;docs_reference_targets&#47;pass`
  - `scripts&#47;ops&#47;verify_docs_reference_targets.sh --repo-root tests&#47;fixtures&#47;docs_reference_targets&#47;relative_repo --docs-root tests&#47;fixtures&#47;docs_reference_targets&#47;relative_repo&#47;docs`
  - `tests/ops/test_verify_docs_reference_targets_script.py`

## References
- PR #350 (merged)
- Script: `scripts/ops/verify_docs_reference_targets.sh`
- Tests: `tests/ops/test_verify_docs_reference_targets_script.py`
