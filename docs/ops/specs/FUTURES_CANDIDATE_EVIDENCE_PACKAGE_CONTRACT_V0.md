# Futures Candidate Evidence Package Contract v0

## Purpose

This contract defines the minimum candidate-specific evidence package required before Peak_Trade can treat a futures or perpetual candidate as ready for any governed futures readiness decision.

It supports the F7 Candidate Evidence Package stage in the Futures Capability Spec v0.

The contract exists to prevent repo docs, labels, dashboards, backtests, or testnet claims from being treated as candidate-specific futures readiness evidence without operator-held artifacts, provenance, checksums, and signoff.

## Non-authority note

This is a docs-only evidence package contract.

It does not implement evidence capture, archive writing, checksum generation, registry writing, dashboard behavior, exchange adapters, testnet paths, or Live paths.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

## Scope

This contract applies to futures/perpetual candidate evidence packages.

It covers:

- candidate identity,
- repo/config/environment binding,
- F1-F6 evidence bindings,
- risk/safety/no-live evidence,
- operator/reviewer signoff,
- archive/checksum/provenance fields,
- G4-G8 / L1-L5 boundaries,
- fail-closed semantics.

It does not create evidence. It defines what evidence must contain when a future governed capture is approved.

## Required prerequisites

A futures candidate evidence package requires completed or explicitly referenced:

1. F1 Instrument Metadata Contract.
2. F2 Market Data Provenance Contract.
3. F3 Backtest Realism Contract, if strategy behavior is evaluated.
4. F4 Risk Safety KillSwitch Contract.
5. F5 Read-only Market Dashboard Contract, if dashboard display is part of review.
6. F6 Testnet Dry-run Proof Contract, if testnet/dry-run proof is claimed.
7. Session env_name / exchange-surface non-authority boundary.
8. Futures Trading Readiness Runbook.

Missing prerequisite evidence makes the candidate package incomplete.

## Required candidate identity fields

| Field | Required | Description |
|---|---:|---|
| `candidate_id` | yes | Stable candidate id. |
| `candidate_family` | yes | Futures candidate family. |
| `candidate_scope` | yes | Scope of the candidate review. |
| `mode` | yes | Inventory, dashboard, backtest, dry-run, testnet, or other governed mode. |
| `operator_initials` | yes | Operator responsible for package preparation. |
| `reviewer` | yes | Reviewer or governance approver. |
| `created_utc` | yes | Package creation timestamp. |
| `updated_utc` | yes | Last update timestamp. |
| `go_no_go_state` | yes | `not_evaluated`, `go`, `no_go`, or governed equivalent. |
| `live_authorization` | yes | Must be `false` unless separately governed later. |

Rules:

- Candidate id must be concrete.
- Candidate id must not be silently reused for unrelated futures work.
- Candidate evidence is not portable across candidates without explicit governance review.

## Required repo / config / environment fields

| Field | Required | Description |
|---|---:|---|
| `git_head` | yes | Exact repo commit. |
| `branch_or_tag` | yes | Branch/tag used during capture. |
| `config_version` | yes | Version or path of relevant config. |
| `python_version` | conditional | Required if tools/tests are run. |
| `dependency_lock_ref` | conditional | Required if runtime execution is evaluated. |
| `environment_name` | yes | Environment label if used. |
| `mode` | yes | Mode that governs the path. |
| `adapter_ref` | conditional | Required if adapter support is claimed. |
| `session_id` | conditional | Required if any session is run. |
| `archive_root` | conditional | Required if artifacts are archived. |

Rules:

- `env_name` is not execution authority.
- Mode and environment label must remain separate.
- Repo docs alone do not satisfy evidence gates.

## Required F1-F6 evidence bindings

The package must bind each claimed stage:

| Stage | Required binding |
|---|---|
| F1 Instrument Metadata | Metadata record, provenance reference, completeness status. |
| F2 Market Data Provenance | Dataset id, source, freshness, cache/write state, provenance reference. |
| F3 Backtest Realism | Realism status, assumptions, missing fields, metrics, stress coverage. |
| F4 Risk / Safety / KillSwitch | Risk-cap values, SafetyGuard result, KillSwitch result, fail-closed status. |
| F5 Dashboard | Read-only display status and no-control/no-live boundary if reviewed. |
| F6 Testnet / Dry-run | Adapter binding, sandbox proof, order-payload proof, no-production-fallback proof if claimed. |

Rules:

- Stages not evaluated must be marked `not_evaluated`.
- Stages with missing inputs must be marked incomplete.
- A later-stage claim cannot override missing earlier-stage evidence.

## Required risk / safety / no-live evidence

The evidence package must include:

