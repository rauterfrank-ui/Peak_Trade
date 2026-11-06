# Local implementation phase 1 — 2026-11-05

Baseline `1814ca5b24d1d3ab537683e340b3ab045ea51e62`; local uncommitted changes.
Scope and limits: [subordinate implementation contract](../specs/BOUNDED_SYSTEM_COMPOSITION_CONTRACT_V1.md).

Before implementation, the corrected new regression suite exposes 14 failures
across GVEF result/readback integrity and federated expected-version admission;
12 existing/control cases pass. An earlier test construction error attempted
mutation of a `None` mapping; it was corrected before that 14-failure reproduction.
Eight separate public-fact consumer/store regressions fail against the baseline.
New tests inject public data, evaluators and callback faults; no real venue data,
credentials, order, capital movement or external notification is involved.

Post-change GVEF corpus plus federated and existing Meta ingest: 288 cases PASS.
This includes existing full GVEF suites, actual measured-learning reference tests
and 16 newly added result/version cases. Public-fact consumer/store plus existing
public runtime, hard-facts, N1 supervisor and WP02 consumer suites: 63 cases PASS,
including eleven new public-data cases. These are disjoint case populations;
intermediate reruns are not added to their totals.

Full deterministic success record comparison uses the original runner source
loaded from Git baseline and the same current dependency/fixture inputs: complete
`dataclasses.asdict` equality PASS. Original runner source SHA256
`fbc0856399a10ebcfff9747198a01b7e25a0cdbaf6d579916dae6590f5d003ea`;
unchanged protected output digest
`45030b87cf6cea7a130638cea326ea064739f4f7048f461322ad4f3a8c5847ea`.
This is a controlled implementation differential, not historical execution proof.
The optional federated expected-version control preserves the full valid result.

The public data control uses the actual REST mark parser and WS books5 normalizer,
then existing append/query storage and Economic-MD source adapter. It verifies
price, instrument, capture/event time and source-channel preservation. It does not
exercise the still-open WS event-sequencing path, whole Ranking pipeline or
independent freshness/source-authenticity admission. The broader retained suites
use their existing injected fixtures; test names do not enlarge their proof scope.

Canonical Python `./scripts/pt runtime-check` PASS before tests. Scope formulas,
parameters, configs and historical tracked ledgers/evidence are outside the changed
path set. Product changes remain local and reviewable; no commit or push.
No claim of full P02/P17 completion, whole-repository CI, natural economic quality
or activation readiness. P09 is corrected to reuse the existing Pending owner.
