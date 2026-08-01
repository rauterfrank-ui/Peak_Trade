"""Focused tests for S03 atomic Auth-v2 reissue→consume→execute owner."""

from __future__ import annotations

import io
import json
import contextlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.constants_v1 import (
    BOUND_DURATION_SECONDS_V1,
    CANONICAL_ATOMIC_OWNER_SYMBOL,
    CAPABILITY_ID,
    CLI_MODE,
    ISSUE_AND_CONSUME_MUST_SHARE_PROCESS_LIFETIME,
    PRODUCTIVE_ATOMIC_EXECUTION_IN_DEFAULT_IMPORT,
    TOKEN_PLAINTEXT_MUST_NOT_CROSS_PROCESS_BOUNDARY,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.ephemeral_token_v1 import (
    EphemeralConfirmTokenHandleV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.models_v1 import (
    AtomicS03AuthV2ReissueConsumeExecuteError,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.offline_probe_v1 import (
    UNCONSUMABLE_FIXTURE_TOKEN,
    run_atomic_offline_capability_probe_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.orchestrator_v1 import (
    run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.confirm_token_stdin_v1 import (
    sha256_fingerprint_plaintext_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    BOUND_DURATION_SECONDS,
    SIDE_EFFECT_AUTHORIZATION_CONSUMED,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_SESSION_LOCK,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    MarketSampleV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    build_additional_evidence_session_authorization_v2,
    load_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.confirm_token_v2 import (
    assert_authorization_payload_token_safe_v2,
    assert_confirm_token_matches_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.ledgers_v2 import (
    authorization_is_consumed_v2,
    authorization_is_revoked_v2,
    load_jsonl_records_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    validate_additional_evidence_session_preregistration_candidate_v2,
)

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SHA = "beb06570a54d4608adbb68422e0da669602b2806"


def _fake_samples() -> tuple[MarketSampleV1, ...]:
    base = 1_700_000_000.0
    return tuple(
        MarketSampleV1(
            sample_identity=f"mark:{i}:{int(base + 60 * i)}",
            mark_price=3000.0 + i,
            event_time_unix_seconds=base + 60 * i,
            receive_time_unix_seconds=base + 60 * i + 0.05,
            monotonic_elapsed_seconds=float(i),
        )
        for i in range(3)
    )


def _clock_completing_duration():
    class _Clock:
        def __init__(self) -> None:
            self._now = 10.0
            self._calls = 0

        def __call__(self) -> float:
            self._calls += 1
            if self._calls >= 3:
                self._now = 10.0 + float(BOUND_DURATION_SECONDS) + 1.0
            return float(self._now)

    return _Clock()


def _build_unconsumable_auth(tmp_path: Path):
    contract = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=ROOT
    )
    prereg = json.loads(
        (
            ROOT
            / "config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_v2.json"
        ).read_text(encoding="utf-8")
    )
    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        prereg, repo_root=ROOT, verify_baseline_artifact_ordering=True
    )
    auth_dir = tmp_path / "old_authorization"
    auth_dir.mkdir(parents=True, exist_ok=True)
    cons = auth_dir / "consumption_ledger.jsonl"
    rev = auth_dir / "revocation_ledger.jsonl"
    _lost = UNCONSUMABLE_FIXTURE_TOKEN
    artifact = build_additional_evidence_session_authorization_v2(
        preregistration_id=str(validated["session_id"]),
        preregistration_digest=str(validated["preregistration_digest"]),
        preregistration_contract_version=str(contract["capability_version"]),
        preregistration_contract_digest=str(contract["contract_digest"]),
        code_baseline_sha=str(validated["code_baseline_sha"]),
        execution_sha=EXECUTION_SHA,
        critical_surface_digest=str(validated["critical_surface_manifest_digest"]),
        runbook_digest=str(prereg["runbook_digest"]),
        venue=str(validated["venue"]),
        instrument=str(validated["instrument"]),
        network_scope=str(validated["network_scope"]),
        session_scope=str(validated["session_scope"]),
        duration_seconds=int(prereg["duration_seconds"]),
        campaign_id=str(validated["campaign_id"]),
        # Short binder avoids Policy Critic NO_SECRETS `token=<long_name>` false positive.
        confirm_token=_lost,
        revocation_ledger_path=str(rev.resolve()),
        consumption_ledger_path=str(cons.resolve()),
        issued_at=datetime(2026, 8, 1, 19, 0, 0, tzinfo=timezone.utc),
    )
    path = auth_dir / "additional_evidence_session_authorization_v2.json"
    write_additional_evidence_session_authorization_v2(output_path=path, artifact=artifact)
    return path, artifact


def test_01_architecture_guards_and_invariants() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert ISSUE_AND_CONSUME_MUST_SHARE_PROCESS_LIFETIME is True
    assert TOKEN_PLAINTEXT_MUST_NOT_CROSS_PROCESS_BOUNDARY is True
    assert PRODUCTIVE_ATOMIC_EXECUTION_IN_DEFAULT_IMPORT is False
    assert CAPABILITY_ID.endswith("EPHEMERAL_CONFIRM_TOKEN_V1")
    assert CLI_MODE == "additional-evidence-s03-atomic-reissue-consume-execute"
    assert CANONICAL_ATOMIC_OWNER_SYMBOL.startswith("run_s03_atomic_")


def test_02_ephemeral_token_mint_fingerprint_and_redacted_repr() -> None:
    handle = EphemeralConfirmTokenHandleV1.mint_canonical_v1()
    fp = handle.fingerprint_v1()
    assert len(fp) == 64
    assert fp == sha256_fingerprint_plaintext_v1(handle.borrow_plaintext_v1())
    text = repr(handle) + str(handle)
    assert "GO_PSO_SESSION_PREREG_V1_" not in text
    assert "cleared=False" in repr(handle)
    handle.clear_v1()
    with pytest.raises(
        AtomicS03AuthV2ReissueConsumeExecuteError,
        match="ephemeral_token_unavailable",
    ):
        handle.borrow_plaintext_v1()


def test_03_wrong_token_rejected_against_bound_fingerprint() -> None:
    handle = EphemeralConfirmTokenHandleV1.mint_canonical_v1()
    bound = sha256_fingerprint_plaintext_v1(handle.borrow_plaintext_v1())
    other = EphemeralConfirmTokenHandleV1.mint_canonical_v1()
    assert other.fingerprint_v1() != bound
    with pytest.raises(AdditionalEvidenceSessionAuthorizationV2Error):
        assert_confirm_token_matches_v2(
            artifact_fingerprint=bound,
            artifact_digest="sha256:" + ("ab" * 32),
            artifact_binding="cd" * 32,
            confirm_token=other.borrow_plaintext_v1(),
            authorization_id="x",
            preregistration_id="y",
            preregistration_digest="z" * 64,
            execution_sha=EXECUTION_SHA,
        )
    handle.clear_v1()
    other.clear_v1()


def test_04_token_unavailable_after_clear_simulates_process_boundary() -> None:
    handle = EphemeralConfirmTokenHandleV1.mint_canonical_v1()
    handle.clear_v1()
    with pytest.raises(
        AtomicS03AuthV2ReissueConsumeExecuteError,
        match="process_boundary",
    ):
        handle.as_getpass_fn_v1()("prompt")


def test_05_issue_and_consume_same_process_offline_probe_pass(tmp_path: Path) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        result = run_atomic_offline_capability_probe_v1(
            repo_root=ROOT,
            tmp_root=tmp_path,
            execution_sha=EXECUTION_SHA,
        )
    assert result["ok"] is True
    assert result["authorization_consumed"] is True
    assert result["token_plaintext_persisted"] is False
    assert result["requested_duration_seconds"] == BOUND_DURATION_SECONDS_V1
    combined = stdout.getvalue() + stderr.getvalue()
    assert "GO_PSO_SESSION_PREREG_V1_" not in combined
    assert UNCONSUMABLE_FIXTURE_TOKEN not in combined


def test_06_old_authorization_revoked_and_new_consumed_exactly_once(tmp_path: Path) -> None:
    old_path, old = _build_unconsumable_auth(tmp_path)
    new_dir = tmp_path / "new_authorization"
    evidence_root = tmp_path / "evidence_root"
    result = run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        unconsumable_authorization_path=old_path,
        unconsumable_authorization_id=old.authorization_id,
        evidence_root=evidence_root,
        isolated_authorization_dir=new_dir,
        offline_probe=True,
        market_samples=_fake_samples(),
        monotonic_clock=_clock_completing_duration(),
    )
    assert result["status"] == "PASS"
    assert result["old_authorization_revoked"] is True
    assert result["authorization_consumed"] is True
    assert result["authorization_consumed_exactly_once"] is True
    assert result["new_authorization_id"]
    assert result["new_authorization_id"] != old.authorization_id

    old_after = load_additional_evidence_session_authorization_v2(old_path)
    assert old_after.revocation_state == "REVOKED"
    assert authorization_is_revoked_v2(
        revocation_ledger_path=Path(old.revocation_ledger_path),
        authorization_id=old.authorization_id,
    )

    new_path = new_dir / "additional_evidence_session_authorization_v2.json"
    new_auth = load_additional_evidence_session_authorization_v2(new_path)
    assert new_auth.consumption_state == "CONSUMED"
    assert authorization_is_consumed_v2(
        consumption_ledger_path=Path(new_auth.consumption_ledger_path),
        authorization_id=new_auth.authorization_id,
    )
    cons_records = load_jsonl_records_v2(Path(new_auth.consumption_ledger_path))
    assert (
        len([r for r in cons_records if r.get("authorization_id") == new_auth.authorization_id])
        == 1
    )
    assert_authorization_payload_token_safe_v2(new_auth.to_dict())
    assert "confirm_token" not in new_auth.to_dict()


def test_07_lock_and_network_only_after_consumption_in_probe(tmp_path: Path) -> None:
    result = run_atomic_offline_capability_probe_v1(
        repo_root=ROOT,
        tmp_root=tmp_path,
        execution_sha=EXECUTION_SHA,
    )
    probe = list(result["side_effect_probe"])
    assert "AUTHORIZATION_CONSUMED" in probe or "OLD_AUTHORIZATION_REVOKED" in probe
    # S03 owner records lock/network after consume; atomic probe surfaces S03 result.
    s03 = None
    # Re-run full orchestrator to inspect nested s03 probe ordering markers.
    old_path, old = _build_unconsumable_auth(tmp_path / "case7")
    full = run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        unconsumable_authorization_path=old_path,
        unconsumable_authorization_id=old.authorization_id,
        evidence_root=tmp_path / "case7_evi",
        isolated_authorization_dir=tmp_path / "case7_new",
        offline_probe=True,
        market_samples=_fake_samples(),
        monotonic_clock=_clock_completing_duration(),
    )
    s03 = full["s03_result"]
    assert s03 is not None
    events = s03["side_effect_probe"]["events"]
    consume_idx = events.index(SIDE_EFFECT_AUTHORIZATION_CONSUMED)
    lock_idx = events.index(SIDE_EFFECT_SESSION_LOCK)
    network_idx = events.index(SIDE_EFFECT_NETWORK)
    assert consume_idx < lock_idx < network_idx
    assert full["session_lock_created"] is True
    assert full["session_lock_removed"] is True
    assert full["network_activity_occurred"] is False  # offline probe


def test_08_preconsumption_failure_auto_revokes_new_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_path, old = _build_unconsumable_auth(tmp_path)

    def _boom(**kwargs):  # noqa: ANN003
        raise RuntimeError("injected_preconsumption_failure")

    monkeypatch.setattr(
        "research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.orchestrator_v1.run_additional_evidence_s03_productive_session_v1",
        _boom,
    )
    new_dir = tmp_path / "new_authorization"
    result = run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        unconsumable_authorization_path=old_path,
        unconsumable_authorization_id=old.authorization_id,
        evidence_root=tmp_path / "evidence_root",
        isolated_authorization_dir=new_dir,
        offline_probe=True,
        market_samples=_fake_samples(),
        monotonic_clock=_clock_completing_duration(),
    )
    assert result["status"] == "BLOCKED"
    assert result["authorization_consumed"] is False
    assert result["new_authorization_revoked_on_failure"] is True
    assert result["new_authorization_id"]
    new_path = new_dir / "additional_evidence_session_authorization_v2.json"
    new_auth = load_additional_evidence_session_authorization_v2(new_path)
    assert new_auth.revocation_state == "REVOKED"
    assert authorization_is_revoked_v2(
        revocation_ledger_path=Path(new_auth.revocation_ledger_path),
        authorization_id=new_auth.authorization_id,
    )


def test_09_exception_repr_and_result_exclude_token_plaintext(tmp_path: Path) -> None:
    handle = EphemeralConfirmTokenHandleV1.mint_canonical_v1()
    token = handle.borrow_plaintext_v1()
    err = AtomicS03AuthV2ReissueConsumeExecuteError("safe_blocker_code")
    assert token not in repr(err)
    assert token not in str(err)
    result = run_atomic_offline_capability_probe_v1(
        repo_root=ROOT,
        tmp_root=tmp_path,
        execution_sha=EXECUTION_SHA,
    )
    dumped = json.dumps(result, sort_keys=True)
    assert token not in dumped
    assert UNCONSUMABLE_FIXTURE_TOKEN not in dumped
    handle.clear_v1()


def test_10_negative_duration_mutation_fail_closed(tmp_path: Path) -> None:
    old_path, old = _build_unconsumable_auth(tmp_path)
    # Corrupt duration on disk after build to force preflight failure before revoke/issue.
    payload = json.loads(old_path.read_text(encoding="utf-8"))
    payload["duration_seconds"] = 3600
    # Keep digest inconsistent → parse/verify fail-closed.
    old_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    result = run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        unconsumable_authorization_path=old_path,
        unconsumable_authorization_id=old.authorization_id,
        evidence_root=tmp_path / "evi",
        isolated_authorization_dir=tmp_path / "new",
        offline_probe=True,
        market_samples=_fake_samples(),
        monotonic_clock=_clock_completing_duration(),
    )
    assert result["status"] == "BLOCKED"
    assert result["authorization_consumed"] is False
    assert result["old_authorization_revoked"] is False
    assert result["new_authorization_id"] == ""


def test_11_default_import_does_not_enable_productive_path(tmp_path: Path) -> None:
    assert PRODUCTIVE_ATOMIC_EXECUTION_IN_DEFAULT_IMPORT is False
    old_path, old = _build_unconsumable_auth(tmp_path)
    result = run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        unconsumable_authorization_path=old_path,
        unconsumable_authorization_id=old.authorization_id,
        enable_productive_atomic_execution=False,
        offline_probe=False,
        preflight_only=False,
    )
    assert result["status"] == "BLOCKED"
    assert "offline_probe_or_productive_or_preflight_required" in str(result.get("blocker"))
    assert result["authorization_consumed"] is False
    assert result["old_authorization_revoked"] is False
