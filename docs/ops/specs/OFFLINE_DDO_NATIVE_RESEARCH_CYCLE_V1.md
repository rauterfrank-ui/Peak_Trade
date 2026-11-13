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
