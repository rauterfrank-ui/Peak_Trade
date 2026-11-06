import json
from pathlib import Path

CONFIG_PATH = Path(
    "config/research/post_pr4909_terminal_failure_next_evidence_scope_definition_v0.json"
)
DOC_PATH = Path("docs/governance/POST_PR4909_TERMINAL_FAILURE_NEXT_EVIDENCE_SCOPE_DEFINITION_V0.md")


def test_scope_config_exists_and_is_scope_definition_only():
    cfg = json.loads(CONFIG_PATH.read_text())
    assert cfg["scope_id"] == "POST_PR4909_TERMINAL_FAILURE_NEXT_EVIDENCE_SCOPE_DEFINITION_V0"
    assert (
        cfg["process_classification"]
        == "POST_PR4909_TERMINAL_FAILURE_NEXT_EVIDENCE_SCOPE_DEFINITION_ONLY_V0"
    )
    assert (
        cfg["scope_classification"]
        == "NEW_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_DEFINITION_ONLY_AFTER_OFFLINE_TERMINAL_FAILURE_ARTIFACT_MATERIALIZATION_V0"
    )


def test_go_token_consumed_for_definition_only():
    cfg = json.loads(CONFIG_PATH.read_text())
    assert (
        cfg["go_token_consumption"]["token"]
        == "GO_OPERATOR_RATIFY_NEXT_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_AFTER_OFFLINE_TERMINAL_FAILURE_ARTIFACT_MATERIALIZATION_V0"
    )
    assert cfg["go_token_consumption"]["status"] == "CONSUMED_ONCE_FOR_SCOPE_DEFINITION_ONLY"


def test_parent_closeout_and_materialization_are_bound():
    cfg = json.loads(CONFIG_PATH.read_text())
    parent = cfg["parent_evidence"]
    assert parent["pr4909_closeout_dir"].endswith("pr4909_squash_merge_closeout_20260706T051959Z")
    assert parent["offline_terminal_failure_artifact_materialization_bundle"].endswith(
        "post_pr4908_offline_terminal_failure_artifact_materialization_v0_20260706T051227Z"
    )
    assert len(parent["ignored_incomplete_closeout_dirs"]) == 2


def test_missing_source_evidence_is_explicit():
    cfg = json.loads(CONFIG_PATH.read_text())
    missing = set(cfg["terminal_failure_materialization_summary"]["missing_source_evidence"])
    assert "trade_ledger_per_trade_decomposition" in missing
    assert "long_short_attribution_ledger" in missing
    assert "short_contribution_ledger_values" in missing
    assert "turnover_timeseries_decomposition" in missing
    assert "fee_drag_decomposition_detail" in missing
    assert "slippage_impact_decomposition_detail" in missing
    assert "instrument_concentration_beyond_rotation_metadata" in missing


def test_failed_evidence_remains_terminal():
    cfg = json.loads(CONFIG_PATH.read_text())
    assert cfg["terminal_failure_materialization_summary"]["failed_evidence_is_terminal"] is True


def test_all_authority_flags_false():
    cfg = json.loads(CONFIG_PATH.read_text())
    assert cfg["authority_flags"]
    assert all(value is False for value in cfg["authority_flags"].values())


def test_forbidden_actions_include_runtime_and_evaluation_boundaries():
    cfg = json.loads(CONFIG_PATH.read_text())
    forbidden = set(cfg["next_scope_definition"]["explicitly_not_authorized_in_this_scope"])
    for item in [
        "economic_evaluation_execution",
        "binding_retry",
        "runtime_rewire",
        "shadow",
        "paper",
        "testnet",
        "scheduler",
        "orders",
        "credentials",
        "arming",
        "canary",
        "live",
    ]:
        assert item in forbidden


def test_next_step_is_separate_execution_go():
    cfg = json.loads(CONFIG_PATH.read_text())
    assert (
        cfg["next_step"]
        == "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_SOURCE_EVIDENCE_INSTRUMENTATION_OR_ADMISSIBILITY_GAP_DEFINITION_EXECUTION_SCOPE_V0"
    )


def test_governance_doc_contains_non_authority_and_terminal_rule():
    text = DOC_PATH.read_text()
    assert "SCOPE_DEFINED_NOT_EXECUTED" in text
    assert "FAILED_EVIDENCE_IS_TERMINAL=true" in text
    assert "does not authorize" in text
    assert (
        "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_SOURCE_EVIDENCE_INSTRUMENTATION_OR_ADMISSIBILITY_GAP_DEFINITION_EXECUTION_SCOPE_V0"
        in text
    )
