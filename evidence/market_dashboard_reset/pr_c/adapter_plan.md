# PR-C Adapter Plan

## Placement

`src/webui/market_dashboard_readmodels_v1/adapters/`

Dependency rules preserved:
- Domain modules do not import adapters
- Adapters do not import Flask/Jinja/templates
- Adapters do not call replay/composition evaluate functions
- Adapters accept explicit already-produced sources (duck-typed)
- No network I/O / runtime activation

## Binding classifications (post-discovery resolution)

| Contract | Classification | Adapter |
|---|---|---|
| MarketInstrumentSnapshotV1 | BINDABLE_WITH_EXPLICIT_UNAVAILABLE_FIELDS | market.py |
| MarketRankingSnapshotV1 | BINDABLE_WITH_EXPLICIT_UNAVAILABLE_FIELDS | ranking.py |
| CanonicalDecisionSummaryV1 | BINDABLE_WITH_EXPLICIT_UNAVAILABLE_FIELDS | canonical_decision.py |
| DoublePlayDecisionSnapshotV1 | BINDABLE_WITH_EXPLICIT_UNAVAILABLE_FIELDS | double_play.py |
| SafetyAuthoritySnapshotV1 | SOURCE_NOT_BOUND | safety_authority.py → NOT_BOUND/unavailable unless pre-consolidated mapping |
| ExecutionStateSnapshotV1 | BINDABLE_WITH_EXPLICIT_UNAVAILABLE_FIELDS | execution.py (fill=NOT_PROVIDED) |
| EconomicSummarySnapshotV1 | BINDABLE_WITH_EXPLICIT_UNAVAILABLE_FIELDS | economic.py |
| DiagnosticsSummarySnapshotV1 | BINDABLE_LOSSLESS | diagnostics.py (support bundle only) |
| DashboardFreshnessSnapshotV1 | BINDABLE_WITH_EXPLICIT_UNAVAILABLE_FIELDS | freshness.py + freshness_policy.py |

Ambiguity resolution before implementation:
- Safety: no consolidated owner → SOURCE_NOT_BOUND (not SOURCE_AMBIGUOUS composer)
- Diagnostics: sole canonical owner = offline productive linear diagnostics support bundle
- Execution: single owner EntryExitPolicyDecisionV0; missing fill remains NOT_PROVIDED

SOURCE_AMBIGUITY_COUNT=0
FORBIDDEN_INFERENCE_COUNT=0

## Out of scope

- Page aggregate / presenter wiring (PR-D)
- Active GET /market route changes
- Core trading / DP / risk / execution semantics
