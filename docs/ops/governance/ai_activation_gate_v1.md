# AI Activation Gate v1

## Principle
- Models may compute signals in Shadow/Paper/Testnet.
- **AI->LIVE execution is hard-blocked** until Papertrail readiness + explicit arming + confirm token.

## Config
`config/governance/ai_activation_gate_v1.json`

## Live unlock conditions (ALL required)
- `papertrail_ready=true`
- `allow_ai_to_execute_live=true`
- `live_unlock.enabled=true`
- `live_unlock.armed=true`
- Confirm token env (default `PT_CONFIRM_TOKEN`) is set (if required)

## Operational rule
If any condition fails: raise AIGateError and do not place live orders.
