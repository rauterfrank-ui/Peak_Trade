# Offline DDO and native research cycle

The entry point consumes a completed offline DDO plan and a separate bounded
research request. It verifies the original DDO state and O4 measurement, exports
LearningEvidence and passes it to the canonical optimization intake. The intake
acknowledges evidence eligibility. The explicit research request supplies the
strategy, parameter regions, dataset and experimental context.

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
Use a clean checkout and an isolated state root outside the repository.

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

Outputs are under the cycle directory inside `offline-ddo-research`. A retry
with identical bindings reads the original baseline, owner records and
receipts. A conflicting request for the same cycle is rejected. If either
search is exhausted, the result retains that disposition. An interrupted
native measurement whose original prepared request is missing stays fenced
by the native research owner.
