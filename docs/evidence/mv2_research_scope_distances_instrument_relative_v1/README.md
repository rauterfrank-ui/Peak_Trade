# MV2 Research Scope Distances Instrument-Relative v1

```text
SLICE=FIX_MV2_RESEARCH_SCOPE_DISTANCES_INSTRUMENT_RELATIVE_V1
BASE_SHA=a55c4000f33269a98107fd1294b1c9ba82433cad
BRANCH=fix/mv2-research-scope-distances-instrument-relative-v1
ROOT_CAUSE_CLASS=UNIT_MISMATCH
DISTANCE_UNIT=BPS
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
LIVE_AUTHORIZED=false
ORDERS=false
```

## Verdict

Hardcoded absolute research distances `120&#47;60&#47;90` in `_build_replay_input` are replaced by
mark-relative BPS (`100&#47;50&#47;75` implied via `100 bps` up + legacy ratios `0.5&#47;0.75`),
converted once to absolute price units for the generator contract.

1INCH research sample: `noop` 2893 → 67; bull/bear geometry candidates reachable;
bull path reaches `upscope_confirmed` / `LONG_ACTIVE`.

## Non-goals

- No generator / `transition_state` / composition changes
- No strategy parameter optimization / PnL tuning
- No runtime / order / live activation
- No removal of pre-existing `LONG_ARMED` research seed (out of scope)

## Follow-up note

Under legacy ratios `adverse < up`, generator prioritizes `ADVERSE_EXIT` over `DOWNSCOPE`
when both match — so bearish bars often emit `adverse_exit_candidate` rather than
`downscope_*`. That is pre-existing selection order + preserved ratio, not unit mismatch.
