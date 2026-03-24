# Workflow Officer v1 — Implementation Slice

## Scope

Extends Workflow Officer v0 with:

- Normalized **profile check plans** in `src&#47;ops&#47;workflow_officer_profiles.py` (per check: `check_id`, `command`, `severity`, `surface`, `category`, `description`).
- **Recommendation layer**: each check in `report.json` includes `recommended_action` and `recommended_priority` (`p0`–`p3`), derived deterministically from `effective_level`, `outcome`, and `severity`.
- **Schema** extended with required v1 fields and `summary.recommended_priority_counts`.
- **Markdown** sections: by priority, by category, recommended next actions (deterministic sort order).

## Guardrails

| Rule | Detail |
|---|---|
| Mode | `paper_stability_guard` — read-only orchestration |
| Mutation | No writes outside `out&#47;ops&#47;workflow_officer&#47;<ts>&#47;` for officer outputs |
| Data | No paper/shadow/evidence path changes |
| Authority | No live/runtime authority; no auto-remediation |

## Output contract

Each run writes a timestamped directory `out&#47;ops&#47;workflow_officer&#47;<ts>&#47;` with `report.json`, `summary.md`, `events.jsonl`, `manifest.json`, and per-check log files.

### Check fields (v1)

| Field | Description |
|---|---|
| `surface` | e.g. `docs`, `local_ops`, `pilot_preflight` |
| `category` | e.g. `documentation`, `environment`, `tooling` |
| `description` | Short operator-facing description |
| `recommended_action` | Static text; never implies auto-fix |
| `recommended_priority` | `p0`, `p1`, `p2`, or `p3` |

### Priority mapping (deterministic)

| Condition | Priority |
|---|---|
| `effective_level` = `error` | `p0` |
| `effective_level` = `warning` | `p1` |
| `effective_level` = `info` and not pass | `p2` |
| `effective_level` = `ok`, or `info` with pass | `p3` |

## Profiles

Unchanged names: `docs_only_pr`, `ops_local_env`, `live_pilot_preflight`.

## Acceptance

1. `python3 src/ops/workflow_officer.py --mode audit --profile docs_only_pr` exits 0 or 1 per existing rules.
2. `report.json` validates with extended schema; `officer_version` is `v1-min`.
3. `summary.md` includes **By priority**, **By category**, **Recommended next actions**.
4. Tests pass: `pytest -q tests/ops/test_workflow_officer*.py`.
