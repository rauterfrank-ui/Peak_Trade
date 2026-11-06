# src/trading/master_v2/feedback_learning_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
Feedback / Learning boundary semantics via the Surface O offline adapter.

Wiring-only parity slice — observe-only; no strategy, promotion, or runtime mutation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.meta.learning_loop.deploy_inactive_v1 import DEPLOYMENT_CANDIDATE_CONTRACT_NAME
from src.meta.learning_loop.runtime_observation_feedback_v1 import OBSERVATION_CONTRACT_NAME
from trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
    FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
    FeedbackLearningBoundaryOfflineReplayBindingResultV0,
    FeedbackLearningBoundaryOfflineReplayContextV0,
    bind_feedback_learning_boundary_offline_replay_evidence_v0,
    feedback_learning_boundary_binding_non_authority_boundary_ok_v0,
)

FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.feedback_learning_boundary_backtest_state_file_binding_adapter_v0"
)
FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "feedback_learning_boundary_backtest_state_file_v0"
)


@dataclass(frozen=True)
class FeedbackLearningBacktestStateFileRecordV0:
    """Parsed Feedback / Learning backtest state-file payload."""

    feedback_learning_mode: str
    feedback_observation_contract_ref: str
    learning_deploy_inactive_contract_ref: str
    state_file_digest_ref: str
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class FeedbackLearningBoundaryBacktestStateFileEvidenceV0:
    feedback_learning_boundary_backtest_state_file_bound: bool
    feedback_learning_boundary_documented: bool
    observe_only_no_mutation_in_backtest: bool
    no_strategy_selection_mutation_represented_in_backtest: bool
    no_promotion_mutation_represented_in_backtest: bool
    no_runtime_eligibility_mutation_represented_in_backtest: bool
    no_sizing_mutation_represented_in_backtest: bool
    no_order_intent_mutation_represented_in_backtest: bool
    no_safety_mutation_represented_in_backtest: bool
    no_reconciliation_mutation_represented_in_backtest: bool
    no_economic_results_mutation_represented_in_backtest: bool
    feedback_observation_contract_ref: str
    learning_deploy_inactive_contract_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: FeedbackLearningBoundaryOfflineReplayBindingResultV0
    surface_o_adapter_owner_ref: str


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


