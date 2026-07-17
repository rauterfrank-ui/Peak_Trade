# Composition Plan — Engineering Drawer Deemphasis v1

## Defect
Closed Engineering drawer still attracts attention via three peer bordered details,
Diagnostics summary at 14px/slate-400, and ~5% page share.

## Goal
Engineering tertiary and unobtrusive while closed; Primary/Decision/Observability hierarchy held.

## Approach
1. Mark Engineering landmark as tertiary deemphasis.
2. Replace peer card chrome with separator-style closed details.
3. Quiet Diagnostics summary to 10px/slate-600; remove heavy borders/background.
4. CSS densify closed padding/gaps; preserve landmark rhythm 8/20/20/20.
5. No producer/authority changes.

## Acceptance
ENGINEERING_DRAWER_DEEMPHASIS_PASS across 1280/1440/1728; prior hierarchy gates held.
