# TASK (Primary): Logical Gap Analysis → Implementation Plan
Input:
- docs/analysis/FEHLENDE_FEATURES_PEAK_TRADE.md
- out/ops/missing_features_prioritized.md
Deliverables:
1) Map missing features → existing modules/owners (src/*, docs/*), propose concrete file/module skeletons.
2) Define dependency DAG across: Feature-Engine, Streaming, Execution gates, Risk, Web, Infra, Research.
3) Propose 3 milestones (M0/M1/M2) with explicit acceptance criteria + tests.
4) Output as: docs/analysis/missing_features_plan.md
Constraints:
- No live trading enabling; preserve current gates.
- Prefer deterministic core + reproducible experiments.
