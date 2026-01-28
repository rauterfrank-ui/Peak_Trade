# PR 1031 — Merge Log (A‑Serie: Item A bis Finish)

## Summary
Item A abgeschlossen: Walk‑Forward Train‑Optimierung (no leakage) + Two‑Pass Portfolio‑Allocation (risk_parity, sharpe_weighted) inkl. Evidence/Backlog Updates.

## Why (Governance / Correctness)
- **No leakage**: Walk‑Forward Train/Test Slicing end‑exclusive, keine `.loc`-Overlap‑Kante.
- **No silent fallback**: Allocation-Methoden werfen **ValueError** bei invaliden/zu kurzen Preview-Daten statt still auf equal zu fallen.
- **Determinism**: stabile Parameter-/Strategie‑Reihenfolge, reproduzierbare Weights/Artifacts.
- **Single weighting point**: Portfolio-Combine als \(equity_p(t)=\sum_i w_i \cdot equity_i(t)\) ohne doppelte Skalierung.

## Changes (grouped)

### 1) A‑WF Code — PR #1028 (merged)
- **PR**: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1028`
- **Merge commit**: `f37535c65f2a4c7cc2f507aa3107604267accb24`
- **MergedAt**: 2026-01-28T03:59:19Z
- **Changed files**:
  - `src/backtest/walkforward.py`
  - `tests/backtest/test_walkforward_optimization.py`
- **Highlights**:
  - Optional **train-only** Optimierung via `param_grid` (deterministisch, stable tie-break).
  - End‑exclusive Window Slicing (Train `[start,end)`, Test `[end,end2)`), keine `.loc`-Inklusivität.
  - Optimization‑Artefakt JSON pro Config/Run.

### 2) A‑WF Docs/Evidence — PR #1029 (merged)
- **PR**: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1029`
- **Merge commit**: `db4e71bfbef6c6adb42fec789e7cb4cd6fc7ced1`
- **MergedAt**: 2026-01-28T04:06:28Z
- **Changed files**:
  - `docs/TECH_DEBT_BACKLOG.md`
  - `docs/ops/evidence/EV_TECH_DEBT_A_WF_20260128.md`

### 3) A‑ALLOC Code — PR #1030 (merged)
- **PR**: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1030`
- **Merge commit**: `af02a6d562e84c9405017016f734b96072b3b444`
- **MergedAt**: 2026-01-28T04:32:08Z
- **Changed files**:
  - `src/backtest/engine.py`
  - `tests/backtest/test_engine_allocations.py`
  - `tests/backtest/test_engine_two_pass_allocation.py`
- **Highlights**:
  - Two‑pass Allocation: Preview (erste `allocation_estimation_bars`) → Gewichte → Full Runs → Combine.
  - v1 `risk_parity`: inverse‑vol Weights (std‑floor epsilon).
  - v1 `sharpe_weighted`: Sharpe → clip(0,+inf) → renorm; **ValueError** wenn alle 0.
  - Combine: **single weighting point**, kein `initial_cash` Pre-Scaling.

### 4) A‑ALLOC Docs/Evidence — PR #1031 (merged)
- **PR**: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1031`
- **Merge commit**: `c6fc803600962c8fb848cfbf896be82c0c37abe7`
- **MergedAt**: 2026-01-28T04:39:11Z
- **Changed files**:
  - `docs/TECH_DEBT_BACKLOG.md`
  - `docs/ops/evidence/EV_TECH_DEBT_A_ALLOC_20260128.md`

## Verification
- **CI required checks (required-only)**:
  - PR #1028: PASS (all required checks `SUCCESS`)
  - PR #1029: PASS (all required checks `SUCCESS`)
  - PR #1030: PASS (all required checks `SUCCESS`)
  - PR #1031: PASS (all required checks `SUCCESS`)
- **Local commands (belegt in PR‑Bodies / Runbooks)**:

```bash
# PR #1028
uv run pytest -q tests/test_walkforward_backtest.py tests/backtest/test_walkforward_optimization.py
uv run ruff format --check src/ tests/ scripts/

# PR #1030
uv run pytest -q tests/backtest/test_engine_allocations.py
uv run ruff format --check src/backtest/engine.py tests/backtest/test_engine_allocations.py

# Docs PRs (#1029/#1031) – changed-only docs gates snapshot (runbook)
bash scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

## Risk
- **NO‑LIVE**: Backtest‑only Engine/Tests + Docs‑only Evidence. Keine Live‑Execution Pfade.
- **Behavior impact**:
  - Walk‑Forward unterstützt optional `param_grid` (Train‑only Selection + JSON‑Artefakte).
  - Portfolio‑Allocation erweitert um `risk_parity`/`sharpe_weighted` ohne silent fallback.

## Operator How‑To
- **Two‑pass allocation knobs (engine pipeline only)**:
  - `allocation_estimation_bars` (Default: 500)
  - `risk_free_rate` (Default: 0.0; nur `sharpe_weighted`)
- **Walk‑Forward optimization**:
  - `param_grid` aktivieren (deterministisch); Artefakt: `*walkforward_optimization.json`

## References
- PRs + Merge Commits:
  - PR #1028 → `f37535c65f2a4c7cc2f507aa3107604267accb24`
  - PR #1029 → `db4e71bfbef6c6adb42fec789e7cb4cd6fc7ced1`
  - PR #1030 → `af02a6d562e84c9405017016f734b96072b3b444`
  - PR #1031 → `c6fc803600962c8fb848cfbf896be82c0c37abe7`
- Evidence:
  - `docs/ops/evidence/EV_TECH_DEBT_A_WF_20260128.md`
  - `docs/ops/evidence/EV_TECH_DEBT_A_ALLOC_20260128.md`
- Backlog status:
  - `docs/TECH_DEBT_BACKLOG.md`
- Runbook:
  - `docs/ops/runbooks/RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md`
