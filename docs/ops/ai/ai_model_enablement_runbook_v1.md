# AI Model Enablement Runbook v1

## Overview
P50 policy layer: enable + arm + optional confirm token. Required for paper/shadow model calls.

## Env
- `PEAKTRADE_STAGE` = research | shadow | testnet | live (default: research)
- `PEAKTRADE_AI_CONFIRM_SECRET` = HMAC secret for mint/verify tokens
- `PEAKTRADE_AI_CONFIRM_TOKEN` = token provided at runtime (required in testnet/live)

## Status (no side effects)
```bash
python3 -m src.ops.p50.ai_model_policy_cli_v1 --json status
```

## Enable + Arm (paper/shadow)
```bash
python3 -m src.ops.p50.ai_model_policy_cli_v1 enable
python3 -m src.ops.p50.ai_model_policy_cli_v1 arm
```

## Token Flow (when token_required)
```bash
# Mint token (requires PEAKTRADE_AI_CONFIRM_SECRET)
python3 -m src.ops.p50.ai_model_policy_cli_v1 mint-token --reason "paper session"

# Verify (pass token via env or arg)
python3 -m src.ops.p50.ai_model_policy_cli_v1 verify --token '<TOKEN>'
```

## Disable / Disarm
```bash
python3 -m src.ops.p50.ai_model_policy_cli_v1 disable
python3 -m src.ops.p50.ai_model_policy_cli_v1 disarm
```

## Audit
Audit events: `out&#47;ops&#47;ai_policy&#47;ai_model_policy_v1_audit.ndjson`
