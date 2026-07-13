"""Contract tests for lead-lag v0 evaluation-path parity flag ratification v1."""

from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
    load_evaluation_path_parity_status_v0,
    load_ops_evaluation_config_v0,
    materialize_preexecution_fail_closed_block_v0,
)
from src.research.cross_sectional_lead_lag_v0_evaluation_path_parity_flag_ratification_v0 import (
    CANONICAL_OWNER,
    OPERATOR_GO,
    STALE_FALSE_FIELD_PATHS,
    RatificationValidationVerdict,
    build_before_after_field_diff_v0,
    collect_unexpected_change_count,
    compare_materialized_configs_v0,
    materialize_evaluation_path_parity_flag_ratification_v0,
    materializer_to_validator_roundtrip_v0,
    validate_evaluation_path_parity_flag_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SOURCE_EVIDENCE = (
    ARCHIVE_ROOT
    / "planning/cross_sectional_lead_lag_v0_full_canonical_chain_and_runtime_decision_parity_"
    "post_position_feedback_gap_assessment_read_only_v0_20260713T020952Z"
)
CONFIG_PATH = REPO_ROOT / CANONICAL_OWNER


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


def test_operator_go_constant() -> None:
    assert OPERATOR_GO == (
        "GO_CROSS_SECTIONAL_LEAD_LAG_V0_EVALUATION_PATH_PARITY_FLAG_RATIFICATION_V1"
    )


def test_ratified_true_field_paths_in_ops_config() -> None:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parity = cfg["evaluation_path_parity_binding_v0"]
    assert parity["full_canonical_chain_wired"] is True
    assert parity["backtest_runtime_decision_parity_pass"] is True
    assert parity["evaluation_path_parity_ratified"] is True


def test_materialize_ratification_from_verified_source_evidence() -> None:
    if not SOURCE_EVIDENCE.is_dir():
        pytest.skip("source evidence bundle unavailable")
    ratified = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=REPO_ROOT,
        source_evidence_dir=SOURCE_EVIDENCE,
        archive_root=ARCHIVE_ROOT,
        ratification_evidence_ref="research/test_ratification_ref",
    )
    parity = ratified["evaluation_path_parity_binding_v0"]
    assert parity["full_canonical_chain_wired"] is True
    assert parity["backtest_runtime_decision_parity_pass"] is True
    assert parity["evaluation_path_parity_ratified"] is True
    assert parity["ratified_read_only"] is True


def test_validator_roundtrip_passes_for_materialized_config() -> None:
    if not SOURCE_EVIDENCE.is_dir():
        pytest.skip("source evidence bundle unavailable")
    ratified = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=REPO_ROOT,
        source_evidence_dir=SOURCE_EVIDENCE,
        archive_root=ARCHIVE_ROOT,
        ratification_evidence_ref="research/test_ratification_ref",
    )
    source_ref = str(SOURCE_EVIDENCE.relative_to(ARCHIVE_ROOT))
    roundtrip = materializer_to_validator_roundtrip_v0(ratified, expected_source_ref=source_ref)
    assert roundtrip["materializer_to_validator_roundtrip_pass"] is True


def test_deterministic_double_materialization() -> None:
    if not SOURCE_EVIDENCE.is_dir():
        pytest.skip("source evidence bundle unavailable")
    first = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=REPO_ROOT,
        source_evidence_dir=SOURCE_EVIDENCE,
        archive_root=ARCHIVE_ROOT,
        ratification_evidence_ref="research/test_ratification_ref",
    )
    second = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=REPO_ROOT,
        source_evidence_dir=SOURCE_EVIDENCE,
        archive_root=ARCHIVE_ROOT,
        ratification_evidence_ref="research/test_ratification_ref",
    )
    assert compare_materialized_configs_v0(first, second) is True


def test_only_expected_fields_change() -> None:
    if not SOURCE_EVIDENCE.is_dir():
        pytest.skip("source evidence bundle unavailable")
    before = load_ops_evaluation_config_v0(REPO_ROOT)
    after = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=REPO_ROOT,
        source_evidence_dir=SOURCE_EVIDENCE,
        archive_root=ARCHIVE_ROOT,
        ratification_evidence_ref="research/test_ratification_ref",
    )
    diff_rows = build_before_after_field_diff_v0(before=before, after=after)
    assert collect_unexpected_change_count(diff_rows) == 0
    assert before["binding_digest"] == after["binding_digest"]
    assert before["config_digest"] == after["config_digest"]
    assert before["strategy_id"] == after["strategy_id"]


def test_stale_false_config_blocks_preexecution_guard() -> None:
    block = materialize_preexecution_fail_closed_block_v0(
        block_reason=BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
    )
    assert block["PREEXECUTION_PARITY_GUARD_PASS"] is False


def test_ratified_config_validator_accepts_materialized_output() -> None:
    if not SOURCE_EVIDENCE.is_dir():
        pytest.skip("source evidence bundle unavailable")
    ratified = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=REPO_ROOT,
        source_evidence_dir=SOURCE_EVIDENCE,
        archive_root=ARCHIVE_ROOT,
        ratification_evidence_ref="research/test_ratification_ref",
    )
    validation = validate_evaluation_path_parity_flag_ratification_v0(ratified)
    assert validation.verdict is RatificationValidationVerdict.ACCEPTED


def test_config_file_ratified_flags_loaded_by_parity_status_loader() -> None:
    full_chain, parity_pass = load_evaluation_path_parity_status_v0(REPO_ROOT)
    cfg = load_ops_evaluation_config_v0(REPO_ROOT)
    expected_full = cfg["evaluation_path_parity_binding_v0"]["full_canonical_chain_wired"]
    expected_parity = cfg["evaluation_path_parity_binding_v0"][
        "backtest_runtime_decision_parity_pass"
    ]
    assert full_chain is expected_full
    assert parity_pass is expected_parity
