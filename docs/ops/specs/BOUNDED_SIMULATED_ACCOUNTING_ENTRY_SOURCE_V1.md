# Applied simulated accounting fills as an explicit episode source

Local implementation, 2026-11-05; baseline
`1814ca5b24d1d3ab537683e340b3ab045ea51e62`. Subordinate to the master
runbook and [episode contract](BOUNDED_POSITION_EPISODE_EXIT_CONTINUITY_V1.md).
This is an optional offline source adapter. It does not activate a host, capture
venue data or authenticate a real account/position.

## Source reconstruction and decision

The current per-lane position resolver at `0808d2eed72edc9c4677f01da48cb5a8b11110dc`
uses instrument-specific position responses to establish quantity/side. Neither
that DTO nor `PortfolioTruthSnapshotV1` establishes an original entry time or
an accounting average-entry price. A mark, position-status observation, response
receipt time or raw position cTime must not silently become a fill/entry anchor.
The purpose-specific live flatten freshness policy is not transferred here.

Cap 3.1's existing accounting engine, most recently changed at
`af2f748de6424910ea6f2b56856c9f972c1111b7`, already handles simulated opening,
same-side increase, partial reduction and close through the canonical futures
kernel. Its current checkpoint version 2 retains ordered fill IDs, original input
and output digests, and the current position. Restored result objects project the
current portfolio; those objects alone cannot reconstruct historical fill times.
Complete supplied fill bodies must therefore match the applied original digests.

The adapter reuses that original engine for verification, rather than implementing
another weighted-average or position lifecycle calculation. The new construction
is bounded to `INTERNAL_SIMULATED_EXECUTION`. LIVE, TESTNET, PAPER_EXCHANGE and
SHADOW are rejected. No simulated evidence can be relabeled through this API.

## Actual source and consumer contract

`simulated_accounting_entry_source_v1.py` provides explicit create/recover APIs.
It freezes the supplied accounting session through its own strict checkpoint
loader, requires the exact complete applied fill order, and replays those fills
in a fresh original accounting session. Each original input digest, accounting
output digest and action must match. The final portfolio, risk projection and
last fill time must also match. A later mark update is replayed through the same
owner; it never becomes the entry price. Ordered funding replay is not implemented,
so sessions with funding events or nonzero funding PnL reject rather than guessing.
This verification does not mutate the caller's session or its original ledger.

The last original OPEN action after any CLOSE identifies the current simulated
episode. Its fill event time, in seconds, is the first-open anchor. A missing time
stays missing even if later fills have times. No trading epoch is invented.
The current average entry comes from the verified accounting position, including
same-side increases and preserving the average through partial reductions. The
archived accounting values remain Decimal strings; the existing Exit owner still
consumes its original floating representation. No new precision policy is claimed.

`bind_simulated_accounting_episode_identity_v1` binds the episode key to the exact
opening-fill digest plus account/mode/lane/instrument/side context. This mapping
is checked against the actual replayed OPEN. Partial reductions retain the key;
a later opening after simulated flat has a different key. Caller-supplied account
scope is a binding declaration, not authentication: the accounting session has
no independent account credential identity. Identity continuity cannot manufacture
historical Decision-to-fill attribution.

Before creating Exit state, the adapter writes a new content-addressed source
artifact under an explicitly supplied absolute archive root. The artifact contains
the complete initial checkpoint, fill bodies and episode identity. Canonical
payload digest and original-engine replay are checked on readback. Existing bytes
are never overwritten or repaired. A failed later context creation can leave a
retained source artifact; it does not make that artifact an active episode.

The original episode identity record references the exact source path and digest.
Creation delegates numeric anchors to the existing Exit owner using its existing
price-basis token, within the strictly simulated account/mode. Recovery validates
the retained source again, then requires the same source reference and numeric
anchors in the original Exit state. A changed archive, substituted source or
different opening cannot quietly reanchor an existing episode. It retains the
existing pending Exit/cursor association. Generic low-level episode APIs remain
caller-supplied ports; not every existing episode is upgraded to this source class.

## Acceptance and limits

Controlled tests reach actual current-core TimeExit and actual N1/S7/DP/full-close
quantity processing for both long and short, using a verified remaining position
of 0.4 from the original accounting history. No order or permit is created. The
source archive is supporting provenance, not a new live position/quantity owner.

This supplies an initial simulated adoption/reload path. It does not update the
entry basis of an already-open Exit context after later increases, automatically
close/release that context at flat, rotate lanes, run a shared session root, or
automatically install the adapter in an outer N5 service. Real venue source
authentication, freshness/as-of admission, original decision/fill association,
quantity-unit reconciliation across real venues, funding chronology, all-owner
transaction/recovery and whole-system semantic acceptance remain open. File fsync
and readback are not directory/power-loss durability or rollback protection.
[Scoped verification](../evidence/BOUNDED_SYSTEM_LOCAL_IMPLEMENTATION_PHASE5_2026_11_05.md).
