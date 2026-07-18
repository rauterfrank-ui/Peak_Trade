# Scope Event Noop Root Cause Audit v1

```text
SLICE=READ_ONLY_SCOPE_EVENT_NOOP_ROOT_CAUSE_AUDIT_V1
BASE_SHA=a55c4000f33269a98107fd1294b1c9ba82433cad
BRANCH=audit/scope-event-noop-root-cause-v1
PRODUCTIVE_FILES_CHANGED=false
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
LIVE_AUTHORIZED=false
ORDERS=false
STATUS=PASS
ROOT_CAUSE_CLASS=UNIT_MISMATCH
```

## Verdict

`deterministic_scope_event_generator_v1` emittiert auf Economic-Research-Bars ausschließlich `noop`, weil
`mv2_research_wiring_v1._build_replay_input` die Distanz-Inputs als **absolute Preis-Einheiten**
`up_distance=120.0`, `adverse_exit_distance=60.0`, `reversal_distance=90.0` hardcodiert.

Für 1INCH (Mark ~0.23–0.53, max. Bar-Move ~0.029) sind Bull-/Bear-Thresholds mathematisch
unerreichbar (`anchor±120`). Es entsteht kein Kandidat → Confirmation greift nie → `transition_state`
bleibt auf dem Research-Seed `LONG_ARMED` ohne `DOWNSCOPE_*`.

## Prüffragen (kurz)

| Area | Finding |
|------|---------|
| A Input-Binding | CMC/Mark/price_path gebunden und bar-dynamisch; Distances konstant 120/60/90 aus Wiring |
| B Distance/Threshold | Absolute price units; Vorzeichen LONG: up=`anchor+up`, down=`anchor-up`; bei Mark≪120 ist down-threshold negativ → unreachable |
| C Confirmation | `confirmation_epochs=2` gebunden; nie erreicht, weil `selected_kind=None` |
| D CMC | Mark/prior/price_path dynamisch; kein CMC-Boundary-Verlust für Scope-Inputs |
| E State/Trailing | Confirmation/SideState getrailt; Distances pro Bar neu als Konstanten injiziert; Anchor allein rettet nicht |
| F Symmetrie | bull/bear candidate geometry hits = 0; counterfactual 1% median → bull 255 / bear 239 |
| G Authority | Keine zweite Direction-/Composition-Authority; `entry_side=NONE`; Bridge `BOUND_NOT_ACTIVATED` |

## First value-loss boundary

`src/backtest/mv2_research_wiring_v1.py::_build_replay_input` (hardcoded `up_distance=120.0` …)
→ Generator: `generate_deterministic_scope_event` setzt `event_type=NOOP` wenn `selected_kind is None`.

## Next recommended action

`FIX_MV2_RESEARCH_SCOPE_DISTANCES_INSTRUMENT_RELATIVE_V1` — nur Wiring-Distances instrument-relativ
skalieren (ohne Generator-/Threshold-/Confirmation-Authority zu verdoppeln).

## Safety

Read-only Evidence. Kein Commit/Push/PR. Keine produktiven Dateien geändert.
Fremde untracked Evidence-Ordner und Stashes unverändert.
