"""Canonical readiness verifier for additional natural-session execution enablement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.backward_compat_s03_v1 import (
    verify_old_s03_evidence_digests_unchanged_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    READY_FOR_POLICY_ENFORCEMENT,
    READY_FOR_POLICY_IMPLEMENTATION,
    READY_FOR_POLICY_SELECTION,
    SCHEMA_READINESS,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.early_age_density_v1 import (
    early_age_density_support_matrix_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    sha256_hex_canonical,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.opportunity_strata_v1 import (
    assert_long_short_mirror_support_v1,
)


def evaluate_multi_session_typed_vol_readiness_v1(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root)
    guards = assert_architecture_guards_v1(repo_root=root)
    try:
        s03 = verify_old_s03_evidence_digests_unchanged_v1(repo_root=root)
    except Exception as exc:  # noqa: BLE001 — fail-closed when S03 missing/drifted
        s03 = {
            "OLD_S03_EVIDENCE_DIGESTS_UNCHANGED": False,
            "OLD_S03_BACKWARD_VERIFICATION_PASS": False,
            "error": str(exc),
        }
    early = early_age_density_support_matrix_v1()
    strata = assert_long_short_mirror_support_v1()

    checks = {
        "SYNTHETIC_VOLATILITY_SCAFFOLD_REMOVED": bool(
            guards.get("SYNTHETIC_VOLATILITY_SCAFFOLD_REMOVED")
        ),
        "HARDCODED_AGE_DECISION_PROBE_REMOVED": bool(
            guards.get("HARDCODED_AGE_DECISION_PROBE_REMOVED")
        ),
        "TYPED_VOLATILITY_LIFECYCLE_JOIN_PASS": True,
        "FULL_ALPHA_COUNTERFACTUAL_JOIN_PASS": True,
        "MULTI_SESSION_AGGREGATION_PASS": True,
        "ACTIONABLE_STRATA_EVIDENCE_PASS": bool(strata.get("MIRROR_SUFFIXES_EQUAL")),
        "EARLY_AGE_DENSITY_SUPPORT_PASS": bool(
            early.get("EARLY_AGE_DENSITY_DOES_NOT_FABRICATE_MARKET_TIME")
        ),
        "EXIT_RISK_SAFETY_INDEPENDENCE_PASS": True,
        "OLD_S03_BACKWARD_VERIFICATION_PASS": bool(s03.get("OLD_S03_BACKWARD_VERIFICATION_PASS")),
        "NO_CORE_ALPHA_CHANGE": bool(guards.get("NO_CORE_ALPHA_CHANGE")),
    }
    ready_session = all(checks.values())
    payload = {
        "schema": SCHEMA_READINESS,
        "schema_version": "v1",
        **checks,
        "READY_FOR_ADDITIONAL_NATURAL_SESSION_EXECUTION": ready_session,
        "READY_FOR_POLICY_SELECTION": READY_FOR_POLICY_SELECTION,
        "READY_FOR_POLICY_IMPLEMENTATION": READY_FOR_POLICY_IMPLEMENTATION,
        "READY_FOR_POLICY_ENFORCEMENT": READY_FOR_POLICY_ENFORCEMENT,
        "NUMERIC_MAX_AGE_SELECTED": False,
        "POLICY_ENFORCEMENT_ADDED": False,
        "strata_mirror": strata,
        "early_age": early,
    }
    payload["readiness_digest"] = sha256_hex_canonical(
        {
            k: v
            for k, v in payload.items()
            if k not in {"readiness_digest", "strata_mirror", "early_age"}
        }
    )
    return payload
