"""Platform-unified native vs candidate baseline evidence v1 (Concept v3.2 D26).

Read-only classification and composition over existing CURRENT producers.
Does not confer trading, promotion, optimization productive, or external authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    BASELINE_CANDIDATE_ID,
    COUNTERFACTUAL_ONLY,
    NON_AUTHORITY_SCOPE,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    SCHEMA_VERSION as OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    validate_optimization_experiment_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    validate_counterfactual_record_v0,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    EVIDENCE_SCHEMA_VERSION as CANONICAL_DECISION_EVIDENCE_SCHEMA_VERSION,
    CanonicalTradingDecisionEvidenceV1,
)
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER,
)

SCHEMA_VERSION: Final[str] = "platform_unified_native_vs_candidate_baseline_evidence_v1"
WORKPACKAGE_ID: Final[str] = (
    "V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d26_platform_unified_native_vs_candidate_baseline_evidence_closure_v1_decision_v1.json"
)

NATIVE_PRODUCER_OWNER: Final[str] = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
NATIVE_EVIDENCE_ADAPTER: Final[str] = (
    "src.governance.integrated_replay_native_baseline_evidence_adapter_v1."
    "bind_integrated_replay_native_baseline_classification_v1"
)
F1_CANDIDATE_ADAPTER: Final[str] = (
    "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1."
    "baseline_evidence_classification_adapter_v1."
    "bind_f1_parameter_research_candidate_baseline_classification_v1"
)
COMPARISON_JOIN_OWNER: Final[str] = (
    "src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1."
    "derive_comparison_context_identity_v1"
)

CURRENT_MV2_DP_DECISION_SSOT: Final[str] = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)

AUTHORITY_EFFECT: Final[str] = "NONE"
RUNTIME_EFFECT: Final[str] = "NONE"
PROMOTION_AUTHORITY: Final[str] = "NONE"
LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
P5_AUTHORITY_CUTOVER_AUTHORIZED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
NEW_AUTHORITY_CREATED: Final[bool] = False


class InfluenceClassificationV1(str, Enum):
    NATIVE_BASELINE = "NATIVE_BASELINE"
    CANDIDATE_OR_COUNTERFACTUAL = "CANDIDATE_OR_COUNTERFACTUAL"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


class PlatformUnifiedBaselineEvidenceError(ValueError):
    """Fail-closed D26 classification error."""


@dataclass(frozen=True, slots=True)
class PlatformUnifiedBaselineEvidenceRecordV1:
    schema_version: str
    record_id: str
    influence_classification: InfluenceClassificationV1
    baseline_reference_identity: str
    baseline_provenance: Mapping[str, Any]
    native_decision_outcome_ref: str | None
    candidate_identity: str | None
    influence_provenance: Mapping[str, Any] | None
    comparison_context_identity: str | None
    source_kind: str
    producer_owner: str
    authority_effect: str
    runtime_effect: str
    promotion_authority: str
    fail_closed_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "baseline_provenance": dict(self.baseline_provenance),
            "baseline_reference_identity": self.baseline_reference_identity,
            "candidate_identity": self.candidate_identity,
            "comparison_context_identity": self.comparison_context_identity,
            "fail_closed_reasons": list(self.fail_closed_reasons),
            "influence_classification": self.influence_classification.value,
            "influence_provenance": None
            if self.influence_provenance is None
            else dict(self.influence_provenance),
            "native_decision_outcome_ref": self.native_decision_outcome_ref,
            "producer_owner": self.producer_owner,
            "promotion_authority": self.promotion_authority,
            "record_id": self.record_id,
            "runtime_effect": self.runtime_effect,
            "schema_version": self.schema_version,
            "source_kind": self.source_kind,
        }


def derive_baseline_reference_identity_v1(
    *,
    decision_id: str,
    replay_id: str,
    semantic_digest: str,
) -> str:
    if not decision_id or not replay_id:
        raise PlatformUnifiedBaselineEvidenceError("BASELINE_REFERENCE_IDENTITY_INPUT_MISSING")
    if semantic_digest and not is_valid_sha256_hex(semantic_digest):
        raise PlatformUnifiedBaselineEvidenceError("BASELINE_SEMANTIC_DIGEST_INVALID")
    body = {
        "decision_id": str(decision_id),
        "digest_domain": f"{SCHEMA_VERSION}.baseline_reference_identity",
        "replay_id": str(replay_id),
        "semantic_digest": str(semantic_digest or ""),
    }
    return compute_content_sha256(body)


def derive_comparison_context_identity_v1(
    *,
    baseline_reference_identity: str,
    candidate_record_id: str,
) -> str:
    if not is_valid_sha256_hex(baseline_reference_identity):
        raise PlatformUnifiedBaselineEvidenceError("BASELINE_REFERENCE_IDENTITY_INVALID")
    if not candidate_record_id:
        raise PlatformUnifiedBaselineEvidenceError("CANDIDATE_RECORD_ID_MISSING")
    return compute_content_sha256(
        {
            "baseline_reference_identity": baseline_reference_identity,
            "candidate_record_id": candidate_record_id,
            "digest_domain": f"{SCHEMA_VERSION}.comparison_context_identity",
        }
    )


def _record_id_from_body(body: Mapping[str, Any]) -> str:
    digest = compute_content_sha256(body)
    return f"pub.v1.{digest[:48]}"


def _native_provenance_from_decision_evidence(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> Mapping[str, Any]:
    return MappingProxyType(
        {
            "decision_id": evidence.decision_id,
            "replay_id": evidence.replay_id,
            "semantic_digest": evidence.semantic_digest,
            "input_digest": evidence.input_digest,
            "implementation_digest": evidence.implementation_digest,
            "config_digest": evidence.config_digest,
            "evidence_schema_version": evidence.evidence_schema_version,
            "producer_owner": NATIVE_PRODUCER_OWNER,
            "decision_ssot": CURRENT_MV2_DP_DECISION_SSOT,
        }
    )


def classify_canonical_trading_decision_evidence_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    influence_markers: Mapping[str, Any] | None = None,
) -> PlatformUnifiedBaselineEvidenceRecordV1:
    """Native CURRENT integrated replay decision evidence → NATIVE_BASELINE when clean."""
    markers = dict(influence_markers or {})
    fail_reasons: list[str] = []

    if evidence.evidence_schema_version != CANONICAL_DECISION_EVIDENCE_SCHEMA_VERSION:
        fail_reasons.append("EVIDENCE_SCHEMA_VERSION_MISMATCH")

    forbidden_marker_keys = (
        "candidate_id",
        "counterfactual_only",
        "optimization_experiment_record_id",
        "parameter_research_execution_id",
        "research_candidate_influence",
    )
    for key in forbidden_marker_keys:
        if key in markers and markers[key] not in (None, "", False):
            fail_reasons.append(f"FORBIDDEN_INFLUENCE_MARKER:{key}")

    if str(evidence.authority_effect or "") not in ("", "NONE"):
        fail_reasons.append("AUTHORITY_EFFECT_NOT_NONE")

    if fail_reasons:
        body = {
            "decision_id": evidence.decision_id,
            "fail_reasons": fail_reasons,
            "source_kind": "canonical_trading_decision_evidence_v1",
        }
        return PlatformUnifiedBaselineEvidenceRecordV1(
            schema_version=SCHEMA_VERSION,
            record_id=_record_id_from_body(body),
            influence_classification=InfluenceClassificationV1.INVALID,
            baseline_reference_identity="",
            baseline_provenance=MappingProxyType({}),
            native_decision_outcome_ref=None,
            candidate_identity=None,
            influence_provenance=None,
            comparison_context_identity=None,
            source_kind="canonical_trading_decision_evidence_v1",
            producer_owner=NATIVE_PRODUCER_OWNER,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            promotion_authority=PROMOTION_AUTHORITY,
            fail_closed_reasons=tuple(fail_reasons),
        )

    baseline_ref = derive_baseline_reference_identity_v1(
        decision_id=evidence.decision_id,
        replay_id=evidence.replay_id,
        semantic_digest=evidence.semantic_digest,
    )
    provenance = _native_provenance_from_decision_evidence(evidence)
    body = {
        "baseline_reference_identity": baseline_ref,
        "classification": InfluenceClassificationV1.NATIVE_BASELINE.value,
        "source_kind": "canonical_trading_decision_evidence_v1",
    }
    return PlatformUnifiedBaselineEvidenceRecordV1(
        schema_version=SCHEMA_VERSION,
        record_id=_record_id_from_body(body),
        influence_classification=InfluenceClassificationV1.NATIVE_BASELINE,
        baseline_reference_identity=baseline_ref,
        baseline_provenance=provenance,
        native_decision_outcome_ref=evidence.decision_id,
        candidate_identity=None,
        influence_provenance=None,
        comparison_context_identity=None,
        source_kind="canonical_trading_decision_evidence_v1",
        producer_owner=NATIVE_PRODUCER_OWNER,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        promotion_authority=PROMOTION_AUTHORITY,
        fail_closed_reasons=(),
    )


def classify_f1_parameter_research_candidate_result_v1(
    *,
    candidate_result: Mapping[str, Any],
    baseline_reference: Mapping[str, Any],
) -> PlatformUnifiedBaselineEvidenceRecordV1:
    """F1 max-age parameter research candidate evaluation → never NATIVE_BASELINE."""
    candidate_id = str(candidate_result.get("candidate_id") or "")
    if not candidate_id:
        return _unknown_record(
            source_kind="f1_max_age_parameter_research_candidate_result_v1",
            producer_owner=F1_CANDIDATE_ADAPTER,
            fail_reasons=("CANDIDATE_ID_MISSING",),
        )

    decision_id = str(baseline_reference.get("decision_id") or "")
    replay_id = str(baseline_reference.get("replay_id") or "")
    semantic_digest = str(baseline_reference.get("semantic_digest") or "")
    if not decision_id or not replay_id:
        return _unknown_record(
            source_kind="f1_max_age_parameter_research_candidate_result_v1",
            producer_owner=F1_CANDIDATE_ADAPTER,
            fail_reasons=("BASELINE_REFERENCE_INCOMPLETE",),
        )

    baseline_ref = derive_baseline_reference_identity_v1(
        decision_id=decision_id,
        replay_id=replay_id,
        semantic_digest=semantic_digest,
    )
    influence = MappingProxyType(
        {
            "candidate_id": candidate_id,
            "counterfactual_only": bool(
                candidate_result.get("counterfactual_only", COUNTERFACTUAL_ONLY)
            ),
            "non_authority_scope": NON_AUTHORITY_SCOPE,
            "parameter_influence": "canonical_volatility_numeric_max_age_seconds",
            "f1_baseline_candidate_slot": BASELINE_CANDIDATE_ID,
            "research_execution_scope": "F1_MAX_AGE_PARAMETER_RESEARCH",
        }
    )
    body = {
        "baseline_reference_identity": baseline_ref,
        "candidate_id": candidate_id,
        "classification": InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL.value,
        "source_kind": "f1_max_age_parameter_research_candidate_result_v1",
    }
    record_id = _record_id_from_body(body)
    comparison_id = derive_comparison_context_identity_v1(
        baseline_reference_identity=baseline_ref,
        candidate_record_id=record_id,
    )
    return PlatformUnifiedBaselineEvidenceRecordV1(
        schema_version=SCHEMA_VERSION,
        record_id=record_id,
        influence_classification=InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL,
        baseline_reference_identity=baseline_ref,
        baseline_provenance=MappingProxyType(
            {
                "decision_id": decision_id,
                "replay_id": replay_id,
                "semantic_digest": semantic_digest,
                "reference_kind": "INTEGRATED_REPLAY_NATIVE_BASELINE",
            }
        ),
        native_decision_outcome_ref=decision_id,
        candidate_identity=candidate_id,
        influence_provenance=influence,
        comparison_context_identity=comparison_id,
        source_kind="f1_max_age_parameter_research_candidate_result_v1",
        producer_owner=F1_CANDIDATE_ADAPTER,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        promotion_authority=PROMOTION_AUTHORITY,
        fail_closed_reasons=(),
    )


def classify_ddo_counterfactual_record_v1(
    *,
    counterfactual_record: Mapping[str, Any],
    baseline_reference: Mapping[str, Any],
) -> PlatformUnifiedBaselineEvidenceRecordV1:
    try:
        validated = validate_counterfactual_record_v0(counterfactual_record)
    except Exception:
        return _unknown_record(
            source_kind="ddo_counterfactual_record_v0",
            producer_owner="src.learning.deterministic_decision_outcome_v0.evaluation_records_v0",
            fail_reasons=("DDO_COUNTERFACTUAL_VALIDATION_FAILED",),
        )

    decision_id = str(baseline_reference.get("decision_id") or "")
    replay_id = str(baseline_reference.get("replay_id") or "")
    semantic_digest = str(baseline_reference.get("semantic_digest") or "")
    if not decision_id:
        decision_id = str(validated.get("decision_event_ref") or "")
    if not decision_id or not replay_id:
        return _unknown_record(
            source_kind="ddo_counterfactual_record_v0",
            producer_owner="src.learning.deterministic_decision_outcome_v0.evaluation_records_v0",
            fail_reasons=("BASELINE_REFERENCE_JOIN_MISSING",),
        )

    baseline_ref = derive_baseline_reference_identity_v1(
        decision_id=decision_id,
        replay_id=replay_id,
        semantic_digest=semantic_digest,
    )
    cf_record_id = str(validated.get("record_id") or "")
    influence = MappingProxyType(
        {
            "counterfactual_admissibility": validated.get("counterfactual_admissibility"),
            "decision_event_ref": validated.get("decision_event_ref"),
            "ddo_record_id": cf_record_id,
            "research_influence": "DDO_COUNTERFACTUAL_EVALUATION",
        }
    )
    body = {
        "baseline_reference_identity": baseline_ref,
        "ddo_record_id": cf_record_id,
        "source_kind": "ddo_counterfactual_record_v0",
    }
    record_id = _record_id_from_body(body)
    comparison_id = derive_comparison_context_identity_v1(
        baseline_reference_identity=baseline_ref,
        candidate_record_id=record_id,
    )
    return PlatformUnifiedBaselineEvidenceRecordV1(
        schema_version=SCHEMA_VERSION,
        record_id=record_id,
        influence_classification=InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL,
        baseline_reference_identity=baseline_ref,
        baseline_provenance=MappingProxyType(
            {
                "decision_id": decision_id,
                "replay_id": replay_id,
                "semantic_digest": semantic_digest,
                "reference_kind": "INTEGRATED_REPLAY_OR_DECISION_EVENT",
            }
        ),
        native_decision_outcome_ref=decision_id,
        candidate_identity=cf_record_id,
        influence_provenance=influence,
        comparison_context_identity=comparison_id,
        source_kind="ddo_counterfactual_record_v0",
        producer_owner="src.learning.deterministic_decision_outcome_v0.evaluation_records_v0",
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        promotion_authority=PROMOTION_AUTHORITY,
        fail_closed_reasons=(),
    )


def classify_optimization_experiment_evidence_v1(
    evidence: Mapping[str, Any],
    *,
    baseline_reference: Mapping[str, Any],
) -> PlatformUnifiedBaselineEvidenceRecordV1:
    try:
        validated = validate_optimization_experiment_evidence_v1(evidence)
    except Exception:
        return _unknown_record(
            source_kind="canonical_optimization_experiment_evidence_v1",
            producer_owner="src.experiments.canonical_optimization_experiment_evidence_v1",
            fail_reasons=("OPTIMIZATION_EXPERIMENT_EVIDENCE_INVALID",),
        )

    decision_id = str(baseline_reference.get("decision_id") or "")
    replay_id = str(baseline_reference.get("replay_id") or "")
    semantic_digest = str(baseline_reference.get("semantic_digest") or "")
    if not decision_id or not replay_id:
        learning_digest = str(validated.get("learning_evidence_digest") or "")
        if not is_valid_sha256_hex(learning_digest):
            return _unknown_record(
                source_kind="canonical_optimization_experiment_evidence_v1",
                producer_owner="src.experiments.canonical_optimization_experiment_evidence_v1",
                fail_reasons=("BASELINE_REFERENCE_AND_LEARNING_DIGEST_MISSING",),
            )
        baseline_ref = learning_digest
        baseline_prov: Mapping[str, Any] = MappingProxyType(
            {
                "learning_evidence_digest": learning_digest,
                "reference_kind": "LEARNING_EVIDENCE_EXPORT_LINEAGE",
            }
        )
        native_ref = None
    else:
        baseline_ref = derive_baseline_reference_identity_v1(
            decision_id=decision_id,
            replay_id=replay_id,
            semantic_digest=semantic_digest,
        )
        baseline_prov = MappingProxyType(
            {
                "decision_id": decision_id,
                "replay_id": replay_id,
                "semantic_digest": semantic_digest,
                "reference_kind": "INTEGRATED_REPLAY_NATIVE_BASELINE",
            }
        )
        native_ref = decision_id

    record_id = str(validated.get("record_id") or "")
    candidate_identity = str(validated.get("search_identity") or record_id)
    influence = MappingProxyType(
        {
            "optimization_experiment_record_id": record_id,
            "plane_identity": validated.get("plane_identity"),
            "universe_class": validated.get("universe_class"),
            "research_influence": "OPTIMIZATION_EXPERIMENT_EVIDENCE",
            "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        }
    )
    comparison_id = derive_comparison_context_identity_v1(
        baseline_reference_identity=baseline_ref,
        candidate_record_id=record_id or candidate_identity,
    )
    body = {
        "baseline_reference_identity": baseline_ref,
        "record_id": record_id,
        "source_kind": "canonical_optimization_experiment_evidence_v1",
    }
    return PlatformUnifiedBaselineEvidenceRecordV1(
        schema_version=SCHEMA_VERSION,
        record_id=_record_id_from_body(body),
        influence_classification=InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL,
        baseline_reference_identity=baseline_ref,
        baseline_provenance=baseline_prov,
        native_decision_outcome_ref=native_ref,
        candidate_identity=candidate_identity,
        influence_provenance=influence,
        comparison_context_identity=comparison_id,
        source_kind="canonical_optimization_experiment_evidence_v1",
        producer_owner="src.experiments.canonical_optimization_experiment_evidence_v1",
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        promotion_authority=PROMOTION_AUTHORITY,
        fail_closed_reasons=(),
    )


def _unknown_record(
    *,
    source_kind: str,
    producer_owner: str,
    fail_reasons: tuple[str, ...],
) -> PlatformUnifiedBaselineEvidenceRecordV1:
    body = {"fail_reasons": fail_reasons, "source_kind": source_kind}
    return PlatformUnifiedBaselineEvidenceRecordV1(
        schema_version=SCHEMA_VERSION,
        record_id=_record_id_from_body(body),
        influence_classification=InfluenceClassificationV1.UNKNOWN,
        baseline_reference_identity="",
        baseline_provenance=MappingProxyType({}),
        native_decision_outcome_ref=None,
        candidate_identity=None,
        influence_provenance=None,
        comparison_context_identity=None,
        source_kind=source_kind,
        producer_owner=producer_owner,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        promotion_authority=PROMOTION_AUTHORITY,
        fail_closed_reasons=fail_reasons,
    )


def assert_candidate_never_native_baseline_v1(
    record: PlatformUnifiedBaselineEvidenceRecordV1,
) -> None:
    if record.influence_classification == InfluenceClassificationV1.NATIVE_BASELINE:
        if record.candidate_identity or record.influence_provenance:
            raise PlatformUnifiedBaselineEvidenceError("CANDIDATE_MARKERS_ON_NATIVE_BASELINE")


def assert_baseline_reference_immutable_v1(
    *,
    baseline_record: PlatformUnifiedBaselineEvidenceRecordV1,
    candidate_record: PlatformUnifiedBaselineEvidenceRecordV1,
) -> None:
    if baseline_record.influence_classification != InfluenceClassificationV1.NATIVE_BASELINE:
        raise PlatformUnifiedBaselineEvidenceError("BASELINE_RECORD_NOT_NATIVE")
    if candidate_record.baseline_reference_identity != baseline_record.baseline_reference_identity:
        raise PlatformUnifiedBaselineEvidenceError("CANDIDATE_BASELINE_REFERENCE_MISMATCH")
    if (
        candidate_record.influence_classification
        != InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL
    ):
        raise PlatformUnifiedBaselineEvidenceError("CANDIDATE_CLASSIFICATION_REQUIRED")


def assert_no_trading_decision_authority_from_evidence_v1() -> None:
    if TRADING_DECISION_AUTHORITY_OWNER != CURRENT_MV2_DP_DECISION_SSOT:
        raise PlatformUnifiedBaselineEvidenceError("TRADING_DECISION_SSOT_DRIFT")
    if OPTIMIZATION_CORE_MUTATION_AUTHORITY != "NONE":
        raise PlatformUnifiedBaselineEvidenceError("OPTIMIZATION_MUTATION_NOT_NONE")


def prove_d26_platform_unified_baseline_evidence_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / "src/governance/platform_unified_native_vs_candidate_baseline_evidence_v1.py",
        root / "src/governance/integrated_replay_native_baseline_evidence_adapter_v1.py",
        root
        / "src/research/canonical_volatility_numeric_max_age_parameter_research_execution_v1"
        / "baseline_evidence_classification_adapter_v1.py",
        root / "tests/governance/test_platform_unified_native_vs_candidate_baseline_evidence_v1.py",
    )
    if not all(path.is_file() for path in required):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    return bool(decision.get("d26_implemented")) and decision.get("d26_status") == "PROVEN_CURRENT"


__all__ = [
    "AUTHORITY_EFFECT",
    "COMPARISON_JOIN_OWNER",
    "CURRENT_MV2_DP_DECISION_SSOT",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "F1_CANDIDATE_ADAPTER",
    "InfluenceClassificationV1",
    "LEARNING_PRODUCTIVE_AUTHORITY",
    "NATIVE_EVIDENCE_ADAPTER",
    "NATIVE_PRODUCER_OWNER",
    "NEW_AUTHORITY_CREATED",
    "NORMATIVE_SPEC",
    "OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION",
    "P5_AUTHORITY_CUTOVER_AUTHORIZED",
    "PlatformUnifiedBaselineEvidenceError",
    "PlatformUnifiedBaselineEvidenceRecordV1",
    "PROMOTION_AUTHORITY",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "assert_baseline_reference_immutable_v1",
    "assert_candidate_never_native_baseline_v1",
    "assert_no_trading_decision_authority_from_evidence_v1",
    "classify_canonical_trading_decision_evidence_v1",
    "classify_ddo_counterfactual_record_v1",
    "classify_f1_parameter_research_candidate_result_v1",
    "classify_optimization_experiment_evidence_v1",
    "derive_baseline_reference_identity_v1",
    "derive_comparison_context_identity_v1",
    "prove_d26_platform_unified_baseline_evidence_v1",
]
