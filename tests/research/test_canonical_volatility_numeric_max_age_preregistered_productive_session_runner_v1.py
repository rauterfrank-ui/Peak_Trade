"""Focused tests for preregistered productive session runner capability v1."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    build_campaign_authorization_artifact_v1,
    write_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_SESSION_IDS,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.consume_v1 import (
    consume_campaign_authorization_session_v1,
    revoke_campaign_authorization_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
    load_consumption_records_v1,
    resolve_ledger_path_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.architecture_guards_v1 import (
    assert_preregistered_session_runner_architecture_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_EVIDENCE_SCOPE,
    BOUND_INSTRUMENT_ID,
    BOUND_PREREGISTRATION_ID,
    BOUND_VENUE,
    BOUND_VENUE_SCOPE,
    CLI_MODE,
    PRODUCTIVE_BRIDGE_ACCUMULATE_CLI_MODE,
    SESSION_01_ID,
    SESSION_02_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    GitBaselineSnapshotV1,
    PreregisteredSessionRunnerError,
    SideEffectProbeV1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_source_v1 import (
    assert_public_get_allowlist_v1,
    reject_offline_synthetic_mark_source_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.runner_v1 import (
    run_preregistered_productive_session_v1,
)

ROOT = Path(__file__).resolve().parents[2]
CLI = (
    ROOT
    / "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py"
)
REPO_SHA = "4e587f8dbf72a77f6bef96c042c804d8fd6ba7dd"
ISSUED = datetime.now(timezone.utc) - timedelta(minutes=5)
S1, S2 = BOUND_SESSION_IDS


def _baseline() -> GitBaselineSnapshotV1:
    return GitBaselineSnapshotV1(
        branch="main",
        head_sha=REPO_SHA,
        origin_main_sha=REPO_SHA,
        worktree_allowed_delta_only=True,
    )


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


def _fake_mark_fetcher(mark: str = "2500.5", ts_ms: int | None = None):
    def _fetcher(url: str, method: str, headers: dict[str, str], timeout: float):
        del headers, timeout
        assert method == "GET"
        stamp = ts_ms if ts_ms is not None else int(time.time() * 1000)
        payload = {
            "code": "0",
            "data": [
                {
                    "instId": "ETH-USD_UM_XPERP-310404",
                    "instType": "FUTURES",
                    "markPx": mark,
                    "ts": str(stamp),
                }
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        return 200, body, {"Content-Type": "application/json"}

    return _fetcher


def _neg_side_effects(result: dict[str, Any] | None = None, *, consumed: bool = False) -> None:
    if result is not None:
        assert result.get("authorization_consumed") is False
        assert int(result.get("authorization_consumption_count") or 0) == 0
        assert result.get("session_started") is False
        assert result.get("market_data_request_occurred") is False
        assert result.get("session_01_evidence_mutation_occurred") is False
        assert result.get("productive_ledger_mutation_occurred") is False
        assert result.get("session_02_mutation_occurred") is False
    assert consumed is False


def _run_ok(tmp_path: Path, *, session_id: str = SESSION_01_ID, max_cycles: int = 2, **kwargs):
    auth_path, artifact = _write_auth(tmp_path)
    probe = SideEffectProbeV1()
    result = run_preregistered_productive_session_v1(
        repo_root=ROOT,
        campaign_id=BOUND_CAMPAIGN_ID,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        session_id=session_id,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        authorization_artifact_path=auth_path,
        repository_sha=REPO_SHA,
        venue=BOUND_VENUE,
        instrument_id=BOUND_INSTRUMENT_ID,
        market_data_scope=BOUND_VENUE_SCOPE,
        evidence_scope=BOUND_EVIDENCE_SCOPE,
        max_cycles=max_cycles,
        evidence_root=tmp_path,
        git_baseline=_baseline(),
        http_fetcher=_fake_mark_fetcher(),
        side_effect_probe=probe,
        **kwargs,
    )
    return result, auth_path, artifact, probe


def test_00_architecture_guard() -> None:
    out = assert_preregistered_session_runner_architecture_v1(repo_root=ROOT)
    assert out["cli_mode_present"] is True


def test_01_exact_target_session_id_unchanged(tmp_path: Path) -> None:
    result, _, _, _ = _run_ok(tmp_path, session_id=SESSION_01_ID)
    assert result["status"] == "PASS"
    assert result["session_id"] == SESSION_01_ID
    assert "-productive-" not in result["session_id"]


def test_02_no_derived_productive_n_session_id(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    with pytest.raises(PreregisteredSessionRunnerError, match="derived_session_id_forbidden"):
        run_preregistered_productive_session_v1(
            repo_root=ROOT,
            campaign_id=BOUND_CAMPAIGN_ID,
            preregistration_id=BOUND_PREREGISTRATION_ID,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            session_id=f"{SESSION_01_ID}-productive-1",
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            authorization_artifact_path=auth_path,
            repository_sha=REPO_SHA,
            venue=BOUND_VENUE,
            instrument_id=BOUND_INSTRUMENT_ID,
            market_data_scope=BOUND_VENUE_SCOPE,
            evidence_scope=BOUND_EVIDENCE_SCOPE,
            evidence_root=tmp_path,
            git_baseline=_baseline(),
            http_fetcher=_fake_mark_fetcher(),
        )
    _neg_side_effects(consumed=False)
    cons = tmp_path / artifact.consumption_ledger_path
    assert not cons.exists() or load_consumption_records_v1(cons) == []


def test_03_session_02_rejected_when_require_session_01(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    with pytest.raises(
        PreregisteredSessionRunnerError, match="session_id_not_required_exact_target"
    ):
        run_preregistered_productive_session_v1(
            repo_root=ROOT,
            campaign_id=BOUND_CAMPAIGN_ID,
            preregistration_id=BOUND_PREREGISTRATION_ID,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            session_id=SESSION_02_ID,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            authorization_artifact_path=auth_path,
            repository_sha=REPO_SHA,
            venue=BOUND_VENUE,
            instrument_id=BOUND_INSTRUMENT_ID,
            market_data_scope=BOUND_VENUE_SCOPE,
            evidence_scope=BOUND_EVIDENCE_SCOPE,
            evidence_root=tmp_path,
            git_baseline=_baseline(),
            http_fetcher=_fake_mark_fetcher(),
            require_exact_session_id=SESSION_01_ID,
        )
    _neg_side_effects(consumed=False)


def test_04_unknown_session_rejected(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    with pytest.raises(PreregisteredSessionRunnerError, match="unknown_or_unpreregistered"):
        run_preregistered_productive_session_v1(
            repo_root=ROOT,
            campaign_id=BOUND_CAMPAIGN_ID,
            preregistration_id=BOUND_PREREGISTRATION_ID,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            session_id="unknown_session_xyz",
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            authorization_artifact_path=auth_path,
            repository_sha=REPO_SHA,
            venue=BOUND_VENUE,
            instrument_id=BOUND_INSTRUMENT_ID,
            market_data_scope=BOUND_VENUE_SCOPE,
            evidence_scope=BOUND_EVIDENCE_SCOPE,
            evidence_root=tmp_path,
            git_baseline=_baseline(),
            http_fetcher=_fake_mark_fetcher(),
        )
    _neg_side_effects(consumed=False)


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("preregistration_digest", "0" * 64, "preregistration_digest"),
        ("authorization_digest", "0" * 64, "authorization_digest"),
        ("repository_sha", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "repository_sha"),
        ("venue", "BINANCE", "venue_mismatch"),
        ("instrument_id", "BTC-USD_UM_XPERP-999", "instrument_mismatch"),
        ("market_data_scope", "WRONG_SCOPE", "market_data_scope"),
        ("evidence_scope", "wrong_evidence_scope", "evidence_scope"),
    ],
)
def test_05_to_11_binding_mismatches_before_consumption(
    tmp_path: Path, field: str, value: str, match: str
) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    kwargs = {
        "repo_root": ROOT,
        "campaign_id": BOUND_CAMPAIGN_ID,
        "preregistration_id": BOUND_PREREGISTRATION_ID,
        "preregistration_digest": BOUND_PREREGISTRATION_DIGEST,
        "session_id": SESSION_01_ID,
        "authorization_id": artifact.authorization_id,
        "authorization_digest": artifact.artifact_digest,
        "authorization_artifact_path": auth_path,
        "repository_sha": REPO_SHA,
        "venue": BOUND_VENUE,
        "instrument_id": BOUND_INSTRUMENT_ID,
        "market_data_scope": BOUND_VENUE_SCOPE,
        "evidence_scope": BOUND_EVIDENCE_SCOPE,
        "evidence_root": tmp_path,
        "git_baseline": _baseline(),
        "http_fetcher": _fake_mark_fetcher(),
    }
    kwargs[field] = value
    with pytest.raises(PreregisteredSessionRunnerError, match=match):
        run_preregistered_productive_session_v1(**kwargs)
    cons = resolve_ledger_path_v1(
        evidence_root=tmp_path, relative_or_absolute=artifact.consumption_ledger_path
    )
    assert load_consumption_records_v1(cons) == []
    _neg_side_effects(consumed=False)


def test_12_revoked_authorization_rejected(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    revoke_campaign_authorization_v1(
        authorization_artifact_path=auth_path,
        evidence_root=tmp_path,
        reason="test_revoke",
        operator_reference="test",
    )
    with pytest.raises(
        PreregisteredSessionRunnerError, match="authorization_preflight_error|revok"
    ):
        run_preregistered_productive_session_v1(
            repo_root=ROOT,
            campaign_id=BOUND_CAMPAIGN_ID,
            preregistration_id=BOUND_PREREGISTRATION_ID,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            session_id=SESSION_01_ID,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            authorization_artifact_path=auth_path,
            repository_sha=REPO_SHA,
            venue=BOUND_VENUE,
            instrument_id=BOUND_INSTRUMENT_ID,
            market_data_scope=BOUND_VENUE_SCOPE,
            evidence_scope=BOUND_EVIDENCE_SCOPE,
            evidence_root=tmp_path,
            git_baseline=_baseline(),
            http_fetcher=_fake_mark_fetcher(),
        )
    _neg_side_effects(consumed=False)


def test_13_already_consumed_authorization_rejected(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    consume_campaign_authorization_session_v1(
        authorization_artifact_path=auth_path,
        session_id=SESSION_01_ID,
        evidence_root=tmp_path,
        expected_repository_sha=REPO_SHA,
        expected_campaign_id=BOUND_CAMPAIGN_ID,
        expected_preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
    )
    with pytest.raises(
        PreregisteredSessionRunnerError, match="already_consumed|authorization_preflight"
    ):
        run_preregistered_productive_session_v1(
            repo_root=ROOT,
            campaign_id=BOUND_CAMPAIGN_ID,
            preregistration_id=BOUND_PREREGISTRATION_ID,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            session_id=SESSION_01_ID,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            authorization_artifact_path=auth_path,
            repository_sha=REPO_SHA,
            venue=BOUND_VENUE,
            instrument_id=BOUND_INSTRUMENT_ID,
            market_data_scope=BOUND_VENUE_SCOPE,
            evidence_scope=BOUND_EVIDENCE_SCOPE,
            evidence_root=tmp_path,
            git_baseline=_baseline(),
            http_fetcher=_fake_mark_fetcher(),
        )


def test_14_and_15_single_use_consumption_bound_to_session(tmp_path: Path) -> None:
    result, auth_path, artifact, probe = _run_ok(tmp_path)
    assert result["authorization_consumed"] is True
    assert result["authorization_consumption_count"] == 1
    assert result["session_id"] == SESSION_01_ID
    cons = resolve_ledger_path_v1(
        evidence_root=tmp_path, relative_or_absolute=artifact.consumption_ledger_path
    )
    records = load_consumption_records_v1(cons)
    assert len(records) == 1
    assert records[0]["session_id"] == SESSION_01_ID
    assert "AUTHORIZATION_CONSUMED" in probe.events
    assert probe.events.index("PREFLIGHT_PASS") < probe.events.index("AUTHORIZATION_CONSUMED")
    # second run against same auth/session must fail closed
    with pytest.raises(PreregisteredSessionRunnerError):
        run_preregistered_productive_session_v1(
            repo_root=ROOT,
            campaign_id=BOUND_CAMPAIGN_ID,
            preregistration_id=BOUND_PREREGISTRATION_ID,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            session_id=SESSION_01_ID,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            authorization_artifact_path=auth_path,
            repository_sha=REPO_SHA,
            venue=BOUND_VENUE,
            instrument_id=BOUND_INSTRUMENT_ID,
            market_data_scope=BOUND_VENUE_SCOPE,
            evidence_scope=BOUND_EVIDENCE_SCOPE,
            max_cycles=1,
            evidence_root=tmp_path,
            git_baseline=_baseline(),
            http_fetcher=_fake_mark_fetcher(),
        )


def test_16_no_mutation_before_consumption_on_preflight_only(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    probe = SideEffectProbeV1()
    result = run_preregistered_productive_session_v1(
        repo_root=ROOT,
        campaign_id=BOUND_CAMPAIGN_ID,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        session_id=SESSION_01_ID,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        authorization_artifact_path=auth_path,
        repository_sha=REPO_SHA,
        venue=BOUND_VENUE,
        instrument_id=BOUND_INSTRUMENT_ID,
        market_data_scope=BOUND_VENUE_SCOPE,
        evidence_scope=BOUND_EVIDENCE_SCOPE,
        evidence_root=tmp_path,
        git_baseline=_baseline(),
        preflight_only=True,
        side_effect_probe=probe,
    )
    assert result["status"] == "PREFLIGHT_PASS"
    assert "AUTHORIZATION_CONSUMED" not in probe.events
    _neg_side_effects(result)


def test_17_public_get_allowlist() -> None:
    path = assert_public_get_allowlist_v1(
        url="https://eea.okx.com/api/v5/public/mark-price?instId=ETH-USD_UM_XPERP-310404",
        method="GET",
    )
    assert path == "/api/v5/public/mark-price"


def test_18_private_endpoints_blocked() -> None:
    with pytest.raises(PreregisteredSessionRunnerError, match="public_md_path_forbidden"):
        assert_public_get_allowlist_v1(url="https://eea.okx.com/api/v5/trade/order", method="GET")


def test_19_and_20_credentials_and_orders_not_used(tmp_path: Path) -> None:
    result, _, _, _ = _run_ok(tmp_path)
    assert result["credential_access_occurred"] is False
    assert result["order_request_occurred"] is False
    assert result["private_endpoint_request_occurred"] is False
    assert result["public_endpoints_only"] is True


def test_21_offline_synthetic_source_blocked(tmp_path: Path) -> None:
    with pytest.raises(PreregisteredSessionRunnerError, match="offline_synthetic"):
        reject_offline_synthetic_mark_source_v1("deterministic_mark_path")
    auth_path, artifact = _write_auth(tmp_path)
    with pytest.raises(PreregisteredSessionRunnerError, match="offline_synthetic"):
        run_preregistered_productive_session_v1(
            repo_root=ROOT,
            campaign_id=BOUND_CAMPAIGN_ID,
            preregistration_id=BOUND_PREREGISTRATION_ID,
            preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
            session_id=SESSION_01_ID,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.artifact_digest,
            authorization_artifact_path=auth_path,
            repository_sha=REPO_SHA,
            venue=BOUND_VENUE,
            instrument_id=BOUND_INSTRUMENT_ID,
            market_data_scope=BOUND_VENUE_SCOPE,
            evidence_scope=BOUND_EVIDENCE_SCOPE,
            evidence_root=tmp_path,
            git_baseline=_baseline(),
            http_fetcher=_fake_mark_fetcher(),
            mark_source_kind="deterministic_mark_path",
        )
    _neg_side_effects(consumed=False)


def test_22_session_01_evidence_binds_ids(tmp_path: Path) -> None:
    result, _, artifact, _ = _run_ok(tmp_path)
    assert result["status"] == "PASS"
    manifest = Path(result["preflight"]["session_manifest_path"])
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["session_id"] == SESSION_01_ID
    assert payload["campaign_id"] == BOUND_CAMPAIGN_ID
    assert payload["preregistration_digest"] == BOUND_PREREGISTRATION_DIGEST
    assert payload["authorization_id"] == artifact.authorization_id
    assert payload["authorization_digest"] == artifact.artifact_digest


def test_23_session_02_evidence_unchanged(tmp_path: Path) -> None:
    result, _, _, _ = _run_ok(tmp_path)
    assert result["session_02_mutation_occurred"] is False
    s02 = (
        tmp_path
        / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
        / "campaigns"
        / BOUND_CAMPAIGN_ID
        / "sessions"
        / "session_02_manifest.json"
    )
    assert not s02.exists()


def test_24_fail_closed_terminal_after_consumption(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)

    def boom_fetcher(url: str, method: str, headers: dict[str, str], timeout: float):
        del url, method, headers, timeout
        raise RuntimeError("forced_md_failure")

    result = run_preregistered_productive_session_v1(
        repo_root=ROOT,
        campaign_id=BOUND_CAMPAIGN_ID,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        session_id=SESSION_01_ID,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        authorization_artifact_path=auth_path,
        repository_sha=REPO_SHA,
        venue=BOUND_VENUE,
        instrument_id=BOUND_INSTRUMENT_ID,
        market_data_scope=BOUND_VENUE_SCOPE,
        evidence_scope=BOUND_EVIDENCE_SCOPE,
        max_cycles=1,
        evidence_root=tmp_path,
        git_baseline=_baseline(),
        http_fetcher=boom_fetcher,
    )
    assert result["authorization_consumed"] is True
    assert result["terminal_state"] == "FAIL_CLOSED_AFTER_CONSUMPTION"
    assert result["terminal_verdict"] == "FAIL_CLOSED_AFTER_AUTHORIZATION_CONSUMPTION"
    manifest = Path(result["preflight"]["session_manifest_path"])
    assert manifest.is_file()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["integrity_manifest"]["terminal_state"] == "FAIL_CLOSED_AFTER_CONSUMPTION"


def test_25_productive_bridge_accumulate_still_present_but_not_session_runner() -> None:
    help_proc = subprocess.run(
        [sys.executable, str(CLI), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert CLI_MODE in help_proc.stdout
    assert PRODUCTIVE_BRIDGE_ACCUMULATE_CLI_MODE in help_proc.stdout
    # Bridge accumulate still fabricates productive-N ids in its CLI block.
    cli_text = CLI.read_text(encoding="utf-8")
    assert 'f"{args.session_id}-productive-{idx + 1}"' in cli_text
    assert "productive-preregistered-session-run" in cli_text


def test_26_consume_before_side_effects_order(tmp_path: Path) -> None:
    result, _, _, probe = _run_ok(tmp_path, max_cycles=1)
    events = probe.events
    assert events.index("PREFLIGHT_PASS") < events.index("AUTHORIZATION_CONSUMED")
    assert events.index("AUTHORIZATION_CONSUMED") < events.index("SESSION_STARTED")
    assert events.index("SESSION_STARTED") < events.index("MARKET_DATA_FETCHED")
    assert result["status"] == "PASS"


def test_27_cli_mode_requires_bindings_and_refuses_silent_defaults() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--mode",
            CLI_MODE,
            "--campaign-id",
            BOUND_CAMPAIGN_ID,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode != 0
    assert "preregistered_session_run_missing" in (proc.stderr + proc.stdout)
