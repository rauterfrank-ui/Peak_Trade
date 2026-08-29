"""Post-restoration baseline preservation and compatibility contract v1.

Static/docs/source-order guards only. Reuses existing owner tests; does not
duplicate their runtime proofs. No runtime mutation. No live authority.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
C4_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/MV2_C4_POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1.md"
)
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
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
FORENSIC_PACKAGE = (
    REPO_ROOT
    / "forensics/historical_reference"
    / "sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"
)
AUTHORITY_NONE = FORENSIC_PACKAGE / "AUTHORITY_NONE.txt"
CHECKPOINT_SHA = "21452016ff998c1af63f24c36060f2a54020c0df"

_EXISTING_GUARDS = (
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py",
    REPO_ROOT / "tests/ops/test_master_v2_section_5_3_host_graph_ssot_adjudication_v1.py",
    REPO_ROOT / "tests/ops/test_master_v2_c4_named_master_ssot_pointer_v1.py",
    REPO_ROOT / "tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_master_v2_owner_composed_full_chain_host_consumption_proof_v1.py",
    REPO_ROOT
    / "tests/governance/test_historically_attested_current_system_semantic_restoration_authorization_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_parallel_owner_and_skip_safety_path_quarantine_v1.py",
    REPO_ROOT / "tests/ops/test_peak_trade_post_restoration_remaining_p0_quarantine_v1.py",
    REPO_ROOT
    / "tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py",
)

_FORBIDDEN_MAPPER_CALLS = frozenset(
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
_FORBIDDEN_MAPPER_IMPORT_ROOTS = (
    "src.governance.capital_risk_sizing_v1",
    "src.governance.canonical_order_intent_v1",
    "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0",
    "trading.master_v2.double_play_state",
    "trading.master_v2.double_play_entry_exit_policy_v0",
)

_COMPATIBILITY_DIMENSIONS = (
    "HISTORICAL_SEMANTIC_COMPATIBILITY",
    "AUTHORITY_COMPATIBILITY",
    "OWNER_COMPATIBILITY",
    "CALL_ORDER_COMPATIBILITY",
    "SAFETY_COMPATIBILITY",
    "INTENT_COMPATIBILITY",
    "EXIT_PRECEDENCE_COMPATIBILITY",
    "STATE_WRITER_COMPATIBILITY",
    "RISK_SIZING_COMPATIBILITY",
    "FAIL_CLOSED_COMPATIBILITY",
    "SIMULATED_EXECUTION_BOUNDARY_COMPATIBILITY",
    "FORENSIC_AUTHORITY_COMPATIBILITY",
    "LIVE_TRADING_AUTHORITY_COMPATIBILITY",
)
_COMPATIBILITY_OUTCOMES = (
    "COMPATIBLE",
    "COMPATIBLE_WITH_CONSTRAINTS",
    "INCOMPATIBLE",
    "UNKNOWN_INSUFFICIENT_EVIDENCE",
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
    assert "CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md" in spec
    assert "PARALLEL_SSOT_CREATED=false" in spec
    assert "RUNTIME_MUTATION=false" in spec
    assert "NEW_RUNTIME_OWNER=false" in spec
    assert "NEW_STAGE=false" in spec
    assert "COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true" in spec
    assert "COMPATIBILITY_CONTRACT_GRANTS_EXECUTION_AUTHORITY=false" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    assert "NO_EXECUTION_AUTHORITY=true" in spec
    assert "COMPONENT_ADJUDICATION_PERFORMED=false" in spec


def test_restoration_checkpoint_is_historical_not_eternal_main_pin() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert f"RESTORATION_COMPLETION_CHECKPOINT_SHA={CHECKPOINT_SHA}" in text
        assert "RESTORED_BASELINE_MUST_NOT_REGRESS=true" in text
        assert "MAIN_MUST_FOREVER_EQUAL_CHECKPOINT_SHA=false" in text
        assert "HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE" in text
        assert "CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true" in text
        assert "HISTORICAL_CORE_SEMANTICS_MUST_NOT_BE_REWRITTEN=true" in text
        assert "NO_CURRENT_FIRST_ARCHITECTURE=true" in text
    assert "MAIN_MUST_FOREVER_EQUAL_CHECKPOINT_SHA=true" not in spec
    assert "MAIN_MUST_FOREVER_EQUAL_CHECKPOINT_SHA=true" not in section


def test_restoration_claim_precision_forbids_overclaim() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert (
        "ALL_HISTORICALLY_ATTESTED_MASTER_V2_DOUBLE_PLAY_MATERIAL_AVAILABLE_IN_THE_PRESERVED_RECOVERY_CORPUS_HAS_BEEN_ADJUDICATED_FOR_RESTORATION_RELEVANCE=true"
        in spec
    )
    assert "ALL_HISTORICALLY_REQUIRED_CORE_RUNTIME_SEMANTICS_RESTORED=true" in spec
    assert "ALL_HISTORICALLY_REQUIRED_CORE_PROOF_OBLIGATIONS_CLOSED=true" in spec
    assert "ALL_HISTORICALLY_REQUIRED_CORE_DOC_OBLIGATIONS_CLOSED=true" in spec
    assert "KNOWN_NON_BLOCKING_FORENSIC_AMBIGUITIES_REMAIN_ARCHIVAL=true" in spec
    assert "EVERYTHING_THAT_EVER_EXISTED_WAS_RECOVERED=false" in spec
    assert "EVERYTHING_THAT_EVER_EXISTED_WAS_RECOVERED=true" not in spec
    assert "RESTORATION_CLAIM_PRECISION_STATUS=BOUNDED_NO_OVERCLAIM" in spec
    assert "MASTER_V2_DOUBLE_PLAY_RESTORATION_COMPLETE=true" in spec


def test_checkpoint_attests_restored_core_and_host_graph_status() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "ACTIVE_PATH_CORE_CHAIN_STATUS=RESTORED" in spec
    assert "FULL_CHAIN_HISTORICAL_CONTINUITY_STATUS=PROVEN" in spec
    assert "APPENDIX_A_CORE_LOGIC_PARITY_POST_6135_STATUS=PASS" in spec
    assert "HARDENING_V2_SAFETY_SEAM_STATUS=RESTORED_TO_HISTORICAL_BASELINE" in spec
    assert "HOST_GRAPH_SSOT_STATUS=CORRECTED" in spec
    assert "O051_POST_STATUS=DOC_CLOSED" in spec
    assert "FULL_CHAIN_GOLDEN_VECTOR_STRATEGY=OWNER_COMPOSED" in spec
    assert "GOLDEN_VECTOR_CORPUS_STATUS=ABSENT" in spec
    assert "TESTS_PROVE_IMPLEMENTATION_CONSISTENCY=true" in spec
    assert "TESTS_DEFINE_HISTORICAL_TRUTH=false" in spec


def test_compatibility_contract_dimensions_outcomes_and_required_output() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    for dimension in _COMPATIBILITY_DIMENSIONS:
        assert dimension in spec
        assert f"{dimension}=" in spec
    for outcome in _COMPATIBILITY_OUTCOMES:
        assert outcome in spec
    assert "COMPATIBILITY_OUTCOMES_SUPPORTED=" in spec
    assert "OVERALL_COMPATIBILITY=" in spec
    assert "KEEP_AS_IS=" in spec
    assert "ADAPT_DOWNSTREAM=" in spec
    assert "DECOUPLE=" in spec
    assert "DEGRADE=" in spec
    assert "REMOVE=" in spec
    assert "REWIRE=" in spec
    assert "CORE_MUTATION_REQUIRED=" in spec
    assert "NEW_OWNER_REQUIRED=" in spec
    assert "NEW_POLICY_REQUIRED=" in spec
    assert "EVIDENCE_GAPS=" in spec
    assert "PROPOSED_SAFE_ACTION=" in spec


def test_owner_and_ordering_invariants_are_normative_in_spec_and_master() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    for text in (spec, section):
        assert "SECOND_COMPUTE_OWNER_EXISTS=false" in text
        assert "SECOND_RISK_OWNER_EXISTS=false" in text
        assert "SECOND_SAFETY_OWNER_EXISTS=false" in text
        assert "SECOND_INTENT_OWNER_EXISTS=false" in text
        assert "C4_NEW_OWNER=false" in text
        assert "C4_NEW_STAGE=false" in text
    assert "STEP_29P_BEFORE_SAFETY=true" in spec
    assert "SAFETY_BEFORE_STEP_29Q=true" in spec
    assert "NO_29Q_BEFORE_SAFETY=true" in spec
    assert "29P_CALL_COUNT_PER_REPLAY=1" in spec
    assert "SAFETY_CALL_COUNT_PER_REPLAY=1" in spec
    assert "29Q_CALL_COUNT_MAX_PER_REPLAY=1" in spec
    assert "ENTER_HARD_BLOCK_SKIPS_ENTER_29Q=true" in spec
    assert "ENTER_HARD_BLOCK_PRODUCES_NO_ENTER_COI=true" in spec
    assert "EXIT_PRECEDENCE_PRESERVED=true" in spec
    assert "PLAN_ONLY_BOUNDARY_PRESERVED=true" in spec
    assert "SAFETY_DOES_NOT_GRANT_EXECUTION_PERMISSION=true" in spec
    assert "NO_GENERIC_POST_MAPPER_EXIT_TO_HOLD=true" in spec
    assert "ENTER_WITHOUT_CANONICAL_ORDER_INTENT_CANNOT_BUY_OR_SELL=true" in spec
    assert "CAP65_EXIT_PRODUCERS_REMAIN_CONSUMED=true" in spec
    assert "INTENDED_ACTION_MAPPER_COMPUTE_OWNER=false" in spec
    assert "INTENDED_ACTION_MAPPER_RISK_OWNER=false" in spec
    assert "INTENDED_ACTION_MAPPER_SAFETY_OWNER=false" in spec
    assert "INTENDED_ACTION_MAPPER_INTENT_OWNER=false" in spec


def test_existing_preservation_guards_remain_present() -> None:
    restore = _EXISTING_GUARDS[0].read_text(encoding="utf-8")
    appendix = _EXISTING_GUARDS[1].read_text(encoding="utf-8")
    host_graph = _EXISTING_GUARDS[2].read_text(encoding="utf-8")
    c4 = _EXISTING_GUARDS[3].read_text(encoding="utf-8")
    hardening = _EXISTING_GUARDS[4].read_text(encoding="utf-8")
    full_chain = _EXISTING_GUARDS[5].read_text(encoding="utf-8")
    restoration_auth = _EXISTING_GUARDS[6].read_text(encoding="utf-8")
    parallel_owner = _EXISTING_GUARDS[7].read_text(encoding="utf-8")
    for path in _EXISTING_GUARDS:
        assert path.is_file(), path
    assert "crs < safety < intent" in restore
    assert 'order == ["29P", "SAFETY", "29Q", "RECON", "KS"]' in restore
    assert "GOLDEN_VECTOR" in appendix or "owner-composed" in appendix.lower()
    assert "POST_REPLAY_EVIDENCE_OR_CONSUMPTION_STAGE_LABEL_ONLY" in host_graph
    assert "C4_NEW_OWNER=false" in c4
    assert "enter_without_canonical_order_intent" in hardening
    assert "historical_exit_or_reduce_host_action_v2" in hardening
    assert "OWNER_COMPOSED" in full_chain or "owner-composed" in full_chain
    remaining_p0 = _EXISTING_GUARDS[8].read_text(encoding="utf-8")
    accounting_align = _EXISTING_GUARDS[9].read_text(encoding="utf-8")
    assert 'historical_reference_authority"] == "NONE"' in restoration_auth
    assert "EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_OWNER=false" in parallel_owner
    assert "LEGACY_STRATEGY_POSITION_SIZERS_PRODUCTIVE_HOST_REACHABLE=false" in remaining_p0
    assert "ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES" in accounting_align


def test_replay_source_keeps_29p_before_safety_before_29q() -> None:
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    crs = source.index("bind_capital_risk_sizing_offline_replay_evidence_v0(")
    safety = source.index("bind_safety_kernel_offline_replay_evidence_v0(")
    intent = source.index("bind_canonical_order_intent_offline_replay_evidence_v0(")
    recon = source.index("bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(")
    ks = source.index("bind_killswitch_boundary_offline_replay_evidence_v0(")
    assert crs < safety < intent < recon < ks
    assert source.count("bind_capital_risk_sizing_offline_replay_evidence_v0(") == 1
    assert source.count("bind_safety_kernel_offline_replay_evidence_v0(") == 1
    assert source.count("bind_canonical_order_intent_offline_replay_evidence_v0(") == 1


def test_mapper_remains_downstream_translator_not_owner() -> None:
    source = MAPPER_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = _called_names(tree)
    imported = _imported_modules(tree)
    assert not (called & _FORBIDDEN_MAPPER_CALLS)
    for root in _FORBIDDEN_MAPPER_IMPORT_ROOTS:
        assert all(not module == root and not module.startswith(f"{root}.") for module in imported)
    assert "enter_without_canonical_order_intent" in source
    assert "historical_exit_or_reduce" in source
    assert "EXIT" in source and "REDUCE" in source


def test_hardening_does_not_become_second_safety_or_intent_owner() -> None:
    source = HARDENING_MODULE.read_text(encoding="utf-8")
    assert "evaluate_offline_safety_kernel_boundary_v0" not in source
    assert "bind_canonical_order_intent_offline_replay_evidence_v0" not in source
    assert "evaluate_host_exit_policy_producers_v1" in source
    assert "evaluate_bridge_safety_v2(" not in source


def test_c4_remains_existing_binding_not_new_owner() -> None:
    assert C4_SPEC.is_file()
    spec = C4_SPEC.read_text(encoding="utf-8")
    assert "PRIMARY_OWNER=integrated_offline_trading_logic_replay_v1" in spec
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert "POST_REPLAY_EVIDENCE_OR_CONSUMPTION_STAGE_LABEL_ONLY" in section
    assert "POST_REPLAY_RISK_OWNER_REINVOKED=false" in section
    assert "POST_REPLAY_SAFETY_OWNER_REINVOKED=false" in section
    assert "POST_REPLAY_INTENT_OWNER_REINVOKED=false" in section


def test_forensic_reference_authority_remains_none() -> None:
    assert FORENSIC_PACKAGE.is_dir()
    assert AUTHORITY_NONE.is_file()
    authority = AUTHORITY_NONE.read_text(encoding="utf-8")
    assert "AUTHORITY=NONE" in authority
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "FORENSIC_REFERENCE_AUTHORITY=NONE" in spec
    assert "MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY" in spec
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "O046_GATE_3_MATRIX_CANONICALIZED=false" in spec
    assert "UQ1_UQ8_IDS_CANONICALIZED=false" in spec
    assert "O059_UNRESOLVED_TOKEN_ALIASES_CANONICALIZED=false" in spec
    assert "FORENSIC_REFERENCE_AUTHORITY=CANONICAL" not in spec
    assert "GATE_3_CANONICALIZED=false" in spec


def test_master_names_subordinate_preservation_spec() -> None:
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    assert (
        "SPEC=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md"
        in section
    )
    assert "POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1" in section
    assert SPEC_PATH.is_file()
