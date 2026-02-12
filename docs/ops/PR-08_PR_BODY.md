# PR-08: Stage1 runner erzeugt validation.json, Exit 2 on validation failure

## What
- Stage1-Runner erzeugen nach Index-Generierung `validation.json`
- Fail-fast: Exit-Code 2 bei Validierungsfehler
- Erforderliche Artefakte (data.json, report.md) enforced

## Evidence
- `docs/ops/evidence/packs/PR-08/EV-2026-02-PR08-001.json`

## Verify (fixture commands aus Evidence)
```bash
python3 scripts/obs/stage1_report_index.py --root tests/fixtures/stage1_reports/sample_a --out /tmp/stage1_index.json --run-date 2026-02-02
python3 scripts/obs/validate_stage1_index.py --root tests/fixtures/stage1_reports/sample_a --index /tmp/stage1_index.json --out /tmp/stage1_validation.json --require data.json --require report.md
# Erwartung: exit_code=0, index und validation written
```

---
**Head:** `pr-08-stage1-validation`  
**Base:** `pr-05-observability-port-collision` (stacked; nach Merge von PR-05 ggf. Base auf `main` umstellen)
