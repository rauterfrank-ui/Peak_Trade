# Security Notes — Peak_Trade Cybersecurity Baseline Pointers

**Scope ID:** `PEAK_TRADE_CYBERSECURITY_BASELINE_REFRESH_V1`
**Capability overlay:** `CYBER_CI_SUPPLY_CHAIN_HARDENING_V1` (2026-07-26)
**Last Reviewed (repo-static):** 2026-07-26
**Mode:** Documentation + pointers to existing SSOT owners. **Non-authorizing.**
**Does not:** rotate secrets, change GitHub org/repo security toggles, enable live/testnet/orders, or claim unverified scanner results.

---

## 1. Canonical owners (reuse — no parallel cyber SSOT)

| Concern | Owner |
|---------|-------|
| Cybersecurity visibility / retained CI-Ops risks / release RC index | [`docs/ops/CI_AUDIT_KNOWN_ISSUES.md`](docs/ops/CI_AUDIT_KNOWN_ISSUES.md) (§ Cybersecurity …) |
| CI / Actions permissions, secrets, artifacts inventory | [`docs/ops/CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md`](docs/ops/CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md) |
| Operator credential / secret-handling boundaries | [`docs/ops/runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md`](docs/ops/runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md) |
| Local bounded secret env file contract | [`docs/ops/specs/LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md`](docs/ops/specs/LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md) |
| Optional Semgrep/SAST (default-off concept) | [`docs/ops/specs/SEMGREP_SAST_ADOPTION_CONCEPT_V0.md`](docs/ops/specs/SEMGREP_SAST_ADOPTION_CONCEPT_V0.md) |
| Optional ZAP/DAST (default-off concept) | [`docs/ops/specs/ZAP_DAST_SHADOW_CONCEPT_V0.md`](docs/ops/specs/ZAP_DAST_SHADOW_CONCEPT_V0.md) |
| Incident handling | [`docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`](docs/RUNBOOKS_AND_INCIDENT_HANDLING.md) |
| Disaster recovery | [`docs/DISASTER_RECOVERY_RUNBOOK.md`](docs/DISASTER_RECOVERY_RUNBOOK.md) |
| Required CI contexts (branch protection sync, repo-evidenced) | [`config/ci/required_status_checks.json`](config/ci/required_status_checks.json) |
| Dependency audit workflow | [`.github/workflows/audit.yml`](.github/workflows/audit.yml) |
| Manual full audit + optional SBOM export | [`.github/workflows/full_audit_weekly.yml`](.github/workflows/full_audit_weekly.yml) + [`scripts/ops/run_full_audit.sh`](scripts/ops/run_full_audit.sh) |

**Docs ≠ Approval. AI ≠ Authority. Secret names ≠ secret values.**

---

## 2. Python dependency / vulnerability posture (repo-evidenced)

### Support matrix

- `pyproject.toml`: `requires-python = ">=3.9"`
- CI / required tests context: **Python 3.11** (`tests (3.11)` in [`config/ci/required_status_checks.json`](config/ci/required_status_checks.json))
- Locking: `uv.lock` + generated `requirements.txt` (reproducible installs via `uv sync`)

### Version-conditional packages (still present in `requirements.txt`)

| Package | Python &lt;3.10 | Python ≥3.10 / CI 3.11 |
|---------|----------------|-------------------------|
| `filelock` | `3.19.1` | `3.20.1` |
| `mlflow` | `3.1.4` | `3.8.1` |
| `aiohttp` | `3.13.3` (all) | `3.13.3` (all) |

Historical remediation notes: [`docs/ops/AUDIT_DEPENDENCY_REMEDIATION_2026-01-07.md`](docs/ops/AUDIT_DEPENDENCY_REMEDIATION_2026-01-07.md) (snapshot; do not treat as live `pip-audit` proof).

### Audit policy (as implemented)

- PR/push workflow [`audit.yml`](.github/workflows/audit.yml) runs `pip-audit` on Python 3.11.
- Enforcement is **blocking only** when the PR touches dependency lock/manifest files; docs-only PRs treat findings as non-blocking artifacts.
- Manual [`run_full_audit.sh`](scripts/ops/run_full_audit.sh) can export a CycloneDX SBOM via `uv export` when an operator runs it — **not** a required PR gate.
- **This document does not claim** a current clean `pip-audit` result unless an operator records one with date, SHA, and artifact path.

### Recommendations

- Prefer local/CI Python **3.11** for security-relevant work.
- Do **not** mass-upgrade dependencies without a concrete advisory-driven reason and normal review.
- Python 3.9 remains a compatibility surface with older conditional pins; treat it as higher residual risk for local-only use.

---

## 3. Secret management & leak prevention (summary)

