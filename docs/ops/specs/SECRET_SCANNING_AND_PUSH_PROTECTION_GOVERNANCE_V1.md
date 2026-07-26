# SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1

**Capability ID:** `SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1`  
**Mode:** Repository-owned secret scanning governance + evidence of GitHub-hosted controls. **Non-authorizing.**  
**Does not:** rotate secrets, mutate GitHub security/org/billing toggles, rewrite history, enable live/testnet/orders, or claim unverified platform enforcement.

## Authority and ownership

| Role | Path |
|------|------|
| Canonical scanner / tracked-tree gate | [`scripts/ci/check_tracked_credential_hygiene_policy_v1.py`](../../../scripts/ci/check_tracked_credential_hygiene_policy_v1.py) |
| Canonical redaction owner (unchanged) | [`scripts/security/secret_hygiene_redaction_v1.py`](../../../scripts/security/secret_hygiene_redaction_v1.py) |
| Bounded allowlist | [`tracked_credential_like_allowlist_v1.json`](tracked_credential_like_allowlist_v1.json) |
| Complementary redaction / hygiene SSOT | [`SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1.md`](SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1.md) |
| Regression contracts | [`tests/ci/test_secret_scanning_push_protection_governance_v1.py`](../../../tests/ci/test_secret_scanning_push_protection_governance_v1.py) |
| CI enforcement surface | [`.github/workflows/lint_gate.yml`](../../../.github/workflows/lint_gate.yml) step *Tracked secret-like policy gate* (inside required context `Lint Gate`) |

**Reuse-before-new:** This capability extends the existing tracked credential hygiene gate. It does **not** introduce a second scanner or redaction authority.

## Scanner scope (tracked tree)

Deterministic offline scan of tracked textual files for:

- PEM / OpenSSH private-key headers
- High-confidence provider/API token formats (`AKIA…`, `sk-…`, JWT-like triples)
- Credential-bearing URLs (userinfo)
- Suspicious `Authorization` / `Proxy-Authorization` Bearer/Basic assignments
- Bounded high-entropy credential assignments (quoted sensitive-key assignments only)

Documented skip prefixes are always reported (`DOCUMENTED_SKIP_PREFIXES`); exclusions are never silent. Findings report **path + rule id + line** only — never raw secret values. Display-safe diagnostics route through the canonical redaction owner.

Exit non-zero on any non-allowlisted finding. No network dependency.

## Tracked-tree versus history scope

| Mode | Status | Notes |
|------|--------|-------|
| Tracked working tree | **ENFORCED** (local + CI via Lint Gate) | Default `python3 scripts/ci/check_tracked_credential_hygiene_policy_v1.py` |
| Full Git history | **MANUAL_BOUNDED** | `--manual-history` audits recent commit subjects/paths only (bounded window). **Not** complete repository-history protection; **not** CI-enforced |

Do not label tracked-tree scanning as complete history protection.

## CI enforcement

- Workflow: `lint_gate.yml` (required context name: `Lint Gate`)
- Top-level permissions unchanged (read-only; no write expansion)
- No `pull_request_target`
- Third-party Actions remain full 40-hex SHA pinned (no new unpinned Actions)
- Local equivalent: `python3 scripts/ci/check_tracked_credential_hygiene_policy_v1.py`

## GitHub-hosted feature state (API-evidenced snapshot)

Snapshot taken read-only via GitHub API against `rauterfrank-ui&#47;Peak_Trade` during this capability (base `origin/main`):

| Control | Classification | Evidence |
|---------|----------------|----------|
| Secret scanning | **ENFORCED** | `security_and_analysis.secret_scanning.status=enabled` |
| Push protection | **ENFORCED** | `security_and_analysis.secret_scanning_push_protection.status=enabled` |
| Branch protection (`main`) | **ENFORCED** | Required status checks + `enforce_admins=true` (API) |
| Repository ruleset `peak_trade` | **AVAILABLE_NOT_ENFORCED** | Ruleset exists with `enforcement=disabled` |
| New dedicated secret-scan check context | **NOT_APPLICABLE** | Enforced inside existing required `Lint Gate` (no BP mutation) |

Repository code does **not** mutate GitHub security settings. Classifications above are evidence snapshots, not authorization to change billing/org policy.

## Allowlist governance

- Versioned schema: `tracked_credential_like_allowlist_v1`
- Schema-validated on every gate load (fail closed)
- Exact path + exact `pattern_class` only — no directory wildcards; no global rule disable
- Required: `bounded=true`, `owner`, `reason`, and `expires_on` and/or `review_by`
- Reasons must state synthetic / placeholder / fixture / documentation / pattern definition
- Never store real secret values in the allowlist

## Redacted evidence rules

- Scanner output must never include matched secret material
- Exception / diagnostic strings pass through `secret_hygiene_redaction_v1.redact_for_diagnostics`
- JSON summaries set `secret_value_exposed=false` and omit matched values
- CI logs, annotations, artifacts, and job summaries must not receive raw secrets from this gate

## Incident response (real secret detected)

1. Do **not** paste the secret into tickets, chat, or PR comments.
2. Rotate / revoke the credential at the provider immediately (operator action).
3. Remove or rewrite the tracked exposure; add allowlist entries **only** for synthetic fixtures, never for real secrets.
4. If history exposure is suspected, run the manual bounded history command and escalate to a dedicated history-purge / rotation playbook (outside this capability).
5. Record incident via [`docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`](../../../docs/RUNBOOKS_AND_INCIDENT_HANDLING.md).

## Limitations and operator-only follow-ups

- Optional third-party tools (`gitleaks` / `detect-secrets`) remain **not** configured in pre-commit; complementary only.
- Full blob-level Git history scanning is not CI-enforced (`HISTORY_SCAN_STATUS=MANUAL_BOUNDED`).
- Ruleset `peak_trade` remains disabled until an explicit operator enables enforcement (no mutation in this PR).
- Non-provider GitHub secret-scanning patterns / validity checks were observed disabled in the API snapshot — operator may enable later without this PR claiming them.

## Exact local reproduction commands

```bash
# Enforced tracked-tree scan (CI equivalent)
python3 scripts/ci/check_tracked_credential_hygiene_policy_v1.py
python3 scripts/ci/check_tracked_credential_hygiene_policy_v1.py --json

# Manual bounded history audit (not CI-enforced; not full-history protection)
python3 scripts/ci/check_tracked_credential_hygiene_policy_v1.py --manual-history --history-max-commits 100

# Regression contracts
python3 -m pytest -q \
  tests/ci/test_secret_scanning_push_protection_governance_v1.py \
  tests/ci/test_credential_hygiene_redaction_unification_v1.py
```

## Explicit non-claims

This capability does not claim secret rotation, provider revocation, Git history purge, Runtime/Live authorization, or GitHub setting mutation.
