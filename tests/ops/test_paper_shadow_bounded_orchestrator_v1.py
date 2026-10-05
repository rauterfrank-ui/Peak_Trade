"""Paper-Shadow bounded orchestrator v1 contract tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.bounded_limits_v1 import (
    BoundedRunCountersV1,
    check_operational_bounds_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.fixpoint_self_check_v1 import (
    evaluate_fixpoint_self_check_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.owner_go_validator_v1 import (
    validate_owner_go_authorization_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.orchestrator_v1 import (
    run_paper_shadow_preflight_only_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
    RunContractError,
    load_paper_shadow_run_contract_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_state_machine_v1 import (
    RunLifecycleState,
    RunStateMachineError,
    RunStateMachineV1,
)
from tests.ops._paper_shadow_bounded_orchestrator_offline_reproof_v1 import (
    run_offline_integration_reproof_v1,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_DIR = REPO / "evidence/research/paper_shadow_run_contract_v1/20261004T211710Z"
FIXPOINT_SHA = "1dd90cb053522d953aa7518541da2c0d1940ffee"
FIXPOINT_TREE = "16b0dc9e78e0dc1f24ddcb218514e69f5c5462c4"


def _canonical_contract_paths(tmp_path: Path) -> tuple[Path, Path]:
    from src.ops.paper_shadow_bounded_orchestrator_v1.run_settings_manifest_v1 import (
        build_run_settings_manifest_v1,
    )

    manifest = build_run_settings_manifest_v1(repo_root=REPO)
    digest = str(manifest["RUN_SETTINGS_DIGEST"])
    contract_path = tmp_path / "run_contract_v1.json"
    contract_path.write_text(
        json.dumps(
            {
                "RUN_ID": "PAPER_SHADOW_RUN_001",
                "RUN_TYPE": "BOUNDED_PAPER_SHADOW",
                "RUN_DURATION_SECONDS": 3600,
                "MAX_OBSERVATION_COUNT": 2000,
                "MAX_CYCLE_COUNT": 2000,
                "MAX_SIMULATED_EXECUTION_COUNT": 120,
                "MAX_SIMULATED_OPEN_POSITION_COUNT": 1,
                "ENTER_REQUIRED_FOR_SUCCESS": False,
                "FIXPOINT_SHA": FIXPOINT_SHA,
                "FIXPOINT_TREE": FIXPOINT_TREE,
                "SETTINGS_DIGEST": digest,
                "OBSERVATION_SOURCE": "wallclock_public_md_observe_v1",
                "EXECUTION_SINK": "SIMULATED_ONLY",
            }
        ),
        encoding="utf-8",
    )
    digest_path = tmp_path / "run_settings_digest.json"
    digest_path.write_text(
        json.dumps({"RUN_ID": "PAPER_SHADOW_RUN_001", "SETTINGS_DIGEST": digest}),
        encoding="utf-8",
    )
    return contract_path, digest_path


def test_run_contract_loads_from_evidence_bundle() -> None:
    c = load_paper_shadow_run_contract_v1(
        contract_path=CONTRACT_DIR / "run_contract_v1.json",
        settings_digest_path=CONTRACT_DIR / "run_settings_digest.json",
    )
    assert c.run_id == "PAPER_SHADOW_RUN_001"
    assert c.run_duration_seconds == 3600
    assert c.max_observation_count == 2000
    assert c.enter_required_for_success is False


def test_preflight_only_go_ready(tmp_path: Path) -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    if head != FIXPOINT_SHA:
        pytest.skip("fixpoint head mismatch")
    contract_path, digest_path = _canonical_contract_paths(tmp_path)
    result = run_paper_shadow_preflight_only_v1(
        contract_path=contract_path,
        repo_root=REPO,
        settings_digest_path=digest_path,
    )
    assert result.ok is True
    assert result.final_preflight_state == "GO_READY_AWAITING_EXPLICIT_OWNER_GO"
    assert result.run_started is False
    assert result.owner_go_consumed is False


def test_owner_go_validator_wrong_digest_fails() -> None:
    c = load_paper_shadow_run_contract_v1(
        contract_path=CONTRACT_DIR / "run_contract_v1.json",
        settings_digest_path=CONTRACT_DIR / "run_settings_digest.json",
    )
    auth = tmp_path_authorization(c, digest="deadbeef")
    val = validate_owner_go_authorization_v1(
        contract=c,
        authorization_path=auth,
        observation_token=SHADOW_OBSERVATION_OPERATOR_GO,
        activation_token=SHADOW_ACTIVATION_OPERATOR_GO,
    )
    assert val.ok is False
    assert "SETTINGS_DIGEST_MISMATCH" in val.blockers


def tmp_path_authorization(c, digest: str) -> Path:
    p = Path("/tmp") / "paper_shadow_auth_test.json"
    p.write_text(
        json.dumps(
            {
                "BOUND_TO": {
                    "RUN_ID": c.run_id,
                    "FIXPOINT_SHA": c.fixpoint_sha,
                    "SETTINGS_DIGEST": digest,
                    "RUN_DURATION_SECONDS": c.run_duration_seconds,
                    "MAX_OBSERVATION_COUNT": c.max_observation_count,
                    "MAX_CYCLE_COUNT": c.max_cycle_count,
                    "MAX_SIMULATED_EXECUTION_COUNT": c.max_simulated_execution_count,
                    "EXECUTION_SINK": c.execution_sink,
                },
                "OBSERVATION_TOKEN": SHADOW_OBSERVATION_OPERATOR_GO,
                "ACTIVATION_TOKEN": SHADOW_ACTIVATION_OPERATOR_GO,
            }
        ),
        encoding="utf-8",
    )
    return p


def test_owner_go_valid_binding() -> None:
    c = load_paper_shadow_run_contract_v1(
        contract_path=CONTRACT_DIR / "run_contract_v1.json",
        settings_digest_path=CONTRACT_DIR / "run_settings_digest.json",
    )
    auth = tmp_path_authorization(c, digest=c.settings_digest)
    val = validate_owner_go_authorization_v1(
        contract=c,
        authorization_path=auth,
        observation_token=SHADOW_OBSERVATION_OPERATOR_GO,
        activation_token=SHADOW_ACTIVATION_OPERATOR_GO,
    )
    assert val.ok is True
    assert val.owner_go_consumed is False


def test_fixpoint_self_check(tmp_path: Path) -> None:
    if (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        != FIXPOINT_SHA
    ):
        pytest.skip("not on fixpoint")
    contract_path, digest_path = _canonical_contract_paths(tmp_path)
    c = load_paper_shadow_run_contract_v1(
        contract_path=contract_path,
        settings_digest_path=digest_path,
    )
    chk = evaluate_fixpoint_self_check_v1(
        repo_root=REPO,
        expected_fixpoint_sha=c.fixpoint_sha,
        expected_tree_sha=c.fixpoint_tree,
        settings_digest=c.settings_digest,
    )
    assert chk.ok is True


def test_operational_bounds_stop() -> None:
    c = load_paper_shadow_run_contract_v1(
        contract_path=CONTRACT_DIR / "run_contract_v1.json",
        settings_digest_path=CONTRACT_DIR / "run_settings_digest.json",
    )
    counters = BoundedRunCountersV1(observation_count=2000)
    hit = check_operational_bounds_v1(contract=c, counters=counters)
    assert hit.stop is True
    assert hit.reason == "MAX_OBSERVATION_BOUND"


def test_state_machine_no_implicit_running() -> None:
    sm = RunStateMachineV1()
    sm.begin_preflight()
    sm.complete_preflight_ready()
    with pytest.raises(RunStateMachineError):
        sm.start_running()


def test_cli_preflight_only_exit_zero(tmp_path: Path) -> None:
    if (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        != FIXPOINT_SHA
    ):
        pytest.skip("not on fixpoint")
    contract_path, digest_path = _canonical_contract_paths(tmp_path)
    proc = subprocess.run(
        [
            str(REPO / "scripts/pt"),
            str(REPO / "scripts/ops/run_paper_shadow_bounded_orchestrator_v1.py"),
            "--contract",
            str(contract_path),
            "--settings-digest",
            str(digest_path),
            "--json",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(
        proc.stdout.split("\n")[-1] if "REASON_CODE" in proc.stdout else proc.stdout
    )
    # pt wrapper may prefix diagnostics — parse last json block
    if "FINAL_PREFLIGHT_STATE" not in payload:
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
        payload = json.loads(lines[-1])
    assert payload["FINAL_PREFLIGHT_STATE"] == "GO_READY_AWAITING_EXPLICIT_OWNER_GO"


def test_record_productive_cycle_passive_telemetry_projection() -> None:
    from src.ops.paper_shadow_bounded_orchestrator_v1.run_evidence_v1 import (
        RunEvidenceAccumulatorV1,
    )

    acc = RunEvidenceAccumulatorV1(
        run_id="PAPER_SHADOW_RUN_TEST",
        fixpoint_sha="abc",
        fixpoint_tree="def",
        settings_digest="digest",
    )
    acc.record_productive_cycle(
        bridge_cycle={
            "cycle_id": "cycle_test",
            "decision_outcome": "no_action",
            "selected_side": "none",
            "reason_codes": ["no_action"],
            "feature_blockers": [],
            "required_window_complete": True,
        }
    )
    assert acc.decision_outcomes["no_action"] == 1
    assert acc.cycle_samples[0]["reason_codes"] == ["no_action"]
    assert acc.cycle_samples[0]["required_window_complete"] is True


def test_offline_integration_reproof(tmp_path: Path) -> None:
    reproof = run_offline_integration_reproof_v1(work_root=tmp_path)
    assert reproof["REAL_POST_COUNT"] == 0
    assert reproof["EVENT_SUBSTITUTION_COUNT"] == 0
    assert reproof["ok"] is True


def test_orchestrator_package_has_no_webui_imports() -> None:
    from src.ops.paper_shadow_bounded_orchestrator_v1.orchestrator_v1 import (
        _scan_orchestrator_for_webui_imports,
    )

    assert (
        _scan_orchestrator_for_webui_imports(REPO / "src/ops/paper_shadow_bounded_orchestrator_v1")
        == 0
    )


def test_wrong_run_id_contract_fails() -> None:
    bad = Path("/tmp/bad_run_contract.json")
    bad.write_text(
        json.dumps(
            {
                "RUN_ID": "OTHER",
                "RUN_DURATION_SECONDS": 3600,
                "MAX_OBSERVATION_COUNT": 1,
                "MAX_CYCLE_COUNT": 1,
                "MAX_SIMULATED_EXECUTION_COUNT": 1,
                "MAX_SIMULATED_OPEN_POSITION_COUNT": 1,
                "ENTER_REQUIRED_FOR_SUCCESS": False,
                "FIXPOINT_SHA": FIXPOINT_SHA,
                "FIXPOINT_TREE": FIXPOINT_TREE,
                "SETTINGS_DIGEST": "abc",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RunContractError):
        load_paper_shadow_run_contract_v1(contract_path=bad)
