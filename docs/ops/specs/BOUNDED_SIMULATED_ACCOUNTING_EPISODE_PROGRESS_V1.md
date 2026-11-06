# Verified simulated accounting progress within an existing episode

Local implementation, 2026-11-05, on
`1814ca5b24d1d3ab537683e340b3ab045ea51e62`. Subordinate to the master
runbook, [initial source](BOUNDED_SIMULATED_ACCOUNTING_ENTRY_SOURCE_V1.md),
[episode](BOUNDED_POSITION_EPISODE_EXIT_CONTINUITY_V1.md) and
[session](BOUNDED_OFFLINE_EPISODE_SESSION_V1.md) contracts. No activation.

## Purpose and variant decision

The original Accounting owner calculates the current weighted average on an
increase and preserves it on partial reduction. The legacy Exit binding instead
prefers its restored entry anchor while an open position remains open. Phase 5's
initial simulated adoption already supplies the current Accounting average, but
subsequent increases could leave that adopted value frozen. First-open time and
current average price are different quantities in the proposed episode contract.

This explicit simulated update path chooses the verified current Accounting
average as the existing Exit producer's price basis throughout that episode.
It makes ongoing updates consistent with initial simulated adoption, retaining
the original opening fill/time. This is an explicit composition decision, not a
claim that every historical host used an updating average. The legacy absent-
progress path and protected producer formulas/thresholds/precedence are unchanged.

The existing Accounting engine at `af2f748de6424910ea6f2b56856c9f972c1111b7`
still verifies all fill input/output digests and computes price/quantity. No new
average, PnL or quantity arithmetic is introduced. Simulated source declarations
remain distinct from authenticated venue fills and original Decision attribution.

## Append-only source transition and numerical owner

`advance_position_episode_from_simulated_accounting_v1` requires a matching
account/mode and current Exit handle, then the same complete source verification
as initial adoption. All previous fill bodies must remain an exact prefix. Contract
metadata (including multiplier/unit), initial equity and Accounting writer identity
cannot change. New fill event times must be known; an unknown original opening
time remains unknown. A full close or another opening is not a same-episode update.
Repeated identical fill history is acknowledged without advancing Exit state.

The new immutable source artifact is retained and read back through the same
archive owner. The initial identity/source reference remains unchanged. An optional
`simulated_accounting_progress` dictionary in the existing Exit state records the
initial, previous and current source references, fill count and latest fill event
time. Source payloads are read once for digest verification and consumption; a
second unchecked read is not used. Initial/previous/current archives are replay-
verified, checked for prefix/domain continuity and bound to the current anchors.
The core input binding keeps its original source reference and adds an explicit
`current_entry_source_ref` only for progress-enabled episodes; consumers need not
misinterpret the initial adoption archive as the current price-basis source.

The existing numeric Exit `entry_price` changes to the verified current average.
Opening time/epoch, episode/account/side/instrument identity, policy config and
pending Exit/intent identities remain unchanged. Quantity remains in the original
Accounting source/position owners; the new Exit field retains references rather
than becoming another numerical position ledger.

The transition uses the original Exit writer lock, expected generation and
readback. Ordinary decision commits still reject entry-anchor or source-progress
changes. Only this verified source transition uses the shared private persistence
protocol for its specifically validated update. A stale or racing writer cannot
overwrite a newer obligation. An orphan new source artifact after a failed commit
is retained, not treated as authoritative active state.

Both optional composition fields are omitted when absent; the new loader accepts
the original required state fields plus either/both dictionary extensions. Explicit
null/nonobjects and unknown fields reject. Nested progress schema is versioned.
Earlier code need not accept new fields; no downgrade or automatic migration is
claimed. Historical state serialization/digest representation remains preserved.

## Cursor, consumer time and remaining quantity

Before advancing, the actual cursor must restore with an occupied Scope and agree
with any retained Exit/cursor association. The update publishes an identity cursor
association in the same Exit generation: incoming and outgoing cursor digest are
the same. The cursor file, its clock and decision epoch do not advance. Earlier
decision-cursor publication cannot be replayed over this newer update generation.

The current core rejects a market observation earlier than the latest appended
fill event. This is an event-time bound for this simulated progress, not proof of
capture/knowledge time, natural source freshness or all legacy-path as-of semantics.
Original unknown times are not fabricated.

At N1 preflight, a progress-enabled source additionally requires the actual
per-lane observed native-contract quantity to equal the verified current Accounting
quantity. Missing or different quantity rejects before governed authorization.
The adapter does not overwrite position ingress or substitute source quantity for
an absent observation. The existing full-close owner still closes its observed
remaining quantity under its existing unit/metadata rules.

## Session composition and interruption

`BoundedOfflineEpisodeSessionV1.advance_accounting_episode_v1` reloads its existing
sources/owners and checks manifest, registration and receipt drift. The current
source reference advances in Exit state, so the manifest can retain its immutable
initial source and bounds. Recovery verifies the current source rather than
resetting average price to the initial snapshot.

The session records `SOURCE_UPDATE_RUNNING` before invoking the transition and
returns to `READY` after success. Attempt count, consumed cycle prefixes and replay
clock allowance are not renewed or charged as another decision. Exceptions record
`RECOVERY_REQUIRED`; interrupted update statuses cannot automatically resume. This
is explicit source-state adoption, not a fill application or order execution.

## Observed priority interaction and remaining acceptance

The original producer can trigger Adverse from distance to entry price, and the
original EntryExit owner resolves Adverse before TimeExit. A retained TimeExit
signal/obligation therefore does not guarantee that the next final action is
full EXIT: the tested large upward average shift in a long position produces
`adverse_scope_exit` and final `reduce` while the original TimeExit identity and
signal remain active. This interaction is observed current behavior, not ratified
as the intended end-system response merely because it is unchanged. Domain
acceptance must resolve its meaning and mandatory-exit fulfillment separately;
this slice changes no protected priority, Scope calculation or reduction rule.

Full position close/release and registration migration, real venue source and
unit authentication, funding chronology, unknown-event admission, all-owner atomic
transactions/power-loss recovery and complete P05/system acceptance remain open.
The three Exit files still publish sequentially; a partial publication blocks
reload instead of being automatically repaired. No physical source-update crash
proof is claimed. [Exact verification](../evidence/BOUNDED_SYSTEM_LOCAL_IMPLEMENTATION_PHASE7_2026_11_05.md).
