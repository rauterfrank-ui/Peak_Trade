"""Production REAL CLI entry execution smoke (hermetic HTTP boundary only)."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    DURABLE_CAMPAIGN_ROOT_REL,
    REAL_MD_SUPPLIER_ID,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    CONSUMPTION_LEDGER_FILENAME,
    REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS,
    STATUS_REAL_TERMINAL_VERDICT_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.production_real_public_md_session_adapter_v1 import (
    HERMETIC_PUBLIC_MD_BOUNDARY_ENV_V1,
    HERMETIC_PUBLIC_MD_MARKER_ENV_V1,
    PRODUCTION_ADAPTER_CLASS_ID,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_issuance_v1 import (
    issue_f1_m9_prospective_campaign_runtime_authorization_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PT = REPO_ROOT / "scripts/pt"
REAL_CLI = REPO_ROOT / "scripts/run_f1_m9_prospective_real_authorized_campaign_execution_v1.py"
CANONICAL_DURABLE_ROOT = (REPO_ROOT / DURABLE_CAMPAIGN_ROOT_REL).resolve()
SMOKE_TIMEOUT_SECONDS = 120


def _head_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT),
        text=True,
    ).strip()


def _issue_smoke_auth(*, auth_path: Path, authorization_id: str, idempotency: str) -> dict:
    now = datetime.now(timezone.utc)
    body = issue_f1_m9_prospective_campaign_runtime_authorization_v1(
        authorization_id=authorization_id,
        bound_origin_main_sha=_head_sha(),
        execution_idempotency_key=idempotency,
        owner_identity="TEST_PRODUCTION_CLI_ENTRY_SMOKE_V1",
        decision_identity="F1_M9_PRODUCTION_REAL_CLI_ENTRY_EXECUTION_SMOKE_V1",
        earliest_valid_utc=now - timedelta(minutes=5),
        expires_at_utc=now + timedelta(hours=1),
        repo_root=REPO_ROOT,
        allow_issuance=True,
    )
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


def _run_production_cli(
    *,
    auth_path: Path,
    campaign_root: Path,
    marker_path: Path,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env[HERMETIC_PUBLIC_MD_BOUNDARY_ENV_V1] = "1"
    env[HERMETIC_PUBLIC_MD_MARKER_ENV_V1] = str(marker_path)
    cmd = [
        str(PT),
        str(REAL_CLI),
        "--runtime-authorization-path",
        str(auth_path),
        "--expected-bound-origin-main-sha",
        _head_sha(),
        "--isolated-real-campaign-root",
        str(campaign_root),
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=SMOKE_TIMEOUT_SECONDS,
        env=env,
        check=False,
    )


def _parse_cli_json(stdout: str) -> dict:
    start = stdout.find("{")
    if start < 0:
        raise AssertionError(f"CLI_JSON_MISSING:{stdout[-500:]}")
    return json.loads(stdout[start:])


def test_production_real_cli_entry_execution_smoke_v1(tmp_path: Path) -> None:
    marker = tmp_path / "network_boundary.marker"
    campaign_root = tmp_path / "isolated_campaign"
    auth_path = tmp_path / "TEST_PRODUCTION_CLI_SMOKE_AUTH.json"
    _issue_smoke_auth(
        auth_path=auth_path,
        authorization_id="TEST_PRODUCTION_CLI_SMOKE_AUTH",
        idempotency="production-cli-smoke-exec-1",
    )
    durable_before = (
        set(CANONICAL_DURABLE_ROOT.rglob("*")) if CANONICAL_DURABLE_ROOT.is_dir() else set()
    )

    proc = _run_production_cli(
        auth_path=auth_path,
        campaign_root=campaign_root,
        marker_path=marker,
    )
    assert proc.returncode == 0, proc.stderr[-2000:] + proc.stdout[-2000:]
    result = _parse_cli_json(proc.stdout)

    assert REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS is True
    assert result["execution_mode"] == "REAL_AUTHORIZED_CAMPAIGN_EXECUTION"
    assert result["orchestration_status"] == STATUS_REAL_TERMINAL_VERDICT_PASS
    assert result["public_market_data_external_read_occurred"] is True
    assert result["real_evidence_written"] is True
    assert result["productive_apply_occurred"] is False

    marker_text = marker.read_text(encoding="utf-8")
    assert "session_01" in marker_text
    assert "session_02" in marker_text

    ledger = campaign_root / "authorization" / CONSUMPTION_LEDGER_FILENAME
    assert ledger.is_file()
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1

    durable_after = (
        set(CANONICAL_DURABLE_ROOT.rglob("*")) if CANONICAL_DURABLE_ROOT.is_dir() else set()
    )
    assert durable_before == durable_after

    replay = _run_production_cli(
        auth_path=auth_path,
        campaign_root=campaign_root,
        marker_path=tmp_path / "network_boundary_replay.marker",
    )
    replay_result = _parse_cli_json(replay.stdout)
    assert replay_result.get("real_evidence_written") is False


def test_production_real_cli_denies_before_network_boundary_v1(tmp_path: Path) -> None:
    marker = tmp_path / "deny.marker"
    campaign_root = tmp_path / "deny_campaign"
    missing_auth = tmp_path / "missing_authorization.json"
    proc_missing = _run_production_cli(
        auth_path=missing_auth,
        campaign_root=campaign_root,
        marker_path=marker,
    )
    assert proc_missing.returncode != 0
    assert not marker.exists()

    bad_auth = tmp_path / "bad_authorization.json"
    body = _issue_smoke_auth(
        auth_path=bad_auth,
        authorization_id="TEST_PRODUCTION_CLI_SMOKE_BAD_AUTH",
        idempotency="production-cli-smoke-deny-1",
    )
    body["bound_origin_main_sha"] = "0" * 40
    bad_auth.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    marker2 = tmp_path / "deny2.marker"
    proc_bad = _run_production_cli(
        auth_path=bad_auth,
        campaign_root=tmp_path / "deny_campaign_2",
        marker_path=marker2,
    )
    assert proc_bad.returncode != 0
    assert not marker2.exists()


def test_production_entry_smoke_freeze_contract_v1() -> None:
    """Documented production entry wiring contract (no Fake adapter on CLI path)."""
    cli_source = REAL_CLI.read_text(encoding="utf-8")
    assert "build_production_real_public_md_session_adapter_v1" in cli_source
    assert "FakeRealPublicMdSessionAdapterV1" not in cli_source
    assert PRODUCTION_ADAPTER_CLASS_ID == "ProductionRealPublicMdSessionAdapterV1"
    assert REAL_MD_SUPPLIER_ID == "CANONICAL_VOLATILITY_PREREGISTERED_PUBLIC_MD_SOURCE_V1"
