"""Post-restoration parallel-owner and skip-safety path quarantine v1.

Static/docs/source-order guards only. Reuses existing owner tests; does not
duplicate their runtime proofs. No core runtime mutation. No live authority.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md"
)
CAP65_SPEC = REPO_ROOT / "docs/ops/specs/CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1.md"
HARDENING_SPEC = (
    REPO_ROOT / "docs/ops/specs/MASTER_V2_HARDENING_V2_HISTORICAL_SAFETY_SEAM_REMEDIATION_V1.md"
)
A06_SPEC = REPO_ROOT / "docs/ops/specs/MASTER_V2_A06_CAPITAL_RISK_SIZING_INTENT_RESTORE_V1.md"
SIBLING_SPEC = (
    REPO_ROOT / "docs/ops/specs/MASTER_V2_CAPITAL_RISK_SIZING_SAFETY_INTENT_RESTORE_V1.md"
)
AUTHORITY_MATRIX = REPO_ROOT / "src/ops/exit_policy_producer_binding_v1/authority_matrix_v1.py"
PRODUCERS_MODULE = REPO_ROOT / "src/ops/exit_policy_producer_binding_v1/producers_v1.py"
HISTORICAL_CAP65_MATRIX = (
    REPO_ROOT
    / "docs/evidence/capability_6_5_exit_policy_producer_binding_v1"
    / "productive_binding/exit_authority_matrix_v1.json"
)

REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
HARDENING_MODULE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "hardening_cycle_bridge_v2.py"
)
DECISION_HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
MAPPER_MODULE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "intended_action_mapper_v1.py"
)
INTENT_PIPELINE = (
    REPO_ROOT
    / "src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py"
)
A06_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py"
SIBLING_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_safety_intent_restore_v1.py"

_PRODUCTIVE_HOSTS = (REPLAY_MODULE, HARDENING_MODULE, DECISION_HOST, MAPPER_MODULE)
_FORBIDDEN_OWNER_GRAPH_CALLS = frozenset(
    {
        "evaluate_bridge_safety_v2",
        "run_canonical_core_runtime_integration_intent_pipeline_bridge_v0",
        "run_canonical_core_runtime_integration_intent_pipeline_from_harness_v0",
        "compose_capital_risk_sizing_intent_from_core_evidence_v1",
        "compose_capital_risk_sizing_safety_intent_from_core_evidence_v1",
    }
)
_FORBIDDEN_OWNER_GRAPH_IMPORT_ROOTS = (
    "trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0",
    "trading.master_v2.capital_risk_sizing_intent_restore_v1",
    "trading.master_v2.capital_risk_sizing_safety_intent_restore_v1",
)
_STALE_BIND_PHRASE = "bind evaluate_bridge_safety_v2 into productive host"

_REUSED_GUARDS = (
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py",
    REPO_ROOT / "tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_a06_capital_risk_sizing_intent_restore_contract_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_capital_risk_sizing_safety_intent_restore_contract_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py",
)


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_spec_is_subordinate_quarantine_not_restoration_reopen() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "CORE_RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "NEW_STAGE=false" in spec
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "MASTER_V2_DOUBLE_PLAY_RESTORATION_COMPLETE=true" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    assert "NO_EXECUTION_AUTHORITY=true" in spec


def test_master_names_quarantine_and_owner_invariants() -> None:
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    spec = SPEC_PATH.read_text(encoding="utf-8")
    for text in (section, spec):
        assert "EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_OWNER=false" in text
        assert "EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_HOST_REACHABLE=false" in text
        assert "CAP_6_5_EXIT_POLICY_PRODUCERS=INPUT_PRODUCERS_ONLY" in text
        assert "INTENT_PIPELINE_BRIDGE_PRODUCTIVE_REACHABLE=false" in text
        assert "CRS_INTENT_RESTORE_V1_PRODUCTIVE_PATH=false" in text
        assert "CRS_SAFETY_INTENT_RESTORE_V1_ROLE=PROOF_OR_RESTORE_COMPOSER_ONLY" in text
        assert "SECOND_COMPUTE_OWNER_EXISTS=false" in text
        assert "SECOND_RISK_OWNER_EXISTS=false" in text
        assert "SECOND_SAFETY_OWNER_EXISTS=false" in text
        assert "SECOND_INTENT_OWNER_EXISTS=false" in text
        assert "NO_29Q_BEFORE_SAFETY=true" in text
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md"
        in section
    )
    assert "PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1=true" in section
    assert "RESTORATION_REOPEN_REQUIRED=false" in section


def test_cap65_stale_bind_language_rejected_as_current_requirement() -> None:
    matrix_source = AUTHORITY_MATRIX.read_text(encoding="utf-8")
    historical = HISTORICAL_CAP65_MATRIX.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    cap65 = CAP65_SPEC.read_text(encoding="utf-8")
    hardening = HARDENING_SPEC.read_text(encoding="utf-8")
    assert HISTORICAL_CAP65_MATRIX.is_file()
    assert _STALE_BIND_PHRASE in matrix_source
    assert _STALE_BIND_PHRASE in historical
    assert "HISTORICAL_EVIDENCE_MAY_RETAIN_STALE_STRING=true" in spec
    assert "CURRENT_BINDING_REQUIREMENT_STATUS=REJECTED_BY_RESTORED_BASELINE" in spec
    assert "REJECTED_BY_RESTORED_BASELINE" in cap65
    for text in (cap65, hardening, spec):
        assert "EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_OWNER=false" in text
        assert "EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_HOST_REACHABLE=false" in text
    assert "CAP_6_5_EXIT_POLICY_PRODUCERS=INPUT_PRODUCERS_ONLY" in cap65
    assert "NOT_SAFETY_OWNER=true" in cap65
    assert "NOT_ENTRY_EXIT_OWNER=true" in cap65
    assert "NOT_INTENT_OWNER=true" in cap65
    assert "NOT_EXECUTION_AUTHORITY=true" in cap65
    assert "CAP65_STALE_BIND_LANGUAGE_RESOLVED=true" in cap65
    assert "CAP65_STALE_BIND_LANGUAGE_RESOLVED=true" in spec


def test_productive_hosts_do_not_call_quarantined_owner_graphs() -> None:
    for path in _PRODUCTIVE_HOSTS:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        called = _called_names(tree)
        imported = _imported_modules(tree)
        assert not (called & _FORBIDDEN_OWNER_GRAPH_CALLS), path
        for root in _FORBIDDEN_OWNER_GRAPH_IMPORT_ROOTS:
            assert all(
                module != root and not module.startswith(f"{root}.") for module in imported
            ), path
        assert "evaluate_bridge_safety_v2(" not in source


def test_cap65_producers_remain_input_producer_only_not_safety_owner() -> None:
    source = PRODUCERS_MODULE.read_text(encoding="utf-8")
    assert "evaluate_bridge_safety_v2" in source
    assert "build_canonical_order_intent_v1(" not in source
    assert "bind_safety_kernel_offline_replay_evidence_v0(" not in source
    assert "run_integrated_offline_trading_logic_replay_v1(" not in source
    hardening = HARDENING_MODULE.read_text(encoding="utf-8")
    assert "evaluate_host_exit_policy_producers_v1" in hardening
    assert "evaluate_bridge_safety_v2(" not in hardening


def test_intent_pipeline_and_restore_composers_remain_non_productive() -> None:
    a06 = A06_SPEC.read_text(encoding="utf-8")
    sibling = SIBLING_SPEC.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    replay = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "CRS_INTENT_RESTORE_V1_PRODUCTIVE_PATH=false" in a06
    assert "CRS_INTENT_RESTORE_PRODUCTIVE_REACHABLE=false" in a06
    assert "PRODUCTIVE_REPLAY_ORCHESTRATOR=false" in a06
    assert "CRS_SAFETY_INTENT_RESTORE_V1_ROLE=PROOF_OR_RESTORE_COMPOSER_ONLY" in sibling
    assert "PRODUCTIVE_OWNER=false" in sibling
    assert "INTENT_PIPELINE_BRIDGE_PRODUCTIVE_REACHABLE=false" in spec
    assert "PRODUCTIVE_REPLAY_PATH_ALLOWED=false" in spec
    assert INTENT_PIPELINE.is_file()
    assert A06_MODULE.is_file()
    assert SIBLING_MODULE.is_file()
    assert "capital_risk_sizing_intent_restore_v1" not in replay
    assert "capital_risk_sizing_safety_intent_restore_v1" not in replay
    assert "canonical_core_runtime_integration_intent_pipeline_bridge_v0" not in replay
    pipeline = INTENT_PIPELINE.read_text(encoding="utf-8")
    assert "evaluate_offline_safety_kernel_boundary_v0" not in pipeline
    assert "bind_safety_kernel_offline_replay_evidence_v0" not in pipeline
    a06_source = A06_MODULE.read_text(encoding="utf-8")
    assert "bind_safety_kernel_offline_replay_evidence_v0" not in a06_source
    sibling_source = SIBLING_MODULE.read_text(encoding="utf-8")
    safety_i = sibling_source.index("bind_safety_kernel_offline_replay_evidence_v0(")
    intent_i = sibling_source.index("build_canonical_order_intent_v1(")
    assert sibling_source.index("evaluate_quantity_chain_v1(") < safety_i < intent_i


def test_replay_remains_sole_productive_owner_order() -> None:
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    crs = source.index("bind_capital_risk_sizing_offline_replay_evidence_v0(")
    safety = source.index("bind_safety_kernel_offline_replay_evidence_v0(")
    intent = source.index("bind_canonical_order_intent_offline_replay_evidence_v0(")
    assert crs < safety < intent
    assert source.count("bind_capital_risk_sizing_offline_replay_evidence_v0(") == 1
    assert source.count("bind_safety_kernel_offline_replay_evidence_v0(") == 1
    assert source.count("bind_canonical_order_intent_offline_replay_evidence_v0(") == 1


def test_reused_preservation_guards_remain_present() -> None:
    for path in _REUSED_GUARDS:
        assert path.is_file(), path
    restore = _REUSED_GUARDS[0].read_text(encoding="utf-8")
    hardening = _REUSED_GUARDS[2].read_text(encoding="utf-8")
    a06 = _REUSED_GUARDS[3].read_text(encoding="utf-8")
    sibling = _REUSED_GUARDS[4].read_text(encoding="utf-8")
    assert "crs < safety < intent" in restore
    assert 'order == ["29P", "SAFETY", "29Q", "RECON", "KS"]' in restore
    assert "evaluate_bridge_safety_v2(" not in HARDENING_MODULE.read_text(encoding="utf-8")
    assert "BRIDGE_SAFETY_ROLE=INPUT_PRODUCER_ONLY" in hardening
    assert "A06_ADAPTER_COMPUTE_OWNER" in a06
    assert "ADAPTER_IS_SAFETY_OWNER" in sibling
    assert "capital_risk_sizing_safety_intent_restore_v1" not in REPLAY_MODULE.read_text(
        encoding="utf-8"
    )


def test_out_of_scope_p0_surfaces_are_not_mutated_this_slice() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "LEGACY_STRATEGY_POSITION_SIZERS=NOT_MUTATED_THIS_SLICE" in spec
    assert "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL=NOT_MUTATED_THIS_SLICE" in spec
    assert "PR_6129=NOT_THIS_SLICE" in spec
    assert "RECOVERY_TRACK=NOT_THIS_SLICE" in spec
    replay = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "src.risk.position_sizer" not in replay
    assert "independent_pre_trade_safety" not in replay
