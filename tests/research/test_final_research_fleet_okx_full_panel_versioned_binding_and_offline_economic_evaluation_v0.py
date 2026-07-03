"""Contract tests for final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.research.final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0 import (
    AUTHORITY_EFFECT,
    DATASET_CONTENT_DIGEST,
    DATASET_ID,
    DATASET_VERSION,
    GO_TOKEN,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    IdempotentBindingStatus,
    ValidationVerdict,
    compute_completion_digest_v0,
    detect_idempotent_binding_status_v0,
    materialize_binding_completion_v0,
    validate_binding_completion_v0,
    verify_preconditions_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")


@pytest.fixture(name="binding_completion")
def fixture_binding_completion() -> dict:
    return materialize_binding_completion_v0(
        repo_root=REPO_ROOT,
        durable_archive_root=ARCHIVE_ROOT,
    )


def test_go_token_and_scope_classification() -> None:
    assert GO_TOKEN == (
        "GO_BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
    )
    assert (
        SCOPE_CLASSIFICATION
        == "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
    )


def test_no_runtime_authority_order_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_materialize_binding_completion_has_three_candidates(binding_completion: dict) -> None:
    assert binding_completion["dataset_id"] == DATASET_ID
    assert binding_completion["dataset_version"] == DATASET_VERSION
    assert binding_completion["dataset_content_digest"] == DATASET_CONTENT_DIGEST
    assert binding_completion["dataset_binding_active"] is True
    assert len(binding_completion["candidates"]) == len(FLEET_CANDIDATES)


def test_validate_binding_completion_accepted(binding_completion: dict) -> None:
    result = validate_binding_completion_v0(binding_completion, repo_root=REPO_ROOT)
    assert result.verdict is ValidationVerdict.ACCEPTED
    assert result.valid is True
    assert not result.fail_reasons


def test_candidate_bindings_include_required_fields(binding_completion: dict) -> None:
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
        "canonical_trading_logic_version",
        "implementation_digest",
        "config_digest",
        "data_digest",
        "binding_semantic_digest",
    }
    for candidate in binding_completion["candidates"]:
        assert required.issubset(candidate.keys())
        ds = candidate["dataset_binding"]
        assert ds["dataset_id"] == DATASET_ID
        assert ds["dataset_content_digest"] == DATASET_CONTENT_DIGEST
        assert ds["alias_is_not_sole_binding"] is True
        assert candidate["instrument_binding"]["futures_only"] is True
        assert candidate["instrument_binding"]["bitcoin_direction_allowed"] is False
        assert candidate["fee_model_binding"]["fee_bps"] > 0
        assert candidate["slippage_model_binding"]["slippage_bps"] > 0


def test_common_economic_policy_across_candidates(binding_completion: dict) -> None:
    policies = [c["economic_policy_binding"] for c in binding_completion["candidates"]]
    assert len(set(map(str, policies))) == 1


def test_digest_drift_fail_closed(binding_completion: dict) -> None:
    broken = copy.deepcopy(binding_completion)
    broken["candidates"][0]["binding_semantic_digest"] = "0" * 64
    result = validate_binding_completion_v0(broken, repo_root=REPO_ROOT)
    assert result.verdict is ValidationVerdict.REJECTED


def test_completion_digest_stable(binding_completion: dict) -> None:
    assert binding_completion["completion_digest"] == compute_completion_digest_v0(
        binding_completion
    )


def test_idempotent_rebind_no_op_when_unchanged(binding_completion: dict, tmp_path: Path) -> None:
    config_dir = tmp_path / "config" / "research"
    config_dir.mkdir(parents=True)
    (
        config_dir / "final_research_fleet_okx_full_panel_versioned_binding_completion_v0.json"
    ).write_text(
        '{"completion_digest":"'
        + binding_completion["completion_digest"]
        + '","dataset_content_digest":"'
        + DATASET_CONTENT_DIGEST
        + '"}',
        encoding="utf-8",
    )
    status = detect_idempotent_binding_status_v0(
        repo_root=tmp_path,
        new_completion=binding_completion,
    )
    assert status is IdempotentBindingStatus.NO_OP_SUCCESS


def test_verify_preconditions_requires_go_token() -> None:
    ok, reasons = verify_preconditions_v0(
        repo_root=REPO_ROOT,
        confirm="INVALID",
        origin_main_sha="b60573f8ccfb165e3e8706912c84a99326104c5c",
    )
    assert ok is False
    assert any("GO_TOKEN_INVALID" in reason for reason in reasons)
