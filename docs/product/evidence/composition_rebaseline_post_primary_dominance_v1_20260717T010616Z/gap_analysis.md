# Prioritized Gap List — Post PR #5260 Rebaseline

| GAP_ID | OBSERVED_EVIDENCE | RUNBOOK_REQUIREMENT | GLOBAL_COMPOSITION_IMPACT | USER_OR_OPERATOR_IMPACT | ROOT_CAUSE_OWNER | CANDIDATE_FILES | RISK | ESTIMATED_SCOPE | ALREADY_COVERED_BY_PREVIOUS_SLICE | ELIGIBLE_AS_NEXT_BOUNDED_SLICE |
|---|---|---|---|---|---|---|---|---|---|---|
| GAP_LANDMARK_VERTICAL_RHYTHM | Primary→Decision gap 2px; Decision→Obs 12px; stages abut | Composition-first; clear stage bands; scan pauses between landmarks | **Highest** remaining full-page composition defect after mass fix | Abrupt fold transition; no visual pause between Primary and Decision | CSS landmark margins / decision-section-gap reused as landmark margin | `peak_trade_dashboard_layout_v1.css`, `design_tokens_v1.css`, `market_v0.html` | L | S | false (PR#5260 was page-share mass) | **true — SELECTED** |
| GAP_DECISION_INTERNAL_HIERARCHY | Top20 322 / Funnel 233 / Secondary 230 nearly peer; 16 bordered containers | Clear hierarchy inside Decision Surface | High | Long tabular fatigue after first scroll | Decision module presentation density | Decision partials + layout CSS | M | M | partial (compression/dominance densified but hierarchy still flat) | true (defer — larger than rhythm) |
| GAP_ABOVE_FOLD_DECISION_TIP | DECISION_SURFACE visible_px=0 @1440; hero decision sentence partially present | Faster authority/blocker glance before full scroll | Medium | Must scroll to enter Decision landmark | Landmark start Y / fold geometry | Primary/Decision shell CSS | M | S | false | true (defer — tip risk as third focus) |
| GAP_SECONDARY_PANEL_DENSITY | Watchlist/F5/DP/Safety equal ~230px peers | Secondary subordinate to Decision primary modules | Medium | Competing glanceables; redundant Safety cues | Secondary grid presentation | secondary grid partials + CSS | M | M | partial densify in #5260 | true (defer) |
| GAP_OBSERVABILITY_PLACEHOLDER_CALM | Economic NOT_COMPUTED / MISSING_SOURCE sparse look | Observability intentionally secondary, not broken-sparse | Medium-low | Late-scroll polish | Observability empty-state presentation | economic observability partial + CSS | M | M | false | true (defer — lower ROI) |
| GAP_PRIMARY_PAGE_SHARE | Primary 38.9 > Decision 32.7 | Primary dominant full-page mass | Resolved | — | — | — | — | — | **true (PR #5260)** | false — do not repeat |

## Selection

```text
SELECTED_NEXT_SLICE=COMPOSITION_LANDMARK_VERTICAL_RHYTHM_V1
REPEATS_PR5260_SCOPE=false
RATIONALE=Highest remaining global composition gain after Primary dominance; measurable inter-landmark gaps; template/CSS only; previously P1-authorized after compression rebaseline.
```
