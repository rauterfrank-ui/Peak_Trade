"""PR4985 runtime activation materiality classifier contract tests."""

from __future__ import annotations

from pathlib import Path

from trading.master_v2.pr4985_runtime_activation_materiality_classifier_v0 import (
    CLASSIFIER_SLICE_ID,
    classify_runtime_activation_materiality_v0,
    classify_source_snippet_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_classifier_constants_v0() -> None:
    assert CLASSIFIER_SLICE_ID == "PR4985_RUNTIME_ACTIVATION_MATERIALITY_CLASSIFIER_V0"


def test_negative_contract_authority_literals_classified_as_fixtures_v0() -> None:
    trade_ledger_contract = (
        REPO_ROOT
        / "tests/ops/test_trade_ledger_equity_curve_execution_binding_materialization_v0_contract.py"
    )
    go_live_contract = (
        REPO_ROOT / "tests/ops/test_master_v2_go_live_blocker_register_core_doc_contract_v0.py"
    )
    for path in (trade_ledger_contract, go_live_contract):
        source = path.read_text(encoding="utf-8")
        result = classify_source_snippet_v0(
            rel_path=path.relative_to(REPO_ROOT).as_posix(),
            source=source,
        )
        assert result.runtime_authority_true_material is False
        assert result.authority_true_negative_fixture_hits
        assert not result.authority_true_material_hits


def test_docstring_examples_not_material_v0() -> None:
    for rel_path in (
        "src/exchange/kraken_live.py",
        "src/exchange/__init__.py",
        "src/execution/pipeline.py",
    ):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        result = classify_source_snippet_v0(rel_path=rel_path, source=source)
        assert result.execution_action_call_material is False
        assert not result.execution_material_activation_hits


def test_guarded_execution_infrastructure_not_runtime_activation_v0() -> None:
    for rel_path in (
        "src/execution/orchestrator.py",
        "src/execution/pipeline.py",
        "src/execution/router/router_v1.py",
        "src/exchange/dummy_client.py",
        "src/execution/broker/adapter.py",
        "src/live/safety.py",
    ):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        result = classify_source_snippet_v0(rel_path=rel_path, source=source)
        assert result.execution_action_call_material is False
        assert result.runtime_activation is False


def test_synthetic_production_fixture_with_authority_and_execution_is_material_v0() -> None:
    source = """
LIVE_AUTHORIZED = True

def run_live_path(client):
    return client.submit_order({"symbol": "BTC-USD"})
"""
    result = classify_source_snippet_v0(
        rel_path="src/runtime/ambiguous_live_activation_probe_v0.py",
        source=source,
    )
    assert result.runtime_authority_true_material is True
    assert result.execution_action_call_material is True
    assert result.runtime_activation is True
    assert result.execution_material_activation_hits


def test_fail_closed_on_ambiguous_non_docstring_execution_path_v0() -> None:
    source = """
def run_unclassified_runtime_path(client):
    return client.place_order("BTC/EUR", "buy", 0.01, "market")
"""
    result = classify_source_snippet_v0(
        rel_path="src/runtime/ambiguous_execution_probe_v0.py",
        source=source,
    )
    assert result.execution_action_call_material is True
    assert result.runtime_activation is True


def test_current_head_post_pr4985_reassessment_passes_v0() -> None:
    result = classify_runtime_activation_materiality_v0(REPO_ROOT)
    assert result.direct_true_flag_assignment is False
    assert result.runtime_authority_true_material is False
    assert result.execution_action_call_material is False
    assert result.runtime_activation is False
