"""Explicit state propagation; no empty-book fallback or observation authority."""

import argparse
import ast
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1, PositionTruthV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_portfolio_document_v1 import (
    add_startup_portfolio_arguments_v1, read_startup_portfolio_document_v1,
    startup_observation_now_v1,
)

REPO = Path(__file__).resolve().parents[2]
NOW = 1_700_000_000.0


def _document():
    return {
        "schema": "peaktrade.startup_portfolio_observation.v1",
        "account_identity": "synthetic-startup-account", "instrument_type": "SWAP",
        "complete_account_scope": True, "pending_orders": False,
        "source_id": "explicit-synthetic-account-observer",
        "event_time_unix": NOW - 1, "wall_time_unix": NOW,
        "positions": [],
    }


def _read(tmp_path, data):
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(data))
    return read_startup_portfolio_document_v1(path, expected_account_identity="synthetic-startup-account", now_unix=NOW)


def test_explicit_empty_book_and_signed_open_position_are_distinct(tmp_path):
    assert _read(tmp_path, _document()).positions == ()
    data = _document()
    data["positions"] = [{"instrument_id": "inst-eth-usdt-perp", "signed_quantity": "-2.5", "side": "SHORT"}]
    snapshot = _read(tmp_path, data)
    assert len(snapshot.positions) == 1
    assert snapshot.positions[0].signed_quantity == Decimal("-2.5")
    assert snapshot.positions[0].side == "SHORT"
    assert snapshot.source_id == data["source_id"]
    assert snapshot.event_time_unix == data["event_time_unix"]


@pytest.mark.parametrize(("field", "value"), [
    ("schema", "unknown"), ("account_identity", "different-account"),
    ("instrument_type", "SPOT"), ("complete_account_scope", False),
    ("complete_account_scope", "true"), ("pending_orders", True),
    ("pending_orders", "false"), ("source_id", ""),
    ("event_time_unix", NOW - 6), ("event_time_unix", NOW + 1),
    ("event_time_unix", True), ("event_time_unix", float("nan")),
    ("wall_time_unix", NOW + 1), ("positions", None),
])
def test_bad_or_incomplete_account_documents_never_become_flat(tmp_path, field, value):
    data = _document()
    data[field] = value
    with pytest.raises(ValueError):
        _read(tmp_path, data)


@pytest.mark.parametrize("field", list(_document()))
def test_missing_observation_field_has_no_default(tmp_path, field):
    data = _document()
    del data[field]
    with pytest.raises(ValueError):
        _read(tmp_path, data)


@pytest.mark.parametrize("row", [
    {}, {"instrument_id": "x", "signed_quantity": "NaN", "side": "FLAT"},
    {"instrument_id": "x", "signed_quantity": True, "side": "LONG"},
    {"instrument_id": "x", "signed_quantity": "-1", "side": "LONG"},
    {"instrument_id": " x", "signed_quantity": "1", "side": "LONG"},
    {"instrument_id": "x", "signed_quantity": "1", "side": "LONG", "unknown": 1},
])
def test_invalid_position_identity_quantity_and_side_are_rejected(tmp_path, row):
    data = _document()
    data["positions"] = [row]
    with pytest.raises(ValueError):
        _read(tmp_path, data)


def test_duplicate_fields_and_duplicate_positions_are_rejected(tmp_path):
    data = _document()
    row = {"instrument_id": "x", "signed_quantity": "1", "side": "LONG"}
    data["positions"] = [row, row]
    with pytest.raises(ValueError, match="POSITION_ID_INVALID"):
        _read(tmp_path, data)
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema":"a","schema":"b"}')
    with pytest.raises(ValueError, match="DUPLICATE_FIELD"):
        read_startup_portfolio_document_v1(path, expected_account_identity="synthetic-startup-account", now_unix=NOW)


def test_offline_clock_is_only_available_when_explicitly_added():
    production = argparse.ArgumentParser()
    add_startup_portfolio_arguments_v1(production)
    with pytest.raises(SystemExit):
        production.parse_args(["--startup-portfolio", "unused", "--expected-account-identity", "x", "--startup-observation-unix", "0"])
    offline = argparse.ArgumentParser()
    add_startup_portfolio_arguments_v1(offline, replay_clock=True)
    args = offline.parse_args(["--startup-portfolio", "unused", "--expected-account-identity", "x", "--startup-observation-unix", "0"])
    assert startup_observation_now_v1(args) == 0


def test_preflight_forwards_same_nonflat_snapshot_without_replacing_it(tmp_path, monkeypatch):
    from decimal import Decimal
    import src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 as module

    snapshot = PortfolioTruthSnapshotV1(
        positions=(PositionTruthV1.from_signed(instrument_id="held", signed_quantity=Decimal("3")),),
        source_id="explicit-offline-source", event_time_unix=NOW, wall_time_unix=NOW,
    )
    class StoppedAfterObservedHandoff(Exception):
        pass

    def handoff(**kwargs):
        assert kwargs["observed_portfolio"] is snapshot
        assert kwargs["observation_now_unix"] == NOW
        raise StoppedAfterObservedHandoff

    monkeypatch.setattr(module, "acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1", handoff)
    kwargs = dict(productivity_root=tmp_path / "prod", lane_state_root=tmp_path / "lane", repository_sha="a" * 40, binding_epoch="2023-11-14T22:13:20Z", authorization_native_id="ETH-USDT-SWAP")
    with pytest.raises(ValueError, match="OBSERVED_PORTFOLIO_REQUIRED"):
        module.preflight_current_productive_persistent_natural_enter_v1(**kwargs)
    with pytest.raises(StoppedAfterObservedHandoff):
        module.preflight_current_productive_persistent_natural_enter_v1(**kwargs, observed_portfolio=snapshot, observation_now_unix=NOW)
    assert list(tmp_path.iterdir()) == []


def test_seven_original_direct_calls_forward_explicit_observation():
    filenames = [
        "src/governance/pre_live_fresh_state_and_slice_baseline_convergence_v1.py",
        "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_one_shot_enter_e2e_runtime_handoff_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py",
        "scripts/ops/run_current_productive_full_core_pre_external_closure_v1.py",
        "scripts/ops/run_golden_happy_natural_data_offline_witness_adjudication_v1.py",
        "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py",
    ]
    found = []
    for filename in filenames:
        tree = ast.parse((REPO / filename).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1":
                keywords = {k.arg: k.value for k in node.keywords}
                assert isinstance(keywords["observed_portfolio"], ast.Name)
                assert keywords["observed_portfolio"].id == "observed_portfolio"
                assert "observation_now_unix" in keywords
                found.append((filename, node.lineno))
    assert len(found) == 7
