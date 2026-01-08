# Peak_Trade – Evidence Entry Schema (v0.2)

**Purpose:** Canonical schema for evidence entries in the Evidence Index.  
**Owner:** ops  
**Status:** v0.2 (Operational)

---

## Evidence ID Format

**Pattern:** `EV-YYYYMMDD-<TAG>`

**Rules:**
- `YYYYMMDD` = ISO 8601 date (year-month-day, no separators)
- `<TAG>` = Uppercase alphanumeric + hyphens, 2–20 chars (e.g., `SEED`, `P0-BASELINE`, `PR518`)
- **Uniqueness:** Each ID must be unique across the entire Evidence Index

**Valid Examples:**
- `EV-20260107-SEED`
- `EV-20260107-P0-BASELINE`
- `EV-20260103-CI-HARDENING`

**Invalid Examples:**
- `EV-2026-01-07-SEED` (wrong date format, use YYYYMMDD)
- `EV-20260107` (missing TAG)
- `ev-20260107-seed` (must be uppercase)

---

## Categories (Enum)

Evidence entries must belong to ONE of these categories:

1. **CI/Workflow** — CI runs, GitHub Actions, workflow automation
2. **Drill/Operator** — NO-LIVE drills, smoke tests, operator sessions
3. **Test/Refactor** — Test suite runs, refactoring evidence, coverage reports
4. **Incident/RCA** — Postmortems, root cause analysis, incident logs
5. **Config Snapshot** — Configuration snapshots, policy state captures

**Note:** Category names are case-insensitive in Evidence Index (use consistent capitalization for readability).

---

## Mandatory Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Evidence ID** | Unique identifier (see ID Format above) | `EV-20260107-SEED` |
| **Date** | ISO 8601 date (`YYYY-MM-DD`) | `2026-01-07` |
| **Owner** | Responsible party (username/team/role) | `ops`, `@username`, `team-sre` |
| **Source Link** | URL or repo path (prefer relative paths) | `[PR #596](https://github.com/org/repo/pull/596)` or `[docs/ops/PR_596_MERGE_LOG.md](PR_596_MERGE_LOG.md)` |
| **Claim** | What this evidence demonstrates (1–2 sentences, factual) | "Phase 0 Multi-Agent Roleplay complete: 5/5 gate criteria passed, 6079 tests discovered" |
| **Verification** | How to verify authenticity (hash, CI status, command) | "pytest 8.4.2, Python 3.9.6, workspace CLEAN" |
| **Notes** | Optional context, caveats, or risk notes | "Seed entry (example); no live trading claim" |

---

## Optional Fields

- **Related PRs:** Comma-separated PR numbers (e.g., `#512, #514, #515`)
- **Commit SHA:** Short SHA (7–8 chars) or full SHA (40 chars)
- **Risk Level:** LOW / MEDIUM / HIGH (if applicable)
- **Status:** DRAFT / VERIFIED / ARCHIVED (default: VERIFIED)

---

## Link Conventions

**Prefer relative paths** for repo-internal references:
- ✅ `[PR_596_MERGE_LOG.md](PR_596_MERGE_LOG.md)` (relative to `docs/ops/`)
- ✅ Example from `docs/ops/evidence/`: `[config/bounded_live.toml](../../../config/bounded_live.toml)` <!-- pt:ref-target-ignore -->
- ⚠️ GitHub URLs: Use for external references only (e.g., PR URLs, workflow run URLs)

**Important:** Evidence entries in `docs/ops/evidence/` are **3 levels deep** from repo root.
- To link to repo-root files (e.g., `config/`, `.github/workflows/`, `scripts/`), use `../../../` prefix
- Example: `[ci.yml](../../../.github/workflows/ci.yml)` <!-- pt:ref-target-ignore -->
- See [EVIDENCE_ENTRY_TEMPLATE.md](EVIDENCE_ENTRY_TEMPLATE.md) for detailed linking guide

**Markdown Link Format:**
```markdown
[Display Text](relative/path/or/url)
```

---

## Evidence File Storage

**Recommended Location:** `docs/ops/evidence/EV-<ID>.md`

**Example:**
- Entry ID: `EV-20260107-PHASE1`
- File path pattern: `docs/ops/evidence/EV-<YYYYMMDD>-<TAG>.md`

**Note:** Evidence files are **optional**. Inline evidence (commit SHA, PR URL) is sufficient for many cases.

---

## Validation Rules

1. **ID uniqueness:** No duplicate Evidence IDs in the index
2. **ID format:** Must match `EV-YYYYMMDD-<TAG>` pattern
3. **Category validity:** Must be one of the 5 defined categories
4. **Date format:** `YYYY-MM-DD` (ISO 8601)
5. **Mandatory fields:** All 7 mandatory fields must be present (non-empty)
6. **Link validity (best effort):** If Source Link points to a repo file, the file should exist

---

**Version:** v0.2  
**Maintained by:** ops  
**Last Updated:** 2026-01-07  
**Related:** [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md), [EVIDENCE_ENTRY_TEMPLATE.md](EVIDENCE_ENTRY_TEMPLATE.md)
