# Historically Attested Current-System Semantic Restoration Admission v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Governance admission class for restoration to proven Master V2 / Double Play semantics. Not a slice grant. Not live authority.
docs_token: DOCS_TOKEN_HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_ADMISSION_V1

```text
PARALLEL_SSOT_CREATED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
RESTORATION_ADMISSION_BINDS_TO_TARGET=true
RESTORATION_ADMISSION_BINDS_TO_CURRENT_A06_CODE=false
HISTORICAL_REFERENCE_AUTHORITY=NONE
CURRENT_SYSTEM_SEMANTIC_DELTA=true
RISK_SIZING_SEMANTICS_CHANGED_FALSE_REQUIRED=false
GRANT_ACTIVE=false
TOKEN_ALONE_IS_INSUFFICIENT=true
```

## 1) Role

This specification is the class attestation for

`HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`

with

`mutation_purpose_class=HISTORICALLY_ATTESTED_CANONICAL_SEMANTIC_RESTORATION`.

It is distinct from

`TECHNICAL_CANONICAL_WIRING_ONLY` /
`SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING`.

The existing technical wiring authorization remains unchanged and is not
overloaded.

This document does **not** authorize any concrete restoration slice.
`grant_active=false`. Exact-file grants require a later Owner authorization
after the candidate diff is re-adjudicated against the restoration target.

## 2) Restoration precedence

Normative order:

1. proven Master V2 / Double Play historical semantics and structure
2. adjudicated restoration obligations derived from that evidence
3. current canonical implementation adapted to satisfy those obligations
4. an existing candidate implementation only where it conforms to 1–3

`origin/main` is a technical baseline and delta source only.
A candidate PR implementation is not the normative semantic target.

```text
RESTORATION_TARGET_ID=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1
HISTORICAL_REFERENCE_SHA256=a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212
HISTORICAL_REFERENCE_ROLE=FORENSIC_REFERENCE_BINDING
HISTORICAL_REFERENCE_AUTHORITY=NONE
```

The forensic package is not promoted to canonical working authority.

## 3) Machine-validated versus declared claims

Machine-validated (repo-state):

- exact-file allowlist / no directory or glob grant
- restoration target id equals the conserved Master V2 / Double Play model
- class attestation file exists
- historical SHA-256 and `AUTHORITY=NONE` binding
- `CURRENT_SYSTEM_SEMANTIC_DELTA=true`
- execution / live / safety / trading authority flags remain false
- no required-check waiver / branch-protection bypass
- purpose class is not semantics-neutral technical wiring
- `binds_to_current_a06_code=false`

Declared Owner policy / human-adjudicated (not proven by JSON booleans):

- `NEW_POLICY_INTRODUCED=false`
- `UNATTESTED_FORMULA_CHANGE=false`
- `CANONICAL_COMPUTE_OWNER_CHANGED=false`
- `RESTORATION_TARGET_CONFORMANCE` of any future granted slice

This class must **not** claim `RISK_SIZING_SEMANTICS_CHANGED=false`.

## 4) Constructs that must not acquire de-facto authority from a candidate implementation

The following candidate-implementation constructs remain historically
unproven or require exact provenance review. They are **not** admitted by
this class and must not be copied into this contract as required semantics.

| Construct | HISTORICAL_SUPPORT | RESTORATION_TARGET_CONFORMANCE | CURRENT_A06_IMPLEMENTATION_STATUS |
|---|---|---|---|
| Additional candidate fail-closed gates beyond attested stage fail-closed | UNPROVEN | UNPROVEN | PRESENT |
| Packet-as-compute-owner constraints | UNPROVEN | UNPROVEN | PRESENT |
| SideState override constraints | UNPROVEN | UNPROVEN | PRESENT |
| Provenance restrictions beyond historically proven behavior | UNPROVEN | UNPROVEN | PRESENT |
| Stage-contract mechanics not directly evidenced by Master V2 / Double Play | UNPROVEN | UNPROVEN | PRESENT |
| Candidate-specific identifiers or orchestration conventions | UNPROVEN | UNPROVEN | PRESENT |
| Distinct Capital / Risk / Sizing / Intent stages | PROVEN | UNPROVEN | PRESENT |
| Existing STEP 29P / 29Q compute owners as current-system adapters | PROVEN | UNPROVEN | PRESENT |

`UNPROVEN` historical support must not be silently promoted into this
admission contract. If later comparison proves a candidate construct
incompatible with the restoration target:

```text
A06_IMPLEMENTATION_DIVERGENCE_FROM_RESTORATION_TARGET=true
A06_GRANT_MUST_NOT_BE_ISSUED=true
```

until a separately authorized correction restores conformance.
That remediation is out of scope for this governance-prerequisite slice.

## 5) Empty grant

Committed authorization state:

```text
grant_active=false
allowed_paths=[]
slice_grant_id=
RESTORATION_TARGET_CONFORMANCE=false
```

Protected surfaces without an exact-file grant remain fail-closed,
including candidate Capital / Risk / Sizing / Intent restore paths.

## 6) Owners

- Machine authorization: [`config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json`](../../../config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json)
- Boundary contract: [`config/governance/economic_diagnostic_optimization_boundary_v0.json`](../../../config/governance/economic_diagnostic_optimization_boundary_v0.json)
- Guard: [`src/governance/economic_diagnostic_optimization_boundary_v0.py`](../../../src/governance/economic_diagnostic_optimization_boundary_v0.py)
- Parent: [`docs/governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](../../governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md)
- Wiring class (unchanged): [`config/governance/technical_canonical_wiring_authorization_v1.json`](../../../config/governance/technical_canonical_wiring_authorization_v1.json)
