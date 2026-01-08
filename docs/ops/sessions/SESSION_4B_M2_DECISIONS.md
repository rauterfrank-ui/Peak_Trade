# 4B M2 — DECISIONS (20260109)

Record trade-offs and rationale for key decisions during 4B Milestone 2 setup and execution.

---

## Decision 1: Worktree vs. Main Repo Branch

**Date:** 2026-01-09  
**Decision:** Use Git Worktree instead of branch in main repo  
**Options Considered:**
1. Create feature branch in main repo (`/Users/frnkhrz/Peak_Trade`)
2. Create separate worktree (`~/.cursor-worktrees/Peak_Trade/4b-m2`)

**Rationale:**
- **Isolation:** Worktree allows parallel work without disrupting main repo state
- **Clean Context:** Operator can keep main repo on different branch (e.g., `ci/phase4a-evidence-pack-gate`) while working on M2
- **CI Testing:** Easier to test CI behavior in isolation
- **Rollback:** Simple to delete worktree if experiment fails
- **Standard Practice:** Aligns with existing Peak_Trade workflow patterns

**Follow-up:**
- Document worktree cleanup procedure in runbook
- Consider automating worktree lifecycle management in future milestones

---

## Decision 2: uv vs. pip/venv for Development Environment

**Date:** 2026-01-09  
**Decision:** Use `uv` as primary package manager and environment tool  
**Options Considered:**
1. Traditional `pip` + `venv`
2. `uv` (modern Rust-based package manager)
3. `poetry` or `pipenv`

**Rationale:**
- **Speed:** uv is significantly faster than pip (Rust-based)
- **Consistency:** Already used in Peak_Trade CI/CD pipelines
- **Reproducibility:** Better lockfile handling and dependency resolution
- **Simplicity:** Auto-creates .venv, no manual activation needed
- **Audit Support:** Works seamlessly with `pip-audit`

**Follow-up:**
- Verify `uv` is documented in `docs/DEV_SETUP.md`
- Ensure all gate commands use `uv run` prefix

---

## Decision 3: Session Artifacts Structure

**Date:** 2026-01-09  
**Decision:** Create dedicated session artifacts under `docs/ops/sessions/`  
**Options Considered:**
1. Put artifacts in `docs/ai/` (alongside AI orchestration docs)
2. Create new `docs/sessions/` directory
3. Use `docs/ops/sessions/` (chosen)
4. Inline in PR description only (no persistent artifacts)

**Rationale:**
- **Ops Context:** Multi-agent workflow is an operational practice, fits under `docs/ops/`
- **Discoverability:** `sessions/` subdirectory clearly separates from other ops docs
- **Reusability:** Templates (Appendices) can be referenced by future sessions
- **Audit Trail:** Persistent artifacts provide audit trail for decision-making
- **Precedent:** Aligns with existing `docs/ops/` structure (runbooks, merge logs, etc.)

**Follow-up:**
- Consider adding session index/catalog for discoverability (future work)

---

## Decision 4: PR Scope — Setup Only vs. Full Implementation

**Date:** 2026-01-09  
**Decision:** Limit M2 PR to setup artifacts, defer implementation to follow-on work  
**Options Considered:**
1. Include full M2 implementation (code changes, features, etc.) in one PR
2. Split into setup PR (artifacts, runbook) + implementation PR(s) (chosen)

**Rationale:**
- **Reviewability:** Setup artifacts are docs-heavy and easier to review separately
- **Risk Reduction:** Isolate no-op changes (docs/scripts) from functional code changes
- **Fast Merge:** Setup PR can merge quickly, unblocking future work
- **Iterative Approach:** Aligns with Peak_Trade "minimal diffs" philosophy
- **CI Efficiency:** Avoids long-running test suites on pure docs changes

**Follow-up:**
- Create follow-on PRs for actual M2 implementation features
- Reference this setup PR in implementation PRs

---

## Decision 5: Audit Baseline — Accept vs. Remediate

**Date:** 2026-01-09 (Pending CI_GUARDIAN execution)  
**Decision:** TBD (awaiting pip-audit results)  
**Options to Consider:**
1. Accept all findings as-is (document only)
2. Remediate critical/high findings immediately
3. Remediate in separate PR
4. Create exceptions with justification

**Rationale:** (To be filled after audit execution)

**Follow-up:** (To be filled after decision)

---

## Decision 6: Multi-Agent Roles — Fixed vs. Fluid

**Date:** 2026-01-09  
**Decision:** Use fixed role assignments (LEAD, IMPLEMENTER, CI_GUARDIAN, DOCS_OPS)  
**Options Considered:**
1. Fixed roles with clear boundaries (chosen)
2. Fluid roles where any agent can do anything
3. Single agent with multiple hats

**Rationale:**
- **Clarity:** Fixed roles reduce confusion about who owns what
- **Accountability:** Each role has specific verification responsibilities
- **Efficiency:** Agents can specialize and work in parallel
- **Audit Trail:** Clear attribution of decisions and changes
- **Scalability:** Easier to onboard new agents or operators

**Follow-up:**
- Monitor role effectiveness during actual M2 implementation
- Adjust boundaries if overlaps or gaps discovered

---

## Template for Future Decisions

**Date:** YYYY-MM-DD  
**Decision:** [Brief statement]  
**Options Considered:**
1. Option A
2. Option B (chosen)
3. Option C

**Rationale:**
- Key factor 1
- Key factor 2
- Key factor 3

**Follow-up:**
- Action item or monitoring point
