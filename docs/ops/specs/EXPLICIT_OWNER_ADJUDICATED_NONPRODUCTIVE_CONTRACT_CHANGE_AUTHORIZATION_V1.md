# Explicit Owner-Adjudicated Nonproductive Contract-Change Authorization v1

status: ACTIVE
last_updated: 2026-09-01
owner: Peak_Trade
purpose: Fail-closed admission class for explicit Owner-adjudicated nonproductive contract changes on unclassified Economic Guard boundary paths. Not a trading, risk, execution, restoration, decommission, or technical-wiring authority.
docs_token: DOCS_TOKEN_EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_V1

```text
PARALLEL_SSOT_CREATED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
TOKEN_ALONE_IS_INSUFFICIENT=true
OWNER_APPROVED_ALONE_IS_INSUFFICIENT=true
PR_SPECIFIC_EXCEPTION=false
BRANCH_SPECIFIC_EXCEPTION=false
BROAD_MASTER_V2_GRANT=false
BLANKET_ALLOWLIST=false
DIRECTORY_GRANT=false
```

## 1) Role

This specification is the class attestation for

`EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE`

with

`mutation_purpose_class=OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE`.

It is distinct from:

- `TECHNICAL_CANONICAL_WIRING_ONLY`
- `HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`
- `SEMANTICS_NEUTRAL_DECOMMISSION_ONLY`

Those classes remain unchanged. This class is not overloaded onto them.
It is not a research path-prefix allowlist, not a fixture allowlist, and
not a trading-logic, risk, or execution grant.

Committed machine state:

[`config/governance/explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json`](../../../config/governance/explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json)

## 2) Intended use

Admit an unclassified boundary-governed file only when every condition holds:

1. explicit owner adjudication grant is active
2. exact allowed file set
3. allowed surface class exact
4. authorized evidence digest present
5. exact diff-base SHA bound
6. current canonical evidence digest matches
7. no additional protected path
8. no additional hunk
9. no productive runtime reachability increase
10. no trading semantic change
11. no economic semantic change
12. no selection semantic change
13. no risk semantic change
14. no planning semantic change
15. no execution semantic change
16. fail-closed semantics not weakened

Owner adjudication is necessary and not sufficient. `OWNER_APPROVED=true`
alone must not produce PASS.

## 3) Forbidden use

- PR-number or branch-name exceptions
- directory / path-prefix / blanket grants, including `src&#47;research&#47;**` and
  `tests&#47;research&#47;**`
- admitting because a path is a fixture, test, json, or collector
- required-check or branch-protection waivers
- live / testnet / canary / order enablement
- trading, selection, risk, planning, or execution semantic change
- fail-closed weakening
- productive reachability increase
- using this class for semantics-neutral decommission, restoration, or
  technical wiring

If any of the following is true, the class must BLOCK:

```text
PRODUCTIVE_RUNTIME_REACHABILITY_INCREASED
TRADING_SEMANTICS_CHANGED
ECONOMIC_SEMANTICS_CHANGED
SELECTION_SEMANTICS_CHANGED
RISK_SEMANTICS_CHANGED
PLANNING_SEMANTICS_CHANGED
EXECUTION_SEMANTICS_CHANGED
FAIL_CLOSED_SEMANTICS_WEAKENED
```

## 4) Evidence

Reuse the SHA-256 digest infrastructure from semantics-neutral decommission
authorization (`decommission_evidence_digest_v1`). Do not create a second
hash system.

When `grant_active=true`, every admitted path must:

1. be an exact file in `allowed_paths`
2. have a unified diff
3. match `bound_diff_base_sha` against the current diff base
4. match `authorized_evidence_digest` (SHA-256 over `decommission_evidence_digest_v1`:
   sorted exact files, canonical hunk bodies, and the 40-hex `diff_base_sha`)
5. keep every safety predicate machine-false on the current hunk bodies

The digest drops volatile git headers (`diff `, `index `, `--- `, `+++ `,
`new file`, `deleted file`) and normalizes CRLF to LF. Path order does not
change the digest.

Therefore:

```text
SAME_PATH_DIFFERENT_DIFF_REUSE=false
ADDITIONAL_HUNK_REUSE=false
REMOVED_HUNK_REUSE=false
ADDITIONAL_PATH_REUSE=false
DIFFERENT_BASE_REUSE=false
OWNER_ADJUDICATION_FUTURE_REUSE_POSSIBLE=false
```

Authorization is not based on PR number, branch name, directory prefix, or
a global allowlist.
