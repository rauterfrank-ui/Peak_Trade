# Prioritized Next Composition Slices

Evidence: `composition_rebaseline_post_decision_compression_v1_20260717T004021Z`
HEAD: `8fa865061e671d065e93ad5619ce263b91c46fee`
Baseline: post `COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1`

Effort: S ≤0.5d · M ≈0.5–1.5d · L >1.5d  
Risk: L / M / H (presentation regression + operator scan risk)  
Visual gain: relative composition impact on full-page hierarchy

---

## P0 — Recommended next

### `COMPOSITION_PRIMARY_PAGE_SHARE_DOMINANCE_V1`

**Intent:** Flip full-page mass so Primary ≥ Decision (target Primary page share ≥ Decision by ≥2 pp @1440), by further collapsing Decision *secondary* modules (funnel visual + compact 3-panel grid), without touching Top-20 eligibility semantics or Primary chart chrome.

**Why now:** Compression met prior caps (Decision ≤40%, Obs Y ≤2200) but left Decision as the heaviest landmark (39.1% vs Primary 34.2%). This is the largest remaining composition defect.

| | |
|---|---|
| **Effort** | M |
| **Risk** | M — over-collapse could hide Safety/Double-Play glanceables; mitigate by keeping Blocked summary + Top-20 primary, densify/collapse secondary only |
| **Expected visual gain** | **High** — Primary becomes full-page #1; Observability start Y likely ≤1850; Decision wall shortens after first scroll |

**Measurable targets @1440×900 (Chrome full-page):**

| Metric | Now | Target |
|---|---:|---:|
| PRIMARY page share | 34.2% | ≥ Decision share + 2 pp |
| DECISION page share | 39.1% | ≤ 34% |
| DECISION height | 1006 | ≤ 850 |
| OBSERVABILITY start Y | 2007 | ≤ 1850 |
| Chart viewport share | 55.4% | ≥ 40% (no regression) |
| Engineering VP share | 0% | < 15% |
| Overflow / landmark order | PASS | PASS |

**Scope:** templates/CSS inside DECISION_SURFACE only (funnel + secondary grid density / optional collapsed details). No producers, no SSOT, no Engineering feature work, no chart redesign.

**Explicitly excluded:** Observability content redesign, ranking data contracts, Master Runbook mutation, runtime activation.

---

## P1

### `COMPOSITION_LANDMARK_VERTICAL_RHYTHM_V1`

**Intent:** Introduce intentional inter-landmark breathing (Primary→Decision, Decision→Observability) via spacing tokens so stages read as discrete bands rather than abutting slabs.

| | |
|---|---|
| **Effort** | S |
| **Risk** | L — may slightly increase page height; keep gaps bounded (e.g. 16–28 px) |
| **Expected visual gain** | **Medium** — clearer stage separation and scan pauses; does not alone fix Decision mass |

Depends on / pairs well after P0 (rhythm after mass fix).

---

### `COMPOSITION_ABOVE_FOLD_DECISION_STATUS_TIP_V1`

**Intent:** Ensure @1440×900 a thin Decision status tip (Blocked + primary blocker) peeks in the initial viewport without stealing chart dominance (Decision visible_px target 48–96; chart VP share still ≥45%).

| | |
|---|---|
| **Effort** | S |
| **Risk** | M — tip can become a third competing focus if oversized |
| **Expected visual gain** | **Medium** — faster authority/blocker glance before first full scroll |

Note: @1728 tip already partially visible; @1440 Decision starts at Y≈989 (just below fold).

---

## P2

### `COMPOSITION_OBSERVABILITY_PLACEHOLDER_CALM_V1`

**Intent:** Presentation-only calm for Observability empty/NOT_COMPUTED states so the landmark feels intentionally secondary rather than broken-sparse (spacing, typography, muted empty rows — **no new metrics owners**).

| | |
|---|---|
| **Effort** | M |
| **Risk** | M — must not invent economic claims or second truth |
| **Expected visual gain** | **Medium-low** — improves late-scroll polish; does not fix Primary/Decision mass |

---

### `COMPOSITION_DECISION_MATRIX_ROW_WINDOW_V1`

**Intent:** Further constrain Top-20 matrix visible row window / max-height tokens if P0 secondary collapse is insufficient alone.

| | |
|---|---|
| **Effort** | S |
| **Risk** | M — operator may need scroll-inside-matrix more often |
| **Expected visual gain** | **Medium** — direct Decision height reduction; only if P0 misses targets |

Treat as fallback/extension of P0, not a parallel first slice.

---

## Not recommended as next slice

| Slice idea | Why defer |
|---|---|
| Chart candle / chrome polish | Above-fold dominance already PASS; low composition ROI |
| Engineering Drawer expansion | Already correctly secondary |
| Observability content / producer work | Out of composition-presentation scope; risk of second truth |
| Sticky header / sticky Decision | Higher interaction risk; not needed for landmark order |
| Full Observability elevation above Decision | Violates landmark order SSOT |

---

## Authorization posture (this rebaseline)

```text
COMPOSITION_BASELINE_UPDATED=true
IMPLEMENTED_SLICE=COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1
NEXT_RECOMMENDED_SLICE=COMPOSITION_PRIMARY_PAGE_SHARE_DOMINANCE_V1
NEXT_AUTHORIZED_SLICE=COMPOSITION_PRIMARY_PAGE_SHARE_DOMINANCE_V1
NOTE=Operator GO granted for COMPOSITION_PRIMARY_PAGE_SHARE_DOMINANCE_V1
```
