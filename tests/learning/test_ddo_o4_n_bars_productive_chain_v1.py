"""WP_DDO_PRODUCTIVE_CHAIN_TO_NEXT_HARD_BLOCKER_V1 — bridge/supplier/offline E2E."""

from __future__ import annotations

import ast
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.capture_v0 import BLOCKED_CAPTURE_SEAMS_V0
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    N_BARS_BAR_EVIDENCE_SUPPLIER_ID,
    materialize_real_outcome_horizon_supplier_input_v1,
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    O4_N_BARS_BAR_EVIDENCE_BRIDGE_ID,
    O4_SNAPSHOT_SCHEMA_NAME,
    O4_SNAPSHOT_SCHEMA_VERSION,
    O4_STATE_FINALIZED,
    translate_o4_snapshot_to_ddo_n_bars_bindings_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_ENGINE_WIRED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"


def _utc_unix(iso: str) -> float:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc).timestamp()


def _obs_identity(*, venue_event_time: float) -> dict[str, Any]:
    return {
        "venue": "okx_eea",
        "canonical_instrument_id": "ETH-USD-SWAP-CANON",
        "venue_instrument_id": "ETH-USD-SWAP",
        "venue_event_time": venue_event_time,
        "mark_price": 3500.0,
    }


def _o4_bar(
    *,
    open_iso: str,
    close_iso: str,
    close_price: float,
    finalization_state: str = O4_STATE_FINALIZED,
    venue_event_time: float | None = None,
    revision: int = 0,
) -> dict[str, Any]:
    open_t = _utc_unix(open_iso)
    close_t = _utc_unix(close_iso)
    vet = close_t if venue_event_time is None else venue_event_time
    return {
        "canonical_instrument_id": "ETH-USD-SWAP-CANON",
        "venue_instrument_id": "ETH-USD-SWAP",
        "venue": "okx_eea",
        "interval": "PT1H",
        "bar_open_time": open_t,
        "bar_close_time": close_t,
        "finalization_state": finalization_state,
        "quality_state": finalization_state,
        "last_observation_identity": _obs_identity(venue_event_time=vet),
        "session_id": "o4-session-1",
        "repository_sha": "abc12345deadbeef",
        "config_digest": "cfgdigest001",
        "close": close_price,
        "revision": revision,
    }


def _snapshot(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": O4_SNAPSHOT_SCHEMA_NAME,
        "schema_version": O4_SNAPSHOT_SCHEMA_VERSION,
        "decision_event_ref": "dec-chain-0001",
        "horizon_start_time_utc": "2026-09-01T12:00:00Z",
        "n_bars": 2,
        "o4_interval_id": "PT1H",
        "o4_bars": [
            _o4_bar(
                open_iso="2026-09-01T12:00:00Z", close_iso="2026-09-01T13:00:00Z", close_price=100.0
            ),
            _o4_bar(
                open_iso="2026-09-01T13:00:00Z", close_iso="2026-09-01T14:00:00Z", close_price=110.0
            ),
        ],
    }
    payload.update(overrides)
    return payload


def _decision(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "decision_event",
        "schema_version": "decision_event_v0",
        "record_id": "dec-chain-0001",
        "event_id": "evt-chain-0001",
        "correlation_id": "cor-chain-0001",
        "cycle_id": None,
        "event_time_utc": "2026-09-01T12:00:00Z",
        "decision_type": "NO_ENTRY",
        "decision_result": "NO_ACTION",
        "reason_codes": [],
        "hard_block_reasons": [],
        "decision_time_information_set_ref": "info-set-decision-1",
        "market_snapshot_ref": None,
        "feature_snapshot_ref": None,
        "data_quality_ref": None,
        "risk_snapshot_ref": None,
        "position_snapshot_ref": None,
        "selected_instrument_ref": None,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "authority_owner": UNKNOWN,
        "producer_id": "offline-test-producer",
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": [],
        "evidence_source_refs": ["src-evidence-1"],
    }
    payload.update(overrides)
    return payload


def _identity(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "outcome_record_id": "out-chain-0001",
        "attribution_record_id": "attr-chain-0001",
        "counterfactual_record_id": "cf-chain-0001",
        "correlation_id": "cor-chain-0001",
        "event_time_utc": "2026-09-01T14:00:00Z",
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
    }
    payload.update(overrides)
    return payload


def test_capture_and_engine_wired_remain_blocked() -> None:
    assert REAL_OUTCOME_HORIZON_ENGINE_WIRED is False
    assert "real_outcome_horizon_engine" in BLOCKED_CAPTURE_SEAMS_V0


def test_log_return_offline_e2e_real_claim() -> None:
    decision = build_decision_event_v0(_decision())
    result = run_offline_n_bars_horizon_pipeline_v1(
        decision,
        _snapshot(),
        outcome_scalar_kind="LOG_RETURN",
        economic_score="LABEL_1",
    )
    mat = result["materialization"]
    obs = result["evaluation_observation"]
    assert mat.supplier_input["horizon_observation_status"] == "OK"
    assert obs["actual_outcome_ref"] == mat.supplier_input["actual_outcome_ref"]
    assert obs["evaluation_horizon"] == "N_BARS"
    assert (
        mat.evaluation_time_information_set_artifact["bridge_contract_id"]
        == O4_N_BARS_BAR_EVIDENCE_BRIDGE_ID
    )
    assert (
        mat.measurement_evidence_artifact["measurement_producer_id"]
        == N_BARS_BAR_EVIDENCE_SUPPLIER_ID
    )
    expected_log = math.log(110.0 / 100.0)
    assert mat.measurement_evidence_artifact["log_return"] == pytest.approx(expected_log)
    bundle = evaluate_offline_bundle_v0(decision, obs, identity=_identity())
    assert (
        bundle["outcome_record"]["actual_outcome_ref"] == mat.supplier_input["actual_outcome_ref"]
    )
    assert bundle["hindsight_leakage"] is False


