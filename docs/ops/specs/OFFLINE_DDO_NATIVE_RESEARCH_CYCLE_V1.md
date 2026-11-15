# Offline DDO and native research cycle

The entry point consumes a completed offline DDO plan and a bounded research
profile or request. It verifies the original DDO state and O4 measurement, exports
LearningEvidence and passes it to the canonical optimization intake. The intake
acknowledges evidence eligibility. The declaration supplies the strategy,
parameter regions, dataset and experimental context.

```bash
./scripts/pt scripts/ops/run_offline_ddo_learning_follow_up_v1.py \
  --root /absolute/offline-state --cycle case-2 research --plan-digest "$plan_digest" \
  --profile /absolute/profile.json --bars /absolute/bars.csv --config /absolute/resolved.json
```

Use `OfflineDdoResearchProfileV1` in the [research worker](../../../src/experiments/offline_ddo_research_cycle_v1.py).
A profile has the request fields except `learning_evidence_digest`. Set
`schema_version` to `offline_ddo_research_profile.v1` and supply `follow_up_times`
with `meta`, `search` and `measurement` in strictly increasing UTC order after
`times.evaluation`. The worker takes the learning digest and instrument from the
verified export, checks the declared instrument and recomputes the input hashes.
It saves the generated request with the profile digest and follow-up clocks before
measurement. Use a clean checkout and an isolated state root outside the repository.

For an explicitly bound two-trial request, use `--request`:

```bash
./scripts/pt scripts/ops/run_offline_ddo_learning_follow_up_v1.py \
  --root /absolute/offline-state --cycle case-2 export-evidence --plan-digest "$plan_digest"

./scripts/pt scripts/ops/run_offline_ddo_learning_follow_up_v1.py \
  --root /absolute/offline-state --cycle case-2 research --plan-digest "$plan_digest" \
  --request /absolute/request.json --bars /absolute/bars.csv --config /absolute/resolved.json
```

The first command returns the `content_hash` used as `learning_evidence_digest`
in the request. The request schema is
`OfflineDdoResearchRequestV1` in
[offline_ddo_research_cycle_v1.py](../../../src/experiments/offline_ddo_research_cycle_v1.py).

- Bind `instrument_id` to the canonical instrument in the exported outcome.
  Supply the source digests for the declared feature and strategy context.
- Supply finalized, timestamp-indexed bars for that instrument. The index is
  bar-open time, `is_final` is boolean and `bar_interval` declares the duration
  of one bar. `bars_known_at` is the declared UTC availability time of the
  complete dataset. Bind the loaded frame and resolved config with
  `native_research_input_hashes_v1`.
- The resolved strategy configuration supplies the reference parameters. Declare
  the first and next search axes, seed and explicit UTC clocks. The baseline
  search starts after the learning evidence was available and after the dataset
  was known. The next search starts after the first measurement and Meta step.
- Supply the observed gap dimensions and threshold-policy digest for the declared
  offline comparison context. Supply the protected digest baseline for the
  scoped GVEF replay. These are caller declarations and retain their provenance.

The worker persists the request and admission, measures the reference, and
runs up to one candidate per search. The first archived measurement feeds
both Meta and search coverage. Search records distinguish prior measured
coverage, failure dispositions and new proposals. Meta proposals influence
search priority when the canonical Meta policy emits them. The DDO outcome
remains lineage evidence. Native scores come from the supplied backtest data.

When both native measurements exist, GVEF retains both original numeric
packets and evaluates their join in the local self-learning domain. The GVEF
replay reference is the first native result. The backtest comparison
reference remains the measured configuration. The result keeps economic
qualification blocked and carries authority `NONE`.

In profile mode, the worker uses the verdict read from the persisted GVEF
receipt and records its follow-up decision under `follow-up-decisions` by receipt
ID. Mechanism `PASS` runs one further search with `next_axes`, a budget of one,
both archived measurements and the existing Meta and failure-memory policies.
The search can finish without a candidate. `BLOCKED` stops the search.
`INCOMPLETE` records a waiting decision and leaves the run open for a retry with
the same profile. A receipt that fails integrity verification stops the worker.
The follow-up and its measured artifact, when present, are returned under
`follow_up`. The economic verdict remains scoped to the evaluated pair.

Outputs are under the cycle directory inside `offline-ddo-research`. A retry
with identical bindings reads the original baseline, owner records and
receipts. A conflicting request for the same cycle is rejected. If either
search is exhausted, the result retains that disposition. An interrupted
native measurement whose original prepared request is missing stays fenced
by the native research owner.

## Recurring offline research

The [campaign command](../../../scripts/ops/run_recurrent_offline_research_v1.py)
performs one bounded tick. Schedule it with the host scheduler at the desired
interval. Each tick discovers finalized Paper archives and completed I17
follow-ups, checks their original evidence, and handles up to the configured
number of jobs. Each admitted learning digest gets one durable job and one
completion record. A retry uses the original paths, exact dataset and
configuration hashes, profile, original logical phase clocks, and selected
history. Blocked sources get a retry time.

