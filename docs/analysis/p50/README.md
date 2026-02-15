# P50 — AI Model Enablement Policy v1

This adds a **policy-driven enablement layer** on top of P49's hard gate:
- deny-by-default
- stage-aware (research/shadow/testnet/live)
- 2-step activation: `enabled` + `armed`
- optional **confirm token** (required by default for testnet/live)
- audit trail written to `out/ops/ai_policy/*`

## Env
- `PEAKTRADE_STAGE` = research|shadow|testnet|live (default: research)
- `PEAKTRADE_AI_CONFIRM_SECRET` = HMAC secret for mint/verify tokens
- `PEAKTRADE_AI_CONFIRM_TOKEN` = token provided at runtime for model calls (required in testnet/live)

## CLI
```bash
python -m src.ops.p50.ai_model_policy_cli_v1 --json status
python -m src.ops.p50.ai_model_policy_cli_v1 enable
python -m src.ops.p50.ai_model_policy_cli_v1 arm
python -m src.ops.p50.ai_model_policy_cli_v1 mint-token --reason "enable testnet"
python -m src.ops.p50.ai_model_policy_cli_v1 verify --token '<TOKEN>'
```
