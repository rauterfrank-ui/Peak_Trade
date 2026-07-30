"""Contract tests for CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    AuthorizationArtifactV2Error,
    parse_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_writer_v2 import (
    build_authorization_artifact_dict_v2,
    new_authorization_id_v2,
    write_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
    LEGACY_FORMAL_AUTHORIZATION_CLASS,
    REASON_CONFIRM_TOKEN_EXPOSED,
    REVOCATION_SCHEMA,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.consumption_gate_v1 import (
    consume_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
    integrity_digest_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.legacy_formal_authorization_v1 import (
    classify_legacy_formal_authorization_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.revocation_record_v1 import (
    build_revocation_record_dict_v1,
    issue_token_exposure_revocation_v1,
    write_revocation_record_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.revocation_registry_v1 import (
    assert_authorization_consumable_v1,
    resolve_authorization_effective_state_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateV2,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (
    mint_productive_confirm_token_v1,
)

REPO = "e5484b8f4f85f41a589a1b1b73926dff32fde8ef"
RUNBOOK = "a7529ef8ba8c5950f6372822b71ac2a5304ae037013288d48d53306d4105ff5a"
PREREG_ID = "prereg_wallclock_full_canonical_1h_e5484b8f4f85_20260730T175808Z"
PREREG_DIGEST = "67f9646f1b4f59718b75953b732b3f449b446d9696f90659e6c4affaef81619e"
COMPROMISED_AUTH_ID = "auth_wallclock_full_canonical_1h_e5484b8f4f85_6cd2abc02f9dd5d4aeda4aa8"
COMPROMISED_AUTH_DIGEST = "e85d8412ef9f76c6e48461dc3c4ef08c993d495d04675dc4581d30dd9e40a599"
COMPROMISED_AUTH_PATH = (
    Path(__file__).resolve().parents[2]
    / "evidence/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "authorization_1h_sha_bound_e5484b8f4f85_20260730T180434Z"
    / "formal_authorization.json"
)


def _cfg() -> dict[str, str]:
    return {
        "config/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.toml": (
            "6b81ac1719bc8554276d4258e88f995f1a9e7a572de61d5870def574261b9802"
        )
    }


def _safety() -> dict[str, bool]:
    return {
        "private_api": False,
        "order_routing_reachable": False,
        "orders_created": False,
        "testnet_execution_occurred": False,
        "live_execution_occurred": False,
        "promotion_authority": False,
    }


def _write_v2(tmp_path: Path, token: str | None = None) -> tuple[Path, str, dict]:
    tok = token or mint_productive_confirm_token_v1()
    auth_id = new_authorization_id_v2()
    payload = build_authorization_artifact_dict_v2(
        authorization_id=auth_id,
        preregistration_id=PREREG_ID,
        preregistration_digest=PREREG_DIGEST,
        repository_sha=REPO,
        runbook_sha256=RUNBOOK,
        session_duration_seconds=3600,
        config_digests=_cfg(),
        safety_boundaries=_safety(),
        confirm_token=tok,
    )
    path = tmp_path / "authorization_artifact_v2.json"
    result = write_authorization_artifact_v2(output_path=path, artifact_dict=payload)
    assert result.ok, result.blockers
    return path, tok, payload


def test_writer_parser_roundtrip(tmp_path: Path) -> None:
    path, _token, payload = _write_v2(tmp_path)
    loaded = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    assert loaded.schema == AUTHORIZATION_SCHEMA
    assert loaded.state is AuthorizationStateV2.CREATED_UNCONSUMED
    assert loaded.integrity_digest == payload["integrity_digest"]
    assert "confirm_token" not in json.loads(path.read_text(encoding="utf-8"))
    # semantic equality after canonicalize
    again = parse_authorization_artifact_v2(loaded.to_dict())
    assert again.to_dict() == loaded.to_dict()


def test_unknown_schema_fail_closed() -> None:
    with pytest.raises(AuthorizationArtifactV2Error, match="AUTH_SCHEMA_UNSUPPORTED"):
        parse_authorization_artifact_v2(
            {
                "schema": "authorization_artifact_v999",
                "schema_version": "v2",
                "authorization_id": "x",
                "capability": TARGET_RUNTIME_CAPABILITY,
                "preregistration_id": PREREG_ID,
                "preregistration_digest": PREREG_DIGEST,
                "repository_sha": REPO,
                "runbook_sha256": RUNBOOK,
                "session_duration_seconds": 3600,
                "config_digests": _cfg(),
                "safety_boundaries": _safety(),
                "confirm_token_fingerprint": "0" * 64,
                "confirm_token_digest": "sha256:" + "0" * 64,
                "created_at": 1.0,
                "single_use": True,
                "state": "CREATED_UNCONSUMED",
                "state_version": 1,
                "revocation_required_lookup": True,
            }
        )


def test_unknown_state_fail_closed(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["state"] = "authorized_unconsumed"
    raw.pop("integrity_digest", None)
    raw.pop("digest_scope", None)
    with pytest.raises(AuthorizationArtifactV2Error, match="UNKNOWN_AUTHORIZATION_STATE"):
        parse_authorization_artifact_v2(raw)


def test_legacy_formal_not_consumable() -> None:
    if not COMPROMISED_AUTH_PATH.is_file():
        pytest.skip("local compromised authorization evidence absent")
    raw = json.loads(COMPROMISED_AUTH_PATH.read_text(encoding="utf-8"))
    classified = classify_legacy_formal_authorization_v1(
        raw, expected_authorization_digest=COMPROMISED_AUTH_DIGEST
    )
    assert classified.ok
    assert classified.consumable is False
    assert classified.classification == LEGACY_FORMAL_AUTHORIZATION_CLASS


def test_legacy_revocation_by_id_and_digest(tmp_path: Path) -> None:
    if not COMPROMISED_AUTH_PATH.is_file():
        pytest.skip("local compromised authorization evidence absent")
    raw = json.loads(COMPROMISED_AUTH_PATH.read_text(encoding="utf-8"))
    classified = classify_legacy_formal_authorization_v1(
        raw, expected_authorization_digest=COMPROMISED_AUTH_DIGEST
    )
    assert classified.ok and classified.legacy is not None
    legacy = classified.legacy
    evidence = tmp_path / "evidence"
    result = issue_token_exposure_revocation_v1(
        evidence_root=evidence,
        authorization_id=legacy.authorization_id,
        authorization_digest=legacy.authorization_digest,
        preregistration_id=legacy.preregistration_id,
        preregistration_digest=legacy.preregistration_digest,
        repository_sha=legacy.repository_sha,
        previous_state=legacy.arming_state_raw,
        capability=legacy.capability,
        legacy_classification=legacy.classification,
    )
    assert result.ok, result.blockers
    # original unchanged
    raw2 = json.loads(COMPROMISED_AUTH_PATH.read_text(encoding="utf-8"))
    assert raw2.get("consumed") is False
    assert raw2.get("authorization_digest") == COMPROMISED_AUTH_DIGEST
    effective = resolve_authorization_effective_state_v1(
        evidence_root=evidence,
        authorization_id=legacy.authorization_id,
        authorization_digest=legacy.authorization_digest,
        declared_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
        legacy_classification=legacy.classification,
    )
    assert effective.effective_state == AuthorizationStateV2.REVOKED.value
    assert effective.consumable is False


def test_valid_authorization_no_revocation_eligibility(tmp_path: Path) -> None:
    path, _token, payload = _write_v2(tmp_path)
    art = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    eff = assert_authorization_consumable_v1(
        evidence_root=tmp_path / "evidence",
        authorization_id=art.authorization_id,
        authorization_digest=art.integrity_digest,
        declared_state=art.state.value,
        preregistration_id=art.preregistration_id,
        preregistration_digest=art.preregistration_digest,
        capability=art.capability,
        repository_sha=art.repository_sha,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_capability=TARGET_RUNTIME_CAPABILITY,
        config_digests_match=True,
        runbook_sha_match=True,
    )
    assert eff.ok and eff.consumable


def test_revocation_blocks_consumption(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    art = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    evidence = tmp_path / "evidence"
    rev = issue_token_exposure_revocation_v1(
        evidence_root=evidence,
        authorization_id=art.authorization_id,
        authorization_digest=art.integrity_digest,
        preregistration_id=art.preregistration_id,
        preregistration_digest=art.preregistration_digest,
        repository_sha=art.repository_sha,
        previous_state=art.state.value,
        capability=art.capability,
    )
    assert rev.ok
    result = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert result.ok is False
    assert "AUTHORIZATION_REVOKED" in result.blockers or any(
        "REVOKED" in b for b in result.blockers
    )


def test_revocation_digest_mismatch_blocked(tmp_path: Path) -> None:
    path, _token, _ = _write_v2(tmp_path)
    art = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    evidence = tmp_path / "evidence"
    payload = build_revocation_record_dict_v1(
        authorization_id=art.authorization_id,
        authorization_digest="f" * 64,
        preregistration_id=art.preregistration_id,
        preregistration_digest=art.preregistration_digest,
        repository_sha=art.repository_sha,
        reason_code=REASON_CONFIRM_TOKEN_EXPOSED,
        previous_state=art.state.value,
        capability=art.capability,
    )
    assert write_revocation_record_v1(evidence_root=evidence, record_dict=payload).ok
    eff = resolve_authorization_effective_state_v1(
        evidence_root=evidence,
        authorization_id=art.authorization_id,
        authorization_digest=art.integrity_digest,
        declared_state=art.state.value,
    )
    assert eff.ok is False
    assert "REVOCATION_DIGEST_MISMATCH" in eff.blockers


def test_damaged_revocation_record_blocked(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    store = evidence / "authorization_revocations_v1"
    store.mkdir(parents=True)
    (store / "broken.json").write_text("{not-json", encoding="utf-8")
    eff = resolve_authorization_effective_state_v1(
        evidence_root=evidence,
        authorization_id="auth_x",
        authorization_digest="0" * 64,
        declared_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
    )
    assert eff.ok is False
    assert any("DAMAGED" in b or "INTEGRITY" in b or "CORRUPT" in b for b in eff.blockers)


def test_conflicting_revocation_records_blocked(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    auth_id = "auth_conflict"
    for digest in ("a" * 64, "b" * 64):
        payload = build_revocation_record_dict_v1(
            authorization_id=auth_id,
            authorization_digest=digest,
            preregistration_id=PREREG_ID,
            preregistration_digest=PREREG_DIGEST,
            repository_sha=REPO,
            reason_code=REASON_CONFIRM_TOKEN_EXPOSED,
            previous_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
        )
        # Force write without prior conflict check by writing second with allow after first
        # Use write which detects conflict on second
        res = write_revocation_record_v1(evidence_root=evidence, record_dict=payload)
        if digest.startswith("b"):
            assert res.ok is False
            assert "CONFLICTING_REVOCATION_DIGEST_FOR_AUTHORIZATION_ID" in res.blockers
        else:
            assert res.ok


def test_duplicate_identical_revocation_idempotent(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    payload = build_revocation_record_dict_v1(
        authorization_id="auth_dup",
        authorization_digest="c" * 64,
        preregistration_id=PREREG_ID,
        preregistration_digest=PREREG_DIGEST,
        repository_sha=REPO,
        reason_code=REASON_CONFIRM_TOKEN_EXPOSED,
        previous_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
        revocation_id="rev_fixed_1",
    )
    first = write_revocation_record_v1(evidence_root=evidence, record_dict=payload)
    assert first.ok and not first.idempotent_reuse
    second_payload = build_revocation_record_dict_v1(
        authorization_id="auth_dup",
        authorization_digest="c" * 64,
        preregistration_id=PREREG_ID,
        preregistration_digest=PREREG_DIGEST,
        repository_sha=REPO,
        reason_code=REASON_CONFIRM_TOKEN_EXPOSED,
        previous_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
        revocation_id="rev_fixed_2",
    )
    second = write_revocation_record_v1(evidence_root=evidence, record_dict=second_payload)
    assert second.ok and second.idempotent_reuse


def test_consume_then_replay_blocked(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    evidence = tmp_path / "evidence"
    first = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert first.ok, first.blockers
    second = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert second.ok is False
    assert any("CONSUMED" in b or "NOT_CONSUMABLE" in b for b in second.blockers)


def test_revoke_then_consume_blocked(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    art = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    evidence = tmp_path / "evidence"
    assert issue_token_exposure_revocation_v1(
        evidence_root=evidence,
        authorization_id=art.authorization_id,
        authorization_digest=art.integrity_digest,
        preregistration_id=art.preregistration_id,
        preregistration_digest=art.preregistration_digest,
        repository_sha=art.repository_sha,
        previous_state=art.state.value,
        capability=art.capability,
    ).ok
    result = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert result.ok is False


def test_consume_then_revoke_race_terminal(tmp_path: Path) -> None:
    """Consume wins if it completes first; revoke afterwards is still durable."""
    path, token, _ = _write_v2(tmp_path)
    art = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    evidence = tmp_path / "evidence"
    consumed = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert consumed.ok
    rev = issue_token_exposure_revocation_v1(
        evidence_root=evidence,
        authorization_id=art.authorization_id,
        authorization_digest=art.integrity_digest,
        preregistration_id=art.preregistration_id,
        preregistration_digest=art.preregistration_digest,
        repository_sha=art.repository_sha,
        previous_state=AuthorizationStateV2.CONSUMED.value,
        capability=art.capability,
    )
    assert rev.ok
    # Replay still blocked
    replay = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert replay.ok is False


def test_revoke_consume_concurrent_consume_blocked(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    art = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    evidence = tmp_path / "evidence"
    barrier = threading.Barrier(2)
    outcomes: list[bool] = []

    def revoker() -> None:
        barrier.wait()
        issue_token_exposure_revocation_v1(
            evidence_root=evidence,
            authorization_id=art.authorization_id,
            authorization_digest=art.integrity_digest,
            preregistration_id=art.preregistration_id,
            preregistration_digest=art.preregistration_digest,
            repository_sha=art.repository_sha,
            previous_state=art.state.value,
            capability=art.capability,
        )

    def consumer() -> None:
        barrier.wait()
        res = consume_authorization_artifact_v2(
            evidence_root=evidence,
            artifact_path=path,
            confirm_token=token,
            expected_repository_sha=REPO,
            expected_preregistration_id=PREREG_ID,
            expected_preregistration_digest=PREREG_DIGEST,
            expected_runbook_sha256=RUNBOOK,
        )
        outcomes.append(res.ok)

    t1 = threading.Thread(target=revoker)
    t2 = threading.Thread(target=consumer)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    # Safe terminal: either consume succeeded before revoke observed, or blocked.
    # After both finish, further consume must be blocked.
    final = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert final.ok is False
    assert len(outcomes) == 1


def test_wrong_confirm_token_blocked(tmp_path: Path) -> None:
    path, _token, _ = _write_v2(tmp_path)
    evidence = tmp_path / "evidence"
    wrong_confirm = mint_productive_confirm_token_v1()
    result = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=path,
        confirm_token=wrong_confirm,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert result.ok is False
    assert "CONFIRM_TOKEN_MISMATCH" in result.blockers


def test_plaintext_token_absent_from_artifacts(tmp_path: Path) -> None:
    confirm = mint_productive_confirm_token_v1()
    path, _, _ = _write_v2(tmp_path, token=confirm)
    text = path.read_text(encoding="utf-8")
    assert confirm not in text
    assert "GO_PSO_SESSION_PREREG_V1_" not in text or "fingerprint" in text


def test_authorization_digest_mismatch_blocked(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["integrity_digest"] = "0" * 64
    path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    result = consume_authorization_artifact_v2(
        evidence_root=tmp_path / "evidence",
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert result.ok is False


@pytest.mark.parametrize(
    "kwargs,needle",
    [
        ({"expected_preregistration_id": "wrong"}, "PREREGISTRATION_ID_MISMATCH"),
        ({"expected_preregistration_digest": "0" * 64}, "PREREGISTRATION_DIGEST_MISMATCH"),
        ({"expected_repository_sha": "0" * 40}, "REPOSITORY_SHA_MISMATCH"),
        ({"expected_runbook_sha256": "0" * 64}, "RUNBOOK_SHA"),
    ],
)
def test_binding_mismatches_blocked(tmp_path: Path, kwargs: dict, needle: str) -> None:
    path, token, _ = _write_v2(tmp_path)
    base = dict(
        evidence_root=tmp_path / "evidence",
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    base.update(kwargs)
    result = consume_authorization_artifact_v2(**base)
    assert result.ok is False
    assert any(needle in b for b in result.blockers)


def test_config_drift_blocked(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    result = consume_authorization_artifact_v2(
        evidence_root=tmp_path / "evidence",
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
        config_digests_live={"config/ops/example.toml": "1" * 64},
    )
    assert result.ok is False
    assert "CONFIG_DRIFT" in result.blockers


def test_active_session_blocked(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    result = consume_authorization_artifact_v2(
        evidence_root=tmp_path / "evidence",
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
        active_session_found=True,
    )
    assert result.ok is False
    assert "ACTIVE_SESSION_FOUND" in result.blockers


def test_forced_fixture_cannot_consume_productive(tmp_path: Path) -> None:
    path, token, _ = _write_v2(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["forced_wiring_fixture_mode"] = True
    raw.pop("integrity_digest", None)
    raw.pop("digest_scope", None)
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
        stamp_integrity_digest,
    )

    stamped = stamp_integrity_digest(raw)
    path.write_text(json.dumps(stamped, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = consume_authorization_artifact_v2(
        evidence_root=tmp_path / "evidence",
        artifact_path=path,
        confirm_token=token,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert result.ok is False
    assert "FORCED_WIRING_FIXTURE_MODE_FORBIDDEN" in result.blockers


def test_no_private_api_order_routing_constants() -> None:
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1 import (
        constants_v1 as c,
    )

    assert c.PRIVATE_API is False
    assert c.ORDER_ROUTING_REACHABLE is False
    assert c.ORDERS_AUTHORIZED is False
    assert c.TESTNET_AUTHORIZED is False
    assert c.LIVE_AUTHORIZED is False


def test_compromised_authorization_fixture_effective_revoked(tmp_path: Path) -> None:
    if not COMPROMISED_AUTH_PATH.is_file():
        pytest.skip("local compromised authorization evidence absent")
    raw = json.loads(COMPROMISED_AUTH_PATH.read_text(encoding="utf-8"))
    classified = classify_legacy_formal_authorization_v1(
        raw, expected_authorization_digest=COMPROMISED_AUTH_DIGEST
    )
    assert classified.ok and classified.legacy is not None
    legacy = classified.legacy
    evidence = tmp_path / "evidence"
    assert issue_token_exposure_revocation_v1(
        evidence_root=evidence,
        authorization_id=COMPROMISED_AUTH_ID,
        authorization_digest=COMPROMISED_AUTH_DIGEST,
        preregistration_id=legacy.preregistration_id,
        preregistration_digest=legacy.preregistration_digest,
        repository_sha=legacy.repository_sha,
        previous_state=legacy.arming_state_raw,
        capability=legacy.capability,
        legacy_classification=legacy.classification,
    ).ok
    effective = resolve_authorization_effective_state_v1(
        evidence_root=evidence,
        authorization_id=COMPROMISED_AUTH_ID,
        authorization_digest=COMPROMISED_AUTH_DIGEST,
        declared_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
        legacy_classification=LEGACY_FORMAL_AUTHORIZATION_CLASS,
    )
    assert effective.effective_state == AuthorizationStateV2.REVOKED.value
    assert effective.consumable is False
    # session start impossible via consumption gate classification
    probe_confirm = mint_productive_confirm_token_v1()
    result = consume_authorization_artifact_v2(
        evidence_root=evidence,
        artifact_path=COMPROMISED_AUTH_PATH,
        confirm_token=probe_confirm,
        expected_repository_sha=REPO,
        expected_preregistration_id=PREREG_ID,
        expected_preregistration_digest=PREREG_DIGEST,
        expected_runbook_sha256=RUNBOOK,
    )
    assert result.ok is False
    assert any("LEGACY" in b or "NOT_V2" in b or "NOT_CONSUMABLE" in b for b in result.blockers)
    assert REVOCATION_SCHEMA == "authorization_revocation_v1"
    # digest helper smoke
    assert len(integrity_digest_v1({"a": 1})) == 64