The campaign file is local JSON. Set absolute canonical paths for `state`,
`paper_runs`, `shadow_runs`, and `shadow_follow_ups`. Set positive
`jobs_per_tick`, `retry_seconds`, and `history_jobs`. Map each canonical
instrument ID in `research_inputs` to a list of descriptors containing
`template`, `bars`, and `config` paths. Each template is an
`offline_research_input.v1` JSON object with `schema_version`,
`instrument_id`, `bars_csv_sha256`, `backtest_json_sha256`, and `profile`.
The profile uses the existing research profile fields. Set
`gap_dimensions` to an empty list and omit phase clocks. The tick supplies
phase clocks and the actual observed surface. New dataset versions have
distinct `bars_known_at` values. Keep previously selected files available
for restart. New jobs use the latest version already available at the tick.
With no eligible dataset, the source waits. The state is outside the repo
and source archives.

```bash
./scripts/pt scripts/ops/run_recurrent_offline_research_v1.py --campaign /absolute/campaign.json
```

- Paper uses the sealed original decision, fills and Accounting close. The
  learning horizon is `SIMULATED_POSITION_LIFECYCLE`. The research request
  retains net PnL as a decimal string in the original quote currency.
- Shadow verifies the original I17 archive, O4 archive and saved DDO state.
  The binding retains the Mark log return, start/end and bar count. The
  observation has no fills.
- The native provider measures the declared backtest CSV and config. A
  candidate inherits the learning digest as lineage. Meta reads prior
  measured packets of the same instrument and strategy version after the
  earlier jobs have completed. For an identical input descriptor and
  observation surface, the search counts already measured regions as
  covered, including receipts outside the current Meta window. A new
  dataset gets its own measurements.
- A Paper descriptor may supply `paper_fee_tolerance_bps`. The Reality Gap
  compares the backtest taker fee in bps with the original simulated fees
  divided by total simulated fill notional in the same quote currency.
  The comparison measures model parity. Without a comparable observation
  the gap step is `INCOMPLETE`.
- GVEF compares the two new native packets when both exist. Its mechanical
  verdict determines the bounded follow-up. Economic qualification and
  trading authority retain their existing owners. The campaign consumes
  saved observations and research datasets.

The saved Paper and I17 observations precede the new parameter candidate.
A candidate-specific Reality Gap requires a separate, later observation of
that candidate under a comparable measurement contract. The campaign records
exploratory feedback and leaves that comparative evidence open.

## Prospective candidate replay

The [candidate replay command](../../../scripts/ops/run_research_candidate_shadow_v1.py)
freezes both original numeric packets from a passing GVEF mechanism receipt.
It checks the strategy version, effective parameter values, original data
digest and resolved configuration of both packets before registering a
future UTC window. The first packet is the GVEF reference. The second is the
candidate under observation for this experiment. The later follow-up experiment
has its own identity.

```bash
./scripts/pt scripts/ops/run_research_candidate_shadow_v1.py --state /absolute/forward-state prepare \
  --campaign-state /absolute/campaign-state --learning-digest "$learning_digest" \
  --config /absolute/resolved.json --instrument-binding /absolute/instrument-binding.json \
  --start-utc "$window_start_utc" --hours 2
./scripts/pt scripts/ops/run_research_candidate_shadow_v1.py --state /absolute/forward-state observe
./scripts/pt scripts/ops/run_research_candidate_shadow_v1.py --state /absolute/forward-state verify
```

After the registered window closes, `observe` requests original finalized
hourly Last, Mark and Index candles and settled funding-rate history from
public OKX EEA endpoints. The original response bytes, endpoint, query and
receipt time are retained. Both profiles consume the same complete window.
The earlier warmup initializes each replay's simulated state and the existing
hourly research volatility feature. The score starts from the simulated equity
at the window boundary and uses candle-close timestamps. The funding series is
a market context input dated by the funding event. The replay result reports
engine equity before verified funding cashflows, with the execution cost model
from the original experiment, including the engine's closing convention.

This is a forward replay on newly captured market inputs. It records the actual
parameters consumed by the replay, the Master V2 engine signals and the
simulated equity series. The observations needed for an I17 candidate-specific
Reality Gap include which configuration the I17 decision producer actually used
and an independent measurement of the same metric. The replay receipt carries
`reality_gap_status=INCOMPLETE`, `economic_qualification_status=BLOCKED`, and
authority `NONE`. It has no promotion or apply consumer.

### Draft for an economic comparison

The [original self-learning master](../evidence/self_learning_original_layers_restoration_v1_2026_11_04/originals/self_learning_master_core_bound.original.txt)
specifies the sequence from candidate to Shadow evidence, Reality Gap,
research memory and the next hypothesis. GVEF binds the evidence for an
evaluation. The economic judgement needs a versioned owner policy.

