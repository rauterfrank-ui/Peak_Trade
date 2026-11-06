# Exit-owned current cursor publication and bounded recovery

Local implementation, 2026-11-05, baseline
`1814ca5b24d1d3ab537683e340b3ab045ea51e62`. Subordinate to the master
runbook, [composition contract](BOUNDED_SYSTEM_COMPOSITION_CONTRACT_V1.md)
and [explicit episode contract](BOUNDED_POSITION_EPISODE_EXIT_CONTINUITY_V1.md).
This extends phase 3; its dated evidence remains unchanged.

## Purpose and owner decision

The current core commits Exit state before the caller persists its outgoing
SideState/confirmation cursor. Phase 3 had no retained association between them.
A reload could consequently combine a newer Exit obligation with an older
otherwise valid scope cursor and run another decision. Atomic publication of
each individual file alone does not identify that mixed pair.

The existing Cap 6.4 coordinator at
`2dba1355c9907c57fa330aed01a4072faeaf048f` has typed confirmation, dynamic
scope, config and accounting members. It is not bound to this current cursor/
Exit pair. Its goal is relevant, but its historical closure labels do not prove
this new composition. Its source promotes members before the marker, whereas
the older capability document describes the reverse order. Its recovery also
discards a journal rather than reconstructing this new pair. Those differences
remain an explicit review question; this slice neither invokes nor extends that
coordinator, nor upgrades its seven existing tests to broader crash proof.

For the bounded pair, the existing Exit owner now retains the exact outgoing
cursor as publication material, with prior/current digest and root binding. This
is an optional composition field within the existing authoritative Exit record,
covered by its original state/marker/manifest. It introduces no second numeric
Exit owner, new decision state machine or separate authoritative recovery queue.
The original cursor owner still owns its published cursor file.

## Additive payload and consumer behavior

`CanonicalExitPolicyStateV1.current_cursor_publication` is optional. When absent,
serialization omits it entirely, preserving the original field shape and digest
domain. The loader permits exactly the historical field set or that field set
plus this dictionary, rejecting other fields and explicit null/nonobject values.
Old roots are not rewritten or automatically migrated. The first explicit
episode cycle can establish a binding; earlier interrupted cycles with no retained
binding cannot be retroactively certified or recovered by this mechanism.

The nested schema `exit_owned_current_cursor_publication.v1` binds:

- The complete episode identity, including account/mode/lane/native contract.
- The resolved absolute cursor root and prior Exit generation.
- The incoming canonical cursor digest.
- The exact outgoing cursor payload and its canonical digest.

The next episode-enabled core call requires its restored incoming cursor to match
that outgoing digest, before feature/confirmation/decision processing. N1 also
performs this check against the actual lane cursor file before consuming the
governed-cycle authorization. Missing/foreign/older state cannot silently reset
the association. The existing policy formulas and Scope computations do not
change. The absent-episode path has no new association requirement.

## Explicit bounded recovery

`recover_current_cursor_publication_v1` is a local API, not a service, scheduler
or automatic invocation. The caller provides the existing episode, expected
account/mode and cursor root. Under the original Exit OS writer lock, it reloads
the original owner state and requires exact equality with the supplied handle.
It validates nested schema/identity/root/generation/digest and uses the existing
cursor restore owner to validate the retained outgoing payload and scope carrier.

If the current cursor is already exactly outgoing, recovery returns
`ALREADY_PUBLISHED`. If it is exactly the retained incoming cursor, recovery
publishes only the retained outgoing cursor and returns
`PUBLISHED_RETAINED_CURSOR`. A missing, damaged or unrelated file, stale handle,
foreign root/scope or invalid retained record is rejected and preserved.
Recovery does not rerun the decision, advance the Exit sequence, replace anchors,
clear an Exit obligation, repair partial Exit publication or grant execution rights.

The cursor owner's file publication now uses an advisory OS lock, same-directory
temporary file, file flush/fsync, replace and readback. An optional expected-prior
digest is checked under that lock; recovery always supplies it. Ordinary legacy
calls retain their previous overwrite policy unless a digest is explicitly
provided. All callers get indivisible file replacement rather than direct
truncation. Interrupted operations retain either the old or new cursor file;
idempotent recovery distinguishes those cases. The lock file is infrastructure,
not an owner record or evidence of a live process.

## Acceptance limits

This detects and explicitly completes one Exit-to-cursor publication gap. It is
not a transaction across LayeredCore, DDO, governed authorization, budget, fill,
accounting or outcome owners. Other writers using unguarded legacy paths can
still change their state; no session-wide lease, tamper/rollback defense, durable
shared transaction or automatic N5 recovery is claimed. Retained payload copies
are recovery material, not another currently usable decision authority.

The three Exit files still publish sequentially and can fail closed after partial
publication. Parent-directory fsync and actual process/power-loss fault coverage
are not established. A Python fault injection followed by disk reload is narrower
than an operating-system crash experiment. Authentication of entry sources,
confirmed-flat lifecycle, session identity and all callers remain open.
[Exact verification scope](../evidence/BOUNDED_SYSTEM_LOCAL_IMPLEMENTATION_PHASE4_2026_11_05.md).
