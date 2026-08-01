"""Focused tests for productive max-age campaign authorization capability v1."""

from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    deterministic_productive_mark_path_v1,
    run_productive_bridge_accumulation_session_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    build_campaign_authorization_artifact_v1,
    load_campaign_authorization_artifact_v1,
    parse_campaign_authorization_artifact_v1,
    verify_campaign_authorization_artifact_v1,
    write_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_SINGLE_USE_PER_SESSION,
    BOUND_CAMPAIGN_ID,
    BOUND_INSTRUMENT_ALLOWLIST,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST,
    BOUND_PUBLIC_MD_HOST,
    BOUND_PUBLIC_MD_METHOD_ALLOWLIST,
    BOUND_PUBLIC_MD_VENUE,
    BOUND_SESSION_IDS,
    CAMPAIGN_AUTHORIZATION_TTL_SECONDS,
    CREDENTIALS_REQUIRED,
    MAXIMUM_SESSION_COUNT,
    ORDERS_TECHNICALLY_EXCLUDED,
    PRIVATE_ENDPOINTS_EXCLUDED,
    SCHEMA_VERSION,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.consume_v1 import (
    assert_no_foreign_side_effects_before_release_v1,
    consume_campaign_authorization_session_v1,
    revoke_campaign_authorization_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.gate_v1 import (
    assert_orders_and_private_endpoints_excluded_v1,
    require_campaign_authorization_runtime_release_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
    resolve_ledger_path_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationError,
)

ROOT = Path(__file__).resolve().parents[2]
CLI = (
    ROOT
    / "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py"
)
REPO_SHA = "109119ea10c183489e554c8e656f6f6160c6c077"
ISSUED = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
S1, S2 = BOUND_SESSION_IDS


def _write_auth(tmp_path: Path, **overrides):
    kwargs = {
        "repository_sha": REPO_SHA,
        "campaign_id": BOUND_CAMPAIGN_ID,
        "session_ids": BOUND_SESSION_IDS,
        "preregistration_digest": BOUND_PREREGISTRATION_DIGEST,
        "issued_at": ISSUED,
        "earliest_start": ISSUED,
    }
    kwargs.update(overrides)
    artifact = build_campaign_authorization_artifact_v1(**kwargs)
    path = tmp_path / "campaign_authorization.json"
    write_campaign_authorization_artifact_v1(output_path=path, artifact=artifact)
    return path, artifact


def test_01_deterministic_rendering_identical_inputs(tmp_path: Path) -> None:
    a = build_campaign_authorization_artifact_v1(
        repository_sha=REPO_SHA,
        campaign_id=BOUND_CAMPAIGN_ID,
        session_ids=BOUND_SESSION_IDS,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        issued_at=ISSUED,
        earliest_start=ISSUED,
    )
    b = build_campaign_authorization_artifact_v1(
        repository_sha=REPO_SHA,
        campaign_id=BOUND_CAMPAIGN_ID,
        session_ids=tuple(reversed(BOUND_SESSION_IDS)),
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        issued_at=ISSUED,
        earliest_start=ISSUED,
    )
    assert a.to_dict() == b.to_dict()
    assert a.artifact_digest == b.artifact_digest
    write_campaign_authorization_artifact_v1(output_path=tmp_path / "a.json", artifact=a)


def test_02_digest_stability(tmp_path: Path) -> None:
    path, artifact = _write_auth(tmp_path)
    loaded = load_campaign_authorization_artifact_v1(path)
    assert loaded.artifact_digest == artifact.artifact_digest


def test_03_roundtrip_writer_parser_verifier(tmp_path: Path) -> None:
    path, artifact = _write_auth(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    parsed = parse_campaign_authorization_artifact_v1(raw)
    verified = verify_campaign_authorization_artifact_v1(
        parsed,
        expected_repository_sha=REPO_SHA,
        expected_campaign_id=BOUND_CAMPAIGN_ID,
        expected_session_ids=BOUND_SESSION_IDS,
        expected_preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
    )
    assert verified.authorization_id == artifact.authorization_id


def test_04_wrong_repository_sha(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    with pytest.raises(CampaignAuthorizationError, match="repository_sha"):
        verify_campaign_authorization_artifact_v1(
            load_campaign_authorization_artifact_v1(path),
            expected_repository_sha="0" * 40,
        )


def test_05_wrong_campaign_id(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    with pytest.raises(CampaignAuthorizationError, match="campaign_id"):
        verify_campaign_authorization_artifact_v1(
            load_campaign_authorization_artifact_v1(path),
            expected_campaign_id="other_campaign",
        )


def test_06_missing_session_id(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    with pytest.raises(CampaignAuthorizationError, match="session_ids|missing_session"):
        verify_campaign_authorization_artifact_v1(
            load_campaign_authorization_artifact_v1(path),
            expected_session_ids=(S1,),
        )


def test_07_additional_session_id() -> None:
    with pytest.raises(CampaignAuthorizationError):
        build_campaign_authorization_artifact_v1(
            repository_sha=REPO_SHA,
            campaign_id=BOUND_CAMPAIGN_ID,
            session_ids=(S1, S2, "extra_session"),
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            issued_at=ISSUED,
            earliest_start=ISSUED,
        )


def test_08_wrong_session_count() -> None:
    with pytest.raises(CampaignAuthorizationError, match="maximum_session_count|session"):
        build_campaign_authorization_artifact_v1(
            repository_sha=REPO_SHA,
            campaign_id=BOUND_CAMPAIGN_ID,
            session_ids=(S1,),
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            issued_at=ISSUED,
            earliest_start=ISSUED,
        )


def test_09_wrong_preregistration_digest() -> None:
    with pytest.raises(CampaignAuthorizationError, match="preregistration_digest"):
        build_campaign_authorization_artifact_v1(
            repository_sha=REPO_SHA,
            campaign_id=BOUND_CAMPAIGN_ID,
            session_ids=BOUND_SESSION_IDS,
            preregistration_digest="0" * 64,
            issued_at=ISSUED,
            earliest_start=ISSUED,
        )


def test_10_tampered_artifact(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["repository_sha"] = "1" * 40
    path.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(CampaignAuthorizationError, match="digest|repository"):
        load_campaign_authorization_artifact_v1(path)


def test_11_unknown_field_rejected(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["unexpected_field"] = "x"
    with pytest.raises(CampaignAuthorizationError, match="unknown_field"):
        parse_campaign_authorization_artifact_v1(raw)


def test_12_naive_datetime_rejected() -> None:
    with pytest.raises(CampaignAuthorizationError, match="naive_datetime"):
        build_campaign_authorization_artifact_v1(
            repository_sha=REPO_SHA,
            campaign_id=BOUND_CAMPAIGN_ID,
            session_ids=BOUND_SESSION_IDS,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            issued_at=datetime(2026, 8, 1, 12, 0, 0),
            earliest_start=ISSUED,
        )


def test_13_earliest_before_issuance() -> None:
    with pytest.raises(CampaignAuthorizationError, match="earliest_start_before"):
        build_campaign_authorization_artifact_v1(
            repository_sha=REPO_SHA,
            campaign_id=BOUND_CAMPAIGN_ID,
            session_ids=BOUND_SESSION_IDS,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            issued_at=ISSUED,
            earliest_start=ISSUED - timedelta(seconds=1),
        )


def test_14_earliest_after_expiry() -> None:
    with pytest.raises(CampaignAuthorizationError, match="earliest_start_after"):
        build_campaign_authorization_artifact_v1(
            repository_sha=REPO_SHA,
            campaign_id=BOUND_CAMPAIGN_ID,
            session_ids=BOUND_SESSION_IDS,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            issued_at=ISSUED,
            earliest_start=ISSUED + timedelta(seconds=CAMPAIGN_AUTHORIZATION_TTL_SECONDS + 1),
        )


def test_15_exactly_before_earliest_start(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path, earliest_start=ISSUED + timedelta(seconds=10))
    with pytest.raises(CampaignAuthorizationError, match="before_earliest_start"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED + timedelta(seconds=9),
        )


def test_16_exactly_at_earliest_start(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path, earliest_start=ISSUED)
    release = consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    assert release.session_id == S1


def test_17_exactly_before_expiry(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    release = consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED + timedelta(seconds=CAMPAIGN_AUTHORIZATION_TTL_SECONDS - 1),
    )
    assert release.session_id == S1


def test_18_exactly_at_expiry(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    with pytest.raises(CampaignAuthorizationError, match="at_or_after_expires_at"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED + timedelta(seconds=CAMPAIGN_AUTHORIZATION_TTL_SECONDS),
        )


def test_19_after_expiry(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    with pytest.raises(CampaignAuthorizationError, match="at_or_after_expires_at"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED + timedelta(seconds=CAMPAIGN_AUTHORIZATION_TTL_SECONDS + 5),
        )


def test_20_revocation_before_first_consumption(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    revoke_campaign_authorization_v1(
        authorization_artifact_path=path,
        evidence_root=tmp_path,
        reason="operator_abort",
        operator_reference="test-op-1",
        revoked_at=ISSUED,
    )
    with pytest.raises(CampaignAuthorizationError, match="revoked"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED,
        )


def test_21_revocation_after_first_consumption_blocks_second(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    revoke_campaign_authorization_v1(
        authorization_artifact_path=path,
        evidence_root=tmp_path,
        reason="abort_remaining",
        operator_reference="test-op-2",
        revoked_at=ISSUED + timedelta(seconds=1),
    )
    with pytest.raises(CampaignAuthorizationError, match="revoked"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S2,
            evidence_root=tmp_path,
            now=ISSUED + timedelta(seconds=2),
        )


def test_22_duplicate_revocation_irreversible(tmp_path: Path) -> None:
    path, artifact = _write_auth(tmp_path)
    r1 = revoke_campaign_authorization_v1(
        authorization_artifact_path=path,
        evidence_root=tmp_path,
        reason="first",
        operator_reference="op-a",
        revoked_at=ISSUED,
    )
    r2 = revoke_campaign_authorization_v1(
        authorization_artifact_path=path,
        evidence_root=tmp_path,
        reason="second",
        operator_reference="op-b",
        revoked_at=ISSUED + timedelta(seconds=1),
    )
    assert r1["revocation_record_digest"] != r2["revocation_record_digest"]
    # Source artifact unchanged.
    loaded = load_campaign_authorization_artifact_v1(path)
    assert loaded.artifact_digest == artifact.artifact_digest
    with pytest.raises(CampaignAuthorizationError, match="revoked"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED,
        )


def test_23_successful_consumption_session_1(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    release = consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    assert release.consumption_index == 1
    assert release.session_id == S1


def test_24_duplicate_consumption_session_1(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    with pytest.raises(CampaignAuthorizationError, match="already_consumed"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED + timedelta(seconds=1),
        )


def test_25_successful_consumption_session_2(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    release = consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S2,
        evidence_root=tmp_path,
        now=ISSUED + timedelta(seconds=1),
    )
    assert release.session_id == S2
    assert release.consumption_index == 2


def test_26_third_consumption_fail_closed(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S2,
        evidence_root=tmp_path,
        now=ISSUED + timedelta(seconds=1),
    )
    with pytest.raises(CampaignAuthorizationError):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED + timedelta(seconds=2),
        )


def test_27_unknown_session(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    with pytest.raises(CampaignAuthorizationError, match="unknown_session"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id="unknown_session_xyz",
            evidence_root=tmp_path,
            now=ISSUED,
        )


def test_28_parallel_consumption_same_session(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)

    def _one() -> str:
        try:
            consume_campaign_authorization_session_v1(
                authorization_artifact_path=path,
                session_id=S1,
                evidence_root=tmp_path,
                now=ISSUED,
            )
            return "ok"
        except CampaignAuthorizationError:
            return "fail"

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: _one(), range(8)))
    assert results.count("ok") == 1
    assert results.count("fail") == 7


def test_29_parallel_consumption_both_sessions(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)

    def _one(sid: str) -> str:
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=sid,
            evidence_root=tmp_path,
            now=ISSUED,
        )
        return sid

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(_one, [S1, S2]))
    assert set(results) == {S1, S2}


def test_30_corrupt_consumption_ledger(tmp_path: Path) -> None:
    path, artifact = _write_auth(tmp_path)
    cpath = resolve_ledger_path_v1(
        evidence_root=tmp_path, relative_or_absolute=artifact.consumption_ledger_path
    )
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text("{not-json\n", encoding="utf-8")
    with pytest.raises(CampaignAuthorizationError, match="ledger_corrupt|consumption"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED,
        )


def test_31_corrupt_revocation_ledger(tmp_path: Path) -> None:
    path, artifact = _write_auth(tmp_path)
    rpath = resolve_ledger_path_v1(
        evidence_root=tmp_path, relative_or_absolute=artifact.revocation_ledger_path
    )
    rpath.parent.mkdir(parents=True, exist_ok=True)
    rpath.write_text("{not-json\n", encoding="utf-8")
    with pytest.raises(CampaignAuthorizationError, match="ledger_corrupt|revocation"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED,
        )


def test_32_lock_persist_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, _ = _write_auth(tmp_path)
    from research.canonical_volatility_numeric_max_age_campaign_authorization_v1 import (
        consume_v1,
    )

    def _boom(self) -> None:  # noqa: ANN001
        raise CampaignAuthorizationError("lock_persist_error:simulated_lock_failure")

    monkeypatch.setattr(consume_v1._ExclusiveLedgerLockV1, "acquire", _boom)
    with pytest.raises(CampaignAuthorizationError, match="lock_persist_error"):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id=S1,
            evidence_root=tmp_path,
            now=ISSUED,
        )


def test_33_no_side_effects_before_successful_consumption(tmp_path: Path) -> None:
    path, artifact = _write_auth(tmp_path)
    probe: list[str] = []
    # Failed attempt must not create productive ledgers.
    with pytest.raises(CampaignAuthorizationError):
        consume_campaign_authorization_session_v1(
            authorization_artifact_path=path,
            session_id="unknown",
            evidence_root=tmp_path,
            now=ISSUED,
            side_effect_probe=probe,
        )
    assert_no_foreign_side_effects_before_release_v1(
        evidence_root=tmp_path, artifact=artifact, probe=probe
    )
    probe2: list[str] = []
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
        side_effect_probe=probe2,
    )
    assert "CONSUMPTION_PERSIST_VERIFIED" in probe2
    assert probe2.index("CONSUMPTION_PERSIST_VERIFIED") < probe2.index("RUNTIME_RELEASE_RETURNED")


def test_34_accumulation_gate_rejects_missing_authorization(tmp_path: Path) -> None:
    with pytest.raises(CampaignAuthorizationError, match="campaign_authorization_missing"):
        require_campaign_authorization_runtime_release_v1(
            authorization_artifact_path=None,
            session_id=S1,
            campaign_id=BOUND_CAMPAIGN_ID,
            evidence_root=tmp_path,
            repository_sha=REPO_SHA,
        )


def test_35_accumulation_gate_rejects_unconsumed_authorization(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    with pytest.raises(CampaignAuthorizationError, match="not_consumed"):
        require_campaign_authorization_runtime_release_v1(
            authorization_artifact_path=path,
            session_id=S1,
            campaign_id=BOUND_CAMPAIGN_ID,
            evidence_root=tmp_path,
            repository_sha=REPO_SHA,
        )


def test_36_accumulation_gate_accepts_only_consumed_bound_session(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    release = require_campaign_authorization_runtime_release_v1(
        authorization_artifact_path=path,
        session_id=S1,
        campaign_id=BOUND_CAMPAIGN_ID,
        evidence_root=tmp_path,
        repository_sha=REPO_SHA,
    )
    assert release.session_id == S1
    with pytest.raises(ProductiveEvidenceAccumulationError, match="campaign_authorization_gate"):
        run_productive_bridge_accumulation_session_v1(
            session_id=S2,
            campaign_id=BOUND_CAMPAIGN_ID,
            repository_sha=REPO_SHA,
            samples=deterministic_productive_mark_path_v1(count=2),
            repo_root=ROOT,
            productive_ledger_path=tmp_path / "p.jsonl",
            join_ledger_path=tmp_path / "j.jsonl",
            quarantine_ledger_path=tmp_path / "q.jsonl",
            campaign_authorization_artifact_path=path,
            campaign_authorization_evidence_root=tmp_path,
            require_campaign_authorization=True,
        )


def test_37_orders_technically_excluded(tmp_path: Path) -> None:
    path, _ = _write_auth(tmp_path)
    release = consume_campaign_authorization_session_v1(
        authorization_artifact_path=path,
        session_id=S1,
        evidence_root=tmp_path,
        now=ISSUED,
    )
    flags = assert_orders_and_private_endpoints_excluded_v1(release)
    assert flags["orders_technically_excluded"] is True
    assert ORDERS_TECHNICALLY_EXCLUDED is True


def test_38_private_endpoints_excluded() -> None:
    assert PRIVATE_ENDPOINTS_EXCLUDED is True
    artifact = build_campaign_authorization_artifact_v1(
        repository_sha=REPO_SHA,
        campaign_id=BOUND_CAMPAIGN_ID,
        session_ids=BOUND_SESSION_IDS,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        issued_at=ISSUED,
        earliest_start=ISSUED,
    )
    assert artifact.public_md_host == BOUND_PUBLIC_MD_HOST
    assert artifact.public_md_venue == BOUND_PUBLIC_MD_VENUE
    assert "/api/v5/trade" not in artifact.public_md_endpoint_allowlist


def test_39_credentials_not_required() -> None:
    assert CREDENTIALS_REQUIRED is False


def test_40_get_only_public_md_allowlist_bound() -> None:
    artifact = build_campaign_authorization_artifact_v1(
        repository_sha=REPO_SHA,
        campaign_id=BOUND_CAMPAIGN_ID,
        session_ids=BOUND_SESSION_IDS,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        issued_at=ISSUED,
        earliest_start=ISSUED,
    )
    assert tuple(artifact.public_md_method_allowlist) == BOUND_PUBLIC_MD_METHOD_ALLOWLIST
    assert artifact.public_md_method_allowlist == ("GET",)
    assert tuple(artifact.public_md_endpoint_allowlist) == BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST
    assert tuple(artifact.instrument_allowlist) == BOUND_INSTRUMENT_ALLOWLIST
    assert artifact.authorization_scope == AUTHORIZATION_SCOPE
    assert artifact.schema_version == SCHEMA_VERSION
    assert artifact.authorization_single_use_per_session is AUTHORIZATION_SINGLE_USE_PER_SESSION
    assert (
        artifact.authorization_maximum_total_consumptions
        == AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS
    )
    assert artifact.maximum_session_count == MAXIMUM_SESSION_COUNT
    assert artifact.campaign_authorization_ttl_seconds == CAMPAIGN_AUTHORIZATION_TTL_SECONDS


def test_cli_help_and_import_smoke() -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    help_proc = subprocess.run(
        [sys.executable, str(CLI), "--help"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_proc.returncode == 0
    assert "render-campaign-authorization" in help_proc.stdout
    assert "consume-campaign-authorization" in help_proc.stdout
    import_proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from research.canonical_volatility_numeric_max_age_campaign_authorization_v1 import CAPABILITY_ID; print(CAPABILITY_ID)",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert import_proc.returncode == 0
    assert "CAMPAIGN_AUTHORIZATION" in import_proc.stdout


def test_cli_render_requires_explicit_args(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--mode",
            "render-campaign-authorization",
            "--campaign-authorization-output",
            str(tmp_path / "out.json"),
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
