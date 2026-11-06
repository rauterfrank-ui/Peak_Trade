# Bounded position episode to existing Exit owner

Local implementation on `1814ca5b24d1d3ab537683e340b3ab045ea51e62`,
2026-11-05. Subordinate to the master runbook and
[system composition contract](BOUNDED_SYSTEM_COMPOSITION_CONTRACT_V1.md).
No activation or external-effect authority.

## Purpose and historical distinction

At revision `2dba1355c9907c57fa330aed01a4072faeaf048f`, Cap 6.5's
`host_binding_v1.py` already restores entry anchors and pending Exit obligations.
Its producers remain inputs to the existing EntryExit owner, not another Safety,
Intent or execution owner. The corresponding wallclock bridge's
`decision_economics_cycle_bridge_v1.py:1307` substitutes the observation time
when an entry time is unknown. That historical host variant is preserved, but
its substitution is not adopted for an externally observed position episode.
The current core at the local baseline constructs a fresh Exit binding and
supplies no entry anchors on every invocation. File existence and the historical
Cap 6.5 restart claim therefore do not establish continuity in this current path.

The new explicit port connects a supplied position episode to that existing
Exit owner. It does not reconstruct an authentic fill from a current mark or
turn the time of adoption into the time of entry. Unknown anchors stay unknown.
The existing Scope derivation, policy producers, thresholds, precedence, DP,
quantity and full-close owners are unchanged.

## Identity, state and consumer contract

`position_episode_binding_v1.py` binds account identity, execution environment,
lane, canonical instrument, native contract, episode identity and long/short side.
Account/mode must match an independently supplied cycle scope; N1 can use the
already supplied durable host recovery scope, and rejects contradictions.
N1 preflights supplied episodes against actual per-lane position ingress before
consuming governed-cycle authorization. No map means the previous default path.
Providing a map requires contexts for occupied lanes and rejects foreign lanes.

Creation requires an explicit absolute, new directory. Recovery requires matching
identity metadata and complete original owner files; it cannot replace anchors,
adopt a partial bootstrap, migrate old roots or reset an obligation. The metadata
contains identity and source/price-basis declarations, with a content digest.
All numeric Exit state remains in the existing owner. A declared known entry
price requires `CONFIRMED_POSITION_ENTRY_PRICE` and a source reference; neither
the token nor its hash authenticates that source. Timestamps use the existing
event-time seconds contract, not a new processing clock. Trading epoch remains
a distinct optional integer. The v1 current port requires the existing canonical
TimeExit duration, and checks the existing dynamic adverse/profit policy digest.

Evaluation stages a copy. The actual existing producer receives original entry
anchors and the current confirmation binding. The core input binding includes
episode identity/source, prior state digest and actual producer digest only when
this port is supplied. A passing replay with an outgoing cursor publishes through
the original Exit writer; failed replay cannot commit the staged state. The
existing OS writer lock also protects a prior-sequence comparison, preventing a
stale handle from overwriting a newer Exit obligation. Readback must agree.

The N1 management path uses the actual remaining position and existing quantity,
DP and full-close owners. Its venue-plan input mode now follows the explicitly
bound episode scope; the legacy absent-episode default stays unchanged. The final
order envelope currently does not itself carry an environment field. This slice
does not establish mode binding across every later execution/permit consumer.
No permit is minted and no order is sent by this port.

## Restore and failure contract

The existing loader now requires the exact state/commit-marker manifest entries,
matching marker contents, exact state fields, explicit booleans/integers, finite
numeric values and the requested instrument. Integer-valued historic numeric
anchors retain their original digest representation. Any partial owner state is
blocked instead of becoming a new empty binding. Interrupted publication remains
detectable and blocked; no automatic repair is introduced.

The existing publication performs three sequential file replacements. It is not
a multi-file transaction or power-loss guarantee. Exit publication also precedes
the caller's decision-cursor publication. Cross-owner crash consistency/recovery
remains open (P08), and must not be inferred from the local writer CAS.

## Scope still open

This is a bounded Exit episode port, not full P05 acceptance or the entire planned
PositionEpisodeContext. Still required: a canonical authenticated entry/position
source builder, fill lineage and average-entry changes, confirmed-flat lifecycle
and next-episode adoption, session-root lifecycle, all caller variants, cross-owner
publication/recovery, and outcome association. Cold invocation/carry and outer N5
orchestration do not all expose this new context yet. Historical and original
ledgers remain unchanged. No whole-system readiness or natural economic effect
is established. [Bound verification](../evidence/BOUNDED_SYSTEM_LOCAL_IMPLEMENTATION_PHASE3_2026_11_05.md).
