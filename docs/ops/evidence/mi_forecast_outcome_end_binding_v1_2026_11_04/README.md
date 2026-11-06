# MI forecast target-end binding — 2026-11-04

Baseline 02b5fa9b3; join originated at 32171b35e (2026-09-26, Track D03).
The historical implementation and current specification define offline forecast
and calibration evidence with explicit horizons. ForecastEvidence requires
outcome_horizon_end_utc and creation before that end. The original/current join
checked only n_bars/bar_spec and presence of actual_outcome_ref, so a forecast
with another explicit end still returned JOINED. The orchestrator's n_bars-only
lookup made the omitted consumer check consequential for calibration.

The join now derives the actual target end with the existing forecast horizon
helper from the N_BARS horizon start and last bar close, then compares UTC
instants to the forecast target end. Mismatch rejects before calibration.
Evaluation knowledge time may be later and is not substituted for horizon end.
Equivalent UTC precision is accepted. No supplier formula, numeric label,
forecast model, trading policy, or join output schema changes.

Five new cases: three failures before, all five PASS after. Connected MI/realized
behavior scope 27 PASS; downstream M4 optimization intake eight PASS. Full successful
join objects/digests for n=2/n=3 compare identical against the original function.
Original outcome observations remain unchanged.

This repairs explicit target-end identity only. N_BARS still measures first-to-last
bar close. Grid start is not measurement start; forecast_end equality does not
prove instrument/selection identity, forecast creation before the measured start,
source authenticity, or the provenance of separately supplied realized_direction.
The existing offline orchestrator still receives that label from its scenario;
no new automatic MI label or live adapter is introduced. U04/GAP-0370 remain
deferred and the original learning ledger is preserved.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[downstream](downstream.xml), [normal output comparison](normal_join_output_comparison.json).
