# PR-05: Fail-fast Port-Kollisionen + canonical env var + legacy fallback

## What
- Fail-fast bei Metrics-Port-Kollisionen
- Canonical Env-Var für Metrics-Port
- Legacy-Fallback für bestehende Setups

## Evidence
- `docs/ops/evidence/packs/PR-05/EV-2026-02-PR05-001.json`

## Verify
```bash
python3 -m pytest -q tests/ops/test_ports.py
# optional:
python3 -m pytest -q tests/obs/test_metrics_config.py
```

---
**Head:** `pr-05-observability-port-collision`  
**Base:** `main` (oder `pr-04-event-schemas`, falls PR-04 noch nicht gemerged)
