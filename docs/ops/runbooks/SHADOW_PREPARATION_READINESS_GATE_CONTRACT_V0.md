# Shadow Preparation Readiness Gate Contract v0

## Status

**Preparation and classification only.**

Producer family: `ops.shadow_preparation_readiness_gate_v0`

This contract inventories and classifies existing shadow-named repository
surfaces and emits a deterministic machine-readable Shadow-preparation readiness
result. It proves that **canonical STEP 29U Shadow Mode does not currently
exist** and that activation remains unauthorized.

```text
SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0=true
PREPARATION_ONLY=true
NOT_STEP_29U_IMPLEMENTATION=true
AUTHORITY_EFFECT=NONE
NON_ACTIVATING=true
```

## Non-activation guarantees (mandatory)

This contract:

- is **preparation only**;
- is **not** STEP 29U implementation;
- does **not** authorize Shadow;
- does **not** authorize Paper, Testnet, Scheduler, Runtime, Live, or Orders;
- does **not** start, schedule, simulate, or execute any Shadow/Paper/Testnet
  session, worker, runtime bridge, or order path;
- has **no** method that enables or starts a process.

All activation flags remain **false**:

```text
SHADOW_ACTIVATION_AUTHORIZED=false
PAPER_ACTIVATION_AUTHORIZED=false
TESTNET_ACTIVATION_AUTHORIZED=false
SCHEDULER_ACTIVATION_AUTHORIZED=false
RUNTIME_ACTIVATION_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_AUTHORIZED=false
```

A **separate operator GO** is required for any activation-stage work.

## Authority boundaries (unchanged)

- **Master V2** and **Double Play** remain the sole decision/composition
  authorities.
- **Safety** remains an independent veto authority.
- **Runtime Bridge** remains `BOUND_NOT_ACTIVATED`.
- Economic sequencing remains binding:
  `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false` (FAIL/BLOCKED).
- This producer has `authority_effect=NONE` and cannot modify another owner.

## Historical surface non-equivalence

Historical shadow-named surfaces are **not** canonical by name. Existing
Phase-24 (`ShadowOrderExecutor`, `scripts/run_shadow_execution.py`), Phase-31
(`ShadowPaperSession`), Shadow-247 wrappers/preflight, `shadow_no_order_proof`,
`src/data/shadow/__init__.py`, paper/shadow WebUI readmodels, and related
surfaces are classified as non-equivalent to STEP 29U unless an existing
ratified canonical binding explicitly proves otherwise.

Classifications used by this contract include:

- `NON_CANONICAL_STEP29U`
- `HISTORICAL`
- `PREPARATION_ONLY`
- `EVIDENCE_ONLY`
- `OFFLINE_REPLAY`
- `EXECUTOR_WITHOUT_CANONICAL_BINDING`
- `UNKNOWN_FAIL_CLOSED` (fail-closed — evaluation rejects ambiguous surfaces)

## Dashboard blocker (still OPEN)

```text
DASHBOARD_BLOCKER_ID=MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY
DASHBOARD_BLOCKER_STATE=OPEN
DASHBOARD_BLOCKER_RESOLVED=false
DASHBOARD_BLOCKER_WAIVED=false
DASHBOARD_BLOCKER_ACCEPTED_AS_DONE=false
```

Closing PR #5529 did **not** resolve, waive, or accept the dashboard defect.
`MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY` remains **OPEN** in every
produced readiness result. This contract must not resolve or waive that
blocker.

## Canonical STEP 29U / 29V status

```text
CANONICAL_SHADOW_MODE_EXISTS=true
CANONICAL_STEP_29U_BOUND=true
CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false
SHADOW_PREPARATION_COMPLETE=false
AUTHORITY_EFFECT=NONE
NOT_STEP_29U_IMPLEMENTATION=true
```

Canonical STEP 29U Shadow Mode and STEP 29V Paper Mode do not currently exist
in the repository as ratified **bindings**. The semantic definition of STEP 29U
is owned exclusively by the canonical runbook section
`## STEP 29U — Shadow` in
`docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`.

