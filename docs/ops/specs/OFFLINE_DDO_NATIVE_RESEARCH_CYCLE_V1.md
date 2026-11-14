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
