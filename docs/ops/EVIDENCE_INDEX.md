# Peak_Trade – Evidence Index (v0)

**Scope:** Living operational artifact for tracking evidence items related to CI runs, drills, tests, incidents, and process artifacts.  
**Purpose:** Centralized index for nachvollziehbarkeit (traceability) of operational evidence—NOT a compliance claim.  
**Owner:** ops  
**Status:** v0 (Initial)

---

## How to Add Evidence

**What is Evidence?**
Evidence items are operational artifacts that document system behavior, process execution, or decision-making. Examples:
- CI workflow run (GitHub Actions URL)
- PR merge + merge-log doc
- Test output (pytest result, coverage report)
- Drill session log (NO-LIVE drill, smoke test)
- Incident postmortem or RCA doc
- Config snapshot (e.g., required checks snapshot)

**Minimal Fields per Entry:**
- **Evidence ID:** Unique identifier (e.g., `EV-001`, `EV-YYYYMMDD-<name>`)
- **Date:** ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`)
- **Owner:** Responsible party (username, team, or role)
- **Source Link:** URL (GitHub PR/run/commit) or repo path (`docs/ops/...`)
- **Claim:** What this evidence demonstrates (brief, factual)
- **Verification:** How to verify authenticity (hash, CI status, reproducible command)
- **Notes:** Optional context or caveats

**Format:** Prefer table format (below) for consistency. Fehlende Details als `[TBD]` markieren, NICHT als freies TODO.

---

## Evidence Registry

| Evidence ID | Date | Owner | Source Link | Claim / What It Demonstrates | Verification | Notes |
|-------------|------|-------|-------------|------------------------------|--------------|-------|
| EV-20260107-SEED | 2026-01-07 | ops | [PR #596 Merge Log](PR_596_MERGE_LOG.md) | Placeholder policy v0 merged with CI green | GitHub PR status: merged, checks passed | Seed entry (example); no live trading claim |

---

## Evidence by Category

### CI / Workflow Evidence
- **EV-20260107-SEED** — Placeholder standards PR (example seed entry)

### Drill / Operator Evidence
- [TBD] — Future drill evidence items hier eintragen

### Incident / RCA Evidence
- [TBD] — Incident postmortems hier verlinken

### Config Snapshot Evidence
- [TBD] — Required checks, branch protection snapshots

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-07 | v0 Initial — 1 seed entry (PR #596 example) | ops |

---

**Version:** v0  
**Maintained by:** ops  
**Last Updated:** 2026-01-07  
**Next Review:** [TBD] (recommend quarterly or pre-phase-gate)
