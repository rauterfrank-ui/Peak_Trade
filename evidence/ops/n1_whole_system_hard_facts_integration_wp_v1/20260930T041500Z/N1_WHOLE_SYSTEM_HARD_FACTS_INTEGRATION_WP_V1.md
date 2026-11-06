# N=1 Whole-System Hard-Facts Integration WP V1

## Baseline

| Field | Value |
|-------|-------|
| BASELINE_SHA | `f1288b2a289b0cf21c85c746e92e62ee74bc871e` |
| BRANCH | `feat/n1-whole-system-hard-facts-integration-v1` |
| PRE_IMPLEMENTATION_OWNER_CLOSURE | CLOSED |
| RW_PUB_G5_OWNER_CLOSURE | OPTION_A_EEA_ONLY_PRODUCTIVE |
| RW_E6_OWNER_CLOSURE | PROVEN_CURRENT_COMPOSED_OWNER_CHAIN |

## Backlog matrix (26 rows)

| Row | Status |
|-----|--------|
| RW-PUB-G1 | CLOSED |
| RW-PUB-G5 | CLOSED |
| RW-PUB-G9 | CLOSED |
| RW-E1 | CLOSED |
| RW-E2 | CLOSED |
| RW-E3 | CLOSED |
| RW-E4 | CLOSED |
| RW-E5 | CLOSED |
| RW-E6 | CLOSED |
| RW-E7 | CLOSED |
| RW-E8 | CLOSED |
| RW-E9 | CLOSED |
| RW-E10 | CLOSED |
| RW-E11 | CLOSED |
| RW-E12 | CLOSED |
| RW-E13 | CLOSED |
| RW-E14 | CLOSED |
| RW-E15 | CLOSED |
| RW-E16 | CLOSED |
| RW-E17 | CLOSED |
| RW-E18 | CLOSED |
| RW-E19 | CLOSED |
| RW-E20 | CLOSED |
| RW-E21 | CLOSED |
| RW-E22 | CLOSED |
| RW-E23 | CLOSED |

Machine-readable admission: `PRE_EXTERNAL_AUTONOMY_ADMISSION_V1.json`

## Integration package

`src/ops/n1_whole_system_hard_facts_integration_wp_v1/` composes existing canonical owners (public MD runtime, Economic-MD, hard-facts closure, private account runtime, order lifecycle, recovery ordering) through PRE_EXTERNAL only.

## Safety (unchanged)

`POST_ALLOWED=false`, `EXTERNAL_EFFECT_AUTHORIZED=false`, `REAL_VENUE_POST_ALLOWED=false`, PRE_EXTERNAL terminal, `POST_COUNT=0`.

## Tests

`tests/ops/test_n1_whole_system_hard_facts_integration_wp_v1.py` plus prior focused ops baseline (economic MD, public MD runtime, hard-facts closure, productive cap paths).
