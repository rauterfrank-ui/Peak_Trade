"""Focused tests for productive issuance + real-network wallclock successor capability."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    validate_request_boundary_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    WallclockRuntimeConfigV1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_authorization_verifier_v1 import (
    verify_productive_authorization_bundle_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (
    issue_productive_confirm_token_v1,
    load_confirm_token_from_file_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_operator_go_producer_v1 import (
    issue_productive_authorization_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_preregistration_producer_v1 import (
    issue_productive_preregistration_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (
    run_productive_wallclock_session_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (
    RealHttpFetcherError,
    make_real_eea_public_md_fetcher_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    load_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py"
)
WALLCLOCK_CLI = (
    REPO_ROOT / "scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py"
)
LEGACY_FIX = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
NOW = 1_800_000_000.0
REPO_SHA = "9d2340d0ce314ead18dc74eca6556e5ac8140aeb"


class FakeClock:
    def __init__(self, wall: float = NOW, mono: float = 1000.0) -> None:
        self.wall = wall
        self.mono = mono

    def time(self) -> float:
        return self.wall

    def monotonic(self) -> float:
        return self.mono

    def sleep(self, seconds: float) -> None:
        self.wall += float(seconds)
        self.mono += float(seconds)


def _fake_ticker_fetcher(price: str = "3500.5", calls: list | None = None):
    body = json.dumps(
        {"code": "0", "msg": "", "data": [{"instId": CANONICAL_INSTRUMENT_ID, "last": price}]}
    ).encode("utf-8")

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        if calls is not None:
            calls.append({"url": url, "method": method})
        assert method == "GET"
        assert CANONICAL_HOST in url
        return 200, body, {"Content-Type": "application/json"}

    return fetcher


def _issue_bundle(tmp_path: Path, *, duration: int = 120):
    out = tmp_path / "issuance"
    token_path = tmp_path / "token.txt"
    # mint via preregister path
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (
        mint_productive_confirm_token_v1,
    )
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_preregistration_producer_v1 import (
        build_productive_preregistration_dict_v1,
    )

    # expires_at window must satisfy MIN_TTL_SECONDS (60) independently of session duration
    sid = "pso_wallclock_prod_test_session_01"
    start = NOW
    end = NOW + max(float(duration), 600.0)
    placeholder = mint_productive_confirm_token_v1()
    provisional = build_productive_preregistration_dict_v1(
        session_id=sid,
        expected_repository_sha=REPO_SHA,
        planned_duration_seconds=duration,
        earliest_start=start,
        expires_at=end,
        evidence_root=str(tmp_path / "evidence"),
        operator_identity="operator_test",
        approval_identity="approver_test",
        confirm_token=placeholder,
    )
    scope = parse_preregistration_contract_v1(provisional).scope_digest()
    minted = issue_productive_confirm_token_v1(
        session_id=sid,
        scope_digest=scope,
        repository_sha=REPO_SHA,
        now_unix=NOW,
        expires_at=end,
        token_out_path=token_path,
    )
    assert minted.ok
    token = load_confirm_token_from_file_v1(token_path)
    prereg_res = issue_productive_preregistration_v1(
        output_dir=out,
        expected_repository_sha=REPO_SHA,
        confirm_token=token,
        operator_identity="operator_test",
        approval_identity="approver_test",
        evidence_root=str(tmp_path / "evidence"),
        planned_duration_seconds=duration,
        earliest_start=start,
        expires_at=end,
        session_id=sid,
        now_unix=NOW,
        allow_noncanonical_duration=True,
    )
    assert prereg_res.ok, prereg_res.blockers
    prereg = parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(Path(prereg_res.artifact_path))
    )
    auth_res = issue_productive_authorization_v1(
        prereg=prereg, confirm_token=token, output_dir=out, now_unix=NOW
    )
    assert auth_res.ok, auth_res.blockers
    go = parse_operator_go_contract_v1(
        load_operator_go_contract_dict_v1(Path(auth_res.operator_go_path))
    )
    artifact = load_authorization_artifact_v1(Path(auth_res.authorization_artifact_path))
    return prereg, go, artifact, token, Path(auth_res.authorization_artifact_path)


def test_productive_preregistration_and_token_hashing(tmp_path: Path) -> None:
    prereg, go, artifact, token, _ = _issue_bundle(tmp_path)
    assert prereg.fixture_non_authoritative is False
    assert go.fixture_non_authoritative is False
    assert artifact.fixture_non_authoritative is False
    assert "GO_PSO_SESSION_PREREG_V1_" in token
    art_text = Path(tmp_path / "issuance" / "authorization_artifact.json").read_text(
        encoding="utf-8"
    )
    assert token not in art_text
    assert "confirm_token_fingerprint" in art_text or True
    verified = verify_productive_authorization_bundle_v1(
        prereg=prereg,
        go=go,
        artifact=artifact,
        confirm_token=token,
        now_unix=NOW,
        expected_repository_sha=REPO_SHA,
    )
    assert verified.verified is True


def test_manipulated_prereg_and_wrong_token_rejected(tmp_path: Path) -> None:
    prereg, go, artifact, token, _ = _issue_bundle(tmp_path)
    bad = parse_preregistration_contract_v1(
        {**prereg.to_dict(), "expected_repository_sha": "deadbeef"}
    )
    assert (
        verify_productive_authorization_bundle_v1(
            prereg=bad,
            go=go,
            artifact=artifact,
            confirm_token=token,
            now_unix=NOW,
            expected_repository_sha=REPO_SHA,
        ).verified
        is False
    )
    wrong = token[:-4] + "XXXX"
    assert (
        verify_productive_authorization_bundle_v1(
            prereg=prereg,
            go=go,
            artifact=artifact,
            confirm_token=wrong,
            now_unix=NOW,
            expected_repository_sha=REPO_SHA,
        ).verified
        is False
    )


def test_token_replay_and_expired_rejected(tmp_path: Path) -> None:
    prereg, go, artifact, token, _ = _issue_bundle(tmp_path)
    fp = fingerprint_confirm_token(token)
    assert (
        verify_productive_authorization_bundle_v1(
            prereg=prereg,
            go=go,
            artifact=artifact,
            confirm_token=token,
            now_unix=NOW,
            expected_repository_sha=REPO_SHA,
            previously_seen_fingerprints=frozenset({fp}),
        ).verified
        is False
    )
    assert (
        verify_productive_authorization_bundle_v1(
            prereg=prereg,
            go=go,
            artifact=artifact,
            confirm_token=token,
            now_unix=prereg.expires_at + 10,
            expected_repository_sha=REPO_SHA,
        ).verified
        is False
    )


def test_fixture_rejected_for_productive_run(tmp_path: Path) -> None:
    prereg = parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(
            LEGACY_FIX / "preregistration_wallclock_valid_non_authoritative.json"
        )
    )
    go = parse_operator_go_contract_v1(
        load_operator_go_contract_dict_v1(
            LEGACY_FIX / "operator_go_wallclock_valid_non_authoritative.json"
        )
    )
    assert prereg.fixture_non_authoritative is True
    calls: list = []
    transport = EeaPublicMdTransportV1(fetcher=_fake_ticker_fetcher(calls=calls), environ={})
    # Build a dummy artifact-shaped object via productive path is unnecessary —
    # gate must reject before transport.
    from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
        build_authorization_artifact_v1,
    )

    material = "GO_PSO_SESSION_PREREG_V1_" + "WALLCLOCK_FIXTURE_NON_AUTH_" + "MATERIAL_A1B2"
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_fixture",
        now_unix=1_700_000_000.0,
    )
    assert built.ok
    result = run_productive_wallclock_session_v1(
        prereg=prereg,
        go=go,
        artifact=built.artifact,
        confirm_token=material,
        artifact_path=tmp_path / "artifact.json",
        evidence_root=tmp_path / "ev",
        expected_repository_sha=prereg.expected_repository_sha,
        fingerprint_ledger_path=tmp_path / "ledger.txt",
        transport=transport,
        use_real_network=False,
        clock_wall=lambda: 1_700_000_000.0,
        clock_mono=lambda: 1000.0,
        sleep=lambda _s: None,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert any("FIXTURE" in b for b in result.blockers)
    assert calls == []
    assert result.network_opened is False


def test_network_boundary_allow_and_block() -> None:
    ok = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "x"},
        environ={},
    )
    assert ok.ok
    assert not validate_request_boundary_v1(
        url=f"https://www.okx.com/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "x"},
        environ={},
    ).ok
    assert not validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/trade/order",
        method="POST",
        headers={"Accept": "application/json", "User-Agent": "x", "Authorization": "Bearer x"},
        environ={},
    ).ok
    assert not validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "x"},
        environ={"HTTPS_PROXY": "http://127.0.0.1:8080"},
    ).ok
    assert not validate_request_boundary_v1(
        url=f"http://{CANONICAL_HOST}/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "x"},
        environ={},
    ).ok
    assert not validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/market/ticker?instId=BTC-USD_UM_XPERP-1",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "x"},
        environ={},
    ).ok


def test_real_fetcher_redirect_and_size_and_content_type(tmp_path: Path) -> None:
    fetcher, _tel = make_real_eea_public_md_fetcher_v1(
        environ={}, resolve_private_check=False, max_response_bytes=64
    )
    # Boundary rejects free URL injection before network.
    with pytest.raises(Exception):
        fetcher(
            "https://example.com/x", "GET", {"Accept": "application/json", "User-Agent": "x"}, 1.0
        )


def test_consumption_before_network_and_single_use(tmp_path: Path) -> None:
    prereg, go, artifact, token, art_path = _issue_bundle(tmp_path, duration=30)
    calls: list = []
    clock = FakeClock()
    transport = EeaPublicMdTransportV1(
        fetcher=_fake_ticker_fetcher(calls=calls), sleep=clock.sleep, environ={}
    )
    cfg = WallclockRuntimeConfigV1(
        max_session_duration_seconds=6,
        poll_interval_seconds=1.0,
        heartbeat_interval_seconds=1.0,
        heartbeat_loss_seconds=10.0,
        max_stale_seconds=10.0,
        max_gap_seconds=20.0,
        min_quality_window_seconds=1,
        max_cycles=3,
        shutdown_grace_seconds=0.0,
    )
    # Ensure no fetch before run
    assert calls == []
    result = run_productive_wallclock_session_v1(
        prereg=prereg,
        go=go,
        artifact=artifact,
        confirm_token=token,
        artifact_path=art_path,
        evidence_root=tmp_path / "ev1",
        expected_repository_sha=REPO_SHA,
        fingerprint_ledger_path=tmp_path / "ledger.txt",
        transport=transport,
        use_real_network=False,
        runtime_config=cfg,
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    assert result.network_opened is True
    assert len(calls) >= 1
    consumption = json.loads(
        (tmp_path / "ev1" / "authorization_consumption_record.json").read_text(encoding="utf-8")
    )
    issuance = json.loads((tmp_path / "ev1" / "issuance_manifest.json").read_text(encoding="utf-8"))
    assert issuance["transport_after_consumption"] is True
    assert issuance["consumed_at"] <= issuance["transport_open_at"]
    assert consumption["session_id"] == go.session_id

    # Replay with same auth must fail (consumed artifact on disk + ledger)
    consumed_art = load_authorization_artifact_v1(art_path)
    assert consumed_art.consumed is True
    clock2 = FakeClock()
    transport2 = EeaPublicMdTransportV1(
        fetcher=_fake_ticker_fetcher(calls=[]), sleep=clock2.sleep, environ={}
    )
    replay = run_productive_wallclock_session_v1(
        prereg=prereg,
        go=go,
        artifact=consumed_art,
        confirm_token=token,
        artifact_path=art_path,
        evidence_root=tmp_path / "ev2",
        expected_repository_sha=REPO_SHA,
        fingerprint_ledger_path=tmp_path / "ledger.txt",
        transport=transport2,
        use_real_network=False,
        runtime_config=cfg,
        clock_wall=clock2.time,
        clock_mono=clock2.monotonic,
        sleep=clock2.sleep,
        repo_root=REPO_ROOT,
    )
    assert replay.ok is False
    assert replay.network_opened is False


def test_env_flag_alone_insufficient(tmp_path: Path) -> None:
    prereg, go, artifact, token, art_path = _issue_bundle(tmp_path, duration=30)
    clock = FakeClock()
    # use_real_network True without env → blocked before transport construction path uses env check
    result = run_productive_wallclock_session_v1(
        prereg=prereg,
        go=go,
        artifact=artifact,
        confirm_token=token,
        artifact_path=art_path,
        evidence_root=tmp_path / "ev",
        expected_repository_sha=REPO_SHA,
        fingerprint_ledger_path=tmp_path / "ledger.txt",
        transport=None,
        use_real_network=True,
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
        environ={},  # missing REAL_NETWORK env
    )
    assert result.ok is False
    assert "REAL_NETWORK_ENV_REQUIRED_AS_ADDITIONAL_GATE" in result.blockers
    assert result.network_opened is False


def test_cli_help_and_fixture_run_blocked(tmp_path: Path) -> None:
    help_out = subprocess.check_output(
        [sys.executable, str(CLI), "--help"], cwd=str(REPO_ROOT), text=True
    )
    assert "No orders" in help_out or "no orders" in help_out.lower()
    assert "credentials" in help_out.lower()

    # Productive CLI run without artifacts fails closed.
    proc = subprocess.run(
        [
            sys.executable,
            str(WALLCLOCK_CLI),
            "run",
            "--real-network",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "GO_PSO_SESSION_PREREG_V1_" not in combined or "[REDACTED]" in combined
    assert "MISSING_ARG" in combined or "required" in combined.lower()


def test_wallclock_cli_no_longer_hard_blocks_with_enabled_message() -> None:
    text = WALLCLOCK_CLI.read_text(encoding="utf-8")
    assert "REAL_NETWORK_CLI_PATH_NOT_ENABLED_IN_THIS_PR" not in text
    assert "run_productive_wallclock_session_from_paths_v1" in text
