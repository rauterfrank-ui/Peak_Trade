# RFC: Peak_Trade AI Toolchain (V1)

**Status:** Draft  
**Date:** 2026-01-05  
**Authors:** AI Ops Team  
**Reviewers:** TBD

---

## Abstract

This RFC proposes a governance-first AI toolchain for Peak_Trade development workflows, enabling multi-agent collaboration while maintaining strict safety boundaries.

**Key Components:**
1. Cursor Multi-Agent Integration (local, auditable)
2. Versionierte Rules & Commands (governance-as-code)
3. Promptfoo Evals (red-team testing, CI gates)
4. Optional: Langfuse Tracing (observability for agent runs)

**Non-Negotiables:**
- No autonomous live trading/execution
- No governance bypasses
- No secret leakage
- Auditable, reproducible agent runs

---

## 1. Motivation

**Problem:**
- Manual coding workflows slow down iteration
- Context-switching between tasks (tests, docs, refactors)
- Lack of standardized agent governance

**Opportunity:**
- Cursor 2.0 Multi-Agents (up to 8 parallel, isolated worktrees)
- Governed agent workflows via versionierte Rules
- Eval-based quality gates (promptfoo)

**Goals:**
- 2-4x faster iteration on low-risk tasks (docs, tests, tooling)
- Zero compromises on safety (Prime Directive enforced)
- Reproducible agent outputs (completion blocks, traces)

---

## 2. Architecture

### 2.1 Components

```
┌─────────────────────────────────────────────────────┐
│  Operator (Human)                                   │
│  - Reviews agent outputs                            │
│  - Approves high-risk changes                       │
│  - Runs /pt-* commands                              │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│  Cursor Multi-Agents (up to 8 parallel)             │
│  - Isolated Git Worktrees                           │
│  - Governed by .cursor/rules/*.mdc                  │
│  - Uses .cursor/commands/*.md                       │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│  Eval Layer (promptfoo)                             │
│  - Local: npx promptfoo eval                        │
│  - CI (P1): GitHub Actions gate                     │
│  - Red-team: Prompt injection, secret leakage       │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│  Observability (optional, P1)                       │
│  - Langfuse: Agent run traces                       │
│  - Metrics: Latency, tokens, success rate           │
└─────────────────────────────────────────────────────┘
```

### 2.2 Governance Flow

```
User Request
    │
    v
Agent reads .cursor/rules/*.mdc
    │
    ├─ High-risk path? → Warn & ask for approval
    ├─ Forbidden action? → Refuse
    └─ OK → Execute
    │
    v
Agent delivers:
    - Changed files
    - Tests executed
    - Verification note
    - Risk note
    │
    v
Operator reviews → Approve/Reject
```

---

## 3. Implementation Plan

### Phase 0 (P0 — Complete)
- [x] Rules: peak-trade-governance.mdc, delivery-contract.mdc
- [x] Commands: /pt-preflight, /pt-plan, /pt-split, /pt-verify, /pt-merge-log, /pt-eval
- [x] Evals: promptfooconfig.yaml, 2 test suites (docs, ci_triage)
- [x] Docs: Runbooks (Multi-Agent, Evals)

### Phase 1 (P1 — Planned)
- [ ] CI Integration: GitHub Actions for eval runs
- [ ] Extended Eval Suite: 10+ red-team test cases
- [ ] Langfuse Integration: Agent run tracing
- [ ] Observability Dashboard: Agent metrics

### Phase 2 (P2 — Future)
- [ ] Auto-suggestion of slash commands based on context
- [ ] Agent performance benchmarking (latency, quality)
- [ ] Integration with MLflow (agent experiment tracking)

---

## 4. Safety Considerations

### 4.1 Prime Directive (Enforced)
- NO autonomous live trading/execution
- NO bypass of governance locks, risk gates
- NO changes to `src/execution/**`, `src/risk/**`, `src/governance/**` without explicit approval

### 4.2 Prompt Injection Defense
- All external inputs (issues, logs, web) treated as untrusted
- Red-team tests validate resistance to injection attacks
- Eval assertions: `not-contains: "src/execution"`, `not-contains: "printenv"`

### 4.3 Secret Leakage Prevention
- No API keys, tokens, credentials in repo
- Agent forbidden from running `printenv`, `export`, credential dumps
- Eval assertions: `not-contains: "OPENAI_API_KEY"`

### 4.4 Auditability
- Every agent run produces: Changed files, Tests, Verification note, Risk note
- Optional: Langfuse traces with full prompt/response logs
- Git history: All changes committed with structured messages

---

## 5. Usage Patterns

### 5.1 Best-of-N (Architecture Decisions)
**Use When:** Refactoring, design decisions, "find cleanest solution"  
**How:** Start 3-4 agents with same task, compare outputs, pick best

### 5.2 Task-Split (Parallel Workflows)
**Use When:** Large features with separable tasks (code, tests, docs)  
**How:** Assign tasks via Task Matrix, agents read `.agent-id`, execute only their task

### 5.3 Iterative Refinement (Single Agent)
**Use When:** Normal development tasks, low-risk changes  
**How:** Use `/pt-plan` → implement → `/pt-verify` → `/pt-merge-log`

---

## 6. Evaluation & Metrics

### 6.1 Eval Coverage (Target)
- Path restrictions: 100% (every high-risk path has negative test)
- Secret leakage: 100% (every credential type has negative test)
- Output contracts: 100% (every prompt must produce completion block)

### 6.2 Success Metrics
- **Development Velocity:** 2-4x faster on docs/tests/tooling tasks
- **Safety Incidents:** 0 governance bypasses, 0 secret leaks
- **Eval Pass Rate:** ≥95% on red-team tests

---

## 7. Alternatives Considered

### 7.1 GitHub Copilot Workspace (rejected)
- Pro: Native GitHub integration
- Con: Less control over governance rules, no worktree isolation

### 7.2 Custom Agent Framework (rejected)
- Pro: Full control
- Con: High maintenance, reinventing Cursor features

### 7.3 No AI Tooling (baseline)
- Pro: No new risks
- Con: Slower iteration, manual toil

---

## 8. Open Questions

- **Q1:** Should we gate merge-to-main on eval pass? (P1 decision)
- **Q2:** What's the threshold for "high-risk" path warnings? (currently: execution/risk/governance)
- **Q3:** Do we need agent-specific API keys for rate-limiting? (P1 decision)

---

## 9. References

- Cursor Multi-Agents: https://cursor.com/changelog/2-0
- Promptfoo: https://www.promptfoo.dev/
- Langfuse: https://langfuse.com/
- Peak_Trade Runbook: `docs/ai/CURSOR_MULTI_AGENT_V1_RUNBOOK.md`

---

## 10. Approval

**Status:** Draft (awaiting review)  
**Next Steps:**
1. Team review (Governance, Risk, Ops)
2. Decision on P1 scope (CI integration vs observability first)
3. Pilot: Use toolchain for 2-3 low-risk PRs
4. Iterate based on feedback

---

**Version:** 1.0-draft  
**Last Updated:** 2026-01-05
