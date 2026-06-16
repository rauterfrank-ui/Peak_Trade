# CI / GitHub Actions Permissions, Secrets, and Artifacts Audit Index v0

## Status

This is a documentation-only audit index for GitHub Actions / CI permissions, secrets, artifacts, dispatch, and shell-risk surfaces. It records the current static audit surface and proposes safe follow-up directions without changing workflow behavior.

This document is not an authorization surface. It does not authorize workflow dispatches, CI behavior changes, runtime execution, scheduler/daemon control, testnet/live activity, broker/exchange/order activity, or any trading-logic change.

## Source

- Feasibility report: `/tmp/peak_trade_ci_permissions_secrets_artifact_audit_feasibility_20260510T172521Z/CI_PERMISSIONS_SECRETS_ARTIFACT_AUDIT_FEASIBILITY.md`
- Workflow directory: `.github/workflows/`
- Workflow files inventoried: `73`

## Boundary

Out of scope for this index:

- workflow behavior changes
- production code changes
- workflow dispatches
- script execution
- GitHub API calls
- scheduler/daemon/runtime execution
- paper/shadow/testnet/live execution
- broker/exchange/order-submission paths
- Master V2 / Double Play semantics
- Scope/Capital, Risk/KillSwitch, Execution/Live Gates
- dashboard authority, AI authority, strategy live authority
- hot-path changes
- duplicate Evidence, Readiness, Map, Registry, Handoff, Package, or Pointer surfaces

## Access parking note: Tailscale + next secret-handling planning layer

Tailscale / private access architecture was **reviewed** for Peak_Trade and is **`parked_not_discarded`** (not rejected).

- **`local_only`** remains the **default** for dashboard/admin/ops-style surfaces.
- **No** Tailscale install, account/tailnet setup, network changes, or runtime/workflow changes are approved **by this note**.
- **No** public dashboard exposure, **Tailscale Funnel**, or **open admin ports** are approved **by this note**.

**Revisit triggers** (human-led planning only): dashboard/admin/ops access from another device; hosting on a separate machine/server/VPS/NAS; private Shadow/Testnet/Ops monitoring across machines; operational need to avoid public dashboard exposure or open admin ports **without** granting trading or gate authority.

**Secret Handling** (e.g. GitHub org/repo policies, CI secrets posture, operator vaults, local bounded env discipline) is the **next planning layer** and stays **human-gated**. Cursor/AI may draft **docs-only** material (names, examples, pointers) and must **never** see, print, validate, rotate, fetch, or infer **real** secret values.

Docs-only marker — **not** a Tailscale runbook, **not** implementation approval, **not** a CI or trading authorization.

**Secret Handling (planning-first) operator runbook:** [RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md](runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md) — Cursor/docs boundaries, human-only GitHub/vault/credential work; **non-authorizing**.

## Workflow Surface Counts

- Total workflow files: `73`
- `workflow_dispatch`: `59`
- `pull_request_target`: `0`
- `permissions:` blocks: `39`
- `secrets.*` references: `16`
- `GITHUB_TOKEN` references: `4`
- `actions&#47;upload-artifact`: `42`
- `actions&#47;download-artifact`: `1`
- `retention-days`: `36`
- `curl` / `wget` / `gh` markers: `9`
- any `*: write` permission markers: `10`
- `actions: write`: `4`
- `contents: write`: `2`
- `id-token: write`: `1`

## Notable Safety Observations

- `pull_request_target` was not found in the static workflow inventory.
- `secrets.*`, artifact upload/download, and manual dispatch surfaces are present and should remain covered by narrow static contracts rather than broad workflow rewrites.
- Existing static workflow/dispatch contract tests should be reused before adding new validators.

## Optional Semgrep/SAST Adoption Concept (default-off)

