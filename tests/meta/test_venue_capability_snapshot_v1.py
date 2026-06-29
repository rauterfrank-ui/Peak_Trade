"""Contract tests for venue_capability_snapshot_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.venue_capability_snapshot_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.venue_capability_snapshot_v1 import (
    ARTIFACT_REL,
    VENUE_CAPABILITY_SNAPSHOT_AUTHORITY_INVARIANTS,
    build_venue_capability_snapshot_v1,
    classify_venue_capability_drift_v1,
    compute_capability_digest,
    compute_source_digest,
    produce_venue_capability_snapshot_v1,
    reverify_venue_capability_snapshot_v1,
    serialize_venue_capability_snapshot_v1,
    venue_capability_input_to_dict,
)
from tests.meta.venue_capability_snapshot_v1_fixtures import (
    build_valid_venue_capability_input,
    produce_venue_capability_snapshot_fixture,
)

_NON_EXEC_FLAGS = (
    "adapter_invoked",
    "exchange_request_sent",
    "network_side_effect_created",
    "order_created",
    "order_submission_requested",
    "order_submitted",
    "order_cancel_requested",
    "order_amend_requested",
    "order_state_mutated",
    "position_state_mutated",
    "runtime_state_mutated",
    "execution_permission_created",
    "execution_permission_consumed",
    "submission_claim_executed",
    "new_orders_suspended",
    "execution_permissions_invalidated",
    "reconciliation_executed",
    "runtime_eligibility_revalidated",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.venue_capability_snapshot_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str = "venue_capability_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _build(**kwargs):
    input_data = build_valid_venue_capability_input(**kwargs)
    return build_venue_capability_snapshot_v1(input_data=input_data)


def _factor_ids(snapshot: dict) -> set[str]:
    return {str(item.get("factor_id")) for item in snapshot.get("blocking_facts", [])}


def _assert_non_execution(payload: dict) -> None:
    for flag in _NON_EXEC_FLAGS:
        assert payload.get(flag) is False, flag


def test_valid_full_futures_capability_snapshot() -> None:
    snapshot = _build()
    assert snapshot["snapshot_status"] == "VENUE_CAPABILITY_SNAPSHOT_VALID"
    assert snapshot["capability_digest"]
    assert snapshot["venue_capability_snapshot_complete"] is True


def test_deterministic_canonical_serialization() -> None:
    snapshot = _build()
    serialized = serialize_venue_capability_snapshot_v1(snapshot)
    assert serialized == deterministic_json_dumps(snapshot)
    assert '"snapshot_contract_name":"venue_capability_snapshot_v1"' in serialized


def test_identical_inputs_identical_snapshot_and_digest() -> None:
    first = _build()
    second = _build()
    assert first["capability_digest"] == second["capability_digest"]
    assert first["output_digest"] == second["output_digest"]


def test_input_order_does_not_affect_digest() -> None:
    payload = venue_capability_input_to_dict(build_valid_venue_capability_input())
    payload["supported_order_types"] = ["MARKET", "LIMIT"]
    payload["supported_time_in_force"] = ["IOC", "GTC"]
    payload["source_digest"] = compute_source_digest(payload)
    from src.meta.learning_loop.venue_capability_snapshot_v1 import parse_venue_capability_input

    first = build_venue_capability_snapshot_v1(input_data=parse_venue_capability_input(payload))
    payload["supported_order_types"] = ["LIMIT", "MARKET"]
    payload["supported_time_in_force"] = ["GTC", "IOC"]
    payload["source_digest"] = compute_source_digest(payload)
    second = build_venue_capability_snapshot_v1(input_data=parse_venue_capability_input(payload))
    assert first["capability_digest"] == second["capability_digest"]


def test_source_digest_mismatch_fail_closed() -> None:
    snapshot = _build(source_digest="tampered-source-digest")
    assert snapshot["snapshot_status"] == "VENUE_CAPABILITY_SNAPSHOT_INVALID"
    assert "SOURCE_DIGEST_MISMATCH" in _factor_ids(snapshot)


def test_missing_venue_fail_closed() -> None:
    snapshot = _build(venue="")
    assert snapshot["snapshot_status"] == "VENUE_CAPABILITY_SNAPSHOT_INVALID"
    assert "MISSING_VENUE" in _factor_ids(snapshot)


def test_missing_account_scope_fail_closed() -> None:
    snapshot = _build(account_scope="")
    assert "MISSING_ACCOUNT_SCOPE" in _factor_ids(snapshot)


def test_missing_instrument_fail_closed() -> None:
    snapshot = _build(instrument="")
    assert "MISSING_INSTRUMENT" in _factor_ids(snapshot)


def test_missing_market_type_fail_closed() -> None:
    snapshot = _build(market_type="")
    assert "MISSING_MARKET_TYPE" in _factor_ids(snapshot)


@pytest.mark.parametrize("market_type", ["SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"])
def test_spot_and_synthetic_spot_fail_closed(market_type: str) -> None:
    snapshot = _build(market_type=market_type)
    assert snapshot["snapshot_status"] == "VENUE_CAPABILITY_SNAPSHOT_INVALID"
    assert "FORBIDDEN_MARKET_TYPE" in _factor_ids(snapshot)


def test_unknown_market_type_fail_closed() -> None:
    snapshot = _build(market_type="OPTIONS")
    assert "UNKNOWN_MARKET_TYPE" in _factor_ids(snapshot)


def test_missing_contract_type_fail_closed() -> None:
    snapshot = _build(contract_type="")
    assert "MISSING_CONTRACT_TYPE" in _factor_ids(snapshot)


@pytest.mark.parametrize(
    "field,value",
    [
        ("contract_multiplier", ""),
        ("contract_multiplier", "-1"),
        ("contract_multiplier", "NaN"),
        ("contract_multiplier", "Infinity"),
        ("tick_size", "0"),
        ("tick_size", "-0.01"),
        ("lot_size", "0"),
        ("lot_size", "-0.001"),
        ("maximum_order_size", "0"),
        ("maximum_order_size", "-1"),
        ("leverage_cap", "0"),
        ("leverage_cap", "-5"),
    ],
)
def test_invalid_numeric_fields_fail_closed(field: str, value: str) -> None:
    snapshot = _build(**{field: value})
    assert snapshot["snapshot_status"] == "VENUE_CAPABILITY_SNAPSHOT_INVALID"


def test_unknown_position_mode_fail_closed() -> None:
    snapshot = _build(position_mode="TRIPLE_HEDGE")
    assert "UNKNOWN_POSITION_MODE" in _factor_ids(snapshot)


def test_unknown_margin_mode_fail_closed() -> None:
    snapshot = _build(margin_mode="PORTFOLIO")
    assert "UNKNOWN_MARGIN_MODE" in _factor_ids(snapshot)


def test_empty_order_type_list_fail_closed() -> None:
    snapshot = _build(supported_order_types=[])
    assert "INVALID_SUPPORTED_ORDER_TYPES" in _factor_ids(snapshot)


def test_unknown_order_type_fail_closed() -> None:
    snapshot = _build(supported_order_types=["STOP"])
    assert "UNKNOWN_ORDER_TYPE" in _factor_ids(snapshot)


def test_unknown_time_in_force_fail_closed() -> None:
    snapshot = _build(supported_time_in_force=["GTD"])
    assert "UNKNOWN_TIME_IN_FORCE" in _factor_ids(snapshot)


def test_unclear_reduce_only_semantics_fail_closed() -> None:
    snapshot = _build(reduce_only_semantics="")
    assert "MISSING_REDUCE_ONLY_SEMANTICS" in _factor_ids(snapshot)


def test_identical_digests_no_drift() -> None:
    baseline = _build()
    candidate = _build()
    drift = classify_venue_capability_drift_v1(
        baseline_snapshot=baseline,
        candidate_snapshot=candidate,
        baseline_snapshot_ref="baseline.json",
        candidate_snapshot_ref="candidate.json",
    )
    assert drift["drift_classification"] == "NO_DRIFT"
    assert drift["capability_digest_changed"] is False
    assert drift["actions_executed"] is False


def test_capability_change_detected_as_breaking_drift() -> None:
    baseline = _build()
    candidate = _build(leverage_cap="10")
    drift = classify_venue_capability_drift_v1(
        baseline_snapshot=baseline,
        candidate_snapshot=candidate,
        baseline_snapshot_ref="baseline.json",
        candidate_snapshot_ref="candidate.json",
    )
    assert drift["drift_classification"] == "BREAKING_DRIFT"
    assert drift["capability_digest_changed"] is True
    assert drift["suspend_new_orders_required"] is True
    assert drift["invalidate_unused_execution_permissions_required"] is True
    assert drift["reconciliation_required"] is True
    assert drift["runtime_eligibility_revalidation_required"] is True


def test_drift_does_not_execute_actions() -> None:
    baseline = _build()
    candidate = _build(tick_size="0.05")
    drift = classify_venue_capability_drift_v1(
        baseline_snapshot=baseline,
        candidate_snapshot=candidate,
        baseline_snapshot_ref="baseline.json",
        candidate_snapshot_ref="candidate.json",
    )
    _assert_non_execution(drift)
    assert drift["actions_executed"] is False


def test_invalid_snapshot_drift_classification() -> None:
    baseline = _build(venue="")
    candidate = _build()
    drift = classify_venue_capability_drift_v1(
        baseline_snapshot=baseline,
        candidate_snapshot=candidate,
        baseline_snapshot_ref="baseline.json",
        candidate_snapshot_ref="candidate.json",
    )
    assert drift["drift_classification"] == "INVALID_SNAPSHOT"


def test_produce_bundle_manifest_and_reverify(tmp_path) -> None:
    fixture = produce_venue_capability_snapshot_fixture(
        tmp_path,
        _durable_output(tmp_path),
        produce_output=True,
    )
    assert fixture.snapshot_bundle_dir is not None
    ok, _msg = verify_manifest_sha256(fixture.snapshot_bundle_dir)
    assert ok
    reverify_venue_capability_snapshot_v1(output_dir=fixture.snapshot_bundle_dir)
    snapshot = (fixture.snapshot_bundle_dir / ARTIFACT_REL).read_text(encoding="utf-8")
    assert '"snapshot_status":"VENUE_CAPABILITY_SNAPSHOT_VALID"' in snapshot


def test_authority_invariants_present() -> None:
    snapshot = _build()
    assert snapshot["authority_invariants"] == VENUE_CAPABILITY_SNAPSHOT_AUTHORITY_INVARIANTS


def test_capability_digest_matches_normalized_body() -> None:
    snapshot = _build()
    assert snapshot["capability_digest"] == compute_capability_digest(snapshot)


def test_non_execution_flags_on_valid_snapshot() -> None:
    snapshot = _build()
    _assert_non_execution(snapshot)