| Control | Repo-evidenced status |
|---------|----------------------|
| `.env` / `secrets.toml` / `*.pem` / `*_secret*` gitignore | Present in `.gitignore` |
| Tracked `.env.example` placeholders only | `docker/.env.example`, `.cursor/.env.example` |
| Workflow `secrets.*` name inventory (no values) | `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py` |
| GitHub Secret Protection / Push Protection | **Operator-stated** UI snapshot in credential runbook (2026-05-12) — **not** re-verified by this refresh; humans must re-check UI |
| gitleaks / detect-secrets in pre-commit | **Not** configured in `.pre-commit-config.yaml` |
| gitleaks as required PR check | **Not** present |
| Cursor/AI may access real secret values | **Forbidden** (credential runbook) |

**This refresh did not rotate any secrets and did not change external GitHub security settings.**

---

## 4. GitHub Actions supply-chain posture (summary)

Repo-static inventory after **`CYBER_CI_SUPPLY_CHAIN_HARDENING_V1`** (**2026-07-26**; see CI GHA audit index):

- **73** workflow files; **0** `pull_request_target`; **0** `permissions: write-all`
- External GitHub Actions are **full-SHA-pinned** (`uses: owner&#47;repo@<40-hex> # <tag>`): **231** refs / **21** unique actions; **0** floating `@main`/`@master`/`@latest`/`@head`; **0** tag-only external pins
- Readable release/version comments (`# vX…`) are retained for maintainability; upgrading an Action requires a deliberate SHA refresh (resolve the same tag/commit upstream, do not silently bump majors)
- **73 / 73** workflows declare explicit top-level `permissions:` (default baseline `contents: read`; `permissions: {}` only where GITHUB_TOKEN scopes are unused)
- Write-permission surfaces remain a narrow frozen allowlist via `tests/ci/test_workflow_write_permissions_visibility_contract_v0.py`
- Fail-closed regression owner: `tests/ci/test_cybersecurity_baseline_action_ref_and_permissions_visibility_contract_v0.py`

**Not claimed by this capability:** GitHub branch protection UI, push protection / secret scanning enablement, Dependabot/CodeQL org toggles, Runtime/Live authorization.

---

## 5. SAST / SBOM / scanning

| Capability | Status |
|------------|--------|
| Semgrep/SAST | Concept only, default-off ([SEMGREP_SAST_ADOPTION_CONCEPT_V0](docs/ops/specs/SEMGREP_SAST_ADOPTION_CONCEPT_V0.md)) |
| ZAP/DAST | Concept only, default-off |
| SBOM | Optional via `uv export` in manual full audit; artifact upload path exists in `full_audit_weekly.yml` |
| Provenance / SLSA attestations | **Not** implemented in-repo |
| Dependency vulnerability scan | `pip-audit` in `audit.yml` (+ manual full audit) |

---

## 6. Runtime / trading safety boundaries (pointers only)

Do **not** treat this file as live authorization. Relevant gates live in Master V2 / Double Play / risk / kill-switch / live-gate docs and code. Default operator posture for agent work:

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `SHADOW=false`
- `TESTNET=false`

Docs live-enable pattern guard: [`scripts/ci/check_docs_no_live_enable_patterns.sh`](scripts/ci/check_docs_no_live_enable_patterns.sh).

---

## 7. Residual risks & follow-ups (owner: ops)

| ID | Risk | Acceptance / follow-up |
|----|------|------------------------|
| RR-CB-001 | Actions tag-pinned, not SHA-pinned | **Closed** by `CYBER_CI_SUPPLY_CHAIN_HARDENING_V1` (full 40-hex SHA pins + regression contract) |
| RR-CB-002 | Many workflows lack explicit top-level `permissions:` | **Closed** by `CYBER_CI_SUPPLY_CHAIN_HARDENING_V1` (every workflow declares top-level permissions; write allowlist retained) |
| RR-CB-003 | No required secret-scanning job on every PR | Rely on GitHub Push Protection (operator-stated) + local discipline; optional gitleaks remains human-gated |
| RR-CB-004 | Semgrep/SAST not enforced | Accepted default-off per concept |
| RR-CB-005 | Python 3.9 conditional older pins | Prefer 3.11; drop 3.9 only via explicit support decision |
| RR-CB-006 | Branch-protection UI state not re-snapshotted in this refresh | Reuse `config/ci/required_status_checks.json`; human UI re-verify when needed |
| RR-CB-007 | `full_audit_weekly.yml` uses `uv` `version: "latest"` input | Residual; pin uv version in a future workflow hygiene PR |
| RR-CB-008 | Credential UI snapshot dated 2026-05-12 | Operator should re-verify Secret Protection / Push Protection in GitHub UI |

---

## 8. Explicit non-claims

This document and the baseline refresh **must not** be read as proof that:

- secrets were rotated,
- Dependabot / CodeQL / private vulnerability reporting were enabled,
- external org policies changed,
- live/testnet/orders/shadow were armed,
- or a full dependency CVE sweep was executed in this change.

---

**Audit Tooling references:** `pip-audit` (CI), `uv export` CycloneDX (manual), static workflow contract tests under `tests/ci/`.
