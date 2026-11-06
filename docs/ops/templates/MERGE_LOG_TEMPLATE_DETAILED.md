# Merge Log Template (Detailed) — PR #[TBD]

> **Template Note:** This is a detailed template document. All `[TBD]` and `TBD(...)` placeholders should be replaced with actual values. Use this template for complex, high-risk, or multi-component PRs.

---

## Metadata

| Field | Value |
|-------|-------|
| **PR Number** | [TBD] |
| **PR URL** | [TBD] |
| **Title** | [TBD] |
| **Branch** | [TBD] → `main` |
| **Merged Date** | [TBD(YYYY-MM-DD)] |
| **Merge Commit** | [TBD(SHA)] |
| **Author** | [TBD] |
| **Reviewer(s)** | [TBD] |
| **Merge Strategy** | [TBD(squash / merge / rebase)] |

---

## Summary

**What Changed:**
- [TBD(1-sentence overview)]
- [TBD(scope: docs/code/config)]
- [TBD(user-facing impact)]

**Key Deliverables:**
- [TBD]
- [TBD]
- [TBD]

---

## Why

**Problem Statement:**
- [TBD(what was broken or missing)]
- [TBD(pain point or requirement)]

**Desired Outcome:**
- [TBD(what this PR achieves)]
- [TBD(benefit to operators or system)]

**Context:**
- [TBD(related work or dependencies)]
- [TBD(timeline or milestone)]

---

## Changes

### Files Added

| File | Purpose |
|------|---------|
| `[TBD(path)]` | [TBD(description)] |
| `[TBD(path)]` | [TBD(description)] |

### Files Modified

| File | Change Summary |
|------|----------------|
| `[TBD(path)]` | [TBD(what changed)] |
| `[TBD(path)]` | [TBD(what changed)] |

### Files Removed

| File | Reason |
|------|--------|
| [TBD(path or "None")] | [TBD(why removed)] |

### Diff Highlights

Key code/config changes:
```
[TBD(paste relevant diff snippets if helpful)]
```

---

## Verification

### CI Checks Summary

| Check Name | Status | Duration | Notes |
|------------|--------|----------|-------|
| [TBD] | [TBD(✓/✗)] | [TBD] | [TBD] |
| [TBD] | [TBD(✓/✗)] | [TBD] | [TBD] |

**CI Run URL:** [TBD]

### Local Testing

**Commands executed:**
```bash
[TBD(list commands)]
```

**Results:**
- [TBD(outcome)]
- [TBD(any warnings or notes)]

**Test Matrix (if applicable):**

| Test Case | Environment | Result | Notes |
|-----------|-------------|--------|-------|
| [TBD] | [TBD(Python 3.9/3.10/etc)] | [TBD(✓/✗)] | [TBD] |

---

## Risk Assessment

**Overall Risk:** [TBD(🟢 Low / 🟡 Medium / 🔴 High)]

### Risk Factors

| Factor | Rating | Justification |
|--------|--------|---------------|
| Code Complexity | [TBD(Low/Med/High)] | [TBD] |
| Scope of Change | [TBD(Low/Med/High)] | [TBD] |
| Test Coverage | [TBD(Low/Med/High)] | [TBD] |
| Rollback Difficulty | [TBD(Low/Med/High)] | [TBD] |

### What Could Go Wrong

- [TBD(potential issue 1)]
- [TBD(potential issue 2)]

### Mitigation

- [TBD(how risks are addressed)]
- [TBD(safeguards in place)]

---

## Operator How-To

### Quick Start

1. [TBD(step 1)]
2. [TBD(step 2)]
3. [TBD(step 3)]

### Verification Commands

```bash
# Smoke test
[TBD(command)]

# Expected output:
[TBD(what to look for)]
```

### Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| [TBD] | [TBD] | [TBD] |

---

## Timeline

| Event | Timestamp | Notes |
|-------|-----------|-------|
| PR Opened | [TBD] | [TBD] |
| CI Started | [TBD] | [TBD] |
| CI Completed | [TBD] | [TBD] |
| Review Completed | [TBD] | [TBD] |
| Merged | [TBD] | [TBD] |
| Branch Deleted | [TBD] | [TBD] |

---

## Rollback Plan

**If this PR causes issues:**

1. [TBD(rollback step 1)]
2. [TBD(rollback step 2)]
3. [TBD(verification after rollback)]

**Rollback Risk:** [TBD(Low/Medium/High)] — [TBD(why)]

---

## Incident Notes

TBD(phase-6)
<!-- Fill this section only if incidents occurred during or after merge -->

**Incidents:** [TBD(None / list incident IDs)]

**Post-Merge Issues:**
- [TBD(None or list issues found)]

**Resolution:**
- [TBD(how issues were resolved)]

---

## References

### Primary
- **PR:** [TBD(GitHub PR URL)]
- **Merge Commit:** [TBD(SHA)]
- **CI Run:** [TBD(Actions URL)]

### Related Work
- [TBD(related PR #)]
- [TBD(related issue #)]
- [TBD(related documentation)]

### Documentation
- [TBD(updated/created docs)]
- [TBD(runbooks affected)]

---

**Template Version:** v1.0  
**Maintained by:** ops  
**Last Updated:** 2026-01-07
