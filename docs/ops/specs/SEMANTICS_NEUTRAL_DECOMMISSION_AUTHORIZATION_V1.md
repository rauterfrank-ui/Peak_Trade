# Semantics-Neutral Decommission Authorization v1

status: ACTIVE
last_updated: 2026-09-01
owner: Peak_Trade
purpose: Fail-closed admission class for obsolete-reference / deleted-component cleanup on Economic Guard protected surfaces. Not a trading authority. Not a PR bypass.
docs_token: DOCS_TOKEN_SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1

```text
PARALLEL_SSOT_CREATED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
GRANT_ACTIVE=false
TOKEN_ALONE_IS_INSUFFICIENT=true
PR_SPECIFIC_EXCEPTION=false
BRANCH_SPECIFIC_EXCEPTION=false
BROAD_MASTER_V2_GRANT=false
BLANKET_ALLOWLIST=false
```

## 1) Role

This specification is the class attestation for

`SEMANTICS_NEUTRAL_DECOMMISSION_ONLY`

with

`mutation_purpose_class=SEMANTICS_NEUTRAL_DECOMMISSION`.

It is distinct from:

- `TECHNICAL_CANONICAL_WIRING_ONLY` / `SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING`
- `HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`

Those classes remain unchanged. This class is not overloaded onto them.

Committed machine state:

[`config/governance/semantics_neutral_decommission_authorization_v1.json`](../../../config/governance/semantics_neutral_decommission_authorization_v1.json)

Default grant is inactive (`grant_active=false`, empty `allowed_paths`).
The class exists so a later decommission PR can activate exact-file scope
without inventing a bypass.

## 2) Intended use

Allow a protected-surface touch only when the current diff is proven to be
semantics-neutral decommission, for example:

- removing a reference to a deleted component whose target is absent
- neutralizing a negative-test / comment literal without weakening fail-closed
  assertions

## 3) Forbidden use

- PR-number or branch-name exceptions
- directory / blanket MASTER_V2 grants
- required-check or branch-protection waivers
- live / testnet / canary / order enablement
- trading, selection, risk, planning, or execution semantic change
- fail-closed weakening
- productive reachability increase
- self-attestation without machine-validated diff evidence

## 4) Evidence

When `grant_active=true`, every forbidden matched path must:

1. be an exact file in `allowed_paths`
2. have a unified diff
3. contain only decommission-shaped line changes
4. prove at least one predicate from `decommission_predicates.require_at_least_one`

Missing or incomplete evidence is `SEMANTICS_NEUTRAL_DECOMMISSION_EVIDENCE_INSUFFICIENT` (BLOCK).

Malformed contracts are `SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_INVALID` (BLOCK).

## 5) Fail-closed default

No protected touch + no grant → existing Economic Guard behavior.

Protected touch + inactive/missing decommission grant + no other valid
authorization → BLOCK.

Master V2 mutation remains disallowed as a global default.
This class does not create trading, selection, risk, execution, or venue authority.