That runbook section may define STEP 29U as semantically ratified but
operationally unbound. This readiness contract does **not** duplicate that
normative body and does **not** become a second STEP 29U SSOT.

### Readiness producer role (narrow)

`ops.shadow_preparation_readiness_gate_v0`:

- classifies preparation truth;
- proves absence / non-readiness;
- cannot bind STEP 29U;
- cannot implement STEP 29U;
- cannot activate Shadow, Paper, Testnet, Scheduler, Runtime, Live, or Orders.

```text
READINESS_PRODUCER_CLASSIFIES_PREPARATION_TRUTH=true
READINESS_PRODUCER_PROVES_ABSENCE_OR_NON_READINESS=true
READINESS_PRODUCER_CANNOT_BIND_STEP_29U=true
READINESS_PRODUCER_CANNOT_IMPLEMENT_STEP_29U=true
READINESS_PRODUCER_CANNOT_ACTIVATE_STEP_29U=true
```

## Canonical offline Shadow preparation operator command

```text
CANONICAL_OFFLINE_SHADOW_PREPARATION_OPERATOR_COMMAND=
python scripts/ops/run_okx_futures_shadow_offline_e2e_projection_binding_v0.py --mode shadow
SOLE_CANONICAL_OFFLINE_SHADOW_PREPARATION_OPERATOR_COMMAND=true
```

The e2e binding CLI above is the **sole canonical operator command** for
executing the complete offline OKX Futures Shadow preparation chain:

readiness gate → durable projection writer → projection verifier →
OKX Futures no-order HOLD cycle → e2e binding result.

Activation readiness may remain `BLOCKED` even when Step 29U composition is bound; `CANONICAL_STEP_29U_ABSENT` is cleared on verified binding and must not be re-emitted while bound
(and related activation gaps). That activation classification remains truthful
and non-authorizing; it does **not** veto the offline no-order HOLD cycle when
the offline Shadow-preparation path remains permitted. The binding must not
require activation `READY` before invoking the offline cycle.

Related readiness-path component owners (offline projection pipeline,
readiness-only operator entrypoint, readiness bundle) remain valid for the
readiness projection subpath and do **not** introduce a second readiness,
decision, risk, safety, execution, reconciliation, writer, reader, or
projection truth. They are **not** the full-chain canonical operator command.

The sole canonical command is:

- OKX-only
- Futures-only
- BTC-excluding
- Spot-excluding
- offline
- deterministic
- non-activating
- non-networked
- non-ordering

Successful offline cycle semantics remain (composition binding expectations):

```text
decision=HOLD
risk_sizing=NONE
execution=NOT_APPLICABLE:NONE
reconciliation=BOUND_OFFLINE
order_submission_count=0
```

Offline preparation does **not** activate Shadow. Activated Shadow still
requires a separate operator GO and separate runtime/session/scheduler
contracts. `CANONICAL_STEP_29U_SHADOW_MODE` remains unbound/absent.
`CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false` — STEP 29V Paper remains
undefined/future-only; Paper simulation is not implemented. Testnet and Live
remain unauthorized and fail-closed.

### Post-merge offline no-order E2E soak (operational evidence)

