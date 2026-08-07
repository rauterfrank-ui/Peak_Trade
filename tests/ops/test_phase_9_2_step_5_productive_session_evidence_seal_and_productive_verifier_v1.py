"""Tests for Step-5 productive session evidence seal + productive verifier.

No network session. No auth/token issuance or consumption. No secrets.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.evidence_v1 import (
    materialize_terminal_evidence_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.constants_v1 import (
    CANONICAL_SESSION_RELATIVE_PATH,
    CAPABILITY_ID,
    EXPECTED_HEARTBEAT_COUNT,
    EXPECTED_PUBLIC_MD_REQUEST_COUNT,
    NEXT_OPEN_PHASE_9_2_STEP,
    OFFLINE_VERIFIER_DOMAIN,
    OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION,
    PHASE_9_2_STEP_3_STATUS,
    PHASE_9_2_STEP_4_STATUS,
    PHASE_9_2_STEP_5_STATUS,
    PHASE_9_2_STEP_6_STATUS,
    PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER,
    PRODUCTIVE_VERIFIER_DOMAIN,
    SESSION_CONTRACT_SECONDS_EXPECTED,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.evidence_v1 import (
    materialize_seal_evidence_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.productive_session_verifier_v1 import (
    assert_offline_verifier_semantics_unchanged_v1,
    verify_productive_session_evidence_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.seal_v1 import (
    seal_productive_session_evidence_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SESSION = REPO_ROOT / CANONICAL_SESSION_RELATIVE_PATH
EXPECTED_SHA = "5819d971488e05db374f0720884cfea5672832d5"


def _require_canonical_session() -> Path:
    if not CANONICAL_SESSION.is_dir():
        pytest.skip("canonical productive session evidence not present")
    return CANONICAL_SESSION


def _clone_session(tmp_path: Path) -> Path:
    src = _require_canonical_session()
    dst = tmp_path / "session_clone"
    shutil.copytree(src, dst)
    return dst


def _rewrite_json(path: Path, mutator: Any) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def test_domain_constants() -> None:
    assert OFFLINE_VERIFIER_DOMAIN == "IMPLEMENTATION_PROOF"
    assert PRODUCTIVE_VERIFIER_DOMAIN == "AUTHORIZED_PRODUCTIVE_SESSION"
    assert OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION is True
    assert PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER is False
    assert PHASE_9_2_STEP_5_STATUS == "CLOSED_PASS"
    assert PHASE_9_2_STEP_3_STATUS == "OPEN"
    assert PHASE_9_2_STEP_4_STATUS == "CLOSED_PASS"
    assert PHASE_9_2_STEP_6_STATUS == "OPEN"
    assert NEXT_OPEN_PHASE_9_2_STEP == "3_RESTART_RECOVERY_PRODUCTIVE_REAL_NETWORK_SESSION"
    assert SESSION_CONTRACT_SECONDS_EXPECTED == 7200
    assert CAPABILITY_ID.endswith("PRODUCTIVE_VERIFIER_V1")


def test_productive_verifier_pass_against_canonical_session() -> None:
    session = _require_canonical_session()
    result = verify_productive_session_evidence_v1(
        session,
        expected_repository_sha=EXPECTED_SHA,
        expected_public_md_request_count=EXPECTED_PUBLIC_MD_REQUEST_COUNT,
        expected_heartbeat_count=EXPECTED_HEARTBEAT_COUNT,
        repo_root=REPO_ROOT,
    )
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    assert result["checks"]["SESSION_DURATION_REQUIREMENT_PASS"] is True
    assert result["checks"]["PUBLIC_MD_REQUEST_COUNT"] == 3391
    assert result["checks"]["HEARTBEAT_COUNT"] == 1130
    assert result["checks"]["MIN_REQUEST_INTERVAL_SECONDS"] >= 2.0
    assert result["checks"]["ZERO_INTERVAL_BURST_DETECTED"] is False
    assert result["checks"]["RATE_LIMIT_EVENTS"] == 0
    assert result["checks"]["RETRY_BUDGET_EXCEEDED"] is False
    assert result["checks"]["PUBLIC_ENDPOINTS_ONLY"] is True
    assert result["checks"]["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert result["checks"]["AUTH_HEADER_PRESENT"] is False
    assert result["checks"]["CREDENTIAL_ACCESS_DETECTED"] is False
    assert result["checks"]["ORDER_SIDE_EFFECT_OCCURRED"] is False
    assert result["checks"]["AUTHORIZATION_CONSUMED_ONCE"] is True
    assert result["checks"]["CONFIRM_TOKEN_PLAINTEXT_EXPOSED"] is False
    assert result["checks"]["SESSION_PROCESS_EXITED"] is True
    assert result["checks"]["RESIDUAL_PROCESS_FOUND"] is False
    assert result["checks"]["SESSION_LOCK_RELEASED"] is True
    assert result["checks"]["REPOSITORY_SHA_MATCH"] is True
    assert result["checks"]["CONFIG_DIGEST_MATCH"] is True
    assert result["checks"]["SESSION_CONTRACT_DIGEST_MATCH"] is True
    assert result["checks"]["CLAIMS_MATCH_TELEMETRY"] is True
    assert result["offline_verifier_result"]["ok"] is False
    assert result["productive_session_invalidated_by_offline_verifier"] is False


def test_seal_idempotent_and_does_not_rewrite_raw(tmp_path: Path) -> None:
    session = _require_canonical_session()
    before = {p.relative_to(session): p.read_bytes() for p in session.rglob("*") if p.is_file()}
    seal_path = tmp_path / "seal.json"
    seal1 = seal_productive_session_evidence_v1(
        session_root=session,
        expected_repository_sha=EXPECTED_SHA,
        seal_output_path=seal_path,
        repo_root=REPO_ROOT,
    )
    seal2 = seal_productive_session_evidence_v1(
        session_root=session,
        expected_repository_sha=EXPECTED_SHA,
        seal_output_path=seal_path,
        repo_root=REPO_ROOT,
    )
    assert seal1["PRODUCTIVE_EVIDENCE_SEALED"] is True
    assert seal1["seal_digest"] == seal2["seal_digest"]
    after = {p.relative_to(session): p.read_bytes() for p in session.rglob("*") if p.is_file()}
    assert before == after
    assert seal1["claims"]["RAW_SESSION_EVIDENCE_CHANGED"] is False
    assert seal1["claims"]["NEXT_OPEN_PHASE_9_2_STEP"] == (
        "3_RESTART_RECOVERY_PRODUCTIVE_REAL_NETWORK_SESSION"
    )
    assert seal1["claims"]["PHASE_9_2_STEP_4_STATUS"] == "CLOSED_PASS"
    assert seal1["claims"]["PHASE_9_2_STEP_3_STATUS"] == "OPEN"


def test_negative_short_runtime(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["wallclock_seconds"] = 100.0
        payload["telemetry"]["session_monotonic_wallclock_seconds"] = 100.0
        payload["claims"]["SESSION_MONOTONIC_WALLCLOCK_SECONDS"] = 100.0

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "SESSION_WALLCLOCK_SECONDS_BELOW_MINIMUM" in result["blockers"]


def test_negative_min_interval(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["telemetry"]["min_observed_interval_seconds"] = 0.5

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "MIN_REQUEST_INTERVAL_SECONDS_BELOW_MINIMUM" in result["blockers"]


def test_negative_private_endpoint(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["telemetry"]["private_endpoint_access_occurred"] = True
        payload["claims"]["PRIVATE_ENDPOINT_ACCESS_OCCURRED"] = True

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "PRIVATE_ENDPOINT_REACHABLE" in result["blockers"]


def test_negative_auth_header(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["telemetry"]["auth_header_transmitted"] = True
        payload["claims"]["AUTH_HEADER_TRANSMITTED"] = True

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "AUTH_HEADER_PRESENT" in result["blockers"]


def test_negative_credential_access(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["telemetry"]["credential_access_occurred"] = True
        payload["claims"]["CREDENTIAL_ACCESS_OCCURRED"] = True

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "CREDENTIAL_ACCESS_DETECTED" in result["blockers"]


def test_negative_order_side_effect(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["telemetry"]["order_side_effect_occurred"] = True
        payload["claims"]["ORDER_SIDE_EFFECT_OCCURRED"] = True

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "ORDER_SIDE_EFFECT_OCCURRED" in result["blockers"]


def test_negative_multi_authorization_consume(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)
    ledger = clone / "persistence" / "step5_authorization_consumption_ledger_v1.jsonl"
    line = ledger.read_text(encoding="utf-8").strip().splitlines()[0]
    ledger.write_text(line + "\n" + line + "\n", encoding="utf-8")
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "AUTHORIZATION_CONSUMED_NOT_ONCE" in result["blockers"]


def test_negative_token_plaintext_leak(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)
    (clone / "leak.txt").write_text("PTCONFIRMv1_LEAKEDTOKENVALUE1234567890\n", encoding="utf-8")
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "CONFIRM_TOKEN_IN_EVIDENCE" in result["blockers"]


def test_negative_residual_process(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)
    result = verify_productive_session_evidence_v1(
        clone,
        expected_repository_sha=EXPECTED_SHA,
        repo_root=REPO_ROOT,
        residual_process_found=True,
    )
    assert result["ok"] is False
    assert "RESIDUAL_PROCESS_FOUND" in result["blockers"]


def test_negative_repository_digest_mismatch(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)
    result = verify_productive_session_evidence_v1(
        clone,
        expected_repository_sha="0" * 40,
        repo_root=REPO_ROOT,
    )
    assert result["ok"] is False
    assert "REPOSITORY_SHA_MISMATCH" in result["blockers"]


def test_negative_config_digest_mismatch(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["config_digest"] = "deadbeef" * 8

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "CONFIG_DIGEST_MISMATCH" in result["blockers"]


def test_negative_contract_digest_mismatch(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["session_contract_digest"] = "cafebabe" * 8

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert "SESSION_CONTRACT_DIGEST_MISMATCH" in result["blockers"]


def test_negative_claims_telemetry_mismatch(tmp_path: Path) -> None:
    clone = _clone_session(tmp_path)

    def mut(payload: dict[str, Any]) -> None:
        payload["claims"]["REQUEST_COUNT"] = 1
        # keep telemetry request_count unchanged → mismatch

    _rewrite_json(clone / "operator_public_result.json", mut)
    result = verify_productive_session_evidence_v1(
        clone, expected_repository_sha=EXPECTED_SHA, repo_root=REPO_ROOT
    )
    assert result["ok"] is False
    assert any(
        "CLAIM_TELEMETRY_MISMATCH" in b
        or b == "CLAIMS_TELEMETRY_MISMATCH"
        or b == "SESSION_INTERNAL_CONSISTENCY_FAIL"
        for b in result["blockers"]
    )


def test_offline_implementation_verifier_semantics_unchanged(tmp_path: Path) -> None:
    impl_summary = materialize_terminal_evidence_v1(
        repository_sha=EXPECTED_SHA,
        evidence_root=tmp_path / "impl_evidence",
        repo_root=REPO_ROOT,
    )
    assert impl_summary["ok"] is True
    impl_manifest = json.loads(
        (tmp_path / "impl_evidence" / "fixtures" / "manifest_v1.json").read_text(encoding="utf-8")
    )
    assert verify_session_manifest_v1(impl_manifest)["ok"] is True

    session = _require_canonical_session()
    prod_manifest = json.loads(
        (session / "evidence" / "session_terminal_manifest_v1.json").read_text(encoding="utf-8")
    )
    regression = assert_offline_verifier_semantics_unchanged_v1(
        implementation_manifest=impl_manifest,
        productive_manifest=prod_manifest,
    )
    assert regression["ok"] is True
    assert regression["offline_verifier_semantics_changed"] is False
    offline_prod = verify_session_manifest_v1(prod_manifest)
    assert offline_prod["ok"] is False
    for required in (
        "NETWORK_SESSION_MUST_REMAIN_FALSE_IN_IMPLEMENTATION_EVIDENCE",
        "AUTHORIZATION_MUST_NOT_BE_CONSUMED",
        "CONFIRM_TOKEN_MUST_NOT_BE_CONSUMED",
    ):
        assert required in offline_prod["blockers"]


def test_materialize_seal_evidence(tmp_path: Path) -> None:
    summary = materialize_seal_evidence_v1(
        repository_sha=EXPECTED_SHA,
        session_root=_require_canonical_session(),
        evidence_root=tmp_path / "docs_evidence",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["raw_session_evidence_changed"] is False
    assert summary["network_session_started"] is False
    assert Path(summary["productive_evidence_seal_path"]).is_file()
    seal = json.loads(Path(summary["productive_evidence_seal_path"]).read_text(encoding="utf-8"))
    probe = {k: v for k, v in seal.items() if k != "seal_digest"}
    assert seal["seal_digest"] == sha256_canonical_v1(probe)
