"""Contract tests for killswitch_writer_fencing_and_independent_read_paths_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.killswitch_writer_fencing_and_independent_read_paths_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    ARTIFACT_REL,
    GENESIS_EVENT_DIGEST,
    KILL_SWITCH_OWNER_REF,
    KILLSWITCH_WRITER_FENCING_AUTHORITY_INVARIANTS,
    KillSwitchWriterFencingError,
    build_killswitch_writer_fencing_v1,
    compute_canonical_event_payload_digest,
    compute_current_event_digest,
    evaluate_killswitch_writer_fencing_v1,
    produce_killswitch_writer_fencing_v1,
    reverify_killswitch_writer_fencing_v1,
    serialize_killswitch_writer_fencing_v1,
)
from tests.meta.killswitch_writer_fencing_and_independent_read_paths_v1_fixtures import (
    build_monotonic_writer_epoch_change_input,
    build_recovery_continuation_input,
    build_valid_killswitch_writer_fencing_input,
    produce_killswitch_writer_fencing_fixture,
)

_NON_MUTATION_FLAGS = (
    "killswitch_state_mutated",
    "killswitch_trip_executed",
    "killswitch_disarm_executed",
    "killswitch_reset_executed",
    "killswitch_rearm_executed",
    "revocation_epoch_incremented",
    "authority_revoked",
    "authority_created",
    "authority_activated",
    "execution_permission_created",
    "execution_permission_consumed",
    "submission_authorized",
    "submission_claim_executed",
    "adapter_invoked",
    "order_created",
    "order_submitted",
    "order_cancel_requested",
    "order_amend_requested",
    "position_state_mutated",
    "runtime_state_mutated",
    "database_mutated",
    "lock_acquired",
    "reservation_created",
    "network_side_effect_created",
    "exchange_request_sent",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
)

_NON_MUTATION_AFFIRMATIONS = (
    "does_not_mutate_kill_switch_state",
    "does_not_create_authority",
    "does_not_revoke_authority",
    "does_not_activate_runtime",
    "does_not_authorize_submission",
    "does_not_invoke_adapter",
    "does_not_send_network_request",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str = "killswitch_writer_fencing_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _assert_non_mutation(payload: dict) -> None:
    for flag in _NON_MUTATION_FLAGS:
        assert payload.get(flag) is False, flag
    for flag in _NON_MUTATION_AFFIRMATIONS:
        assert payload.get(flag) is True, flag
    assert payload.get("offline_only") is True


def test_valid_initial_writer_epoch_passes() -> None:
    contract = build_killswitch_writer_fencing_v1(build_valid_killswitch_writer_fencing_input())
    assert contract["decision"] == "PASS"
    assert contract["writer_epoch_status"] == "VALID"
    assert contract["event_sequence_status"] == "VALID"
    assert contract["digest_chain_status"] == "VALID"
    _assert_non_mutation(contract)


def test_valid_monotonic_writer_epoch_change_passes() -> None:
    contract = build_killswitch_writer_fencing_v1(build_monotonic_writer_epoch_change_input())
    assert contract["decision"] == "PASS"
    assert contract["writer_epoch"] == 2


def test_valid_recovery_continues_event_chain() -> None:
    contract = build_killswitch_writer_fencing_v1(build_recovery_continuation_input())
    assert contract["decision"] == "PASS"
    assert contract["event_sequence"] == 3
    assert contract["digest_chain_status"] == "VALID"


def test_independent_read_paths_required() -> None:
    contract = build_killswitch_writer_fencing_v1(build_valid_killswitch_writer_fencing_input())
    assert contract["read_paths_independent"] is True
    assert contract["read_paths_agree"] is True


def test_deterministic_repeat_identical_output() -> None:
    request = build_valid_killswitch_writer_fencing_input()
    first = build_killswitch_writer_fencing_v1(request)
    second = build_killswitch_writer_fencing_v1(request)
    assert first["output_digest"] == second["output_digest"]
    assert first["evidence_id"] == second["evidence_id"]


def test_canonical_serialization_stable() -> None:
    contract = build_killswitch_writer_fencing_v1(build_valid_killswitch_writer_fencing_input())
    serialized = serialize_killswitch_writer_fencing_v1(contract)
    assert serialized == deterministic_json_dumps(contract)


def test_producer_validator_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path)
    request = build_valid_killswitch_writer_fencing_input()
    result = produce_killswitch_writer_fencing_v1(request=request, output_dir=out)
    assert result.decision == "PASS"
    ok, _ = verify_manifest_sha256(out)
    assert ok
    replayed = reverify_killswitch_writer_fencing_v1(output_dir=out)
    assert replayed["decision"] == "PASS"
    assert (out / ARTIFACT_REL).is_file()


def test_pass_does_not_authorize_execution() -> None:
    contract = build_killswitch_writer_fencing_v1(build_valid_killswitch_writer_fencing_input())
    invariants = contract["authority_invariants"]
    assert invariants["pass_does_not_mean_killswitch_armed"] is True
    assert invariants["pass_does_not_create_execution_permission"] is True
    assert invariants["pass_does_not_authorize_submission"] is True
    assert invariants["pass_does_not_allow_orders"] is True


def test_kill_switch_owner_ref_unchanged() -> None:
    contract = build_killswitch_writer_fencing_v1(build_valid_killswitch_writer_fencing_input())
    assert contract["kill_switch_owner_ref"] == KILL_SWITCH_OWNER_REF


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"writer_identity": ""}, "MISSING_WRITER_IDENTITY"),
        ({"writer_epoch": -1}, "MISSING_WRITER_EPOCH"),
        ({"writer_epoch": 0, "previous_writer_epoch": 1}, "WRITER_EPOCH_REGRESSION"),
        ({"writer_epoch": 2, "known_writer_epochs": frozenset({0, 1})}, "WRITER_EPOCH_UNKNOWN"),
        ({"concurrent_writer_same_epoch": True}, "WRITER_EPOCH_CONFLICT"),
        ({"event_sequence": 0}, "MISSING_EVENT_SEQUENCE"),
        ({"event_sequence": 1, "previous_event_sequence": 2}, "EVENT_SEQUENCE_REGRESSION"),
        ({"event_sequence": 3, "previous_event_sequence": 1}, "EVENT_SEQUENCE_GAP"),
        ({"concurrent_event_successor": True}, "CONCURRENT_EVENT_SUCCESSOR"),
        ({"previous_event_digest": ""}, "MISSING_PREVIOUS_EVENT_DIGEST"),
        ({"current_event_digest": "f" * 64}, "EVENT_DIGEST_MISMATCH"),
        ({"recovery_chain_reset_attempt": True}, "RECOVERY_CHAIN_RESET_ATTEMPT"),
        ({"canonical_persisted_state_ref": ""}, "MISSING_CANONICAL_PERSISTED_STATE_REF"),
        ({"canonical_persisted_state_digest": ""}, "MISSING_CANONICAL_PERSISTED_STATE_DIGEST"),
        ({"safety_kernel_read_path_ref": ""}, "MISSING_SAFETY_KERNEL_READ_PATH"),
        ({"adapter_read_path_ref": ""}, "MISSING_ADAPTER_READ_PATH"),
        (
            {
                "safety_kernel_read_path_ref": "offline/shared/cache",
                "adapter_read_path_ref": "offline/shared/cache",
            },
            "READ_PATHS_NOT_INDEPENDENT",
        ),
        ({"shared_volatile_cache_only": True}, "SHARED_VOLATILE_CACHE_ONLY"),
        ({"safety_kernel_state_available": False}, "SAFETY_KERNEL_STATE_UNAVAILABLE"),
        ({"adapter_state_available": False}, "ADAPTER_STATE_UNAVAILABLE"),
        ({"safety_kernel_state_readable": False}, "SAFETY_KERNEL_STATE_UNREADABLE"),
        ({"adapter_state_readable": False}, "ADAPTER_STATE_UNREADABLE"),
        (
            {
                "safety_kernel_read_body": {
                    "read_path_kind": "canonical_persisted_state",
                    "kill_switch_state": "TRIPPED",
                    "revocation_epoch": 1,
                    "trading_epoch": 1,
                    "executor_epoch": 1,
                    "observed_at": "1970-01-01T00:00:00+00:00",
                    "is_fresh": True,
                    "state_available": True,
                    "state_readable": True,
                }
            },
            "READ_PATH_STATE_DISAGREEMENT",
        ),
        ({"safety_kernel_read_fresh": False}, "STALE_SAFETY_KERNEL_STATE"),
        ({"adapter_read_fresh": False}, "STALE_ADAPTER_STATE"),
        ({"revocation_epoch": 2}, "REVOCATION_EPOCH_MISMATCH"),
        ({"trading_epoch": 2}, "TRADING_EPOCH_MISMATCH"),
        ({"executor_epoch": 2}, "EXECUTOR_EPOCH_MISMATCH"),
        ({"last_known_armed_fallback_requested": True}, "LAST_KNOWN_ARMED_FALLBACK_REQUESTED"),
        (
            {"adapter_submission_requested_on_unclear_state": True},
            "ADAPTER_SUBMISSION_REQUESTED_ON_UNCLEAR_STATE",
        ),
        ({"input_refs": ()}, "MISSING_INPUT"),
        ({"contract_version": "v999"}, "UNKNOWN_CONTRACT_VERSION"),
    ],
)
def test_negative_fail_closed_cases(override: dict, expected_code: str) -> None:
    request = build_valid_killswitch_writer_fencing_input(**override)
    result = evaluate_killswitch_writer_fencing_v1(request)
    assert result.decision == "BLOCK"
    assert expected_code in result.rejection_reasons
    _assert_non_mutation(result.contract_body)


def test_state_rollback_detected() -> None:
    request = build_valid_killswitch_writer_fencing_input(
        previous_state="TRIPPED",
        proposed_state="ARMED",
    )
    result = evaluate_killswitch_writer_fencing_v1(request)
    assert result.decision == "BLOCK"
    assert "STATE_ROLLBACK_DETECTED" in result.rejection_reasons
    assert result.state_rollback_detected is True


def test_persisted_state_digest_mismatch() -> None:
    request = build_valid_killswitch_writer_fencing_input(
        canonical_persisted_state_digest="a" * 64,
    )
    result = evaluate_killswitch_writer_fencing_v1(request)
    assert result.decision == "BLOCK"
    assert "KILLSWITCH_STATE_DIGEST_MISMATCH" in result.rejection_reasons


def test_manifest_tampering_detected(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "tamper")
    produce_killswitch_writer_fencing_v1(
        request=build_valid_killswitch_writer_fencing_input(),
        output_dir=out,
    )
    artifact = out / ARTIFACT_REL
    payload = artifact.read_text(encoding="utf-8").replace(
        '"decision":"PASS"', '"decision":"BLOCK"'
    )
    artifact.write_text(payload, encoding="utf-8")
    with pytest.raises(KillSwitchWriterFencingError):
        reverify_killswitch_writer_fencing_v1(output_dir=out)


def test_fixture_producer_integration(tmp_path: Path) -> None:
    durable_root = tmp_path / "evidence_root"
    durable_root.mkdir()
    bundle = produce_killswitch_writer_fencing_fixture(
        tmp_path,
        durable_root,
        bundle_name="integration",
    )
    assert bundle.bundle_dir is not None
    assert bundle.bundle_dir.exists()


def test_authority_invariants_present() -> None:
    contract = build_killswitch_writer_fencing_v1(build_valid_killswitch_writer_fencing_input())
    for key, value in KILLSWITCH_WRITER_FENCING_AUTHORITY_INVARIANTS.items():
        if key == "killswitch_writer_fencing_contract_complete":
            assert contract["authority_invariants"][key] is True
        else:
            assert contract["authority_invariants"][key] == value


def test_current_event_digest_formula() -> None:
    payload = {"event_sequence": 1, "market_type": "FUTURES"}
    payload_digest = compute_canonical_event_payload_digest(payload)
    expected = compute_current_event_digest(
        previous_event_digest=GENESIS_EVENT_DIGEST,
        canonical_event_payload_digest=payload_digest,
    )
    assert len(expected) == 64
