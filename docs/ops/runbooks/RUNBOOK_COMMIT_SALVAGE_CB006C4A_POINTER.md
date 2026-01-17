# Commit Salvage Runbook (Pointer)

**Type:** Pointer Document  
**Canonical Location:** [RUNBOOK_COMMIT_SALVAGE_CB006C4A.md](../../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md) (repo root)

---

## Purpose

Operator runbook for salvaging a commit accidentally created on the wrong branch (e.g., local `main` instead of feature branch), and restoring repo-conform workflow:

```
feature branch → PR → CI validation → merge
```

---

## Use Cases

1. **Accidental commit on main**: Commit created locally on `main` branch instead of feature branch
2. **Wrong branch recovery**: Commit on incorrect branch needs to be moved without losing history
3. **Repo-conform workflow restoration**: Salvaging commits while maintaining PR/CI/review workflow

---

## Quick Reference

**Canonical Runbook:** [../../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md](../../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md)

**Phases:**
1. **Phase 0**: State Validation & Truth Capture
2. **Phase 1**: Feature Branch Creation & Commit Salvage
3. **Phase 2**: Reset Local Main to Origin/Main
4. **Phase 3**: Push Feature Branch to Origin
5. **Phase 4**: Create PR with Clean Body
6. **Phase 5**: CI Snapshot (No Watch Loops)
7. **Phase 6**: Merge Plan & Cleanup

**Timeline:** ~15-25 minutes (operator-driven, no watch loops)

---

## Why Pointer?

The canonical runbook remains in the repo root for:
- **Provenance**: Preserves original context and commit reference (cb006c4a)
- **Stability**: Minimizes risk of breaking references from merge logs, evidence index, or other docs
- **Discoverability**: Pointer ensures visibility in ops runbooks landscape

This hybrid approach (root artifact + pointer) balances:
- ✅ Auffindbarkeit (findable from runbooks index)
- ✅ Stabilität (no breaking changes from relocation)
- ✅ Konsistenz (pattern for future root-level runbooks)

---

## Related

- **Evidence**: PR #718 (salvage operation execution + docs gates fixes)
- **Pattern**: Similar to `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` (root-level operational reference)
- **Usage**: Documents salvage workflow for commits accidentally created on wrong branch

---

**Last Updated:** 2026-01-14  
**Maintainer:** ops
