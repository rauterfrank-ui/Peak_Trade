# Bounded offline cycle/capture namespace v1

Status: implemented local simulated slice; no whole-system acceptance.
Revision anchor: local HEAD `1814ca5b24d1d3ab537683e340b3ab045ea51e62`
plus the explicitly uncommitted phase-9 source digests in its implementation report.

## Actual defect and causal path

Fresh original Scope owners can emit identical local Scope labels in separate
episodes. Those labels remain local and unchanged. Separately, the explicit
bounded Root previously forwarded an arbitrary caller cycle prefix. Two actual
Root→N1 sessions using that prefix could emit overlapping DDO record identities.
An initial Root namespace correction still left one collision: the integrated
replay decorator observed its result without a prebound host cycle context.
Its record carried a null cycle and `ddo.corr.default`. Post-replay observation
alone did not repair this already appended record.

## Binding and consumer effect

`cycle_namespace_v1.bind_offline_cycle_namespace_v1` hashes the complete canonical
preimage `{schema, manifest_digest, requested_prefix}` with the existing SHA256
helper. The exact caller label is retained, including its full length and Unicode;
neither sanitized labels nor truncated prefixes are identity preimages. The
manifest binds the declared account/exact simulated environment, episode, lane,
instrument generation, source, original owner roots, code/config and replay bounds.
This is declared provenance, not authentication of the account or venue.

The Root records the raw/effective mapping together with the durable attempt
charge before calling the original N1 port. Only that call receives the 64-hex
effective prefix. Existing lane/cycle suffix owners remain unchanged. There is
no new decision, episode, financial state or Scope calculation owner.

The CURRENT optional capture wrapper calls the existing
`bind_host_cycle_capture_context_v0` before replay. It binds the existing scope
configuration hash afterwards because the host binder clears that field. Thus
decorated in-replay observation and post-replay observation share the supplied
host context. If host time conversion fails, a temporary disabled capture binding
shadows any outer capture; replay still runs once, context is restored, and a
failed capture summary is returned. Producer exceptions continue to propagate.
Neither the financial replay nor an Outcome-source gate is rewritten by capture.

## Persistence and compatibility

The receipt file keeps its existing name but its schema is now
`bounded_offline_episode_session_state.v2`. `cycle_namespaces` must have one exact,
deterministically recomputed row per charged raw prefix. Changed/missing mappings,
foreign manifest digests and v1 receipts reject on recovery. No automatic
migration, retry, allowance renewal or rewriting of historical receipts/ledgers.
Code-pinned earlier manifests likewise require explicit review, as before.

## Acceptance evidence and limits

The actual Root→N1 test runs separate original simulated sessions with an equal
short prefix and, separately, an equal long Unicode prefix. Local Scope labels
remain equal; both decisions still close the original remaining quantity. Every
captured row carries the effective namespace, actual record sets are disjoint,
and appending both into a fresh original DDO ledger preserves the full count and
passes its integrity check. Recovery rejects mapping tampering and old receipts.
Configuration-isolation and capture fail-open controls remain required.

This proves the tested bounded path, not a universal uniqueness theorem. Existing
DDO/client-order ID formats are finite and some legacy builders truncate or
sanitize inputs. Direct callers outside this Root, unbounded suffixes, complete
global Scope/Decision identity semantics, shared Outcome consumers and actual
cross-domain learning remain separate acceptance work. Scope formulas and IDs,
Adverse/TimeExit rules, Accounting, MaxPos, ledgers and external-effect boundaries
are unchanged. The offline export remains `BLOCKED_UNVERIFIED_OUTCOME_SOURCE`.

See [phase-9 verification](../evidence/BOUNDED_SYSTEM_LOCAL_IMPLEMENTATION_PHASE9_2026_11_05.md).
