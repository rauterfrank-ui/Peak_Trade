# Workflow Officer v1 – Implementation Slice

## Goal

Extend Workflow Officer from v0 to v1 by improving operator usefulness
without changing the safety posture. All changes are additive; core behavior
remains read-only and deterministic.

## Scope

### Added in v1

1. **Profile-specific check plans as first-class data**
   - Normalized profile definitions in `workflow_officer_profiles.py`
   - Each check entry carries explicit metadata:
     `check_id`, `command`, `severity`, `surface`, `category`, `description`

2. **Canonical report schema enrichment**
   - All v0 fields preserved
   - New stable fields per check:
     `surface`, `category`, `description`, `recommended_action`, `recommended_priority`
   - New summary fields: `priority_counts`, `category_counts`

3. **Recommendation layer**
   - Deterministic mapping from `effective_level` × `outcome` to:
     - `recommended_priority` ∈ {`p0`, `p1`, `p2`, `p3`}
     - `recommended_action` (static operator-facing string)
   - Mapping rules:
     - `effective_level == error` → `p0`
     - `effective_level == warning` → `p1`
     - `effective_level == info` and `outcome == fail` → `p2`
     - `effective_level == ok` or `effective_level == info` and `outcome != fail` → `p3`
   - Actions are always informational; never auto-fix.

4. **Markdown renderer upgrade**
   - Priority summary section
   - Category summary section
   - Operator recommended actions table

### Unchanged from v0

- Runtime authority: none
- Mutation behavior: none
- Paper/shadow/evidence paths: untouched
- Autonomous fixing: forbidden
- Output location: `out&#47;ops&#47;workflow_officer&#47;<ts>&#47;`

## Guardrails

- Mode: `paper_stability_guard`
- Read-only orchestration only
- No mutation of paper/shadow/evidence data or runs
- No live/runtime authority
- No auto-remediation
- No network dependency
- No new package installs

## Recommendation Model

| effective_level | outcome   | priority | recommended_action                                          |
|-----------------|-----------|----------|-------------------------------------------------------------|
| error           | fail      | p0       | Investigate and resolve immediately before proceeding       |
| error           | missing   | p0       | Locate or restore missing check target before proceeding    |
| warning         | fail      | p1       | Review and address before next deployment                   |
| warning         | missing   | p1       | Locate missing check target or update profile               |
| info            | fail      | p2       | Review when convenient                                      |
| info            | missing   | p2       | Consider restoring missing check target                     |
| ok              | pass      | p3       | No action required                                          |
| info            | pass      | p3       | No action required                                          |

## Profile Metadata Model

Each check entry in a profile carries:

| Field         | Type   | Description                                |
|---------------|--------|--------------------------------------------|
| `check_id`    | str    | Unique identifier for the check            |
| `command`     | list   | Command to execute                         |
| `severity`    | str    | `hard_fail` / `warn` / `info`              |
| `surface`     | str    | `docs` / `codebase` / `local_env` / `runtime` |
| `category`    | str    | Operational category for grouping          |
| `description` | str    | Human-readable description                 |

## Deliverables

- `src&#47;ops&#47;workflow_officer.py` — extended with recommendation layer
- `src&#47;ops&#47;workflow_officer_profiles.py` — normalized rich profile definitions
- `src&#47;ops&#47;workflow_officer_schema.py` — extended schema validation
- `src&#47;ops&#47;workflow_officer_markdown.py` — extended renderer
- `tests&#47;ops&#47;test_workflow_officer.py` — extended
- `tests&#47;ops&#47;test_workflow_officer_schema.py` — extended
- `tests&#47;ops&#47;test_workflow_officer_markdown.py` — extended

## Acceptance Criteria

- v0 functional behavior remains intact (read-only, deterministic, no mutation)
- v1 reports include deterministic recommendation fields on every check
- Schema validation covers all new fields with enum constraints
- Markdown summary reflects priority/category breakdowns
- All tests pass
- No docs token policy drift
