"""Multi-session natural-age typed volatility and actionable strata evidence v1."""

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.backward_compat_s03_v1 import (
    verify_old_s03_evidence_digests_unchanged_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.campaign_aggregation_v1 import (
    build_campaign_aggregation_v1,
    write_campaign_aggregation_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    HARD_STOP,
    PACKAGE_MARKER,
    READY_FOR_POLICY_ENFORCEMENT,
    READY_FOR_POLICY_IMPLEMENTATION,
    READY_FOR_POLICY_SELECTION,
    REVIEW_MODE_ID,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.early_age_density_v1 import (
    early_age_density_support_matrix_v1,
    plan_early_age_evidence_snapshots_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.full_alpha_counterfactual_harness_v1 import (
    run_full_alpha_counterfactual_comparison_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.opportunity_strata_v1 import (
    derive_opportunity_stratum_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.readiness_v1 import (
    evaluate_multi_session_typed_vol_readiness_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.typed_volatility_comparison_v1 import (
    build_typed_volatility_comparison_v1,
    materialize_fresh_estimate_from_mark_prices_v1,
)


def write_typed_s03_session_cycle_evidence_v1(*args, **kwargs):
    """Lazy export to avoid circular import with S03 package init."""
    from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.s03_typed_evidence_cycle_v1 import (
        write_typed_s03_session_cycle_evidence_v1 as _impl,
    )

    return _impl(*args, **kwargs)


__all__ = [
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "HARD_STOP",
    "PACKAGE_MARKER",
    "READY_FOR_POLICY_ENFORCEMENT",
    "READY_FOR_POLICY_IMPLEMENTATION",
    "READY_FOR_POLICY_SELECTION",
    "REVIEW_MODE_ID",
    "assert_architecture_guards_v1",
    "build_campaign_aggregation_v1",
    "build_typed_volatility_comparison_v1",
    "derive_opportunity_stratum_v1",
    "early_age_density_support_matrix_v1",
    "evaluate_multi_session_typed_vol_readiness_v1",
    "materialize_fresh_estimate_from_mark_prices_v1",
    "plan_early_age_evidence_snapshots_v1",
    "run_full_alpha_counterfactual_comparison_v1",
    "verify_old_s03_evidence_digests_unchanged_v1",
    "write_campaign_aggregation_v1",
    "write_typed_s03_session_cycle_evidence_v1",
]
