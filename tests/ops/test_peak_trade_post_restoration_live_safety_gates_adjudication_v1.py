"""Post-restoration live safety gates adjudication v1.

Static/docs/source-order guards. Reuses existing owner tests; does not
duplicate their runtime proofs. Does not repair the preexisting Cap 3.1
CALL_GRAPH tuple equality test. No core runtime mutation. No live authority.
No venue-pretrade adjudication.
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.execution.networked.canary_live_gate_v1 import evaluate_canary_live_gate_v1
from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.constants_v1 import (
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
)
from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    CANARY_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENABLE_LIVE_TRADING,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT,
    LIVE_ENABLED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    ABSENT_TARGET_ROW_IS_NOT_ZERO,
    EMPTY_DATA_IS_NOT_ZERO,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.activation_gate_v1 import (
    validate_no_order_mode_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md"
)
PARENT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
)
SIM_EXEC_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md"
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
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
PORT_MODULE = (
    REPO_ROOT
    / "src/ops/single_future_stateful_no_order_runtime_activation_v1"
    / "simulated_execution_port_v1.py"
)
DECISION_HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
SAFETY_GUARD = REPO_ROOT / "src/live/safety.py"
SUBMIT_GATES = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_gates_v1.py"
)
TRANSPORT_GATE = REPO_ROOT / "src/execution/networked/transport_gate_v1.py"
CONFIG_TOML = REPO_ROOT / "config/config.toml"
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
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_simulated_execution_pipeline_adjudication_v1.py",
    REPO_ROOT / "tests/ops/test_section_11_13_5_z2cm_position_state_predicate_contract_v1.py",
    REPO_ROOT / "tests/ops/test_capability_11_9_live_canary_order_execution_v1.py",
)

_FORBIDDEN_LIVE_SUBMIT_IMPORTS = (
    "src.live.safety",
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1",
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1",
)
_FORBIDDEN_PAPER_IMPORT_ROOTS = (
    "src.execution.paper.engine",
    "src.execution.paper.broker",
    "execution.paper.engine",
    "execution.paper.broker",
)
_SEE_ALSO = (
    "SEE_ALSO_LIVE_SAFETY_GATES_ADJUDICATION="
    "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md"
)


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


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
    assert "RESTORATION_REOPEN_REQUIRED=false" in spec
    assert "COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true" in spec
    assert "NO_LIVE_AUTHORITY=true" in spec
    assert "NO_EXECUTION_AUTHORITY=true" in spec
    assert "CHANGED_RUNTIME_FILES=NONE" in spec
    assert "FORENSIC_REFERENCE_AUTHORITY=NONE" in spec
    assert "MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY" in spec


def test_master_pointer_and_adjudication_result() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "LIVE_SAFETY_GATES_COMPLETE=true" in text
        assert "SECOND_CORE_SAFETY_OWNER_EXISTS=false" in text
        assert "BYPASS_PATH_CONFLICT=false" in text
        assert "RUNTIME_ALIGNMENT_REQUIRED=false" in text
        assert "RESTORATION_REOPEN_REQUIRED=false" in text
        assert "VENUE_PRETRADE_WORK_REMAINS=true" in text
        assert "NEXT_DISTINCT_SURFACE=VENUE_PRETRADE_LIMIT_GATES" in text
        assert (
            "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_LIVE_SAFETY_RESPONSIBILITIES" in text
            or "LIVE_SAFETY_GATES_ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_LIVE_SAFETY_RESPONSIBILITIES"
            in text
        )
    assert "LIVE_SAFETY_GATES_ADJUDICATION_V1=true" in section
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md"
        in section
    )
    assert "LIVE_SAFETY_GATE_COUNT=18" in spec
    assert (
        "LIVE_GATE_OWNER_MODEL=DISTINCT_NON_OVERLAPPING_HOST_FAMILY_ADMISSION_GATES_NOT_A_SECOND_CORE_SAFETY_OWNER"
        in spec
    )
    assert "SECOND_LIVE_SAFETY_OWNER_EXISTS=false" in spec
    assert "EARLIEST_INCOMPLETE_LIVE_SAFETY_EDGE=NONE" in spec
    assert "ADJUDICATION_RESULT=DUPLICATE_LIVE_SAFETY_OWNER_CONFLICT" not in spec
    assert "ADJUDICATION_RESULT=LIVE_SAFETY_BYPASS_CONFLICT" not in spec


def test_core_safety_remains_replay_and_live_admission_is_not_replay() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    remaining = REMAINING_P0_SPEC.read_text(encoding="utf-8")
    assert (
        "CORE_REPLAY_SAFETY_ROLE=SOLE_CORE_SAFETY_OWNER_FOR_MASTER_V2_DOUBLE_PLAY_REPLAY_SEQUENCE"
        in spec
    )
    assert "LIVE_ADMISSION_IS_NOT_REPLAY_SAFETY=true" in spec
    assert "LIVE_ADMISSION_ROLE=DOWNSTREAM_HOST_FAMILY_ADMISSION_NOT_CORE_REPLAY_SAFETY" in spec
    assert "SAFETY_OWNER=trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0" in spec
    assert "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REPLAY_SAFETY_OWNER=false" in remaining
    assert "NO_29Q_BEFORE_SAFETY=true" in spec
    assert "NO_29Q_BEFORE_SAFETY=true" in section
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    crs = source.index("bind_capital_risk_sizing_offline_replay_evidence_v0(")
    safety = source.index("bind_safety_kernel_offline_replay_evidence_v0(")
    intent = source.index("bind_canonical_order_intent_offline_replay_evidence_v0(")
    assert crs < safety < intent
    assert "independent_pre_trade_safety" not in source
    assert "ensure_may_place_order" not in source
    assert "evaluate_canary_submit_gates_v1" not in source


def test_authorization_non_equivalence_remains_fail_closed() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "LIVE_AUTHORIZED=false" in text
        assert "TESTNET_AUTHORIZED=false" in text
        assert "CANARY_AUTHORIZED=false" in text
        assert "LIVE_ENABLED=false" in text
        assert "LIVE_ARMED=false" in text
        assert "LIVE_READINESS=EVALUATED_NOT_READY" in text
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert ENABLE_LIVE_TRADING is False
    assert FULLY_AUTONOMOUS_LIVE_TRADING_READY is False
    assert "READINESS_IS_NOT_AUTHORIZATION=true" in spec
    assert "CREDENTIAL_PRESENCE_IS_NOT_AUTHORIZATION=true" in spec
    assert "ENABLED_IS_NOT_AUTHORIZED=true" in spec
    assert "ARMED_IS_NOT_AUTHORIZED=true" in spec
    assert "CYBERSECURITY_PASS_IS_NOT_LIVE_AUTHORIZATION=true" in spec
    assert "PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_ENABLED=true" in spec
    assert "enable_live_trading = false" in CONFIG_TOML.read_text(encoding="utf-8")


def test_host_family_admission_roles_remain_distinct() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    submit_gates = SUBMIT_GATES.read_text(encoding="utf-8")
    safety_guard = SAFETY_GUARD.read_text(encoding="utf-8")
    transport = TRANSPORT_GATE.read_text(encoding="utf-8")
    assert "OKX_CANARY_ADMISSION_ROLE=evaluate_canary_submit_gates_v1" in spec
    assert "PIPELINE_KRAKEN_ADMISSION_ROLE=SafetyGuard.ensure_may_place_order" in spec
    assert "NETWORKED_ONRAMP_ROLE=guard_transport_gate_v1 + evaluate_canary_live_gate_v1" in spec
    assert "NO_ORDER_HOST_BARRIER_ROLE=validate_no_order_mode_v1" in spec
    assert "def evaluate_canary_submit_gates_v1(" in submit_gates
    assert "class SafetyGuard" in safety_guard
    assert "def ensure_may_place_order(" in safety_guard
    assert "class LiveNotImplementedError" in safety_guard
    assert "guard_transport_gate_v1" in transport
    assert "evaluate_canary_live_gate_v1_from_environ" in transport
    denied = evaluate_canary_live_gate_v1(
        dry_run=True,
        mode="shadow",
        external_approval_ref="LB-APR-001",
    )
    assert denied.outbound_live_or_canary_allowed is False
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=None,
        owner_go_consumed=False,
        authorization_scope=None,
        bound_origin_main_sha=None,
        expected_origin_main_sha=None,
        live_canary_authorized=False,
        live_enabled=False,
        live_armed=False,
        confirm_token=None,
        blocks_new_entry=False,
        unresolved_economic_divergence=False,
        live_reconciliation_proven=True,
        permission_attestation=None,
        environment=None,
        fixture_or_demo_or_testnet=False,
        max_notional=None,
        min_executable_notional=None,
        order_count=1,
        position_count=0,
        exposure_above_minimum_bound=False,
    )
    assert evaluation.submit_allowed is False
    blockers = validate_no_order_mode_v1()
    assert "NO_ORDER_MODE_VIOLATION" not in blockers
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert "CAP11_LIVE_TESTNET_FIXTURE_PORTS_ROLE=DECLARED_UNREACHABLE_CONTRACTS_ONLY" in spec
    assert "MULTIPLE_HOST_ADMISSION_GATES_DO_NOT_IMPLY_DUPLICATE_CORE_SAFETY_OWNER=true" in spec


def test_simulated_execution_has_no_productive_live_submit_edge() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    port = PORT_MODULE.read_text(encoding="utf-8")
    host = DECISION_HOST.read_text(encoding="utf-8")
    imported_port = _imported_modules(ast.parse(port))
    imported_host = _imported_modules(ast.parse(host))
    assert "RESTORED_NO_ORDER_TO_LIVE_SUBMIT=DECLARED_UNREACHABLE" in spec
    assert "SIMULATED_EXECUTION_IS_NOT_LIVE_PERMISSION=true" in spec
    for module in imported_port | imported_host:
        assert module not in _FORBIDDEN_LIVE_SUBMIT_IMPORTS
        assert all(not module.startswith(f"{root}.") for root in _FORBIDDEN_LIVE_SUBMIT_IMPORTS)
        assert module not in _FORBIDDEN_PAPER_IMPORT_ROOTS
        assert all(not module.startswith(f"{root}.") for root in _FORBIDDEN_PAPER_IMPORT_ROOTS)
    assert "PaperExecutionEngine" not in host
    assert "PaperBroker" not in host
    assert "PAPER_EXECUTION_ENGINE_IS_NOT_LIVE_SUBMIT_PATH=true" in spec


def test_flatten_is_separate_emergency_authority_not_live_admission() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token=None,
        purpose=None,
        owner_go=None,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_TOKEN_MISSING" in reasons
    assert "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE" in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert "FLATTEN_ROLE=SEPARATE_EMERGENCY_AUTHORITY_NOT_LIVE_ADMISSION_OWNER" in spec
    assert "FLATTEN_IS_NOT_LIVE_ADMISSION_OWNER=true" in spec
    assert "FLATTEN=NOT_THIS_SLICE" in spec


def test_empty_is_not_zero_and_venue_boundary_remain_open() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert EMPTY_DATA_IS_NOT_ZERO is True
    assert ABSENT_TARGET_ROW_IS_NOT_ZERO is True
    assert "POSITION_ABSENCE_IS_NOT_ZERO=true" in spec
    assert "EMPTY_DATA_IS_NOT_ZERO=true" in spec
    assert "ABSENT_TARGET_ROW_IS_NOT_ZERO=true" in spec
    assert (
        "LIVE_SAFETY_TO_VENUE_PRETRADE_BOUNDARY=AFTER_HOST_ADMISSION_AUTH_ARM_ELIG_ENV_CONFIRM_CYBER_CREDENTIAL_CLASS_INSTRUMENT_BIND_OPEN_STATE_BEFORE_VENUE_NATIVE_SIZE_PRICE_LEVERAGE_POSMODE_MARGIN_MAXAVAIL_LOT_TICK"
        in spec
    )
    assert "VENUE_PRETRADE_WORK_REMAINS=true" in spec
    assert "VENUE_PRETRADE_WORK_REMAINS=true" in section
    assert "VENUE_PRETRADE_ADJUDICATION_IN_SCOPE=false" in spec
    assert "VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE" in spec
    assert (
        "VENUE_NATIVE_SIZE_PRICE_LEVERAGE_POSMODE_MARGIN_MAXAVAIL_LOT_TICK=NEXT_NAMED_SURFACE"
        in spec
    )
    assert "VENUE_PRETRADE_COMPLETE=true" not in spec
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=true" not in spec


def test_closed_owner_graph_and_prior_slices_remain() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    accounting = ACCOUNTING_SPEC.read_text(encoding="utf-8")
    sim_exec = SIM_EXEC_SPEC.read_text(encoding="utf-8")
    remaining = REMAINING_P0_SPEC.read_text(encoding="utf-8")
    parallel = PARALLEL_OWNER_SPEC.read_text(encoding="utf-8")
    parent = PARENT_SPEC.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    for text in (spec, section):
        assert "SECOND_COMPUTE_OWNER_EXISTS=false" in text
        assert "SECOND_RISK_OWNER_EXISTS=false" in text
        assert "SECOND_SAFETY_OWNER_EXISTS=false" in text
        assert "SECOND_INTENT_OWNER_EXISTS=false" in text
        assert "SECOND_EXECUTION_OWNER_EXISTS=false" in text
    assert "CLOSED_OWNER_GRAPH_PRESERVED=true" in spec
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES" in accounting
    assert "SIMULATED_EXECUTION_PIPELINE_COMPLETE=true" in sim_exec
    assert "SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1=true" in section
    assert "ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1=true" in section
    assert "LIVE_SAFETY_GATES=NOT_THIS_SLICE" in remaining
    assert "LIVE_SAFETY_GATES=NOT_THIS_SLICE" in parallel
    assert "LIVE_SAFETY_GATES=NOT_THIS_SLICE" in accounting
    assert "LIVE_SAFETY_GATES=NOT_THIS_SLICE" in sim_exec
    assert _SEE_ALSO in remaining
    assert _SEE_ALSO in parallel
    assert _SEE_ALSO in accounting
    assert _SEE_ALSO in sim_exec
    assert "LIVE_SAFETY_GATES_ADJUDICATION_PRESERVED=true" in parent
    assert "SECOND_CORE_SAFETY_OWNER_PROHIBITED=true" in parent
    assert "LIVE_SAFETY_RUNTIME_REWIRE_REQUIRED=false" in parent
    assert "LIVE_AUTHORITY_REMAINS_FALSE=true" in parent
    assert "VENUE_PRETRADE_REMAINS_SEPARATE=true" in parent
    assert "PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot


def test_preexisting_call_graph_drift_remains_label_only_and_unrepaired() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    preexisting = PREEXISTING_CALL_GRAPH_TEST.read_text(encoding="utf-8")
    assert "PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false" in spec
    assert "PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY" in section
    assert "assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH" in preexisting
    assert "xfail" not in preexisting.lower()
    assert "pytest.skip" not in preexisting


def test_reused_preservation_guards_remain_present() -> None:
    for path in _REUSED_GUARDS:
        assert path.is_file(), path
    restore = _REUSED_GUARDS[0].read_text(encoding="utf-8")
    sim_exec = _REUSED_GUARDS[11].read_text(encoding="utf-8")
    empty = _REUSED_GUARDS[12].read_text(encoding="utf-8")
    cap11 = _REUSED_GUARDS[13].read_text(encoding="utf-8")
    assert "crs < safety < intent" in restore
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_EXECUTION_RESPONSIBILITIES" in sim_exec
    assert "test_empty_data_array_is_not_observed_not_zero" in empty
    assert "LIVE_EXECUTION_REACHABLE" in cap11
