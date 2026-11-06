"""Actual private restart trust, journal corruption and malformed venue inputs."""

from copy import deepcopy
import json
from unittest.mock import MagicMock

import pytest

from src.ops.n1_whole_system_hard_facts_integration_wp_v1 import (
    private_observation_chain_v1 as private,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1 import (
    unified_recovery_orchestration_v1 as recovery,
)
from src.ops.okx_eea_private_account_state_runtime_v1 import runtime_orchestrator_v1 as runtime
from src.ops.okx_eea_private_account_state_runtime_v1.durable_store_v1 import (
    append_private_state_v1,
    default_private_store_paths_v1,
    load_all_private_state_v1,
    load_known_fill_trade_ids_v1,
    DurablePrivateStoreError,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    collect_rest_baseline_v1,
    PrivateRestBaselineError,
)
from src.ops.okx_eea_private_account_state_runtime_v1.reconciliation_v1 import (
    reconcile_rest_baseline_v1,
)
from tests.ops.test_okx_eea_private_account_state_runtime_v1 import _fixture_rest

STAMP = "2026-11-03T12:00:00Z"


def test_real_restored_position_conflict_cannot_be_reported_as_recovered(tmp_path, monkeypatch):
    paths = default_private_store_paths_v1(tmp_path / "private")
    append_private_state_v1(
        paths, {"fact_kind": "PositionStateV1", "instId": "ETH-USDT-SWAP", "pos": "9"}
    )
    proof = private.prove_private_observation_chain_v1(
        store_root=tmp_path / "private", rest_fetch_json=_fixture_rest
    )
    assert not proof.ok and not proof.private_ws_restart_safe
    assert not proof.private_observation_productive_join
    monkeypatch.setattr(
        recovery,
        "prove_composed_safety_chain_v1",
        lambda **_: pytest.fail("Untrusted state reached downstream readiness probes"),
    )
    result = recovery.execute_unified_recovery_orchestration_v1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        public_rest_fetch=lambda *a: {"code": "0", "data": []},
        private_rest_fetch=_fixture_rest,
    )
    assert result.ok is False and result.fail_closed_reason == "PRIVATE_RECONCILIATION_UNTRUSTED"
    assert "canonical_reconciliation" not in result.steps_completed
    assert "reservation_reconstruction" not in result.steps_completed


@pytest.mark.parametrize(
    "variant",
    [
        "trust_false",
        "trust_truthy",
        "boundary_false",
        "quality_unknown",
        "quality_missing",
        "quality_bad_shape",
        "required_missing",
    ],
)
def test_consumer_requires_explicit_consistent_trust(variant):
    record = {
        "trusted_current": True,
        "reconciliation": {
            "trusted_boundary_established": True,
            "quality": {"state": "CURRENT", "reconciliation_required": False},
        },
    }
    assert private.private_restart_reconciliation_trusted_v1(record) is True
    if variant == "trust_false":
        record["trusted_current"] = False
    elif variant == "trust_truthy":
        record["trusted_current"] = "true"
    elif variant == "boundary_false":
        record["reconciliation"]["trusted_boundary_established"] = False
    elif variant == "quality_unknown":
        record["reconciliation"]["quality"]["state"] = "UNKNOWN"
    elif variant == "quality_missing":
        record["reconciliation"].pop("quality")
    elif variant == "quality_bad_shape":
        record["reconciliation"]["quality"] = []
    elif variant == "required_missing":
        record["reconciliation"]["quality"].pop("reconciliation_required")
    assert private.private_restart_reconciliation_trusted_v1(record) is False


