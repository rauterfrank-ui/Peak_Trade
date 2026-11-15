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

The reservation owner rechecks the original consumed POST Owner-GO in the
close submit store at booking and on verification replay. The record must
match the host repository revision. If it is lost during the GET sequence
or is invalid at booking, the verified flat readback is retained with
`L10_CLOSE_BOOKING_POST_OWNER_GO_UNPROVEN` as the reason for pending settlement.
The liveness notice exposes this reason alongside the confirmed flat status
and points to the original consumed record in the submitted close store.
Once the original record is readable again, a fresh admitted GET readback
can complete the booking against the same hold and original submit record.

`CLOSE_NET_BOOKED` records the native-currency net result once in the original
owner's durable store. Restart replays the stored proof and booking without
another GET or economic write. `CLOSE_FLAT_CONFIRMED` with
`L10_CLOSE_NET_BOOKING_PENDING` retains the confirmed close while settlement
evidence is missing or inconsistent. Partial fills do not book. This step
does not release the capital hold, convert currencies, authorize a counter
order or activate the standing profile.

The order reconciliation snapshot marks a full pending-order page as
incomplete, alongside full order-history or fills pages. This preserves the
hold when the required coverage is not proven. It does not fetch additional
pages or change the retained GET sequence.

On `CLOSE_NET_BOOKED`, the supervisor submits a planning request to 29P for
the opposite side of the retained L10 switch on the same bound instrument.
29P verifies the original booking and hold with the reservation owner. The
readback also records the historical mark and the opposite-side reference
derived from the retained switch through the existing Layer-C and 29P
formulas. It binds the original instrument, seal, snapshot and mark-response
digest. The reference belongs to the original switch time. It is a diagnostic
only and cannot supply a current sizing input or an order.

The supervisor reports a blocked sizing attempt until 29P has the current
protective reference for quantity sizing and proof of funding for the original
slot. The reference is a price input to the sizing equation. The reservation
owner checks the booked close, slot binding and original committed hold.
The hold records an existing commitment. Current free margin and funded slot
capital each require their own evidence. The check consumes no new allocation.
The liveness notice and unattended host's stop receipt retain both 29P
blockers. The stop receipt also retains the close envelope digest and the
booking digest when present. The booking remains readable after restart.

## WP-02 seam (CURRENT-WP-02 closed)

When `StandingSupervisorConfigV1.wp02_productive_default_enabled=true` (default) and
universe inject payloads are configured, the supervisor invokes
`build_default_wp02_hook_v1` → `run_wp02_productive_default_chain_v1` (Cap21 → real B05
→ Cap22 → hard-facts handoff). Set `wp02_productive_default_enabled=false` for explicit
no-op. See `docs/ops/specs/CURRENT_WP02_DEFAULT_PRODUCTIVE_UNIVERSE_HANDOFF_V1.md`.
