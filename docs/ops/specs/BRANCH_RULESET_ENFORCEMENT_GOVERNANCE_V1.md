# BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1

**Capability ID:** `BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1`  
**Mode:** Repository governance — enforced GitHub branch ruleset for the canonical integration branch, with fail-closed offline verification and regression contracts.  
**Does not:** alter trading/runtime/dashboard/strategy/risk/execution/capital/scheduler behavior, enable live/testnet/orders, grant admin bypass, rename required checks, or create a second required-check SSOT.

## Authority and ownership

| Role | Path |
|------|------|
| Required-check SSOT (unchanged) | [`config/ci/required_status_checks.json`](../../../config/ci/required_status_checks.json) |
| Ruleset enforcement contract | [`config/ci/branch_ruleset_enforcement_contract_v1.json`](../../../config/ci/branch_ruleset_enforcement_contract_v1.json) |
| Fail-closed verifier | [`scripts/ci/check_branch_ruleset_enforcement_governance_v1.py`](../../../scripts/ci/check_branch_ruleset_enforcement_governance_v1.py) |
| Sanitized API evidence (after) | [`branch_ruleset_enforcement_api_evidence_after_v1.json`](branch_ruleset_enforcement_api_evidence_after_v1.json) |
| Sanitized API evidence (before / rollback) | [`branch_ruleset_enforcement_api_evidence_before_v1.json`](branch_ruleset_enforcement_api_evidence_before_v1.json) |
| Regression contracts | [`tests/ci/test_branch_ruleset_enforcement_governance_v1.py`](../../../tests/ci/test_branch_ruleset_enforcement_governance_v1.py) |
| CI enforcement surface | [`.github/workflows/lint_gate.yml`](../../../.github/workflows/lint_gate.yml) step *Branch ruleset enforcement governance v1* (inside required context `Lint Gate`) |
| Complementary security pointers | [`SECURITY_NOTES.md`](../../../SECURITY_NOTES.md) |
| Prior capability — secret scanning / push protection | [`SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1.md`](SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1.md) |
| Prior capability — SHA-pinned Actions / explicit permissions | `CYBER_CI_SUPPLY_CHAIN_HARDENING_V1` (see SECURITY_NOTES) |
| Canonical redaction owner (unchanged) | [`scripts/security/secret_hygiene_redaction_v1.py`](../../../scripts/security/secret_hygiene_redaction_v1.py) |
| Canonical credential-hygiene scanner (unchanged) | [`scripts/ci/check_tracked_credential_hygiene_policy_v1.py`](../../../scripts/ci/check_tracked_credential_hygiene_policy_v1.py) |

**Reuse-before-new:** This capability extends existing CI/security governance owners. It does **not** introduce a second required-check baseline, second scanner, or second redaction owner.

## Canonical protected branch

- GitHub default branch (API): `main`
- Ruleset target include: `refs&#47;heads&#47;main`
- Enforcement mechanism: Repository ruleset `peak_trade` (`id=11192468`) with `enforcement=active` (not evaluate-only, not disabled)
- Classic branch protection on `main` remains as a complementary layer; required-check names stay owned by `config/ci/required_status_checks.json`

## Required reviews (canonical policy)

Preserves the existing solo-operator **PR-flow without mandatory approvals** while strengthening review hygiene flags:

| Setting | Value |
|---------|-------|
| Pull request required | **true** (ruleset `pull_request` rule) |
| Required approving review count | **0** (matches pre-existing classic protection policy) |
| Dismiss stale approvals | **true** (`dismiss_stale_reviews_on_push`) |
| Require approval of the latest reviewable push | **true** (applies when approvals &gt; 0) |
| Require conversation resolution | **true** |
| Code owner reviews | **false** (unchanged) |

## Required checks

Exact contexts must match the effective set from [`config/ci/required_status_checks.json`](../../../config/ci/required_status_checks.json) (`required_contexts` minus `ignored_contexts`).  
Do **not** rename workflow/job/matrix display names merely for implementation convenience. Drift (missing, extra, duplicate, or renamed contexts) fails closed.

`strict_required_status_checks_policy=true` (branch must be up to date before merge). Compatible: no merge queue is configured on this repository.

## Bypass / force-push / deletion

| Control | Policy |
|---------|--------|
| Bypass actors | **none** (`BROAD_BYPASS_ACTOR_COUNT=0`) |
| Hidden / unconditional admin bypass via ruleset | **forbidden** |
| Force push | **blocked** (`non_fast_forward` rule present) |
| Branch deletion | **blocked** (`deletion` rule present) |
| Emergency path | Operator-visible GitHub settings change with explicit GO; restore from before-evidence; never silent token/admin bypass in CI |

## API evidence contract

- Evidence schema: `branch_ruleset_enforcement_api_evidence_v1`
- Evidence must be sanitized (no tokens, Authorization headers, cookies, or credential-bearing command traces)
- Offline CI uses committed after-evidence; operators may re-verify with `--fetch`
- Verifier never prints credentials

## Failure semantics

Verifier exits non-zero when any of the following hold:

- ruleset absent / partial / malformed evidence
- `enforcement` is `disabled` or `evaluate`
- wrong target branch / empty include
- missing required rule types
- required-check set mismatch (including stale/renamed contexts)
- broad bypass actors present
- force-push or branch-deletion allowed (missing protective rules)

## CI integration

- Workflow: `lint_gate.yml` (required context name: `Lint Gate`)
- Top-level permissions unchanged (read-only; no write expansion)
- No `pull_request_target`
- No privileged live ruleset mutation from PR CI
- Third-party Actions remain full 40-hex SHA pinned
- Local equivalent: `python3 scripts/ci/check_branch_ruleset_enforcement_governance_v1.py`

## Operator recovery / rollback

1. Re-read live state: `python3 scripts/ci/check_branch_ruleset_enforcement_governance_v1.py --fetch --json`
2. If broken, restore ruleset from [`branch_ruleset_enforcement_api_evidence_before_v1.json`](branch_ruleset_enforcement_api_evidence_before_v1.json) via GitHub Settings → Rules → Rulesets, or `gh api` PUT using the before payload (operator action; not CI).
3. Re-verify after restore with `--fetch`.
4. Do **not** disable required checks or grant broad bypass to unblock merges without a separate explicit governance GO.

## Exact local reproduction commands

```bash
# Offline fail-closed verifier (CI equivalent)
python3 scripts/ci/check_branch_ruleset_enforcement_governance_v1.py
python3 scripts/ci/check_branch_ruleset_enforcement_governance_v1.py --json

# Live operator re-query (network; still redacts credentials from output)
python3 scripts/ci/check_branch_ruleset_enforcement_governance_v1.py --fetch --json

# Regression contracts
python3 -m pytest -q tests/ci/test_branch_ruleset_enforcement_governance_v1.py
```

## Explicit non-claims

This capability does not claim runtime/live authorization, order capability, merge of this PR, auto-merge enablement, or admin bypass usage.
