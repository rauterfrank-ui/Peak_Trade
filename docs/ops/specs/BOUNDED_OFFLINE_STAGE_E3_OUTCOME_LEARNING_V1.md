# E3: retained Outcome and actual offline learning consumer

Status: implementation contract for P09/P10 and AC21–AC24, 2026-11-05.
Authority: explicit local implementation only. E3 does not accept the whole system.

## Existing ownership and original intent

The original Pending owner already has a validated append journal, compare-and-swap
updates, writer exclusion, terminal states and full natural measurement artifacts.
The proposed separate authoritative Outcome queue in the first design is superseded
by the existing-owner decision in BOUNDED_SYSTEM_COMPOSITION_CONTRACT_V1. The new
`offline_v1.py` is inside that owner package. Its lifecycle is a projection of the
same Pending events, not a second mutable job index or resettable retry counter.

The historical natural-only creator/resolver, source-class checks and
`BLOCKED_UNVERIFIED_SOURCE` export boundary retain their original code. No natural
Pending record is fabricated by this adapter. The selected new port accepts only
`SYNTHETIC_OFFLINE`; historical replay and authentic natural observations need their
own independently supported admission. An injected canonical bar is not authenticated
market evidence. No fixture is relabeled as productive natural evidence.

## Explicit entry and target

`create_explicit_offline_pending_v1` requires a retained source ledger, exact typed
PendingDecisionContext, stored DPO/Decision lineage, original OUTCOME purpose source,
explicit synthetic source class, forecast, account, venue, N, acquisition deadline,
retry interval, attempt budget, job capacity and byte backpressure threshold.
There are no productive numeric defaults. The test profile is not an operational
policy ratification.

The source ledger is copied byte-for-byte under its existing writer exclusion.
Every source record must precede or equal the declared decision knowledge time.
No absent market/feature/risk/position snapshot is reconstructed; absence is listed
in the capsule. The copied ledger's envelope ingestion timestamps retain their
original values: an explicit offline knowledge clock does not prove historic capture
availability. The immutable original DecisionEvent is never retimed or rewritten.
The original selector receives the separate, later context knowledge time, while
the supplier/evaluator still consume the original captured DecisionEvent.

The chosen target is LOG_RETURN over N >= 2 finalized PT1H closes. The horizon opens
at the first hourly grid boundary at or after decision knowledge time. N closes
span N-1 close-to-close return intervals. Decision mark and grid-open time are
not the first close price. Instrument and bar-spec refs are minted with the
original bridge's content-reference helper. The pre-existing forecast must carry
that exact target and be created by decision knowledge time. Revised/corrected
price bases do not silently replace this selected finalized-price target.

The original purpose consumer enforces capture/as-of, instrument, units, source,
finality and correction policy. Missing first bars cannot shift the target window.
The original supplier creates the complete measurement/information-set pair; a
reload reruns that supplier over the retained snapshot and validates its exact
artifacts. No partial result is converted to zero or an economic score.

## Retention and state transitions

The explicit retention root must be outside the purgeable source lane. A deterministic
key binds Decision, exact target, account and source class within that retention root.
Changing a source store, forecast or policy for the same obligation conflicts rather
than creating an extra independent sample. Only the existing Pending journal owns
PENDING/IN_PROGRESS/CLOSED/FAILED_TERMINAL. Event details project WAITING_SOURCE,
WAITING_HORIZON, WAITING_STALE_SOURCE, EXPIRED, QUARANTINED and retry exhaustion.
Retries are charged before source acquisition. Backward clocks block; early retry
has no additional charge. An already persisted measurement can finish its consumer
handoff after the acquisition deadline, without fetching new data or resetting retries.

`artifact_matrix_v1.py` calls retention at the actual release/rekey boundary.
All previously purgeable paths, cursor and old identity manifest are inventoried,
copied outside the lane, fsynced and read back before an immutable retention ACK.
Only then are original paths moved into `released_originals`. Originals are not
recursively deleted. The archive retains malformed historical bytes too; retaining
bytes is not certifying their semantics. The original DDO writer lock blocks release
against a concurrent ledger writer. Copy, storage, readback or ACK failures block
release; interrupted moves retain verified snapshots and are finishable.

Job count and retained-byte high-water checks apply to the explicitly selected
retention root. Byte checks are backpressure thresholds before new acquisition,
not a filesystem hard quota or a bound on the size of every subsequent owner write.
They never garbage-collect open pins. Existing terminal/deadline evidence remains
recordable. Durable capacity reservation, archive GC, distributed writers and
power-loss certification are not claimed by E3. Other existing mutable owners still
need their normal quiescent lane-release preconditions; the DDO lock alone does
not create a distributed generation transaction.

## Actual consumers and ACK

A common learning scope gate precedes the selected SelfLearning, Optimization and
MI handoffs. Source class, semantic pool, external-capital NONE, account, captured
code/configuration, scalar, horizon and exact target/metric remain distinct.
The existing SelfLearning and Optimization eligibility gates also run. Optimization
now rejects the capital contamination already rejected by SelfLearning, preventing
a direct projected-evidence bypass. Legacy paths are not automatically certified
by the selected port.

The existing DDO evaluator persists its outcome/attribution/counterfactual bundle;
the original ingest persists a LearningState record. The original Optimization
input validator consumes the actual exported evidence; its complete input/result
is retained as an immutable artifact. This is input admission, not an optimization
search or parameter update. The original MI adapter consumes the supplier's actual
LOG_RETURN and persists its full forecast/calibration/research triad in its own store.

The ACK is published only after fsync and actual owner readback. It binds capsule,
measurement, original stored DDO records, complete Optimization admission artifact,
MI durable ID and exact numerical calibration readback. CLOSED is the final Pending
commit after that ACK. Reload verifies those same original records and MI numbers;
a missing numeric record or altered ACK never becomes a successful ingest. Seven
interrupted handoff boundaries replay idempotently. Sample count one describes one
job within its pinned retention namespace, not global statistical independence
across accounts or unrelated datasets.

Market return, forecast error and Accounting PnL remain different quantities. The
same closes with a different decision mark and fees preserve LOG_RETURN and its
forecast error, while the original Accounting kernel's net PnL changes. There is
no REAL POSITION_LIFECYCLE, training, productive apply, quality claim, automatic
scheduler, trading effect or new operational authorization.
