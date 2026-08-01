"""Tests for additional-evidence session authorization v2 authority."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.architecture_guards_v2 import (
    assert_architecture_guards_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    build_additional_evidence_session_authorization_v2,
    load_additional_evidence_session_authorization_v2,
    parse_additional_evidence_session_authorization_v2,
    verify_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.confirm_token_v2 import (
    assert_authorization_payload_token_safe_v2,
    bind_confirm_token_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    AUTHORIZATION_VERSION,
    ISSUED_BY_AUTHORITY,
    REQUIRED_DURATION_SECONDS,
    REQUIRED_NETWORK_SCOPE,
    SIDE_EFFECT_AUTHORIZATION_CONSUMED,
    SIDE_EFFECT_EVIDENCE_CREATION,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_RUNTIME_INITIALIZATION,
    SIDE_EFFECT_SESSION_LOCK,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.consume_v2 import (
    consume_additional_evidence_session_authorization_v2,
    revoke_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.discovery_v2 import (
    assert_no_unconsumed_scope_conflict_v2,
    count_unconsumed_authorizations_for_scope_v2,
    discover_unconsumed_additional_evidence_authorizations_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.issuance_v2 import (
    issue_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.readiness_v2 import (
    evaluate_additional_evidence_authorization_issuance_readiness_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.side_effect_order_v2 import (
    assert_consume_before_side_effects_v2,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    PRODUCTIVE_ISSUANCE_IN_THIS_CAPABILITY,
    SCHEMA_VERSION as CAMPAIGN_SCHEMA_VERSION,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_writer_v2 import (
    build_authorization_artifact_dict_v2,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    REQUIRED_SESSION_DURATION_SECONDS,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.mandatory_bindings_v1 import (
    MandatoryBindingError,
    validate_mandatory_network_scope_v1,
    validate_mandatory_session_duration_v1,
)

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SHA = "6056e0370a49ca6a26d68bcb43b6124e9a8ea014"
TOKEN = "GO_AE_SESSION_AUTH_V2_TEST_TOKEN_NOT_FOR_PRODUCTION"


def _readiness(**kwargs):
    return evaluate_additional_evidence_authorization_issuance_readiness_v2(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        **kwargs,
    )


def _build_from_readiness(**overrides):
    ready = _readiness()
    kwargs = dict(
        preregistration_id=ready["preregistration_id"],
        preregistration_digest=ready["preregistration_digest"],
        preregistration_contract_version=ready["preregistration_contract_version"],
        preregistration_contract_digest=ready["preregistration_contract_digest"],
        code_baseline_sha=ready["code_baseline_sha"],
        execution_sha=EXECUTION_SHA,
        critical_surface_digest=ready["critical_surface_digest"],
        runbook_digest=ready["runbook_digest"],
        venue=ready["venue"],
        instrument=ready["instrument"],
        network_scope=ready["network_scope"],
        session_scope=ready["session_scope"],
        duration_seconds=ready["duration_seconds"],
        campaign_id=ready["campaign_id"],
        confirm_token=TOKEN,
        revocation_ledger_path="tmp/revocation_ledger.jsonl",
        consumption_ledger_path="tmp/consumption_ledger.jsonl",
        issued_at=datetime(2026, 8, 1, 19, 0, 0, tzinfo=timezone.utc),
    )
    kwargs.update(overrides)
    return build_additional_evidence_session_authorization_v2(**kwargs)


def test_01_schema_roundtrip(tmp_path: Path) -> None:
    artifact = _build_from_readiness()
    path = tmp_path / "auth.json"
    write_additional_evidence_session_authorization_v2(output_path=path, artifact=artifact)
    loaded = load_additional_evidence_session_authorization_v2(path)
    assert loaded.to_dict() == artifact.to_dict()
    assert loaded.authorization_version == AUTHORIZATION_VERSION


def test_02_builder_deterministic_bindings() -> None:
    a = _build_from_readiness()
    b = _build_from_readiness()
    assert a.authorization_id == b.authorization_id
    assert a.authorization_digest == b.authorization_digest
    assert a.network_scope == REQUIRED_NETWORK_SCOPE
    assert a.duration_seconds == REQUIRED_DURATION_SECONDS
    assert a.issued_by_authority == ISSUED_BY_AUTHORITY


def test_03_exact_network_scope_accepted() -> None:
    artifact = _build_from_readiness()
    assert artifact.network_scope == REQUIRED_NETWORK_SCOPE


def test_04_wrong_network_scope_rejected() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="network_scope_binding_mismatch"
    ):
        _build_from_readiness(network_scope="PUBLIC_MARKET_DATA_ONLY")


def test_05_duration_10860_accepted() -> None:
    assert _build_from_readiness().duration_seconds == 10860


def test_06_duration_3600_rejected() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="duration_seconds_mismatch"
    ):
        _build_from_readiness(duration_seconds=3600)


def test_07_other_duration_rejected() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="duration_seconds_mismatch"
    ):
        _build_from_readiness(duration_seconds=7200)


def test_08_instrument_mismatch_rejected() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="instrument_binding_mismatch"
    ):
        _build_from_readiness(instrument="BTC-USD_UM_XPERP-000000")


def test_09_session_scope_mismatch_rejected() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="session_scope_binding_mismatch"
    ):
        _build_from_readiness(session_scope="WRONG_SCOPE")


def test_10_venue_mismatch_rejected() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="venue_binding_mismatch"
    ):
        _build_from_readiness(venue="BINANCE")


def test_11_code_baseline_mismatch_rejected() -> None:
    artifact = _build_from_readiness()
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="code_baseline_sha_mismatch"
    ):
        verify_additional_evidence_session_authorization_v2(
            artifact,
            repo_root=ROOT,
            expected_code_baseline_sha="a" * 40,
        )


def test_12_execution_sha_mismatch_rejected() -> None:
    artifact = _build_from_readiness()
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="execution_sha_mismatch"
    ):
        verify_additional_evidence_session_authorization_v2(
            artifact,
            repo_root=ROOT,
            expected_execution_sha="b" * 40,
        )


def test_13_baseline_not_ancestor_rejected() -> None:
    artifact = _build_from_readiness(execution_sha="ffffffffffffffffffffffffffffffffffffffff")
    with pytest.raises(AdditionalEvidenceSessionAuthorizationV2Error):
        verify_additional_evidence_session_authorization_v2(artifact, repo_root=ROOT)


def test_14_critical_surface_mismatch_rejected() -> None:
    artifact = _build_from_readiness()
    with pytest.raises(AdditionalEvidenceSessionAuthorizationV2Error, match="critical_surface"):
        verify_additional_evidence_session_authorization_v2(
            artifact,
            repo_root=ROOT,
            expected_critical_surface_digest="c" * 64,
        )


def test_15_runbook_digest_mismatch_rejected() -> None:
    artifact = _build_from_readiness()
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="runbook_digest_mismatch"
    ):
        verify_additional_evidence_session_authorization_v2(
            artifact,
            repo_root=ROOT,
            expected_runbook_digest="d" * 64,
        )


def test_16_preregistration_digest_mismatch_rejected() -> None:
    artifact = _build_from_readiness()
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="preregistration_digest_mismatch"
    ):
        verify_additional_evidence_session_authorization_v2(
            artifact,
            repo_root=ROOT,
            expected_preregistration_digest="e" * 64,
        )


def test_17_unknown_version_rejected() -> None:
    payload = _build_from_readiness().to_dict()
    payload["authorization_version"] = "canonical.../v9"
    payload["authorization_digest"] = "x"
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="unknown_authorization_version"
    ):
        parse_additional_evidence_session_authorization_v2(payload)


def test_18_unknown_field_rejected() -> None:
    payload = _build_from_readiness().to_dict()
    payload["unexpected_field"] = 1
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="unknown_authorization_fields"
    ):
        parse_additional_evidence_session_authorization_v2(payload)


def test_19_missing_field_rejected() -> None:
    payload = _build_from_readiness().to_dict()
    del payload["instrument"]
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="missing_required_field"
    ):
        parse_additional_evidence_session_authorization_v2(payload)


def test_20_duplicate_unconsumed_authorization_rejected(tmp_path: Path) -> None:
    # Simulate conflict via discovery helper using a temp repo layout is heavy;
    # instead issue dry-run twice is fine, while persist path uses assert_no conflict.
    # Build one persisted auth under ROOT campaign path is forbidden (no productive write).
    # Unit-level: second discovery conflict via monkeypatched path.
    ready = _readiness()
    artifact = _build_from_readiness()
    campaign_dir = (
        tmp_path
        / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
        / "campaigns"
        / ready["campaign_id"]
        / "authorization"
    )
    campaign_dir.mkdir(parents=True)
    # Point ledgers inside tmp and rewrite artifact paths.
    artifact = _build_from_readiness(
        revocation_ledger_path=str(
            (
                Path(
                    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
                )
                / "campaigns"
                / ready["campaign_id"]
                / "authorization"
                / "revocation_ledger.jsonl"
            ).as_posix()
        ),
        consumption_ledger_path=str(
            (
                Path(
                    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
                )
                / "campaigns"
                / ready["campaign_id"]
                / "authorization"
                / "consumption_ledger.jsonl"
            ).as_posix()
        ),
    )
    write_additional_evidence_session_authorization_v2(
        output_path=campaign_dir / "additional_evidence_session_authorization_v2.json",
        artifact=artifact,
    )
    found = discover_unconsumed_additional_evidence_authorizations_v2(
        repo_root=tmp_path,
        preregistration_id=ready["preregistration_id"],
    )
    assert len(found) == 1
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error,
        match="duplicate_unconsumed_authorization_for_scope",
    ):
        assert_no_unconsumed_scope_conflict_v2(
            repo_root=tmp_path,
            preregistration_id=ready["preregistration_id"],
            session_scope=ready["session_scope"],
            network_scope=ready["network_scope"],
            instrument=ready["instrument"],
        )
    assert (
        count_unconsumed_authorizations_for_scope_v2(
            repo_root=ROOT, preregistration_id=ready["preregistration_id"]
        )
        == 0
    )


def test_21_expired_authorization_rejected() -> None:
    issued = datetime(2020, 1, 1, tzinfo=timezone.utc)
    artifact = _build_from_readiness(
        issued_at=issued,
        earliest_start=issued,
        expires_at=issued + timedelta(seconds=60),
    )
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="authorization_expired"
    ):
        verify_additional_evidence_session_authorization_v2(
            artifact,
            repo_root=ROOT,
            now_utc=datetime(2026, 8, 1, tzinfo=timezone.utc),
        )


def test_22_revoked_authorization_rejected(tmp_path: Path) -> None:
    auth_dir = tmp_path / "authorization"
    auth_dir.mkdir(parents=True)
    rev_abs = str((auth_dir / "revocation_ledger.jsonl").resolve())
    cons_abs = str((auth_dir / "consumption_ledger.jsonl").resolve())
    artifact = _build_from_readiness(
        revocation_ledger_path=rev_abs, consumption_ledger_path=cons_abs
    )
    path = auth_dir / "additional_evidence_session_authorization_v2.json"
    write_additional_evidence_session_authorization_v2(output_path=path, artifact=artifact)
    revoke_additional_evidence_session_authorization_v2(
        repo_root=ROOT, authorization_path=path, reason="test_revoke"
    )
    loaded = load_additional_evidence_session_authorization_v2(path)
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="authorization_revoked"
    ):
        verify_additional_evidence_session_authorization_v2(
            loaded, repo_root=ROOT, require_unrevoked=True
        )


def test_23_consumed_authorization_rejected(tmp_path: Path) -> None:
    auth_dir = tmp_path / "authorization"
    auth_dir.mkdir(parents=True)
    rev_abs = str((auth_dir / "revocation_ledger.jsonl").resolve())
    cons_abs = str((auth_dir / "consumption_ledger.jsonl").resolve())
    artifact = _build_from_readiness(
        revocation_ledger_path=rev_abs, consumption_ledger_path=cons_abs
    )
    path = auth_dir / "additional_evidence_session_authorization_v2.json"
    write_additional_evidence_session_authorization_v2(output_path=path, artifact=artifact)
    consume_additional_evidence_session_authorization_v2(
        repo_root=ROOT,
        authorization_path=path,
        confirm_token=TOKEN,
        side_effect_probe=[],
    )
    loaded = load_additional_evidence_session_authorization_v2(path)
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="authorization_already_consumed"
    ):
        verify_additional_evidence_session_authorization_v2(
            loaded, repo_root=ROOT, require_unconsumed=True
        )


def test_24_single_use_enforced() -> None:
    payload = _build_from_readiness().to_dict()
    payload["single_use"] = False
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="single_use_required_true"
    ):
        parse_additional_evidence_session_authorization_v2(payload)


def test_25_confirm_token_redaction() -> None:
    payload = _build_from_readiness().to_dict()
    assert "confirm_token" not in payload
    assert_authorization_payload_token_safe_v2(payload)
    with pytest.raises(Exception):
        assert_authorization_payload_token_safe_v2({**payload, "confirm_token": TOKEN})


def test_26_confirm_token_replay_rejected() -> None:
    bound = bind_confirm_token_v2(
        confirm_token=TOKEN,
        authorization_id="x",
        preregistration_id="p",
        preregistration_digest="d" * 64,
        execution_sha=EXECUTION_SHA,
    )
    result = issue_additional_evidence_session_authorization_v2(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        confirm_token=TOKEN,
        dry_run=True,
        previously_seen_fingerprints=frozenset({bound["confirm_token_fingerprint"]}),
    )
    assert result.ok is False
    assert "confirm_token_replay_rejected" in result.blockers


def test_27_consume_before_session_lock() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="side_effect_before_consume"
    ):
        assert_consume_before_side_effects_v2([SIDE_EFFECT_SESSION_LOCK])


def test_28_consume_before_evidence_creation() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="side_effect_before_consume"
    ):
        assert_consume_before_side_effects_v2([SIDE_EFFECT_EVIDENCE_CREATION])


def test_29_consume_before_network() -> None:
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="side_effect_before_consume"
    ):
        assert_consume_before_side_effects_v2([SIDE_EFFECT_NETWORK])
    assert_consume_before_side_effects_v2(
        [
            SIDE_EFFECT_AUTHORIZATION_CONSUMED,
            SIDE_EFFECT_NETWORK,
            SIDE_EFFECT_RUNTIME_INITIALIZATION,
        ]
    )


def test_30_atomic_write_cleanup_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _build_from_readiness()
    path = tmp_path / "auth.json"

    def boom(*_a, **_k):
        raise OSError("disk_full")

    monkeypatch.setattr("os.replace", boom)
    with pytest.raises(OSError):
        write_additional_evidence_session_authorization_v2(output_path=path, artifact=artifact)
    assert not path.exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_31_post_write_reload_validation(tmp_path: Path) -> None:
    artifact = _build_from_readiness()
    path = tmp_path / "auth.json"
    write_additional_evidence_session_authorization_v2(output_path=path, artifact=artifact)
    loaded = load_additional_evidence_session_authorization_v2(path)
    assert loaded.authorization_digest == artifact.authorization_digest


def test_32_wallclock_authority_regression() -> None:
    assert AUTHORIZED_NETWORK_SCOPE == "PUBLIC_MARKET_DATA_ONLY"
    assert REQUIRED_SESSION_DURATION_SECONDS == 3600
    validate_mandatory_network_scope_v1(AUTHORIZED_NETWORK_SCOPE)
    validate_mandatory_session_duration_v1(3600)
    with pytest.raises(MandatoryBindingError):
        validate_mandatory_network_scope_v1(REQUIRED_NETWORK_SCOPE)
    with pytest.raises(MandatoryBindingError):
        validate_mandatory_session_duration_v1(10860)
    # Writer still builds only with wallclock bindings.
    payload = build_authorization_artifact_dict_v2(
        authorization_id="wallclock_probe",
        preregistration_id="p",
        preregistration_digest="f" * 64,
        repository_sha=EXECUTION_SHA,
        runbook_sha256="a" * 64,
        session_duration_seconds=3600,
        confirm_token=TOKEN,
        venue="OKX",
        network_scope=AUTHORIZED_NETWORK_SCOPE,
    )
    assert payload["network_scope"] == AUTHORIZED_NETWORK_SCOPE
    assert payload["session_duration_seconds"] == 3600


def test_33_campaign_v1_regression() -> None:
    assert PRODUCTIVE_ISSUANCE_IN_THIS_CAPABILITY is False
    assert str(CAMPAIGN_SCHEMA_VERSION).endswith("/v1")


def test_34_cross_authority_rejection() -> None:
    wallclock = {
        "schema": "authorization_artifact_v2",
        "schema_version": "v2",
        "authorization_id": "x",
    }
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="cross_authority_wallclock"
    ):
        parse_additional_evidence_session_authorization_v2(wallclock)  # type: ignore[arg-type]
    campaign = {
        "authorization_version": (
            "canonical_volatility_numeric_max_age_productive_evidence_campaign_authorization/v1"
        )
    }
    with pytest.raises(
        AdditionalEvidenceSessionAuthorizationV2Error, match="cross_authority_campaign_v1"
    ):
        parse_additional_evidence_session_authorization_v2(campaign)


def test_35_readiness_pass_for_current_v2_preregistration() -> None:
    ready = _readiness()
    assert ready["ready"] is True
    assert ready["authorization_issuance_readiness"] == "PASS"
    assert ready["network_scope"] == REQUIRED_NETWORK_SCOPE
    assert ready["duration_seconds"] == 10860
    assert ready["preregistration_id"].endswith("s03_4c31d7dc5a08")


def test_36_issuance_dry_run_creates_no_authorization() -> None:
    before = list(
        (
            ROOT
            / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
            / "campaigns"
        ).glob("**/additional_evidence_session_authorization_v2.json")
    )
    result = issue_additional_evidence_session_authorization_v2(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        confirm_token=TOKEN,
        dry_run=True,
    )
    assert result.ok is True
    assert result.dry_run is True
    assert result.authorization_path == ""
    after = list(
        (
            ROOT
            / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
            / "campaigns"
        ).glob("**/additional_evidence_session_authorization_v2.json")
    )
    assert before == after
    assert "AUTHORIZATION_NOT_PERSISTED" in result.notes


def test_37_no_network_activity_during_tests() -> None:
    # Structural: package guards forbid network side effects.
    guards = assert_architecture_guards_v2(repo_root=ROOT)
    assert guards["guards_pass"] is True


def test_38_no_session_execution_during_tests() -> None:
    result = issue_additional_evidence_session_authorization_v2(
        repo_root=ROOT,
        execution_sha=EXECUTION_SHA,
        confirm_token=TOKEN,
        dry_run=True,
    )
    assert result.ok is True
    assert "NO_SESSION_EXECUTION" in result.notes
