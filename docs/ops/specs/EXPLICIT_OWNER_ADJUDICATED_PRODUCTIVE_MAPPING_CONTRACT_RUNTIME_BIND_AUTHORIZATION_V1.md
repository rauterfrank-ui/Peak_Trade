# Explicit Owner-Adjudicated Productive Mapping-Contract Runtime-Bind Authorization v1

status: ACTIVE
last_updated: 2026-09-05
owner: Peak_Trade
purpose: Fail-closed admission class for an Owner-adjudicated productive binding of an already-adjudicated directional mapping contract into named Master V2 runtime owners. Not wiring, restoration, decommission, or nonproductive contract change. Not live authority.
docs_token: DOCS_TOKEN_EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZATION_V1

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
STANDING_AUTHORIZATION_ALLOWED=false
UNKNOWN_FIELD_FAIL_CLOSED=true
```

## 1) Role

This specification is the class attestation for

`EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_V1`

with

`mutation_purpose_class=PRODUCTIVE_CANONICAL_MAPPING_CONTRACT_RUNTIME_BIND`.

It is distinct from:

- `TECHNICAL_CANONICAL_WIRING_ONLY`
- `HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`
- `SEMANTICS_NEUTRAL_DECOMMISSION_ONLY`
- `EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE`

Those classes remain unchanged. This class is not overloaded onto them.
It does not waive `MASTER_V2_MUTATION_ALLOWED=false` or
`CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false`.

Committed machine state:

[`config/governance/explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1.json`](../../../config/governance/explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1.json)

Default grant is inactive (`grant_active=false`, empty `allowed_paths`).
An active slice grant is a later Owner step and must be digest-bound.

## 2) Intended use

Admit remaining Economic Guard forbidden matches only when every condition holds:

1. explicit Owner adjudication grant is active
2. exact `allowed_paths` cover every forbidden matched path in the current diff
3. `required_runtime_paths` is a non-empty exact-file subset of `allowed_paths`
4. every required runtime path is present in the current diff
5. `mapping_contract_spec` exists and is the directional mapping contract
6. `authorized_evidence_digest` matches `decommission_evidence_digest_v1`
7. `bound_diff_base_sha` matches the current diff base
8. no `excluded_paths` entry is present in the diff
9. no changed path starts with a `forbidden_diff_prefixes` directory
10. unknown JSON fields are absent
11. capability and live/testnet/canary/order invariants remain false

Owner adjudication is necessary and not sufficient.

## 3) Threat model

| Threat | Control |
|---|---|
| Inject extra Master V2 files under this purpose | extra forbidden path not in `allowed_paths` fails |
| Swap evidence / extra hunk | digest mismatch |
| Wrong base | `bound_diff_base_sha` mismatch |
| Claim tests-only while runtime changed | `required_runtime_paths` must be in the diff |
| False negative claims | `excluded_paths` and `forbidden_diff_prefixes` are machine-checked |
| Reuse grant on a different hunk | digest binds exact canonical hunks |
| Standing allowlist | inactive grant requires empty paths and empty digest |
| PR or branch exception | JSON hardcode detector; flags must be false |
| Restore or wiring purpose | purpose mismatch fails |
| Global mutation flags | unknown-field fail-closed plus explicit reject of those flags |

Residual risk: a human Owner may still list too many exact files. That is not a standing glob grant.

## 4) Evidence and digest

Reuse SHA-256 `decommission_evidence_digest_v1`. Do not invent a second hash system.

When `grant_active=true`, digest input is:

- sorted exact `allowed_paths`
- canonical hunk bodies (volatile git headers dropped)
- 40-hex `diff_base_sha`

```text
SAME_PATH_DIFFERENT_DIFF_REUSE=false
ADDITIONAL_HUNK_REUSE=false
STANDING_PATH_REUSE=false
```

Proof that a mapping runtime bind is offline-fixture-proven is
`DECLARED_OWNER_POLICY` /
`CONTRACT_RUNTIME_BINDING_PROVEN_SCOPE=OFFLINE_FIXTURE_PROOF_ONLY_NOT_LIVE`.
This class does not machine-validate pytest logs.

## 5) Precedence

1. Technical Canonical Wiring
2. Semantics-Neutral Decommission
3. Historically Attested Restoration
4. This class (remaining forbidden matches only)
5. Explicit Owner-Adjudicated Nonproductive Contract Change (unclassified only)

This class must not consume unclassified nonproductive paths.

## 6) Closeout

After a digest-bound slice is merged, a follow-up must set
`grant_active=false` and empty `allowed_paths`, `required_runtime_paths`,
digest, and `bound_diff_base_sha`. The class remains; the grant does not.

## 7) Fail-closed rules

See `fail_closed_validation_rules` in the machine-readable owner.
Unknown JSON keys fail closed. Glob characters in path fields fail closed.
Directory / prefix grants fail closed. Required-check waivers fail closed.
