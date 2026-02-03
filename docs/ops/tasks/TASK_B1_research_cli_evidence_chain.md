# Task B1: research_cli Evidence-Chain

**Phase:** B (Evidence-Chain standardisieren)  
**Status:** In Progress  
**Branch:** `feat/research-cli-evidence-chain`

## Ziel

`scripts/research_cli.py` produziert pro Lauf ein reproduzierbares Evidence Pack:

- `artifacts/research/<run_id>/meta.json` (git sha, python, sandbox, run params)
- Unterverzeichnisse: `env/`, `logs/`, `reports/`, `plots/`, `results/`

## Preconditions

- Repo auf `main`, aktuell
- Keine uncommitted Changes an kritischen Pfaden

## Schritte

1. **Output-Contract** – Evidence Pack Layout als Code (src/ops/evidence.py):
   - `EVIDENCE_LAYOUT`: meta.json, env, logs, reports, plots, results
   - `ensure_evidence_dirs(base_dir)`, `write_meta(meta_path, extra)`

2. **research_cli.py anbinden**
   - run_id: CLI-Argument oder generiert (z.B. `research_YYYYMMDD_HHMMSS_<short_id>`)
   - base_dir = `artifacts/research/<run_id>`
   - Beim Start: `ensure_evidence_dirs(base_dir)`; `write_meta(base_dir / "meta.json", extra={command, run_id, …})`

3. **Tests / Checks**
   - `python -m py_compile src/ops/evidence.py scripts/research_cli.py`
   - Optional: Smoke-Run mit kleinem Modus
   - `PEAKTRADE_SANDBOX=1 pytest -q tests/ops tests/scripts …`

## Definition of Done

- [ ] `src/ops/evidence.py` existiert mit EVIDENCE_LAYOUT, ensure_evidence_dirs, write_meta
- [ ] research_cli.py erstellt pro Run ein Evidence-Verzeichnis und meta.json
- [ ] Docs: docs/ops/drills/PHASE_B_RESEARCH_CLI_EVIDENCE_CHAIN.md
- [ ] PR offen, Checks grün

## Referenzen

- Phase A: Sandbox/Ops (PHASE_A_…)
- src/experiments/evidence_chain.py (Backtest Evidence)
- docs/ops/PHASE3_VERIFICATION_EVIDENCE_PACK.md
