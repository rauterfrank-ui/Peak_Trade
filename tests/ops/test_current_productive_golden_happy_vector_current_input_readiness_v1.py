"""CURRENT productive GHV input observation adapter + live readiness evaluator tests."""

from __future__ import annotations

import json
import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_golden_happy_vector_current_input_observation_adapter_v1 import (
    CLASS_CURRENT_MISSING,
    FORBIDDEN_SOURCE_FIXTURE_REPLAY,
    SOURCE_INJECTED_TRANSPORT,
    build_fixture_vs_current_gap_matrix_v1,
    observe_current_productive_ghv_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_golden_happy_vector_startability_evaluator_v1 import (
    evaluate_current_productive_golden_happy_vector_startability_v1,
    report_to_machine_json_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)
from tests.ops.test_current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    _mark_row,
)

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1"
NATIVE = "API3-USDT-SWAP"


@dataclass
class _FakeGetResult:
    get_performed: bool
    payload: dict[str, Any] | None


class _FakeTransport:
    def __init__(self, responses: deque[tuple[str, _FakeGetResult]]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    ) -> _FakeGetResult:
        del auth_required, pretrade_decision_id, get_cache_policy
        self.calls.append(endpoint)
        if not self._responses:
            return _FakeGetResult(get_performed=False, payload=None)
        expected_prefix, result = self._responses.popleft()
        assert endpoint.startswith(expected_prefix) or expected_prefix in endpoint
        return result


def _mark_history_payload() -> dict[str, Any]:
    rows = list(reversed([_mark_row(i, px=f"{0.30 + i * 0.0001:.6f}") for i in range(61)]))
    return {"code": "0", "msg": "", "data": rows}


def _seed_productivity(tmp_path: Path) -> Path:
    prod = tmp_path / "productivity"
    sel_dir = prod / "runtime_state/selection"
    sel_dir.mkdir(parents=True)
    shutil.copy(
        FIXTURE / "single_selected_future_selection_v1.json",
        sel_dir / "single_selected_future_selection_v1.json",
    )
    return prod


def test_offline_gap_matrix_marks_live_fields_missing() -> None:
    manifest = json.loads((FIXTURE / "golden_vector_manifest_v1.json").read_text())
    rows = build_fixture_vs_current_gap_matrix_v1(manifest=manifest, observation=None)
    by_field = {r.field_id: r for r in rows}
    assert by_field["mark_price"].classification == CLASS_CURRENT_MISSING
    assert by_field["volatility_estimate"].classification == CLASS_CURRENT_MISSING


def test_fixture_masquerade_fail_closed() -> None:
    obs = observe_current_productive_ghv_inputs_v1(
        productivity_root=Path("/nonexistent"),
        evidence_store_root=Path("/tmp"),
        transport=_FakeTransport(deque()),
        source_kind=FORBIDDEN_SOURCE_FIXTURE_REPLAY,
    )
    assert obs.observation_ok is False
    assert obs.current_input_blocker == "FIXTURE_CANNOT_MASQUERADE_AS_CURRENT"


def test_live_observation_mock_transport_current_input_ready(tmp_path: Path) -> None:
    prod = _seed_productivity(tmp_path)
    mark = okx_public_mark_price_payload_v1(native_id=NATIVE, mark_px=0.3403)
    transport = _FakeTransport(
        deque(
            [
                (ENDPOINT_PUBLIC_MARK_PRICE, _FakeGetResult(True, mark)),
                (
                    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
                    _FakeGetResult(True, _mark_history_payload()),
                ),
            ]
        )
    )
    obs = observe_current_productive_ghv_inputs_v1(
        productivity_root=prod,
        evidence_store_root=tmp_path / "g17",
        transport=transport,
        source_kind=SOURCE_INJECTED_TRANSPORT,
        expected_instrument_id=str(
            json.loads((FIXTURE / "golden_vector_manifest_v1.json").read_text())["INSTRUMENT_ID"]
        ),
        expected_native_id=NATIVE,
    )
    assert obs.observation_ok is True
    assert obs.gge_current_input_valid is True
    assert obs.current_input_provenance_valid is True
    assert obs.current_selection_binding_valid is True
    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO,
        golden_vector_root=FIXTURE,
        live_inputs_required=True,
        current_input_observation=obs,
    )
    assert report.current_input_ready is True
    assert report.golden_vector_replay_valid is True
    payload = report_to_machine_json_v1(report)
    assert payload["GGE_CURRENT_INPUT_VALID"] is True
    assert payload["CURRENT_INPUT_READY"] is True


def test_wrong_native_id_binding_fail_closed(tmp_path: Path) -> None:
    prod = _seed_productivity(tmp_path)
    transport = _FakeTransport(deque())
    obs = observe_current_productive_ghv_inputs_v1(
        productivity_root=prod,
        evidence_store_root=tmp_path / "g17",
        transport=transport,
        source_kind=SOURCE_INJECTED_TRANSPORT,
        expected_native_id="OTHER-USDT-SWAP",
    )
    assert obs.observation_ok is False
    assert obs.current_input_blocker == "CURRENT_NATIVE_ID_BINDING_MISMATCH"


def test_live_inputs_required_without_observation_not_ready() -> None:
    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO,
        golden_vector_root=FIXTURE,
        live_inputs_required=True,
        current_input_observation=None,
    )
    assert report.current_input_ready is False
    assert report.current_input_blocker == "LIVE_CURRENT_INPUT_OBSERVATION_MISSING"


def test_offline_fixture_ghv_regression_unchanged() -> None:
    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO,
        golden_vector_root=FIXTURE,
        live_inputs_required=False,
    )
    assert report.golden_vector_replay_valid is True
    assert report.current_input_ready is False


def test_stale_mark_fail_closed(tmp_path: Path) -> None:
    prod = _seed_productivity(tmp_path)
    mark = okx_public_mark_price_payload_v1(native_id=NATIVE, mark_px=0.3403)
    transport = _FakeTransport(
        deque(
            [
                (ENDPOINT_PUBLIC_MARK_PRICE, _FakeGetResult(True, mark)),
                (
                    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
                    _FakeGetResult(True, _mark_history_payload()),
                ),
            ]
        )
    )
    obs = observe_current_productive_ghv_inputs_v1(
        productivity_root=prod,
        evidence_store_root=tmp_path / "g17",
        transport=transport,
        source_kind=SOURCE_INJECTED_TRANSPORT,
        fresh_mark_max_age_seconds=-1.0,
        expected_native_id=NATIVE,
    )
    assert obs.current_input_freshness_valid is False
    assert obs.observation_ok is False
    assert obs.current_input_blocker == "CURRENT_MARK_STALE"
