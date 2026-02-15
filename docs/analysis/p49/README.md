# P49 — AI model hard gate v1

## What
A deny-by-default hard gate for any AI-model-powered execution.

### Required env (ALL must be YES)
- `PT_AI_MODELS_ENABLED=YES`
- `PT_PAPERTRAIL_READY=YES`

### Optional 2-step arming (only if you set it)
- `PT_AI_MODELS_ARMED=YES`

## Why
Prevents accidental activation of AI model actions before papertrail/audit surfaces are "ready".

## Quick verify (local)
```bash
pytest -q tests/p49/test_ai_model_hard_gate_v1.py
```
