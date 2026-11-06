# Bounded Adverse/TimeExit consumer semantics v1

Status: local diagnostic repair and bounded semantic evidence. No new Exit policy,
partial-reduction quantity rule, activation or whole-system acceptance.
Local revision: `1814ca5b24d1d3ab537683e340b3ab045ea51e62` plus phase-10 report hashes.

## Reconstructed purpose and variants

The original user request in Cursor chat
`64bf4bc4-191f-4873-89ef-ea9c4e053fdf`, JSONL line 1, explicitly separates
Decision Policy from later Order/Execution semantics. It permits Adverse EXIT or
REDUCE under an explicit policy, requires versioned stable Exit priority and
keeps quantity unbound. This is an original intent source, not proof of execution.
Its timestamp and the earliest origin of all variants have not been established.

The locally reachable July-8 revision
`abb34f6d46559595b60a937ac58344f56f5524fb` already implements Adverse→REDUCE and
the mandatory ordering Adverse, Profit, Time, Invalidation. The September-23
restored baseline `2dba1355c9907c57fa330aed01a4072faeaf048f` and current local HEAD
retain that mapping. The latter commit is a shallow boundary; its absent parent
does not establish an uninterrupted history. Current original policy tests cover
mirrored Adverse REDUCE, Time EXIT and simultaneous-signal priority.

Cap 6.5 later retains the first triggered obligation in original Exit state and
reasserts its signal. It does not make that class defeat a newly triggered higher
priority class. RUN-0061 recorded this as static inventory at its own pin, with
no runtime proof; current phase-10 tests supply the bounded runtime evidence.

Therefore automatic TimeExit dominance, converting Adverse to full close, or
inventing a partial-reduction percentage would each be a new policy decision.
This implementation preserves the explicit original policy while exposing its
actual execution boundary. It does not ratify indefinite TimeExit preemption.

## Actual causal chain and repair

An original simulated Accounting journal supplies the exact episode anchors and
remaining `0.4` contracts. The original core first produces a due TimeExit; the
Exit writer persists its obligation, and the original cursor owner publishes its
cursor. After actual recovery, a new market observation triggers Adverse while
TimeExit remains true. The unchanged policy selects Adverse REDUCE.

Before this repair, occupied N1 replaced every reduction quantity result with
`REDUCE_RISK_RULE_REQUIRED`, even when the quantity owner reported missing
metadata or a rejection. Its public governed-cycle result then collapsed the
cause again into `POSITION_MANAGEMENT_EXECUTION_HANDOFF_REQUIRED`.

Now N1 preserves non-ready/rejected quantity results. Only a successful quantity
binding is labelled as awaiting an explicit reduction rule. When no execution
handoff exists, the original quantity reason reaches the governed-cycle
`first_genuine_blocker`/reason path; existing venue-plan reasons retain precedence.
This also preserves missing-metadata reasons for full-close decisions.
No financial result, quantity formula, authority or submission flag is changed.

## Persisted obligation versus fulfillment

Pending class/identity survive original owner recovery. The detailed `last_bundle`
is an in-memory evaluation result, not a restored persistent bundle. Tests inspect
the evaluated bundle before recovery and persistent class/identity afterwards.
Adverse REDUCE without a bound quantity produces no envelope, permit or post and
does not change the Accounting position. A prepared full-close envelope likewise
does not prove an applied fill; the existing Accounting/flat-seal path remains
the distinct local terminal proof. A technical `COMPLETED` or Root `READY` status
does not mean that an Exit obligation is fulfilled.

## Newly confirmed continuation boundary

The original governed-cycle ledger is single-use per evidence root. A subsequent
N1 call with a fresh cycle prefix rejects with `CYCLE_AUTHORIZATION_REPLAY` before
another decision execution. The actual test preserves the ledger and episode;
it does not purge or rebind them. The first obligation is staged through the
actual core, followed by one actual N1 call, not two successful governed cycles.

Consequently the session manifest's `max_attempts` is an upper technical charge
limit, not proof that multiple successful N1 cycles can use those roots. A future
continuation design must retain shared cursor/Exit/resource/budget ownership,
bind each original single-use authorization and its evidence to a charged
attempt, and preserve crash/no-retry rules. It must not renew budgets by choosing
new roots. No such continuation is introduced by this repair.

## Acceptance and remaining decisions

Eight new controls cover long/short, present/missing metadata, a deliberately
injected typed quantity rejection, retained TimeExit, exact public blockers and
the original replay guard. The rejection injection proves boundary transport;
it is not a claim that an invalid venue payload bypassed upstream admission.
Existing original priority, close sizing, restore, source, session, namespace and
seal controls remain required; see the phase-10 evidence.

Reduction sizing and temporal liveness remain separate requirements: define
which original risk owner can supply a quantity and when an outstanding TimeExit
must become terminal despite repeated higher-priority reductions. If TimeExit is
intended as a hard liquidation deadline, that rule needs an explicit versioned
policy change plus simultaneous-signal, Safety/HardRisk and reconciliation
acceptance. No historical source inspected here supplies that deadline override.

Scope calculation, thresholds, existing policy order, Accounting, MaxPos,
original ledgers and external-effect limits remain protected and unchanged.
