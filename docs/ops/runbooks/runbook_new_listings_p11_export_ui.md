# New Listings — P11 Export UI (WIP)

## Goal
Provide a minimal, read-only UI for browsing exported candidates (JSON/CSV) and inspecting the CEX risk + score heuristics output.

## Non-Goals
- No live trading.
- No write/delete operations.
- No authentication/roles yet (unless already present in stack).

## Entry Points
- Local dev: TBD
- **Artifacts location (P10):** `out&#47;research&#47;new_listings&#47;`
  - Candidates export: `candidates_{run_id}.json`, `candidates_{run_id}.csv`
  - Produced by: `python -m src.research.new_listings export --db <db> --out-dir out&#47;research&#47;new_listings [--run-id <id>]`
  - Pipeline: `run` → `risk` → `score` → `export` (see `test_p10_cex_risk_score_export.py`)

## P10 Export Schema (candidates JSON/CSV)
- `asset_id`, `symbol`, `risk_severity`, `score`, `first_seen_at`
- Source view: `v_assets_candidates`; joins `v_latest_risk`, `v_latest_score` (see `src&#47;research&#47;new_listings&#47;exporter.py`)

## Tasks
- [ ] Identify P10 export locations + schema(s) — **done** (see above)
- [ ] Decide UI surface (CLI TUI vs. small local web UI vs. static HTML report)
- [ ] Add renderer: table + filters + links to raw JSON/CSV
- [ ] Add snapshot build step into out&#47; (ignored)
- [ ] Add smoke test (render step produces expected files)

## Exit Criteria
- Deterministic render from a given export snapshot
- No network requirement
- Produces artifacts under out&#47; (gitignored)
