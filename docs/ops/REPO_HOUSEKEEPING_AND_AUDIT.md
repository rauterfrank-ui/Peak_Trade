# Repo Housekeeping & Audit (Peak_Trade)

## Ziele
1. **Aufräumen ohne Breaking Changes** (Struktur, Duplikate, Altlasten, Naming, Ignored files).
2. Danach **großes Audit** (Tests, Lint/Format, Typing optional, Security/Dependency optional) mit kuratiertem Report in `docs/audits/`.

## Grundregeln
- Moves ausschließlich via `git mv`.
- Erst **Plan/Dry-Run**, dann **Apply**.
- Raw Outputs unter `reports/audit/` und `reports/housekeeping/` werden **nicht committed**.
- Report wird in `docs/audits/REPO_AUDIT_<timestamp>.md` committed.

## Quickstart

### 1. Housekeeping Scan (Dry-Run)
```bash
# Scan for issues (no changes made)
scripts/automation/repo_housekeeping_scan.sh

# Review the generated plan
cat reports/housekeeping/cleanup_plan_*.md
```

### 2. Repository Audit
```bash
# Quick audit (smoke tests only)
scripts/automation/repo_audit.sh quick

# Full audit (all tests, all checks)
scripts/automation/repo_audit.sh full

# Review curated report
ls -lrt docs/audits/
cat docs/audits/REPO_AUDIT_*.md
```

## Workflow: Full Housekeeping + Audit

### Phase 1: Initial Scan
```bash
# Create working branch
git checkout -b chore/repo-housekeeping-audit

# Run housekeeping scan
scripts/automation/repo_housekeeping_scan.sh

# Review plan
LATEST_PLAN=$(ls -t reports/housekeeping/cleanup_plan_*.md | head -1)
cat "${LATEST_PLAN}"
```

### Phase 2: Execute Cleanup (Manual)
Based on the scan results, execute cleanup operations **carefully**:

```bash
# Example: Move top-level markdown files to docs/ops/
git mv SOME_FILE.md docs/ops/

# Example: Remove backup files
git rm path/to/file.bak

# Example: Consolidate config files
git mv config.toml config/config.toml

# After each logical group of changes
pytest  # Verify nothing broke
git commit -m "chore: move X files to proper location"
```

**Rules:**
- ✅ Use `git mv` for moves (preserves history)
- ✅ Use `git rm` for deletions
- ✅ Run tests after each change group
- ✅ Commit incrementally with clear messages
- ❌ Never copy+delete manually
- ❌ Never skip tests
- ❌ Never batch unrelated changes

### Phase 3: Comprehensive Audit
```bash
# Run full audit
scripts/automation/repo_audit.sh full

# Review results
LATEST_AUDIT=$(ls -t docs/audits/REPO_AUDIT_*.md | head -1)
cat "${LATEST_AUDIT}"

# Check for issues to address
grep -E "FAILED|error|Error|ERROR" reports/audit/*/

# Address any critical issues found
```

### Phase 4: Final Verification
```bash
# Run full test suite
pytest -v

# Check git status
git status

# Review all changes
git log --oneline origin/main..HEAD

# Push for review
git push -u origin chore/repo-housekeeping-audit

# Create PR
gh pr create --title "chore: repo housekeeping and audit" \
  --body "$(cat <<EOF
## Summary
- Completed repository housekeeping scan
- Moved misplaced files to proper locations
- Removed obsolete backup files
- Ran comprehensive audit

## Audit Results
- See: docs/audits/REPO_AUDIT_*.md
- All tests passing: $(pytest --co -q | wc -l) tests

## Changes
- Organized file structure
- No breaking changes
- All tests passing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Available Scripts

### `scripts/automation/repo_housekeeping_scan.sh`
**Purpose**: Scan repository for housekeeping issues (no modifications)

**Detects**:
- Backup files (`.bak`, `.old`, etc.)
- Versioned filenames (`_old`, `_copy`, etc.)
- Misplaced markdown files (top-level → should be in docs/)
- Config files outside `config/`
- Duplicate `.gitignore` files
- Large files (>1MB)
- Archive analysis

**Output**:
- Raw scan data: `reports/housekeeping/scan_<timestamp>/`
- Cleanup plan: `reports/housekeeping/cleanup_plan_<timestamp>.md`

### `scripts/automation/repo_audit.sh [quick|full]`
**Purpose**: Comprehensive repository audit

**Checks**:
- Git status and inventory
- File hygiene (CRLF, tabs, TODO/FIXME)
- Python compilation
- Dependency integrity (`pip check`)
- Tests (`pytest`)
- Linting (`ruff`, `black`)
- Type checking (`mypy`, optional)
- Security (`bandit`, `pip-audit`, `gitleaks`, optional)

**Output**:
- Raw data: `reports/audit/<timestamp>/`
- Curated report: `docs/audits/REPO_AUDIT_<timestamp>.md` (committed)

## Safety Features

### Graceful Tool Detection
Both scripts check for tool availability and skip gracefully if not installed:
- ✓ `ruff`, `black`, `mypy` - Optional linting/formatting
- ✓ `bandit`, `pip-audit`, `gitleaks` - Optional security
- ✓ `tree` - Optional visualization
- ✅ `python`, `pytest`, `git` - Required

### No Silent Failures
- All operations logged to `_log.txt`
- Failed commands marked as `[FAILED]`
- Exit codes preserved in raw outputs

### Separation of Raw/Curated Data
- **Raw outputs** (`reports/audit/`, `reports/housekeeping/`): Not committed, full details
- **Curated reports** (`docs/audits/`): Committed, human-readable summaries

## Troubleshooting

### "Permission denied" when running scripts
```bash
chmod +x scripts/automation/*.sh
```

### Tests fail after moving files
```bash
# Revert the last commit
git reset --soft HEAD^

# Or restore specific file
git checkout HEAD -- path/to/file

# Re-run tests to verify
pytest -v
```

### Large .gitignore changes
Review carefully - ensure you're not accidentally ignoring tracked files:
```bash
git status --ignored
```

### Audit script times out
```bash
# Use quick mode for faster feedback
scripts/automation/repo_audit.sh quick

# Or increase timeout in script (edit repo_audit.sh)
```

## Best Practices

1. **Always branch**: Work in `chore/repo-housekeeping` or similar
2. **Test incrementally**: Run `pytest` after each logical change
3. **Commit atomically**: One type of change per commit
4. **Document decisions**: Update this file with any new patterns
5. **Review before merge**: Have another developer review structural changes

## Integration with CI/CD

Add to `.github/workflows/audit.yml`:
```yaml
name: Periodic Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run audit
        run: scripts/automation/repo_audit.sh quick
      - name: Upload audit report
        uses: actions/upload-artifact@v3
        with:
          name: audit-report
          path: docs/audits/
```

## Maintenance

- **Frequency**: Run housekeeping scan monthly or before major releases
- **Full audit**: Run quarterly or after significant refactoring
- **Quick audit**: Can run in CI on every PR (fast feedback)

## History

- 2025-12-16: Initial setup with housekeeping scan and audit scripts
