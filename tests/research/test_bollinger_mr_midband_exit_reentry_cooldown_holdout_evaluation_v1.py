"""Synthetic/structural tests for Exit V8 holdout evaluation wiring v1.

No holdout data access. Does not call run_holdout_evaluation / run_arm /
resolve_holdout_archive_root / load_member_bars / verify_holdout_panel_hashes.
Does not set the execution GO in a way that starts the CLI runner.
"""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

import src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1 as holdout_pkg
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.constants_v1 import (
    CLI_REL_PATH,
    CONTRACT_REL_PATH,
    DATASET_ID,
    HOLDOUT_PREREGISTRATION_DIGEST,
    HYPOTHESIS_ID,
    PANEL_ID,
    REQUIRED_ENTRY_LANE_STATUS,
    REQUIRED_EXIT_LANE_STATUS,
    REQUIRED_SUCCESSOR_STATUS,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.execution_authorization_v1 import (
    AUTH_DATASET_ENV,
    AUTH_DIGEST_ENV,
    AUTH_HEAD_SHA_ENV,
    AUTH_PANEL_ENV,
    AUTH_SUCCESSOR_ENV,
    assert_execution_authorization_bound,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.structural_preflight_v1 import (
    assert_run_slot_available,
    run_structural_preflight,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistration_v1 import (
    EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST,
    OPERATOR_GO_ENV,
    REQUIRED_FROZEN_PARAMETERS,
    HoldoutPreregistrationError,
    assert_execution_go_present,
    assert_holdout_run_not_yet_consumed,
    load_and_validate_repo_holdout_contract,
    preflight_holdout_execution_gates,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
RUNNER_PATH = REPO / CLI_REL_PATH
EVAL_PKG = REPO / "src/research/bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1"
V7_SUMMARY = (
    REPO
    / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7/summary.json"
)
V8_SUMMARY = (
    REPO
    / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v8/summary.json"
)
V8_MANIFEST = (
    REPO
    / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v8/MANIFEST.sha256"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _auth_env(head: str) -> dict[str, str]:
    return {
        OPERATOR_GO_ENV: "true",
        AUTH_HEAD_SHA_ENV: head,
        AUTH_DIGEST_ENV: HOLDOUT_PREREGISTRATION_DIGEST,
        AUTH_DATASET_ENV: DATASET_ID,
        AUTH_PANEL_ENV: PANEL_ID,
        AUTH_SUCCESSOR_ENV: HYPOTHESIS_ID,
    }


def test_package_and_runner_exist_and_import() -> None:
    assert holdout_pkg.HOLDOUT_EXECUTION_IMPLEMENTED is True
    assert holdout_pkg.PACKAGE_MARKER.endswith("=true")
    assert RUNNER_PATH.is_file()
    assert (EVAL_PKG / "__init__.py").is_file()
    assert (EVAL_PKG / "panel_runner_v1.py").is_file()
    assert (EVAL_PKG / "holdout_panel_bars_v1.py").is_file()
    assert (EVAL_PKG / "structural_preflight_v1.py").is_file()


def test_runner_script_importable_without_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    # Load as file module without invoking main.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "bollinger_holdout_v1_runner_under_test", RUNNER_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.delenv(OPERATOR_GO_ENV, raising=False)
    spec.loader.exec_module(mod)
    assert callable(mod.main)
    # Ensure tests never call main().


def test_no_import_time_holdout_io_in_panel_bars() -> None:
    src = (EVAL_PKG / "holdout_panel_bars_v1.py").read_text(encoding="utf-8")
    # Module body must not call resolve/load/verify at import time.
    tree_mod = importlib.import_module(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.holdout_panel_bars_v1"
    )
    # Sanity: functions exist but we do not call them.
    assert callable(tree_mod.resolve_holdout_archive_root)
    assert callable(tree_mod.load_member_bars)
    assert "pd.read_parquet" in src
    assert "if __name__" not in src or '__name__ == "__main__"' not in src


def test_contract_digest_and_frozen_parameters() -> None:
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_preregistration_digest"] == HOLDOUT_PREREGISTRATION_DIGEST
    frozen = contract["exit_mechanism"]["frozen_parameters"]
    for key, value in REQUIRED_FROZEN_PARAMETERS.items():
        assert frozen[key] == value
    assert contract["dataset_id"] == DATASET_ID
    assert contract["sealed_holdout_id"] == PANEL_ID
    assert contract["holdout_run_count"] == 1
    assert contract["status"] == "HOLDOUT_EVALUATION_EXECUTED_TERMINAL"
    assert contract["terminal_holdout_result_class"] == "FAIL"
    assert contract["holdout_executed"] is True


def test_canonical_lifecycle_vocabulary_excludes_invented_awaiting_label() -> None:
    life = _load(
        REPO / "config/research/canonical_research_lane_post_terminal_lifecycle_contract_v1.json"
    )
    states = set(life.get("canonical_lane_states") or [])
    assert REQUIRED_EXIT_LANE_STATUS in states
    assert REQUIRED_ENTRY_LANE_STATUS in states
    assert "AWAITING_HOLDOUT_EXECUTION_OPERATOR_GO" not in states
    exit_bl = _load(
        REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
    )
    entry_bl = _load(
        REPO / "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
    )
    assert exit_bl["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert exit_bl["explicit_closeout_decision"] is True
    assert entry_bl["status"] == REQUIRED_ENTRY_LANE_STATUS
    assert exit_bl["preregistered_hypotheses"] == []
    assert exit_bl["open_unpreregistered_candidates"] == []


def test_go_absent_blocks() -> None:
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V1_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={})


def test_authorization_requires_head_digest_dataset_panel_successor() -> None:
    head = "abc123"
    with pytest.raises(HoldoutPreregistrationError, match="AUTH_HEAD_SHA_REQUIRED"):
        assert_execution_authorization_bound(repo_head_sha=head, environ={OPERATOR_GO_ENV: "true"})
    env = _auth_env(head)
    env[AUTH_DIGEST_ENV] = "0" * 64
    with pytest.raises(HoldoutPreregistrationError, match="AUTH_CONTRACT_DIGEST_MISMATCH"):
        assert_execution_authorization_bound(repo_head_sha=head, environ=env)
    env = _auth_env(head)
    env[AUTH_HEAD_SHA_ENV] = "deadbeef"
    with pytest.raises(HoldoutPreregistrationError, match="AUTH_HEAD_SHA_MISMATCH"):
        assert_execution_authorization_bound(repo_head_sha=head, environ=env)
    env = _auth_env(head)
    env[AUTH_DATASET_ENV] = "wrong"
    with pytest.raises(HoldoutPreregistrationError, match="AUTH_DATASET_ID_MISMATCH"):
        assert_execution_authorization_bound(repo_head_sha=head, environ=env)
    env = _auth_env(head)
    env[AUTH_PANEL_ENV] = "wrong"
    with pytest.raises(HoldoutPreregistrationError, match="AUTH_PANEL_ID_MISMATCH"):
        assert_execution_authorization_bound(repo_head_sha=head, environ=env)
    env = _auth_env(head)
    env[AUTH_SUCCESSOR_ENV] = "WRONG"
    with pytest.raises(HoldoutPreregistrationError, match="AUTH_SUCCESSOR_ID_MISMATCH"):
        assert_execution_authorization_bound(repo_head_sha=head, environ=env)
    bound = assert_execution_authorization_bound(repo_head_sha=head, environ=_auth_env(head))
    assert bound.contract_digest == HOLDOUT_PREREGISTRATION_DIGEST
    assert bound.dataset_id == DATASET_ID
    assert bound.panel_id == PANEL_ID
    assert bound.successor_id == HYPOTHESIS_ID


def test_preflight_blocks_on_digest_dataset_panel_frozen_and_run_count(tmp_path: Path) -> None:
    from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistration_v1 import (
        definition_body_for_preregistration_digest,
    )

    live = _load(CONTRACT_PATH)
    # Reconstruct definition-only body so preflight gates remain testable after terminalization.
    contract = definition_body_for_preregistration_digest(live)
    contract["holdout_preregistration_digest"] = live["holdout_preregistration_digest"]
    view = copy.deepcopy(contract)
    preflight_holdout_execution_gates(view)

    bad = copy.deepcopy(contract)
    bad["holdout_preregistration_digest"] = "0" * 64
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_PREREGISTRATION_DIGEST_DRIFT"):
        preflight_holdout_execution_gates(bad)

    bad = copy.deepcopy(contract)
    bad["dataset_id"] = "wrong"
    with pytest.raises(HoldoutPreregistrationError, match="DATASET_ID_MISMATCH"):
        preflight_holdout_execution_gates(bad)

    bad = copy.deepcopy(contract)
    bad["sealed_holdout_id"] = "wrong"
    with pytest.raises(HoldoutPreregistrationError, match="PANEL_ID_MISMATCH"):
        preflight_holdout_execution_gates(bad)

    bad = copy.deepcopy(contract)
    bad["exit_mechanism"] = copy.deepcopy(contract["exit_mechanism"])
    bad["exit_mechanism"]["frozen_parameters"] = dict(bad["exit_mechanism"]["frozen_parameters"])
    bad["exit_mechanism"]["frozen_parameters"].pop("bb_period")
    with pytest.raises(HoldoutPreregistrationError, match="FROZEN_PARAM_MISMATCH"):
        preflight_holdout_execution_gates(bad)

    bad = copy.deepcopy(contract)
    bad["holdout_run_count"] = 1
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V1_RUN_ALREADY_CONSUMED"):
        assert_holdout_run_not_yet_consumed(bad)
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V1_RUN_ALREADY_CONSUMED"):
        preflight_holdout_execution_gates(bad)


def test_run_slot_and_runner_start_markers_block(tmp_path: Path) -> None:
    assert_run_slot_available(tmp_path)
    (tmp_path / ".holdout_run_consumed").write_text("x\n", encoding="utf-8")
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_SLOT_CONSUMED"):
        assert_run_slot_available(tmp_path)
    tmp2 = tmp_path / "b"
    tmp2.mkdir()
    (tmp2 / "run_slot_claim.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_SLOT_CLAIM"):
        assert_run_slot_available(tmp2)
    tmp3 = tmp_path / "c"
    tmp3.mkdir()
    (tmp3 / ".holdout_runner_started").write_text("1\n", encoding="utf-8")
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUNNER_START_COUNT"):
        assert_run_slot_available(tmp3)
    tmp4 = tmp_path / "d"
    tmp4.mkdir()
    (tmp4 / "summary.json").write_text(
        json.dumps({"holdout_run_count": 1, "runner_start_count": 0}) + "\n", encoding="utf-8"
    )
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_COUNT_ALREADY_POSITIVE"):
        assert_run_slot_available(tmp4)


def test_structural_preflight_fail_closed_without_auth(tmp_path: Path) -> None:
    with pytest.raises(HoldoutPreregistrationError):
        run_structural_preflight(
            repo_root=REPO,
            output_dir=tmp_path,
            environ={},
            require_authorization=True,
        )


def test_structural_preflight_blocks_after_terminal_consumed_slot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Live repo is terminalized; structural preflight must fail-closed (no second run)."""
    from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1 import (
        structural_preflight_v1 as sp,
    )

    monkeypatch.setattr(sp, "git_head_sha", lambda repo: "f" * 40)
    with pytest.raises(
        HoldoutPreregistrationError,
        match=(
            "HOLDOUT_V1_RUN_ALREADY_CONSUMED|HOLDOUT_PREREGISTRATION_DIGEST_RECOMPUTE_DRIFT|"
            "PREREGISTERED_SUCCESSOR_COUNT_MUST_BE_1|EXIT_LANE_STATUS_MISMATCH|"
            "SUCCESSOR_RUN_COUNT_NOT_ZERO|HOLDOUT_RUN_SLOT"
        ),
    ):
        run_structural_preflight(
            repo_root=REPO,
            output_dir=tmp_path,
            environ=_auth_env("f" * 40),
            require_authorization=True,
        )


def test_structural_preflight_blocks_wrong_lifecycle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1 import (
        structural_preflight_v1 as sp,
    )

    real_load = sp.load_json

    def _tamper(path: Path):
        payload = real_load(path)
        if path.name.startswith("canonical_open_mr_exit"):
            payload = copy.deepcopy(payload)
            payload["status"] = "LANE_CLOSED_NO_FURTHER_RESEARCH"
        return payload

    monkeypatch.setattr(sp, "load_json", _tamper)
    monkeypatch.setattr(sp, "git_head_sha", lambda repo: "f" * 40)
    with pytest.raises(HoldoutPreregistrationError):
        run_structural_preflight(
            repo_root=REPO,
            output_dir=tmp_path,
            environ=_auth_env("f" * 40),
            require_authorization=True,
        )


def test_structural_preflight_blocks_entry_not_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1 import (
        structural_preflight_v1 as sp,
    )

    real_load = sp.load_json

    def _tamper(path: Path):
        payload = real_load(path)
        if path.name.startswith("canonical_open_mr_entry"):
            payload = copy.deepcopy(payload)
            payload["status"] = "OPEN_BACKLOG"
        return payload

    monkeypatch.setattr(sp, "load_json", _tamper)
    monkeypatch.setattr(sp, "git_head_sha", lambda repo: "f" * 40)
    with pytest.raises(HoldoutPreregistrationError):
        run_structural_preflight(
            repo_root=REPO,
            output_dir=tmp_path,
            environ=_auth_env("f" * 40),
            require_authorization=True,
        )


def test_panel_runner_does_not_export_side_effect_on_import() -> None:
    import src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.panel_runner_v1 as pr

    assert callable(pr.run_holdout_evaluation)
    # Guard: tests must not invoke evaluation.
    assert (
        "run_holdout_evaluation("
        not in Path(__file__)
        .read_text(encoding="utf-8")
        .split("def test_panel_runner_does_not_export_side_effect_on_import")[1][:200]
    )


def test_v7_v8_terminals_unchanged_hashes() -> None:
    import hashlib

    assert V7_SUMMARY.is_file()
    assert V8_SUMMARY.is_file()
    assert V8_MANIFEST.is_file()
    # Stable expected digests from preflight baseline of this wiring branch tip.
    assert (
        hashlib.sha256(V7_SUMMARY.read_bytes()).hexdigest()
        == "e090f4d0b367091f06d89992765f1182c518922e3e75e9971c913ecb2009c7e6"
    )
    assert (
        hashlib.sha256(V8_SUMMARY.read_bytes()).hexdigest()
        == "8ac99a0b2fda02e34d28cf4ac6cdcd63c74d40b234d8f9ab82989ed845d3a874"
    )


def test_gates_remain_closed_on_live_ssot() -> None:
    exit_bl = _load(
        REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
    )
    contract = _load(CONTRACT_PATH)
    assert exit_bl["promotion_and_economic_gate_policy"]["economic_gate_open"] is False
    assert exit_bl["promotion_and_economic_gate_policy"]["promotion_eligible"] is False
    assert exit_bl["runtime_policy"]["runtime_activated"] is False
    assert exit_bl["runtime_policy"]["orders_allowed"] is False
    assert contract["promotion_and_economic_gate_policy"]["economic_gate_open"] is False
    assert contract["runtime_policy"]["orders_allowed"] is False


def test_evaluate_evidence_dir_present_and_run_count_one() -> None:
    evaluate = REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1"
    assert evaluate.is_dir()
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_run_count"] == 1
    assert contract["holdout_executed"] is True
    assert contract["terminal_holdout_result_class"] == "FAIL"
    summary = _load(evaluate / "summary.json")
    assert summary["result_class"] == "FAIL"
    assert summary["holdout_run_count"] == 1
    assert summary["runner_start_count"] == 1
    assert summary["economic_gate_open"] is False
    assert summary["promotion_eligible"] is False
    assert summary["runtime_activated"] is False
    assert summary["orders_sent"] is False
    assert (evaluate / ".holdout_run_consumed").is_file()
    assert (evaluate / ".holdout_runner_started").read_text(encoding="utf-8").strip() == "1"


def test_lane_close_does_not_reenable_holdout_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Closed Exit lane still fail-closes holdout structural preflight (no re-run)."""
    from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1 import (
        structural_preflight_v1 as sp,
    )

    exit_bl = _load(
        REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
    )
    assert exit_bl["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert exit_bl["explicit_closeout_decision"] is True
    assert exit_bl["preregistered_hypotheses"] == []
    monkeypatch.setattr(sp, "git_head_sha", lambda repo: "f" * 40)
    with pytest.raises(
        HoldoutPreregistrationError,
        match=(
            "EXIT_LANE_STATUS_MISMATCH|PREREGISTERED_SUCCESSOR_COUNT_MUST_BE_1|"
            "HOLDOUT_V1_RUN_ALREADY_CONSUMED|HOLDOUT_RUN_SLOT|SUCCESSOR_RUN_COUNT"
        ),
    ):
        run_structural_preflight(
            repo_root=REPO,
            output_dir=tmp_path,
            environ=_auth_env("f" * 40),
            require_authorization=True,
        )


def test_holdout_terminal_evidence_invariants_unchanged_by_lane_closeout() -> None:
    summary = _load(
        REPO
        / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/summary.json"
    )
    assert summary["result_class"] == "FAIL"
    assert summary["decision"]["reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert int(summary["holdout_run_count"]) == 1
    assert int(summary["runner_start_count"]) == 1
    assert summary["no_retry"] is True
    assert abs(float(summary["baseline_metrics"]["net_profit_factor"]) - 0.5774036019332512) < 1e-12
    assert (
        abs(float(summary["treatment_metrics"]["net_profit_factor"]) - 0.5280135615083571) < 1e-12
    )
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_run_count"] == 1
    assert contract["status"] == "HOLDOUT_EVALUATION_EXECUTED_TERMINAL"
    assert contract["terminal_holdout_result_class"] == "FAIL"
