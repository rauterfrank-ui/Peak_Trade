# Recommended Next Slice

```text
RECOMMENDED_CONTRACT=OPTION_D
NEXT_RECOMMENDED_ACTION=STOP_NO_SIDE_ACTIVATION_UNTIL_SEPARATE_OPERATOR_GO_FOR_OPTION_B_COMPOSER
```

## Why stop

- OBL_B07 already ratifies EVENT_ONLY with `entry_side=NONE`.
- No competing productive Side authority exists.
- Activating LONG&#47;SHORT now would violate EVENT_ONLY and risk a second truth.

## Smallest future slice (only after new Operator-GO)

If later authorizing **OPTION_B**:

1. Define Bollinger Strategy Intent as event-only permission (ENTRY&#47;EXIT), still no side emission from producer.
2. Add a **single** Master-V2-scoped agreement gate: Intent ∧ Composition selected_side → executable direction, else NONE.
3. Do **not** project Bull&#47;Bear into `entry_side`.
4. Keep Classic `run_realistic` non-canonical.
5. Symmetric fail-closed for missing Intent and Direction conflict.
6. No LIVE&#47;Orders activation in that slice.

## Explicitly out of scope next

- OPTION_A Bollinger-owned LONG&#47;SHORT
- Symmetric short geometry
- Runtime&#47;bridge activation
- Economic evaluation
