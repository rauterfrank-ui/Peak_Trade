# OKX Futures Offline Shadow No-Order E2E — Post-Merge 600s Soak PASS

## Result and scope

**STATUS=PASS** — The canonical offline OKX Futures Shadow no-order path is proven
on `origin/main` by a post-merge monotonic-wallclock soak of more than 600 seconds.

This evidence proves **only** the offline no-order path. It does **not** prove
runtime activation, networked Shadow, exchange connectivity, orders, fills,
capital deployment, economic validity, Step 29U completion, Testnet readiness,
or Live readiness.

Canonical status token:

```text
OFFLINE_OKX_FUTURES_SHADOW_NO_ORDER_E2E_STATUS=PROVEN_POST_MERGE_600S_SOAK
```

## Canonical command

```bash
python scripts/ops/run_okx_futures_shadow_offline_e2e_projection_binding_v0.py --mode shadow
```

## Post-merge repository state

| Field | Value |
|-------|-------|
| PR | #5544 (merged) |
| Merge commit / origin/main | `bc7b9309b1f7e2e1411e22b483388331f355d0dd` |
| Soak worktree | see `git_state.txt` / `primary/soak_worktree.txt` |

## Exact timing

| Field | Value |
|-------|-------|
| SOAK_START_UTC | 2026-07-25T20:00:40Z |
| SOAK_END_UTC | 2026-07-25T20:10:40Z |
| SOAK_MONOTONIC_ELAPSED_SECONDS | 600.370976375 |
| SOAK_DURATION_REQUIREMENT_MET | true |

## Invocation counts

| Metric | Value |
|--------|-------|
| INVOCATIONS_TOTAL | 1287 |
| INVOCATIONS_SUCCESSFUL | 1287 |
| INVOCATIONS_FAILED | 0 |
| COMPLETE_FOUR_STAGE_CYCLES | 1287 |
| HOLD_CYCLES | 1287 |
| BINDING_PASS_COUNT | 1287 |
| BINDING_BLOCKED_COUNT | 0 |
| CYCLE_NOT_INVOKED_COUNT | 0 |

## Duration statistics (seconds)

| Stat | Value |
|------|-------|
| min | 0.451528 |
| median | 0.465016 |
| p95 | 0.472661 |
| max | 0.623872 |

## Stage-observation results

For every completed invocation:

1. Decision observed
2. Risk observed
3. Execution no-order observed
4. Reconciliation observed

Terminal outcome: **HOLD** (1287/1287).

## Safety invariants

- OKX Futures only; BTC excluded; Spot excluded
- ORDERS_CREATED_ANY=false; ORDERS_SUBMITTED_ANY=false
- NETWORK_ACCESS_ANY=false
- RUNTIME_ACTIVATED_ANY=false
- REPOSITORY_MUTATION_DURING_SOAK=false
- ACTIVATION_AUTHORITY_GRANTED_ANY=false
- SECOND_TRUTH_INTRODUCED=false

## Activation distinction

`CANONICAL_STEP_29U_ABSENT` remained truthfully present in the activation
projection (`CANONICAL_STEP_29U_ABSENT_REMAINS_TRUTHFUL=true`).

This is an intentional activation-path truth. It is **not** an offline Shadow
execution failure and must **not** be removed, downgraded, hidden, or marked
resolved by this evidence.

Runtime remains `BOUND_NOT_ACTIVATED`. No activation is authorized.

## Remaining blockers (separate; still open)

- CANONICAL_STEP_29U_ABSENT — OPEN_INTENTIONAL_ACTIVATION_PREREQUISITE
- ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL_BLOCKED
- DASHBOARD_BLOCKER_OPEN:MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY
- RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED
- HISTORICAL_SHADOW_SURFACES_NON_EQUIVALENT_TO_STEP_29U
- NO_ACTIVATION_AUTHORIZED

## Primary evidence retained

Under `primary/`:

- `soak_summary.json` — aggregate soak result
- `progress.jsonl` — 1287 per-invocation records (independent verification source)
- `progress_300s.json` — mid-soak checkpoint
- `MANIFEST.sha256` — original source soak manifest
  (SHA256=`c1aa75a0794488f3fb9a9b76f9734779f0ab65d00b8be7c81f8fa7654de8747a`)
- timing / command / git / heartbeat metadata
- `invocations_sample/` — first/mid/last invocation JSON + stdout/stderr samples

Full per-invocation stdout/stderr triples (1287 × 3 = 3861 files) were verified
in the local source directory
`/tmp/peak_trade_okx_shadow_soak_20260725T195942Z` (non-durable operator
machine path). Aggregate + samples are retained here for durable independent
validation without redundant identical triples.

## Reproduction and verification

1. Checkout `bc7b9309b1f7e2e1411e22b483388331f355d0dd` (or later main containing it).
2. Run the canonical command above in an isolated offline worktree (no network,
   no orders, no activation GO).
3. Independently verify this bundle:

```bash
# source soak manifest hash
shasum -a 256 primary/MANIFEST.sha256
# expect: c1aa75a0794488f3fb9a9b76f9734779f0ab65d00b8be7c81f8fa7654de8747a

# progress.jsonl line count and success
python -c "import json; rows=[json.loads(l) for l in open('primary/progress.jsonl') if l.strip()]; assert len(rows)==1287 and all(r['success'] and r['binding']=='BINDING_PASS' for r in rows)"

# durable bundle manifest
shasum -a 256 -c evidence_manifest.sha256
```

## Explicit non-claims

Do **not** read this bundle as authorizing or proving: activated Shadow runtime;
production-complete Shadow; exchange-connected Shadow; a validated order
pipeline; proven economic validity; completed Step 29U; Testnet readiness; Live
readiness; or full autonomy.

Correct formulation:

> The canonical offline OKX Futures Shadow no-order path is proven by a
> post-merge 600.37-second monotonic soak with 1287/1287 complete HOLD cycles
> and no orders, network access or runtime activation.
