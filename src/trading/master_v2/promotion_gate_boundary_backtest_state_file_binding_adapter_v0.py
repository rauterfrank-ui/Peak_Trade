# src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
Promotion Gate boundary semantics via the Surface M offline replay adapter.

Wiring-only parity slice — no runtime authority, no order effects, no promotion authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    PROMOTION_ECONOMIC_GATE_POLICY_VERSION,
)
from trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    PromotionGateBoundaryOfflineReplayBindingResultV0,
    PromotionGateBoundaryOfflineReplayContextV0,
    bind_promotion_gate_boundary_offline_replay_evidence_v0,
    promotion_gate_boundary_binding_non_authority_boundary_ok_v0,
)

PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.promotion_gate_boundary_backtest_state_file_binding_adapter_v0"
)
PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "promotion_gate_boundary_backtest_state_file_v0"
)


@dataclass(frozen=True)
class PromotionGateBacktestStateFileRecordV0:
    """Parsed Promotion Gate backtest state-file payload."""

    strategy_id: str
    strategy_version: str
    candidate_id: str
    economic_viability_evidence_ref: str
    economic_validity_status: str
    robustness_status: str
    data_admissibility_status: str
    evidence_admissibility_status: str
    policy_threshold_status: str
    walk_forward_status: str
    out_of_sample_status: str
    monte_carlo_status: str
    stress_status: str
    parameter_sensitivity_status: str
    reproducibility_status: str
    digest_binding_status: str
    manifest_binding_status: str
    safety_policy_status: str
    futures_only: bool
    bitcoin_direction_allowed: bool
    config_digest: str
    implementation_digest: str
    policy_digest: str
    evidence_manifest_digest: str
    economic_validity_proven: bool
    profitability_claim_allowed: bool
    promotion_basis_confidence_only: bool
    promotion_basis_in_sample_profit_only: bool
    zero_cost_evidence: bool
    raw_signal_evidence: bool
    manifest_verify_only: bool
    promotion_gate_owner_digest_ref: str
    state_file_digest_ref: str
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class PromotionGateBoundaryBacktestStateFileEvidenceV0:
    promotion_gate_boundary_backtest_state_file_bound: bool
    promotion_gate_semantics_bound: bool
    promotion_gate_semantics_represented_in_backtest: bool
    economic_validity_required_for_promotion_represented_in_backtest: bool
    robustness_required_for_promotion_represented_in_backtest: bool
    evidence_admissibility_required_for_promotion_represented_in_backtest: bool
    safety_policy_required_for_promotion_represented_in_backtest: bool
    no_promotion_from_confidence_only_represented_in_backtest: bool
    no_runtime_authority_from_promotion_represented_in_backtest: bool
    no_economic_claim_from_manifest_verify_alone_represented_in_backtest: bool
    raw_signal_evidence_not_promotion_admissible_represented_in_backtest: bool
    promotion_eligible: bool
    promotion_gate_owner_digest_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: PromotionGateBoundaryOfflineReplayBindingResultV0
    surface_m_adapter_owner_ref: str


