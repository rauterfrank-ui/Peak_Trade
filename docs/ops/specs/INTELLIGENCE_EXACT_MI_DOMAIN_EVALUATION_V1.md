---
docs_token: DOCS_TOKEN_INTELLIGENCE_EXACT_MI_DOMAIN_EVALUATION_V1
status: active
scope: Original MI evaluator preceded by exact numeric/source admission
---

# Exact MI domain evaluation

This explicit offline adapter reads the original MI store and its exact
forecast/measurement/readback attachments before invoking the existing
MarketIntelligenceEvaluatorV1 for baseline and candidate. It does not modify,
register or activate an evaluator, runner, domain plan or Governance receiver.

Both sides must have exactly one explicitly labeled MI replay entry, the exact
run identity, consistent context/replay bytes and the original replay digest.
Unlabeled or duplicate MI entries reject before the native first-match consumer.
Both complete bundles must match the original frozen source-generation/causal
bindings, source-derived time token, calibration readback and exact numbers.
A missing proof key cannot pass by omission. Native veto results remain intact.

The original GVEF replay codec forbids floats. Accordingly the numeric transport
contains a versioned exact JSON byte string and its SHA256. Original float values
are neither rounded nor coerced into different scientific quantities. The
adapter reads and compares the original numbers before passing the typed byte
transport to the existing evaluator. Global GVEF hashing rules are unchanged.

The result receipt retains both complete native evaluator returns plus separate
full numeric bindings and exact context/replay hashes. Its claim is explicitly
limited to original-MI replay mechanism and numeric integrity. The older native
SEALED label is retained as native output; it is not source authentication.
This is one domain, not GenericRunner/five-domain/whole-system acceptance.

Forecast quality, feature usefulness and economic quality remain NOT_PROVEN.
No user or caller flag can promote this mechanism to natural/economic acceptance.
Without a separately identified receiver/ACK contract, Governance disposition is
BLOCKED_NO_EXPLICIT_RECEIVER. Safety, Kill, Risk and trading/external boundaries
remain independent. No automatic apply or activation occurs.

Tests: [exact evaluation](../../../tests/learning/test_exact_intelligence_evaluation_v1.py),
[original domain evaluators](../../../tests/evaluation/golden_vectors/test_gvef_domain_evaluators_bwp456_v1.py).
