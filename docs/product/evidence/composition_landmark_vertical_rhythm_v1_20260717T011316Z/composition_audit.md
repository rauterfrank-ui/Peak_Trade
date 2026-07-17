# Composition Audit — Landmark Vertical Rhythm v1

## Intent

Introduce intentional inter-landmark breathing so Header → Primary → Decision → Observability → Engineering read as discrete bands after Primary page-share dominance was restored by PR #5260.

## Scope

Template/CSS presentation only. No ViewModel, producer, Master V2, Double Play, or authority changes.

## Measured after @1440×900

- Gaps: Header→Primary 8 · Primary→Decision 20 · Decision→Obs 20 · Obs→Eng 20
- Page shares: Primary 38.8% · Decision 32.6%
- Chart VP share: 62.05555555555556
- Page height: 2422 (before 2413)

## Non-goals preserved

- REPEATS_PR5260_SCOPE=false (no page-share mass levers)
- CORE_FILES_CHANGED=false
- BUSINESS_LOGIC_CHANGED=false
- SECOND_TRUTH_CREATED=false