Optional static-pattern analysis (**Semgrep** or similar) is documented only as a **manual-first, default-off** posture in [`specs&#47;SEMGREP_SAST_ADOPTION_CONCEPT_V0.md`](specs&#47;SEMGREP_SAST_ADOPTION_CONCEPT_V0.md). That spec is non-authorizing, does **not** add workflows or gates by itself, and defers installs, scans, and any **`workflow_dispatch`** automation to explicit future PRs consistent with this index boundary.

## Optional ZAP/DAST Shadow–Staging Adoption Concept (default-off)

Optional dynamic analysis (**OWASP ZAP** or similar **DAST**) against **explicitly allowlisted** local/shadow/staging HTTP surfaces is documented only as a **manual-first, default-off** posture in [`specs&#47;ZAP_DAST_SHADOW_CONCEPT_V0.md`](specs&#47;ZAP_DAST_SHADOW_CONCEPT_V0.md). That spec is non-authorizing, does **not** add workflows, installs, scans, targets, or web-server starts by itself, and defers any execution and **`workflow_dispatch`** automation to explicit future PRs consistent with this index boundary (no live/public targets by default; passive/baseline default until explicitly approved).

## Workflow Files By Signal

### `workflow_dispatch`

- `.github/workflows/aiops-promptfoo-evals.yml`
- `.github/workflows/aiops-trend-ledger-from-seed.yml`
- `.github/workflows/audit.yml`
- `.github/workflows/ci-export-pack-download-verify.yml`
- `.github/workflows/ci-operator-verify-registry.yml`
- `.github/workflows/ci-scheduled-paper-and-export-smoke.yml`
- `.github/workflows/ci-workflow-dispatch-guard.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/ci_recon_audit_gate_smoke.yml`
- `.github/workflows/class-a-shadow-paper-scheduled-probe-v1.yml`
- `.github/workflows/cursor_auto_automerge.yml`
- `.github/workflows/cursor_auto_pr.yml`
- `.github/workflows/deps_sync_guard.yml`
- `.github/workflows/docs-token-policy-gate.yml`
- `.github/workflows/docs_diff_guard_policy_gate.yml`
- `.github/workflows/docs_reference_targets_fullscan_schedule.yml`
- `.github/workflows/docs_reference_targets_gate.yml`
- `.github/workflows/evidence_pack_gate.yml`
- `.github/workflows/full_audit_weekly.yml`
- `.github/workflows/infostream-automation.yml`
- `.github/workflows/knowledge_extras_chromadb.yml`
- `.github/workflows/l4_critic_replay_determinism.yml`
- `.github/workflows/lint_gate.yml`
- `.github/workflows/market_outlook_automation.yml`
- `.github/workflows/master_v2_dry_smoke.yml`
- `.github/workflows/mcp_smoke_preflight.yml`
- `.github/workflows/merge_log_hygiene.yml`
- `.github/workflows/offline_suites.yml`
- `.github/workflows/ops_doctor_dashboard.yml`
- `.github/workflows/ops_doctor_pages.yml`
- `.github/workflows/optional-deps-gate.yml`
- `.github/workflows/paper_session_audit_evidence.yml`
- `.github/workflows/paper_session_telemetry_summary.yml`
- `.github/workflows/paper_tests_audit_evidence.yml`
- `.github/workflows/policy_critic_gate.yml`
- `.github/workflows/policy_tracked_reports_guard.yml`
- `.github/workflows/prbc-stability-gate.yml`
- `.github/workflows/prbd-live-readiness-scorecard.yml`
- `.github/workflows/prbe-shadow-testnet-scorecard.yml`
- `.github/workflows/prbg-execution-evidence.yml`
- `.github/workflows/prbi-live-pilot-scorecard.yml`
- `.github/workflows/prbj-testnet-exec-events.yml`
- `.github/workflows/prcc-aws-export-smoke.yml`
- `.github/workflows/prcd-aws-export-write-smoke.yml`
- `.github/workflows/prj-scheduled-shadow-paper-features-smoke.yml`
- `.github/workflows/prk-prj-status-report.yml`
- `.github/workflows/pro-prk-nightly-selfcheck.yml`
- `.github/workflows/pru-required-checks-drift-detector.yml`
- `.github/workflows/quarto_smoke.yml`
- `.github/workflows/real-market-forward-evidence-smoke.yml`
- `.github/workflows/replay_compare_report.yml`
- `.github/workflows/shadow_paper_smoke.yml`
- `.github/workflows/test-health-automation.yml`
- `.github/workflows/test_health.yml`
- `.github/workflows/truth_gates_pr.yml`
- `.github/workflows/typecheck-mypy.yml`
- `.github/workflows/typecheck-pyright.yml`
- `.github/workflows/var_report_regression_gate.yml`
- `.github/workflows/weekly_core_audit.yml`

### `permissions`

- `.github/workflows/aiops-trend-ledger-from-seed.yml`
- `.github/workflows/aiops-trend-seed-from-normalized-report.yml`
- `.github/workflows/ci-export-pack-download-verify.yml`
- `.github/workflows/ci-operator-verify-registry.yml`
- `.github/workflows/ci-pr-merge-state-signal.yml`
- `.github/workflows/ci-scheduled-paper-and-export-smoke.yml`
- `.github/workflows/class-a-shadow-paper-scheduled-probe-v1.yml`
- `.github/workflows/cursor_auto_automerge.yml`
- `.github/workflows/cursor_auto_pr.yml`
- `.github/workflows/docs-integrity-snapshot.yml`
- `.github/workflows/docs_reference_targets_fullscan_schedule.yml`
- `.github/workflows/infostream-automation.yml`
- `.github/workflows/l4_critic_replay_determinism_v2.yml`
- `.github/workflows/lint_gate.yml`
- `.github/workflows/merge-logs-sanity.yml`
- `.github/workflows/ops_doctor_dashboard.yml`
- `.github/workflows/ops_doctor_pages.yml`
- `.github/workflows/paper_session_audit_evidence.yml`
- `.github/workflows/paper_session_telemetry_summary.yml`
- `.github/workflows/paper_tests_audit_evidence.yml`
- `.github/workflows/policy_critic.yml`
- `.github/workflows/policy_critic_gate.yml`
- `.github/workflows/policy_tracked_reports_guard.yml`
- `.github/workflows/pr-head-sha-required-checks-liveness-guard.yml`
- `.github/workflows/prbc-stability-gate.yml`
- `.github/workflows/prbd-live-readiness-scorecard.yml`
- `.github/workflows/prbe-shadow-testnet-scorecard.yml`
- `.github/workflows/prbg-execution-evidence.yml`
- `.github/workflows/prbi-live-pilot-scorecard.yml`
- `.github/workflows/prbj-testnet-exec-events.yml`
- `.github/workflows/prcc-aws-export-smoke.yml`
- `.github/workflows/prcd-aws-export-write-smoke.yml`
- `.github/workflows/prj-scheduled-shadow-paper-features-smoke.yml`
- `.github/workflows/prk-prj-status-report.yml`
- `.github/workflows/pro-prk-nightly-selfcheck.yml`
- `.github/workflows/pru-required-checks-drift-detector.yml`
- `.github/workflows/real-market-forward-evidence-smoke.yml`
- `.github/workflows/shadow_paper_smoke.yml`
- `.github/workflows/weekly_core_audit.yml`

### `secrets`

- `.github/workflows/add-to-project.yml`
- `.github/workflows/aiops-promptfoo-evals.yml`
- `.github/workflows/ci-export-pack-download-verify.yml`
- `.github/workflows/ci-operator-verify-registry.yml`
- `.github/workflows/ci-scheduled-paper-and-export-smoke.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/cursor_auto_automerge.yml`
- `.github/workflows/cursor_auto_pr.yml`
- `.github/workflows/infostream-automation.yml`
- `.github/workflows/market_outlook_automation.yml`
- `.github/workflows/paper_session_audit_evidence.yml`
- `.github/workflows/paper_tests_audit_evidence.yml`
- `.github/workflows/pr-head-sha-required-checks-liveness-guard.yml`
- `.github/workflows/prbj-testnet-exec-events.yml`
- `.github/workflows/prcc-aws-export-smoke.yml`
- `.github/workflows/prcd-aws-export-write-smoke.yml`

### `github_token`

- `.github/workflows/ci-operator-verify-registry.yml`
- `.github/workflows/cursor_auto_automerge.yml`
- `.github/workflows/cursor_auto_pr.yml`
- `.github/workflows/pr-head-sha-required-checks-liveness-guard.yml`

### `upload_artifact`

- `.github/workflows/aiops-promptfoo-evals.yml`
- `.github/workflows/aiops-trend-ledger-from-seed.yml`
- `.github/workflows/aiops-trend-seed-from-normalized-report.yml`
- `.github/workflows/audit.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/class-a-shadow-paper-scheduled-probe-v1.yml`
- `.github/workflows/docs-integrity-snapshot.yml`
- `.github/workflows/docs-token-policy-gate.yml`
- `.github/workflows/evidence_pack_gate.yml`
- `.github/workflows/full_audit_weekly.yml`
- `.github/workflows/infostream-automation.yml`
- `.github/workflows/knowledge_extras_chromadb.yml`
- `.github/workflows/l4_critic_replay_determinism.yml`
- `.github/workflows/l4_critic_replay_determinism_v2.yml`
- `.github/workflows/market_outlook_automation.yml`
- `.github/workflows/offline_suites.yml`
- `.github/workflows/ops_doctor_dashboard.yml`
- `.github/workflows/ops_doctor_pages.yml`
- `.github/workflows/paper_session_audit_evidence.yml`
- `.github/workflows/paper_session_telemetry_summary.yml`
- `.github/workflows/paper_tests_audit_evidence.yml`
- `.github/workflows/policy_critic.yml`
- `.github/workflows/pr-head-sha-required-checks-liveness-guard.yml`
- `.github/workflows/prbc-stability-gate.yml`
- `.github/workflows/prbd-live-readiness-scorecard.yml`
- `.github/workflows/prbe-shadow-testnet-scorecard.yml`
- `.github/workflows/prbg-execution-evidence.yml`
- `.github/workflows/prbi-live-pilot-scorecard.yml`
- `.github/workflows/prbj-testnet-exec-events.yml`
- `.github/workflows/prcc-aws-export-smoke.yml`
- `.github/workflows/prcd-aws-export-write-smoke.yml`
- `.github/workflows/prj-scheduled-shadow-paper-features-smoke.yml`
- `.github/workflows/prk-prj-status-report.yml`
- `.github/workflows/pro-prk-nightly-selfcheck.yml`
- `.github/workflows/quarto_smoke.yml`
- `.github/workflows/real-market-forward-evidence-smoke.yml`
- `.github/workflows/replay_compare_report.yml`
- `.github/workflows/required-checks-hygiene-gate.yml`
- `.github/workflows/shadow_paper_smoke.yml`
- `.github/workflows/test-health-automation.yml`
- `.github/workflows/test_health.yml`
- `.github/workflows/var_report_regression_gate.yml`

### `download_artifact`

- `.github/workflows/evidence_pack_gate.yml`

### `retention_days`

- `.github/workflows/aiops-promptfoo-evals.yml`
- `.github/workflows/aiops-trend-ledger-from-seed.yml`
- `.github/workflows/aiops-trend-seed-from-normalized-report.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/class-a-shadow-paper-scheduled-probe-v1.yml`
- `.github/workflows/docs-integrity-snapshot.yml`
- `.github/workflows/docs-token-policy-gate.yml`
- `.github/workflows/evidence_pack_gate.yml`
- `.github/workflows/full_audit_weekly.yml`
- `.github/workflows/infostream-automation.yml`
- `.github/workflows/knowledge_extras_chromadb.yml`
- `.github/workflows/l4_critic_replay_determinism.yml`
- `.github/workflows/l4_critic_replay_determinism_v2.yml`
- `.github/workflows/offline_suites.yml`
- `.github/workflows/ops_doctor_dashboard.yml`
- `.github/workflows/ops_doctor_pages.yml`
- `.github/workflows/policy_critic.yml`
- `.github/workflows/pr-head-sha-required-checks-liveness-guard.yml`
- `.github/workflows/prbc-stability-gate.yml`
- `.github/workflows/prbd-live-readiness-scorecard.yml`
- `.github/workflows/prbe-shadow-testnet-scorecard.yml`
- `.github/workflows/prbg-execution-evidence.yml`
- `.github/workflows/prbi-live-pilot-scorecard.yml`
- `.github/workflows/prbj-testnet-exec-events.yml`
- `.github/workflows/prcc-aws-export-smoke.yml`
- `.github/workflows/prcd-aws-export-write-smoke.yml`
- `.github/workflows/prj-scheduled-shadow-paper-features-smoke.yml`
- `.github/workflows/prk-prj-status-report.yml`
- `.github/workflows/pro-prk-nightly-selfcheck.yml`
- `.github/workflows/quarto_smoke.yml`
- `.github/workflows/real-market-forward-evidence-smoke.yml`
- `.github/workflows/replay_compare_report.yml`
- `.github/workflows/required-checks-hygiene-gate.yml`
- `.github/workflows/test-health-automation.yml`
- `.github/workflows/test_health.yml`
- `.github/workflows/var_report_regression_gate.yml`

### `curl_wget_gh`

- `.github/workflows/aiops-trend-ledger-from-seed.yml`
- `.github/workflows/ci-operator-verify-registry.yml`
- `.github/workflows/ci-scheduled-paper-and-export-smoke.yml`
- `.github/workflows/policy_critic.yml`
- `.github/workflows/prbd-live-readiness-scorecard.yml`
- `.github/workflows/prbe-shadow-testnet-scorecard.yml`
- `.github/workflows/prbg-execution-evidence.yml`
- `.github/workflows/prbi-live-pilot-scorecard.yml`
- `.github/workflows/prk-prj-status-report.yml`

### `write_permissions`

- `.github/workflows/aiops-promptfoo-evals.yml`
- `.github/workflows/ci-scheduled-paper-and-export-smoke.yml`
- `.github/workflows/cursor_auto_automerge.yml`
- `.github/workflows/cursor_auto_pr.yml`
- `.github/workflows/infostream-automation.yml`
- `.github/workflows/ops_doctor_pages.yml`
- `.github/workflows/paper_session_audit_evidence.yml`
- `.github/workflows/policy_critic.yml`
- `.github/workflows/prbg-execution-evidence.yml`
- `.github/workflows/weekly_core_audit.yml`

### `actions_write`

- `.github/workflows/ci-scheduled-paper-and-export-smoke.yml`
- `.github/workflows/cursor_auto_pr.yml`
- `.github/workflows/paper_session_audit_evidence.yml`
- `.github/workflows/weekly_core_audit.yml`

### `contents_write`

- `.github/workflows/cursor_auto_automerge.yml`
- `.github/workflows/infostream-automation.yml`

### `id_token_write`

- `.github/workflows/ops_doctor_pages.yml`

### `pull_request_target`

- none

## Existing Related Tests / Guards

Existing tests should be extended before new parallel surfaces are created.

### Workflow contract-style tests

- `tests/ci/test_ci_export_pack_download_verify_workflow_contract_v0.py`
- `tests/ci/test_ci_scheduled_paper_export_smoke_workflow_contract_v0.py`
- `tests/ci/test_class_a_shadow_paper_scheduled_probe_workflow_contract_v0.py`
- `tests/ci/test_paper_session_audit_evidence_workflow_contract_v0.py`
- `tests/ci/test_paper_tests_audit_evidence_workflow_contract_v0.py`
- `tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py`
- `tests/ci/test_prj_scheduled_shadow_paper_features_smoke_workflow_contract_v0.py`
- `tests/ci/test_shadow_paper_smoke_workflow_contract_v0.py`

### Broader CI / dispatch / artifact / guard tests

- `tests/ci/test_check_docs_diff_guard_section_contract_v0.py`
- `tests/ci/test_ci_export_pack_download_verify_workflow_contract_v0.py`
- `tests/ci/test_ci_scheduled_paper_export_smoke_workflow_contract_v0.py`
- `tests/ci/test_class_a_shadow_paper_scheduled_probe_workflow_contract_v0.py`
- `tests/ci/test_paper_session_audit_evidence_workflow_contract_v0.py`
- `tests/ci/test_paper_tests_audit_evidence_workflow_contract_v0.py`
- `tests/ci/test_pr_head_sha_required_checks_liveness_guard.py`
- `tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py`
- `tests/ci/test_prj_scheduled_shadow_paper_features_smoke_workflow_contract_v0.py`
- `tests/ci/test_shadow_paper_smoke_workflow_contract_v0.py`
- `tests/ci/test_workflow_no_fallback_policy_json.py`
- `tests/ops/test_autofix_docs_token_policy_inline_code_smoke.py`
- `tests/ops/test_aws_export_smoke_contract.py`
- `tests/ops/test_aws_export_write_smoke_contract.py`
- `tests/ops/test_check_docs_drift_guard.py`
- `tests/ops/test_execution_guards.py`
- `tests/ops/test_fetch_prk_dashboard_artifacts_syntax.py`
- `tests/ops/test_generate_evidence_entry_smoke.py`
- `tests/ops/test_generate_placeholder_reports_smoke.py`
- `tests/ops/test_knowledge_prod_smoke_script.py`
- `tests/ops/test_ma_smoke.py`
- `tests/ops/test_mcp_smoke_check_contract_v0.py`
- `tests/ops/test_mcp_smoke_preflight_syntax.py`
- `tests/ops/test_ops_center_smoke.py`
- `tests/ops/test_ops_run_helpers_adoption_guard.py`
- `tests/ops/test_p7_ctl_cli_smoke.py`
- `tests/ops/test_pipeline_cli_smoke.py`
- `tests/ops/test_validate_docs_token_policy_smoke.py`
- `tests/ops/test_validate_evidence_index_smoke.py`
- `tests/ops/test_validate_workflow_dispatch_guards.py`
- `tests/ops/test_verify_git_rescue_artifacts_contract_v0.py`
- `tests/ops/test_verify_registry_pointer_artifacts_smoke.py`
- `tests/ops/test_workflow_officer.py`
- `tests/ops/test_workflow_officer_markdown.py`
- `tests/ops/test_workflow_officer_schema.py`

## Recommended Follow-Up Candidates

1. **Static no-`pull_request_target` meta-contract** if no existing test already owns that invariant.
2. **Artifact retention visibility contract** for workflows that upload artifacts without explicit retention, if confirmed.
3. **Permissions visibility contract** for workflows with write permissions, limited to documentation/tests-only classification first.
4. **Secrets-reference visibility contract** only for workflows where existing tests do not already freeze secret-reference boundaries.

## Reuse-Before-New Rule

Before implementing any follow-up, inventory existing tests under `tests/ci/` and `tests/ops/` and extend an existing owner if one exists. Create a new test file only when no clear owner exists.

## Proposed Validation For Future Tests-Only Slices

- targeted `uv run pytest <new-or-extended-test-file> -q`
- targeted `uv run ruff check <new-or-extended-test-file>`
- targeted `uv run ruff format --check <new-or-extended-test-file>`
- `git diff --check`

## Final Verdict

`CI_GITHUB_ACTIONS_AUDIT_INDEX_V0_READY=true`

`IMPLEMENT_NOW=false`

`NO_LOGIC_CHANGE=true`

`NO_PERFORMANCE_REGRESSION=true`

`NEXT_ACTION=review_index_then_choose_small_tests_only_followup`
