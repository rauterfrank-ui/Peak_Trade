## What changed

### Commits
- cf76dd4 ops(scripts): fix bg_job exitcode capture (avoid exec so trap writes .exit)
- 00c9593 ops: add background job runner for long-running commands
- b253b67 docs(ops): add merge log for PR #485
- 173855a docs: fix inline ignore marker position for ref target
- d07e216 docs: add inline ignore markers for legacy references
- 7a80345 docs: escape legacy reference targets in historical docs (strict CI)
- 74432ef docs(ops): use code blocks for triage lists to avoid ref-target validation
- fc96116 docs(ops): align docs drill A2 with CI parity; keep full-scan as optional audit
- d25a5eb ops(docs): add ignore list support to docs reference targets verifier
- 706a115 docs(ops): triage + fix priority reference targets (ops/risk)

### Files
- M	.gitignore
- M	docs/CONTRACT_VERIFICATION_FINAL.md
- M	docs/FINAL_VERIFICATION_SUMMARY.md
- M	docs/HARDENING_PATCH_SUMMARY.md
- M	docs/OPS_INSPECTOR_FULL.md
- M	docs/ops/DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md
- A	docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt
- A	docs/ops/DOCS_REFERENCE_TARGETS_TRIAGE_20260101.md
- M	docs/ops/PR_409_MERGE_LOG.md
- A	docs/ops/PR_485_MERGE_LOG.md
- M	docs/ops/README.md
- A	docs/ops/RUNBOOK_BACKGROUND_JOBS.md
- M	docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md
- M	docs/ops/merge_logs/2025-12-25_pr-347_docs-reference-targets-guardrail.md
- M	docs/risk/KILL_SWITCH_RUNBOOK.md
- M	docs/risk/RISK_METRICS_SCHEMA.md
- M	docs/risk/VAR_BACKTEST_GUIDE.md
- M	docs/risk/VAR_GATE_RUNBOOK.md
- A	scripts/ops/bg_job.sh
- M	scripts/ops/verify_docs_reference_targets.sh