@pytest.mark.parametrize(
    "damage", ["payload", "digest", "schema", "raw_legacy", "truncated", "unterminated"]
)
def test_corrupt_private_journal_is_preserved_and_trust_invalidated(tmp_path, damage):
    paths = default_private_store_paths_v1(tmp_path)
    append_private_state_v1(
        paths, {"fact_kind": "PositionStateV1", "instId": "ETH-USDT-SWAP", "pos": "1"}
    )
    record = json.loads(paths.normalized_state.read_text())
    if damage == "payload":
        record["payload"]["pos"] = "99"
    elif damage == "digest":
        record["state_digest"] = "wrong"
    elif damage == "schema":
        record["schema_version"] = "unknown"
    elif damage == "raw_legacy":
        record = record["payload"]
    paths.normalized_state.write_text(
        "{broken"
        if damage == "truncated"
        else json.dumps(record) + ("" if damage == "unterminated" else "\n")
    )
    before = paths.normalized_state.read_bytes()
    instance = runtime.OkxEeaPrivateAccountStateRuntimeV1(
        tmp_path, _fixture_rest, trusted_current=True
    )
    with pytest.raises(DurablePrivateStoreError):
        instance.restore_durable_state_v1()
    assert instance.trusted_current is False
    assert paths.normalized_state.read_bytes() == before


@pytest.mark.parametrize(
    "endpoint,bad_data",
    [
        ("account/config", []),
        ("account/config", [{}]),
        ("account/balance", []),
        ("account/balance", [{"totalEq": "NaN", "details": [{"ccy": "USDT", "availEq": "2"}]}]),
        ("account/balance", [{"totalEq": "10", "details": []}]),
        ("account/positions", [None]),
        ("account/positions", [{"instId": "ETH-USDT-SWAP"}]),
        ("account/positions", [{"instId": "ETH-USDT-SWAP", "pos": "Infinity"}]),
        ("trade/orders-pending", [{"instId": "ETH-USDT-SWAP", "state": "live"}]),
        ("trade/orders-pending", [{"instId": "ETH-USDT-SWAP", "ordId": "1", "state": "unproven"}]),
        (
            "trade/fills",
            [{"instId": "ETH-USDT-SWAP", "tradeId": "t1", "fillSz": "0", "fillPx": "10"}],
        ),
        ("trade/fills", [{"instId": "ETH-USDT-SWAP", "tradeId": "t1", "fillSz": "1"}]),
    ],
)
def test_malformed_success_payload_never_establishes_current_state(tmp_path, endpoint, bad_data):
    def fetch(path, params):
        return (
            {"code": "0", "data": deepcopy(bad_data)}
            if path.endswith(endpoint)
            else _fixture_rest(path, params)
        )

    instance = runtime.OkxEeaPrivateAccountStateRuntimeV1(tmp_path, fetch, trusted_current=True)
    with pytest.raises(PrivateRestBaselineError):
        instance.run_rest_baseline_v1(captured_at=STAMP, recovery=True)
    assert instance.trusted_current is False
    assert load_all_private_state_v1(default_private_store_paths_v1(tmp_path)) == []


@pytest.mark.parametrize(
    "payload", [None, {}, {"code": "", "data": []}, {"code": "0", "data": [False]}]
)
def test_missing_success_or_malformed_envelope_is_rejected(payload):
    with pytest.raises(PrivateRestBaselineError):
        collect_rest_baseline_v1(lambda *a: payload, captured_at=STAMP, recovery=True)


@pytest.mark.parametrize(
    "position",
    [
        {"instId": "OTHER-USDT-SWAP", "pos": "1"},
        {"instId": "ETH-USDT-SWAP"},
        {"instId": "ETH-USDT-SWAP", "pos": "1", "posSide": "short"},
    ],
)
def test_missing_quantity_or_foreign_position_is_a_conflict(position):
    baseline = collect_rest_baseline_v1(_fixture_rest, captured_at=STAMP, recovery=True)
    result = reconcile_rest_baseline_v1(
        reconciliation_id="test", rest_baseline=baseline, ws_positions=[position]
    )
    assert result.trusted is False


def test_raw_order_state_matches_normalized_rest_but_foreign_instrument_does_not():
    baseline = collect_rest_baseline_v1(_fixture_rest, captured_at=STAMP, recovery=True)
    row = {"instId": "ETH-USDT-SWAP", "ordId": "1", "clOrdId": "c1", "state": "live"}
    assert (
        reconcile_rest_baseline_v1(
            reconciliation_id="test", rest_baseline=baseline, ws_orders=[row]
        ).trusted
        is True
    )
    row["instId"] = "OTHER-USDT-SWAP"
    assert (
        reconcile_rest_baseline_v1(
            reconciliation_id="test", rest_baseline=baseline, ws_orders=[row]
        ).trusted
        is False
    )


