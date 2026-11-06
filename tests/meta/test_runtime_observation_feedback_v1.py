"""Contract tests for runtime_observation_feedback_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.runtime_observation_feedback_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    COMPARISON_INPUT_ARTIFACT_REL,
    LEARNING_INPUT_ARTIFACT_REL,
    OBSERVATION_ARTIFACT_REL,
    RUNTIME_OBSERVATION_FEEDBACK_AUTHORITY_INVARIANTS,
    RuntimeObservationFeedbackError,
    build_runtime_observation_bundle_v1,
    build_runtime_performance_comparison_input_v1,
    build_runtime_to_learning_input_v1,
    default_runtime_observation_bundle_input,
    produce_runtime_observation_bundle_v1,
    produce_runtime_performance_comparison_input_v1,
    produce_runtime_to_learning_input_v1,
    reverify_runtime_observation_bundle_v1,
    reverify_runtime_performance_comparison_input_v1,
    reverify_runtime_to_learning_input_v1,
    serialize_runtime_observation_bundle_v1,
    verify_source_evidence_bundle,
)
from tests.meta.runtime_observation_feedback_v1_fixtures import (
    build_valid_comparison_request,
    build_valid_learning_request,
    build_valid_observation_input,
    minimal_invalid_digest,
    missing_binding,
    produce_full_chain_fixtures,
    produce_source_evidence_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.runtime_observation_feedback_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


# --- Contract A: runtime_observation_bundle_v1 ---


def test_observation_happy_path_complete() -> None:
    contract = build_runtime_observation_bundle_v1()
    assert contract["observation_status"] == "COMPLETE"
    assert contract["decision_code"] == "COMPLETE"
    assert contract["offline_projection_only"] is True
    assert contract["real_runtime_observation"] is False
    assert contract["learning_authorized"] is False


def test_observation_deterministic_repeat() -> None:
    request = default_runtime_observation_bundle_input()
    assert build_runtime_observation_bundle_v1(request) == build_runtime_observation_bundle_v1(
        request
    )


def test_observation_canonical_json_stability() -> None:
    contract = build_runtime_observation_bundle_v1()
    assert serialize_runtime_observation_bundle_v1(contract) == deterministic_json_dumps(contract)


def test_observation_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "observation_out")
    produce_runtime_observation_bundle_v1(
        request=default_runtime_observation_bundle_input(),
        output_dir=out,
    )
    verified = reverify_runtime_observation_bundle_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["observation_status"] == "COMPLETE"


def test_observation_source_manifest_verified(tmp_path: Path) -> None:
    source = produce_source_evidence_bundle(tmp_path)
    digest = verify_source_evidence_bundle(source)
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(
            source_evidence_bundle_dir=str(source),
            source_manifest_digest=digest,
        )
    )
    assert contract["observation_status"] == "COMPLETE"


def test_observation_rejects_missing_source_manifest(tmp_path: Path) -> None:
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(
            source_evidence_bundle_dir=str(tmp_path / "missing"),
            source_manifest_digest=minimal_invalid_digest(),
        )
    )
    assert contract["observation_status"] == "INVALID"


def test_observation_rejects_digest_mismatch(tmp_path: Path) -> None:
    source = produce_source_evidence_bundle(tmp_path)
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(
            source_evidence_bundle_dir=str(source),
            source_manifest_digest=minimal_invalid_digest(),
        )
    )
    assert contract["observation_status"] == "INVALID"
    assert "SOURCE_DIGEST_MISMATCH" in contract["blocking_reasons"]


def test_observation_incomplete_when_bindings_missing() -> None:
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(
            order_evidence=missing_binding(),
            fill_evidence=missing_binding(),
            position_evidence=missing_binding(),
            pnl_evidence=missing_binding(),
            reconciliation_event=missing_binding(),
        )
    )
    assert contract["observation_status"] == "INCOMPLETE"


@pytest.mark.parametrize(
    ("market_type", "expected_code"),
    [
        ("SPOT", "SPOT_MARKET_TYPE_REJECTED"),
        ("SYNTHETIC_SPOT", "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED"),
        ("UNKNOWN", "UNKNOWN_MARKET_TYPE_REJECTED"),
        ("", "MISSING_MARKET_TYPE_REJECTED"),
    ],
)
def test_observation_rejects_non_futures_market(market_type: str, expected_code: str) -> None:
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(market_type=market_type)
    )
    assert contract["observation_status"] == "INVALID"
    assert contract["decision_code"] == expected_code


def test_observation_rejects_bitcoin_instrument() -> None:
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(instrument="BTC-USDT-SWAP")
    )
    assert contract["observation_status"] == "INVALID"
    assert contract["decision_code"] == "BITCOIN_INSTRUMENT_REJECTED"


def test_observation_rejects_epoch_mismatch() -> None:
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(trading_epoch=2, executor_epoch=3)
    )
    assert contract["observation_status"] == "INVALID"
    assert contract["decision_code"] == "SESSION_EPOCH_MISMATCH"


def test_observation_rejects_real_runtime_request() -> None:
    contract = build_runtime_observation_bundle_v1(
        build_valid_observation_input(real_runtime_observation_requested=True)
    )
    assert contract["observation_status"] == "INVALID"


# --- Contract B: runtime_to_learning_input_v1 ---


def test_learning_input_happy_path() -> None:
    contract = build_runtime_to_learning_input_v1()
    assert contract["learning_input_status"] == "VALID"
    assert contract["is_learning_input"] is True
    assert contract["learning_input_does_not_train"] is True
    assert contract["learning_input_does_not_promote"] is True
    assert contract["learning_input_does_not_authorize_runtime"] is True


def test_learning_input_deterministic_repeat() -> None:
    request = build_valid_learning_request()
    assert build_runtime_to_learning_input_v1(request) == build_runtime_to_learning_input_v1(
        request
    )


def test_learning_input_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "learning_out")
    produce_runtime_to_learning_input_v1(request=build_valid_learning_request(), output_dir=out)
    verified = reverify_runtime_to_learning_input_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["learning_input_status"] == "VALID"


def test_learning_input_rejects_digest_mismatch() -> None:
    contract = build_runtime_to_learning_input_v1(
        build_valid_learning_request(source_observation_digest=minimal_invalid_digest())
    )
    assert contract["learning_input_status"] == "INVALID"
    assert contract["decision_code"] == "SOURCE_OBSERVATION_DIGEST_MISMATCH"


def test_learning_input_rejects_incomplete_observation() -> None:
    incomplete_obs = build_runtime_observation_bundle_v1(
        build_valid_observation_input(order_evidence=missing_binding())
    )
    contract = build_runtime_to_learning_input_v1(
        build_valid_learning_request(
            source_observation_body=incomplete_obs,
            source_observation_digest=str(incomplete_obs["output_digest"]),
            source_observation_status=str(incomplete_obs["observation_status"]),
        )
    )
    assert contract["learning_input_status"] == "INCOMPLETE"


def test_learning_input_does_not_authorize_training() -> None:
    contract = build_runtime_to_learning_input_v1(
        build_valid_learning_request(learning_training_requested=True)
    )
    assert contract["learning_input_status"] == "INVALID"
    assert contract["decision_code"] == "LEARNING_TRAINING_REQUESTED"


# --- Contract C: runtime_performance_comparison_input_v1 ---


def test_comparison_input_happy_path_ready() -> None:
    contract = build_runtime_performance_comparison_input_v1()
    assert contract["comparison_readiness_status"] == "READY"
    assert contract["comparison_not_executed"] is True
    assert contract["winner_not_selected"] is True
    assert contract["candidate_not_selected"] is True
    assert contract["promotion_not_authorized"] is True


def test_comparison_input_deterministic_repeat() -> None:
    request = build_valid_comparison_request()
    first = build_runtime_performance_comparison_input_v1(request)
    second = build_runtime_performance_comparison_input_v1(request)
    assert first == second
    assert first["output_digest"] == second["output_digest"]


def test_comparison_input_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "comparison_out")
    produce_runtime_performance_comparison_input_v1(
        request=build_valid_comparison_request(),
        output_dir=out,
    )
    verified = reverify_runtime_performance_comparison_input_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["comparison_readiness_status"] == "READY"


def test_comparison_input_not_ready_without_reconciliation() -> None:
    contract = build_runtime_performance_comparison_input_v1(
        build_valid_comparison_request(reconciliation_quality_refs=())
    )
    assert contract["comparison_readiness_status"] == "NOT_READY"
    assert "RECONCILIATION_EVIDENCE_INCOMPLETE" in contract["comparison_readiness_reasons"]


def test_comparison_input_rejects_digest_mismatch() -> None:
    contract = build_runtime_performance_comparison_input_v1(
        build_valid_comparison_request(runtime_learning_input_digest=minimal_invalid_digest())
    )
    assert contract["comparison_readiness_status"] == "NOT_READY"
    assert contract["decision_code"] == "LEARNING_INPUT_DIGEST_MISMATCH"


def test_comparison_does_not_execute_or_select_winner() -> None:
    contract = build_runtime_performance_comparison_input_v1(
        build_valid_comparison_request(comparison_execution_requested=True)
    )
    assert contract["comparison_readiness_status"] == "NOT_READY"
    assert contract["decision_code"] == "COMPARISON_EXECUTION_REQUESTED"


# --- Chain, authority, reuse ---


def test_full_offline_chain_same_digests_on_repeat(tmp_path: Path) -> None:
    obs1, learning1, comparison1 = produce_full_chain_fixtures(tmp_path / "run1")
    obs2, learning2, comparison2 = produce_full_chain_fixtures(tmp_path / "run2")
    obs_a = reverify_runtime_observation_bundle_v1(output_dir=obs1)
    obs_b = reverify_runtime_observation_bundle_v1(output_dir=obs2)
    assert obs_a["output_digest"] == obs_b["output_digest"]
    learning_a = reverify_runtime_to_learning_input_v1(output_dir=learning1)
    learning_b = reverify_runtime_to_learning_input_v1(output_dir=learning2)
    assert learning_a["output_digest"] == learning_b["output_digest"]
    comp_a = reverify_runtime_performance_comparison_input_v1(output_dir=comparison1)
    comp_b = reverify_runtime_performance_comparison_input_v1(output_dir=comparison2)
    assert comp_a["output_digest"] == comp_b["output_digest"]


def test_authority_invariants_futures_only_no_bitcoin() -> None:
    assert RUNTIME_OBSERVATION_FEEDBACK_AUTHORITY_INVARIANTS["futures_only"] is True
    assert RUNTIME_OBSERVATION_FEEDBACK_AUTHORITY_INVARIANTS["bitcoin_direction_allowed"] is False
    assert RUNTIME_OBSERVATION_FEEDBACK_AUTHORITY_INVARIANTS["spot_allowed"] is False
    assert (
        RUNTIME_OBSERVATION_FEEDBACK_AUTHORITY_INVARIANTS["progress_registry_mutation_allowed"]
        is False
    )


def test_reverify_rejects_missing_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "broken_out")
    out.mkdir()
    (out / OBSERVATION_ARTIFACT_REL).write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeObservationFeedbackError):
        reverify_runtime_observation_bundle_v1(output_dir=out)


def test_no_registry_mutation_flags() -> None:
    for contract in (
        build_runtime_observation_bundle_v1(),
        build_runtime_to_learning_input_v1(),
        build_runtime_performance_comparison_input_v1(),
    ):
        assert contract.get("progress_registry_mutated") is False


def test_reuse_existing_runtime_evidence_owners_importable() -> None:
    from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
    from src.meta.learning_loop.deploy_inactive_v1 import OBSERVED_STATE_SOURCE
    from src.meta.learning_loop.runtime_state_reconciliation_v1 import CONTRACT_NAME

    assert read_manifest is not None
    assert OBSERVED_STATE_SOURCE
    assert CONTRACT_NAME == "runtime_state_reconciliation_v1"
