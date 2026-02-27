# Wave 2 – AI Entry Points Plan

## Ziel
Strategisch wichtige AI-Module mit reproduzierbarer Bedienoberfläche versehen.

## Fokus
- `src/ai/audit/ai_model_policy_audit_v1.py`
- `src/ai/switch_layer/switch_layer_v1.py`

## Deliverables
- minimaler Entrypoint / CLI-Surface
- Smoke-Test
- Make-Target
- Runbook
- keine Live-Kopplung

## Guardrails
- local-first
- deterministic smoke
- keine Order-/Execution-Freigabe
- keine Side Effects außerhalb von lokalen Output-Artefakten

## Pass 1 – Aktivierte Einstiege
- Policy Audit: `PYTHONPATH=. python3 src&#47;ops&#47;p50&#47;ai_model_policy_cli_v1.py --help`
- Switch Layer: `python3 scripts/ai/switch_layer_smoke.py`
- Make: `make wave2-ai-entrypoints-smoke`

## Pass 2 – deterministische Smoke-Runs
- Policy Audit: `PYTHONPATH=. python3 scripts&#47;ai&#47;policy_audit_smoke.py`
- Switch Layer: `PYTHONPATH=. python3 scripts&#47;ai&#47;switch_layer_smoke.py`
- Fixtures: `tests&#47;fixtures&#47;ai&#47;policy_audit_input.json`, `switch_layer_input.json`
- Make: `make wave2-ai-deterministic-smoke`
