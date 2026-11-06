# MASTER_V2 Canonical Volatility Numeric Max-Age Additional Evidence Repository SHA Semantics Resolution v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_REPOSITORY_SHA_SEMANTICS_RESOLUTION_V1
STATUS: CAPABILITY_AVAILABLE
scope: resolve additional-evidence preregistration repository SHA semantics to immutable ancestor baseline + critical-surface digest; no authorization issuance; no session execution
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NETWORK_AUTHORIZED: false
EXECUTION_AUTHORIZED: false
AUTHORIZATION_ISSUANCE_AUTHORIZED: false
HARD_STOP: true
---

> **Contract capability only (v2 SHA semantics).**
> Introduces
> `canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract&#47;v2`
> with explicit separation of `code_baseline_sha`, `artifact_creation_sha`, and
> dynamic `execution_repository_sha`. Does **not** issue or consume
> authorization, open network, execute a session, or mutate Master-V2 /
> Double-Play / Risk / Safety semantics.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_REPOSITORY_SHA_SEMANTICS_RESOLUTION_V1
CONTRACT_VERSION=canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract/v2
CODE_BASELINE_BINDING_MODE=IMMUTABLE_ANCESTOR_SHA
ARTIFACT_CREATION_SHA_ROLE=PROVENANCE_ONLY
EXECUTION_SHA_ROLE=DYNAMIC_READINESS_INPUT
TIP_OF_MAIN_EQUALITY_REQUIRED=false
SELF_COMMIT_SHA_EMBEDDING_REQUIRED=false
V1_NEW_AUTHORIZATION_READINESS_ALLOWED=false
PR_5629_SUPERSEDED=true
HARD_STOP=true
```

## Why tip-of-main self-binding is unlawful

v1 bound `repository_sha` to a concrete tip SHA and treated
`contract.repository_sha == origin&#47;main tip` as authorization readiness.
Because the contract/preregistration artifacts themselves live in the
repository, every merge that advances `origin/main` made the embedded tip
stale. Rebasing the artifact onto the new tip recreated the same problem
(non-terminating rebase/merge loop). PR #5629 embodied that obsolete
rebase approach and is **superseded** by this capability; it must not be
merged.

## Identity separation

| Identity | Role |
|---|---|
| `code_baseline_sha` | Immutable full Git SHA of the reviewed code baseline; may be an ancestor of later execution SHAs; bound in contract + preregistration |
| `artifact_creation_sha` | Provenance-only SHA of the worktree that created the artifact; not tip readiness authority |
| `execution_repository_sha` | Dynamic readiness input at authorization/execution time; must contain baseline; never self-embedded as predicted merge SHA |

## Readiness rules (strictly distinct)

1. `CODE_BASELINE_IS_ANCESTOR_OF_EXECUTION_SHA` — `git merge-base --is-ancestor`
2. `CRITICAL_SURFACE_DIGEST_MATCH` — versioned path manifest + content digest at execution SHA
3. `HEAD_EQUALS_ORIGIN_MAIN` — optional operational checkout gate only; **never** artifact authority

Ancestor-only is insufficient: critical-surface drift fail-closes even when
baseline remains an ancestor.

## Critical-surface manifest

Canonical artifact:
`config/research/canonical_volatility_numeric_max_age_additional_evidence_critical_surface_manifest_v2.json`

Covers contract schema/validator/constants/builder/readiness surfaces and the
manifest itself. Contract/preregistration JSON artifacts embed the digest and
are intentionally excluded from the digested path set (acyclic).

## Migration v1 → v2

| Concern | v1 | v2 |
|---|---|---|
| Contract version | `...contract&#47;v1` | `...contract&#47;v2` |
| Tip binding field | `repository_sha` | removed; use `code_baseline_sha` |
| Tip equality readiness | required in practice | forbidden (`TIP_OF_MAIN_EQUALITY_REQUIRED=false`) |
| New authorization readiness | blocked by tip drift | v2 only; v1 fail-closed unsupported |
| Existing s01/s02 evidence | unchanged | unchanged |
| Quarantine artifacts | unchanged | unchanged |

v1 remains parseable for historical evidence. New authorization-/session
creation must use v2.

## Builder semantics

- Accept explicit `code_baseline_sha` or default reviewed baseline.
- Read `artifact_creation_sha` from local `git rev-parse HEAD` (provenance).
- Compute critical-surface digest deterministically from worktree.
- Emit exactly one active v2 preregistration.
- Never emit a new v1 preregistration.
- Never overwrite s01/s02 or quarantine evidence.
- Byte-stable canonical JSON output.

## Operator workflow

```
CONTRACT_V2_CAPABILITY_MERGE
  → CREATE_ADDITIONAL_SESSION_PREREGISTRATION_V2
  → ISSUE_SESSION_SPECIFIC_AUTHORIZATION
  → EXECUTE_EXACTLY_ONE_SESSION
  → VERIFY_TERMINAL_EVIDENCE
  → REPEAT_FOR_SECOND_SESSION
  → DERIVE_NUMERIC_MAX_AGE_EVIDENCE
  → POLICY_DECISION_SEPARATE
```

## PR #5629

PR #5629 (`feat(research): rebase additional evidence preregistration contract SHA`)
is superseded by this capability. Do not merge. Close as superseded when
owner/operator cleanup authorization permits.
