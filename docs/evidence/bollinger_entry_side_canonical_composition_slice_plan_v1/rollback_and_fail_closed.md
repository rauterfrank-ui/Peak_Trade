# Rollback and Fail-Closed

## Current law (OPTION_D)

- Keep `entry_side=NONE`
- Keep EVENT_ONLY mapping
- Keep Master V2 sole Direction Authority
- On doubt → no executable directional cycle

## If a future OPTION_B slice lands and regresses

1. Revert the composer PR (single bounded revert)
2. Adapter&#47;carrier must again force Bollinger `NONE`
3. Quarantine&#47;sole-authority tests must stay green
4. No partial activation (LIVE&#47;Orders remain false)

## Never rollback-by-loosening

- Do not weaken fail-closed assertions to green CI
- Do not admin-bypass required checks
- Do not reclassify Classic LONG as canonical Intent
