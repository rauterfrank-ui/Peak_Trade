# PR #144 – Merge Log (MERGED ✅)

## Merge Details
- PR: #144 – docs(reporting): clean up doc paths, avoid tracking in ignored dirs
- Repo: rauterfrank-ui/Peak_Trade
- PR URL: https://github.com/rauterfrank-ui/Peak_Trade/pull/144
- Merge Commit: `a4a18f21d2cd61c438bc678c235a1ca2282299fc`
- Merged At: 2025-12-18T20:41:30Z

## What Changed
- Moved `docs/reports/REPORTING_QUICKSTART.md` → `docs/reporting/REPORTING_QUICKSTART.md`
- Updated `scripts/research_el_karoui_vol_model.py`: changed `REPORT_PATH` from `docs/reports` → `docs/research`
- Ensures no tracked files remain under `docs/reports/` (ignored directory)

## Verification
- `git check-ignore -v docs/reports/`: directory correctly ignored via `.gitignore`
- `git ls-files docs/reports/`: no tracked files under `reports/`
- `pytest tests/integration/test_evidence_chain.py`: 14 passed
- Smoke test: Quarto rendering and artifact chain integrity confirmed

## Notes / Follow-ups
- Consider documenting "docs/reports is ignored" policy in `docs/reporting/README.md` for future contributors
- Reporting documentation now centralized under `docs/reporting/`
