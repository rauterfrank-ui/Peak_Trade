"""Post-restoration simulated execution pipeline adjudication v1.

Static/docs/source-order guards. Reuses existing owner tests; does not
duplicate their runtime proofs. Does not repair the preexisting Cap 3.1
CALL_GRAPH tuple equality test. No core runtime mutation. No live authority.
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    SIMULATED_EXECUTION_DELEGATE,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    map_replay_result_to_intended_analytical_action_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md"
)
PARENT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
)
ACCOUNTING_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md"
)
REMAINING_P0_SPEC = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md"
)
PARALLEL_OWNER_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md"
)
HOST_GRAPH_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_HOST_GRAPH_SSOT_AND_OWNER_COMPOSED_FULL_CHAIN_PROOF_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
PORT_MODULE = (
    REPO_ROOT
    / "src/ops/single_future_stateful_no_order_runtime_activation_v1"
    / "simulated_execution_port_v1.py"
)
HOST_BINDING = (
    REPO_ROOT
    / "src/ops/single_future_stateful_no_order_runtime_activation_v1"
    / "host_binding_v1.py"
)
CAP3_BRIDGE = (
    REPO_ROOT / "src/ops/productive_futures_accounting_runtime_binding_v1/bridge_binding_v1.py"
)
CAP3_FILL = REPO_ROOT / "src/ops/productive_futures_accounting_runtime_binding_v1/fill_model_v1.py"
CAP3_CONSTANTS = (
    REPO_ROOT / "src/ops/productive_futures_accounting_runtime_binding_v1/constants_v1.py"
)
DECISION_HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
VERIFIER_V1 = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "full_economic_reconstruction_verifier_v1.py"
)
MAPPER_MODULE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "intended_action_mapper_v1.py"
)
HARDENING_MODULE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "hardening_cycle_bridge_v2.py"
)
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
PREEXISTING_CALL_GRAPH_TEST = (
    REPO_ROOT / "tests/ops/test_productive_futures_accounting_runtime_binding_v1.py"
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
    REPO_ROOT / "tests/ops/test_peak_trade_post_restoration_remaining_p0_quarantine_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py",
    REPO_ROOT / "tests/ops/test_productive_futures_accounting_runtime_binding_v1.py",
    REPO_ROOT / "tests/ops/test_wallclock_bridge_hardening_v2.py",
)

_FORBIDDEN_PAPER_IMPORT_ROOTS = (
    "src.execution.paper.engine",
    "src.execution.paper.broker",
    "execution.paper.engine",
    "execution.paper.broker",
)
_FORBIDDEN_REPLAY_FILL_CALLS = frozenset(
    {
        "apply_intended_action_via_canonical_accounting_v1",
        "build_simulated_fill_v1",
        "construct_simulated_execution_port_v1",
        "host_simulated_execution_port_v1",
    }
)
_FORBIDDEN_MAPPER_WRITE_CALLS = frozenset(
    {
        "apply_intended_action_via_canonical_accounting_v1",
        "build_simulated_fill_v1",
        "ensure_accounting_session_v1",
        "construct_simulated_execution_port_v1",
    }
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


def test_spec_is_subordinate_and_does_not_grant_authority() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3" in spec
    assert "CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "CORE_RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "NEW_STAGE=false" in spec
    assert "NEW_EXECUTION_COMPONENT_REQUIRED=false" in spec
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    assert "NO_EXECUTION_AUTHORITY=true" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "RUNTIME_ALIGNMENT_REQUIRED=false" in spec
    assert "RUNTIME_MUTATION_JUSTIFIED=false" in spec
    assert "FORENSIC_REFERENCE_AUTHORITY=NONE" in spec
    assert "MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_EXECUTION_RESPONSIBILITIES" in text or (
            "SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_EXECUTION_RESPONSIBILITIES"
            in text
        )
        assert "SIMULATED_EXECUTION_PIPELINE_COMPLETE=true" in text
        assert "SECOND_EXECUTION_OWNER_EXISTS=false" in text
        assert "RUNTIME_ALIGNMENT_REQUIRED=false" in text
        assert "RESTORATION_REOPEN_REQUIRED=false" in text
        assert "CANONICAL_EXECUTION_OWNER=SimulatedExecutionPortV1_DELEGATE_CAP3_1" in text
    assert "SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md"
        in section
    )
    assert "EARLIEST_INCOMPLETE_EDGE=NONE" in spec
    assert "SAME_EXECUTION_RESPONSIBILITY=false" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false" in spec
    assert "ADJUDICATION_RESULT=DUPLICATE_EXECUTION_OWNER_CONFLICT" not in spec
    assert "ADJUDICATION_RESULT=SIMULATED_EXECUTION_RUNTIME_COMPLETION_REQUIRED" not in spec


def test_negative_claims_are_named() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "SAME_MODEL_CLASS_IS_NOT_SAME_WRITE_AUTHORITY=true" in spec
    assert "SAME_BUY_SELL_HOLD_VOCABULARY_IS_NOT_SAME_EXECUTION_RESPONSIBILITY=true" in spec
    assert (
        "MULTIPLE_FILL_PRODUCING_HOST_MODES_IS_NOT_DUPLICATE_CANONICAL_EXECUTION_OWNER=true" in spec
    )
    assert "EXISTENCE_OF_PAPER_EXECUTION_ENGINE_IS_NOT_PRODUCTIVE_REACHABILITY=true" in spec
    assert "CALL_GRAPH_TUPLE_INEQUALITY_IS_NOT_MISSING_RUNTIME_EDGE=true" in spec
    assert "SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true" in spec
    assert "REPLAY_OUTPUT_IS_NOT_VENUE_OR_ORDER_AUTHORITY=true" in spec
    assert "HARDENING_V2_IS_SECOND_CANONICAL_EXECUTION_OWNER=false" in spec
    assert "INTEGRATED_REPLAY_FILL_AUTHORITY=NONE" in spec
    assert "MAPPER_EXECUTION_AUTHORITY=NONE" in spec


def test_canonical_wallclock_execution_owner_is_port_delegating_to_cap31() -> None:
    host = DECISION_HOST.read_text(encoding="utf-8")
    port = PORT_MODULE.read_text(encoding="utf-8")
    host_binding = HOST_BINDING.read_text(encoding="utf-8")
    assert "host_simulated_execution_port_v1" in host
    assert "apply_intended_action_via_canonical_accounting_v1" in host
    assert "apply_intended_action_via_canonical_accounting_v1" in port
    assert "construct_simulated_execution_port_v1" in host_binding
    assert SimulatedExecutionPortV1.PORT_KIND == "SIMULATED_EXECUTION_PORT_V1"
    assert SIMULATED_EXECUTION_DELEGATE.endswith(
        "apply_intended_action_via_canonical_accounting_v1"
    )
    assert "build_simulated_fill_v1" in CAP3_BRIDGE.read_text(encoding="utf-8")
    assert "no portfolio authority" in CAP3_FILL.read_text(encoding="utf-8")
    imported_port = _imported_modules(ast.parse(port))
    assert any("bridge_binding_v1" in module for module in imported_port)
    assert all(
        module not in _FORBIDDEN_PAPER_IMPORT_ROOTS
        and not any(module.startswith(f"{root}.") for root in _FORBIDDEN_PAPER_IMPORT_ROOTS)
        for module in imported_port
    )
    assert "execution.paper.engine" in port
    assert "execution.paper.broker" in port
    assert "_FORBIDDEN_IMPORT_SUFFIXES" in port
    host_tree = ast.parse(host)
    assert "IdempotentPortfolioV2" not in host
    imported_host = _imported_modules(host_tree)
    assert all("idempotent_portfolio_v2" not in module for module in imported_host)
    assert all(
        module not in _FORBIDDEN_PAPER_IMPORT_ROOTS
        and not any(module.startswith(f"{root}.") for root in _FORBIDDEN_PAPER_IMPORT_ROOTS)
        for module in imported_host
    )


def test_replay_has_no_fill_or_execution_authority() -> None:
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = _called_names(tree)
    imported = _imported_modules(tree)
    assert not (called & _FORBIDDEN_REPLAY_FILL_CALLS)
    assert all("simulated_execution_port" not in module for module in imported)
    assert all("productive_futures_accounting" not in module for module in imported)
    assert all("idempotent_portfolio_v2" not in module for module in imported)
    crs = source.index("bind_capital_risk_sizing_offline_replay_evidence_v0(")
    safety = source.index("bind_safety_kernel_offline_replay_evidence_v0(")
    intent = source.index("bind_canonical_order_intent_offline_replay_evidence_v0(")
    assert crs < safety < intent
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "INTEGRATED_REPLAY_FILL_AUTHORITY=NONE" in spec
    assert "INTEGRATED_REPLAY_FILL_AUTHORITY=NONE" in section
    assert "NO_29Q_BEFORE_SAFETY=true" in section


def test_mapper_remains_translator_without_write_authority() -> None:
    source = MAPPER_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = _called_names(tree)
    imported = _imported_modules(tree)
    assert not (called & _FORBIDDEN_MAPPER_WRITE_CALLS)
    assert all("productive_futures_accounting" not in module for module in imported)
    assert all("simulated_execution_port" not in module for module in imported)
    assert all("idempotent_portfolio_v2" not in module for module in imported)
    assert "enter_without_canonical_order_intent" in source
    assert "NO_CANONICAL_ORDER_INTENT" in source
    assert "historical_exit_or_reduce" in source
    enter_hold_idx = source.index("enter_without_coi")
    buy_idx = source.index('intended_side="BUY"', enter_hold_idx)
    assert source.index('intended_side="HOLD"', enter_hold_idx) < buy_idx
    hold_return = source.rindex('intended_side="HOLD"')
    assert "NON_ACTIONABLE_HOLD" in source[hold_return:]
    assert map_replay_result_to_intended_analytical_action_v1.__name__
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "MAPPER_EXECUTION_AUTHORITY=NONE" in spec
    assert "HOLD_PRODUCES_FILL=false" in spec
    assert "ENTER_WITHOUT_CANONICAL_ORDER_INTENT_PRODUCES_BUY_OR_SELL_FILL=false" in spec


def test_exit_reduce_and_cap31_flip_boundary_are_not_redefined() -> None:
    for path in (CAP3_BRIDGE, CAP3_FILL, MAPPER_MODULE, HARDENING_MODULE):
        source = path.read_text(encoding="utf-8")
        assert "EXIT_TO_HOLD" not in source
        assert "convert historical EXIT" not in source
    constants = CAP3_CONSTANTS.read_text(encoding="utf-8")
    assert "POSITION_FLIP_ALLOWED = False" in constants
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "POSITION_FLIP_ALLOWED=false" in spec
    host_graph = HOST_GRAPH_SPEC.read_text(encoding="utf-8")
    assert "MODE_SPECIFIC_ANALYTICAL_HOST" in host_graph


def test_hardening_v2_is_mode_specific_not_second_canonical_owner() -> None:
    source = HARDENING_MODULE.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "IdempotentPortfolioV2" in source
    assert "state.portfolio.apply_intended_action" in source
    assert "apply_intended_action_via_canonical_accounting_v1" not in source
    assert "ensure_accounting_session_v1" not in source
    imported = _imported_modules(ast.parse(source))
    assert all("productive_futures_accounting" not in module for module in imported)
    assert all("simulated_execution_port_v1" not in module for module in imported)
    assert "HARDENING_V2_IS_SECOND_CANONICAL_EXECUTION_OWNER=false" in spec
    assert "HARDENING_V2_IS_SECOND_CANONICAL_EXECUTION_OWNER=false" in section
    assert (
        "DIRECT_PORTFOLIO_MUTATION_BYPASS_CLASS=MODE_SPECIFIC_VALID"
        in HOST_GRAPH_SPEC.read_text(encoding="utf-8")
    )


def test_accounting_portfolio_6143_relation_remains_closed() -> None:
    accounting = ACCOUNTING_SPEC.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES" in accounting
    assert "SAME_CANONICAL_ACCOUNT_STATE_DOUBLE_WRITTEN_IN_ONE_CYCLE=false" in accounting
    assert "EXECUTION_PIPELINE_INTEGRATION=NOT_THIS_SLICE" in accounting
    assert "SEE_ALSO_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=" in accounting
    assert "ACCOUNTING_PORTFOLIO_RELATION=" in spec
    assert "ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1=true" in section
    assert "SAME_CANONICAL_ACCOUNT_STATE_DOUBLE_WRITTEN_IN_ONE_CYCLE=false" in section


def test_paper_engine_and_broker_remain_outside_canonical_no_order_port() -> None:
    port = PORT_MODULE.read_text(encoding="utf-8")
    host = DECISION_HOST.read_text(encoding="utf-8")
    assert "execution.paper.engine" in port
    assert "execution.paper.broker" in port
    assert "PaperExecutionEngine" not in host
    assert "PaperBroker" not in host
    assert "from src.execution.paper.engine" not in host
    assert "from src.execution.paper.broker" not in host
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "PAPER_EXECUTION_ENGINE_PRODUCTIVE_NO_ORDER_REACHABLE=false" in spec
    assert "PAPER_BROKER_PRODUCTIVE_NO_ORDER_REACHABLE=false" in spec


def test_preexisting_call_graph_drift_remains_label_only_and_unrepaired() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    preexisting = PREEXISTING_CALL_GRAPH_TEST.read_text(encoding="utf-8")
    wallclock = DECISION_HOST.read_text(encoding="utf-8")
    verifier = VERIFIER_V1.read_text(encoding="utf-8")
    assert "PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY" in section
    assert "PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false" in section
    assert "assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH" in preexisting
    assert "xfail" not in preexisting.lower()
    assert "pytest.skip" not in preexisting
    assert "CALL_GRAPH_V1: tuple[str, ...]" in wallclock
    assert "REQUIRED_CALL_GRAPH: tuple[str, ...]" in verifier
    assert "simulated_execution_port" in wallclock
    assert '"simulated_execution_port"' not in verifier


def test_prior_contracts_remain_closed_and_map_of_truth_is_navigation_only() -> None:
    remaining = REMAINING_P0_SPEC.read_text(encoding="utf-8")
    parallel = PARALLEL_OWNER_SPEC.read_text(encoding="utf-8")
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "EXECUTION_PIPELINE=NOT_THIS_SLICE" in remaining
    assert "SEE_ALSO_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=" in remaining
    assert "SEE_ALSO_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=" in parallel
    assert "SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_PRESERVED=true" in parent
    assert "SECOND_EXECUTION_OWNER_PROHIBITED=true" in parent
    assert "PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot


def test_reused_preservation_guards_remain_present() -> None:
    for path in _REUSED_GUARDS:
        assert path.is_file(), path
    restore = _REUSED_GUARDS[0].read_text(encoding="utf-8")
    full_chain = _REUSED_GUARDS[3].read_text(encoding="utf-8")
    accounting = _REUSED_GUARDS[10].read_text(encoding="utf-8")
    assert "crs < safety < intent" in restore
    assert "construct_simulated_execution_port_v1" in full_chain
    assert "fill_present" in full_chain
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES" in accounting
