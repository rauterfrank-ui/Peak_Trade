"""Post-restoration remaining P0 quarantine v1.

Static/docs/source-order guards only. Reuses existing owner tests; does not
duplicate their runtime proofs. No core runtime mutation. No live authority.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md"
PARENT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
)
PRIOR_QUARANTINE_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md"
)
INVENTORY_DOC = REPO_ROOT / "docs/governance/RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md"
TOPOLOGY_DOC = REPO_ROOT / "docs/governance/RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md"
INVENTORY_JSON = REPO_ROOT / "config/governance/risk_sizing_owner_inventory_ssot_v1.json"
KERNEL_MODULE = REPO_ROOT / "src/meta/learning_loop/independent_pre_trade_safety_kernel_v1.py"
CRS_OWNER = REPO_ROOT / "src/governance/capital_risk_sizing_v1.py"
SAFETY_OWNER = (
    REPO_ROOT / "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
)
INTENT_OWNER = REPO_ROOT / "src/governance/canonical_order_intent_v1.py"
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
CAP72_HOST_BINDING = (
    REPO_ROOT / "src/ops/single_future_stateful_no_order_runtime_activation_v1/host_binding_v1.py"
)

_PRODUCTIVE_HOSTS = (
    REPLAY_MODULE,
    HARDENING_MODULE,
    DECISION_HOST,
    MAPPER_MODULE,
    CRS_OWNER,
    SAFETY_OWNER,
    INTENT_OWNER,
    CAP72_HOST_BINDING,
)
_FORBIDDEN_IMPORT_ROOTS = (
    "src.risk.position_sizer",
    "src.core.position_sizing",
    "src.core.risk",
    "src.portfolio",
    "src.meta.learning_loop.independent_pre_trade_safety_kernel_v1",
)
_FORBIDDEN_CALLS = frozenset(
    {
        "calc_position_size",
        "build_position_sizer_from_config",
        "produce_independent_pre_trade_safety_kernel_v1",
        "build_independent_pre_trade_safety_kernel_v1",
        "reverify_independent_pre_trade_safety_kernel_v1",
        "verify_independent_pre_trade_safety_kernel_inputs",
    }
)
_FORBIDDEN_IMPORTED_NAMES = _FORBIDDEN_CALLS | frozenset(
    {
        "PositionSizer",
        "BasePositionSizer",
        "PortfolioManager",
        "EqualWeightPortfolioStrategy",
    }
)
_REUSED_GUARDS = (
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py",
    REPO_ROOT / "tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_owner_composed_full_chain_host_consumption_proof_v1.py",
    REPO_ROOT / "tests/ops/test_master_v2_section_5_3_host_graph_ssot_adjudication_v1.py",
    REPO_ROOT / "tests/ops/test_master_v2_c4_named_master_ssot_pointer_v1.py",
    REPO_ROOT
    / "tests/governance/test_historically_attested_current_system_semantic_restoration_authorization_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_parallel_owner_and_skip_safety_path_quarantine_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py",
    REPO_ROOT / "tests/meta/test_independent_pre_trade_safety_kernel_v1.py",
    REPO_ROOT / "tests/governance/test_risk_sizing_owner_inventory_ssot_v1.py",
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


def _imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.rsplit(".", 1)[-1])
    return names


def _import_hits_forbidden(module: str) -> bool:
    for root in _FORBIDDEN_IMPORT_ROOTS:
        if module == root or module.startswith(f"{root}."):
            return True
    return False


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
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "RUNTIME_DECOUPLING_REQUIRED=false" in spec


def test_master_names_remaining_p0_quarantine_and_owner_invariants() -> None:
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    spec = SPEC_PATH.read_text(encoding="utf-8")
    for text in (section, spec):
        assert "LEGACY_STRATEGY_POSITION_SIZERS_PRODUCTIVE_HOST_REACHABLE=false" in text
        assert "LEGACY_STRATEGY_POSITION_SIZERS_CANONICAL_RISK_OWNER=false" in text
        assert "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_PRODUCTIVE_REPLAY_REACHABLE=false" in text
        assert "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REPLAY_SAFETY_OWNER=false" in text
        assert "SECOND_RISK_OWNER_EXISTS=false" in text
        assert "SECOND_SAFETY_OWNER_EXISTS=false" in text
        assert "NO_29Q_BEFORE_SAFETY=true" in text
        assert "RESTORATION_REOPEN_REQUIRED=false" in text
    remaining_spec = "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md"
    assert remaining_spec in section
    assert "REMAINING_P0_QUARANTINE_V1=true" in section
    assert "LEGACY_STRATEGY_POSITION_SIZERS_ROLE=RESEARCH_BACKTEST_NON_PRODUCTIVE" in spec
    assert "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_ROLE=NON_AUTHORIZING_NON_REPLAY_SAFETY" in spec


def test_productive_hosts_do_not_import_or_call_legacy_sizers_as_quantity_owner() -> None:
    for path in _PRODUCTIVE_HOSTS:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = _imported_modules(tree)
        called = _called_names(tree)
        imported_names = _imported_names(tree)
        hits = sorted(module for module in imported if _import_hits_forbidden(module))
        assert hits == [], f"{path}: forbidden imports {hits}"
        forbidden_called = called & _FORBIDDEN_CALLS
        assert not forbidden_called, f"{path}: forbidden calls {sorted(forbidden_called)}"
        forbidden_names = imported_names & _FORBIDDEN_IMPORTED_NAMES
        assert not forbidden_names, f"{path}: forbidden imported names {sorted(forbidden_names)}"


def test_step29p_remains_sole_productive_risk_owner_and_does_not_import_legacy_sizers() -> None:
    source = CRS_OWNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = _imported_modules(tree)
    assert not any(_import_hits_forbidden(module) for module in imported)
    assert "def evaluate_quantity_chain_v1(" in source
    assert "def evaluate_capital_risk_sizing_v1(" in source
    replay = REPLAY_MODULE.read_text(encoding="utf-8")
    assert replay.count("bind_capital_risk_sizing_offline_replay_evidence_v0(") == 1
    assert "src.risk.position_sizer" not in replay
    assert "src.core.position_sizing" not in replay
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "RISK_OWNER=STEP-29P / src.governance.capital_risk_sizing_v1" in spec
    assert "SECOND_RISK_OWNER_EXISTS=false" in spec


def test_historical_sizer_inventory_labels_are_rejected_as_current_owner_graph() -> None:
    inventory = INVENTORY_DOC.read_text(encoding="utf-8")
    topology = TOPOLOGY_DOC.read_text(encoding="utf-8")
    json_text = INVENTORY_JSON.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED" in inventory
    assert "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED" in topology
    assert '"reachability": "REACHABLE_PRODUCTIVE"' in json_text
    assert "src.risk.position_sizer" in json_text
    assert "REJECTED_BY_RESTORED_BASELINE" in inventory
    assert "REJECTED_BY_RESTORED_BASELINE" in topology
    assert "REJECTED_BY_RESTORED_BASELINE" in spec
    assert "HISTORICAL_TECHNICAL_CAPABILITY_INVENTORY_NOT_OWNER_GRAPH_AUTHORIZATION" in spec
    assert "LEGACY_STRATEGY_POSITION_SIZERS_CANONICAL_RISK_OWNER=false" in inventory


def test_independent_kernel_remains_non_authorizing_and_not_replay_safety_owner() -> None:
    source = KERNEL_MODULE.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert 'AUTHORITY_LEVEL = "NON_AUTHORITIZING"' in source
    assert "safety_decision_approve_does_not_create_execution_permission" in source
    assert "safety_decision_approve_does_not_authorize_submission" in source
    assert "independent_pre_trade_safety_kernel_is_offline_only" in source
    assert "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REPLAY_SAFETY_OWNER=false" in spec
    assert "SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true" in spec
    safety_owner = SAFETY_OWNER.read_text(encoding="utf-8")
    assert "independent_pre_trade_safety_kernel" not in safety_owner
    replay = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "independent_pre_trade_safety" not in replay
    assert replay.count("bind_safety_kernel_offline_replay_evidence_v0(") == 1


def test_replay_order_and_enter_without_coi_remain_protected() -> None:
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    crs = source.index("bind_capital_risk_sizing_offline_replay_evidence_v0(")
    safety = source.index("bind_safety_kernel_offline_replay_evidence_v0(")
    intent = source.index("bind_canonical_order_intent_offline_replay_evidence_v0(")
    assert crs < safety < intent
    mapper = MAPPER_MODULE.read_text(encoding="utf-8")
    assert "enter_without_canonical_order_intent" in mapper
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "STEP_29P_BEFORE_SAFETY=true" in spec
    assert "SAFETY_BEFORE_STEP_29Q=true" in spec
    assert "NO_29Q_BEFORE_SAFETY=true" in spec
    assert "ENTER_WITHOUT_CANONICAL_ORDER_INTENT_CANNOT_BUY_OR_SELL=true" in spec
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "NO_29Q_BEFORE_SAFETY=true" in section


def test_prior_quarantine_and_parent_contract_remain_and_out_of_scope_is_named() -> None:
    prior = PRIOR_QUARANTINE_SPEC.read_text(encoding="utf-8")
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "LEGACY_STRATEGY_POSITION_SIZERS=NOT_MUTATED_THIS_SLICE" in prior
    assert "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL=NOT_MUTATED_THIS_SLICE" in prior
    assert "test_peak_trade_post_restoration_remaining_p0_quarantine_v1.py" in parent
    assert "ACCOUNTING_PORTFOLIO_ALIGNMENT=NOT_THIS_SLICE" in spec
    assert "EXECUTION_PIPELINE=NOT_THIS_SLICE" in spec
    assert "PR_6129=NOT_THIS_SLICE" in spec
    assert "RECOVERY_TRACK=NOT_THIS_SLICE" in spec
    assert "FORENSIC_REFERENCE_AUTHORITY=NONE" in spec
    assert "MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY" in spec


def test_reused_preservation_guards_remain_present() -> None:
    for path in _REUSED_GUARDS:
        assert path.is_file(), path
    restore = _REUSED_GUARDS[0].read_text(encoding="utf-8")
    parallel = _REUSED_GUARDS[7].read_text(encoding="utf-8")
    kernel = _REUSED_GUARDS[9].read_text(encoding="utf-8")
    assert "crs < safety < intent" in restore
    assert 'order == ["29P", "SAFETY", "29Q", "RECON", "KS"]' in restore
    assert "EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_OWNER=false" in parallel
    assert "test_authority_invariants" in kernel
    assert "_assert_non_execution" in kernel
