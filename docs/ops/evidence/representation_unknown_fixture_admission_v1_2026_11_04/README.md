# Representation unknown fixture admission — 2026-11-04

Baseline 2858f6079; Phase-24 origin 90183c9be (2026-09-26). The normative contract
and implementation establish a bounded fixture evaluation path. The upstream plan
can contain arbitrary pattern_ref text; its integrity validation proves identity,
not a numeric evaluation. The evaluator formerly returned RESEARCH_EVIDENCE_SUPPORTED
for every label not matched by a rejection branch, including nonfixture references
and typos.

Success now requires one of the three existing declared success fixture labels:
feature usefulness, regime conditionality or context family usefulness. Existing
typed rejection/fail-closed branches remain. An unrecognized remaining label raises
the existing LearningRepresentationOfflineEvaluationError with
EVALUATION_FIXTURE_UNSUPPORTED before an evaluation result/next evidence is minted.
No new numerical evaluator, measured success, outcome class or authority is invented.

Three failures before; 27 connected tests PASS after, including plan, evaluator,
actual Loop-C wrapper and governance tests. Nine existing success/rejection fixture
outputs and digests compare fully identical against the original function. Upstream
factory default fixtures remain a fixture convenience, not measured natural evidence.
A real reference requires a real evaluator contract, not fallback fixture success.

The preceding Meta comparability review also confirms _as_candidate omits later
observed_surface; current predictive buckets use metric_name. This scoped source
observation does not by itself ratify equality or inequality across Shadow/Testnet/
Live values. Numeric units/source and target-surface compatibility remain separate;
no automatic surface adapter or new pooling rule was inferred.

No original-ledger/historical-record changes, activation, new agents, live/testnet
operation or push. U04/GAP-0370 remain deferred.

[Receipt](receipt.json), [before](before.xml), [after](after.xml),
[known fixture output comparison](known_fixture_output_comparison.json).
