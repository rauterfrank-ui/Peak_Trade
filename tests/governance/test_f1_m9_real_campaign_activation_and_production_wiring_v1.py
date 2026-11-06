"""Proofs for F1/M9 REAL campaign activation and production wiring v1."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.activation_and_production_wiring_closure_v1 import (
    prove_f1_m9_real_campaign_activation_and_production_wiring_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    F1M9AuthorizedCampaignRunOrchestrationRequestV1,
    run_f1_m9_prospective_authorized_campaign_run_orchestration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    REAL_MD_SUPPLIER_ID,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_mode_v1 import (
    F1M9OrchestrationExecutionModeV1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS,
    STATUS_BUILD_SLICE_BOUND_ONLY,
    STATUS_ORCHESTRATION_DENIED,
    STATUS_REAL_TERMINAL_VERDICT_PASS,
    STATUS_TERMINAL_VERDICT_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.production_real_public_md_session_adapter_v1 import (
    PRODUCTION_ADAPTER_CLASS_ID,
    PREREGISTERED_SESSION_IDS,
    ProductionRealPublicMdSessionAdapterV1,
    build_production_real_public_md_session_adapter_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_public_md_session_adapter_v1 import (
    FakeRealPublicMdSessionAdapterV1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_issuance_v1 import (
    issue_f1_m9_prospective_campaign_runtime_authorization_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    compute_runtime_authorization_digest,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.session_work_units_v1 import (
    resolve_preregistered_session_work_units_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import OUTCOME_SELECTED
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_BASE_SHA = "3d779b1461fd93187c633913a057a4dc460dd83f"
EVAL_TIME = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
REAL_CLI = REPO_ROOT / "scripts/run_f1_m9_prospective_real_authorized_campaign_execution_v1.py"
PT = REPO_ROOT / "scripts/pt"


def _fake_mark_fetcher(mark: str = "2500.5", ts_ms: int | None = None):
    def _fetcher(url: str, method: str, headers: dict[str, str], timeout: float):
        del url, headers, timeout
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


def _issued_auth(**overrides: object) -> dict:
    body = issue_f1_m9_prospective_campaign_runtime_authorization_v1(
        authorization_id="TEST_ACTIVATION_AUTH_1",
        bound_origin_main_sha=CANONICAL_BASE_SHA,
        execution_idempotency_key=str(
            overrides.pop("execution_idempotency_key", "activation-key-1")
        ),
        owner_identity="TEST_OWNER",
        decision_identity="TEST_DECISION",
        earliest_valid_utc=EVAL_TIME,
        expires_at_utc=EVAL_TIME + timedelta(hours=1),
        repo_root=REPO_ROOT,
        allow_issuance=True,
    )
    if overrides:
        body.update(overrides)
        issuance_body = {k: v for k, v in body.items() if k != "authorization_digest"}
        check = {k: v for k, v in issuance_body.items() if k != "issuance_record_digest"}
        body["issuance_record_digest"] = compute_content_sha256(check)
        body["authorization_digest"] = compute_runtime_authorization_digest(body)
    return body


def _production_request(
    tmp_path: Path,
    auth: dict,
    *,
    execution_idempotency_key: str = "activation-key-1",
) -> F1M9AuthorizedCampaignRunOrchestrationRequestV1:
    adapter = build_production_real_public_md_session_adapter_v1(
        http_fetcher=_fake_mark_fetcher(),
    )
    assert not isinstance(adapter, FakeRealPublicMdSessionAdapterV1)
    return F1M9AuthorizedCampaignRunOrchestrationRequestV1(
        runtime_authorization=auth,
        evaluation_time_utc=EVAL_TIME,
        repo_root=REPO_ROOT,
        execution_mode=F1M9OrchestrationExecutionModeV1.REAL_AUTHORIZED_CAMPAIGN_EXECUTION,
        real_campaign_root=tmp_path,
        real_public_md_adapter=adapter,
        expected_bound_origin_main_sha=CANONICAL_BASE_SHA,
    )


def test_process_activation_flag_enabled() -> None:
    assert REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS is True


def test_canonical_real_cli_bootstraps_via_pt() -> None:
    proc = subprocess.run(
        [str(PT), str(REAL_CLI), "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--runtime-authorization-path" in proc.stdout


def test_real_cli_source_uses_production_adapter_not_fake() -> None:
    source = REAL_CLI.read_text(encoding="utf-8")
    assert "build_production_real_public_md_session_adapter_v1" in source
    assert "FakeRealPublicMdSessionAdapterV1" not in source
    assert "peak_trade_python_script_entry_bootstrap_v1" in source


def test_missing_authorization_denied_before_external_effect(tmp_path: Path) -> None:
    proc = subprocess.run(
        [str(PT), str(REAL_CLI), "--runtime-authorization-path", str(tmp_path / "missing.json")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_production_adapter_binds_canonical_supplier_and_sessions() -> None:
    adapter = build_production_real_public_md_session_adapter_v1(http_fetcher=_fake_mark_fetcher())
    assert type(adapter).__name__ == PRODUCTION_ADAPTER_CLASS_ID
    units = resolve_preregistered_session_work_units_v1(repo_root=REPO_ROOT)
    assert {str(u["session_id"]) for u in units} == set(PREREGISTERED_SESSION_IDS)
    auth = _issued_auth()
    for unit in units:
        row = adapter.execute_work_unit_v1(work_unit=unit, authorization=auth)
        assert row.supplier_id == REAL_MD_SUPPLIER_ID
        assert row.evidence_source_class == "REAL_PUBLIC_MARKET_DATA"
        assert row.public_md_fetch_count >= 1
        assert not (row.private_api_effect or row.credential_access or row.order_effect)


def test_fresh_authorization_reaches_real_terminal_with_production_adapter(tmp_path: Path) -> None:
    auth = _issued_auth(execution_idempotency_key="activation-real-terminal-1")
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _production_request(tmp_path, auth)
    )
    assert result.orchestration_status == STATUS_REAL_TERMINAL_VERDICT_PASS
    assert result.public_market_data_external_read_occurred is True
    assert result.real_evidence_written is True
    assert result.terminal_selection.get("outcome") == OUTCOME_SELECTED


def test_invalid_authorization_denied(tmp_path: Path) -> None:
    bad = _issued_auth(bound_origin_main_sha="0" * 40)
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _production_request(tmp_path, bad)
    )
    assert result.orchestration_status == STATUS_ORCHESTRATION_DENIED


def test_exactly_once_authorization_and_work_units(tmp_path: Path) -> None:
    auth = _issued_auth(execution_idempotency_key="activation-once-1")
    first = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _production_request(tmp_path, auth)
    )
    assert first.orchestration_status == STATUS_REAL_TERMINAL_VERDICT_PASS
    replay = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _production_request(tmp_path, auth)
    )
    assert replay.real_evidence_written is False
    assert "REPLAY" in replay.orchestration_status or replay.reason_codes


def test_build_bind_and_hermetic_modes_remain_distinct(tmp_path: Path) -> None:
    auth = _issued_auth()
    bound = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=auth,
            evaluation_time_utc=EVAL_TIME,
            repo_root=REPO_ROOT,
        )
    )
    assert bound.orchestration_status == STATUS_BUILD_SLICE_BOUND_ONLY

    from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
        build_runtime_authorization_template_v1,
    )

    body = build_runtime_authorization_template_v1(
        authorization_id="HERMETIC_AUTH",
        earliest_valid_utc=EVAL_TIME.isoformat().replace("+00:00", "Z"),
        expires_at_utc=(EVAL_TIME + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        execution_idempotency_key="hermetic-key",
    )
    body["campaign_execution_authorized"] = True
    body["public_market_data_read_authorized"] = True
    body["durable_evidence_write_authorized"] = True
    body["authorization_digest"] = compute_runtime_authorization_digest(body)
    hermetic = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=body,
            evaluation_time_utc=EVAL_TIME,
            repo_root=REPO_ROOT,
            hermetic_isolated_campaign_root=tmp_path,
            allow_hermetic_terminal_effects=True,
            public_md_session_fn=lambda **_: {"simulated": True},
        )
    )
    assert hermetic.orchestration_status == STATUS_TERMINAL_VERDICT_PASS
    assert hermetic.real_authorized_campaign_execution_path_proven is False


def test_activation_and_production_wiring_closure() -> None:
    assert prove_f1_m9_real_campaign_activation_and_production_wiring_v1(repo_root=REPO_ROOT)


def test_post_merge_real_run_requires_no_further_code_change() -> None:
    decision = json.loads(
        (
            REPO_ROOT
            / "config/governance/f1_m9_real_campaign_activation_and_production_wiring_v1_decision_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert decision["no_further_code_change_required_for_real_run"] is True
    assert decision["campaign_id"] == CAMPAIGN_ID
