# Actual parameter sensitivity split observation transport — 2026-11-04

Source pin `77d5eae0d`. Follows the actual supplier study in Blueprint 79.
The existing sensitivity owner now has optional `split_result_observer`.
It transports each computed train/validation/OOS metrics map before it would
otherwise be discarded. No new statistics, policy, runner, storage SSOT or
canonical experiment identity is introduced. All persisted v1 result fields and
hash domains remain unchanged.

The callback receives read-only metadata and a read-only copy of the actual
metrics: grid parameter_set_id, split_name, result_ref, bar count and start/end,
cost/funding references. Actual stats owner defines units, annualization and
nonfinite outputs. Nothing is filled with zero or reinterpreted. Bar count is
not automatically a certified independent-sample count. Callers must preserve
frequency/metric semantics and bind their source identity separately.

Callbacks occur only after actual metric computation. A later split or observer
can fail after earlier results were observed. The existing full-grid failed-point
path retains that failure. Callers must join exact point/result refs to final
EVALUATED status and require the needed split observations before forming a
complete experiment. Callback presence and PIPELINE_PASS are not success proofs.
Failure to collect a split is not silently swallowed as successful collection.
No automatic Phase10/Meta invocation or persistence is added.

## Actual checks and numerical results

25 connected tests PASS (three new controls plus the existing 22). Real MV2
backtests produce six observations on two native-name grid points. Tests compare
observations with actual stats-owner outputs, reject writes to metadata/metrics,
check chronological refs/counts, and preserve nonfinite metric values. The short
fixture's failed points emit no fabricated metrics. A collector that fails at
validation leaves two partial training observations and two FAILED points, no
complete successful experiment.

A separate actual observed run uses exactly the previously recorded 768-bar
inputs/configuration/data digest. Its complete serialized grid output is equal
to the pre-change full record, including digests. Six split outputs are retained.
For native slow 50: train Sharpe 3.566909498529816, validation -1.4124758175235277,
OOS 4.8937003830724946. For slow 100: train 3.451807015686721, validation
-6.754628043053148, OOS 4.8937003830724946. These are actual hourly supplier values
from controlled simulator data, not invented train/test flags or natural-market
proof. Equal OOS outputs do not erase the measured validation difference.

[Contract](../../specs/PARAMETER_SENSITIVITY_SPLIT_OBSERVATION_TRANSPORT_V1.md),
[captured measurements](captured_split_results.json), [complete before](result_before.json),
[complete with observer](result_with_observer.json), [original owner](owner_before.py.txt),
[patch](change.diff), [test XML](tests.xml), [receipt and checks](receipt.json).
Raw supplier nonfinite values are represented with explicit evidence-only status
markers for valid JSON; the runtime port preserves them unchanged. Prior sizing,
funding, CRS, frequency/CAGR and core-attribution limitations remain. No productive
activation, historical identity migration or original-ledger mutation.
