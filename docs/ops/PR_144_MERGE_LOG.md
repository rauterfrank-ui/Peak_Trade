# PR #144 — Merge Log

## PR
- Title: docs(reporting): clean up doc paths, avoid tracking in ignored dirs
- URL: https://github.com/rauterfrank-ui/Peak_Trade/pull/144
- Base: main
- Head: feat/reporting-docs-cleanup

## Merge
- Merge SHA: a4a18f21d2cd61c438bc678c235a1ca2282299fc
- Merged at: 2025-12-18T20:41:30Z
- Diffstat: +3 / -3 (files changed: 3)

## Summary
- Move `docs&sol;reports&sol;REPORTING_QUICKSTART.md (planned)` → `docs/reporting/REPORTING_QUICKSTART.md`
- Update `scripts/research_el_karoui_vol_model.py`: `REPORT_PATH` from `docs&sol;reports` (planned directory) → `docs&sol;research` (planned directory)
- Update `tests/research/test_research_el_karoui_vol_model.py`: adjust assertion for new path
- Ensure no tracked files under `docs&#47;reports&#47;` (gitignored directory)

## Why
- Separation of concerns: tracked docs under `docs&#47;*`, generated artifacts under `reports&#47;*`
- Avoid policy violations: don't track files in ignored directories
- Centralize reporting documentation under `docs/reporting/`

## Changes
- **Moved:**
  - `docs&sol;reports&sol;REPORTING_QUICKSTART.md (planned)` → `docs/reporting/REPORTING_QUICKSTART.md`

- **Modified:**
  - `scripts/research_el_karoui_vol_model.py` – `REPORT_PATH = "docs&#47;research"`
  - `tests/research/test_research_el_karoui_vol_model.py` – assertion path updated

## Verification
- CI: All PR checks green (3792 tests passed, audit, strategy-smoke, health-gate)
- `git check-ignore -v docs&#47;reports&#47;` → correctly ignored via `.gitignore`
- `git ls-files docs&#47;reports&#47;` → no tracked files
- `pytest tests&#47;integration&#47;test_evidence_chain.py` → 14 passed
- Quarto rendering + artifact chain integrity confirmed

## Notes / Follow-ups
- Consider documenting "docs/reports is ignored" policy in `docs&sol;reporting&sol;README.md` (planned)
- Reporting docs now centralized under `docs/reporting/`