def _canonical_payload_bytes(payload: Mapping[str, Any]) -> bytes:
    stripped = {k: v for k, v in payload.items() if k != "state_file_digest_ref"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_backtest_state_file_digest_v0(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_backtest_state_file_digest_from_payload_v0(payload: Mapping[str, Any]) -> str:
    return compute_backtest_state_file_digest_v0(_canonical_payload_bytes(payload))


def _require_text(raw: object, *, field_name: str) -> str:
    if raw is None or not str(raw).strip():
        raise ValueError(f"{field_name}_missing")
    return str(raw).strip()


def _require_status(raw: object, *, field_name: str) -> str:
    value = _require_text(raw, field_name=field_name)
    return value.upper()


def parse_promotion_gate_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> PromotionGateBacktestStateFileRecordV0:
    """Parse backtest Promotion Gate state file. Fail-closed on missing or invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("promotion_gate_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("promotion_gate_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("promotion_gate_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("promotion_gate_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("promotion_gate_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("promotion_gate_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if (
        schema_version
        and schema_version != PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION
    ):
        raise ValueError("promotion_gate_backtest_state_file_schema_version_mismatch")

    owner_ref = str(decoded.get("promotion_gate_owner_digest_ref", "")).strip()
    if not owner_ref:
        raise ValueError("promotion_gate_owner_digest_ref_missing")
    if owner_ref != PROMOTION_ECONOMIC_GATE_POLICY_VERSION:
        raise ValueError("promotion_gate_owner_digest_ref_mismatch")

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("promotion_gate_backtest_state_file_digest_mismatch")

    return PromotionGateBacktestStateFileRecordV0(
        strategy_id=_require_text(decoded.get("strategy_id"), field_name="strategy_id"),
        strategy_version=_require_text(
            decoded.get("strategy_version"),
            field_name="strategy_version",
        ),
        candidate_id=_require_text(decoded.get("candidate_id"), field_name="candidate_id"),
        economic_viability_evidence_ref=_require_text(
            decoded.get("economic_viability_evidence_ref"),
            field_name="economic_viability_evidence_ref",
        ),
        economic_validity_status=_require_status(
            decoded.get("economic_validity_status"),
            field_name="economic_validity_status",
        ),
        robustness_status=_require_status(
            decoded.get("robustness_status"),
            field_name="robustness_status",
        ),
        data_admissibility_status=_require_status(
            decoded.get("data_admissibility_status"),
            field_name="data_admissibility_status",
        ),
        evidence_admissibility_status=_require_status(
            decoded.get("evidence_admissibility_status"),
            field_name="evidence_admissibility_status",
        ),
        policy_threshold_status=_require_status(
            decoded.get("policy_threshold_status"),
            field_name="policy_threshold_status",
        ),
        walk_forward_status=_require_status(
            decoded.get("walk_forward_status"),
            field_name="walk_forward_status",
        ),
        out_of_sample_status=_require_status(
            decoded.get("out_of_sample_status"),
            field_name="out_of_sample_status",
        ),
        monte_carlo_status=_require_status(
            decoded.get("monte_carlo_status"),
            field_name="monte_carlo_status",
        ),
        stress_status=_require_status(
            decoded.get("stress_status"),
            field_name="stress_status",
        ),
        parameter_sensitivity_status=_require_status(
            decoded.get("parameter_sensitivity_status"),
            field_name="parameter_sensitivity_status",
        ),
        reproducibility_status=_require_status(
            decoded.get("reproducibility_status"),
            field_name="reproducibility_status",
        ),
        digest_binding_status=_require_status(
            decoded.get("digest_binding_status"),
            field_name="digest_binding_status",
        ),
        manifest_binding_status=_require_status(
            decoded.get("manifest_binding_status"),
            field_name="manifest_binding_status",
        ),
        safety_policy_status=_require_status(
            decoded.get("safety_policy_status"),
            field_name="safety_policy_status",
        ),
        futures_only=bool(decoded.get("futures_only", True)),
        bitcoin_direction_allowed=bool(decoded.get("bitcoin_direction_allowed", False)),
        config_digest=_require_text(decoded.get("config_digest"), field_name="config_digest"),
        implementation_digest=_require_text(
            decoded.get("implementation_digest"),
            field_name="implementation_digest",
        ),
        policy_digest=str(decoded.get("policy_digest", "")).strip(),
        evidence_manifest_digest=_require_text(
            decoded.get("evidence_manifest_digest"),
            field_name="evidence_manifest_digest",
        ),
        economic_validity_proven=bool(decoded.get("economic_validity_proven", False)),
        profitability_claim_allowed=bool(decoded.get("profitability_claim_allowed", False)),
        promotion_basis_confidence_only=bool(decoded.get("promotion_basis_confidence_only", False)),
        promotion_basis_in_sample_profit_only=bool(
            decoded.get("promotion_basis_in_sample_profit_only", False)
        ),
        zero_cost_evidence=bool(decoded.get("zero_cost_evidence", False)),
        raw_signal_evidence=bool(decoded.get("raw_signal_evidence", False)),
        manifest_verify_only=bool(decoded.get("manifest_verify_only", False)),
        promotion_gate_owner_digest_ref=owner_ref,
        state_file_digest_ref=state_file_digest_ref,
        raw_payload=dict(decoded),
    )


def verify_promotion_gate_backtest_state_file_digest_v0(
    record: PromotionGateBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("promotion_gate_backtest_state_file_digest_mismatch")


def _context_from_state_file(
    state_file: PromotionGateBacktestStateFileRecordV0,
) -> PromotionGateBoundaryOfflineReplayContextV0:
    return PromotionGateBoundaryOfflineReplayContextV0(
        strategy_id=state_file.strategy_id,
        strategy_version=state_file.strategy_version,
        candidate_id=state_file.candidate_id,
        economic_viability_evidence_ref=state_file.economic_viability_evidence_ref,
        economic_validity_status=state_file.economic_validity_status,
        robustness_status=state_file.robustness_status,
        data_admissibility_status=state_file.data_admissibility_status,
        evidence_admissibility_status=state_file.evidence_admissibility_status,
        policy_threshold_status=state_file.policy_threshold_status,
        walk_forward_status=state_file.walk_forward_status,
        out_of_sample_status=state_file.out_of_sample_status,
        monte_carlo_status=state_file.monte_carlo_status,
        stress_status=state_file.stress_status,
        parameter_sensitivity_status=state_file.parameter_sensitivity_status,
        reproducibility_status=state_file.reproducibility_status,
        digest_binding_status=state_file.digest_binding_status,
        manifest_binding_status=state_file.manifest_binding_status,
        safety_policy_status=state_file.safety_policy_status,
        futures_only=state_file.futures_only,
        bitcoin_direction_allowed=state_file.bitcoin_direction_allowed,
        config_digest=state_file.config_digest,
        implementation_digest=state_file.implementation_digest,
        policy_digest=state_file.policy_digest,
        evidence_manifest_digest=state_file.evidence_manifest_digest,
        economic_validity_proven=state_file.economic_validity_proven,
        profitability_claim_allowed=state_file.profitability_claim_allowed,
        promotion_basis_confidence_only=state_file.promotion_basis_confidence_only,
        promotion_basis_in_sample_profit_only=state_file.promotion_basis_in_sample_profit_only,
        zero_cost_evidence=state_file.zero_cost_evidence,
        raw_signal_evidence=state_file.raw_signal_evidence,
        manifest_verify_only=state_file.manifest_verify_only,
    )


def bind_promotion_gate_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: PromotionGateBacktestStateFileRecordV0,
) -> PromotionGateBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file Promotion Gate through the Surface M offline adapter."""
    offline_binding = bind_promotion_gate_boundary_offline_replay_evidence_v0(
        evidence,
        context=_context_from_state_file(state_file),
    )
    if not promotion_gate_boundary_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("promotion_gate_backtest_state_file_non_authority_boundary_failed")

    boundary = offline_binding.boundary
    return PromotionGateBoundaryBacktestStateFileEvidenceV0(
        promotion_gate_boundary_backtest_state_file_bound=True,
        promotion_gate_semantics_bound=boundary.promotion_gate_boundary_bound,
        promotion_gate_semantics_represented_in_backtest=boundary.promotion_gate_semantics_represented,
        economic_validity_required_for_promotion_represented_in_backtest=(
            boundary.economic_validity_required_for_promotion_represented
        ),
        robustness_required_for_promotion_represented_in_backtest=(
            boundary.robustness_required_for_promotion_represented
        ),
        evidence_admissibility_required_for_promotion_represented_in_backtest=(
            boundary.evidence_admissibility_required_for_promotion_represented
        ),
        safety_policy_required_for_promotion_represented_in_backtest=(
            boundary.safety_policy_required_for_promotion_represented
        ),
        no_promotion_from_confidence_only_represented_in_backtest=(
            boundary.no_promotion_from_confidence_only_represented
        ),
        no_runtime_authority_from_promotion_represented_in_backtest=(
            boundary.no_runtime_authority_from_promotion_represented
        ),
        no_economic_claim_from_manifest_verify_alone_represented_in_backtest=(
            boundary.no_economic_claim_from_manifest_verify_alone_represented
        ),
        raw_signal_evidence_not_promotion_admissible_represented_in_backtest=(
            boundary.raw_signal_evidence_not_promotion_admissible_represented
        ),
        promotion_eligible=boundary.promotion_eligible,
        promotion_gate_owner_digest_ref=state_file.promotion_gate_owner_digest_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_m_adapter_owner_ref=PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    )


def evaluate_backtest_promotion_gate_state_file_boundary_only_v0(
    state_file: PromotionGateBacktestStateFileRecordV0,
) -> PromotionGateBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-promotion-gate-state-file-stub",
        replay_id="backtest-promotion-gate-state-file-stub",
        instrument_id="backtest-stub",
        trading_epoch=0,
        composition_result_id="stub",
        entry_exit_policy_ref="stub",
        selected_side="none",
        decision_outcome="observe",
        reason_codes=("stub",),
        decision_precedence_trace=("stub",),
        config_digest="stub",
        implementation_digest="stub",
    )
    return bind_promotion_gate_boundary_backtest_state_file_evidence_v0(
        stub,
        state_file=state_file,
    )


def apply_backtest_promotion_gate_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: PromotionGateBoundaryBacktestStateFileEvidenceV0,
) -> int:
    """Promotion Gate boundary representation does not grant runtime trading authority."""
    if not evidence.promotion_gate_semantics_represented_in_backtest:
        return position_signal
    return position_signal


def promotion_gate_boundary_semantics_represented_in_backtest_v0(
    evidence: PromotionGateBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    return (
        evidence.promotion_gate_semantics_represented_in_backtest
        and evidence.promotion_gate_semantics_bound
        and evidence.no_runtime_authority_from_promotion_represented_in_backtest
    )


def backtest_promotion_gate_state_file_binding_non_authority_ok_v0(
    evidence: PromotionGateBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.promotion_gate_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    return promotion_gate_boundary_binding_non_authority_boundary_ok_v0(evidence.offline_binding)


def load_promotion_gate_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> PromotionGateBacktestStateFileRecordV0:
    record = parse_promotion_gate_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_promotion_gate_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
