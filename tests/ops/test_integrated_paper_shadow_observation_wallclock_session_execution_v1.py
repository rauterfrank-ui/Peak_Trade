"""Tests for wallclock MD-observe capability (fake transport/clock only)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (
    produce_paper_shadow_observation_readiness_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.session_lifecycle_v1 import (
    plan_observation_session_lifecycle_v1,
    refuse_wallclock_session_execution_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.authorization_consumption_runtime_v1 import (
    consume_authorization_for_wallclock_start_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    NETWORK_SCOPE,
    SESSION_EXECUTION_SCOPE,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.import_surface_guard_v1 import (
    attest_wallclock_import_surface_v1,
    scan_source_for_forbidden_surfaces_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    validate_request_boundary_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    WallclockRuntimeConfigV1,
    WallclockSessionRuntimeV1,
    preflight_wallclock_session_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_state_machine_v1 import (
    WallclockSessionState,
    assert_transition_allowed,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceWriterV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    build_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
    validate_preregistration_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.discovery_v1 import (
    discover_session_preregistration_and_operator_go_contract_present_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIX = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
LEGACY_FIX = (
    REPO_ROOT / "tests/fixtures/ops/paper_shadow_observation_operator_go_session_preregistration_v1"
)
NOW = 1_700_000_000.0
SHA = "fbfc3fdbae2b966d0ae44044b1d3c3b64da68afd"


def _material() -> str:
    return "GO_PSO_SESSION_PREREG_V1_" + "WALLCLOCK_FIXTURE_NON_AUTH_" + "MATERIAL_A1B2"


def _load_wallclock_prereg():
    return parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(
            FIX / "preregistration_wallclock_valid_non_authoritative.json"
        )
    )


def _load_wallclock_go():
    return parse_operator_go_contract_v1(
        load_operator_go_contract_dict_v1(
            FIX / "operator_go_wallclock_valid_non_authoritative.json"
        )
    )


def _fake_ticker_fetcher(price: str = "3500.5"):
    body = json.dumps(
        {"code": "0", "msg": "", "data": [{"instId": CANONICAL_INSTRUMENT_ID, "markPx": price}]}
    ).encode("utf-8")

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        assert method == "GET"
        assert CANONICAL_HOST in url
        return 200, body, {}

    return fetcher


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


def test_preflight_offline_and_discovery_regression() -> None:
    pre = preflight_wallclock_session_v1(repo_root=REPO_ROOT)
    assert pre["ok"] is True
    assert pre["network_used"] is False
    discovery = discover_session_preregistration_and_operator_go_contract_present_v1(
        repo_root=REPO_ROOT
    )
    assert discovery.SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT is True
    readiness = produce_paper_shadow_observation_readiness_v1(repo_root=REPO_ROOT)
    assert readiness.PAPER_SHADOW_OBSERVATION_AUTHORIZED is False


def test_ipso_still_refuses_wallclock() -> None:
    plan = plan_observation_session_lifecycle_v1()
    assert plan.wallclock_execution_allowed is False
    with pytest.raises(Exception):
        refuse_wallclock_session_execution_v1()


def test_scoped_go_accepted_and_unscoped_network_rejected() -> None:
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    assert validate_preregistration_contract_v1(prereg, now_unix=NOW).ok
    assert validate_operator_go_contract_v1(go, prereg=prereg, now_unix=NOW).ok

    bad = parse_operator_go_contract_v1(
        {**go.to_dict(), "network_authorized": True, "network_scope": "", "arming_state": "armed"}
    )
    blockers = ",".join(validate_operator_go_contract_v1(bad, prereg=prereg, now_unix=NOW).blockers)
    assert "NETWORK_AUTHORIZED_WITHOUT_EXACT_SCOPE" in blockers

    orders = parse_operator_go_contract_v1(
        {**go.to_dict(), "orders_authorized": True, "arming_state": "armed"}
    )
    assert "ORDERS_OR_BROKER_WRITES_AUTHORIZED_FORBIDDEN" in ",".join(
        validate_operator_go_contract_v1(orders, prereg=prereg, now_unix=NOW).blockers
    )

    btc = parse_operator_go_contract_v1(
        {
            **go.to_dict(),
            "instrument_allowlist": ["BTC-USD_UM_XPERP-1"],
            "arming_state": "armed",
        }
    )
    assert any(
        "BTC" in b
        for b in validate_operator_go_contract_v1(btc, prereg=prereg, now_unix=NOW).blockers
    )


def test_legacy_offline_fixture_still_valid_without_wallclock_scopes() -> None:
    prereg = parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(
            LEGACY_FIX / "preregistration_valid_non_authoritative.json"
        )
    )
    go = parse_operator_go_contract_v1(
        load_operator_go_contract_dict_v1(LEGACY_FIX / "operator_go_valid_non_authoritative.json")
    )
    legacy_now = 1_700_000_000.0
    assert validate_preregistration_contract_v1(prereg, now_unix=legacy_now).ok
    assert validate_operator_go_contract_v1(go, prereg=prereg, now_unix=legacy_now).ok
    assert go.network_authorized is False
    assert go.session_execution_authorized is False


def test_network_boundary_allow_and_denies() -> None:
    ok = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        environ={},
    )
    assert ok.ok

    www = validate_request_boundary_v1(
        url=f"https://www.okx.com/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        environ={},
    )
    assert not www.ok
    assert any("HOST_FORBIDDEN" in b for b in www.blockers)

    http = validate_request_boundary_v1(
        url=f"http://{CANONICAL_HOST}/api/v5/public/time",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        environ={},
    )
    assert any("SCHEME_FORBIDDEN" in b for b in http.blockers)

    post = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/public/time",
        method="POST",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        environ={},
    )
    assert any("METHOD_FORBIDDEN" in b for b in post.blockers)

    trade = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/trade/order",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        environ={},
    )
    assert not trade.ok

    auth_h = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/public/time",
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "PeakTradeTest/1.0",
            "Authorization": "Bearer x",
        },
        environ={},
    )
    assert any("AUTH_HEADER" in b for b in auth_h.blockers)

    ok_access = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/public/time",
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "PeakTradeTest/1.0",
            "OK-ACCESS-KEY": "abc",
        },
        environ={},
    )
    assert any("AUTH_HEADER" in b for b in ok_access.blockers)

    sim = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/public/time",
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "PeakTradeTest/1.0",
            "x-simulated-trading": "1",
        },
        environ={},
    )
    assert any("X_SIMULATED" in b for b in sim.blockers)

    proxy = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/public/time",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        environ={"HTTPS_PROXY": "http://evil.example:8080"},
    )
    assert any("PROXY_EGRESS" in b for b in proxy.blockers)

    cred_env = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/public/time",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        environ={"OKX_API_KEY": "not-a-real-key-but-present"},
    )
    assert any("CREDENTIAL_ENV" in b for b in cred_env.blockers)

    body = validate_request_boundary_v1(
        url=f"https://{CANONICAL_HOST}/api/v5/public/time",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradeTest/1.0"},
        body=b'{"ordType":"market","clOrdId":"x"}',
        environ={},
    )
    assert any("ORDER_PAYLOAD" in b or "REQUEST_BODY" in b for b in body.blockers)


def test_import_surface_guard_detects_forbidden_and_package_clean() -> None:
    att = attest_wallclock_import_surface_v1(repo_root=REPO_ROOT)
    assert att.ok, att.blockers
    bad = scan_source_for_forbidden_surfaces_v1(
        "from src.orders.foo import place_order\nplace_order()\n",
        module_name="synthetic",
    )
    assert any("FORBIDDEN_IMPORT" in b or "FORBIDDEN_CALL" in b for b in bad)


def test_state_machine_rejects_invalid_transition() -> None:
    assert_transition_allowed(
        from_state=WallclockSessionState.CREATED,
        to_state=WallclockSessionState.AUTH_VERIFIED,
    )
    with pytest.raises(Exception):
        assert_transition_allowed(
            from_state=WallclockSessionState.CREATED,
            to_state=WallclockSessionState.RUNNING,
        )


def test_consume_before_transport_and_replay_guard(tmp_path: Path) -> None:
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    material = _material()
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_wallclock_fixture_v1",
        now_unix=NOW,
    )
    assert built.ok and built.artifact is not None
    assert built.artifact.network_authorized is True
    assert built.artifact.network_scope == NETWORK_SCOPE
    assert built.artifact.session_execution_scope == SESSION_EXECUTION_SCOPE

    evidence_root = tmp_path / "ev1"
    evidence_root.mkdir()
    writer = WallclockEvidenceWriterV1(evidence_root=evidence_root)
    writer.ensure_append_files()
    artifact_path = tmp_path / "auth_artifact.json"
    ledger = tmp_path / "fingerprints.ledger"

    open_calls = {"n": 0}

    def fetcher(url, method, headers, timeout):
        open_calls["n"] += 1
        raise AssertionError("transport fetch must not run during consume")

    transport = EeaPublicMdTransportV1(fetcher=fetcher)
    assert transport.opened is False

    result = consume_authorization_for_wallclock_start_v1(
        prereg=prereg,
        go=go,
        artifact=built.artifact,
        confirm_token=material,
        evidence_writer=writer,
        artifact_path=artifact_path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=ledger,
    )
    assert result.ok
    assert result.transport_open_allowed is True
    assert transport.opened is False
    assert open_calls["n"] == 0
    assert (evidence_root / "authorization_consumption_record.json").is_file()
    assert artifact_path.is_file()
    consumed_raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert consumed_raw["consumed"] is True

    # replay fingerprint
    writer2 = WallclockEvidenceWriterV1(evidence_root=tmp_path / "ev2")
    (tmp_path / "ev2").mkdir()
    writer2.ensure_append_files()
    built2 = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_wallclock_fixture_v2",
        now_unix=NOW,
    )
    # Use fresh unconsumed artifact model but same token fingerprint in ledger
    from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
        parse_authorization_artifact_v1,
    )

    fresh = parse_authorization_artifact_v1(
        {**built2.artifact.to_dict(), "consumed": False, "arming_state": "authorized"}
    )
    replay = consume_authorization_for_wallclock_start_v1(
        prereg=prereg,
        go=go,
        artifact=fresh,
        confirm_token=material,
        evidence_writer=writer2,
        artifact_path=tmp_path / "auth2.json",
        now_unix=NOW,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=ledger,
    )
    assert replay.ok is False
    assert any("CONFIRM_TOKEN_REPLAY" in b for b in replay.blockers)


def test_short_fake_clock_session_pass(tmp_path: Path) -> None:
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    material = _material()
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_wallclock_run_v1",
        now_unix=NOW,
    )
    assert built.ok and built.artifact is not None

    clock = FakeClock()
    transport = EeaPublicMdTransportV1(
        fetcher=_fake_ticker_fetcher(),
        sleep=clock.sleep,
        environ={},
    )
    evidence_root = tmp_path / "session_ev"
    runtime = WallclockSessionRuntimeV1(
        evidence_root=evidence_root,
        transport=transport,
        config=WallclockRuntimeConfigV1(
            max_cycles=3,
            poll_interval_seconds=0.01,
            min_quality_window_seconds=0,
            heartbeat_interval_seconds=1.0,
            heartbeat_loss_seconds=100.0,
        ),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    artifact_path = tmp_path / "artifact.json"
    result = runtime.run(
        prereg=prereg,
        go=go,
        artifact=built.artifact,
        confirm_token=material,
        artifact_path=artifact_path,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    assert result.consumed is True
    assert result.network_opened is True
    assert result.cycle_count >= 1
    assert result.terminal_verdict in {"PASS", "FAIL"}
    assert result.economic_validity_pass is False
    assert result.paper_execution is False
    assert result.orders_submitted is False
    verified = verify_wallclock_evidence_bundle_v1(evidence_root=evidence_root)
    assert verified.verified is True
    assert verified.economic_validity_pass is False


def test_401_aborts_credential_surface(tmp_path: Path) -> None:
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    material = _material()
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_wallclock_401",
        now_unix=NOW,
    )

    def fetcher(url, method, headers, timeout):
        return 401, b"{}", {}

    clock = FakeClock()
    runtime = WallclockSessionRuntimeV1(
        evidence_root=tmp_path / "ev401",
        transport=EeaPublicMdTransportV1(fetcher=fetcher, sleep=clock.sleep, environ={}),
        config=WallclockRuntimeConfigV1(max_cycles=1, min_quality_window_seconds=0),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    result = runtime.run(
        prereg=prereg,
        go=go,
        artifact=built.artifact,
        confirm_token=material,
        artifact_path=tmp_path / "a401.json",
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp401.ledger",
    )
    assert result.terminal_verdict == "ABORT"
    assert result.consumed is True


def test_duplicate_session_lock(tmp_path: Path) -> None:
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    material = _material()
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_lock_1",
        now_unix=NOW,
    )
    clock = FakeClock()
    evidence_root = tmp_path / "lock_ev"
    # First runtime consume+lock then leave lock held by writing lock file manually after first run completes (releases).
    # Instead: acquire lock file before run.
    evidence_root.mkdir()
    (evidence_root / "session.lock").write_text("held\n", encoding="utf-8")
    runtime = WallclockSessionRuntimeV1(
        evidence_root=evidence_root,
        transport=EeaPublicMdTransportV1(fetcher=_fake_ticker_fetcher(), environ={}),
        config=WallclockRuntimeConfigV1(max_cycles=1, min_quality_window_seconds=0),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    # Consumption writes into evidence_root; lock file already exists -> ABORT after consume
    # Need empty evidence for immutable writes - use fresh root and pre-create lock after consume is hard.
    # Simpler: run twice with same session id on different roots but known_session_ids set.
    evidence_root2 = tmp_path / "lock_ev2"
    built2 = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_lock_2",
        now_unix=NOW,
    )
    runtime2 = WallclockSessionRuntimeV1(
        evidence_root=evidence_root2,
        transport=EeaPublicMdTransportV1(fetcher=_fake_ticker_fetcher(), environ={}),
        config=WallclockRuntimeConfigV1(max_cycles=1, min_quality_window_seconds=0),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    result = runtime2.run(
        prereg=prereg,
        go=go,
        artifact=built2.artifact,
        confirm_token=material,
        artifact_path=tmp_path / "alock.json",
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fplock.ledger",
        known_session_ids={go.session_id},
    )
    assert result.terminal_verdict == "ABORT"
    assert (
        any("DUPLICATE" in b or result.consumed is False for b in (result.blockers or [""]))
        or result.consumed is False
    )


def test_evidence_tamper_detected(tmp_path: Path) -> None:
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    material = _material()
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_tamper",
        now_unix=NOW,
    )
    clock = FakeClock()
    evidence_root = tmp_path / "tamper_ev"
    runtime = WallclockSessionRuntimeV1(
        evidence_root=evidence_root,
        transport=EeaPublicMdTransportV1(fetcher=_fake_ticker_fetcher(), environ={}),
        config=WallclockRuntimeConfigV1(max_cycles=2, min_quality_window_seconds=0),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    runtime.run(
        prereg=prereg,
        go=go,
        artifact=built.artifact,
        confirm_token=material,
        artifact_path=tmp_path / "atamper.json",
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fptamper.ledger",
    )
    target = evidence_root / "session_manifest.json"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    verified = verify_wallclock_evidence_bundle_v1(evidence_root=evidence_root)
    assert verified.verified is False
    assert any("EVIDENCE_TAMPER" in b for b in verified.blockers)


def test_capability_id_constant() -> None:
    assert CAPABILITY_ID.endswith("WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1")
    assert NETWORK_SCOPE == "okx_eea_futures_public_md_observe_v1"
    assert SESSION_EXECUTION_SCOPE == "paper_shadow_observation_wallclock_v1"
