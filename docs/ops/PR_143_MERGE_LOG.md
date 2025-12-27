# PR #143 — MERGE LOG

- **PR:** #143
- **Title:** feat(p1): evidence chain artifacts + optional MLflow/Quarto reporting for core runners
- **Merged at:** 2025-12-18T20:21:45Z
- **Merge commit:** `312b0fea6e0eb2ccb14dcda9646e1b633f3d948e`
- **Base branch:** `main`

## Summary
P1 Evidence Chain implemented and integrated (policy-safe templates + optional Quarto rendering):
- Evidence Chain core helper: emits standard artifacts under `results/<run_id>/`
- Unit tests for Evidence Chain core (comprehensive)
- `scripts/run_backtest.py` upgraded to write artifacts + optional report
- Quarto template stored under `templates/quarto/` to satisfy repo policy (no tracked `reports/`)
- Render script writes only into run-local output: `results/<run_id>/report/`

## Changed Files (High level)
- `src/experiments/evidence_chain.py`
- `tests/test_evidence_chain.py`
- `scripts/run_backtest.py`
- `templates/quarto/backtest_report.qmd`
- `scripts/render_last_report.sh`
- `docs&sol;reports&sol;REPORTING_QUICKSTART.md (planned)`

## Verification
- `python -m pytest -q tests/test_evidence_chain.py`: **PASS**
- `bash scripts/validate_git_state.sh`: **PASS**
- `bash scripts/automation/post_merge_verify.sh`: **PASS**

## Notes / Follow-ups
- Next: extend Evidence Chain integration to `research_cli.py` and `live_ops.py` (P1.1).
