# Integrated Visual Models

All primary diagrams: `TEMPORAL_VIEW=CURRENT_ONLY`

## DIAGRAM_A — IU L00–L13
```text
L00→L01→L02→L03→L04→L05→L06→L07→L08
                              ├→L09 (dormant residency)
                              └→L10→L11→L12→L13
```

## DIAGRAM_B — IU + parallel planes
```text
[IU vertical] || P_DDO | P_GVEF_RU/OU/SL/MI | P_PROFILE | residency
```

## DIAGRAM_C — Populations
```text
U_CAP21 ⊃ U_S_STAR → ranked → U_TOP20 ; U_TOP20_RESIDENCY lifecycle (off)
```

## DIAGRAM_D — GVEF pipeline
```text
CorpusManifest→Registry→Gate→Context→DI→GenericRunner→Evaluator→Comparator/Constraints→EvidenceRegistry→PromotionEnvelope
```

## DIAGRAM_E — GV coverage
```text
DIRECT L07=vec-gvef-ru-mechanism-001 ; INDIRECT L05/L08 ; PTP registered lateral
```

## DIAGRAM_F — Authority
```text
Cap22 RANK ; Cap23 SELECT ; Cap24 BIND ; GV/GVEF/GHV AUTHORITY=NONE ; POST=false
```

## DIAGRAM_G/H — State/Config
See 11/12 registries (CURRENT vs labeled historical config residual).

## DIAGRAM_I — Productive path
```text
L12→L13→Full-Core→MV2/DP→Confirmation→NaturalEnter→PRE_EXTERNAL→HARD_STOP
```

## DIAGRAM_J — Transitive closure
IU core + GVEF offline + productive downstream to PRE_EXTERNAL.

## DIAGRAM_K — Provenance
See 23/24.

## DIAGRAM_L — Historical→Current evolution
Round4(6ed52d01) --supersede functional-path--> NE closure → CURRENT claims
K1 witness --carryforward--> CURRENT NE doc

## DIAGRAM_M — Current vs historical difference
CURRENT architecture counts use IU/GVEF@0316e9e20dd589e4b3b6e7d21941e3e217868eaf; Round3/4 edge inventories remain historical-labeled.
