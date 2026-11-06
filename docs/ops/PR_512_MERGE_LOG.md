# PR #512 — Merge Log

## Summary
CI-Required-Checks wurden gehärtet, sodass Required Contexts (insb. `tests (3.11)` und `strategy-smoke`) deterministisch materialisieren und nicht mehr durch Skip/Cancellation/Pending-Artefakte den Merge blockieren. Zusätzlich wurde ein Operator-Quickflow für `mergeable: UNKNOWN` dokumentiert und an den relevanten Frontdoors verlinkt.

## Why
Branch-/Ruleset-Required Checks waren zeitweise „stuck" (pending/cancelled), obwohl CI-Runs insgesamt erfolgreich waren. Ursache war nicht deterministische Materialisierung bzw. ein fragiler Change-Detection-Pfad. Ziel war audit-stabile, deterministische Required-Context-Erzeugung (auch bei docs-only) sowie PR-isolierte Concurrency.

## Changes
- CI Workflow Härtung:
  - PR-isolierte `concurrency.group` (Workflow + PR-Nummer/Ref), um Cross-PR Cancels zu verhindern.
  - `changes` Job fail-open: bei `paths-filter` Problemen default `code_changed=true` (damit Required Jobs laufen statt hängen).
  - Required Jobs behalten feste Namen:
    - `tests (${{ matrix.python-version }})` → garantiert `tests (3.11)`
    - `strategy-smoke`
- Guardrail:
  - `ci-required-contexts-contract` erzwingt deterministisch:
    - keine job-level `if:` auf required jobs
    - explizite Namen + Matrix-Var im Namen
    - Python 3.11 enthalten
    - PR-isolierte Concurrency ohne Cross-PR Drift
- Ops-Dokumentation:
  - Runbook `github_rulesets_pr_reviews_policy.md` inkl. Operator-Quickflow bei `mergeable: UNKNOWN`
  - Verlinkung an 3 Frontdoors: Runbook, Ops README, CI Workflow Kommentar.

## Verification
- PR #512: Required Checks `tests (3.11)` und `strategy-smoke` sind `COMPLETED&#47;SUCCESS`.
- `ci-required-contexts-contract` Job grün; Guardrail schlägt bei Drift deterministisch fehl.
- Merge erfolgreich; Branch cleanup durchgeführt (local + remote).

## Risk
Low. Änderungen betreffen CI-Orchestrierung und Guardrails, nicht Trading-Logik. Fail-open im `changes`-Job kann zu mehr Testausführung führen (konservativ), nicht zu weniger.

## Operator How-To
- Bei `mergeable: UNKNOWN`: Runbook-Quickflow verwenden.
- Wenn Required Check Context fehlt/pending: `ci-required-contexts-contract` Output ist Source-of-Truth.

## References
- PR: #512
- Runbook: `docs/ops/runbooks/github_rulesets_pr_reviews_policy.md`
- CI: `.github/workflows/ci.yml`
- Guard: `scripts/ops/check_required_ci_contexts_present.sh`
