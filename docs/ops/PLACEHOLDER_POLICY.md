# Peak_Trade – Placeholder & TODO Standards (Policy v0)

**Scope:** Repository-wide standards for placeholder markers in code, docs, and config.  
**Goal:** Consistent semantics, traceable ownership, and minimal placeholder debt in production paths.

---

## 1. Marker Definitions

### TODO
**Purpose:** Work item that should be completed but is not blocking current functionality.

**Format:**
```
TODO(owner): Brief description
TODO(owner, issue-ref): Brief description
```

**Examples:**
```python
# TODO(ops): Add retry logic for transient failures
# TODO(alice, #123): Implement caching layer
```

**When to use:**
- Missing feature that's planned but not critical
- Code improvement or refactoring opportunity
- Known technical debt with no immediate impact

**When NOT to use:**
- Blocking bugs → use FIXME
- Production-critical missing pieces → resolve before merge

---

### FIXME
**Purpose:** Known bug or defect that should be fixed soon.

**Format:**
```
FIXME(scope): Problem description
FIXME(scope, severity): Problem description
```

**Examples:**
```python
# FIXME(auth): Password validation allows weak passwords
# FIXME(critical): Race condition in order submission
```

**When to use:**
- Known bug that's reproducible
- Incorrect behavior that needs correction
- Security vulnerability (pair with issue tracker)

**When NOT to use:**
- Design improvements → use TODO
- Future features → use TODO

---

### TBD (To Be Determined / Decided)
**Purpose:** Placeholder where a decision hasn't been made yet, or information is incomplete.

**Format:**
```
TBD(phase): What needs to be determined
TBD(decision-owner): What needs to be decided
```

**Examples:**
```yaml
# TBD(phase-3): Finalize retry strategy
# TBD(product): Confirm UI flow for edge case
# config: TBD(ops) # Value pending production measurement
```

**When to use:**
- Design decision pending stakeholder input
- Value/parameter that requires real-world data
- Placeholder in documentation for future content

**Template-first contexts:**
- Audit templates, runbook templates, phase plans
- Expected and acceptable (mark as template if possible)

---

### [TBD]
**Purpose:** Inline placeholder in structured documents (checklists, tables, forms).

**Format:**
```markdown
- Metric: [TBD]
- Threshold: [TBD(ops)]
| Field | Value |
|-------|-------|
| Count | [TBD] |
```

**When to use:**
- Checklist items not yet filled
- Table cells awaiting data
- Form fields in templates

**Note:** Prefer bracket form `[TBD]` over bare `TBD` in structured contexts for clarity.

---

### XXX
**Purpose:** Attention marker for code that needs review, is experimental, or has caveats.

**Format:**
```
XXX(reason): Explanation
XXX: Brief warning
```

**Examples:**
```python
# XXX(temporary): Workaround until upstream fix in v2.1
# XXX: This assumes single-threaded execution
```

**When to use:**
- Temporary workaround that should be revisited
- Code with non-obvious assumptions
- Experimental feature flag

**When NOT to use:**
- Known bugs → use FIXME
- Planned work → use TODO

---

### ROADMAP
**Purpose:** Marker for future features or architectural changes mentioned in code/docs.

**Format:**
```
ROADMAP(phase): Feature description
ROADMAP(version): Planned enhancement
```

**Examples:**
```python
# ROADMAP(v2): Migrate to async execution model
# ROADMAP(phase-5): Add distributed caching
```

**When to use:**
- Long-term architectural vision
- Feature flagged for future version
- Cross-cutting changes requiring coordination

---

### HACK
**Purpose:** Quick-and-dirty solution that violates best practices (ideally rare).

**Format:**
```
HACK(justification): Why this is necessary
```

**Example:**
```python
# HACK(deadline): Bypassing validation for demo, revert after launch
```

**When to use:**
- Time-constrained workaround with known tech debt
- Must be paired with issue/task to remove

**Policy:** HACK markers should be rare in production paths. If found during audit, require justification or removal.

