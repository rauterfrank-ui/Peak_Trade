"""Contract tests for versioned_final_fleet_bindings_offline_economic_evaluation_v0."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    AUTHORITY_EFFECT,
    DATASET_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    ValidationVerdict,
    compute_completion_digest_v0,
    load_scope_config_v0,
    materialize_binding_completion_v0,
    materialize_narrow_evaluation_dataset_v0,
    resolve_staging_root,
    validate_binding_completion_v0,
    verify_preconditions_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
STAGING_ROOT = (
    ARCHIVE_ROOT / "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)


@pytest.fixture(name="scope_config")
def fixture_scope_config() -> dict:
    return load_scope_config_v0(REPO_ROOT)


@pytest.fixture(name="narrow_dataset")
def fixture_narrow_dataset(tmp_path: Path) -> object:
    if not STAGING_ROOT.is_dir():
        pytest.skip("extended_chronological_v1 staging unavailable")
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        _load_period_policy,
    )

    return materialize_narrow_evaluation_dataset_v0(
        staging_root=STAGING_ROOT,
        output_root=tmp_path / "narrow",
        period_policy=_load_period_policy(REPO_ROOT),
    )


def test_go_token_and_scope_classification() -> None:
    assert GO_TOKEN == (
        "GO_BOUNDED_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_V0"
    )
    assert (
        SCOPE_CLASSIFICATION
        == "BOUNDED_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_V0"
    )
    assert EXPECTED_ORIGIN_MAIN_SHA == "d7e03de515a7349b01cc4058379fcbb65c4548d8"


def test_no_runtime_authority_order_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_scope_config_loads(scope_config: dict) -> None:
    assert scope_config["dataset_id"] == DATASET_ID
    assert scope_config["go_token"] == GO_TOKEN
    assert scope_config["network_fetch_run"] is False


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="staging unavailable")
def test_verify_preconditions_passes_with_live_staging() -> None:
    ok, reasons, panel_binding, coverage = verify_preconditions_v0(
        repo_root=REPO_ROOT,
        confirm=GO_TOKEN,
        staging_root=STAGING_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is True, reasons
    assert panel_binding is not None
    assert panel_binding.panel_member_count == 118
    assert coverage.coverage_ratio == 1.0


def test_verify_preconditions_rejects_invalid_go_token() -> None:
    ok, reasons, _, _ = verify_preconditions_v0(
        repo_root=REPO_ROOT,
        confirm="INVALID",
        staging_root=STAGING_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert any("GO_TOKEN_INVALID" in reason for reason in reasons)


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="staging unavailable")
def test_materialize_narrow_dataset_produces_parquet_and_manifest(
    narrow_dataset: object,
) -> None:
    assert narrow_dataset.bars_path.is_file()
    assert narrow_dataset.manifest_path.is_file()
    assert narrow_dataset.row_count > 0
    assert len(narrow_dataset.dataset_digest) == 64


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="staging unavailable")
def test_materialize_binding_completion_has_three_candidates(
    narrow_dataset: object,
    tmp_path: Path,
) -> None:
    from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
        compute_funding_coverage_report_v0,
        load_panel_member_binding_v0,
    )
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        build_runtime_step31f_config_v0,
    )

    panel_binding = load_panel_member_binding_v0(STAGING_ROOT)
    coverage = compute_funding_coverage_report_v0(STAGING_ROOT)
    runtime_paths = {}
    for strategy_id, _ in FLEET_CANDIDATES:
        runtime_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=tmp_path / f"{strategy_id}.json",
        )
    completion = materialize_binding_completion_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_paths,
    )
    assert len(completion["candidates"]) == len(FLEET_CANDIDATES)
    assert completion["dataset_id"] == DATASET_ID


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="staging unavailable")
def test_validate_binding_completion_accepted(
    narrow_dataset: object,
    tmp_path: Path,
) -> None:
    from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
        compute_funding_coverage_report_v0,
        load_panel_member_binding_v0,
    )
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        build_runtime_step31f_config_v0,
    )

    panel_binding = load_panel_member_binding_v0(STAGING_ROOT)
    coverage = compute_funding_coverage_report_v0(STAGING_ROOT)
    runtime_paths = {}
    for strategy_id, _ in FLEET_CANDIDATES:
        runtime_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=tmp_path / f"{strategy_id}.json",
        )
    completion = materialize_binding_completion_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_paths,
    )
    result = validate_binding_completion_v0(completion, repo_root=REPO_ROOT)
    assert result.verdict is ValidationVerdict.ACCEPTED
    assert result.valid is True


def test_candidate_bindings_include_required_fields(
    narrow_dataset: object,
    tmp_path: Path,
) -> None:
    if not STAGING_ROOT.is_dir():
        pytest.skip("staging unavailable")
    from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
        compute_funding_coverage_report_v0,
        load_panel_member_binding_v0,
    )
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        build_runtime_step31f_config_v0,
    )

    panel_binding = load_panel_member_binding_v0(STAGING_ROOT)
    coverage = compute_funding_coverage_report_v0(STAGING_ROOT)
    runtime_paths = {}
    for strategy_id, _ in FLEET_CANDIDATES:
        runtime_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=tmp_path / f"{strategy_id}.json",
        )
    completion = materialize_binding_completion_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_paths,
    )
    required = {
        "strategy_id",
        "strategy_version",
        "parameter_binding",
        "dataset_binding",
        "period_binding",
        "instrument_binding",
        "fee_model_binding",
        "slippage_model_binding",
        "funding_model_binding",
        "execution_model_binding",
        "economic_policy_binding",
        "implementation_digest",
        "config_digest",
        "data_digest",
        "binding_semantic_digest",
    }
    for candidate in completion["candidates"]:
        assert required.issubset(candidate.keys())
        assert candidate["fee_model_binding"]["fee_bps"] > 0
        assert candidate["slippage_model_binding"]["slippage_bps"] > 0
        assert candidate["funding_model_binding"]["bind"] is True


def test_common_economic_policy_across_candidates(
    narrow_dataset: object,
    tmp_path: Path,
) -> None:
    if not STAGING_ROOT.is_dir():
        pytest.skip("staging unavailable")
    from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
        compute_funding_coverage_report_v0,
        load_panel_member_binding_v0,
    )
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        build_runtime_step31f_config_v0,
    )

    panel_binding = load_panel_member_binding_v0(STAGING_ROOT)
    coverage = compute_funding_coverage_report_v0(STAGING_ROOT)
    runtime_paths = {}
    for strategy_id, _ in FLEET_CANDIDATES:
        runtime_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=tmp_path / f"{strategy_id}.json",
        )
    completion = materialize_binding_completion_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_paths,
    )
    policies = [c["economic_policy_binding"] for c in completion["candidates"]]
    assert len(set(map(str, policies))) == 1


def test_digest_drift_fail_closed(
    narrow_dataset: object,
    tmp_path: Path,
) -> None:
    if not STAGING_ROOT.is_dir():
        pytest.skip("staging unavailable")
    from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
        compute_funding_coverage_report_v0,
        load_panel_member_binding_v0,
    )
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        build_runtime_step31f_config_v0,
    )

    panel_binding = load_panel_member_binding_v0(STAGING_ROOT)
    coverage = compute_funding_coverage_report_v0(STAGING_ROOT)
    runtime_paths = {}
    for strategy_id, _ in FLEET_CANDIDATES:
        runtime_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=tmp_path / f"{strategy_id}.json",
        )
    completion = materialize_binding_completion_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_paths,
    )
    broken = copy.deepcopy(completion)
    broken["candidates"][0]["binding_semantic_digest"] = "0" * 64
    result = validate_binding_completion_v0(broken, repo_root=REPO_ROOT)
    assert result.verdict is ValidationVerdict.REJECTED


def test_completion_digest_stable(
    narrow_dataset: object,
    tmp_path: Path,
) -> None:
    if not STAGING_ROOT.is_dir():
        pytest.skip("staging unavailable")
    from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
        compute_funding_coverage_report_v0,
        load_panel_member_binding_v0,
    )
    from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
        build_runtime_step31f_config_v0,
    )

    panel_binding = load_panel_member_binding_v0(STAGING_ROOT)
    coverage = compute_funding_coverage_report_v0(STAGING_ROOT)
    runtime_paths = {}
    for strategy_id, _ in FLEET_CANDIDATES:
        runtime_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=tmp_path / f"{strategy_id}.json",
        )
    completion = materialize_binding_completion_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_paths,
    )
    assert completion["completion_digest"] == compute_completion_digest_v0(completion)


def test_resolve_staging_root(scope_config: dict) -> None:
    root = resolve_staging_root(
        durable_archive_root=ARCHIVE_ROOT,
        scope_config=scope_config,
    )
    assert "extended_chronological_v1" in str(root)
