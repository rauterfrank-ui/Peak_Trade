# Bounded offline attempt continuation and data admission v1

E1 working contract; stage acceptance remains open. This is not a new numbered
implementation phase or a change to the six-stage completion criteria.

## Original owner and continuation

The original governed-cycle owner is intentionally single-use per evidence root.
Its code and consumed ledgers remain unchanged. The explicit bounded session now
passes a typed `OfflineGovernedAttemptV1` to N1 after durably charging the attempt.
The context binds the retained manifest, exact RUNNING receipt digest, effective
namespace, account/environment, episode roots, implementation digest and observed
clock. A different label, clock, account or charge digest rejects before execution.

N1 retains the original cursor root and shared lock root. Only its governed-cycle
evidence is placed below the original evidence root at
`offline_attempts_v1&#47;<effective_prefix>`. The original owner executes once there;
a repeat still triggers its existing `CYCLE_AUTHORIZATION_REPLAY` guard. A legacy
ledger directly at the old root blocks this profile rather than being reclassified
as a fresh allowance. Existing permanent resource registrations and session limits
remain binding. A failed/interrupted charged attempt still requires review.

This context is declared local composition provenance, not an authenticated
execution permit. Direct N1 callers without it retain the original paths and
single-use behavior. No new order, network, live or testnet authority results.
Existing cooperative session leases do not lock every arbitrary legacy caller;
there is no new claim of a global all-owner transaction or tamper-proof storage.

## Purpose and point-in-time data

The explicit `PublicFactPurposePolicyV1` declares purpose, exact consumer and
canonical instrument, allowed fact-kind/channel pairs, event and capture age
limits per kind, capture skew, correction admission and finality per kind.
All numeric limits are caller-supplied, with no productive defaults. A quote
does not inherit a candle finality requirement. The policy is not a numerical
feature definition or a substitute for the original downstream validation.

The public-runtime Economic-MD source has an optional RANKING admission profile
with an explicit `as_of_ms`. It reads original digest-checked durable facts,
filters event/capture/effective times to availability at that instant, rejects
wrong sources, wrong canonical identity, prohibited quality/corrections and
missing required kinds, and then runs its unchanged raw-input projection.
Supplying another purpose's policy cannot authorize this ranking source.
Original marks/window and quote checks remain downstream; no fill, forward-fill
or alternative price basis is manufactured. Legacy calls without an admission
profile retain their old behavior and are not newly certified as purpose-safe.

The common checker recognizes other purpose names for explicit binding checks;
TRADING, LIQUIDITY, OUTCOME and RESEARCH consumers are not thereby integrated.
Those consumers, exact feature units/windows and required policies need their own
actual call-path evidence before P03/E1 acceptance. The data profile and actual
occupied N1 continuation are separately tested slices, not one proven complete
public-fact-to-five-lane trading pipeline.

## Tests and retained limits

Actual long/short controls produce two close envelopes in one bounded session,
with a session close/reopen between calls, the same original Exit/cursor/lock
roots and retained TimeExit obligation. Both original governed ledgers remain
reachable and the first stays byte-identical after the second cycle. Same-attempt
replay, foreign namespace/account/clock/digest and exhausted allowance reject.
The Accounting quantity remains `0.4` contracts: no close fill is executed.

Durable store→actual ranking-source controls verify later event/capture/effective
versions cannot replace the as-of quote, distinct purpose rejection, exact source
and instrument, missing/stale/gapped/corrected inputs, per-kind finality and skew.
All time/quality thresholds in those controls are explicit synthetic test policy.

E1 remains in progress until its remaining N5, complete purpose-consumer and
configuration/session acceptance criteria are met. The old phase-2 completion
and host-fixture failures remain recorded; selected green tests do not erase them.
Scope geometry/parameters, original financial owners, MaxPos and original ledgers
remain protected. The six stages are worked sequentially without extra agents.
