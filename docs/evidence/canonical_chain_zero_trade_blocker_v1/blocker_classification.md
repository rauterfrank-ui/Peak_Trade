# Blocker Classification

```text
PRIMARY=F_ENTRY_PROJECTION_MISMATCH
SECONDARY=F_ENTRY_PROJECTION_MISMATCH+BEAR_SUITABILITY_LONG_BIAS
NOT_H=EXPECTED_ZERO_AS_POLICY_FOR_INTENT_IMPOSSIBILITY
```

| Class | Verdict | Evidence |
|-------|---------|----------|
| A PRODUCER_ZERO | **rejected** | Bollinger ENTRY `+1` panels/events present |
| B MARKET_CONTEXT_NOT_BOUND | **rejected** | CMC binds; missing was prior-mark trailing into price_path |
| C DYNAMIC_SCOPE_FROZEN | **rejected** | Scope/transition path bound; not first loss |
| D TRANSITION_NOT_REACHED | **rejected** | `transition_state` invoked; results consumed |
| E COMPOSITION_NOT_REACHED | **rejected** | Matrix ran; output was observe due to upstream flat DA |
| **F ENTRY_PROJECTION_MISMATCH** | **confirmed** | Strategy-direction-gated flat path + ENTRY→LONG suitability bias after OPTION_D |
| G INTENT_DROPPED | symptom only | Intent never actionable before fix |
| H EXPECTED_ZERO | **rejected as sole class** | Synthetic bull/bear controls produce ENTER_* without activating `entry_side` |

OPTION_D still means strategy `ENTRY_SIDE=NONE` (no Bollinger side activation). It does **not** mean the MV2 chain is forbidden from forming intents when market path + `transition_state` + composition admit a side.
