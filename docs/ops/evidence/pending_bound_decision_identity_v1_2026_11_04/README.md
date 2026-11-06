# Pending stored decision identity to Learning — 2026-11-04

Baseline 7b940091d. Cross-check of the normal context return contract found that
creation still reconstructed correlation from a cycle-name convention and kept
the concrete policy decision id empty. Resolver passes the Pending correlation
into evaluation runtime, Learning ingest and export, so this is consumer-visible
identity rather than cosmetic metadata. Capture legitimately accepts a supplied
correlation that differs from the default session-name construction.

The existing validated DPO/DecisionEvent reader now returns a frozen pair of the
stored parent correlation and exact producer policy_decision_id. Creation copies
these present facts for context-bound calls, rejecting a conflicting optional
caller decision_id. The boolean lineage-check entry point remains available.
Context-free legacy creation retains its old contract. Policy decision id and
DecisionEvent record ref remain different identities. Existing Pending records
are preserved; no silent metadata migration or re-certification of old records.

Three before-cases fail: guessed correlation, empty policy id and accepted caller
substitution. 73 connected cases PASS, followed by one additional actual-capture
→ Pending → elapsed N_BARS → Learning closure case PASS. That control uses explicit
injected declared-public input contracts and an injected clock in temporary roots;
it is not public-source authenticity or a natural-run witness. The actual captured
UNKNOWN generic parent is retained. Resulting Learning state correlation matches
the stored parent, proving the checked value reaches its real downstream consumer.

74 distinct cases across those runs. No formula, class, authority, original-ledger
or historical Pending mutation. Older records may retain old guessed/empty facts;
this change does not assert their provenance is now repaired. Source freshness,
complete episode target equivalence and cross-ledger atomicity remain separate.
U04/GAP-0370 deferred; no live/testnet operation or push.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[Learning consumer control](learning_closure.xml).
