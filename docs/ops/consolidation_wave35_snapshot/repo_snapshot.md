# Repo Snapshot — Wave 35 Consolidation Audit

**Timestamp:** 2026-03-12  
**Branch:** feat/full-scan-wave35-consolidation-audit-snapshot  
**Base:** main (origin/main)

---

## Current Repo Head / Key Commits

```
0b10a99f feat(config): align required_status_checks to GitHub branch protection (#1760)
0052b315 fix(ci): expand matrix job names in required-checks hygiene validator (#1759)
b2429e8f docs(ops): Wave 30 required contexts docs clarification (#1758)
86ee5e79 docs(ops): Wave 29 required contexts proof review — evidence package (#1757)
```

---

## Validator Fix Presence (Wave 34)

- **Commit:** 0052b315 (#1759)
- **Fix:** `scripts/ci/validate_required_checks_hygiene.py` — `_expand_matrix_job_names()` expands matrix job names (e.g. `tests (${{ matrix.python-version }})`) so runtime-emitted contexts like `tests (3.11)` are recognized.
- **Status:** ✅ Present on main

---

## Config Alignment (Wave 33 Retry)

- **Commit:** 0b10a99f (#1760)
- **Change:** `config/ci/required_status_checks.json` aligned to GitHub branch protection (9 required contexts).
- **Status:** ✅ Present on main

---

## Docs Wording References (Required Checks)

- **CI.md:** States config is aligned to GitHub branch protection (9 required contexts). References `config/ci/required_status_checks.json` and `gh api repos/<owner>/<repo>/branches/main/protection`.
- **GATES_OVERVIEW.md:** States config is aligned to GitHub branch protection (9 required contexts). References `config/ci/required_status_checks.json` and branch protection API.

---

## Wave 26 / Wave 29 Context

- **Wave 26:** CI/Ops hygiene classification; no functional mutation.
- **Wave 29:** Documented docs-reality gap (config said PR Gate only; GitHub had 9 contexts).
- **Wave 33 retry (#1760):** Config aligned to GitHub.
- **Wave 34 (#1759):** Validator expanded matrix job names.
