# Bounded system composition: implementation and semantic acceptance

Date: 2026-11-05. Local implementation baseline:
`1814ca5b24d1d3ab537683e340b3ab045ea51e62`.
Original implementation freeze: `732601aeacca7b87ff3df2e0373f180f8de50081`.
Local `origin/main` readback: `5d1c838c15369507c5247834db4dd0df25592169`;
this is a local ref observation, not a fetched remote-current claim.

This subordinate implementation contract consumes the user's explicit instruction
“Ja, lokale Umsetzung beginnen”. It records local code/test work only. The Master
Runbook remains the canonical navigation/authority entry. Its complete 10,273-line
baseline content was read before product mutation. Historical review/closure stamps
remain attached to their own revisions; none is upgraded to a whole-system review
of this working tree. The baseline working tree was clean.

## System-wide semantic acceptance requirement

The user's additional requirement is preservation of the originally intended
system behavior across domains. Each implementation package must establish:

1. The original purpose and evidenced historical variants, with source/revision.
   There is no assumed single unchanged historic design. Unknown origin remains
   unknown; a new desired decision must be named separately.
2. The producer's actual value meaning, unit, instrument/account/episode identity,
   event/capture/knowledge time, schema and persistence owner.
3. Every intermediate transformation and the actual consumer's use. A forwarded
   reference, digest, field, accepted record or green isolated test is insufficient
   to establish an intended numerical or behavioral effect.
4. A controlled positive case and a meaningful intervention/negative control at
   the actual boundary. State what changes, what must remain invariant, and why.
5. Restart/partial-write/duplicate semantics where that boundary owns obligations,
   preserving original records. Process restart is distinct from power-loss proof.
6. The remaining source, runtime and quality limits. Synthetic/injected observations
   cannot be promoted into naturally observed economic effectiveness.

This applies within and between Trading, Ranking, Treasury/Risk, Outcome/Learning,
Research/Optimization, Market Intelligence and shared evaluation/host services.
It is an acceptance discipline for the existing owners, not a parallel authority
graph. Guardian and a new general dashboard remain outside the implementation scope.

Important distinctions include reference mark versus fill price; market return
versus accounting PnL; event time versus information availability; complete position
exit versus partial reduction; order completion versus position/slot custody;
proposed research versus a measured experiment; and evidence versus permission.

Scope formulas/parameters, original ledgers and historical evidence remain
protected. This work grants no live/testnet, credential, venue request, order,
capital movement, promotion, publication or service-activation rights.

## First local implementation scope

P02 is partly implemented, not closed. The existing canonical fact DTOs already
define nested timestamps and scalar bid/ask. Their Economic-MD adapter previously
read a different shape, used a historical capture fallback and selected the first
stored quote. The adapter now reads existing fields, preserves the producer
kind/channel, requires an explicit capture, and orders quotes by event and exact
capture time through nanoseconds. Conflicting same-time quotes reject. Mark-only
facts cannot become ticker substitutes. Legacy top-level payloads require their
own explicit capture; no new historical time is supplied.

The finalized-mark consumer filters the native instrument instead of relabeling
all supplied facts. Canonical capture is preserved, including at restart readback.
Existing legacy API callers may still supply an outer capture only for payloads
without a canonical timestamp envelope. This compatibility path is not certified
as canonical-source proof.

Public store readback validates record schema, payload digest and complete newline
framing. Raw/legacy unwrapped, torn or changed records are retained and rejected;
no migration/reset/repair is performed. This is integrity checking, not source
authentication, rollback protection or transaction/power-loss durability.

P12 implements full first/second candidate result comparison alongside baseline
comparison. Retained first results are checked across downstream callbacks;
comparator/builder receive independent validated result copies. Registry readback
validates and rehashes content, returning a detached copy. Existing EvidenceBundle
hash domains and success output remain unchanged. The registry is still in-memory;
there is no distributed transaction or rollback guarantee for an injected registry
that mutates during its own registration. No whole-system quality claim follows.

P14 enforces the already declared expected Optimization evidence version at
federated Meta ingress, using the existing stale-contract result. `None` keeps the
existing non-federated optional-expectation meaning; actual payload validation is
still required. Existing M5 join identity, digest, Meta validation and no-authority
boundaries remain in force. This does not invoke the native Meta analyzer or Search.

## P09 ownership correction before further implementation

The proposal for a separate authoritative outcome-job queue must not be implemented
as written. The existing `natural_enter_cross_session_outcome_closure_v1` package
already owns pending records, journal authority, writer exclusion, exact stored
Decision/DPO admission and retained complete supplier measurement/information
artifacts. Its existing states remain authoritative. An orchestration projection
may reference those records; it must not introduce competing obligation state.

This corrects an omission in the design inventory. Pending creation/closure is
distinct from the blocked same-cycle capture-to-export seam. Remaining work is
actual source/episode continuity, release/rekey retention, consumer acknowledgement
and a complete connected episode. Existing source gates and original ledgers must
remain intact; fixture sources cannot be relabeled as real observations.

## Remaining composition work

P01/P03–P11/P13/P15–P17 are not implemented by this first change. In particular:
as-of/freshness and purpose-specific admission, WS envelope/sequence handling,
shared host lifecycle, single-invocation N5 completion, exit-episode continuity,
durable budget recovery passage, restrictive risk integration, research preflight
and recovery, measured domain fanout and combined system episodes remain open.
P02 is not closed by a quote decoder or store integrity checks. P12/P14 tests do
not establish historical completeness, natural learning or system readiness.

Source anchors: existing `facts_v1.py`, public normalizers and consumer/store modules;
GVEF V1.5 original pages retained in
`docs/ops/evidence/self_learning_original_design_gvef_boundary_v1_2026_11_04/gvef_v15_completeness_source_excerpts.json`;
runner introduction `5b1a7ab525b9853035766165ce041617a702f862` and current baseline;
existing federated ingress request/validator; Pending journal/artifact/decision
evidence dated 2026-11-04. These are distinct evidence kinds, not interchangeable
whole-system proof. Scoped verification is recorded in the local implementation
evidence note.
