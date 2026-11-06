# Explicit simulated flat seal and successor episode

Local implementation, 2026-11-05, baseline
`1814ca5b24d1d3ab537683e340b3ab045ea51e62`. Subordinate to the master
runbook and [episode progress](BOUNDED_SIMULATED_ACCOUNTING_EPISODE_PROGRESS_V1.md),
[source](BOUNDED_SIMULATED_ACCOUNTING_ENTRY_SOURCE_V1.md) and
[session](BOUNDED_OFFLINE_EPISODE_SESSION_V1.md) contracts. Partial P05/P01;
no activation or global release authority.

## Existing constructions and chosen boundary

The existing per-lane position/reconciliation helpers can accept an empty position
response or absent portfolio instrument as flat/harness admission. That is not
sufficient evidence to terminate this explicitly sourced episode. The new boundary
requires positive zero observations rather than inferring observation completeness.
It does not redefine every venue's authenticated empty-response interpretation.

The original `position_aware_rotation_v1` separately checks reconciliation,
external/pre-external custody and lane health. Its lifecycle wrapper supplies false
custody flags; this adapter does not adopt those literals as proof that all
obligations are gone. The original artifact matrix also purges selected state,
cursor and DDO files during release/rekey. This bounded path does not invoke that
purge or global rotation. Old roots/registrations/ledgers remain retained; a
successor uses separate roots. Position flat, order acknowledgement, capital/slot
release and pending Outcome completion remain distinct claims.

## Source and observation requirements

`simulated_accounting_close_v1.py` verifies the complete appended fill history with
the unchanged Accounting engine. A closed source has the distinct
`simulated_accounting_flat_source.v1` schema; ordinary initial entry-source loading
still requires an open position. The final CLOSE must belong to this exact opening
fill/episode key, end at zero and extend the previously verified source prefix.
Contract/unit metadata, initial equity and writer domain remain fixed. New event
times must be known. No current observation time becomes an original entry time.
Funding chronology remains unsupported as in the initial simulated source.

The caller must also supply all of the following:

- An explicit successful position response containing exactly one zero row for
  the bound native contract; an empty/missing/duplicate row is not accepted here.
- An explicit successful ordinary pending-order response with no pending rows.
- A healthy `PortfolioTruthSnapshotV1` with an explicit zero/FLAT canonical
  instrument, finite zero quantities and no other open portfolio position.
- Explicit positive close/event/capture/evaluation times in order, and an explicit
  finite snapshot max age. The snapshot must be after the close and within that
  supplied bound. No live monotonic freshness threshold is borrowed or invented.

Existing per-lane position truth and reconciliation owners consume those inputs;
the adapter requires their flat/admitted result after its stricter explicit
observation checks. The account/mode remains caller-bound simulation, not
independently authenticated venue data. Ordinary pending emptiness does not prove
all algo, capital, external custody or analytical obligations resolved.

## Terminal state and exact retained evidence

Before mutation, the original owner state/handle and prior occupied Scope cursor
must agree, including any retained Exit/cursor association. New flat source and
close audit artifacts are retained/read back before the original Exit writer CAS.
The close artifact includes full bound identity, observations, prior canonical
Exit state and byte-exact base64 copies with hashes of the prior state, marker,
manifest and immutable identity file. Reader validation checks those retained
bytes/marker/manifest, the original source domain/prefix, closed Accounting source,
and the original explicit flat observations.

The existing Exit state gains an optional versioned `simulated_accounting_close`
reference. A successful seal marks its local position closed, clears active entry
anchors, pending Exit/intent fields and active cursor/progress publication material,
and advances its original generation once. Cleared obligations remain exactly
represented in the retained prior-state audit. The resolution label is explicitly
`OBSERVED_SIMULATED_FLAT_NOT_ORDER_ACK`; it does not assert the recorded intent
caused a venue fill or release another owner's obligation.

Cursor bytes, Scope/SideState stores, governed evidence, Outcome/DDO journals and
resource registrations are not deleted, reset or repurposed. An old active-episode
restore or occupied-cycle call cannot reopen the sealed owner. The dedicated
inspector validates a historical `SEALED` episode; it is not a fresh assertion that
the whole account is currently flat. The raw prior bytes are supporting audit
material, not an automatic restoration/rollback mechanism.

## Session and successor behavior

`seal_flat_episode_v1` binds the existing composed lane, explicit replay bounds,
manifest, resource registrations and original source before its technical
`FLAT_SEAL_RUNNING` checkpoint. Success records terminal `SEALED`; failed/interrupted
work records or retains a review-required state. The attempt allowance/prefixes
are preserved. A sealed session can be reopened for validated inspection, but
decision calls, source updates and another seal reject. Context exit releases
cooperative leases; persistent registration remains historical and prevents silent
reuse of the old roots. No global slot or capital registration is freed.

`create_successor_after_sealed_simulated_episode_v1` validates the old seal and a
new open Accounting source whose complete history extends that closed prefix.
Account, lane, canonical/native instrument and Accounting domain remain bound;
the opening-fill-derived episode key must differ. New owner/archive writes cannot
target the old Exit/cursor roots or their descendants. Initial adoption delegates
to the original source/Exit adapter in a new exclusive state root. No old Scope or
cursor is copied. In the connected tests, the original current-core owner explicitly
bootstraps a fresh Scope/SideState in a separate cursor directory.

This is not an automatic all-caller bootstrap factory or proof that arbitrary
caller-selected cursors were freshly constructed. Global registration migration,
shared-account arbitration and every caller's episode/Scope binding remain open.

## Identity and remaining semantic questions

The actual old/new bootstrap tests produce equal existing `scope_id` labels in
separate roots, with different snapshots/SideStates. Those names are locally
deterministic and cannot alone identify a global episode. This composition retains
distinct episode keys, roots and content bindings; Scope calculation/ID producers
are unchanged. Consumers elsewhere that may use a bare Scope label as a global
deduplication or attribution key still require review. File isolation and differing
digests are not a claim that every downstream consumer has been verified.

The existing Adverse/TimeExit priority question from phase 7 remains unratified.
All-owner transactions, physical seal-time/power-loss recovery, natural fill/source
authentication, knowledge-time admission, global custody/capital/Outcome closure
and whole-system acceptance remain open. Sequential Exit publication still blocks
after partial failure rather than being silently repaired.
[Verification scope](../evidence/BOUNDED_SYSTEM_LOCAL_IMPLEMENTATION_PHASE8_2026_11_05.md).
