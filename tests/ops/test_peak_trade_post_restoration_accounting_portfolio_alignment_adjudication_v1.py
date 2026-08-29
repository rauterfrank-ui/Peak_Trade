"""Post-restoration accounting / portfolio alignment adjudication v1.

Static/docs/source-order guards plus owner-composed writer comparison.
Reuses existing owner tests; does not duplicate their runtime proofs.
No core runtime mutation. No live authority.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    AccountingEngineError,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    apply_intended_action_via_canonical_accounting_v1,
    ensure_accounting_session_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
    IdempotencyErrorV2,
    IdempotentPortfolioV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    map_replay_result_to_intended_analytical_action_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md"
)
PARENT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
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
CAP3_ENGINE = (
    REPO_ROOT / "src/ops/productive_futures_accounting_runtime_binding_v1/accounting_engine_v1.py"
)
CAP3_BRIDGE = (
    REPO_ROOT / "src/ops/productive_futures_accounting_runtime_binding_v1/bridge_binding_v1.py"
)
CAP3_FILL = REPO_ROOT / "src/ops/productive_futures_accounting_runtime_binding_v1/fill_model_v1.py"
IDEMPOTENT_PORTFOLIO = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "idempotent_portfolio_v2.py"
)
PAPER_SHADOW_MODEL = (
    REPO_ROOT
    / "src/ops/integrated_paper_shadow_observation_session_v1/portfolio_economics_model_v1.py"
)
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
PORT_MODULE = (
    REPO_ROOT
    / "src/ops/single_future_stateful_no_order_runtime_activation_v1"
    / "simulated_execution_port_v1.py"
)

_INSTRUMENT = "ETH-USD_UM_XPERP-310404"
_MARK = Decimal("3500")
_QTY = Decimal("0.1")

_ACCOUNTING_LAYERS = (
    CAP3_ENGINE,
    CAP3_BRIDGE,
    CAP3_FILL,
    IDEMPOTENT_PORTFOLIO,
    PAPER_SHADOW_MODEL,
)

_FORBIDDEN_OWNER_CALLS = frozenset(
    {
        "evaluate_quantity_chain_v1",
        "evaluate_offline_safety_kernel_boundary_v0",
        "bind_safety_kernel_offline_replay_evidence_v0",
        "build_canonical_order_intent_v1",
        "bind_canonical_order_intent_offline_replay_evidence_v0",
        "transition_state",
        "evaluate_double_play_entry_exit_policy_v0",
    }
)
_FORBIDDEN_OWNER_IMPORT_ROOTS = (
    "src.governance.capital_risk_sizing_v1",
    "src.governance.canonical_order_intent_v1",
    "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0",
    "trading.master_v2.double_play_state",
    "trading.master_v2.double_play_entry_exit_policy_v0",
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
    REPO_ROOT / "tests/ops/test_productive_futures_accounting_runtime_binding_v1.py",
    REPO_ROOT / "tests/ops/test_wallclock_bridge_hardening_v2.py",
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


def _apply_cap31(
    *,
    side: str,
    quantity: Decimal,
    session_id: str,
    cycle_index: int,
    session=None,
    portfolio=None,
):
    if session is None:
        session = ensure_accounting_session_v1(instrument_id=_INSTRUMENT, state_root=None)
    if portfolio is None:
        portfolio = SimulatedPortfolioEconomicsModelV1(
            PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
        )
    result = apply_intended_action_via_canonical_accounting_v1(
        session=session,
        portfolio=portfolio,
        instrument_id=_INSTRUMENT,
        side=side,
        quantity=quantity,
        mark_price=_MARK,
        session_id=session_id,
        cycle_index=cycle_index,
        persist=False,
    )
    return session, portfolio, result


def test_spec_is_subordinate_and_does_not_grant_authority() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "CORE_RUNTIME_MUTATION=false" in spec
    assert "DEFAULT_RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "NEW_STAGE=false" in spec
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    assert "NO_EXECUTION_AUTHORITY=true" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "RUNTIME_ALIGNMENT_REQUIRED=false" in spec
    assert "FORENSIC_REFERENCE_AUTHORITY=NONE" in spec
    assert "MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY" in spec


def test_adjudication_result_is_distinct_compatible_responsibilities() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES" in text
        assert "ACCOUNTING_PORTFOLIO_OWNER_MODEL=DISTINCT_NON_OVERLAPPING_RESPONSIBILITIES" in text
        assert "PORTFOLIO_WRITER_DUPLICATION_UNRESOLVED=false" in text
        assert "ACCOUNTING_SEMANTIC_DIVERGENCE_UNRESOLVED=false" in text
        assert "SECOND_COMPUTE_OWNER_EXISTS=false" in text
        assert "SECOND_RISK_OWNER_EXISTS=false" in text
        assert "SECOND_SAFETY_OWNER_EXISTS=false" in text
        assert "SECOND_INTENT_OWNER_EXISTS=false" in text
    assert "INCOMPATIBLE_DUAL_WRITER" in spec
    assert "ADJUDICATION_RESULT=INCOMPATIBLE_DUAL_WRITER" not in spec
    assert "ADJUDICATION_RESULT=UNKNOWN_INSUFFICIENT_EVIDENCE" not in spec
    assert "ADJUDICATION_RESULT=SINGLE_CANONICAL_WRITER_ALREADY_EXISTS" not in spec


def test_writer_steckbriefe_are_named() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert (
        "PRODUCTIVE_FUTURES_ACCOUNTING_ROLE=CANONICAL_DOWNSTREAM_FUTURES_ACCOUNTING_WRITER_FOR_WALLCLOCK_V1_AND_CAP72"
        in spec
    )
    assert "PRODUCTIVE_FUTURES_ACCOUNTING_EXECUTION_AUTHORITY=NONE_SIMULATED_ONLY" in spec
    assert "PRODUCTIVE_FUTURES_ACCOUNTING_IDEMPOTENCE=FILL_ID_REPLAY_RETURNS_PRIOR_RESULT" in spec
    assert "HARDENING_PORTFOLIO_ROLE=MODE_SPECIFIC_ANALYTICAL_PAPER_SHADOW_PORTFOLIO_WRITER" in spec
    assert "HARDENING_PORTFOLIO_EXECUTION_AUTHORITY=NONE_SIMULATED_ONLY" in spec
    assert (
        "HARDENING_PORTFOLIO_IDEMPOTENCE=INTENT_ID_AND_FILL_ID_FAIL_CLOSED_RAISE_ON_DUPLICATE"
        in spec
    )
    assert "BOTH_PATHS_CAN_WRITE_EQUIVALENT_ACCOUNT_STATE=false" in spec
    assert "SAME_CANONICAL_ACCOUNT_STATE_DOUBLE_WRITTEN_IN_ONE_CYCLE=false" in spec
    assert "CASH_PARITY=DISTINCT_RESPONSIBILITY" in spec
    assert "REVERSAL_SEMANTICS_PARITY=DISTINCT_RESPONSIBILITY" in spec
    assert "IDEMPOTENCE_PARITY=DISTINCT_RESPONSIBILITY" in spec
    assert "ACCOUNT_STATE_PARITY=PASS" not in spec


def test_v1_host_accounting_call_path_is_cap31_not_idempotent_portfolio() -> None:
    host = DECISION_HOST.read_text(encoding="utf-8")
    port = PORT_MODULE.read_text(encoding="utf-8")
    assert "apply_intended_action_via_canonical_accounting_v1" in host
    assert "host_simulated_execution_port_v1" in host
    assert "ensure_accounting_session_v1" in host
    assert "IdempotentPortfolioV2" not in host
    assert "apply_intended_action_via_canonical_accounting_v1" in port
    tree = ast.parse(host)
    called = _called_names(tree)
    assert "apply_intended_action_via_canonical_accounting_v1" in called
    imported = _imported_modules(tree)
    assert all("idempotent_portfolio_v2" not in module for module in imported)


def test_hardening_v2_portfolio_call_path_is_idempotent_portfolio_not_cap31() -> None:
    source = HARDENING_MODULE.read_text(encoding="utf-8")
    assert "IdempotentPortfolioV2" in source
    assert "state.portfolio.apply_intended_action" in source
    assert "apply_intended_action_via_canonical_accounting_v1" not in source
    assert "ensure_accounting_session_v1" not in source
    imported = _imported_modules(ast.parse(source))
    assert all("productive_futures_accounting" not in module for module in imported)
    assert any("idempotent_portfolio_v2" in module for module in imported)


def test_accounting_layers_do_not_become_core_owners() -> None:
    for path in _ACCOUNTING_LAYERS:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        called = _called_names(tree)
        imported = _imported_modules(tree)
        assert not (called & _FORBIDDEN_OWNER_CALLS), path
        for root in _FORBIDDEN_OWNER_IMPORT_ROOTS:
            assert all(
                module != root and not module.startswith(f"{root}.") for module in imported
            ), path
        assert "build_canonical_order_intent_v1" not in source
        assert "evaluate_quantity_chain_v1" not in source
        assert "evaluate_offline_safety_kernel_boundary_v0" not in source


def test_mapper_enter_without_coi_cannot_buy_or_sell() -> None:
    mapper = MAPPER_MODULE.read_text(encoding="utf-8")
    assert "enter_without_canonical_order_intent" in mapper
    assert "NO_CANONICAL_ORDER_INTENT" in mapper
    assert "historical_exit_or_reduce" in mapper
    assert map_replay_result_to_intended_analytical_action_v1.__name__
    enter_hold_idx = mapper.index("enter_without_coi")
    buy_idx = mapper.index('intended_side="BUY"', enter_hold_idx)
    assert mapper.index('intended_side="HOLD"', enter_hold_idx) < buy_idx


def test_accounting_does_not_rewrite_exit_or_reduce_to_hold() -> None:
    for path in (CAP3_BRIDGE, IDEMPOTENT_PORTFOLIO, PAPER_SHADOW_MODEL):
        source = path.read_text(encoding="utf-8")
        assert "EXIT_TO_HOLD" not in source
        assert "convert historical EXIT" not in source


def test_owner_composed_flat_enter_hold_exit_and_reduce() -> None:
    session, portfolio, opened = _apply_cap31(
        side="BUY", quantity=_QTY, session_id="adj-a", cycle_index=1
    )
    assert opened.get("ok") is True
    assert opened.get("fill") is not None
    assert opened["fill"]["side"] == "BUY"
    assert session.position is not None
    assert session.position.qty == _QTY
    cap31_cash_after_open = portfolio.state.cash

    hardening = IdempotentPortfolioV2.from_params(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    h_open = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="BUY",
        quantity=_QTY,
        mark_price=_MARK,
        intent_id="adj-a-intent",
        fill_id="adj-a-fill",
    )
    assert h_open is not None
    h_qty = hardening.model.state.positions[_INSTRUMENT].quantity
    assert h_qty == _QTY
    assert hardening.model.state.cash != cap31_cash_after_open

    _, portfolio, held = _apply_cap31(
        side="HOLD",
        quantity=Decimal("0"),
        session_id="adj-c",
        cycle_index=2,
        session=session,
        portfolio=portfolio,
    )
    assert held.get("fill") is None
    assert session.position is not None
    h_hold = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="HOLD",
        quantity=Decimal("0"),
        mark_price=_MARK,
        intent_id="adj-c-intent",
    )
    assert h_hold is None

    half = Decimal("0.05")
    _, portfolio, reduced = _apply_cap31(
        side="SELL",
        quantity=half,
        session_id="adj-g",
        cycle_index=3,
        session=session,
        portfolio=portfolio,
    )
    assert reduced.get("ok") is True
    assert reduced.get("fill") is not None
    assert session.position is not None
    assert session.position.qty == _QTY - half
    h_reduce = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="SELL",
        quantity=half,
        mark_price=_MARK,
        intent_id="adj-g-intent",
        fill_id="adj-g-fill",
    )
    assert h_reduce is not None
    assert hardening.model.state.positions[_INSTRUMENT].quantity == _QTY - half

    _, portfolio, closed = _apply_cap31(
        side="SELL",
        quantity=half,
        session_id="adj-e",
        cycle_index=4,
        session=session,
        portfolio=portfolio,
    )
    assert closed.get("ok") is True
    assert session.position is None
    h_exit = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="SELL",
        quantity=half,
        mark_price=_MARK,
        intent_id="adj-e-intent",
        fill_id="adj-e-fill",
    )
    assert h_exit is not None
    assert hardening.model.state.positions[_INSTRUMENT].quantity == Decimal("0")


def test_owner_composed_short_enter_and_exit() -> None:
    session, portfolio, opened = _apply_cap31(
        side="SELL", quantity=_QTY, session_id="adj-b", cycle_index=1
    )
    assert opened.get("fill") is not None
    assert opened["fill"]["side"] == "SELL"
    assert session.position is not None
    assert session.position.side.value == "short"
    hardening = IdempotentPortfolioV2.from_params(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    h_open = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="SELL",
        quantity=_QTY,
        mark_price=_MARK,
        intent_id="adj-b-intent",
        fill_id="adj-b-fill",
    )
    assert h_open is not None
    assert hardening.model.state.positions[_INSTRUMENT].quantity == -_QTY
    _, _, closed = _apply_cap31(
        side="BUY",
        quantity=_QTY,
        session_id="adj-f",
        cycle_index=2,
        session=session,
        portfolio=portfolio,
    )
    assert closed.get("ok") is True
    assert session.position is None
    h_exit = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="BUY",
        quantity=_QTY,
        mark_price=_MARK,
        intent_id="adj-f-intent",
        fill_id="adj-f-fill",
    )
    assert h_exit is not None
    assert hardening.model.state.positions[_INSTRUMENT].quantity == Decimal("0")


def test_owner_composed_reversal_and_idempotence_are_distinct() -> None:
    session, portfolio, _ = _apply_cap31(
        side="BUY", quantity=_QTY, session_id="adj-h", cycle_index=1
    )
    with pytest.raises(RuntimeError, match="OVER_REDUCE|POSITION_FLIP"):
        _apply_cap31(
            side="SELL",
            quantity=_QTY + _QTY,
            session_id="adj-h",
            cycle_index=2,
            session=session,
            portfolio=portfolio,
        )
    hardening = IdempotentPortfolioV2.from_params(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="BUY",
        quantity=_QTY,
        mark_price=_MARK,
        intent_id="adj-h-open",
        fill_id="adj-h-open-fill",
    )
    flipped = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="SELL",
        quantity=_QTY + _QTY,
        mark_price=_MARK,
        intent_id="adj-h-flip",
        fill_id="adj-h-flip-fill",
    )
    assert flipped is not None
    assert hardening.model.state.positions[_INSTRUMENT].quantity == -_QTY

    session2, portfolio2, first = _apply_cap31(
        side="BUY", quantity=_QTY, session_id="adj-i", cycle_index=1
    )
    replayed = apply_intended_action_via_canonical_accounting_v1(
        session=session2,
        portfolio=portfolio2,
        instrument_id=_INSTRUMENT,
        side="BUY",
        quantity=_QTY,
        mark_price=_MARK,
        session_id="adj-i",
        cycle_index=1,
        persist=False,
    )
    assert first.get("fill") is not None
    fill_id = first["fill"]["fill_id"]
    assert session2.fill_order.count(fill_id) == 1
    assert replayed.get("ok") is True
    assert replayed.get("accounting", {}).get("idempotent_replay") is True
    assert session2.position is not None
    assert session2.position.qty == _QTY

    hardening_i = IdempotentPortfolioV2.from_params(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    hardening_i.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="BUY",
        quantity=_QTY,
        mark_price=_MARK,
        intent_id="adj-i-intent",
        fill_id="adj-i-fill",
    )
    with pytest.raises(IdempotencyErrorV2):
        hardening_i.apply_intended_action(
            instrument_id=_INSTRUMENT,
            side="BUY",
            quantity=_QTY,
            mark_price=_MARK,
            intent_id="adj-i-intent",
            fill_id="adj-i-fill",
        )


def test_hold_does_not_account_buy_or_sell() -> None:
    _, _, held = _apply_cap31(side="HOLD", quantity=_QTY, session_id="adj-o", cycle_index=1)
    assert held.get("fill") is None
    hardening = IdempotentPortfolioV2.from_params(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    h_hold = hardening.apply_intended_action(
        instrument_id=_INSTRUMENT,
        side="HOLD",
        quantity=_QTY,
        mark_price=_MARK,
        intent_id="adj-o-intent",
    )
    assert h_hold is None
    assert hardening.model.state.fill_count == 0


def test_prior_quarantines_remain_closed_and_historical_not_this_slice() -> None:
    remaining = REMAINING_P0_SPEC.read_text(encoding="utf-8")
    parallel = PARALLEL_OWNER_SPEC.read_text(encoding="utf-8")
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    assert "ACCOUNTING_PORTFOLIO_ALIGNMENT=NOT_THIS_SLICE" in remaining
    assert "ACCOUNTING_PORTFOLIO_ALIGNMENT=NOT_THIS_SLICE" in parallel
    assert "LEGACY_STRATEGY_POSITION_SIZERS_PRODUCTIVE_HOST_REACHABLE=false" in remaining
    assert "EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_OWNER=false" in parallel
    assert "COMPONENT_ADJUDICATION_PERFORMED=false" in parent
    assert (
        "test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py"
        in parent
    )


def test_master_and_map_of_truth_name_this_slice() -> None:
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    host_graph = HOST_GRAPH_SPEC.read_text(encoding="utf-8")
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md"
        in section
    )
    assert "PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "MODE_SPECIFIC_ANALYTICAL_HOST" in host_graph
    assert "DIRECT_PORTFOLIO_MUTATION_BYPASS_CLASS=MODE_SPECIFIC_VALID" in host_graph


def test_reused_preservation_guards_remain_present() -> None:
    for path in _REUSED_GUARDS:
        assert path.is_file(), path
    restore = _REUSED_GUARDS[0].read_text(encoding="utf-8")
    remaining = _REUSED_GUARDS[8].read_text(encoding="utf-8")
    cap31 = _REUSED_GUARDS[10].read_text(encoding="utf-8")
    hardening = _REUSED_GUARDS[11].read_text(encoding="utf-8")
    assert "crs < safety < intent" in restore
    assert "LEGACY_STRATEGY_POSITION_SIZERS_PRODUCTIVE_HOST_REACHABLE=false" in remaining
    assert "apply_intended_action_via_canonical_accounting_v1" in cap31
    assert "test_intent_and_fill_idempotency" in hardening
    assert AccountingEngineError is not None
