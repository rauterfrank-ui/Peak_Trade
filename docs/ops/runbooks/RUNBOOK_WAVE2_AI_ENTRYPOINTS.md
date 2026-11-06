# RUNBOOK – Wave 2 AI Entry Points

## Ziel
Strategisch wichtige AI-Module mit reproduzierbarer Bedienoberfläche versehen.

## Kandidaten
- AI Model Policy Audit
- Switch Layer

## Aktivierungsmuster
- CLI oder Script
- Smoke-Test
- Make-Target
- Runbook

## Nicht-Ziele
- keine Live-Freigabe
- keine Execution-Kopplung
- keine Order-Entscheidungen

## Pass 1 – Aktivierte Einstiege
Policy Audit:
- `PYTHONPATH=. python3 src&#47;ops&#47;p50&#47;ai_model_policy_cli_v1.py --help`

Switch Layer:
- `python3 scripts/ai/switch_layer_smoke.py`

Make:
```bash
make wave2-ai-entrypoints-smoke
```

## Pass 2 – deterministische Smoke-Runs
Policy Audit:
- `PYTHONPATH=. python3 scripts&#47;ai&#47;policy_audit_smoke.py`

Switch Layer:
- `PYTHONPATH=. python3 scripts&#47;ai&#47;switch_layer_smoke.py`

Fixtures:
- `tests&#47;fixtures&#47;ai&#47;policy_audit_input.json`
- `tests&#47;fixtures&#47;ai&#47;switch_layer_input.json`

Make:
```bash
make wave2-ai-deterministic-smoke
```
