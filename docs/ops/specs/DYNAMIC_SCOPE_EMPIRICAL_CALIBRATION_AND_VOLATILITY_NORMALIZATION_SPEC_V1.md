---
title: "Dynamic Scope Empirical Calibration and Volatility Normalization Spec v1"
status: "RESEARCH_EVIDENCE_ONLY"
owner: "trading.master_v2.dynamic_scope_empirical_calibration_research_v1"
docs_token: "DOCS_TOKEN_DYNAMIC_SCOPE_EMPIRICAL_CALIBRATION_V1"
---

# Dynamic Scope Empirical Calibration v1 (Research)

```text
AUTHORITY=NONE
RUNTIME_AUTHORITY=NONE
PRODUCTIVE_D_T_FORMULA_SELECTED=false
MECHANICAL_CORE=execute_naked_mechanical_step_v1 (unchanged)
```

Research harness owner: `src/trading/master_v2/dynamic_scope_empirical_calibration_research_v1.py`

Candidate families (RESEARCH_CANDIDATE only):

- ABSOLUTE: D_t = k
- RELATIVE: D_t = k * M_t
- VOL_NORMALIZED: D_t = k * sigma_t * M_t (fail-closed when sigma invalid)

Volatility lineage for PT1M datasets: `canonical_volatility_estimate_materializer_v1` /
rolling std of finalized mark log returns (60-bar window).

No productive binding. No integrated replay mutation.
