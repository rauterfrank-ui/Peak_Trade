# Operator Decision — OBL_B07

```text
OPERATOR_OPTION=OPTION_EVENT_ONLY
```

## Chosen

Bollinger remains a **direction-neutral Entry&#47;Exit event producer**.

## Explicitly not authorized

| Option | Status |
|--------|--------|
| LONG_ONLY | **not authorized** |
| SYMMETRIC_SHORT_GEOMETRY | **not authorized** |
| SHORT_ENTRY | **not authorized** |
| Classic-LONG as Strategy Intent | **not authorized** |
| Generic sign→direction heuristic | **not authorized** |

## Direction / Side

| Field | Value |
|-------|-------|
| Bollinger Direction | **unratifiziert** (`NONE`) |
| Entry Side | `NONE` |

## Follow-on rule

A later Direction ratification requires:

1. a **separate Operator-GO**, and
2. a **separate Strategy-Design slice**

This slice does not pre-authorize either.

## Parent chain

- OBL_B05 Decision C: `CONTRACT_REMAINS_AMBIGUOUS` (side)
- OBL_B05 Operator selection: `OPTION_D_REMAIN_FAIL_CLOSED`
- OBL_B06 audit: semantics unconfirmed for LONG&#47;SHORT; `-1=EXIT` confirmed
- OBL_B07: EVENT_ONLY geometry ratified; side remains fail-closed `NONE`