---

## 2. Best Practices

### Ownership
- **Always specify an owner** (username, role, or phase): `TODO(alice)`, `TBD(ops)`, `FIXME(auth-team)`
- If ownership is unclear, use team name or phase: `TODO(phase-2)`, `TBD(product)`

### Issue Linking
- **Link to issue tracker when available**: `TODO(alice, #456)`
- Helps track progress and provides context

### Scope Limits
- **Keep markers close to the code** they reference (not at file top unless file-wide)
- **Avoid vague markers**: ❌ `TODO: fix this` ✅ `TODO(ops): add input validation for negative prices`

### Template-First Approach
- **Mark templates explicitly**:
  ```markdown
  # Audit Template v1
  This template contains [TBD] placeholders by design.
  ```
- **Acceptable placeholder density** in templates/runbooks (expected workflow)
- **Unacceptable density** in production code/live configs

### Tracking & Debt Management
- Run periodic placeholder audits: `python scripts&#47;ops&#47;placeholders&#47;generate_placeholder_reports.py`
- Review high-density files (use target map reports)
- Prioritize cleanup in production/execution paths over docs/templates

---

## 3. Reporting & Inventory

### Local Reports (`.ops_local&#47;inventory&#47;`)
Placeholder reports are generated locally and **NOT committed** to Git.

**Files:**
- `TODO_PLACEHOLDER_INVENTORY.md` — Summary counts + top files
- `TODO_PLACEHOLDER_TARGET_MAP.md` — Path-prefix analysis (docs/, src/, config/, etc.)

**Generation:**
```bash
python scripts/ops/placeholders/generate_placeholder_reports.py
```

**Output location:** `.ops_local&#47;inventory&#47;` (git-ignored)

### Audit Workflow
1. **Generate reports** locally before major milestones (phase gates, releases)
2. **Review high-density files** (top 10 from target map)
3. **Triage markers**:
   - Production code: resolve or issue-link
   - Templates/docs: acceptable if marked as template
4. **Track trends** over time (manual comparison of reports)

---

## 4. Anti-Patterns

❌ **Don't:**
- Use bare `TODO` without owner: `TODO: fix`
- Mix multiple markers: `TODO&#47;FIXME: ...`
- Leave markers in production-critical execution paths without issue links
- Use `HACK` without justification or removal plan

✅ **Do:**
- Specify owner: `TODO(alice)`
- Link issues: `TODO(alice, #123)`
- Resolve before production: `FIXME` in execution code → block deployment
- Mark templates: "Template v1 — [TBD] placeholders expected"

---

## 5. CI / Enforcement (Future)

**Current state:** Policy documentation only, no automated enforcement.

**Future options:**
- Pre-commit hook: warn on new `FIXME` in `src/execution/` or `src/live/`
- CI check: fail if `HACK` count increases without issue link
- Periodic audit: scheduled report generation + trend analysis

**Not planned:**
- Blocking all TODOs (impractical)
- Enforcing format (developer ergonomics vs. strictness tradeoff)

---

## 6. Scope & Exclusions

**In scope:**
- All `.py`, `.md`, `.toml`, `.yaml`, `.yml`, `.sh` files in repo

**Excluded from reports:**
- `.git/`, `venv&#47;`, `.venv&#47;`, `node_modules&#47;`, `dist&#47;`, `build&#47;`, caches
- `.ops_local&#47;` (output folder)
- Binary files, lock files (e.g., `uv.lock`)

**Why exclude `.ops_local&#47;`?**
- Output folder for local artifacts
- Not committed (in `.gitignore`)
- Scanning it would create false positives from generated reports

---

## 7. References

- Generator script: `scripts/ops/placeholders/generate_placeholder_reports.py`
- Gitignore entry: `.ops_local&#47;` (line 111 in `.gitignore`)
- Audit docs: `docs/audit/` (high TBD density expected in templates)

---

**Version:** v0 (Initial Draft)  
**Owner:** ops  
**Last Updated:** 2026-01-07
