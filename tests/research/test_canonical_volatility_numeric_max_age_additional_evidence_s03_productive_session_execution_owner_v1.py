"""Focused tests for Additional-Evidence S03 productive session execution owner."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.bindings_v1 import (
    validate_s03_scope_bindings_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.confirm_token_stdin_v1 import (
    read_confirm_token_interactively_v1,
    sha256_fingerprint_plaintext_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_IN_THIS_CAPABILITY,
    BOUND_CAMPAIGN_ID,
    BOUND_CONTRACT_DIGEST,
    BOUND_DURATION_SECONDS,
    BOUND_INSTRUMENT,
    BOUND_NETWORK_SCOPE,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_PREREGISTRATION_ID,
    BOUND_RUNBOOK_DIGEST_V1,
    BOUND_SESSION_ID,
    BOUND_SESSION_LABEL,
    BOUND_SESSION_SCOPE,
    BOUND_VENUE,
    CAPABILITY_ID,
    CLI_MODE,
    CURRENT_AUTHORIZATION_REQUIRES_SEPARATE_REVOCATION_AND_REISSUANCE,
    EXIT_PRECEDENCE_OBSERVED,
    EXISTING_CLI_OWNER,
    NUMERIC_MAX_AGE_SELECTED,
    POLICY_ENFORCEMENT_ADDED,
    PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY,
    READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION,
    REAL_NETWORK_IN_THIS_CAPABILITY,
    SIDE_EFFECT_AUTHORIZATION_CONSUMED,
    SIDE_EFFECT_EVIDENCE_CREATION,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_SESSION_LOCK,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.duration_v1 import (
    MonotonicDurationAuthorityV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.evidence_v1 import (
    classify_sample_ordering_v1,
    resolve_s03_session_dir_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.independence_v1 import (
    assert_exit_precedence_preserved_v1,
    assert_reversal_reduce_first_v1,
    build_exit_risk_safety_independence_record_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    MarketSampleV1,
    S03ScopeBindingsV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.network_boundary_v1 import (
    assert_no_credentials_v1,
    assert_public_md_request_allowed_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.offline_probe_v1 import (
    OFFLINE_PROBE_TOKEN,
    run_offline_capability_probe_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.orchestrator_v1 import (
    preflight_s03_execution_owner_v1,
    run_additional_evidence_s03_productive_session_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.real_session_loop_v1 import (
    build_injectable_sequence_provider_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.session_lock_v1 import (
    S03SessionLockV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.side_effect_order_v1 import (
    assert_s03_consume_before_side_effects_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    build_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    validate_additional_evidence_session_preregistration_candidate_v2,
)

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SHA = "be8f9f798c792e13b66710ebf71ea3ee53d861f5"


def _bindings(**overrides) -> dict:
    base = {
        "campaign_id": BOUND_CAMPAIGN_ID,
        "session_label": BOUND_SESSION_LABEL,
        "session_id": BOUND_SESSION_ID,
        "preregistration_id": BOUND_PREREGISTRATION_ID,
        "preregistration_digest": BOUND_PREREGISTRATION_DIGEST,
        "contract_digest": BOUND_CONTRACT_DIGEST,
        "runbook_digest": BOUND_RUNBOOK_DIGEST_V1,
        "authorization_id": "cv_maxage_additional_evidence_auth_v2_test",
        "authorization_digest": "a" * 64,
        "repository_sha": EXECUTION_SHA,
        "venue": BOUND_VENUE,
        "instrument": BOUND_INSTRUMENT,
        "network_scope": BOUND_NETWORK_SCOPE,
        "session_scope": BOUND_SESSION_SCOPE,
        "duration_seconds": BOUND_DURATION_SECONDS,
    }
    base.update(overrides)
    return base


def _scope() -> S03ScopeBindingsV1:
    return validate_s03_scope_bindings_v1(_bindings())


def _build_temp_auth(tmp_path: Path):
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
    cons = tmp_path / "consumption_ledger.jsonl"
    rev = tmp_path / "revocation_ledger.jsonl"
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
        confirm_token=OFFLINE_PROBE_TOKEN,
        revocation_ledger_path=str(rev.resolve()),
        consumption_ledger_path=str(cons.resolve()),
        issued_at=datetime(2026, 8, 1, 19, 0, 0, tzinfo=timezone.utc),
    )
    path = tmp_path / "auth.json"
    write_additional_evidence_session_authorization_v2(output_path=path, artifact=artifact)
    return path, artifact, cons


def test_01_s03_contract_and_scope_pass() -> None:
    b = validate_s03_scope_bindings_v1(_bindings())
    assert b.session_label == "S03"
    assert b.duration_seconds == 10860
    assert b.session_id == BOUND_SESSION_ID


def test_02_authorization_v2_active_and_matching_via_preflight_contract() -> None:
    contract = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=ROOT
    )
    assert contract["contract_digest"] == BOUND_CONTRACT_DIGEST
    prereg = json.loads(
        (
            ROOT
            / "config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_v2.json"
        ).read_text(encoding="utf-8")
    )
    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        prereg, repo_root=ROOT, verify_baseline_artifact_ordering=True
    )
    assert validated["session_id"] == BOUND_SESSION_ID


def test_03_consume_before_side_effects_order() -> None:
    assert_s03_consume_before_side_effects_v1(
        [SIDE_EFFECT_AUTHORIZATION_CONSUMED, SIDE_EFFECT_SESSION_LOCK, SIDE_EFFECT_NETWORK]
    )
    with pytest.raises(Exception):
        assert_s03_consume_before_side_effects_v1(
            [SIDE_EFFECT_SESSION_LOCK, SIDE_EFFECT_AUTHORIZATION_CONSUMED]
        )


def test_04_05_06_no_lock_network_evidence_before_consume() -> None:
    for bad in (
        SIDE_EFFECT_SESSION_LOCK,
        SIDE_EFFECT_NETWORK,
        SIDE_EFFECT_EVIDENCE_CREATION,
    ):
        with pytest.raises(Exception):
            assert_s03_consume_before_side_effects_v1([bad])


def test_07_wrong_token_keeps_authorization_unconsumed(tmp_path: Path) -> None:
    path, artifact, cons = _build_temp_auth(tmp_path)
    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=ROOT,
        authorization_path=path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=EXECUTION_SHA,
        evidence_root=tmp_path / "evi",
        confirm_token="WRONG_TOKEN",
        market_samples=(),
        offline_probe=True,
    )
    assert result["authorization_consumed"] is False
    assert result["status"] == "BLOCKED"
    assert not cons.exists() or not cons.read_text(encoding="utf-8").strip()


def test_08_09_atomic_consume_and_second_rejected(tmp_path: Path) -> None:
    probe = run_offline_capability_probe_v1(
        repo_root=ROOT, tmp_root=tmp_path, execution_sha=EXECUTION_SHA
    )
    assert probe["ok"] is True
    events = probe["result"]["side_effect_probe"]["events"]
    assert "SECOND_CONSUMPTION_REJECTED" in events
    assert events.count("AUTHORIZATION_CONSUMED") == 1


def test_10_11_12_session_lock_bindings_and_ownership(tmp_path: Path) -> None:
    scope = _scope()
    clock = lambda: 1.0  # noqa: E731
    lock = S03SessionLockV1(
        session_dir=tmp_path / "S03",
        bindings=scope,
        monotonic_clock=clock,
        process_id=12345,
        owner_identity="host:12345",
    )
    rec = lock.acquire()
    assert rec.campaign_id == BOUND_CAMPAIGN_ID
    assert rec.session_id == BOUND_SESSION_ID
    assert rec.authorization_id == scope.authorization_id
    assert rec.preregistration_digest == BOUND_PREREGISTRATION_DIGEST
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        S03SessionLockV1(
            session_dir=tmp_path / "S03",
            bindings=scope,
            monotonic_clock=clock,
            process_id=999,
            owner_identity="other",
        ).acquire()
    lock.assert_ownership()
    assert lock.release() is True


def test_13_14_15_monotonic_duration_bound_no_artificial_aging() -> None:
    vals = {"t": 0.0}

    def clock() -> float:
        return vals["t"]

    auth = MonotonicDurationAuthorityV1(
        requested_duration_seconds=BOUND_DURATION_SECONDS, monotonic_clock=clock
    )
    auth.start()
    vals["t"] = 100.0
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        auth.assert_sufficient_for_pass()
    vals["t"] = float(BOUND_DURATION_SECONDS)
    auth.assert_sufficient_for_pass()
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        MonotonicDurationAuthorityV1(requested_duration_seconds=3600, monotonic_clock=clock)


def test_16_17_duplicate_and_out_of_order_policy() -> None:
    s1 = MarketSampleV1("id1", 1.0, 100.0, 100.1, 0.0)
    s2 = MarketSampleV1("id1", 1.0, 100.0, 101.1, 1.0)
    s3 = MarketSampleV1("id2", 1.0, 90.0, 102.1, 2.0)
    seen: set[str] = set()
    d, o, adv = classify_sample_ordering_v1(sample=s1, seen_identities=seen, last_event_time=None)
    assert (d, o, adv) == (False, False, True)
    seen.add(s1.sample_identity)
    d, o, adv = classify_sample_ordering_v1(sample=s2, seen_identities=seen, last_event_time=100.0)
    assert d is True and adv is False
    d, o, adv = classify_sample_ordering_v1(sample=s3, seen_identities=seen, last_event_time=100.0)
    assert o is True and adv is False


def test_18_19_20_21_public_md_boundary() -> None:
    assert_public_md_request_allowed_v1(
        url="https://eea.okx.com/api/v5/public/mark-price?instId=ETH-USD-SWAP",
        method="GET",
    )
    with pytest.raises(Exception):
        assert_public_md_request_allowed_v1(
            url="https://eea.okx.com/api/v5/trade/order", method="GET"
        )
    with pytest.raises(Exception):
        assert_public_md_request_allowed_v1(
            url="https://eea.okx.com/api/v5/public/mark-price", method="POST"
        )
    with pytest.raises(Exception):
        assert_no_credentials_v1({"OK-ACCESS-KEY": "x"})


def test_22_23_s03_root_and_s01_s02_forbidden(tmp_path: Path) -> None:
    session_dir = resolve_s03_session_dir_v1(evidence_root=tmp_path)
    assert BOUND_CAMPAIGN_ID in str(session_dir)
    assert "S03" in str(session_dir)
    from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.evidence_v1 import (
        assert_not_s01_s02_path_v1,
    )

    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        assert_not_s01_s02_path_v1(
            Path(
                "docs/evidence/.../cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe/sessions/x"
            )
        )


def test_24_25_counterfactual_non_authority_and_age_only() -> None:
    from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.evidence_v1 import (
        build_counterfactual_record_v1,
        build_decision_sensitivity_v1,
    )

    scope = _scope()
    cf = build_counterfactual_record_v1(
        bindings=scope,
        runtime_decision="HOLD",
        counterfactual_decision="BLOCK_ALPHA_AGE_ONLY",
        monotonic_elapsed_seconds=10.0,
        receive_time_unix_seconds=1.0,
    )
    assert cf["COUNTERFACTUAL_RUNTIME_AUTHORITY_OCCURRED"] is False
    ds = build_decision_sensitivity_v1(
        bindings=scope,
        other_inputs_digest="same",
        old_decision="HOLD",
        fresh_counterfactual_decision="BLOCK_ALPHA_AGE_ONLY",
        monotonic_elapsed_seconds=10.0,
        receive_time_unix_seconds=1.0,
    )
    assert ds["AGE_ONLY_DECISION_CHANGE"] is True
    assert ds["other_inputs_digest"] == "same"


def test_26_27_28_29_30_31_exit_risk_safety_independence() -> None:
    scope = _scope()
    rec = build_exit_risk_safety_independence_record_v1(
        bindings=scope,
        alpha_gate_blocked=True,
        monotonic_elapsed_seconds=1.0,
        receive_time_unix_seconds=1.0,
    )
    assert_exit_precedence_preserved_v1(rec)
    assert rec["exit_precedence"] == list(EXIT_PRECEDENCE_OBSERVED)
    assert rec["safety_path_available"] is True
    assert rec["hard_risk_reduce_available"] is True
    assert rec["reconciliation_available"] is True
    seq = assert_reversal_reduce_first_v1(
        position_side="OPEN_LONG", selected_opposite="SHORT_SELECTION"
    )
    assert seq[0].startswith("REDUCE")


def test_32_33_34_35_offline_probe_token_scan_terminal_no_real_wait(tmp_path: Path) -> None:
    probe = run_offline_capability_probe_v1(
        repo_root=ROOT, tmp_root=tmp_path, execution_sha=EXECUTION_SHA
    )
    assert probe["confirm_token_plaintext_persisted"] is False
    assert probe["real_network"] is False
    assert probe["real_session"] is False
    result = probe["result"]
    assert result["status"] == "PASS"
    assert result["sufficient_s03_evidence"] is True
    assert Path(result["terminal_verdict_path"]).is_file()
    assert Path(result["integrity_manifest_path"]).is_file()
    assert result["actual_monotonic_duration_seconds"] >= BOUND_DURATION_SECONDS


def test_abort_before_10860_not_sufficient(tmp_path: Path) -> None:
    path, artifact, _cons = _build_temp_auth(tmp_path)
    clock = {"t": 0.0}

    def mono() -> float:
        return clock["t"]

    samples = (
        MarketSampleV1("a", 1.0, 100.0, 100.1, 0.0),
        MarketSampleV1("b", 1.1, 160.0, 160.1, 1.0),
    )
    # Clock never reaches 10860.
    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=ROOT,
        authorization_path=path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=EXECUTION_SHA,
        evidence_root=tmp_path / "evi",
        confirm_token=OFFLINE_PROBE_TOKEN,
        monotonic_clock=mono,
        market_samples=samples,
        offline_probe=True,
    )
    assert result["status"] == "ABORTED"
    assert result["authorization_consumed"] is True
    assert result["sufficient_s03_evidence"] is False


def test_binding_negatives() -> None:
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        validate_s03_scope_bindings_v1(_bindings(campaign_id="wrong"))
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        validate_s03_scope_bindings_v1(_bindings(duration_seconds=3600))
    bad = _bindings()
    bad["extra_field"] = "x"
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        validate_s03_scope_bindings_v1(bad)


def test_confirm_token_getpass_mismatch() -> None:
    fp = sha256_fingerprint_plaintext_v1(OFFLINE_PROBE_TOKEN)
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        read_confirm_token_interactively_v1(expected_fingerprint=fp, getpass_fn=lambda _p: "nope")
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        read_confirm_token_interactively_v1(expected_fingerprint=fp, getpass_fn=lambda _p: "")


def test_capability_flags_enabled() -> None:
    assert PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY is True
    assert REAL_NETWORK_IN_THIS_CAPABILITY is True
    assert AUTHORIZATION_CONSUMPTION_IN_THIS_CAPABILITY is True
    assert READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION is True
    assert NUMERIC_MAX_AGE_SELECTED is False
    assert POLICY_ENFORCEMENT_ADDED is False
    assert CURRENT_AUTHORIZATION_REQUIRES_SEPARATE_REVOCATION_AND_REISSUANCE is True


def test_architecture_guards_and_cli_mode() -> None:
    g = assert_architecture_guards_v1(repo_root=ROOT)
    assert g["guards_pass"] is True
    assert g["productive_execution_enabled"] is True
    assert g["cli_real_path_enabled"] is True
    assert g["confirm_token_cli_argument_absent"] is True
    assert CLI_MODE == "additional-evidence-s03-session-run"
    assert CAPABILITY_ID.endswith("S03_PRODUCTIVE_SESSION_EXECUTION_OWNER_V1")
    cli_text = (ROOT / EXISTING_CLI_OWNER).read_text(encoding="utf-8")
    assert "enable_real_s03_session_execution=True" in cli_text
    assert "offline_probe=False" in cli_text
    assert "--confirm-token" not in cli_text


def test_campaign_auth_v1_consume_forbidden_in_owner_package() -> None:
    orch = (
        ROOT
        / "src/research/canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1/orchestrator_v1.py"
    ).read_text(encoding="utf-8")
    assert "consume_additional_evidence_session_authorization_v2" in orch
    assert "consume_campaign_authorization_session_v1" not in orch


def test_real_path_token_parameter_forbidden(tmp_path: Path) -> None:
    path, artifact, cons = _build_temp_auth(tmp_path)
    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=ROOT,
        authorization_path=path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=EXECUTION_SHA,
        evidence_root=tmp_path / "evi2",
        confirm_token=OFFLINE_PROBE_TOKEN,
        enable_real_s03_session_execution=True,
        enable_real_public_md_network=True,
        offline_probe=False,
    )
    assert result["authorization_consumed"] is False
    assert result["session_lock_created"] is False
    assert result["network_activity_occurred"] is False
    assert result["status"] == "BLOCKED"
    assert "confirm_token_parameter_forbidden_on_real_path" in str(result.get("blocker") or "")
    assert not cons.exists() or not cons.read_text(encoding="utf-8").strip()


def test_real_path_token_mismatch_null_side_effects(tmp_path: Path) -> None:
    path, artifact, cons = _build_temp_auth(tmp_path)
    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=ROOT,
        authorization_path=path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=EXECUTION_SHA,
        evidence_root=tmp_path / "evi_mismatch",
        enable_real_s03_session_execution=True,
        enable_real_public_md_network=True,
        offline_probe=False,
        getpass_fn=lambda _p: "WRONG_TOKEN",
        market_sample_provider=lambda: None,
        pace_sleep=lambda _s: None,
    )
    assert result["authorization_consumed"] is False
    assert result["session_lock_created"] is False
    assert result["network_activity_occurred"] is False
    assert result["evidence_mutation_occurred"] is False
    assert result["real_session_started"] is False
    assert not cons.exists() or not cons.read_text(encoding="utf-8").strip()


def test_real_path_mock_consume_before_lock_network_evidence(tmp_path: Path) -> None:
    path, artifact, cons = _build_temp_auth(tmp_path)
    clock = {"t": 0.0}

    def mono() -> float:
        return float(clock["t"])

    samples = (
        MarketSampleV1("mark:a", 1.0, 100.0, 100.1, 0.0),
        MarketSampleV1("mark:b", 1.1, 160.0, 160.1, 1.0),
    )
    provider = build_injectable_sequence_provider_v1(samples)

    def pace(_s: float) -> None:
        clock["t"] = float(BOUND_DURATION_SECONDS) + 1.0

    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=ROOT,
        authorization_path=path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=EXECUTION_SHA,
        evidence_root=tmp_path / "evi_real",
        enable_real_s03_session_execution=True,
        enable_real_public_md_network=True,
        offline_probe=False,
        getpass_fn=lambda _p: OFFLINE_PROBE_TOKEN,
        monotonic_clock=mono,
        market_sample_provider=provider,
        pace_sleep=pace,
    )
    assert result["status"] == "PASS"
    assert result["authorization_consumed"] is True
    assert result["real_session_started"] is True
    assert result["sufficient_s03_evidence"] is True
    events = result["side_effect_probe"]["events"]
    assert events.index("INTERACTIVE_TOKEN_READ") < events.index(SIDE_EFFECT_AUTHORIZATION_CONSUMED)
    assert events.index(SIDE_EFFECT_AUTHORIZATION_CONSUMED) < events.index(
        "CONSUMPTION_DURABILITY_CHECK"
    )
    assert events.index("CONSUMPTION_DURABILITY_CHECK") < events.index(SIDE_EFFECT_SESSION_LOCK)
    assert events.index(SIDE_EFFECT_SESSION_LOCK) < events.index(SIDE_EFFECT_NETWORK)
    assert events.index(SIDE_EFFECT_NETWORK) < events.index(SIDE_EFFECT_EVIDENCE_CREATION)
    assert "SECOND_CONSUMPTION_REJECTED" in events
    assert cons.is_file() and cons.read_text(encoding="utf-8").strip()


def test_real_path_existing_lock_fail_closed(tmp_path: Path) -> None:
    path, artifact, _cons = _build_temp_auth(tmp_path)
    evi = tmp_path / "evi_lock"
    scope = _scope()
    # Pre-create lock under the same S03 session dir the orchestrator will use.
    session_dir = resolve_s03_session_dir_v1(evidence_root=evi)
    busy = S03SessionLockV1(
        session_dir=session_dir,
        bindings=scope,
        monotonic_clock=lambda: 1.0,
        process_id=1,
        owner_identity="busy:1",
    )
    busy.acquire()
    clock = {"t": 0.0}

    def mono() -> float:
        return float(clock["t"])

    def pace(_s: float) -> None:
        clock["t"] = float(BOUND_DURATION_SECONDS) + 1.0

    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=ROOT,
        authorization_path=path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=EXECUTION_SHA,
        evidence_root=evi,
        enable_real_s03_session_execution=True,
        enable_real_public_md_network=True,
        offline_probe=False,
        getpass_fn=lambda _p: OFFLINE_PROBE_TOKEN,
        monotonic_clock=mono,
        market_sample_provider=lambda: MarketSampleV1("mark:x", 1.0, 100.0, 100.1, 0.0),
        pace_sleep=pace,
    )
    assert result["authorization_consumed"] is True
    assert result["status"] == "ABORTED"
    assert "session_lock_busy" in str(result.get("blocker") or "")


def test_preflight_wrong_sha_digest_fail_closed(tmp_path: Path) -> None:
    path, artifact, _ = _build_temp_auth(tmp_path)
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        preflight_s03_execution_owner_v1(
            repo_root=ROOT,
            authorization_path=path,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.authorization_digest,
            repository_sha="0" * 40,
        )
    with pytest.raises(AdditionalEvidenceS03SessionExecutionOwnerError):
        preflight_s03_execution_owner_v1(
            repo_root=ROOT,
            authorization_path=path,
            authorization_id=artifact.authorization_id,
            authorization_digest="f" * 64,
            repository_sha=EXECUTION_SHA,
        )


def test_preflight_only_no_side_effects(tmp_path: Path) -> None:
    path, artifact, cons = _build_temp_auth(tmp_path)
    result = run_additional_evidence_s03_productive_session_v1(
        repo_root=ROOT,
        authorization_path=path,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.authorization_digest,
        repository_sha=EXECUTION_SHA,
        evidence_root=tmp_path / "evi",
        preflight_only=True,
    )
    assert result["status"] == "PREFLIGHT_PASS"
    assert result["authorization_consumed"] is False
    assert not cons.exists()
