# Local implementation phase 9 — 2026-11-05

Local HEAD `1814ca5b24d1d3ab537683e340b3ab045ea51e62`; uncommitted implementation,
no activation or whole-system semantic acceptance.

## Verified change

An actual two-session Root→N1→DDO→shared-ledger control exposed overlapping
DecisionEvent IDs when callers reused a local cycle label. Merely hashing the
Root prefix left one in-replay record with null cycle/default correlation. The
CURRENT capture wrapper now binds the existing host context before decorated
producers run; the Root derives its transport prefix from the full manifest and
raw caller label. Exact namespace/attempt mappings are retained and checked on
recovery. Receipt schema v2 rejects legacy v1 without rewriting it.

The original Scope labels still repeat across these separate roots. Actual
captured record sets are now disjoint for both short and long Unicode labels;
the original combined DDO ledger preserves all records and verifies integrity.
Original N1 still yields `exit`, quantity `0.4`, in both independent scenarios.
This is concrete consumer evidence for the bounded path, not proof of global
Scope identity, all downstream joins or authenticity of declared account data.

## Checks and corrections

- 345 distinct relevant test cases have successful latest observations: the
  connected run had 344 PASS and one stale schema assertion failure; the final
  targeted run passed all 17 cases in the two affected test files, including
  the corrected case. No source code changed between these runs. The local
  phase-9 JSON report retains both receipts and verifies their exact union.
- The stale schema assertion also failed with only the capture wrapper replaced
  in memory by its unmodified local-HEAD body. That controlled comparison is not
  a claim that the whole checkout at HEAD was tested.
- The omitted schema was the already existing Double-Play policy-input evidence,
  not a new Incident. The test now uses the original ledger reader, checks
  integrity and verifies that input evidence points to a retained DecisionEvent.
  Its `BLOCKED_UNVERIFIED_OUTCOME_SOURCE` assertions remain intact.
- Current scope-learning configuration controls: 31 PASS. Original policy-input
  evidence controls: 22 PASS. Prior phase-8 connected population: 272 PASS again.
- Namespace controls: 7 PASS, including actual two-session/shared-ledger tests,
  full-prefix distinction, altered receipt rejection and legacy schema rejection.
- Capture context failure is observation-only: producer runs once, disabled
  temporary capture shadows an outer context, stale identities clear, and the
  outer context is restored. Existing capture/I/O financial-parity controls pass.
- Scoped Ruff lint/format and Git whitespace checks pass. Protected owner bytes
  and retained phase-8 files are checked separately in the JSON report.

## Remaining limits

Scope/Decision namespaces outside this Root, finite/truncated client-order IDs,
global Outcome/custody/capital/slot release and actual cross-domain learning
still need investigation. The existing Adverse REDUCE versus pending TimeExit
interaction remains unratified. No protected formula, policy parameter,
Accounting owner or original ledger is modified. No migration, service, network,
credential, order or publication action is introduced. The separately documented
phase-2 baseline failures are not erased by this selected green population.

[Contract](../specs/BOUNDED_OFFLINE_CYCLE_CAPTURE_NAMESPACE_V1.md).
