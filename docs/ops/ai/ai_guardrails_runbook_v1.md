# AI Guardrails Runbook v1

## Principles
- **Deny by default**: all AI model calls must be blocked unless explicitly enabled/armed with a verified token.
- **Modes**:
  - `paper`, `shadow`: allowed *only if* policy enablement permits.
  - `live`, `record`: **blocked** (hard gate) unless and until a dedicated release explicitly lifts it.

## Current Gates
- P49: AI Model Hard Gate v1 (deny-by-default)
- P50: AI Model Enablement Policy v1 (enable + arm + token; audit trail)

## Quick Verify (no model calls)
```bash
python3 -m src.ops.p50.ai_model_policy_cli_v1 --json status
```

## Escalation
- To enable paper/shadow: see `ai_model_enablement_runbook_v1.md`
- Live/record: **do not attempt** — requires governance release
