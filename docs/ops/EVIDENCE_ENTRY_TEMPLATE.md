# Evidence Entry Template (v0.2)

**Purpose:** Copy-paste template for creating new evidence entries.  
**Usage:** Fill in ALL mandatory fields, then add to `EVIDENCE_INDEX.md` (table + category section).

---

## Template (Markdown Format)

```markdown
## Evidence Entry: [SHORT_TITLE]

**Evidence ID:** EV-YYYYMMDD-<TAG>  
**Date:** YYYY-MM-DD  
**Category:** [CI/Workflow | Drill/Operator | Test/Refactor | Incident/RCA | Config Snapshot]  
**Owner:** [username/team/role]  
**Status:** VERIFIED

### Scope
[1–2 sentences: What system/component/process does this evidence cover?]

### Claims
[What does this evidence demonstrate? Be specific and factual.]
- Claim 1: [e.g., "138/138 tests passed"]
- Claim 2: [e.g., "Zero breaking changes"]

### Evidence / Source Links
- [Primary Source: PR #XXX Merge Log](relative/path/to/merge_log.md)
- [CI Run: workflow_run_url]
- [Commit: SHA]

### Verification Steps
[How can someone verify this evidence?]
1. Step 1: [e.g., "Check out commit SHA"]
2. Step 2: [e.g., "Run `pytest tests/test_kupiec.py`"]
3. Expected result: [e.g., "138/138 tests pass"]

### Risk Notes
[Optional: Any caveats, limitations, or risk context]
- [e.g., "Read-only changes, no live trading impact"]

### Related PRs / Commits
- PR #XXX: [Title](github_url)
- Commit: [SHA] - [Short description]

### Owner / Responsibility
**Owner:** [username/team]  
**Contact:** [Slack channel / email / GitHub handle]

---

**Entry Created:** YYYY-MM-DD  
**Last Updated:** YYYY-MM-DD
```

---

## Example (Filled Template)

```markdown
## Evidence Entry: Phase 8A Kupiec POF Deduplication

**Evidence ID:** EV-20251228-PHASE8A  
**Date:** 2025-12-28  
**Category:** Test/Refactor  
**Owner:** ops  
**Status:** VERIFIED

### Scope
Phase 8A refactoring: Kupiec POF (Proportion of Failures) test deduplication, single canonical engine established.

### Claims
- 138/138 tests passed (pytest 8.4.2, Python 3.9.6)
- Single canonical engine established (`src/backtesting/validation/kupiec_pof.py`)
- Zero breaking changes (all delegation tests verify wrapper correctness)

### Evidence / Source Links
- [PR #XXX Merge Log](../../PHASE8A_MERGE_LOG.md)
- Branch: `refactor/kupiec-pof-single-engine`

### Verification Steps
1. Check out commit `main@<SHA>`
2. Run: `pytest tests/backtesting/validation/test_kupiec*.py -v`
3. Expected: 138/138 tests pass in <10s

### Risk Notes
- Risk: VERY LOW (refactor-only, no behavior changes)
- Ready for merge

### Related PRs / Commits
- PR #XXX: Phase 8A Kupiec POF Deduplication

### Owner / Responsibility
**Owner:** ops  
**Contact:** #peak-trade-ops

---

**Entry Created:** 2025-12-28  
**Last Updated:** 2025-12-28
```

---

**Version:** v0.2  
**Maintained by:** ops  
**Last Updated:** 2026-01-07  
**Related:** [EVIDENCE_SCHEMA.md](EVIDENCE_SCHEMA.md), [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md)
