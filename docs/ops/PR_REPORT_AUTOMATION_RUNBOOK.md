# PR Final Report Automation – Runbook

**Purpose**: Generate and validate PR final reports in standardized markdown format.

---

## Quick Reference

### Generate a PR Report

```bash
bash scripts/automation/generate_pr_report.sh <PR_NUMBER>
```

**Example**:
```bash
bash scripts/automation/generate_pr_report.sh 59
```

**Output**: `docs&#47;ops&#47;PR_<NUMBER>_FINAL_REPORT.md`

**Requirements**:
- `gh` CLI installed and authenticated
- PR must exist and be accessible via GitHub API

---

### Validate All PR Reports

```bash
bash scripts/automation/validate_all_pr_reports.sh
```

**What it does**:
- Finds all `docs&#47;ops&#47;PR_*_FINAL_REPORT.md` files
- Validates each using `scripts/validate_pr_report_format.sh`
- Returns exit code 0 if all pass, 1 if any fail

**Safe to run**:
- Returns exit 0 if no reports found (CI-friendly)
- No side effects (read-only validation)

---

### Validate Single Report

```bash
bash scripts/validate_pr_report_format.sh docs/ops/PR_59_FINAL_REPORT.md
```

**Exit codes**:
- `0`: Validation passed
- `1`: Invalid arguments
- `2`: Double backticks at list start (e.g., `- ``` instead of `- ` `)
- `3`: Missing closing backtick in `src&#47;*` paths
- `4`: Missing closing backtick in `tests&#47;*` paths
- `5`: Missing PR header (`# PR #<number>`)
- `6`: Missing "Changed Files" section
- `7`: Empty "Changed Files" section (no files listed)

---

## Common Validation Failures

### 1. Double Backticks at List Start

**Symptom**:
```
ERROR: Broken markdown list formatting detected (double backticks).
Offending lines:
42:- ``src/data/feeds/offline_realtime_feed.py
```

**Cause**: Script error generating file list with extra backtick

**Fix**: Ensure file list generation uses single backtick:
```bash
printf -- "- \`%s\`\n" "$path"  # Correct
```

---

### 2. Missing Closing Backtick

**Symptom**:
```
ERROR: Likely missing closing backtick in src/* bullet line(s).
Offending lines:
58:- `src/data/safety/data_safety_gate.py
```

**Cause**: Inline backtick in filename or truncation error

**Fix**: Ensure every path has closing backtick:
```markdown
- `src/data/safety/data_safety_gate.py`  ✅
- `src/data/safety/data_safety_gate.py   ❌
```

---

### 3. Empty Changed Files Section

**Symptom**:
```
ERROR: Changed Files section is empty (no files listed)
```

**Cause**: `gh pr view` returned no files or list generation failed

**Fix**:
- Verify PR has changed files: `gh pr view <PR> --json files`
- Check `FILES_LIST` variable in generation script

---

## CI Integration

**Workflow**: `.github/workflows/audit.yml`

**Step**:
```yaml
- name: Validate PR final report formatting
  run: |
    chmod +x scripts/validate_pr_report_format.sh
    chmod +x scripts/automation/validate_all_pr_reports.sh
    bash scripts/automation/validate_all_pr_reports.sh
```

**Runs on**:
- Push to `main`
- Pull requests
- Manual dispatch
- Scheduled (weekly)

**Failure behavior**:
- Validation failures block CI
- Offending lines printed to workflow log
- Exit code indicates failure type

---

## Post-Generation Checklist

After generating a new PR report, verify:

- [ ] **Header**: `# PR #<number>` present
- [ ] **Metadata**: PR link, title, state, branch, merge commit
- [ ] **Changed Files**: Section exists and contains file list
- [ ] **File List Format**: All bullets use single backticks `` `path` ``
- [ ] **Links**: PR URL is valid and clickable
- [ ] **Validation**: `bash scripts/validate_pr_report_format.sh <report>` passes

---

## Where to Update Index

After creating a new PR final report:

1. **Add entry** to `docs/ops/README.md` under **Audit Logs** section
2. **Format**: Link to the generated report file (see example below)
3. **Order**: Descending (newest first)

**Example**:
```markdown
## Audit Logs

- [PR #59](PR_59_FINAL_REPORT.md) – OFFLINE Realtime Feed: Inspect CLI + Dashboard + Runbook
- [PR #53](PR_53_FINAL_REPORT.md) – RL v0.1 Contract Tests + Smoke Suites
```

---

## Troubleshooting

### Script not executable
```bash
chmod +x scripts/validate_pr_report_format.sh
chmod +x scripts/automation/validate_all_pr_reports.sh
chmod +x scripts/automation/generate_pr_report.sh
```

### Validator not found in CI
- Ensure scripts are committed to repo
- Check paths in workflow YAML match actual locations

### No reports found (local)
- Reports must match pattern: `docs&#47;ops&#47;PR_*_FINAL_REPORT.md`
- Check naming convention (underscore, not dash)

---

## Manual Validation Example

```bash
# Generate report for PR #66
bash scripts/automation/generate_pr_report.sh 66

# Validate single report
bash scripts/validate_pr_report_format.sh docs/ops/PR_66_FINAL_REPORT.md

# Validate all reports
bash scripts/automation/validate_all_pr_reports.sh
```

**Expected output**:
```
Validating 8 PR final report(s)...
==> docs/ops/PR_45_FINAL_REPORT.md
✅ Format validation passed: docs/ops/PR_45_FINAL_REPORT.md
==> docs/ops/PR_51_FINAL_REPORT.md
✅ Format validation passed: docs/ops/PR_51_FINAL_REPORT.md
...
All PR final reports passed validation.
```

---

## Contact

For issues or improvements to this automation:
- Create issue in Peak_Trade repo
- Tag with `ops` / `automation` labels
- Include error output and offending report file
