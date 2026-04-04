# Evidence Entry Template (v0.3)

**Purpose:** Copy-paste template for creating new evidence entries.  
**Usage:** Fill in mandatory fields, replace `[draft — replace]` slots with real content, then add to `EVIDENCE_INDEX.md` (table + category section).

**Alignment:** Matches `scripts/ops/generate_evidence_entry.py` output (**Template Version:** v0.3). Draft slots use `[draft — replace]` so placeholder-inventory scans stay triage-friendly.

---

## Template (Markdown Format)

Use this structure for new files under `docs/ops/evidence/`. After verification, set **Status** to `VERIFIED` (or `ARCHIVED`).

```markdown
# Evidence Entry: [SHORT_TITLE]

**Evidence ID:** EV-YYYYMMDD-<TAG>
**Date:** YYYY-MM-DD
**Category:** [CI/Workflow | Drill/Operator | Test/Refactor | Incident/RCA | Config Snapshot]
**Owner:** [username/team/role]
**Status:** DRAFT

---

## Scope
[1–2 sentences: What system/component/process does this evidence cover?]

---

## Claims
[What does this evidence demonstrate? Be specific and factual.]
- Claim 1: [draft — replace]
- Claim 2: [draft — replace]

---

## Evidence / Source Links
- Primary source: [draft — replace]
- CI run / commit: [draft — replace]

---

## Verification Steps
[How can someone verify this evidence?]
1. Step 1: [draft — replace]
2. Step 2: [draft — replace]
3. Expected result: [draft — replace]

---

## Risk Notes
[Optional: Any caveats, limitations, or risk context]
- [draft — replace]

---

## Related PRs / Commits
- PR #<pr-number> — [draft — replace]
- Commit: [draft — replace]

---

## Owner / Responsibility
**Owner:** [username/team/role]
**Contact:** [draft — replace]

---

**Entry Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD
**Template Version:** v0.3
```

---

## Linking Conventions for Evidence Entries

**Important:** Evidence entries are stored in `docs/ops/evidence/`, which is **3 levels deep** from the repository root.

**Rule:** To link to repo-root files, use `../../../` prefix.

### Common Link Patterns

| Target Location | Relative Path from Evidence Entry | Example Pattern |
|-----------------|-----------------------------------|-----------------|
| `config&#47;` files | `..&#47;..&#47;..&#47;config&#47;` | `` `[bounded_live.toml](..&#47;..&#47;..&#47;config&#47;bounded_live.toml)` `` |
| `.github&#47;workflows&#47;` files | `..&#47;..&#47;..&#47;.github&#47;workflows&#47;` | `` `[ci.yml](..&#47;..&#47;..&#47;.github&#47;workflows&#47;ci.yml)` `` |
| `scripts&#47;ops&#47;` files | `..&#47;..&#47;..&#47;scripts&#47;ops&#47;` | `` `[run_audit.sh](..&#47;..&#47;..&#47;scripts&#47;ops&#47;run_audit.sh)` `` |
| `docs&#47;ops&#47;` files (sibling) | `..&#47;` | `` `[EVIDENCE_INDEX.md](..&#47;EVIDENCE_INDEX.md)` `` |
| Other `docs&#47;` files | `..&#47;..&#47;..&#47;docs&#47;` | `` `[README.md](..&#47;..&#47;..&#47;README.md)` `` |

### Examples (Correct ✅ vs Incorrect ❌)

**✅ Correct (3 levels up from** `docs&#47;ops&#47;evidence&#47;`**)**:
```markdown
- [Config: bounded_live.toml](../../../config/bounded_live.toml)
- [CI Workflow](../../../.github/workflows/ci.yml)
- [Audit Script](../../../scripts/ops/run_audit.sh)
```

**❌ Incorrect (only 2 levels up):**
```markdown
- [Config: bounded_live.toml](../../config/bounded_live.toml)  ← BROKEN LINK
- [CI Workflow](../../.github/workflows/ci.yml)               ← BROKEN LINK
```

**Why this matters:**
- Evidence entries in `docs&#47;ops&#47;evidence&#47;EV-*.md` are 3 directories deep from repo root
- Path structure: `repo-root&#47;docs&#47;ops&#47;evidence&#47;EV-*.md`
- Broken links cause `docs-reference-targets-gate` CI check to fail

**Verification:**
```bash
# Always validate links after creating/editing evidence entries:
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

---

## Example (Filled Template)

```markdown
# Evidence Entry: Phase 8A Kupiec POF Deduplication

**Evidence ID:** EV-20251228-PHASE8A
**Date:** 2025-12-28
**Category:** Test/Refactor
**Owner:** ops
**Status:** VERIFIED

---

## Scope
Phase 8A refactoring: Kupiec POF (Proportion of Failures) test deduplication, single canonical engine established.

---

## Claims
- 138/138 tests passed (pytest 8.4.2, Python 3.9.6)
- Single canonical engine established (`src/backtesting/validation/kupiec_pof.py`)
- Zero breaking changes (all delegation tests verify wrapper correctness)

---

## Evidence / Source Links
- Primary source: [PR merge log](archives/repo_root_docs/PHASE8A_MERGE_LOG.md)
- CI run / commit: Branch `refactor/kupiec-pof-single-engine` (see merge log)

---

## Verification Steps
1. Check out commit `main@<SHA>`
2. Run: `pytest tests/backtesting/validation/test_kupiec*.py -v`
3. Expected: 138/138 tests pass in <10s

---

## Risk Notes
- Risk: VERY LOW (refactor-only, no behavior changes)
- Ready for merge

---

## Related PRs / Commits
- PR #596 — Phase 8A Kupiec POF Deduplication (see merge log for URL)

---

## Owner / Responsibility
**Owner:** ops
**Contact:** #peak-trade-ops

---

**Entry Created:** 2025-12-28
**Last Updated:** 2025-12-28
**Template Version:** v0.3
```

---

**Version:** v0.3  
**Maintained by:** ops  
**Last Updated:** 2026-04-01  
**Related:** [EVIDENCE_SCHEMA.md](EVIDENCE_SCHEMA.md), [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md)
