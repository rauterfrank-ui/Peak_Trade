# N=1 Standing PRE_EXTERNAL Runtime Supervisor V1

**Authority:** orchestration/liveness only — `SUPERVISOR_ZERO_ECONOMIC_AUTHORITY=true`  
**POST:** forbidden (`POST_ALLOWED=false`, `EXTERNAL_EFFECT_AUTHORIZED=false`)

## Canonical entry point

```bash
./scripts/ops/run_n1_standing_pre_external_runtime_supervisor_v1.py --help
```

Production/scoped runs require:

- Durable store roots (public, private, lane state, evidence)
- Explicit expected account identity and an already initialized private budget owner; normal startup is recover-only. See [Treasury budget-owner startup contract](TREASURY_BUDGET_OWNER_START_CONTRACT_V1.md) for absolute/disjoint roots, bootstrap separation and remaining deployment limits.
- Valid `config/governance/current_productive_bounded_continuous_run_and_fresh_c1_get_owner_go_v1_decision.json` for the pinned baseline lineage
- Consumed Owner-GO evidence written under the evidence root (supervisor delegates to existing persistent natural-enter wiring)
- Read-only transport scope explicitly configured (no credential auto-discovery)

The launcher performs **one supervisor session** (recovery → public refresh → pretrade refresh → policy-governed continuous run). It does not activate POST or flip `CONTINUOUS_RUN_AUTHORIZED`.

## Recovery of a submitted Double Play close

When the scoped supervisor is explicitly supplied the private occupied-mark
proof root, it recovers the original L10 close before admitting another cycle.
The unattended host binds that exact private path into its request digest.
An omitted or different proof root fails the request binding before the
supervisor runs.
After exact order and fill reconciliation and confirmed flat, it reads the
authenticated OKX closed position for the original entry episode. The existing
reservation owner verifies the episode, settlement currency, fill PnL and
entry/close fees against the history row. Funding and futures settlement must
reconcile with the venue's realized PnL.

`CLOSE_NET_BOOKED` records the native-currency net result once in the original
owner's durable store. Restart replays the stored proof and booking without
another GET or economic write. `CLOSE_FLAT_CONFIRMED` with
`L10_CLOSE_NET_BOOKING_PENDING` retains the confirmed close while settlement
evidence is missing or inconsistent. Partial fills do not book. This step
does not release the capital hold, convert currencies, authorize a counter
order or activate the standing profile.

On `CLOSE_NET_BOOKED`, the supervisor submits a planning request to 29P for
the opposite side of the retained L10 switch on the same bound instrument.
29P verifies the original booking and hold with the reservation owner. The
supervisor reports a blocked sizing attempt until the productive protective
stop and funded slot capital basis are available. The check reads the
original slot and its booking; it does not request another allocation. The
original booking remains readable after restart. The unattended host's stop
receipt retains the close envelope digest, booking digest when present,
and the 29P sizing disposition when reached.

## WP-02 seam (CURRENT-WP-02 closed)

When `StandingSupervisorConfigV1.wp02_productive_default_enabled=true` (default) and
universe inject payloads are configured, the supervisor invokes
`build_default_wp02_hook_v1` → `run_wp02_productive_default_chain_v1` (Cap21 → real B05
→ Cap22 → hard-facts handoff). Set `wp02_productive_default_enabled=false` for explicit
no-op. See `docs/ops/specs/CURRENT_WP02_DEFAULT_PRODUCTIVE_UNIVERSE_HANDOFF_V1.md`.
