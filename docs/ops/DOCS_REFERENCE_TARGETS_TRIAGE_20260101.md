# Docs Reference Targets Triage - 2026-01-01

## Metadata
- **Date**: 2026-01-01  
- **Branch**: docs/fix-reference-targets-priority1  
- **Base Commit**: b9171fec85bfd635830a31cb6900d3e748e43685 (2026-01-01 06:33:42 +0000)  
- **Command**: `./scripts/ops/verify_docs_reference_targets.sh`

## Summary
- **Total Markdown files scanned**: 600
- **Total references found**: 4250
- **Missing targets**: 198

## Priority 1: Ops/Risk-Relevant References

### ops_inspector.sh References (HIGH PRIORITY)
Diese Referenzen sind operations-kritisch und müssen aufgelöst werden:

- `docs/CONTRACT_VERIFICATION_FINAL.md:32` → scripts/ops/ops_inspector.sh
- `docs/CONTRACT_VERIFICATION_FINAL.md:42` → scripts/ops/ops_inspector.sh
- `docs/CONTRACT_VERIFICATION_FINAL.md:53` → scripts/ops/ops_inspector.sh
- `docs/CONTRACT_VERIFICATION_FINAL.md:54` → ./scripts/ops/ops_inspector.sh
- `docs/CONTRACT_VERIFICATION_FINAL.md:201` → scripts/ops/ops_inspector.sh
- `docs/CONTRACT_VERIFICATION_FINAL.md:232` → scripts/ops/ops_inspector.sh
- `docs/CONTRACT_VERIFICATION_FINAL.md:298` → scripts/ops/ops_inspector.sh
- `docs/FINAL_VERIFICATION_SUMMARY.md:193` → scripts/ops/ops_inspector.sh
- `docs/HARDENING_PATCH_SUMMARY.md:40` → scripts/ops/ops_inspector.sh

### risk_layer/ Module References (HIGH PRIORITY)
Risk-Management-kritische Referenzen:

- `docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md:16` → src/risk_layer/micro_metrics.py
- `docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md:17` → src/risk_layer/liquidity_gate.py
- `docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md:22` → src/risk_layer/risk_gate.py
- `docs/ops/PR_409_MERGE_LOG.md:45` → src/risk_layer/risk_gate.py
- `docs/ops/PR_409_MERGE_LOG.md:85` → src/risk_layer/risk_gate.py
- `docs/risk/KILL_SWITCH_RUNBOOK.md:375` → src/risk_layer/kill_switch.py
- `docs/risk/KILL_SWITCH_RUNBOOK.md:376` → src/risk_layer/risk_gate.py
- `docs/risk/RISK_METRICS_SCHEMA.md:15` → src/risk_layer/metrics.py
- `docs/risk/RISK_METRICS_SCHEMA.md:265` → src/risk_layer/metrics.py
- `docs/risk/RISK_METRICS_SCHEMA.md:272` → src/risk_layer/metrics.py
- `docs/risk/VAR_BACKTEST_GUIDE.md:28` → src/risk_layer/var_gate.py
- `docs/risk/VAR_GATE_RUNBOOK.md:337` → src/risk_layer/var_gate.py

### Other Ops-Related (MEDIUM PRIORITY)
- `docs/CONTRACT_VERIFICATION_FINAL.md:38` → docs/ops/OPS_INSPECTOR_FULL.md
- `docs/CONTRACT_VERIFICATION_FINAL.md:62` → scripts/ops/test_ops_inspector_minimal.sh
- `docs/CONTRACT_VERIFICATION_FINAL.md:205` → docs/ops/OPS_INSPECTOR_FULL.md
- `docs/CONTRACT_VERIFICATION_FINAL.md:302` → docs/ops/OPS_INSPECTOR_FULL.md

## Out of Scope: Legacy Worklogs

Die folgenden Missing Targets befinden sich in Legacy-Worklogs und werden **nicht** im Rahmen dieses PRs repariert:

### docs/_worklogs/2025-12-23_untracked_salvage/* (47 targets)
- Betrifft hauptsächlich: `src/core/tracking.py`, `src/strategies/parameters.py`, `scripts/run_optuna_study.py`, `src/data/backend.py`
- Diese Dateien sind historische Logs und müssen nicht vollständig aktualisiert werden
- Können mit Top-of-File Disclaimer versehen werden

### Strategy/Development Guides (Placeholders)
- `docs/DEV_GUIDE_ADD_EXCHANGE.md` → src/data/my_exchange.py (placeholder example)
- `docs/DEV_GUIDE_ADD_STRATEGY.md` → src/strategies/my_new_strategy.py (placeholder example)

### Other Legacy/Historical References
- Diverse alte Phase-Reports, PR-Logs, Roadmap-Dokumente
- Total ca. 150+ out-of-scope targets

## Action Items

1. **ops_inspector.sh**: Prüfen, ob Nachfolger existiert oder minimal-safe Wrapper erstellen
2. **risk_layer/**: Module-Pfade verifizieren und Docs aktualisieren
3. **Legacy worklogs**: Mit Disclaimer versehen statt vollständig reparieren
4. **Re-verify**: Script nach Fixes erneut ausführen

## Expected Outcome
Nach den Priority-1 Fixes erwarten wir:
- Reduzierung der Missing Targets um ca. 20-30 (Ops/Risk-Bereich)
- Legacy-Bereich bleibt unverändert (~150 targets)
- Verbleibende Missing Targets sind dokumentiert und akzeptiert
