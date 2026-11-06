"""Tests for CURRENT productive GHV startability evaluator (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import math
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_golden_happy_vector_startability_evaluator_v1 import (
    EVALUATION_MODE_OFFLINE_EVIDENCE,
    EXECUTION_AUTHORITY,
    GHV_AUTHORITY,
    GHV_CAN_OPEN_SAFETY_GATES,
    GHV_CAN_POST,
    GHV_HAS_GEOMETRY_AUTHORITY,
    GHV_HAS_SELECTION_AUTHORITY,
    GHV_HAS_TRADING_AUTHORITY,
    GEOMETRY_AUTHORITY,
    NETWORK_REQUIRED_FOR_STRUCTURAL_MODE,
    SELECTION_AUTHORITY,
    TRADING_AUTHORITY,
    evaluate_current_productive_golden_happy_vector_startability_v1,
    report_to_machine_json_v1,
    run_negative_startability_vectors_v1,
)
from trading.master_v2.golden_geometry_engine_v1 import (
    compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_mark_and_volatility_v1,
)

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1"
BASELINE = "ffbc8fbe606640fff19b1094a1873b3f684499c7"


def test_authority_none_invariants() -> None:
    assert GHV_AUTHORITY == "NONE"
    assert TRADING_AUTHORITY == "NONE"
    assert SELECTION_AUTHORITY == "NONE"
    assert GEOMETRY_AUTHORITY == "NONE"
    assert EXECUTION_AUTHORITY == "NONE"
    assert GHV_HAS_TRADING_AUTHORITY is False
    assert GHV_HAS_SELECTION_AUTHORITY is False
    assert GHV_HAS_GEOMETRY_AUTHORITY is False
    assert GHV_CAN_POST is False
    assert GHV_CAN_OPEN_SAFETY_GATES is False
    assert NETWORK_REQUIRED_FOR_STRUCTURAL_MODE is False


def test_negative_invalid_mark_rejected() -> None:
    res = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="test",
        mark_price=-1.0,
        volatility_estimate=0.01,
    )
    assert not res.ok


def test_negative_zero_mark_rejected() -> None:
    res = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="test",
        mark_price=0.0,
        volatility_estimate=0.01,
    )
    assert not res.ok


def test_negative_nan_mark_rejected() -> None:
    res = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="test",
        mark_price=float("nan"),
        volatility_estimate=0.01,
    )
    assert not res.ok


def test_negative_layer_c_bind_rejected() -> None:
    res = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=-1.0,
        volatility_estimate=0.02,
    )
    assert not res.ok


def test_negative_vectors_fail_closed_suite() -> None:
    total, rejected = run_negative_startability_vectors_v1()
    assert total >= 5
    assert rejected == total


def test_fixture_provenance_manifest() -> None:
    manifest = json.loads((FIXTURE / "golden_vector_manifest_v1.json").read_text())
    assert manifest["SOURCE_RUN"] == "post-7065 Natural-Enter Evidence"
    assert manifest["SOURCE_EXECUTION_HEAD_SHA"] == "8cf74278712bf2db247884cc102cc516165c1abf"
    assert manifest["EXPECTED_SIDE"] == "LONG"
    assert manifest["EXPECTED_PRE_EXTERNAL"] is True
    assert manifest["EXPECTED_POST_COUNT"] == 0
    assert manifest["CONTAINS_SECRETS"] is False
    assert manifest["TRADING_AUTHORITY"] == "NONE"


def test_golden_vector_reference_replay_and_dual_verdict() -> None:
    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO,
        golden_vector_root=FIXTURE,
        expected_baseline_sha=BASELINE,
        actual_head_sha=BASELINE,
        live_inputs_required=False,
    )
    assert report.vector_id == "GHV_NATURAL_ENTER_POST_7065_REFERENCE_V1"
    assert report.golden_vector_replay_valid is True
    assert report.structurally_startable is True
    assert report.fail_closed_proven is True
    assert report.current_input_ready is False
    assert report.post_required is False
    assert report.offline_startable_to_pre_external is True
    assert report.startable_to_pre_external is True
    assert report.immediate_current_input_startable is False
    assert report.evaluation_mode == EVALUATION_MODE_OFFLINE_EVIDENCE
    assert report.trading_semantics_changed is False
    by_domain = {d.domain: d for d in report.domains}
    assert by_domain["SAFETY"].status == "PASS"
    assert by_domain["GGE_SCOPE"].status == "PASS"
    assert by_domain["DOUBLE_PLAY"].status == "PASS"
    assert by_domain["EXECUTION_PRE_EXTERNAL"].status == "PASS"
    assert by_domain["MARKET_DATA"].status == "UNKNOWN"
    rep = json.loads((FIXTURE / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text())
    assert int(rep.get("POST_COUNT") or 0) == 0


def test_machine_report_dual_verdict_semantics() -> None:
    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO,
        golden_vector_root=FIXTURE,
        live_inputs_required=False,
    )
    payload = report_to_machine_json_v1(report)
    assert payload["IMMEDIATELY_LIVE_STARTABLE_NOW"] is False
    assert payload["offline_startable_to_pre_external"] is True
    assert "NOT_IMMEDIATE_LIVE_START" in payload["STARTABLE_TO_PRE_EXTERNAL_SEMANTICS"]


def test_wrong_instrument_binding_in_selection_fails(tmp_path: Path) -> None:
    root = tmp_path / "gv"
    root.mkdir()
    bad_sel = json.loads((FIXTURE / "single_selected_future_selection_v1.json").read_text())
    bad_sel["authority"]["MULTI_FUTURE_RUNTIME_AUTHORIZED"] = True
    (root / "single_selected_future_selection_v1.json").write_text(json.dumps(bad_sel))
    for rel in (
        "golden_vector_manifest_v1.json",
        "PRE_EXTERNAL_CONVERGENCE_REPORT.json",
        "lane_state/LANE_1/current_productive_sidestate_confirmation_cursor_v1.json",
        "lane_state/LANE_1/ddo_learning_capture_v1.jsonl",
    ):
        src = FIXTURE / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO,
        golden_vector_root=root,
        live_inputs_required=False,
    )
    sel = next(d for d in report.domains if d.domain == "SELECTION_BINDING")
    assert sel.status == "FAIL"
    assert report.structurally_startable is False


def test_positive_gge_finite_output() -> None:
    cursor = json.loads(
        (
            FIXTURE / "lane_state/LANE_1/current_productive_sidestate_confirmation_cursor_v1.json"
        ).read_text()
    )
    scope = cursor["existing_scope"]
    mag = float(scope["scope_band"])
    assert math.isfinite(mag) and mag > 0
