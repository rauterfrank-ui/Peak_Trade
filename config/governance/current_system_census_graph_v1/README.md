# CURRENT System Census Graph V1

## What it is

`current_system_census_graph_v1` is a **navigation and evidence index** for the Peak_Trade system topology as established by the **CURRENT Complete System Census V1** forensic runs, navigation-rebound at architecture fixpoint baseline `d26caea78d1a178fde0a9e91aee169d454eebcae`.

It materializes:

- **301** census objects (package / infrastructure-surface granularity)
- **84** semantic system edges (not a Python import graph)
- Topology domains, WebSocket closure, intelligence topology, productive hot path, and authority-map reconciliation **as census evidence**

## What it is not

- **Not** a runtime authority source
- **Not** a decision or trading authority
- **Not** a universe ratification or replacement for the Master Runbook, Map of Truth, or canonical verifiers
- **Not** a substitute for the existing `current_system_interaction_authority_map_v1` (that map remains `AUTHORITY=NONE` navigation only)

If this graph conflicts with CURRENT code or canonical authority sources: **`GRAPH_LOSES=true`**.

## Authority

```text
artifact_kind=NAVIGATION_EVIDENCE_INDEX
AUTHORITY=NONE
MAP_AUTHORITY=NONE
RUNTIME_AUTHORITY=NONE
DECISION_AUTHORITY=NONE
```

## Object granularity

- `src&#47;<top-level-package>`
- `src&#47;ops&#47;<capability-package>`
- Explicit infrastructure surfaces (governance config tree, ops scripts tree, …)

## Semantic edges

Architecture / system handoffs (DATA, DECISION, CONSTRAINT, EVIDENCE, …).  
Does **not** include every Python import.

Edges are tagged `CODE_AND_MAP`, `CODE_ONLY`, `MAP_ONLY`, or `CONFLICTING` relative to the authority map at census time.

## Census provenance

- `census_phase_1_status=INCOMPLETE`
- `census_phase_2_status=COMPLETE`
- `investigation_completeness=COMPLETE`
- `taxonomy_status=OPEN_CURRENT` (universe vs plane vs boundary taxonomy not closed)

See `census_discrepancies` in `source_v1.json` for preserved epistemic mismatches from the census narrative.

## Future audit / Cursor workflow

1. Read `source_v1.json`.
2. Compare `git rev-parse HEAD` to `source_baseline_head`.
3. `git diff --name-only <source_baseline_head>..HEAD` against `objects[].paths` and `evidence_refs`.
4. Re-prove only impacted objects/edges.
5. **Never** treat unchanged graph records as runtime permission to trade, post, or activate capabilities.
6. Update this graph only through separate, evidence-backed governance work (not silent drift).

## Validation

```bash
python3 scripts/ops/validate_current_system_census_graph_v1.py
python3 scripts/ops/validate_current_system_census_graph_v1.py --check-head-drift
```

## Drift

No dedicated drift service. Path and evidence fields are sufficient to match git diffs to census records manually or with simple scripts.
