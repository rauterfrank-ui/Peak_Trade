import json
from pathlib import Path

CONFIG_PATH = Path("config/research/offline_source_evidence_instrumentation_admissibility_gap_v0.json")
DOC_PATH = Path("docs/governance/OFFLINE_SOURCE_EVIDENCE_INSTRUMENTATION_ADMISSIBILITY_GAP_V0.md")


def load_config():
    return json.loads(CONFIG_PATH.read_text())


def test_scope_is_offline_only_definition_execution():
    cfg = load_config()
    assert cfg["scope_id"] == "OFFLINE_SOURCE_EVIDENCE_INSTRUMENTATION_ADMISSIBILITY_GAP_DEFINITION_EXECUTION_V0"
    assert cfg["process_classification"] == "OFFLINE_ONLY_SOURCE_EVIDENCE_INSTRUMENTATION_OR_ADMISSIBILITY_GAP_DEFINITION_EXECUTION_SCOPE_V0"
    assert cfg["scope_classification"] == "SOURCE_EVIDENCE_CONTRACT_AND_ADMISSIBILITY_DEFINITION_ONLY_NO_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY"


def test_go_token_consumed_once_for_this_scope_only():
    cfg = load_config()
    assert cfg["go_token_consumption"]["token"] == "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_SOURCE_EVIDENCE_INSTRUMENTATION_OR_ADMISSIBILITY_GAP_DEFINITION_EXECUTION_SCOPE_V0"
    assert cfg["go_token_consumption"]["status"] == "CONSUMED_ONCE_FOR_THIS_OFFLINE_ONLY_DEFINITION_EXECUTION_SCOPE"


def test_parent_evidence_is_bound():
    cfg = load_config()
    parent = cfg["parent_evidence"]
    assert parent["pr4910_scope_definition_merge_closeout_dir"].endswith("post_pr4909_terminal_failure_next_evidence_scope_definition_merge_closeout_20260706T052749Z")
    assert parent["pr4909_artifact_materialization_merge_closeout_dir"].endswith("pr4909_squash_merge_closeout_20260706T051959Z")
    assert parent["pr4909_materialization_bundle"].endswith("post_pr4908_offline_terminal_failure_artifact_materialization_v0_20260706T051227Z")


def test_all_required_source_evidence_contracts_defined():
    cfg = load_config()
    contract_ids = {item["contract_id"] for item in cfg["source_evidence_contracts"]}
    assert contract_ids == {
        "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0",
        "LONG_SHORT_ATTRIBUTION_LEDGER_V0",
        "TURNOVER_COST_DRAG_TIMESERIES_V0",
        "INSTRUMENT_CONCENTRATION_DETAIL_V0",
    }


def test_each_contract_has_manifest_ref_and_required_fields():
    cfg = load_config()
    for contract in cfg["source_evidence_contracts"]:
        assert "manifest_ref" in contract["required_fields"]
        assert len(contract["required_fields"]) >= 10
        assert contract["admissibility_status"].startswith("REQUIRED_FOR_FUTURE_")


def test_future_admissibility_blocks_incomplete_claims_without_reclassifying_terminal_evidence():
    cfg = load_config()
    requirements = cfg["future_evaluation_admissibility_requirements"]
    assert requirements["economic_claim_requires_all_contracts_present"] is True
    assert requirements["missing_contract_blocks_promotion_claim"] is True
    assert requirements["missing_contract_does_not_reclassify_historical_terminal_failure"] is True
    assert requirements["failed_evidence_is_terminal"] is True


def test_authority_flags_all_false():
    cfg = load_config()
    assert all(value is False for value in cfg["authority_flags"].values())


def test_forbidden_actions_cover_runtime_and_economic_boundaries():
    cfg = load_config()
    forbidden = set(cfg["explicitly_not_authorized"])
    for item in [
        "economic_evaluation_execution",
        "binding_retry",
        "parameter_optimization",
        "threshold_lowering",
        "historical_failure_reclassification",
        "runtime_rewire",
        "shadow",
        "paper",
        "testnet",
        "scheduler",
        "adapter_submission",
        "orders",
        "credentials",
        "arming",
        "canary",
        "live",
    ]:
        assert item in forbidden


def test_governance_doc_carries_terminal_rule_and_next_step():
    text = DOC_PATH.read_text()
    assert "FAILED_EVIDENCE_IS_TERMINAL=true" in text
    assert "does not execute a new economic evaluation" in text
    assert "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_SOURCE_EVIDENCE_CONTRACT_IMPLEMENTATION_OR_COLLECTOR_MATERIALIZATION_SCOPE_V0" in text
