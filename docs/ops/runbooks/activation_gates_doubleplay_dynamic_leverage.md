# Activation Gates — Double-Play + Dynamic Leverage (Operator Toggles)

## Goal
Enable advanced sizing/selection features **only** under explicit operator intent:
- Double-Play specialists selector
- Dynamic leverage sizing hint (cap 50×)

## Safety Model
Default behavior: **OFF** (no changes).
To enable a feature in live context:
1) `enabled == True`
2) `armed == True`
3) `confirm_token` valid (live execution gate already enforces this)
4) Feature-specific allow flag is **True**:
   - `allow_double_play == True`
   - `allow_dynamic_leverage == True`

If any condition fails: feature remains OFF and a reason is recorded.

## Outputs
Live gates attach details:
- `details["features"] = { double_play: {enabled, reasons}, dynamic_leverage: {enabled, reasons} }`

## Non-Goals
- This PR does not execute trades.
- This PR does not change eligibility beyond existing safety gates.