```text
OFFLINE_OKX_FUTURES_SHADOW_NO_ORDER_E2E_STATUS=PROVEN_POST_MERGE_600S_SOAK
PR_NUMBER=5544
PR_MERGED=true
MERGE_COMMIT_SHA=bc7b9309b1f7e2e1411e22b483388331f355d0dd
POST_MERGE_ORIGIN_MAIN_SHA=bc7b9309b1f7e2e1411e22b483388331f355d0dd
SOAK_MONOTONIC_ELAPSED_SECONDS=600.370976375
INVOCATIONS_TOTAL=1287
INVOCATIONS_SUCCESSFUL=1287
INVOCATIONS_FAILED=0
COMPLETE_FOUR_STAGE_CYCLES=1287
HOLD_CYCLES=1287
BINDING_PASS_COUNT=1287
BINDING_BLOCKED_COUNT=0
CYCLE_NOT_INVOKED_COUNT=0
ORDERS_CREATED_ANY=false
ORDERS_SUBMITTED_ANY=false
NETWORK_ACCESS_ANY=false
RUNTIME_ACTIVATED_ANY=false
ACTIVATION_AUTHORITY_GRANTED_ANY=false
CANONICAL_STEP_29U_ABSENT=CLEARED_COMPOSITION_BOUND_ACTIVATION_STILL_UNAUTHORIZED
RUNTIME_BRIDGE=BOUND_NOT_ACTIVATED
ECONOMIC_VALIDITY=NOT_PROVEN_BLOCKED
DURABLE_EVIDENCE_PATH=evidence/ops/okx_futures_shadow_no_order/2026-07-25_postmerge_600s_soak
SOURCE_EVIDENCE_MANIFEST_SHA256=c1aa75a0794488f3fb9a9b76f9734779f0ab65d00b8be7c81f8fa7654de8747a
```

The canonical offline OKX Futures Shadow no-order path is proven by a
post-merge 600.37-second monotonic soak with 1287/1287 complete HOLD cycles
and no orders, network access or runtime activation.

