"""Contract tests for V7 Operator Clarification Authority (no evaluation / no panel)."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v7 import (
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    load_and_validate_repo_contract,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7 import (
    ALLOWED_TRANSITIONS,
    AUTHORITY_ID,
    AUTHORITY_REL_PATH,
    OPERATOR_DECISIONS_STATUS,
    READY_STATUS,
    REQUIRED_PREREGISTRATION_DIGEST,
    OperatorClarificationAuthorityError,
    assert_transition_allowed,
    compute_authority_digest,
    load_and_validate_authority,
    load_authority,
    validate_authority,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.panel_runner_v7 import (
    assert_v7_authority_and_prereg_gates,
    run_development_evaluation,
)

REPO = Path(__file__).resolve().parents[2]
AUTHORITY_PATH = REPO / AUTHORITY_REL_PATH
PREREG_PATH = (
    REPO
    / "config/research/"
    / "bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json"
)
CLI = (
    REPO
    / "scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7.py"
)
EXPECTED_AUTHORITY_DIGEST = "fbf9e8cf7715484e68755a5bd2149bd0d63c94705be8e982611fcf7cc4ace62f"


def test_valid_authority_and_digests() -> None:
    report = load_and_validate_authority(
        REPO, require_registered=True, require_ready_status=True, require_authorized_status=True
    )
    assert report["authority_id"] == AUTHORITY_ID
    assert report["authority_digest"] == EXPECTED_AUTHORITY_DIGEST
    assert report["preregistration_digest"] == REQUIRED_PREREGISTRATION_DIGEST
    assert report["status"] == "EVALUATION_AUTHORIZED"
    assert report["operator_decisions_status"] == OPERATOR_DECISIONS_STATUS
    assert report["evaluation_authorized"] is False
    assert report["evaluation_run_count"] == 1
    assert report["run_slot_consumed"] is True
    auth = report["authority"]
    for key in ("B1", "B2", "B3", "B4", "B5", "B6"):
        assert auth["decisions"][key]["resolved"] is True


def test_preregistration_byte_identical() -> None:
    raw = PREREG_PATH.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    body = {k: v for k, v in obj.items() if k != "development_preregistration_digest"}
    computed = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    assert computed == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    assert obj["development_preregistration_digest"] == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    assert obj["evaluation_authorized"] is False
    assert int(obj["evaluation_run_count"]) == 0
    report = load_and_validate_repo_contract(REPO)
    assert report["evaluation_run_count"] == 0


def test_missing_authority_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7.AUTHORITY_REL_PATH",
        "config/research/__missing_operator_clarification_authority_v7.json",
    )
    with pytest.raises(OperatorClarificationAuthorityError, match="MISSING_AUTHORITY"):
        load_authority(REPO)


def test_manipulated_authority_digest_fail_closed() -> None:
    auth = load_authority(REPO)
    mutated = copy.deepcopy(auth)
    mutated["authority_digest"] = "0" * 64
    with pytest.raises(OperatorClarificationAuthorityError, match="AUTHORITY_DIGEST_MISMATCH"):
        validate_authority(mutated, repo_root=REPO, require_registered=False)


def test_wrong_prereg_digest_fail_closed() -> None:
    auth = load_authority(REPO)
    mutated = copy.deepcopy(auth)
    mutated["preregistration_digest"] = "1" * 64
    mutated["authority_digest"] = compute_authority_digest(mutated)
    with pytest.raises(
        OperatorClarificationAuthorityError, match="PREREGISTRATION_DIGEST_MISMATCH"
    ):
        validate_authority(mutated, repo_root=REPO, require_registered=False)


def test_unresolved_b1_fail_closed() -> None:
    auth = load_authority(REPO)
    mutated = copy.deepcopy(auth)
    mutated["decisions"]["B1"]["resolved"] = False
    mutated["b1_through_b6_fully_resolved"] = False
    mutated["authority_digest"] = compute_authority_digest(mutated)
    with pytest.raises(OperatorClarificationAuthorityError, match="UNRESOLVED_B1"):
        validate_authority(mutated, repo_root=REPO, require_registered=False)


def test_unregistered_authority_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = load_authority(REPO)

    def _boom(repo, authority):  # noqa: ANN001
        raise OperatorClarificationAuthorityError("AUTHORITY_NOT_REGISTERED")

    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7._assert_registered",
        _boom,
    )
    with pytest.raises(OperatorClarificationAuthorityError, match="AUTHORITY_NOT_REGISTERED"):
        validate_authority(auth, repo_root=REPO, require_registered=True)


def test_forbidden_lifecycle_transition() -> None:
    with pytest.raises(OperatorClarificationAuthorityError, match="FORBIDDEN_LIFECYCLE_TRANSITION"):
        assert_transition_allowed(
            from_state="DEFINITION_ONLY_PREREGISTERED",
            to_state="READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION",
        )
    assert (
        "DEFINITION_ONLY_PREREGISTERED",
        "OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY",
    ) in ALLOWED_TRANSITIONS
    assert (
        "READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION",
        "EVALUATION_AUTHORIZED",
    ) in ALLOWED_TRANSITIONS


def test_runner_without_cli_hypothesis_auth_no_data_no_slot(tmp_path: Path) -> None:
    """Even when lifecycle is authorized, missing hypothesis CLI auth must not start."""
    out = tmp_path / "evaluate_must_not_claim"
    with pytest.raises(RuntimeError, match="V7_EVALUATION_NOT_AUTHORIZED"):
        run_development_evaluation(
            output_dir=out,
            authorize_hypothesis_id="WRONG_HYPOTHESIS",
            allow_panel_run=True,
            repo_root=REPO,
        )
    assert not out.exists() or not any(out.iterdir())
    assert not (out / "run_slot_claim.json").exists()
    assert not (out / "summary.json").exists()


def test_gate_failures_before_slot_and_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7 import (
        panel_runner_v7 as runner,
    )

    out = tmp_path / "blocked_preflight_out"

    def _boom(**kwargs):  # noqa: ANN003
        raise RuntimeError("OPERATOR_CLARIFICATION_AUTHORITY_GATE:MISSING_AUTHORITY")

    monkeypatch.setattr(runner, "assert_v7_authority_and_prereg_gates", _boom)
    with pytest.raises(RuntimeError, match="MISSING_AUTHORITY"):
        runner.run_preflight_only(output_dir=out, repo_root=REPO)
    assert not out.exists()

    with pytest.raises(RuntimeError, match="MISSING_AUTHORITY"):
        runner.run_development_evaluation(
            output_dir=out,
            authorize_hypothesis_id=(
                "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
            ),
            allow_panel_run=True,
            repo_root=REPO,
        )
    assert not out.exists()
    assert not (out / "run_slot_claim.json").exists()
    assert not (out / "summary.json").exists()
    assert not (out / "comparison_decision.json").exists()


def test_runner_source_order_gates_before_claim_before_panel() -> None:
    text = (
        REPO
        / "src/research/bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7"
        / "panel_runner_v7.py"
    ).read_text(encoding="utf-8")
    # Scope to evaluate body so helper *definitions* earlier in the module
    # cannot invert the call-order proof.
    evaluate_fn = text.split("def run_development_evaluation(")[1].split(
        "\ndef ",
        1,
    )[0]
    gate_pos = evaluate_fn.find("assert_v7_authority_and_prereg_gates(")
    claim_pos = evaluate_fn.find("_claim_run_slot_atomic_v7(")
    archive_pos = evaluate_fn.find("resolve_development_archive_root(")
    panel_pos = evaluate_fn.find("verify_development_panel_hashes(")
    assert 0 <= gate_pos < claim_pos < archive_pos
    assert claim_pos < panel_pos
    # Preflight-only: gates before mkdir / artifact write
    preflight_fn = text.split("def run_preflight_only(")[1].split(
        "def run_development_evaluation("
    )[0]
    assert preflight_fn.find("assert_v7_authority_and_prereg_gates(") < preflight_fn.find(
        "output_dir.mkdir("
    )
    assert preflight_fn.find("assert_v7_authority_and_prereg_gates(") < preflight_fn.find(
        "preflight_only_summary.json"
    )


def test_assert_gates_effective_authorization_false_after_slot_consumed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After the single authorized start, effective auth is closed; prereg field remains false."""
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v7.is_panel_released",
        lambda archive_root=None: True,
    )
    with pytest.raises(RuntimeError, match="V7_EVALUATION_NOT_AUTHORIZED"):
        assert_v7_authority_and_prereg_gates(
            repo=REPO,
            require_evaluation_authorized=True,
            require_ready_status=True,
        )
    contract = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    assert contract["evaluation_authorized"] is False
    assert int(contract["evaluation_run_count"]) == 0


def test_cli_evaluate_fail_closed_without_hypothesis_flag(tmp_path: Path) -> None:
    env = {
        **{
            k: v for k, v in __import__("os").environ.items() if k != "PEAK_TRADE_DATA_ARCHIVE_ROOT"
        },
        "PYTHONPATH": f"{REPO}/src:{REPO}",
    }
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--mode",
            "evaluate",
            "--output-dir",
            str(tmp_path / "cli_eval_out"),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
    )
    assert proc.returncode != 0
    assert not (tmp_path / "cli_eval_out" / "run_slot_claim.json").exists()
    assert "V7_EVALUATION_NOT_AUTHORIZED" in proc.stdout or "NOT_AUTHORIZED" in proc.stdout


def test_authority_registered_in_owner_and_wiring() -> None:
    owner = json.loads(
        (
            REPO
            / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert AUTHORITY_ID in owner["allowed_optimization_surfaces"]
    wiring = json.loads(
        (REPO / "config/governance/technical_canonical_wiring_authorization_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert AUTHORITY_REL_PATH in wiring["allowed_paths"]
    assert (
        "TECHNICAL_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7_WIRING"
        in wiring["allowed_surface_classes"]
    )
    assert AUTHORITY_PATH.is_file()