The proposed primary metric is net return on beginning equity, measured for both
profiles over the same independent observation horizon. Use fees and slippage
from the measurement's accounting basis and reconcile funding against applied
position quantities and event times. Count each cost once. Specify the position
state at both boundaries, the settlement and price basis, and the unit. Pair the
candidate and reference observations by window and use the difference in returns.
Keep drawdown, sample sizes and an
uncertainty estimate with that difference. A two-hour observation can test the
data flow. The responsible owner must ratify the evaluation horizon, required
sample size, uncertainty method and pass thresholds before a quality claim.
Incomplete or incomparable evidence leaves the verdict `BLOCKED`.

## Historical I17 candidate comparison

The [I17 comparison command](../../../scripts/ops/run_i17_candidate_comparison_v1.py)
revalidates the frozen GVEF pair and the original sealed I17 decision and
market ledgers. It runs the existing I17 observation bridge twice, starting
each profile in its own local state. The strategy registry in both runs
contains the same canonical `ma_crossover` entry. Both runs use the same
recorded Mark observations, original decision times and I17 safety inputs.
The market observation acceptor evaluates the archived venue event time and
Mark for the same instrument in both arms. A repeated event with a new receive
time does not advance the market observation epoch. The direction confirmation
owner consumes this accepted observation through the integrated replay and
retains its own Long and Short progress separately for each profile.

```bash
./scripts/pt scripts/ops/run_i17_candidate_comparison_v1.py \
  --state /absolute/i17-comparison --pair-plan /absolute/forward-state/plan.json \
  --campaign-state /absolute/campaign-state --base-config /absolute/resolved.json \
  --i17-evidence /absolute/qualified-i17/evidence --capture-public-last
```

The optional capture performs one public OKX EEA request for finalized hourly
Last candles and retains the original response and capture times. Replace
`--capture-public-last` with `--verify` to recompute the result from the saved
inputs. For each cycle, the MA uses only candles that had closed by the
original decision time. The hourly candle index and I17 decision epoch are
different coordinates. The receipt records both, the market observation
epoch and classification, directional confirmation progress, and the strategy
parameter and signal digests. It records the actual Suitability output when
that owner is reached, the decision reasons and the Double Play outcome. The bridge reads the same existing governed parameter
seam for both arms. The comparison carries authority `NONE`.

The hourly Last data was retrieved retrospectively. This fixture shows
historical decision behavior under the specified profiles. A prospective
I17 observation requires the profiles and candle availability to be bound
before the decisions under study, followed by independent, comparable
measurements for any Reality Gap.

### I17 decision-time input preflight

The same command accepts `--decision-time-last-captures` in place of
`--capture-public-last`. Supply a separate sealed JSON archive with schema
`i17_decision_time_last_captures.v1`, the frozen `plan_digest`, the
`original_i17_manifest_sha256` and an ordered `captures` array. Each entry
keeps the request, raw response, response hash, and request and receipt times
in the Last-candle archive format. Use captures that extend a contiguous
prefix of finalized Last hours. Earlier warmup bars must agree where they
overlap.

Both profiles and their research input must be known at preregistration
before the window opens. The I17 mark archive must lie inside that window.
Each decision uses the latest finalized hour from the captures received by
its own decision time. While a just-closed candle is in transit, both arms
continue with the previous available hour. The preflight stops if the first
decision has no available warmup. Each cycle records the selected close time,
receipt time and capture digest along with the consumed strategy material.
`--verify` replays the same inputs and checks the stored result.

The Last-candle capture entry point is `capture_decision_time_last_v1`.
It takes an isolated archive, the frozen plan, the intended I17
preregistration scope digest, an explicit transport and a UTC clock. It
stamps the request and receipt around the transport call, validates the
finalized OHLCV and both MA warmups, and stores one immutable response per
hour. A repeated request for that hour reads the saved response.
`seal_decision_time_last_v1` checks the original I17 manifest and the scope
bound by its preregistration, then writes the archive consumed by
`--decision-time-last-captures`. The comparison verifies the scope again.

This mode reads archived evidence offline and emits
`I17_DECISION_TIME_OFFLINE_PREFLIGHT` with authority `NONE`.

### I17 host comparison

An I17 host can receive an explicit `I17CandidateHostObservationV1` bound to
the frozen plan and its local Last-capture journal. The preregistration's
strategy components must carry the plan digest produced by
`candidate_plan_component_v1`. The existing preregistration scope digest binds
that identity before authorization consumption. A mismatched plan or a
candidate preregistration without its observer stops at preflight.

The observer consumes the host's Mark event and natural receipt time. It
reads the scoped journal and stamps its own paired decision cutoff. Both
profiles then use the latest available finalized Last prefix. The canonical
market observation acceptor handles event identity, and each arm retains its
own direction confirmation and simulation state. The MA value enters
Suitability. The receipt records that owner's actual response when reached
and the subsequent Double Play outcome. Each paired receipt in the bridge
cycle ledger references the original host decision, the original Mark clocks
and the Last close and receipt clocks.

Missing initial Last evidence marks the candidate comparison failed for that
session. The ordinary Shadow observation continues through its owners. An
independent venue observation still requires a session-bound operator GO and
an approved public Last capture source. The comparison carries authority
`NONE`. Economic qualification also requires a comparable measurement.
