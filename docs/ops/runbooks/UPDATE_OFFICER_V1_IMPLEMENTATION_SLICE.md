# Update Officer v1 – Implementation Slice

## Goal

Extend Update Officer v0 with deterministic operator recommendations and richer
metadata while staying **read-only**, **deterministic**, and free of network or
package mutations.

## Scope

### Added in v1

1. **Finding metadata**
   - `category` — operational grouping (from profile surface metadata)
   - `description` — short operator-facing description of the scanned item
   - `recommended_action` — static string; never implies auto-fix
   - `recommended_priority` — `p0` … `p3`

2. **Recommendation layer**
   - Deterministic mapping from `classification` × `surface` to priority and action
   - `blocked` on `pyproject.toml` (runtime-adjacent list) → `p0`
   - `blocked` on `github_actions` → `p1`
   - `manual_review` on `github_actions` → `p1`
   - `manual_review` on `pyproject.toml` → `p2`
   - `safe_review` → `p3`

3. **Summary**
   - Preserves v0 classification counts
   - Adds `priority_counts` (`p0`–`p3`)
   - Adds `category_counts` (per category string)

4. **Markdown**
   - By classification, priority counts, category counts
   - Sections: by priority, by category, recommended next actions, findings table

5. **Profiles**
   - `dev_tooling_review` unchanged in behavior; `surface_metadata` documents
     categories and description templates per surface

### Unchanged from v0

- Surfaces: `pyproject.toml`, `github_actions`
- Classifications: `safe_review`, `manual_review`, `blocked`
- No dependency bumps, lockfile writes, or installs
- Outputs only under `out&#47;ops&#47;update_officer&#47;<ts>&#47;`

## Guardrails

- Mode: `paper_stability_guard`
- Read-only scout; no paper/shadow/evidence mutation
- No live/runtime authority
- No autonomous updates
- No WebUI in this slice

## Deliverables (code)

- `src&#47;ops&#47;update_officer.py` — enrichment + summary
- `src&#47;ops&#47;update_officer_profiles.py` — surface metadata
- `src&#47;ops&#47;update_officer_schema.py` — v1 fields + counts
- `src&#47;ops&#47;update_officer_markdown.py` — extended summary
- `tests&#47;ops&#47;test_update_officer.py` (and schema/markdown tests)

## Acceptance

- `officer_version` is `v1-min`
- Every finding carries v1 metadata fields
- Schema rejects invalid priorities or missing summary count keys
- Markdown includes by-priority, by-category, and recommended-actions sections
- Tests pass; docs token policy satisfied for this runbook
