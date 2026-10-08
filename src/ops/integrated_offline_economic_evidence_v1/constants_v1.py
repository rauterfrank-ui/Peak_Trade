"""Constants for integrated offline economic evidence contract v1 (Increment A).

Contract/verifier/discovery only. authority_effect=NONE.
"""

from __future__ import annotations

AUTHORITY_EFFECT_NONE = "NONE"
CAPABILITY_ID = "INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1"
PACKAGE_MARKER = "INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1=true"
PRODUCER_FAMILY = "ops.integrated_offline_economic_evidence_v1"

INTEGRATED_SCHEMA_ID = "ops.integrated_offline_economic_evidence.v1"
INTEGRATED_SCHEMA_VERSION = "v1"
INTEGRATED_ARTIFACT = "INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1.json"
INTEGRATED_VERIFIER_ID = "ops.integrated_offline_economic_evidence_verifier.v1"

ECONOMIC_METRICS_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_metrics_domain.v1"
WALK_FORWARD_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_walk_forward_domain.v1"
MONTE_CARLO_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_monte_carlo_domain.v1"
STRESS_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_stress_domain.v1"
DOMAIN_SCHEMA_VERSION = "v1"

ECONOMIC_METRICS_VERIFIER_ID = "ops.integrated_offline_economic_metrics_domain_verifier.v1"
WALK_FORWARD_VERIFIER_ID = "ops.integrated_offline_economic_walk_forward_domain_verifier.v1"
MONTE_CARLO_VERIFIER_ID = "ops.integrated_offline_economic_monte_carlo_domain_verifier.v1"
STRESS_VERIFIER_ID = "ops.integrated_offline_economic_stress_domain_verifier.v1"

CONFIG_RELPATH = "config/ops/integrated_offline_economic_evidence_v1.toml"
CONTRACT_DOC_RELPATH = "docs/ops/runbooks/INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1.md"

# Synthetic contract-test fixtures only; not productive discovery targets.
SYNTHETIC_FIXTURE_RELPATH_PREFIX = (
    "tests/fixtures/ops/integrated_offline_economic_evidence_contract_v1/"
)

FORBIDDEN_SUBSTITUTION_RELPATH_MARKERS: tuple[str, ...] = (
    "evidence/ops/current_6h_paper_shadow_soak_v1/",
    "integrated_paper_shadow_economic_bundle_head_bound_v1/",
    "peak_trade_robustness",
    "economic_viability_evidence_v1",
    "peak_trade_b10",
    "robustness_and_stress_v1",
)

FORBIDDEN_SUBSTITUTION_PRODUCER_MARKERS: tuple[str, ...] = (
    "backtest.economic_viability_evidence_v1",
    "peak_trade_robustness_and_stress_v1",
    "productive_wallclock",
    "integrated_paper_shadow_economic_evidence_bundle",
    "manual",
    "operator_asserted",
)

FORBIDDEN_EVIDENCE_CLASS_MARKERS: tuple[str, ...] = (
    "B10_RANKING_ROBUSTNESS_ONLY",
    "STEP29M_STATUS_ONLY",
    "WALLCLOCK_ANALYTICAL_OBSERVATION_ONLY",
    "V1_1_BUNDLE_ONLY",
    "MANUAL_AGGREGATE_BOOLEAN",
    "OFFLINE_COMPLETE_MANUAL",
)

ALLOWED_CONTRACT_TEST_PRODUCER_PREFIX = "ops.integrated_offline_economic_evidence_v1.contract_test."
