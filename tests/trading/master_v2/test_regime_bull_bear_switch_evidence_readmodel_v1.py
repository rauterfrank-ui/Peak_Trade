"""Focused tests for EVIDENCE_ONLY regime/bull-bear/switch evidence readmodel."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from src.ops.full_decision_path_atomic_restart_closure_v1.state_classification_v1 import (
    build_state_root_classification_matrix_v1,
    classify_fields_by_bucket_v1,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState, TransitionDecision
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.capture_v1 import (
    capture_regime_bull_bear_switch_evidence_readmodel_v1,
)
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.constants_v1 import (
    EVIDENCE_CLASSIFICATION,
    ERROR_INVALID_ENUM,
    ERROR_MISSING_FIELD,
    ERROR_SIDE_NEXT_MISMATCH,
    RESTART_AUTHORITY,
    TRADING_INPUT,
)
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.models_v1 import (
    RegimeBullBearSwitchEvidenceError,
    RegimeBullBearSwitchEvidenceReadmodelV1,
    build_from_authorized_capture_inputs_v1,
)
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.persistence_v1 import (
    load_regime_bull_bear_switch_evidence_readmodel_v1,
    write_regime_bull_bear_switch_evidence_readmodel_v1,
)
from trading.master_v2.suitability_binding_v1 import SuitabilityRegimeStatus

REPO = Path(__file__).resolve().parents[3]


def _transition(*, allowed: bool = True, reason: str = "UPSCOPE_CONFIRMED") -> TransitionDecision:
    return TransitionDecision(allowed=allowed, reason_code=reason)


def _capture_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "regime_id": "trending",
        "regime_status": SuitabilityRegimeStatus.KNOWN,
        "previous_side_state": SideState.LONG_ARMED,
        "next_side_state": SideState.LONG_ACTIVE,
        "scope_event_type": ScopeEvent.UPSCOPE_CONFIRMED,
        "transition": _transition(),
        "instrument_id": "BTC-USDT-SWAP",
        "trading_epoch": 7,
    }
    base.update(overrides)
    return base


def test_eight_field_roundtrip(tmp_path: Path) -> None:
    evidence = build_from_authorized_capture_inputs_v1(**_capture_kwargs())
    path = tmp_path / "regime_bull_bear_switch_evidence_readmodel.v1.json"
    write_regime_bull_bear_switch_evidence_readmodel_v1(path, evidence)
    loaded = load_regime_bull_bear_switch_evidence_readmodel_v1(path)
    assert loaded.to_dict() == evidence.to_dict()
    assert loaded.regime_id == "trending"
    assert loaded.regime_status is SuitabilityRegimeStatus.KNOWN
    assert loaded.side_state is SideState.LONG_ACTIVE
    assert loaded.previous_side_state is SideState.LONG_ARMED
    assert loaded.next_side_state is SideState.LONG_ACTIVE
    assert loaded.scope_event_type is ScopeEvent.UPSCOPE_CONFIRMED
    assert loaded.transition_allowed is True
    assert loaded.transition_reason_code == "UPSCOPE_CONFIRMED"


def test_side_state_equals_next_post_transition() -> None:
    evidence = build_from_authorized_capture_inputs_v1(**_capture_kwargs())
    assert evidence.side_state is evidence.next_side_state
    assert evidence.side_state is SideState.LONG_ACTIVE


def test_enum_status_serialization(tmp_path: Path) -> None:
    evidence = build_from_authorized_capture_inputs_v1(
        **_capture_kwargs(
            regime_status=SuitabilityRegimeStatus.UNKNOWN,
            next_side_state=SideState.NEUTRAL_OBSERVE,
            previous_side_state=SideState.NEUTRAL_OBSERVE,
            scope_event_type=ScopeEvent.NOOP,
            transition=_transition(allowed=False, reason="NOOP"),
        )
    )
    path = tmp_path / "e.json"
    write_regime_bull_bear_switch_evidence_readmodel_v1(path, evidence)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["regime_status"] == "unknown"
    assert raw["side_state"] == "neutral_observe"
    assert raw["scope_event_type"] == "noop"
    assert raw["transition_allowed"] is False


def test_missing_required_field_fail_closed() -> None:
    with pytest.raises(RegimeBullBearSwitchEvidenceError) as exc:
        build_from_authorized_capture_inputs_v1(**_capture_kwargs(regime_id=""))
    assert ERROR_MISSING_FIELD in str(exc.value)


def test_unknown_enum_fail_closed() -> None:
    with pytest.raises(RegimeBullBearSwitchEvidenceError) as exc:
        RegimeBullBearSwitchEvidenceReadmodelV1.from_dict(
            {
                **build_from_authorized_capture_inputs_v1(**_capture_kwargs()).to_dict(),
                "side_state": "not_a_side_state",
            }
        )
    assert ERROR_INVALID_ENUM in str(exc.value)


def test_side_next_mismatch_fail_closed() -> None:
    payload = build_from_authorized_capture_inputs_v1(**_capture_kwargs()).to_dict()
    payload["side_state"] = SideState.SHORT_ACTIVE.value
    payload["next_side_state"] = SideState.LONG_ACTIVE.value
    with pytest.raises(RegimeBullBearSwitchEvidenceError) as exc:
        RegimeBullBearSwitchEvidenceReadmodelV1.from_dict(payload)
    assert ERROR_SIDE_NEXT_MISMATCH in str(exc.value)


def test_atomic_write_no_partial_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = build_from_authorized_capture_inputs_v1(**_capture_kwargs())
    path = tmp_path / "target.json"

    def boom(*_a: object, **_k: object) -> None:
        raise OSError("disk_full")

    monkeypatch.setattr(
        "trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.persistence_v1.os.replace",
        boom,
    )
    with pytest.raises(RegimeBullBearSwitchEvidenceError):
        write_regime_bull_bear_switch_evidence_readmodel_v1(path, evidence)
    assert not path.exists()
    leftovers = list(tmp_path.glob("target.json.*"))
    assert leftovers == []


def test_classification_evidence_only_non_restart() -> None:
    evidence = build_from_authorized_capture_inputs_v1(**_capture_kwargs())
    assert evidence.evidence_classification == EVIDENCE_CLASSIFICATION
    assert evidence.restart_authority is False
    assert evidence.trading_input is False
    assert evidence.decision_authority is False
    assert evidence.parallel_persistence_domain is False
    assert RESTART_AUTHORITY is False
    assert TRADING_INPUT is False


def test_state_matrix_evidence_only_not_restart_member() -> None:
    rows = build_state_root_classification_matrix_v1()
    match = [r for r in rows if r["field"] == "regime_bull_bear_switch_evidence_readmodel"]
    assert len(match) == 1
    row = match[0]
    assert row["classification"] == "EVIDENCE_ONLY"
    assert row["state_root"] == "evidence"
    assert row.get("restart_authority") is False
    assert row.get("trading_input") is False
    assert row.get("parallel_domain") is False
    buckets = classify_fields_by_bucket_v1()
    assert "regime_bull_bear_switch_evidence_readmodel" in buckets["EVIDENCE_ONLY"]
    assert "regime_bull_bear_switch_evidence_readmodel" not in buckets["PERSIST_DIRECTLY"]
    assert "master_v2_full_decision_blob" in buckets["FORBIDDEN_TO_PERSIST"]
    assert "double_play_parallel_domain" in buckets["FORBIDDEN_TO_PERSIST"]
    # Restart SideState owner unchanged under dynamic_scope member.
    from src.ops.full_decision_path_atomic_restart_closure_v1.constants_v1 import (
        MEMBER_DYNAMIC_SCOPE,
    )

    runtime_scope = [r for r in rows if r["field"] == "runtime_scope_state"]
    assert runtime_scope[0]["state_root"] == MEMBER_DYNAMIC_SCOPE
    assert runtime_scope[0]["classification"] == "PERSIST_DIRECTLY"
    carrier = [r for r in rows if r["field"] == "master_v2_double_play_carrier_required"]
    assert carrier[0]["state_root"] == MEMBER_DYNAMIC_SCOPE


def test_no_loader_import_in_trading_decision_modules() -> None:
    forbidden_roots = [
        REPO / "src/trading/master_v2/double_play_state.py",
        REPO / "src/trading/master_v2/suitability_binding_v1.py",
        REPO / "src/trading/master_v2/double_play_composition.py",
        REPO / "src/ops/dynamic_scope_persistence_binding_v1/persistence_v1.py",
        REPO / "src/ops/dynamic_scope_persistence_binding_v1/models_v1.py",
    ]
    needle = "regime_bull_bear_switch_evidence_readmodel"
    for path in forbidden_roots:
        text = path.read_text(encoding="utf-8")
        assert needle not in text, f"unexpected evidence coupling in {path}"


def test_capture_exact_field_copy() -> None:
    transition = _transition(allowed=False, reason="COOLDOWN")
    evidence = capture_regime_bull_bear_switch_evidence_readmodel_v1(
        regime_id="ranging",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        previous_side_state=SideState.SHORT_ACTIVE,
        next_side_state=SideState.SHORT_BLOCKED,
        scope_event_type=ScopeEvent.DOWNSCOPE_CONFIRMED,
        transition=transition,
        instrument_id="ETH-USDT-SWAP",
        trading_epoch=3,
    )
    assert evidence.regime_id == "ranging"
    assert evidence.regime_status is SuitabilityRegimeStatus.KNOWN
    assert evidence.previous_side_state is SideState.SHORT_ACTIVE
    assert evidence.side_state is SideState.SHORT_BLOCKED
    assert evidence.next_side_state is SideState.SHORT_BLOCKED
    assert evidence.scope_event_type is ScopeEvent.DOWNSCOPE_CONFIRMED
    assert evidence.transition_allowed is False
    assert evidence.transition_reason_code == "COOLDOWN"


def test_dynamic_scope_state_model_unchanged() -> None:
    mod = importlib.import_module("src.ops.dynamic_scope_persistence_binding_v1.models_v1")
    src = Path(mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    class_names = {n.name for n in tree.body if isinstance(n, ast.ClassDef)}
    assert "CanonicalDynamicScopeStateV1" in class_names
    # Evidence package must not be referenced from dynamic-scope model.
    assert "regime_bull_bear_switch_evidence" not in src
