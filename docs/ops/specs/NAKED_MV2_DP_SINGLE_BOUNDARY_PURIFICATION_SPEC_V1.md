---
title: "Naked MV2+DP Single-Boundary Purification Spec v1"
status: "OWNER_SPEC_IMPLEMENTATION_BOUND"
owner: "trading.master_v2.naked_mv2_dp_single_boundary_purification_v1"
docs_token: "DOCS_TOKEN_NAKED_MV2_DP_SINGLE_BOUNDARY_PURIFICATION_SPEC_V1"
---

# Naked MV2+DP Single-Boundary Purification Spec v1

Normative owner SSOT for the naked Dynamic Scope decision path. Initial Entry
remains `OUT_OF_SCOPE_SEPARATE_CENSUS`.

```text
RULE_CLASS=C_VOLATILITY_NORMALIZED_SINGLE_BOUNDARY (architecture)
BOUNDARY_COUNT=1
CALIBRATION_DIRECTION_AUTHORITY=OPEN
NUMERIC_FORMULA_AUTHORITY=NONE
M_t=CURRENT trusted finalized CMC mark_price (NULLLINE, direction-neutral)
R_t=scope-internal reference for counter-move only (not NULLLINE)
YELLOW=BOUNDARY_REACHED_CONFIRMATION_PENDING
PRE_BOUNDARY_PROXIMITY_PHI=NONE
HISTORICAL_50_500_AUTHORITY=NONE
HISTORICAL_80_120_200_AUTHORITY=NONE
MODEL_C_AUTHORITY=NONE
```

**Owner correction:** `D_t = σ_t * M_t` (DIRECT_VOL monotonicity) is **not** authorized
productive calibration. Inverse sensitivity (high vol → tighter scope) is under
investigation only — no formula until Owner adjudication.

Implementation owners:
- Primitives: `src/trading/master_v2/naked_mv2_dp_single_boundary_purification_v1.py`
- Isolated mechanical step: `src/trading/master_v2/naked_mv2_dp_mechanical_core_v1.py`

Productive binding: **none in v1 mechanical isolation** (explicit external `D_t` only; no integrated replay owner).

This spec does **not** re-open Clean Core closure as proof of unrelated semantics;
it defines the **naked** switch path only.
