# Audit Scripts

This directory contains automation scripts to support the audit process.

## Planned Scripts

### `run_audit_snapshot.py`
Automated snapshot collection:
- Repository structure analysis
- File and directory counts
- Configuration file inventory
- Dependency analysis
- Quick security pattern checks (keywords only, no secrets output)

### `run_audit_commands.sh`
Batch execution of common audit commands:
- Test runs (`pytest`)
- Linter checks (`ruff`, `mypy`)
- Security scans (`gitleaks`, `detect-secrets`, `pip-audit`)
- Build validation
- CI policy verification

### `validate_audit_evidence.py`
Evidence validation:
- Check all findings reference evidence
- Verify evidence files exist
- Check for redaction of sensitive data
- Validate naming conventions

### `generate_audit_summary.py`
Summary report generation:
- Aggregate findings by severity
- Generate risk matrix visualization
- Create compliance checklist
- Export to various formats (MD, HTML, JSON)

## Usage

Scripts should be run from the repository root:

```bash
cd /Users/frnkhrz/Peak_Trade

# Example: Run snapshot
python scripts/audit/run_audit_snapshot.py --output docs/audit/evidence/snapshots/

# Example: Run command suite
bash scripts/audit/run_audit_commands.sh --redact --output docs/audit/evidence/commands/
```

## Guidelines

- All scripts must support `--dry-run` mode
- All scripts must support `--redact` flag to automatically redact sensitive data
- Never execute live trades or make live API calls
- Always include timestamps and commit hash in outputs
- Write outputs to `docs/audit/evidence/` subdirectories
- Log all executed commands for reproducibility
