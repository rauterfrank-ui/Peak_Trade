"""Contract tests for STEP29M post-selection dynamic instrument binding v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest import step29m_current_single_selected_future_dynamic_binding_v1 as binding
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    STATE_NO_SELECTION,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import write_manifest


def _eth_selection(*, state: str = STATE_SELECTED_ACTIVE) -> SingleSelectedFutureSelectionV1:
    base = SingleSelectedFutureSelectionV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        selection_id="ssf_test_eth",
        instrument_id="okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap",
        venue_native_id="ETH-USDT-SWAP",
        ranking_snapshot_id="pfr_test",
        ranking_integrity_digest="abc123",
        ranking_event_time="2026-09-16T00:00:00Z",
        selected_at_event_time="2026-09-16T00:00:00Z",
        selected_at_wall_time="2026-09-16T00:00:01Z",
        valid_from="2026-09-16T00:00:00Z",
        valid_until="2099-01-01T00:00:00Z",
        policy_version="v1",
        policy_id="single_selected_future_policy_v1",
        config_digest="cfg",
        repository_sha="sha",
        reason_codes=("INITIAL_SELECTION",),
        state=state,
        integrity_digest="",
        single_selected_future=True,
        multi_future_runtime_authorized=False,
    )
    return base.with_integrity_digest()


def _0g_selection() -> SingleSelectedFutureSelectionV1:
    base = SingleSelectedFutureSelectionV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        selection_id="ssf_test_0g",
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        venue_native_id="0G-USDT-SWAP",
        ranking_snapshot_id="pfr_test_0g",
        ranking_integrity_digest="def456",
        ranking_event_time="2026-09-16T00:00:00Z",
        selected_at_event_time="2026-09-16T00:00:00Z",
        selected_at_wall_time="2026-09-16T00:00:01Z",
        valid_from="2026-09-16T00:00:00Z",
        valid_until="2099-01-01T00:00:00Z",
        policy_version="v1",
        policy_id="single_selected_future_policy_v1",
        config_digest="cfg",
        repository_sha="sha",
        reason_codes=("INITIAL_SELECTION",),
        state=STATE_SELECTED_ACTIVE,
        integrity_digest="",
        single_selected_future=True,
        multi_future_runtime_authorized=False,
    )
    return base.with_integrity_digest()


def _persist_selection(root: Path, selection: SingleSelectedFutureSelectionV1) -> None:
    root.mkdir(parents=True, exist_ok=True)
    from src.ops.single_selected_future_policy_v1.constants_v1 import (  # noqa: PLC0415
        EVIDENCE_FILENAME,
        SELECTION_FILENAME,
    )

    (root / SELECTION_FILENAME).write_text(
        json.dumps(selection.to_dict(), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / EVIDENCE_FILENAME).write_text("{}\n", encoding="utf-8")
    write_manifest(root, (SELECTION_FILENAME, EVIDENCE_FILENAME))


ROOT = Path(__file__).resolve().parents[2]


def test_eth_explicit_binding_from_post_selection_output(tmp_path: Path) -> None:
    _persist_selection(tmp_path, _eth_selection())
    resolved = binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(
        tmp_path,
        require_manifest=True,
    )
    assert resolved.native_instrument_id == "ETH-USDT-SWAP"
    assert resolved.canonical_instrument_id.endswith("eth-usdt-swap")
    assert resolved.consumption_class == "POST_SELECTION_OUTPUT_ONLY"


def test_non_eth_selected_future_binding(tmp_path: Path) -> None:
    _persist_selection(tmp_path, _0g_selection())
    resolved = binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(tmp_path)
    assert resolved.native_instrument_id == "0G-USDT-SWAP"
    assert "0g-usdt-swap" in resolved.canonical_instrument_id


def test_missing_selection_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(binding.Step29mDynamicBindingError, match="SELECTION_LOAD_FAILED"):
        binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(tmp_path)


def test_no_selection_state_fail_closed(tmp_path: Path) -> None:
    _persist_selection(tmp_path, _eth_selection(state=STATE_NO_SELECTION))
    with pytest.raises(binding.Step29mDynamicBindingError, match="SELECTION_NOT_ACTIVE"):
        binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(tmp_path)


def test_stale_selection_fail_closed(tmp_path: Path) -> None:
    stale = _eth_selection()
    payload = stale.to_dict()
    payload["valid_until"] = "2020-01-01T00:00:00Z"
    stale_sel = SingleSelectedFutureSelectionV1.from_dict(payload).with_integrity_digest()
    _persist_selection(tmp_path, stale_sel)
    with pytest.raises(binding.Step29mDynamicBindingError, match="SELECTION_STALE"):
        binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(
            tmp_path,
            observed_at_unix=1_700_000_000.0,
        )


def test_identity_mismatch_fail_closed(tmp_path: Path) -> None:
    bad = _eth_selection()
    bad = bad.with_integrity_digest()
    payload = bad.to_dict()
    payload["venue_native_id"] = "SOL-USDT-SWAP"
    broken = SingleSelectedFutureSelectionV1.from_dict(payload).with_integrity_digest()
    _persist_selection(tmp_path, broken)
    with pytest.raises(binding.Step29mDynamicBindingError, match="SELECTION_IDENTITY_MISMATCH"):
        binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(tmp_path)


def test_ranking_snapshot_alone_is_insufficient(tmp_path: Path) -> None:
    ranking_only = tmp_path / "ranking"
    ranking_only.mkdir()
    (ranking_only / "productive_futures_ranking_snapshot_v1.json").write_text(
        json.dumps(
            {
                "ranked_candidates": [
                    {
                        "canonical_instrument_id": "okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap",
                        "venue_native_id": "ETH-USDT-SWAP",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(binding.Step29mDynamicBindingError):
        binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(ranking_only)


def test_evaluation_config_overlay_removes_frozen_digests(tmp_path: Path) -> None:
    instrument = binding.resolve_step29m_instrument_binding_from_selection_state_root_v1(
        _write_eth_state(tmp_path)
    )
    template = binding.resolve_evaluation_config_template_path_v1(ROOT)
    cfg = binding.materialize_step29m_evaluation_config_for_instrument_binding_v1(
        instrument,
        template_config_path=template,
        dataset_path="/tmp/bars.parquet",
        dataset_manifest_path="/tmp/dataset_manifest.json",
    )
    section = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert section["native_instrument_id"] == "ETH-USDT-SWAP"
    assert "expected_dataset_digest" not in section
    assert "expected_manifest_digest" not in section
    assert cfg["economic_evaluation_v1"]["walk_forward"]["train_bars"] == 4320


def _write_eth_state(root: Path) -> Path:
    _persist_selection(root, _eth_selection())
    return root


def test_contract_config_declares_no_step29m_selection_authority() -> None:
    payload = binding.load_contract_config_v1()
    assert payload["step29m_selection_authority"] is False
    assert payload["ranking_universe_consumption_forbidden"] is True
