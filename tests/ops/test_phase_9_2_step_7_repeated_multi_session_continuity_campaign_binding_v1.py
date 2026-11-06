"""Tests for Step-7 repeated multi-session continuity campaign binding."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_bundle_v1 import (
    build_campaign_bundle_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    evaluate_step7_binding_gate_v1,
    run_step7_campaign_harness_binding_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_state_contract_v1 import (
    load_and_validate_campaign_state_contract_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_verifier_v1 import (
    verify_binding_manifest_v1,
    verify_campaign_bundle_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    CORE_LOGIC_CHANGE,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_SESSION_LADDER_COMPLETE,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    STEP7_BINDING_IMPLEMENTED,
    STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT,
    STEP7_CAMPAIGN_HARNESS_BOUND,
    STEP7_CAMPAIGN_OWNER_PRESENT,
    STEP7_CAMPAIGN_VERIFIER_PRESENT,
    STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT,
    STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT,
    TARGET_SESSION_ID_PREFIX,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.evidence_v1 import (
    _pass_session_v1,
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.parity_v1 import (
    assert_no_parallel_campaign_authority_v1,
    prove_phase92_step7_campaign_binding_parity_v1,
    prove_step7_reuse_bindings_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.py"
)


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _two_pass_sessions(
    *,
    repo: str | None = None,
    cfg: str | None = None,
) -> tuple[dict, dict]:
    repository_sha = repo or _sha()
    config_digest = cfg or _cfg()
    s1 = _pass_session_v1(
        session_id=f"{TARGET_SESSION_ID_PREFIX}_001",
        ordinal=1,
        repository_sha=repository_sha,
        config_digest=config_digest,
        state_before="state_root_A",
        state_after="state_root_B",
        authorization_id="auth_session_1",
        confirm_fp="confirm_fp_1",
    )
    s2 = _pass_session_v1(
        session_id=f"{TARGET_SESSION_ID_PREFIX}_002",
        ordinal=2,
        repository_sha=repository_sha,
        config_digest=config_digest,
        state_before="state_root_B",
        state_after="state_root_C",
        authorization_id="auth_session_2",
        confirm_fp="confirm_fp_2",
    )
    return s1, s2


def test_parity_reuse_and_binding_flags() -> None:
    parity = prove_phase92_step7_campaign_binding_parity_v1()
    reuse = prove_step7_reuse_bindings_v1()
    authority = assert_no_parallel_campaign_authority_v1()
    assert parity["ok"] is True
    assert reuse["ok"] is True
    assert authority["ok"] is True
    assert CORE_LOGIC_CHANGE is False
    assert NETWORK_SESSION_ALLOWED is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert PHASE_9_2_STEP_7_STATUS == "OPEN"
    assert PHASE_9_2_SESSION_LADDER_COMPLETE is False
    assert STEP7_BINDING_IMPLEMENTED is True
    assert STEP7_CAMPAIGN_OWNER_PRESENT is True
    assert STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT is True
    assert STEP7_CAMPAIGN_HARNESS_BOUND is True
    assert STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT is True
    assert STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT is True
    assert STEP7_CAMPAIGN_VERIFIER_PRESENT is True
    assert MULTI_SESSION_REQUIREMENT_EXPRESSION == ">1"
    assert multi_session_requirement_satisfied_v1(1) is False
    assert multi_session_requirement_satisfied_v1(2) is True
    assert reuse["STEP3_RESTART_SEMANTICS_REUSED"] is True
    assert reuse["STEP4_RECONNECT_SEMANTICS_REUSED"] is True
    assert reuse["STEP6_STALE_ADVERSE_SEMANTICS_REUSED"] is True


def test_campaign_contract_loads() -> None:
    contract = load_and_validate_campaign_state_contract_v1(repo_root=REPO_ROOT)
    assert contract["session_ladder_step"] == "MULTI_SESSION_CONTINUITY_CAMPAIGN"
    assert contract["multi_session_requirement"]["expression"] == ">1"
    assert contract["phase_9_2_step_7_status"] == "OPEN"


def test_harness_forbids_real_network() -> None:
    gate = evaluate_step7_binding_gate_v1(owner_go=True, request_real_network=True)
    assert gate["ok"] is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in gate["blockers"]
    harness = run_step7_campaign_harness_binding_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        owner_go=True,
        request_real_network=False,
        repo_root=REPO_ROOT,
    )
    assert harness["ok"] is True
    assert harness["NETWORK_SESSION_STARTED"] is False
    assert harness["PHASE_9_2_STEP_7_STATUS"] == "OPEN"


def test_one_session_bundle_fails() -> None:
    s1, _ = _two_pass_sessions()
    bundle = build_campaign_bundle_v1(
        sessions=[s1],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    verdict = verify_campaign_bundle_v1(bundle)
    assert verdict["ok"] is False
    assert any(b.startswith("MULTI_SESSION_REQUIREMENT_NOT_MET") for b in verdict["blockers"])


def test_multi_session_all_pass_bundle_passes() -> None:
    s1, s2 = _two_pass_sessions()
    bundle = build_campaign_bundle_v1(
        sessions=[s1, s2],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    verdict = verify_campaign_bundle_v1(bundle)
    assert verdict["ok"] is True
    assert verdict["multi_session_requirement_satisfied"] is True
    assert verdict["PHASE_9_2_SESSION_LADDER_COMPLETE"] is False
    assert verdict["PHASE_9_2_STEP_7_STATUS"] == "OPEN"


def test_one_failed_session_fails_campaign() -> None:
    s1, s2 = _two_pass_sessions()
    s2 = copy.deepcopy(s2)
    s2["verifier_result"] = {"ok": False, "status": "FAIL", "blockers": ["SYNTHETIC"]}
    s2["session_result"] = {"ok": False, "status": "FAIL", "observed_session": True}
    bundle = build_campaign_bundle_v1(
        sessions=[s1, s2],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    verdict = verify_campaign_bundle_v1(bundle)
    assert verdict["ok"] is False
    assert any(b.startswith("SESSION_VERIFIER_FAIL") for b in verdict["blockers"])


def test_state_discontinuity_fails() -> None:
    s1, s2 = _two_pass_sessions()
    s2 = copy.deepcopy(s2)
    s2["state_root_before"] = "state_root_OTHER"
    bundle = build_campaign_bundle_v1(
        sessions=[s1, s2],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    verdict = verify_campaign_bundle_v1(bundle)
    assert verdict["ok"] is False
    assert any(b.startswith("STATE_DISCONTINUITY") for b in verdict["blockers"])


def test_duplicate_economic_effect_fails() -> None:
    s1, s2 = _two_pass_sessions()
    s2 = copy.deepcopy(s2)
    s2["duplicate_confirmation_advance_count"] = 1
    s2["claims"]["DUPLICATE_CONFIRMATION_ADVANCE"] = True
    s2["telemetry"]["duplicate_confirmation_advance_count"] = 1
    bundle = build_campaign_bundle_v1(
        sessions=[s1, s2],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    verdict = verify_campaign_bundle_v1(bundle)
    assert verdict["ok"] is False
    assert "DUPLICATE_CONFIRMATION_ADVANCE_IN_CAMPAIGN" in verdict["blockers"] or any(
        "DUPLICATE_CONFIRMATION_ADVANCE" in b for b in verdict["blockers"]
    )

    s1b, s2b = _two_pass_sessions()
    s2b = copy.deepcopy(s2b)
    s2b["duplicate_fill_count"] = 1
    s2b["claims"]["DUPLICATE_FILL"] = True
    s2b["telemetry"]["duplicate_fill_count"] = 1
    bundle2 = build_campaign_bundle_v1(
        sessions=[s1b, s2b],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    verdict2 = verify_campaign_bundle_v1(bundle2)
    assert verdict2["ok"] is False
    assert "DUPLICATE_FILL_IN_CAMPAIGN" in verdict2["blockers"] or any(
        "DUPLICATE_FILL" in b for b in verdict2["blockers"]
    )


def test_repo_config_mismatch_fails_unless_governed() -> None:
    s1, s2 = _two_pass_sessions()
    s2 = copy.deepcopy(s2)
    s2["repository_sha"] = "deadbeef" * 5
    s2["config_digest"] = "cfg_other"
    bundle = build_campaign_bundle_v1(
        sessions=[s1, s2],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    verdict = verify_campaign_bundle_v1(bundle)
    assert verdict["ok"] is False
    assert any("MISMATCH" in b for b in verdict["blockers"])

    governed = build_campaign_bundle_v1(
        sessions=[s1, s2],
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        allowed_binding_transitions=[
            {
                "from_repository_sha": _sha(),
                "from_config_digest": _cfg(),
                "to_repository_sha": "deadbeef" * 5,
                "to_config_digest": "cfg_other",
                "explicitly_governed": True,
            }
        ],
    )
    verdict_g = verify_campaign_bundle_v1(governed)
    assert verdict_g["ok"] is True


def test_missing_stale_reconnect_restart_proof_fails() -> None:
    s1, s2 = _two_pass_sessions()
    for key in ("restart_recovery_result", "reconnect_result", "stale_adverse_result"):
        bad = copy.deepcopy(s2)
        bad[key] = {"ok": False, "status": "MISSING"}
        claim_map = {
            "restart_recovery_result": "RESTART_RECOVERY_PROVED",
            "reconnect_result": "BOUNDED_RECONNECT_PROVED",
            "stale_adverse_result": "STALE_ADVERSE_PROVED",
        }
        bad["claims"][claim_map[key]] = False
        bundle = build_campaign_bundle_v1(
            sessions=[s1, bad],
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
        )
        verdict = verify_campaign_bundle_v1(bundle)
        assert verdict["ok"] is False


def test_order_private_credential_reachability_fails() -> None:
    s1, s2 = _two_pass_sessions()
    for field, claim in (
        ("private_endpoint_reachable", "PRIVATE_ENDPOINT_REACHED"),
        ("credential_access_reachable", "EXCHANGE_CREDENTIAL_PATH_REACHED"),
        ("order_side_effect_occurred", "ORDER_SIDE_EFFECT_OCCURRED"),
    ):
        bad = copy.deepcopy(s2)
        bad[field] = True
        bad["claims"][claim] = True
        bad["telemetry"][field] = True
        bundle = build_campaign_bundle_v1(
            sessions=[s1, bad],
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
        )
        verdict = verify_campaign_bundle_v1(bundle)
        assert verdict["ok"] is False


def test_materialize_evidence_and_cli(tmp_path: Path) -> None:
    summary = materialize_capability_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path,
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["PHASE_9_2_STEP_7_STATUS"] == "OPEN"
    assert summary["PHASE_9_2_SESSION_LADDER_COMPLETE"] is False
    manifest = json.loads(
        (
            tmp_path / "repeated_multi_session_continuity_campaign_binding_manifest_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert verify_binding_manifest_v1(manifest)["ok"] is True

    proc = subprocess.run(
        [sys.executable, str(CLI), "preflight", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["NETWORK_SESSION_STARTED"] is False

    blocked = subprocess.run(
        [sys.executable, str(CLI), "preflight", "--request-real-network", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert blocked.returncode == 2