def test_bridge_does_not_import_ops() -> None:
    forbidden = ("src.ops", "src.trading", "src.execution", "src.live", "src.risk")
    for name in (
        "o4_n_bars_bar_evidence_bridge_contracts_v1.py",
        "n_bars_bar_evidence_supplier_v1.py",
    ):
        path = PACKAGE_DIR / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hits: list[str] = []
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for mod in modules:
                if any(mod == p or mod.startswith(p + ".") for p in forbidden):
                    hits.append(f"{name}:{mod}")
        assert hits == []


def test_gapless_translation_deterministic() -> None:
    snap = _snapshot()
    first = translate_o4_snapshot_to_ddo_n_bars_bindings_v1(snap)
    second = translate_o4_snapshot_to_ddo_n_bars_bindings_v1(snap)
    assert first.to_dict() == second.to_dict()
    assert first.horizon_observation_status == "OK"
    assert len(first.bar_identity_refs) == 2


def test_non_gapless_bars_fail_closed() -> None:
    bars = [
        _o4_bar(
            open_iso="2026-09-01T12:00:00Z", close_iso="2026-09-01T13:00:00Z", close_price=100.0
        ),
        _o4_bar(
            open_iso="2026-09-01T14:00:00Z", close_iso="2026-09-01T15:00:00Z", close_price=101.0
        ),
    ]
    translation = translate_o4_snapshot_to_ddo_n_bars_bindings_v1(_snapshot(o4_bars=bars))
    assert translation.horizon_observation_status == "GAP"
    decision = build_decision_event_v0(_decision())
    mat = materialize_real_outcome_horizon_supplier_input_v1(
        decision, _snapshot(o4_bars=bars), outcome_scalar_kind="LOG_RETURN"
    )
    assert mat.supplier_input["horizon_observation_status"] == "GAP"
    obs = run_offline_n_bars_horizon_pipeline_v1(
        decision, _snapshot(o4_bars=bars), outcome_scalar_kind="LOG_RETURN"
    )["evaluation_observation"]
    bundle = evaluate_offline_bundle_v0(decision, obs, identity=_identity())
    assert bundle["outcome_record"]["actual_outcome_ref"] == UNKNOWN


def test_pit_post_boundary_observation_rejected() -> None:
    bad_bar = _o4_bar(
        open_iso="2026-09-01T13:00:00Z",
        close_iso="2026-09-01T14:00:00Z",
        close_price=110.0,
        venue_event_time=_utc_unix("2026-09-01T14:30:00Z"),
    )
    snap = _snapshot(
        o4_bars=[
            _o4_bar(
                open_iso="2026-09-01T12:00:00Z", close_iso="2026-09-01T13:00:00Z", close_price=100.0
            ),
            bad_bar,
        ]
    )
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="PIT_POST_BOUNDARY_OBSERVATION"):
        materialize_real_outcome_horizon_supplier_input_v1(
            decision, snap, outcome_scalar_kind="LOG_RETURN"
        )


def test_decision_time_information_set_reuse_forbidden() -> None:
    decision = build_decision_event_v0(_decision())
    snap = _snapshot()
    mat = materialize_real_outcome_horizon_supplier_input_v1(
        decision, snap, outcome_scalar_kind="LOG_RETURN"
    )
    eval_ref = mat.supplier_input["evaluation_time_information_set_ref"]
    assert eval_ref != decision["decision_time_information_set_ref"]


def test_unsupported_outcome_kind_rejected() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(DdoValidationError, match="UNSUPPORTED_OUTCOME_SCALAR_KIND"):
        materialize_real_outcome_horizon_supplier_input_v1(
            decision, _snapshot(), outcome_scalar_kind="UNKNOWN_KIND"
        )


def test_hit_target_measurement() -> None:
    decision = build_decision_event_v0(_decision())
    mat = materialize_real_outcome_horizon_supplier_input_v1(
        decision,
        _snapshot(),
        outcome_scalar_kind="HIT_TARGET",
        hit_target_value=105.0,
        hit_target_comparator="GE",
    )
    assert mat.measurement_evidence_artifact["hit_result"] is True


def test_provenance_mismatch_rejected() -> None:
    bars = [
        _o4_bar(
            open_iso="2026-09-01T12:00:00Z", close_iso="2026-09-01T13:00:00Z", close_price=100.0
        ),
        _o4_bar(
            open_iso="2026-09-01T13:00:00Z", close_iso="2026-09-01T14:00:00Z", close_price=110.0
        ),
    ]
    bars[1] = {**bars[1], "session_id": "other-session"}
    with pytest.raises(DdoValidationError, match="O4_PROVENANCE_SESSION_MISMATCH"):
        translate_o4_snapshot_to_ddo_n_bars_bindings_v1(_snapshot(o4_bars=bars))
