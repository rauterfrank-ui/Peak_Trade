# Audit Evidence

This directory contains all supporting evidence collected during the audit process.

## Directory Structure

```
evidence/
├── snapshots/     # System state snapshots (repo structure, configs, etc.)
├── commands/      # Command output logs (tests, scans, validation runs)
├── ci/            # CI/CD pipeline logs and artifacts
└── screenshots/   # Visual evidence (dashboards, alerts, etc.)
```

## Evidence Naming Convention

Format: `{category}_{YYYYMMDD}_{HHMMSS}_{commit_short}_{description}`

Examples:
- `repo_tree_20251230_120000_fb82934_full.txt`
- `pytest_results_20251230_130000_fb82934_all_tests.txt`
- `secrets_scan_20251230_140000_fb82934_gitleaks.txt`
- `ci_run_20251230_150000_fb82934_policy_check.log`

## Evidence Guidelines

### DO:
- Include timestamps and commit hashes in all artifacts
- Redact sensitive information (API keys, secrets, credentials, PII)
- Document the exact command/procedure used to generate each piece of evidence
- Cross-reference evidence to findings using EV-XXXX IDs from EVIDENCE_INDEX.md

### DON'T:
- Include actual secrets or credentials (even in "redacted" form - use placeholders like `***REDACTED***`)
- Make live API calls or execute live trades for evidence gathering
- Include unnecessarily large files (summarize or excerpt instead)
- Lose reproducibility - always document how evidence was collected

## Subdirectory Guidelines

### snapshots/
- Repository structure exports
- Configuration file snapshots
- System state captures
- Database schema exports (if applicable)

### commands/
- Test execution results (`pytest`, unit tests, integration tests)
- Linter and type checker outputs (`ruff`, `mypy`)
- Security scan results (`gitleaks`, `detect-secrets`, `pip-audit`)
- Build and validation commands
- Grep/search results for code patterns

### ci/
- CI pipeline run logs
- Policy enforcement results
- Build artifacts metadata
- Deployment verification logs

### screenshots/
- Monitoring dashboard views
- Alerting configurations
- Admin panel screenshots (with sensitive data redacted)
- Grafana/Prometheus queries and results

## Evidence Lifecycle

1. **Collection:** Evidence gathered during audit phases
2. **Cataloging:** Logged in EVIDENCE_INDEX.md with unique EV-XXXX ID
3. **Reference:** Linked from findings and audit report
4. **Retention:** Kept for compliance and future audit reference
5. **Archival:** Moved to archive after audit cycle complete (retain per policy)

## Redaction Guidelines

When redacting sensitive information, use clear placeholders:

```
# Good redaction
API_KEY=***REDACTED***
exchange_secret=***REDACTED_32_CHARS***

# Bad redaction (still reveals partial info)
API_KEY=sk_live_abc...xyz
```

For logs with sensitive data, use tools like `sed` to redact before saving:
```bash
command | sed 's/api_key=[^&]*/api_key=***REDACTED***/g' > evidence.txt
```
