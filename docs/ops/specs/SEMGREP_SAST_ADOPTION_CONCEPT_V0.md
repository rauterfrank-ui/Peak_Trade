# SEMGREP / SAST ADOPTION CONCEPT V0

Documentation-only. This file does not authorize scans, CI changes, workflow dispatches, runtime execution, or any trading, broker, exchange, or order activity.

## 1. Purpose

Capture a **manual-first, default-off** adoption model for optional **Semgrep** (or similar static pattern matching) on Peak_Trade **without** requiring CI gates, paid remote services, or automatic remediation. The goal is **bounded security hygiene** for Python and GitHub Actions YAML surfaces that complements existing **docs-only** CI/secrets/artifacts governance.

## 2. Non-goals

- No **required** PR or merge-blocking CI gate in v0.
- No assumption of **paid** tokens, SaaS uploads, or organization-wide dashboards.
- No **automatic fixes**, bot commits, or “scanner says merge” workflows.
- No collection, printing, validation, rotation, inference, or storage of **real secret values**.
- No change to Master V2 / Double Play strategy semantics, Risk/KillSwitch, execution/live gates, schedulers, paper/testnet/live paths, broker/exchange APIs, Kraken interaction, or Uvicorn/runtime startup documented here.
- **AI ≠ Authority**, **Signal ≠ Trade**, **Docs ≠ Approval**: findings and this document are advisory inputs only.

## 3. v0 Adoption Model

- **Phase v0:** concept and operator discipline only — **documented**, not enforced by repo automation in this slice.
- **Phase next (explicit future PR):** optional **operator-run** local CLI usage, separately approved and never default-on for the whole org.
- **Phase later (explicit future PR):** optional **`workflow_dispatch` / manual-only** CI job pattern — never `schedule`-as-default, never required-on-PR unless a separate charter says otherwise.

Semgrep installation, execution, and any workflow edits are **out of scope** for this v0 markdown file alone.

## 4. Cursor Boundary

Cursor/agents **may**:

- Maintain or extend **this** conceptual doc and cross-links under `docs/` when explicitly tasked.
- Suggest **placeholder** command shapes and triage headings for humans to adapt locally.

Cursor/agents **must not**:

- Install or run Semgrep (or analogous tools) in automation without explicit operator approval.
- Edit `.github&#47;workflows&#47;**` except under a separate governance PR.
- Add dependencies, scanners, or secrets to the repo **as part of** this adoption concept slice.
- Read `.env*` or other likely secret-containing files “to validate” scans; treat secret-smell rules as **heuristic**, not proof.

## 5. Operator Boundary

Operators:

- Decide **when** (if ever) to install Semgrep locally and which rulesets to enable.
- Run scans only in environments appropriate for the repo (**no** forwarding of raw logs that might contain secrets to untrusted sinks).
- Keep **narrow** rule sets at first to control noise.

## 6. Suggested Manual Workflow

Placeholder shape only — **do not treat as runnable approval** inside CI:

1. Use a maintained Semgrep OSS install method on an operator workstation (outside this repo’s v0 scope).
2. Start with **narrow** rules (see §7): Python security/correctness subset, sparing GitHub Actions YAML checks.
3. Emit **report-only** output (stdout, SARIF, or JSON) kept **local** or in internal ticket systems without secret paste.
4. Triage findings (§8); open normal human-reviewed PRs for real issues.
5. Re-scan after fixes only if worthwhile; suppress false positives explicitly in-repo when justified (future change, not mandated here).

## 7. Ruleset Scope

Initial **narrow** intent:

| Area | Intent |
|------|--------|
| Python application code | Injection, dangerous `subprocess`, unsafe deserialization patterns; **scoped** paths, avoiding wholesale test-noise bursts |
| YAML / GitHub Actions | Risky shell patterns, permission surprises — **few** curated rules aligned with CI audit themes |
| Secret smell | Pattern-only hints in **tracked** source/workflows; **not** credential scanning proof |
| Explicitly cautious | Anything that floods the repo with style noise or misconstrues trading/execution paths as “auto-fixable” |

Broad community packs **without** tuning are explicitly discouraged for early adoption.

## 8. Findings Triage

- **Severity:** prioritize credible security/correctness; defer style-only churn.
- **Report-only:** no auto-fix pipelines tied to scanner output for v0 mental model.
- **Human review:** every code change arising from findings goes through normal review; **docs** alone never approve merges or runtime.

## 9. Future CI Considerations

If a separate PR ever adds CI:

- **Manual dispatch only** (`workflow_dispatch`), **not** on every PR by default for this adoption story.
- **No** artifact publishing that could leak environment or fork PR secret context.
- **No** schedules in the same PR as introducing Semgrep unless explicitly chartered.
- Reuse existing static workflow/secrets posture lessons from [`CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md`](../CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md).

## 10. Stop Conditions

Suspend or revert expansion if:

- Someone proposes **required merge gates** solely on Semgrep noise.
- Adoption **requires paid** SaaS subscriptions or uploads by default.
- Findings pipelines risk **printing or collecting real secrets**.
- Rulesets become **too broad** (lost signal, CI minutes burn, reviewer fatigue).
- Anyone attempts **automatic code modification** or agent-driven authority from scanner output alone.
- Anything ties scanning to live trading, brokers, exchanges, Kraken credentials, runtime schedulers not explicitly intended.

## 11. Relationship to Existing CI/Secrets/Artifacts Governance

This concept is **orthogonal** to dashboard or strategy workstreams and **anchors** beside the canonical **documentation-only** inventory in [`CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md`](../CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md). It does **not** duplicate Evidence/Readiness/Map package surfaces; it is a **single bounded spec** for optional static analysis posture.

Credential planning remains under human-gated paths such as [`RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md`](../runbooks/RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md).

## 12. Final Status Lines

```
SEMGREP_ADOPTION_DOC_VERSION=v0
SEMGREP_DEFAULT_OFF=true
SEMGREP_REQUIRED_CI_GATE=false
SEMGREP_MANUAL_OPERATOR_FIRST=true
SEMGREP_INSTALLED_REPO=false
AUTOMATIC_FIX=false
```
