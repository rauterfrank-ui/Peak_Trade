# src/trading/master_v2/ai_observability_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
AI / Observability / Explainability boundary semantics via the Surface N offline adapter.

Wiring-only parity slice — read-only evidence-only; no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY,
    AiObservabilityBoundaryOfflineReplayBindingResultV0,
    AiObservabilityBoundaryOfflineReplayContextV0,
    ai_observability_boundary_binding_non_authority_boundary_ok_v0,
    bind_ai_observability_boundary_offline_replay_evidence_v0,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import EVIDENCE_SCHEMA_VERSION
from trading.master_v2.decision_packet_v1 import MASTER_V2_DECISION_PACKET_LAYER_VERSION

AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.ai_observability_boundary_backtest_state_file_binding_adapter_v0"
)
AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "ai_observability_boundary_backtest_state_file_v0"
)


@dataclass(frozen=True)
class AiObservabilityBacktestStateFileRecordV0:
    """Parsed AI / Observability backtest state-file payload."""

    explainability_envelope_mode: str
    ai_layer_owner_digest_ref: str
    decision_packet_owner_digest_ref: str
    state_file_digest_ref: str
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class AiObservabilityBoundaryBacktestStateFileEvidenceV0:
    ai_observability_boundary_backtest_state_file_bound: bool
    ai_layer_observability_boundary_documented: bool
    read_only_evidence_only: bool
    explainability_envelope_represented_in_backtest: bool
    reason_codes_observable_in_backtest: bool
    decision_precedence_trace_observable_in_backtest: bool
    no_ai_trade_authority_in_backtest: bool
    ai_layer_owner_digest_ref: str
    decision_packet_owner_digest_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: AiObservabilityBoundaryOfflineReplayBindingResultV0
    surface_n_adapter_owner_ref: str


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


def parse_ai_observability_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> AiObservabilityBacktestStateFileRecordV0:
    """Parse backtest AI / Observability state file. Fail-closed on missing or invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("ai_observability_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("ai_observability_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("ai_observability_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("ai_observability_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("ai_observability_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("ai_observability_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if (
        schema_version
        and schema_version != AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION
    ):
        raise ValueError("ai_observability_backtest_state_file_schema_version_mismatch")

    mode = _require_text(
        decoded.get("explainability_envelope_mode"), field_name="explainability_envelope_mode"
    )
    if mode != EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY:
        raise ValueError("ai_observability_explainability_mode_invalid")

    ai_layer_ref = _require_text(
        decoded.get("ai_layer_owner_digest_ref"),
        field_name="ai_layer_owner_digest_ref",
    )
    packet_ref = _require_text(
        decoded.get("decision_packet_owner_digest_ref"),
        field_name="decision_packet_owner_digest_ref",
    )

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("ai_observability_backtest_state_file_digest_mismatch")

    return AiObservabilityBacktestStateFileRecordV0(
        explainability_envelope_mode=mode,
        ai_layer_owner_digest_ref=ai_layer_ref,
        decision_packet_owner_digest_ref=packet_ref,
        state_file_digest_ref=state_file_digest_ref,
        raw_payload=dict(decoded),
    )


def verify_ai_observability_backtest_state_file_digest_v0(
    record: AiObservabilityBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("ai_observability_backtest_state_file_digest_mismatch")


def _context_from_state_file(
    state_file: AiObservabilityBacktestStateFileRecordV0,
) -> AiObservabilityBoundaryOfflineReplayContextV0:
    return AiObservabilityBoundaryOfflineReplayContextV0(
        explainability_envelope_mode=state_file.explainability_envelope_mode,
        ai_layer_owner_digest_ref=state_file.ai_layer_owner_digest_ref,
        decision_packet_owner_digest_ref=state_file.decision_packet_owner_digest_ref,
    )


def bind_ai_observability_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: AiObservabilityBacktestStateFileRecordV0,
) -> AiObservabilityBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file AI / Observability through the Surface N offline adapter."""
    offline_binding = bind_ai_observability_boundary_offline_replay_evidence_v0(
        evidence,
        context=_context_from_state_file(state_file),
    )
    if not ai_observability_boundary_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("ai_observability_backtest_state_file_non_authority_boundary_failed")

    boundary = offline_binding.boundary
    return AiObservabilityBoundaryBacktestStateFileEvidenceV0(
        ai_observability_boundary_backtest_state_file_bound=True,
        ai_layer_observability_boundary_documented=boundary.ai_layer_observability_boundary_documented,
        read_only_evidence_only=boundary.read_only_evidence_only,
        explainability_envelope_represented_in_backtest=boundary.explainability_envelope_represented,
        reason_codes_observable_in_backtest=boundary.reason_codes_observable,
        decision_precedence_trace_observable_in_backtest=boundary.decision_precedence_trace_observable,
        no_ai_trade_authority_in_backtest=boundary.no_ai_trade_authority,
        ai_layer_owner_digest_ref=state_file.ai_layer_owner_digest_ref,
        decision_packet_owner_digest_ref=state_file.decision_packet_owner_digest_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_n_adapter_owner_ref=AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    )


def evaluate_backtest_ai_observability_state_file_boundary_only_v0(
    state_file: AiObservabilityBacktestStateFileRecordV0,
) -> AiObservabilityBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-ai-observability-state-file-stub",
        replay_id="backtest-ai-observability-state-file-stub",
        instrument_id="backtest-stub",
        trading_epoch=0,
        composition_result_id="stub",
        entry_exit_policy_ref="stub",
        selected_side="long",
        decision_outcome="enter_long",
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="stub",
        implementation_digest="stub",
    )
    return bind_ai_observability_boundary_backtest_state_file_evidence_v0(
        stub,
        state_file=state_file,
    )


def apply_backtest_ai_observability_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: AiObservabilityBoundaryBacktestStateFileEvidenceV0,
) -> int:
    """AI / Observability boundary representation does not grant runtime trading authority."""
    if not evidence.explainability_envelope_represented_in_backtest:
        return position_signal
    return position_signal


def ai_observability_boundary_semantics_represented_in_backtest_v0(
    evidence: AiObservabilityBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    return (
        evidence.explainability_envelope_represented_in_backtest
        and evidence.ai_layer_observability_boundary_documented
        and evidence.read_only_evidence_only
        and evidence.no_ai_trade_authority_in_backtest
    )


def backtest_ai_observability_state_file_binding_non_authority_ok_v0(
    evidence: AiObservabilityBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.ai_observability_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    if not AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED:
        return False
    return ai_observability_boundary_binding_non_authority_boundary_ok_v0(evidence.offline_binding)


def load_ai_observability_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> AiObservabilityBacktestStateFileRecordV0:
    record = parse_ai_observability_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_ai_observability_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


def default_ai_observability_backtest_state_file_payload_v0() -> dict[str, object]:
    base = {
        "schema_version": AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "explainability_envelope_mode": EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY,
        "ai_layer_owner_digest_ref": EVIDENCE_SCHEMA_VERSION,
        "decision_packet_owner_digest_ref": MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