- no-live statement,
- no-order statement unless a governed testnet proof explicitly permits non-Live order payload validation,
- risk-cap summary,
- SafetyGuard status,
- KillSwitch status,
- LiveRiskLimits status if relevant,
- no-production-endpoint statement when testnet/dry-run is claimed,
- fail-closed result for missing futures inputs,
- unresolved safety gaps.

Rules:

- Risk diagnostics are not enforcement.
- Dashboard display is not enforcement.
- RiskGate pass is not Live authorization.
- KillSwitch status must be visible for any execution-like claim.

## Required operator / reviewer signoff

The package must include:

| Field | Required | Description |
|---|---:|---|
| `operator_signoff` | yes | Operator prepared/reviewed the package. |
| `operator_signoff_utc` | yes | Timestamp. |
| `reviewer_signoff` | yes | Reviewer/governance acknowledgement. |
| `reviewer_signoff_utc` | yes | Timestamp. |
| `signoff_scope` | yes | Exact scope of signoff. |
| `signoff_exclusions` | yes | Explicit exclusions. |

Rules:

- Self-review must be labeled as self-review.
- Signoff cannot silently authorize Live.
- Signoff cannot cover artifacts that are missing or not evaluated.

## Required archive / checksum / provenance fields

If artifacts are captured, the package must include:

- archive root,
- read-only archive URI,
- artifact list,
- artifact kind,
- checksums,
- checksum manifest,
- provenance manifest,
- immutable/archive status,
- upload/write status,
- external pointer metadata where applicable.

Rules:

- If no artifacts are captured, mark archive/checksum fields `not_applicable_no_artifacts_captured`.
- If artifacts exist without checksums, the evidence package is incomplete.
- If archive immutability is not verified, mark it `not_verified`.
- Local planning files are not evidence unless explicitly captured and classified.

## Required evidence package manifest

A package manifest must include:

- candidate id,
- git head,
- config version,
- stage status summary,
- artifact list,
- checksum summary,
- provenance summary,
- operator/reviewer signoff summary,
- missing/incomplete fields,
- no-live statement,
- next required governance action.

Recommended package statuses:

- `planning_only`,
- `evidence_incomplete`,
- `evidence_captured_unreviewed`,
- `reviewed_no_go`,
- `reviewed_go_for_next_stage`,
- `rejected`,
- `superseded`.

## G4-G8 / L1-L5 boundary

Repo docs and contracts do not satisfy G4-G8.

G4-G8 require candidate-specific evidence, review, and signoff.

L1-L5 pointer/evidence classes must remain explicit:

- L1 metadata / pointer preparation,
- L2 change-control / review metadata,
- L3 archive/read-only verification,
- L4 deeper replay/proof artifacts where required,
- L5 final signoff / governance package where required.

Do not mark any gate passed from this contract alone.

## Dashboard / testnet / live boundary

Dashboard review may only show read-only state.

Testnet proof requires F6 evidence and operator approval.

Live is out of scope.

No evidence package may imply Live authorization unless a separate future Master V2 / PRE_LIVE / First-Live governance path explicitly grants it.

## Fail-closed semantics

A futures candidate evidence package is incomplete when:

- candidate id is missing,
- git head is missing,
- config version is missing,
- F1 metadata is missing,
- F2 provenance is missing,
- F3 realism is claimed but evidence is missing,
- F4 risk/safety is missing,
- F6 testnet proof is claimed but adapter/sandbox/order/risk proof is missing,
- operator signoff is missing,
- reviewer signoff is missing,
- artifacts exist without checksums,
- archive status is unknown,
- no-live boundary is missing.

Incomplete means no promotion to the next governed stage.

## Validation / future tests

Future tests should prove:

1. Candidate packages require candidate id and git head.
2. Claimed F1-F6 stages require evidence references.
3. Missing signoff marks package incomplete.
4. Missing checksum for captured artifacts marks package incomplete.
5. Dashboard display cannot create evidence claims.
6. Testnet label cannot create F6 proof.
7. Live authorization remains false unless separately governed.
8. Planning-only packages cannot satisfy G4-G8.

## References

- [Futures Capability Spec v0](FUTURES_CAPABILITY_SPEC_V0.md)
- [Futures Instrument Metadata Contract v0](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md)
- [Futures Market Data Provenance Contract v0](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md)
- [Futures Backtest Realism Contract v0](FUTURES_BACKTEST_REALISM_CONTRACT_V0.md)
- [Futures Risk Safety KillSwitch Contract v0](FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md)
- [Futures Read-only Market Dashboard Contract v0](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md)
- [Futures Testnet Dry-run Proof Contract v0](FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md)
- [Session env_name and exchange surfaces non-authority v0](SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md)
- [Futures Trading Readiness Runbook v0](../runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