The post-merge soak operational evidence alone does **not** resolve composition absence; canonical Step 29U shadow binding does. Soak evidence still does **not** authorize activation,
does **not** activate runtime, does **not** prove economic validity, and does
**not** authorize Testnet or Live. False readiness veto of the offline
no-order cycle (pre-#5544) is resolved by PR #5544; activation blockers remain
open and separate.

### Component commands (not full-chain canonical)

```text
READINESS_ONLY_COMPONENT_COMMAND=
python -m src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0
READINESS_ONLY_COMPONENT_OWNER=true
READINESS_ONLY_NOT_FULL_CHAIN_CANONICAL_OPERATOR_COMMAND=true
```

Classification: readiness-only component owner; **not** the full-chain
canonical operator command.

```text
NO_ORDER_ONLY_COMPONENT_COMMAND=
python scripts/ops/run_okx_futures_shadow_no_order_v0.py --mode shadow
NO_ORDER_ONLY_COMPONENT_OWNER=true
NO_ORDER_ONLY_NOT_FULL_CHAIN_CANONICAL_OPERATOR_COMMAND=true
```

Classification: no-order cycle component owner; **not** the full-chain
canonical operator command.

## Owners and artifacts

| Role | Path |
|------|------|
| Sole canonical offline Shadow preparation operator command | `scripts/ops/run_okx_futures_shadow_offline_e2e_projection_binding_v0.py` |
| E2E binding owner (composition-only) | `src/ops/okx_futures_shadow_offline_e2e_projection_binding_v0.py` |
| Producer | `src/ops/shadow_preparation_readiness_gate_v0.py` |
| Offline projection pipeline (component) | `src/ops/shadow_preparation_readiness_offline_projection_pipeline_v0.py` |
| Offline operator entrypoint (readiness-only component) | `src/ops/shadow_preparation_readiness_offline_operator_entrypoint_v0.py` |
| Readiness bundle (read-only aggregate component) | `src/ops/shadow_preparation_readiness_bundle_v0.py` |
| OKX Futures no-order cycle (component) | `scripts/ops/run_okx_futures_shadow_no_order_v0.py` |
| Config (static, non-activating) | `config/ops/shadow_preparation_readiness_gate_v0.toml` |
| Contract doc (this file) | `docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md` |
| Post-merge 600s offline no-order soak evidence (docs/evidence-only) | `evidence/ops/okx_futures_shadow_no_order/2026-07-25_postmerge_600s_soak/` |
| Related charter (non-activating) | `docs/ops/runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md` |
| Focused tests | `tests/ops/test_shadow_preparation_readiness_gate_v0.py` |
| Pipeline focused tests | `tests/ops/test_shadow_preparation_readiness_offline_projection_pipeline_v0.py` |
| Operator entrypoint focused tests | `tests/ops/test_shadow_preparation_readiness_offline_operator_entrypoint_v0.py` |
| Bundle focused tests | `tests/ops/test_shadow_preparation_readiness_bundle_v0.py` |
| Durable projection output (generated) | `out&#47;ops&#47;shadow_preparation_readiness_projection_v0.json` |

## Fail-closed conditions

Evaluation fails closed when:

- config is missing or invalid;
- a required canonical reference cannot be established;
- the configured `canonical_step_29u_semantics_reference` is missing, empty,
  absolute, outside `repo_root`, not a file, or otherwise invalid;
- any `historical_surfaces[].path` is missing, empty, absolute, outside
  `repo_root`, not a file (directories are rejected), or otherwise invalid;
- any configured Mindestkontrakt `evidence_paths` entry is missing, empty,
  absolute, outside `repo_root`, not a file, or otherwise invalid;
- contradictory activation state is supplied;
- any activation flag is true;
- dashboard blocker state is missing or claims resolved/waived/accepted;
- historical surfaces are ambiguously classified (`UNKNOWN_FAIL_CLOSED`);
- `authority_effect` is not `NONE`.

### Repository-relative path / reference validation

Evaluation requires an explicit or deterministically inferred `repo_root`.
Required repository-relative references are validated before a readiness result
is accepted. Invalid references raise
`ShadowPreparationReadinessGateError` (exception fail-closed) and do **not**
produce a normal BLOCKED readiness result.

Reason-code prefixes (context id appended after `:`):

- `HISTORICAL_SURFACE_PATH_MISSING|NOT_FILE|OUTSIDE_REPO|ABSOLUTE|EMPTY`
- `EVIDENCE_PATH_MISSING|NOT_FILE|OUTSIDE_REPO|ABSOLUTE|EMPTY`
- `CANONICAL_STEP_29U_SEMANTICS_REFERENCE_MISSING|NOT_FILE|OUTSIDE_REPO|ABSOLUTE|EMPTY|INVALID`

Existence of `canonical_step_29u_semantics_reference` proves only that the
canonical STEP 29U semantics/runbook file is present. It does **not** set
`STEP_29U_IMPLEMENTED`, `CANONICAL_STEP_29U_BOUND`, or
`SHADOW_PREPARATION_COMPLETE`, and grants no activation authority.


## STEP 29U Mindestkontrakt gap inventory (preparation only)

This producer emits a deterministic, machine-readable inventory of required
STEP 29U Mindestkontrakt components. Inventory status values are closed-enum:

- `PRESENT`
- `MISSING`
- `UNBOUND`
- `DOCS_ONLY`
- `LEGACY_NON_CANONICAL`

```text
MINDESTKONTRAKT_GAP_INVENTORY_V0=true
NOT_STEP_29U_IMPLEMENTATION=true
STEP_29U_IMPLEMENTED=true
SHADOW_ACTIVATABLE=false
SHADOW_MODE_ALLOWED=false
SEPARATE_GO_REQUIRED_FOR_IMPLEMENTATION=true
SEPARATE_GO_REQUIRED_FOR_ACTIVATION=true
CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false
```

The inventory proves preparation gaps only. It does **not** implement STEP 29U,
bind Master V2 / Double Play to a Shadow session, create a lifecycle, simulate
orders/fills, or authorize activation. Historical Shadow/Paper surfaces remain
non-canonical (`LEGACY_NON_CANONICAL` / historical surface classifications).

STEP 29V Paper Mode remains canonically undefined
(`CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false`). This contract does not define
STEP 29V semantics.

## Durable readiness projection (projection-only, non-authoritative)

```text
PROJECTION_SCHEMA_ID=shadow_preparation_readiness_projection
PROJECTION_SCHEMA_VERSION=v0
PROJECTION_ONLY=true
AUTHORITY_EFFECT=NONE
ACTIVATION_AUTHORITY=false
EXPLICIT_WRITE_CALL_REQUIRED=true
NOT_STEP_29U_IMPLEMENTATION=true
NOT_READINESS_APPROVAL=true
NOT_ACTIVATION_AUTHORITY=true
NOT_SCHEDULER_INPUT=true
NOT_RUNTIME_COMMAND=true
NOT_DASHBOARD_AUTHORITY=true
```

An optional durable projection writer may serialize **one already-computed**
readiness evaluation into immutable, versioned, deterministic UTF-8 JSON bytes
and atomically replace an explicitly configured repository-relative output path.

- Writing requires an **explicit** writer call
  (`write_shadow_preparation_readiness_projection_v0`).
- Evaluation alone remains side-effect free and writes **no** artifact.
- The writer does **not** recompute readiness, filesystem evidence, blockers, or
  STEP-29U semantics; it consumes the canonical evaluation payload
  (`evaluation.to_dict()`).
- Default configured path:
  `out&#47;ops&#47;shadow_preparation_readiness_projection_v0.json`
  (generated evidence/projection only; not an activation input; does not
  overwrite historical source evidence).

### Deterministic serialization contract

- UTF-8 JSON
- deterministic key ordering (`sort_keys=true`)
- deterministic separators (`","`, `":"`)
- trailing newline explicitly defined
- fixed `evaluated_at` yields byte-identical output
- no wall-clock timestamp inside the writer
- no random IDs
- no host-specific absolute paths in serialized content
- complete file replacement only (no append)

### Atomic-write contract

1. serialize complete deterministic bytes
2. write to a temporary sibling file in the same directory
3. flush + fsync (where supported)
4. atomically replace the destination
5. clean up temporary files on failure

No partial destination is left on write failure. A failed atomic replace must
preserve any previous complete destination.

### Path containment rules

The projection output path must be:

- explicit and repository-relative
- resolved inside `repo_root` (independent of current working directory)
- reject empty values, absolute paths, and traversal outside `repo_root`
- reject an existing directory target
- require the parent directory to already exist (fail closed; no silent nested
  directory creation)

Stable failure reason prefixes include:

- `PROJECTION_OUTPUT_PATH_EMPTY`
- `PROJECTION_OUTPUT_PATH_ABSOLUTE`
- `PROJECTION_OUTPUT_PATH_OUTSIDE_REPO`
- `PROJECTION_OUTPUT_PARENT_MISSING`
- `PROJECTION_OUTPUT_PATH_IS_DIRECTORY`
- `PROJECTION_SERIALIZATION_FAILED`
- `PROJECTION_TEMP_WRITE_FAILED`
- `PROJECTION_ATOMIC_REPLACE_FAILED`

Write failure must not be converted into a successful readiness result and must
not alter evaluation blocker order or readiness outcome.

The projection is **not**: STEP-29U implementation; readiness approval;
activation authority; scheduler input; runtime command; or dashboard authority.

### Durable projection reader / verifier (offline, non-activating)

```text
PROJECTION_VERIFICATION_SCHEMA_ID=shadow_preparation_readiness_projection_verification
PROJECTION_VERIFICATION_SCHEMA_VERSION=v0
PROJECTION_READER_VERIFIER_V0=true
PROJECTION_ONLY=true
AUTHORITY_EFFECT=NONE
ACTIVATION_AUTHORITY=false
ZERO_SIDE_EFFECTS=true
NOT_STEP_29U_IMPLEMENTATION=true
NOT_READINESS_APPROVAL=true
NOT_ACTIVATION_AUTHORITY=true
```

`verify_shadow_preparation_readiness_projection_v0` reads one durable projection
at an **explicit** repository-relative path or the configured default
`readiness_projection_output_path`. It never searches arbitrary directories and
never infers an alternate path.

Fail-closed verification outcomes (`overall_status=BLOCKED`, `verified=false`)
include:

- `MISSING_PROJECTION`
- `INVALID_PROJECTION`
- `SCHEMA_MISMATCH`
- missing mandatory fields / invalid enum values (`BLOCKED`)
- `CONTRADICTORY_PROJECTION` (READY-like claim while required readiness
  components remain non-ready)
- evidence reference invalid / missing / path escape
- `DIGEST_MISMATCH` when a digest is contractually present
- `FUTURE_DATED` beyond permitted clock skew
  (`PROJECTION_VERIFIER_CLOCK_SKEW_SECONDS`)
- `STALE` beyond freshness max age
  (`PROJECTION_VERIFIER_FRESHNESS_MAX_AGE_SECONDS`)

A verified result may be returned for a valid current projection, but
verification triggers **no** action, write, activation, scheduler, runtime, or
order side effect.

### Offline projection pipeline (orchestration only)

```text
OFFLINE_PROJECTION_PIPELINE_V0=true
PROJECTION_ONLY=true
AUTHORITY_EFFECT=NONE
ACTIVATION_AUTHORITY=false
ZERO_SIDE_EFFECTS=true
```

`run_shadow_preparation_readiness_offline_projection_pipeline_v0` (producer
`ops.shadow_preparation_readiness_offline_projection_pipeline_v0`) composes the
canonical gate evaluation (exactly once), durable writer, and reader/verifier.
It proves exact semantic consistency between the evaluated result and the
reread projection, then returns `PIPELINE_PASS`, `PIPELINE_BLOCKED`, or
`PIPELINE_ERROR`. A blocked readiness evaluation that is successfully projected
and verified is `PIPELINE_BLOCKED` (not an execution failure). The pipeline does
not activate Shadow/Paper/Testnet/Runtime/Scheduler/Orders/Live and does not
introduce a second readiness truth owner.

### Offline operator entrypoint (readiness-only component CLI)

```text
OFFLINE_OPERATOR_ENTRYPOINT_V0=true
READINESS_ONLY_COMPONENT_OWNER=true
READINESS_ONLY_NOT_FULL_CHAIN_CANONICAL_OPERATOR_COMMAND=true
PROJECTION_ONLY=true
AUTHORITY_EFFECT=NONE
ACTIVATION_AUTHORITY=false
NOT_SCHEDULER_ENTRYPOINT=true
NOT_RUNTIME_ENTRYPOINT=true
ZERO_RUNTIME_ACTIVATION=true
```

Component invocation (readiness-only; **not** the full-chain canonical operator
command; repo-native `python -m`, argparse):

```text
python -m src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0 \
  --repo-root . \
  --output-path out&#47;ops&#47;shadow_preparation_readiness_projection_v0.json \
  --format text
```

JSON form:

```text
python -m src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0 \
  --repo-root . \
  --output-path out&#47;ops&#47;shadow_preparation_readiness_projection_v0.json \
  --format json
```

Exit-code contract (stable):

| Exit code | Meaning |
|-----------|---------|
| `0` | `PIPELINE_PASS` |
| `2` | `PIPELINE_BLOCKED` (authorizes nothing) |
| `1` | `PIPELINE_ERROR` or invalid CLI arguments |

`--format text` prints a deterministic `status=PIPELINE_*` summary. `--format json`
emits the canonical pipeline `to_dict()` object (schema_id/schema_version,
pipeline_status, projection_path, verification_status, reason_codes,
authority_effect=NONE, activation_authority=false, projection_only=true). The
entrypoint invokes the canonical pipeline exactly once and does not duplicate
gate, writer, reader, verifier, or serialization logic.

Illustrative outcomes (paths encoded per docs-token policy):

```text
# PASS (exit 0) — illustrative only; current readiness is typically BLOCKED
python -m src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0 \
  --repo-root . \
  --output-path out&#47;ops&#47;shadow_preparation_readiness_projection_v0.json \
  --format text
# status=PIPELINE_PASS

# BLOCKED (exit 2) — authorizes nothing; no Shadow/Paper/Testnet/Scheduler/Runtime
python -m src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0 \
  --repo-root . \
  --output-path out&#47;ops&#47;shadow_preparation_readiness_projection_v0.json \
  --format json
# {"pipeline_status":"PIPELINE_BLOCKED",...}

# ERROR (exit 1) — missing/invalid inputs fail closed
python -m src.ops.shadow_preparation_readiness_offline_operator_entrypoint_v0 \
  --repo-root /tmp&#47;missing_repo_root_illustrative \
  --format text
# status=PIPELINE_ERROR (or ENTRYPOINT_REPO_ROOT_INVALID)
```

This command is a **readiness-only component owner**, **not** the full-chain
canonical operator command, **not** a scheduler entrypoint, and **not** a
runtime entrypoint. It is offline preparation tooling only.
`PIPELINE_BLOCKED` never authorizes Shadow, Paper, Testnet, Scheduler, Orders,
or Runtime.

### Shadow Preparation Readiness Bundle v0 (read-only aggregate)

```text
SHADOW_PREPARATION_READINESS_BUNDLE_V0=true
BUNDLE_ONLY=true
READ_ONLY=true
PROJECTION_ONLY=true
AUTHORITY_EFFECT=NONE
ACTIVATION_AUTHORITY=false
ZERO_RUNTIME_ACTIVATION=true
```

`build_shadow_preparation_readiness_bundle_v0` (producer
`ops.shadow_preparation_readiness_bundle_v0`) aggregates already-existing
canonical offline artifacts into one operator-consumption bundle:

- canonical offline projection pipeline result (`to_dict()`);
- durable projection payload reread from disk (no re-serialization of gate
  truth);
- canonical reader/verifier result (`to_dict()`).

It invokes the canonical pipeline exactly once (reusing gate, writer, and
reader/verifier) and never introduces a second readiness truth. Missing or
unreadable required artifacts fail closed as `BUNDLE_BLOCKED` with reason codes;
values are never synthesized. Bundle statuses: `BUNDLE_PASS`, `BUNDLE_BLOCKED`,
`BUNDLE_ERROR`. The bundle authorizes nothing.

## Next permitted action

The offline no-order path is **proven** (`PROVEN_POST_MERGE_600S_SOAK`) and is
no longer the active blocker for that narrow scope.

STEP 29U binding/implementation inventory (docs/contract only; non-implementing)
is owned by
[`STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md`](STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md).
That inventory may claim `STEP_29U_INVENTORY_PASS` /
`STEP_29U_BINDING_SPEC_PASS` and, once the offline capability is present,
`STEP_29U_IMPLEMENTATION_PASS` for the offline non-activating chain only. It
must **not** claim activation, must **not** clear
activation authorization, and must **not**
reinterpret the soak as STEP-29U activation/closure.

This readiness producer remains classification-only:

```text
READINESS_PRODUCER_CANNOT_BIND_STEP_29U=true
READINESS_PRODUCER_CANNOT_IMPLEMENT_STEP_29U=true
READINESS_PRODUCER_CANNOT_ACTIVATE_STEP_29U=true
```

Offline STEP 29U capability owner:
`ops.step_29u_offline_capability_v0`
(`scripts/ops/run_step_29u_offline_capability_v0.py`). Activation remains
unauthorized. Next **activation-eligibility** work requires a **separate
operator GO**. No activation from this readiness contract alone. Runtime
remains `BOUND_NOT_ACTIVATED`. Economic validity remains not proven / blocked.
Dashboard blocker `MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY` remains OPEN
and separate.

## Explicit exclusions

Does not modify: Master V2, Double Play, Dynamic Scope, Risk/Sizing, Safety,
Runtime Bridge implementation, scheduler runner/models/jobs, WebUI/dashboard
implementation, economic-policy thresholds, order/execution adapters, or any
PR #5529 dashboard code.
