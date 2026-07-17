# Post-Hierarchy Composition Rebaseline v1

Slice completed on main: `COMPOSITION_DECISION_SURFACE_HIERARCHY_V1` (PR #5263)  
Feature commit: `d689d087d65a487e9506ae5685c5f0b638a9e62e`  
Docs policy fix: `1bf80e7615285541485a9ae7ca9ec77fe3875813`  
Merge: `301c50f28a824fe2f03e2561a5b0903e772d01d8`  
Browser: `GOOGLE_CHROME` · REAL_CHROME_VERIFIED=true · CHROMIUM_FALLBACK_USED=false

## Held gates (@1440×900)

| Gate | Result |
|---|---|
| Landmark order | PASS |
| Horizontal overflow | PASS |
| Primary chart dominance | PASS (Primary 39.2% > Decision 32.0%) |
| Top-20 > Funnel > Secondary | PASS (354.5 / 216.2 / ≤152) |
| Decision frames | 3 (held) |
| Rhythm gaps | 8/20/20/20 |
| Engineering secondary/closed | PASS |
| Read-only / no BTC / no orders | PASS |

## Remaining gap (authorized next)

`COMPOSITION_OBSERVABILITY_SURFACE_HIERARCHY_V1` — Economic observability primary > Linear diagnostics secondary; reduce peer-card chrome inside Observability.

Status: `AUTHORIZED_NOT_IMPLEMENTED`  
`DASHBOARD_PROJECT_COMPLETE=false`