def test_fill_journal_prevents_duplicate_after_missing_or_corrupt_index(tmp_path):
    instance = runtime.OkxEeaPrivateAccountStateRuntimeV1(tmp_path, _fixture_rest)
    fill = {"fact_kind": "FillFactV1", "instId": "ETH-USDT-SWAP", "tradeId": "trade-1"}
    assert instance.persist_normalized_facts_v1([fill, fill]) == 1
    paths = default_private_store_paths_v1(tmp_path)
    paths.fill_dedup_index.unlink()
    assert load_known_fill_trade_ids_v1(paths) == {"trade-1"}
    restarted = runtime.OkxEeaPrivateAccountStateRuntimeV1(tmp_path, _fixture_rest)
    assert restarted.persist_normalized_facts_v1([fill]) == 0
    paths.fill_dedup_index.write_text("invalid rebuildable index")
    assert restarted.persist_normalized_facts_v1([fill]) == 0


def test_failed_reconciliation_persist_does_not_leave_trust_true(tmp_path, monkeypatch):
    instance = runtime.OkxEeaPrivateAccountStateRuntimeV1(
        tmp_path, _fixture_rest, trusted_current=True
    )
    baseline = collect_rest_baseline_v1(_fixture_rest, captured_at=STAMP, recovery=True)
    monkeypatch.setattr(
        runtime, "append_private_state_v1", MagicMock(side_effect=OSError("injected write failure"))
    )
    with pytest.raises(OSError):
        instance.reconcile_after_restore_or_ws_v1(reconciliation_id="test", rest_snapshot=baseline)
    assert instance.trusted_current is False


@pytest.mark.parametrize(
    "prior_kind", ["metadata", "position", "order", "balance", "unknown", "metadata_extra"]
)
def test_fresh_baseline_can_replace_only_known_pure_metadata(tmp_path, prior_kind):
    first = runtime.OkxEeaPrivateAccountStateRuntimeV1(tmp_path, _fixture_rest)
    assert first.restart_sequence_v1(captured_at=STAMP)["trusted_current"] is True
    paths = default_private_store_paths_v1(tmp_path)
    if prior_kind == "metadata_extra":
        record = dict(load_all_private_state_v1(paths)[0])
        record["unrecognized_state"] = {"position": "9"}
        append_private_state_v1(paths, record)
    elif prior_kind != "metadata":
        kind = {
            "position": "PositionStateV1",
            "order": "OrderSnapshotV1",
            "balance": "BalanceSnapshotV1",
            "unknown": "UnknownStateV1",
        }[prior_kind]
        append_private_state_v1(paths, {"fact_kind": kind})
    calls = []

    def fetch(path, params):
        calls.append(path)
        return _fixture_rest(path, params)

    restarted = runtime.OkxEeaPrivateAccountStateRuntimeV1(tmp_path, fetch)
    result = restarted.restart_sequence_v1(captured_at=STAMP)
    assert len(calls) == 6
    assert result["restored_economic_state_present"] is (prior_kind != "metadata")
    assert result["trusted_current"] is (prior_kind == "metadata")


def test_failed_websocket_reconnect_does_not_leave_readiness_true(tmp_path):
    transport = MagicMock()
    transport.connect_login_subscribe.side_effect = ConnectionError("injected disconnect")
    instance = runtime.OkxEeaPrivateAccountStateRuntimeV1(
        tmp_path, _fixture_rest, ws_transport=transport
    )
    with pytest.raises(ConnectionError):
        instance.restart_sequence_v1(captured_at=STAMP)
    assert instance.trusted_current is False


def test_append_cannot_join_new_record_onto_torn_journal_tail(tmp_path):
    paths = default_private_store_paths_v1(tmp_path)
    paths.normalized_state.parent.mkdir(parents=True)
    paths.normalized_state.write_text('{"unfinished":')
    before = paths.normalized_state.read_bytes()
    with pytest.raises(DurablePrivateStoreError):
        append_private_state_v1(paths, {"fact_kind": "FillFactV1", "tradeId": "test"})
    assert paths.normalized_state.read_bytes() == before