def parse_feedback_learning_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> FeedbackLearningBacktestStateFileRecordV0:
    """Parse backtest Feedback / Learning state file. Fail-closed on missing or invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("feedback_learning_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("feedback_learning_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("feedback_learning_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("feedback_learning_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("feedback_learning_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("feedback_learning_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if (
        schema_version
        and schema_version != FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION
    ):
        raise ValueError("feedback_learning_backtest_state_file_schema_version_mismatch")

    mode = _require_text(decoded.get("feedback_learning_mode"), field_name="feedback_learning_mode")
    if mode != FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION:
        raise ValueError("feedback_learning_mode_invalid")

    observation_ref = _require_text(
        decoded.get("feedback_observation_contract_ref"),
        field_name="feedback_observation_contract_ref",
    )
    deploy_ref = _require_text(
        decoded.get("learning_deploy_inactive_contract_ref"),
        field_name="learning_deploy_inactive_contract_ref",
    )

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("feedback_learning_backtest_state_file_digest_mismatch")

    return FeedbackLearningBacktestStateFileRecordV0(
        feedback_learning_mode=mode,
        feedback_observation_contract_ref=observation_ref,
        learning_deploy_inactive_contract_ref=deploy_ref,
        state_file_digest_ref=state_file_digest_ref,
        raw_payload=dict(decoded),
    )


def verify_feedback_learning_backtest_state_file_digest_v0(
    record: FeedbackLearningBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("feedback_learning_backtest_state_file_digest_mismatch")


def _context_from_state_file(
    state_file: FeedbackLearningBacktestStateFileRecordV0,
) -> FeedbackLearningBoundaryOfflineReplayContextV0:
    return FeedbackLearningBoundaryOfflineReplayContextV0(
        feedback_learning_mode=state_file.feedback_learning_mode,
        feedback_observation_contract_ref=state_file.feedback_observation_contract_ref,
        learning_deploy_inactive_contract_ref=state_file.learning_deploy_inactive_contract_ref,
    )


def bind_feedback_learning_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: FeedbackLearningBacktestStateFileRecordV0,
) -> FeedbackLearningBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file Feedback / Learning through the Surface O offline adapter."""
    offline_binding = bind_feedback_learning_boundary_offline_replay_evidence_v0(
        evidence,
        context=_context_from_state_file(state_file),
    )
    if not feedback_learning_boundary_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("feedback_learning_backtest_state_file_non_authority_boundary_failed")

    boundary = offline_binding.boundary
    return FeedbackLearningBoundaryBacktestStateFileEvidenceV0(
        feedback_learning_boundary_backtest_state_file_bound=True,
        feedback_learning_boundary_documented=boundary.feedback_learning_boundary_documented,
        observe_only_no_mutation_in_backtest=boundary.observe_only_no_mutation,
        no_strategy_selection_mutation_represented_in_backtest=boundary.no_strategy_selection_mutation,
        no_promotion_mutation_represented_in_backtest=boundary.no_promotion_mutation,
        no_runtime_eligibility_mutation_represented_in_backtest=(
            boundary.no_runtime_eligibility_mutation
        ),
        no_sizing_mutation_represented_in_backtest=boundary.no_sizing_mutation,
        no_order_intent_mutation_represented_in_backtest=boundary.no_order_intent_mutation,
        no_safety_mutation_represented_in_backtest=boundary.no_safety_mutation,
        no_reconciliation_mutation_represented_in_backtest=boundary.no_reconciliation_mutation,
        no_economic_results_mutation_represented_in_backtest=boundary.no_economic_results_mutation,
        feedback_observation_contract_ref=state_file.feedback_observation_contract_ref,
        learning_deploy_inactive_contract_ref=state_file.learning_deploy_inactive_contract_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_o_adapter_owner_ref=FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    )


def evaluate_backtest_feedback_learning_state_file_boundary_only_v0(
    state_file: FeedbackLearningBacktestStateFileRecordV0,
) -> FeedbackLearningBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-feedback-learning-state-file-stub",
        replay_id="backtest-feedback-learning-state-file-stub",
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
    return bind_feedback_learning_boundary_backtest_state_file_evidence_v0(
        stub,
        state_file=state_file,
    )


def apply_backtest_feedback_learning_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: FeedbackLearningBoundaryBacktestStateFileEvidenceV0,
) -> int:
    """Feedback / Learning boundary representation does not mutate trading exposure."""
    if not evidence.observe_only_no_mutation_in_backtest:
        return position_signal
    return position_signal


def feedback_learning_boundary_semantics_represented_in_backtest_v0(
    evidence: FeedbackLearningBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    return (
        evidence.feedback_learning_boundary_documented
        and evidence.observe_only_no_mutation_in_backtest
        and evidence.no_strategy_selection_mutation_represented_in_backtest
        and evidence.no_promotion_mutation_represented_in_backtest
        and evidence.no_economic_results_mutation_represented_in_backtest
    )


def backtest_feedback_learning_state_file_binding_non_authority_ok_v0(
    evidence: FeedbackLearningBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.feedback_learning_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    if not FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED:
        return False
    return feedback_learning_boundary_binding_non_authority_boundary_ok_v0(evidence.offline_binding)


def load_feedback_learning_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> FeedbackLearningBacktestStateFileRecordV0:
    record = parse_feedback_learning_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_feedback_learning_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


def default_feedback_learning_backtest_state_file_payload_v0() -> dict[str, object]:
    base = {
        "schema_version": FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "feedback_learning_mode": FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
        "feedback_observation_contract_ref": OBSERVATION_CONTRACT_NAME,
        "learning_deploy_inactive_contract_ref": DEPLOYMENT_CANDIDATE_CONTRACT_NAME,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
