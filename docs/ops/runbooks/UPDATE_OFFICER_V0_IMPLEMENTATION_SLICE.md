# Update Officer v0 — Implementation Slice

## Scope

Minimal **read-only, deterministic** update scout for `Peak_Trade`.
Inspects pinned/ranged dev-tooling dependencies and GitHub Actions references,
classifies each finding, and emits a structured report under
`out&#47;ops&#47;update_officer&#47;<ts>&#47;`.

No network calls, no package mutations, no paper/shadow/evidence interaction.

## Guardrails

| Rule | Detail |
|---|---|
| Mode | `paper_stability_guard` — read-only scout only |
| Mutation | No writes outside `out&#47;ops&#47;update_officer&#47;<ts>&#47;` |
| Data isolation | No mutation of paper/shadow/evidence data or runs |
| Dependencies | No dependency bumping, no lockfile changes, no package installation |
| Network | No network calls required |
| Patterns | Reuse Workflow Officer patterns where practical |

## Output Contract

Each run produces a timestamped directory `out&#47;ops&#47;update_officer&#47;<ts>&#47;` containing:

| File | Format | Purpose |
|---|---|---|
| `report.json` | JSON | Full structured report with findings + summary |
| `summary.md` | Markdown | Human-readable summary |
| `events.jsonl` | JSONL | One event per finding |
| `manifest.json` | JSON | List of emitted files with sizes |

### Report shape

```json
{
  "officer_version": "v0-min",
  "profile": "dev_tooling_review",
  "started_at": "<ISO 8601>",
  "finished_at": "<ISO 8601>",
  "output_dir": "<path>",
  "repo_root": "<path>",
  "success": true,
  "findings": [ ... ],
  "summary": { ... }
}
```

### Finding fields

| Field | Type | Description |
|---|---|---|
| `surface` | string | Source: `pyproject.toml` or `github_actions` |
| `item_name` | string | Package name or action reference |
| `current_spec` | string | Version spec as declared |
| `classification` | enum | `safe_review`, `manual_review`, or `blocked` |
| `reason` | string | Why this classification was assigned |
| `notes` | list[str] | Optional extra notes |

### Summary fields

| Field | Type |
|---|---|
| `total_findings` | int |
| `safe_review` | int |
| `manual_review` | int |
| `blocked` | int |

## Profile: `dev_tooling_review`

### Surfaces

1. **pyproject.toml** — parse `[project.optional-dependencies].dev` and `[dependency-groups].dev`
   for dev-tooling package pins and ranges.
2. **GitHub Actions** (optional) — scan `.github&#47;workflows&#47;*.yml` for `uses:` lines
   referencing actions with version pins.

### Classification semantics

| Classification | Criteria |
|---|---|
| `safe_review` | Recognized dev/test/lint/format/doc tooling with clear pin (e.g. `ruff`, `pytest`, `black`, `mypy`, `pyright`, `pre-commit`, `pytest-cov`) |
| `manual_review` | Broad ranges, missing pin clarity, GitHub actions without version pin, unknown tooling bucket |
| `blocked` | Execution/live/risk/policy/runtime-adjacent packages (e.g. `fastapi`, `uvicorn`, `ccxt`, `prometheus-client`) |

### Known dev-tooling packages (safe bucket)

`pytest`, `pytest-cov`, `ruff`, `black`, `mypy`, `pyright`, `pre-commit`,
`pip-audit`, `httpx` (test client), `tomli` (stdlib backfill).

## Minimal Acceptance Criteria

1. `python3 src&#47;ops&#47;update_officer.py --profile dev_tooling_review` exits 0
2. `report.json` passes schema validation
3. `summary.md` contains header, run metadata, summary counts, findings table
4. `events.jsonl` has one line per finding
5. `manifest.json` lists all output files
6. All tests pass: `pytest -q tests&#47;ops&#47;test_update_officer*.py`
7. No mutation outside `out&#47;ops&#47;update_officer&#47;<ts>&#47;`
8. No network dependency
