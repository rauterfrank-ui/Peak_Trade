# Research memory return roles — 2026-11-04

Pin 31bc249c0; supports Blueprint 71. Read-only current owner/contract review.

The canonical Failure Memory store exposes validated append, get, list_records,
fingerprint lookup and duplicate assessment. Append is idempotent for identical
canonical content and rejects divergent content for an existing record identity.
This provides persistence and retrieval capability; it does not choose research.

Phase10 accepts existing_failure_records separately from its optional output
failure_memory_store. It assesses supplied prior records after explicit hypothesis
selection and identity/fingerprint preparation. A detected duplicate without an
explicit retest reason raises; a reason permits a reviewed retest, not automatic
research banning. Newly produced failure records can be appended to the supplied
store. It does not itself load prior records from that output store or select a
new hypothesis from returned failures.

Advanced Search already accepts explicit failure_records, reality_gap_records and
retest_reason. It validates supplied records and uses them before candidates can
be proposed. Exact duplicates can become explicit rejected evidence; known failed
parameter regions can be retained with deprioritized status. Its contract preserves
negative evidence and forbids silent omission. These are existing behavioral
consumer seams, not just decorative memory references.

The current outer M4 request exposes Meta signals/identity but not those three
Search memory/retest inputs; its call does not pass them, so Search defaults apply
there. The direct Search owner and Phase10 remain separately usable. This local
wrapper fact is not a proof that every host lacks memory feedback or that the
original bounded M4 contract required automatic store ingestion. No speculative
forwarding change was made.

Existing test bodies demonstrate manual chaining of Phase10 failure output into a
subsequent request and separate optional persistence; Search tests supply a known
failed region or duplicate to exercise its policy. Those fixtures establish the
test's intended scenario, not a newly executed PASS or an automatic scheduler.

Smallest candidate continuation: identify the actual outer caller and its history
selection/time/version/comparability responsibilities, reuse the existing validated
reader and request fields, then verify actual downstream choice changes. If that
caller belongs to M4, determine the explicit contract extension required. Do not
replace Failure Memory or invent automatic selection/retest authority. Persistence,
request assembly and effect on next research are three separate facts.
[Sources](sources.json), [receipt/checks](receipt.json). No runtime mutation or
natural-data run; U04 and GAP-0370 remain deferred.

## Follow-up: intermediate composition hosts

[Source-bound host inspection](intermediate_hosts_review.json) at b175c5985 extends
the exact-symbol check with actual intermediate components. The MI offline
orchestrator's memory helper appends, assesses duplicates and reopens/reads the
store twice for deterministic replay comparison. Its optional M4 branch supplies
the caller's plane request separately; the helper's loaded records are not fed
into that request. This is real persistence/read composition, not demonstrated
next-choice adaptation.

The autonomous non-live orchestration plan evaluator rejects requested scheduling,
execution and runtime start. Its CLI produces a declarative, non-authorizing
bundle. A plan with stage contracts is not an installed research scheduler. It
also carries scope restrictions of its own; do not transplant it unchanged into
the current target based on its name. Other research-surface-specific orchestrators
were located but not certified as universal hosts. No existing host was started.
