# Bounded offline episode session

Local implementation on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`,
2026-11-05. Subordinate to the master runbook and
[composition contract](BOUNDED_SYSTEM_COMPOSITION_CONTRACT_V1.md).
This is the already-open simulated episode profile, not the entire proposed
SystemCompositionManifest or an activated N5 service.

## Existing construction and chosen boundary

The existing `n1_standing_pre_external_runtime_supervisor_v1&#47;unattended_v1.py`
at `0808d2eed72edc9c4677f01da48cb5a8b11110dc` already retains technical
restart limits, source-tree binding and interruption checkpoints. Its actual
supervisor/request-factory/service boundary is separate from the new explicit
simulated-accounting episode API. This implementation uses the same purpose
(no renewed allowance on restart), but does not invoke its service, adopt its
wall-clock expiry as replay time, or infer permission from its historical tests.

The original Cap24/identity owners still define bound instrument and lane
generation; the original topology permits five slot identities while the current
position limit remains one. This profile therefore admits at most the existing
`MAX_POSITIONS_EFFECTIVE` open episode, in an existing allowed lane. It does not
turn five slots into five positions, override membership or select an instrument.

The composition package owns only its manifest, technical attempt receipt,
cooperative leases and resource registrations. Existing source archive, Exit,
cursor, LayeredCore, governed-cycle and quantity owners retain their state and
authority. No numerical financial state is copied into the session receipt.

## Manifest and startup contract

`manifest_v1.py` defines a strict typed/JSON manifest with no arbitrary factory
imports or network/signing ports. Its only source path is the existing applied
simulated-accounting adapter. Mode must be `INTERNAL_SIMULATED_EXECUTION`.
Unknown fields and duplicate JSON keys reject; no LIVE, TESTNET or SHADOW profile
is accepted. Mandatory bindings are:

- Session ID, declared repository revision and distinct origin-main reference.
- Exact current working-tree Python source digest over `src&#47;**&#47;*.py` paths/bytes.
- Existing Exit policy config digest and explicit account/mode scope.
- Explicit replay start/stop seconds and maximum total session attempts.
- Episode identity, existing bound-instrument identity/generation, retained source
  path/content digest, and existing absolute Exit/cursor owner roots.

Declared Git pins are bound to the existing records; this library does not query
Git to authenticate them. The local evidence report separately records actual
checkout HEAD/branch. The source digest detects disk-source drift, including
uncommitted files, not dynamic monkeypatches, credentials, configuration outside
that domain or dependency/binary integrity. The config pin is specifically the
existing Exit policy identity, not a certificate for every system policy.

Owner roots must be canonical, existing and pairwise disjoint. Sources cannot
reside inside these writable owner roots; the separate session root must not
overlap owners or source. Startup validates retained source/anchors and the actual
occupied cursor before creating session metadata. It acquires OS advisory leases
on the session and both owner roots, then rereads the owners. The current Exit/
cursor association must be coherent; pending publication is not silently repaired.

Explicit `create` registers the owner roots to this exact manifest/session root
and writes manifest plus initial receipt. Explicit `recover` requires all existing
registrations, manifest and receipt. A new root or session ID cannot silently
rebind the same registered owners and renew its counter after leases are released.
Missing or partial publication is retained and blocked, with no bootstrap/reset.
There is no automatic release/migration of these registrations in v1.

Leases are cooperative composition leases; old direct owner callers do not
participate in them. Original Exit/cursor writer locks still apply. A lease file
does not itself assert that a process is alive or that an episode is valid.

## Actual consumer and technical lifetime

`BoundedOfflineEpisodeSessionV1` is an explicit context manager. Its
`run_occupied_cycle_v1` validates the actual composed lane set/root, Cap24/native
identity, ranking/universe conformance and original instrument generation. It
rejects caller attempts to override episode handles/scope or inject a different
budget owner through this profile. It verifies the actual N1 signature before
charging an attempt, reloads retained source/Exit/cursor state, and checks source,
manifest, resource registration and receipt drift on every invocation.

Replay times are explicit synthetic UTC epoch seconds: observations stay within
the manifest window and do not go backwards; the last finalized event must lie
within that window and not after observation. These are replay bounds, not a
real-time watchdog, freshness policy or transfer of live flatten clocks. Reused
cycle prefixes reject before invoking the governed owner. The receipt stores the
attempt count, prefixes, last observed time and technical status.

Before calling the actual existing N1 consumer, the session durably charges the
attempt and records `RUNNING`. The session injects its recovered original episode
handles and explicit scope. Existing N1/S7/Exit/DP/quantity/full-close and governance
checks remain in force. Returned permits/POST counts must remain false/zero.
Completion returns the receipt to `READY`; this means no technical attempt is
in flight, not profitable, healthy, reconciled, filled or trading-admitted.

An exception records `RECOVERY_REQUIRED`. A process death can leave `RUNNING`.
Both statuses block further calls and automatic recovery/replay. The same manifest
and receipt preserve already used attempts across close/reopen. `close` releases
handles/leases without resetting financial owners, cursor or attempt allowance.
The context manager starts no thread, background loop, process manager or service.

## Publication and acceptance limits

Technical metadata uses same-directory temporary writes, file and directory
fsync, replacement and readback. Multiple registrations/manifest/receipt are still
sequential publications, not an all-owner transaction. Partial startup remains
blocked; original records are not repaired or deleted. A physical SIGKILL test
covers one technical checkpoint after the charge and before a real N1 invocation,
not a crash inside the actual N1 decision or hardware power loss.

This is partial P01. Flat bootstrap/adoption, registration release at a confirmed
episode end, dynamic average-entry updates, mixed flat/pending/open five-slot
orchestration, other policy/market/research/learning roots, budget-host composition,
full temporal admission, all-owner recovery and complete system semantic acceptance
remain open. No unattended-host replacement, default activation, service launcher,
network, credential, real order, capital or publication authority.
[Bound verification](../evidence/BOUNDED_SYSTEM_LOCAL_IMPLEMENTATION_PHASE6_2026_11_05.md).
