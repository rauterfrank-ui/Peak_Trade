"""Contract/unit tests for VDB v1 development-evaluation entry point."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.volatility_decay_breakout_v1_development_evaluation_v1.authorization_v1 import (
    resolve_authorization_decision_v1,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.binding_v1 import (
    EntryPointBindingError,
    assert_dataset_allowed,
    assert_shared_channel_core_bound,
    compute_config_digest,
    compute_strategy_params_digest,
    load_and_validate_entry_point_binding,
    reject_holdout_reference,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    CLI_REL_PATH,
    DATASET_ID,
    ENTRY_POINT_BINDING_REL_PATH,
    EVIDENCE_REL_PATH,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    GOVERNANCE_REL_PATH,
    HOLDOUT_OPAQUE_ID,
    HYPOTHESIS_ID,
    OWNER_SURFACE,
    PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
    PROGRAM_ID,
    STRATEGY_IDENTITY,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.entry_point_v1 import (
    run_evaluate_fail_closed,
    run_preflight_only,
    validate_repo_entry_point,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_exactly_one_run_limit,
    assert_holdout_guard,
    assert_retry_forbidden,
    preflight_guards,
    read_run_counters,
)

REPO = Path(__file__).resolve().parents[2]
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
CONTRACT = REPO / (
    "config/research/"
    "volatility_decay_breakout_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
PROGRAM = REPO / "config/research/volatility_regime_research_program_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_owner_registry_and_entry_point_files_bound() -> None:
    owner_map = _load(OWNER_MAP)
    owner = owner_map["allowed_optimization_surfaces"][OWNER_SURFACE]
    prefixes = owner["path_prefixes"]
    assert ENTRY_POINT_BINDING_REL_PATH in prefixes
    assert CLI_REL_PATH in prefixes
    assert (
        "tests/research/test_volatility_decay_breakout_v1_development_evaluation_entry_point_v1.py"
        in prefixes
    )
    assert (REPO / CLI_REL_PATH).is_file()
    assert (REPO / ENTRY_POINT_BINDING_REL_PATH).is_file()
    assert (REPO / GOVERNANCE_REL_PATH).is_file()
    assert (REPO / EVIDENCE_REL_PATH / "README.md").is_file()
    assert "src/research/volatility_decay_breakout_v1_development_evaluation_v1/" in prefixes


def test_import_safe_no_dataset_no_runner() -> None:
    before = read_run_counters(REPO)
    mod = importlib.import_module(
        "src.research.volatility_decay_breakout_v1_development_evaluation_v1"
    )
    assert mod.PACKAGE_MARKER.endswith("=true")
    importlib.reload(mod)
    after = read_run_counters(REPO)
    assert after == before
    assert before["contract_development_run_count"] == 1
    assert before["contract_runner_start_count"] == 1


def test_static_ids_and_bindings() -> None:
    assert STRATEGY_IDENTITY == "VOLATILITY_DECAY_BREAKOUT_V1"
    assert BASELINE_ID == "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
    assert PROGRAM_ID == "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
    assert DATASET_ID == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    assert TIME_SEGMENT_DEFINITION_ID == "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["development_evaluation_authorized"] is True
    assert binding["evaluation_authorized"] is False
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1
    assert binding["development_run_limit"] == 1
    assert binding["frozen_measurement_contract_digest"] == FROZEN_MEASUREMENT_CONTRACT_DIGEST
    assert binding["shared_channel_core_bound"] is True
    assert binding["productive_exit_pnl_evaluator_ref"] == PRODUCTIVE_PNL_EVALUATOR_REL_PATH
    assert binding["productive_pnl_evaluator_duplicated"] is False
    assert (REPO / PRODUCTIVE_PNL_EVALUATOR_REL_PATH).is_file()
    assert binding["config_digest"] == compute_config_digest(REPO)
    assert len(binding["config_digest"]) == 64
    contract = _load(CONTRACT)
    assert binding["strategy_params_digest"] == compute_strategy_params_digest(contract)
    assert binding["time_segment_definition_id"] == TIME_SEGMENT_DEFINITION_ID


def test_shared_channel_core_identical() -> None:
    assert_shared_channel_core_bound()


def test_dataset_allowlist_and_holdout_rejection() -> None:
    assert_dataset_allowed(DATASET_ID)
    assert_holdout_guard(dataset_id=DATASET_ID)
    with pytest.raises(EntryPointBindingError):
        assert_dataset_allowed(HOLDOUT_OPAQUE_ID)
    with pytest.raises(EntryPointBindingError):
        reject_holdout_reference(HOLDOUT_OPAQUE_ID)
    with pytest.raises(GuardError):
        assert_holdout_guard(dataset_id=DATASET_ID, attempted_holdout_ids=(HOLDOUT_OPAQUE_ID,))


def test_exactly_one_run_and_retry_guards() -> None:
    assert_exactly_one_run_limit(1)
    with pytest.raises(GuardError):
        assert_exactly_one_run_limit(2)
    assert_retry_forbidden(retry_requested=False, development_run_count=0, runner_start_count=0)
    with pytest.raises(GuardError):
        assert_retry_forbidden(retry_requested=True, development_run_count=0, runner_start_count=0)


def test_preflight_authorized_no_evaluate_execution_or_run_consumption() -> None:
    before = read_run_counters(REPO)
    report = run_preflight_only(REPO)
    assert report["status"] == "PREFLIGHT_PASS_EVALUATION_UNAUTHORIZED"
    assert report["runner_started"] is False
    assert report["evaluation_executed"] is False
    assert report["development_dataset_loaded"] is False
    assert report["holdout_accessed"] is False
    assert report["development_evaluation_authorized"] is True
    assert report["entry_point_binding"]["development_evaluation_authorized"] is True
    # Authorization-only slice: do not invoke --mode evaluate / runner.
    validated = validate_repo_entry_point(REPO)
    assert validated["valid"] is True
    assert validated["development_evaluation_authorized"] is True
    after = read_run_counters(REPO)
    assert after == before


def test_repo_authorization_authorized_on_head() -> None:
    decision = resolve_authorization_decision_v1(REPO, authorize_token=HYPOTHESIS_ID)
    assert decision.authorized is True
    assert decision.authorize_token_valid is True
    assert decision.repo_development_evaluation_authorized is True
    assert decision.program_development_evaluation_authorized is True
    assert decision.entry_point_binding_authorized is True
    assert decision.reason_codes == ()


def test_unauthorized_token_blocks_evaluate_no_run_consumption() -> None:
    before = read_run_counters(REPO)
    decision = resolve_authorization_decision_v1(REPO, authorize_token="WRONG_TOKEN")
    assert decision.authorized is False
    assert "AUTHORIZE_TOKEN_MISMATCH" in decision.reason_codes
    with pytest.raises(GuardError) as exc:
        run_evaluate_fail_closed(
            REPO,
            authorize_token="WRONG_TOKEN",
            output_dir=REPO / EVIDENCE_REL_PATH,
        )
    assert "EVALUATION_UNAUTHORIZED" in str(exc.value)
    after = read_run_counters(REPO)
    assert after == before
    # Terminal evidence from the consumed authorized run remains present; wrong-token
    # evaluate must not mutate or replace it.
    assert (REPO / EVIDENCE_REL_PATH / "summary.json").is_file()
    assert (REPO / EVIDENCE_REL_PATH / "run_slot_claim.json").is_file()
    claim = json.loads(
        (REPO / EVIDENCE_REL_PATH / "run_slot_claim.json").read_text(encoding="utf-8")
    )
    assert claim["evaluation_run_count"] == 1
    assert claim["runner_start_count"] == 1


def test_cli_evaluate_fail_closed_wrong_token_subprocess() -> None:
    before = read_run_counters(REPO)
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / CLI_REL_PATH),
            "--mode",
            "evaluate",
            "--authorize-single-development-evaluation",
            "WRONG_TOKEN",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["status"] == "FAIL_CLOSED"
    assert payload["runner_started"] is False
    assert payload["evaluation_executed"] is False
    assert payload["development_dataset_loaded"] is False
    after = read_run_counters(REPO)
    assert after == before


def test_measurement_contract_authorized_and_guards() -> None:
    contract = _load(CONTRACT)
    program = _load(PROGRAM)
    assert contract["contract_digest"] == FROZEN_MEASUREMENT_CONTRACT_DIGEST
    assert contract["development_evaluation_authorized"] is True
    assert program["development_evaluation_authorized"] is True
    assert contract["development_evaluation_executed"] is True
    assert contract["development_run_count"] == 1
    assert contract["runner_start_count"] == 1
    assert program["development_run_count"] == 1
    assert program["runner_start_count"] == 1
    guards = preflight_guards(REPO)
    assert guards["development_evaluation_authorized"] is True
    assert guards["entry_point_binding_authorized"] is True
    assert guards["evaluation_authorized"] is False
    assert guards["run_slot_exhausted"] is True
