"""Static contract: INV-016 durable completion canonical binding registry (Package F F1).

Contract-only binding slice. Binds the testnet completion path wiring owner into the
durable completion canonical registry using the Package-E dedicated-testowner pattern
(mirror PE-22 / E1; not the B2 dual-testowner path).

Non-authorizing. No runtime, network, testnet execution, or production mutation.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal, TypedDict

import pytest

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    MASTER_V2_BINDING_TO_COMPLETION_CHAIN_FIELD_NAMES,
    default_minimal_completion_integration_input,
)
from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_LAYER_VERSION,
    BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER,
    CANONICAL_TESTNET_COMPLETION_OWNER,
    PACKAGE_MARKER as INV016_WIRING_PACKAGE_MARKER,
    TestnetCompletionPathMarketInputV0,
    build_replay_input_from_testnet_market_input,
    evaluate_bounded_master_v2_testnet_completion_path_wiring,
    verify_dashboard_display_projection_digest_wiring,
    verify_replay_proof_classification_wiring,
)
from src.ops.offline_master_v2_replay_six_node_validation_graph_binding_v0 import (
    build_completion_integration_input_from_offline_replay_result,
    prove_offline_replay_six_node_validation_graph_binding_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from src.ops.durable_completion_validation.graph import (
    PROOF_BINDING_VALIDATION_GRAPH,
    PROOF_BINDING_VALIDATION_ORDER,
    VALIDATOR_COMPLETION_CHAIN,
    VALIDATOR_EVENT_STREAM,
)
from src.ops.durable_completion_validation.models import ValidationContext
from src.ops.durable_completion_validation.validators.completion_chain import (
    validate_completion_proof_chain_binding,
)
from src.ops.offline_master_v2_replay_six_node_validation_graph_binding_v0 import (
    PROOF_CLASSIFICATION_FULL_E2E_BOUND,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

INV016_DURABLE_COMPLETION_BINDING_PACKAGE_MARKER = (
    "INV016_DURABLE_COMPLETION_CANONICAL_BINDING_CONTRACT_V0=true"
)
F1_CONTRACT_ONLY_COMPLETE_MARKER = "F1_CONTRACT_ONLY_COMPLETE=true"
PACKAGE_F_COMPLETE_MARKER = "PACKAGE_F_COMPLETE=false"
F2_COMPLETE_MARKER = "F2_COMPLETE=false"
INV005_RUNTIME_PARKED_MARKER = "INV005_RUNTIME_PARKED=true"
RUNTIME_GO_READY_MARKER = "RUNTIME_GO_READY=false"
INTENT_9_BLOCKS_RUNTIME_ONLY_MARKER = "INTENT_9_BLOCKS_RUNTIME_ONLY=true"
RUNTIME_PROVEN_MARKER = "RUNTIME_PROVEN=false"

INV016_MODULE = REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py"
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
)
INV016_CANONICAL_OWNER_PATH = str(INV016_MODULE.relative_to(REPO_ROOT))
DURABLE_COMPLETION_CANONICAL_OWNER_PATH = str(INTEGRATION_MODULE.relative_to(REPO_ROOT))
DURABLE_COMPLETION_VALIDATION_GRAPH_PATH = "src/ops/durable_completion_validation/graph.py"
DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH = (
    "src/ops/durable_completion_validation/validators/completion_chain.py"
)

BindingLayer = Literal[
    "INV016_UPSTREAM_CANONICAL",
    "PE42_COMPLETION_FACADE",
    "DURABLE_COMPLETION_VALIDATION_GRAPH",
]


class Inv016DurableCompletionBindingRecord(TypedDict):
    binding_id: str
    layer: BindingLayer
    owner_path: str
    downstream_path: str
    digest_fields: tuple[str, ...]
    authority_lift: bool
    operative_testnet_execution_executed: bool
    operative_network_access_executed: bool
    repair_authority: bool
    trading_authority: bool
    promotion_authority: bool
    reverse_authority_forbidden: bool


INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY: tuple[
    Inv016DurableCompletionBindingRecord, ...
] = (
    {
        "binding_id": "inv016_upstream_canonical",
        "layer": "INV016_UPSTREAM_CANONICAL",
        "owner_path": INV016_CANONICAL_OWNER_PATH,
        "downstream_path": DURABLE_COMPLETION_CANONICAL_OWNER_PATH,
        "digest_fields": (
            "canonical_testnet_completion_owner",
            "dashboard_display_projection_digest",
            "replay_proof_classification",
        ),
        "authority_lift": False,
        "operative_testnet_execution_executed": False,
        "operative_network_access_executed": False,
        "repair_authority": False,
        "trading_authority": False,
        "promotion_authority": False,
        "reverse_authority_forbidden": True,
    },
    {
        "binding_id": "pe42_completion_facade",
        "layer": "PE42_COMPLETION_FACADE",
        "owner_path": DURABLE_COMPLETION_CANONICAL_OWNER_PATH,
        "downstream_path": DURABLE_COMPLETION_VALIDATION_GRAPH_PATH,
        "digest_fields": ("completion_referenced_dashboard_display_projection_digest",),
        "authority_lift": False,
        "operative_testnet_execution_executed": False,
        "operative_network_access_executed": False,
        "repair_authority": False,
        "trading_authority": False,
        "promotion_authority": False,
        "reverse_authority_forbidden": True,
    },
    {
        "binding_id": "durable_completion_validation_graph",
        "layer": "DURABLE_COMPLETION_VALIDATION_GRAPH",
        "owner_path": DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH,
        "downstream_path": DURABLE_COMPLETION_VALIDATION_GRAPH_PATH,
        "digest_fields": ("completion_referenced_dashboard_display_projection_digest",),
        "authority_lift": False,
        "operative_testnet_execution_executed": False,
        "operative_network_access_executed": False,
        "repair_authority": False,
        "trading_authority": False,
        "promotion_authority": False,
        "reverse_authority_forbidden": True,
    },
)

INV016_DURABLE_COMPLETION_DEPENDENCY_DIRECTION: tuple[str, ...] = (
    "offline_master_v2_replay",
    "offline_replay_six_node_validation_graph_binding",
    "inv016_completion_path_wiring",
    "pe42_durable_completion_facade",
    "durable_completion_validation_graph",
)

_COMPLETION_FACADE_CANONICAL_IMPORT_MODULE: Final[str] = (
    "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0"
)
_FORBIDDEN_PARALLEL_INV016_BINDING_SOURCES: Final[frozenset[str]] = frozenset(
    {
        "scripts.ops.run_testnet_bounded_observation_adapter_v0",
        "src.execution.order_router",
        "src.risk.live_killswitch",
    }
)


def _imported_modules_from_source(source_path: Path) -> frozenset[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return frozenset(modules)


@lru_cache(maxsize=1)
def _cached_default_minimal_completion_integration_input():
    return default_minimal_completion_integration_input()


def _valid_market_input() -> TestnetCompletionPathMarketInputV0:
    return TestnetCompletionPathMarketInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        source_run_id="inv016-durable-completion-binding",
    )


def _offline_replay_bundle():
    market_input = _valid_market_input()
    replay_input = build_replay_input_from_testnet_market_input(market_input)
    replay_result = run_offline_double_play_scenario_replay_v0(replay_input)
    six_node_binding = prove_offline_replay_six_node_validation_graph_binding_v0(replay_input)
    integration_input = build_completion_integration_input_from_offline_replay_result(replay_result)
    return replay_result, six_node_binding, integration_input


def _replace_completion_proof_chain(integration_input, **overrides):
    chain = replace(integration_input.completion_proof_chain, **overrides)
    return replace(integration_input, completion_proof_chain=chain)


def test_inv016_durable_completion_binding_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert INV016_DURABLE_COMPLETION_BINDING_PACKAGE_MARKER in text
    assert F1_CONTRACT_ONLY_COMPLETE_MARKER in text
    assert PACKAGE_F_COMPLETE_MARKER in text
    assert F2_COMPLETE_MARKER in text
    assert INV005_RUNTIME_PARKED_MARKER in text
    assert RUNTIME_GO_READY_MARKER in text


def test_inv016_durable_completion_canonical_binding_registry_complete() -> None:
    assert len(INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY) == 3
    binding_ids = {
        record["binding_id"] for record in INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY
    }
    assert binding_ids == {
        "inv016_upstream_canonical",
        "pe42_completion_facade",
        "durable_completion_validation_graph",
    }
    for record in INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY:
        assert record["authority_lift"] is False
        assert record["operative_testnet_execution_executed"] is False
        assert record["operative_network_access_executed"] is False
        assert record["repair_authority"] is False
        assert record["trading_authority"] is False
        assert record["promotion_authority"] is False
        assert record["reverse_authority_forbidden"] is True
        assert Path(REPO_ROOT / record["owner_path"]).exists()


def test_inv016_durable_completion_registry_upstream_owner_matches_inv016_contract() -> None:
    upstream = INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[0]
    assert upstream["owner_path"] == INV016_CANONICAL_OWNER_PATH
    assert upstream["layer"] == "INV016_UPSTREAM_CANONICAL"
    assert BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER == (
        "ops.bounded_master_v2_testnet_completion_path_wiring_v0"
    )
    assert (
        INV016_WIRING_PACKAGE_MARKER == "BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_V0=true"
    )


def test_inv016_durable_completion_dependency_direction_is_downstream_only() -> None:
    assert INV016_DURABLE_COMPLETION_DEPENDENCY_DIRECTION == (
        "offline_master_v2_replay",
        "offline_replay_six_node_validation_graph_binding",
        "inv016_completion_path_wiring",
        "pe42_durable_completion_facade",
        "durable_completion_validation_graph",
    )
    inv016_index = INV016_DURABLE_COMPLETION_DEPENDENCY_DIRECTION.index(
        "inv016_completion_path_wiring"
    )
    pe42_index = INV016_DURABLE_COMPLETION_DEPENDENCY_DIRECTION.index(
        "pe42_durable_completion_facade"
    )
    assert inv016_index < pe42_index


def test_inv016_durable_completion_sole_canonical_completion_facade_import_in_wiring_owner() -> (
    None
):
    wiring_imports = _imported_modules_from_source(INV016_MODULE)
    completion_imports = {
        module
        for module in wiring_imports
        if module.endswith("durable_run_primary_evidence_completion_integration_contract_v0")
    }
    assert completion_imports == {_COMPLETION_FACADE_CANONICAL_IMPORT_MODULE}
    assert _FORBIDDEN_PARALLEL_INV016_BINDING_SOURCES.isdisjoint(wiring_imports)
    wiring_source = INV016_MODULE.read_text(encoding="utf-8")
    assert CANONICAL_TESTNET_COMPLETION_OWNER == DURABLE_COMPLETION_CANONICAL_OWNER_PATH


@lru_cache(maxsize=1)
def _cached_wiring_evaluation():
    return evaluate_bounded_master_v2_testnet_completion_path_wiring(_valid_market_input())


@lru_cache(maxsize=1)
def _cached_offline_replay_bundle():
    return _offline_replay_bundle()


@pytest.fixture(scope="module", name="wiring_evaluation")
def _wiring_evaluation_fixture():
    return _cached_wiring_evaluation()


@pytest.fixture(scope="module", name="offline_replay_bundle")
def _offline_replay_bundle_fixture():
    return _cached_offline_replay_bundle()


def test_inv016_durable_completion_completion_chain_validator_references_inv016_digest_fields() -> (
    None
):
    validator_path = REPO_ROOT / DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH
    validator_source = validator_path.read_text(encoding="utf-8")
    assert "_validate_master_v2_completion_chain_digest_binding" in validator_source
    assert "MASTER_V2_BINDING_TO_COMPLETION_CHAIN_FIELD_NAMES" in validator_source
    master_v2_fields = {
        field
        for binding_field, chain_field in MASTER_V2_BINDING_TO_COMPLETION_CHAIN_FIELD_NAMES
        for field in (binding_field, chain_field)
    }
    assert "dashboard_display_projection_digest" in master_v2_fields
    assert "completion_referenced_dashboard_display_projection_digest" in master_v2_fields
    validator_imports = _imported_modules_from_source(validator_path)
    assert "bounded_master_v2_testnet_completion_path_wiring_v0" not in validator_imports
    assert _FORBIDDEN_PARALLEL_INV016_BINDING_SOURCES.isdisjoint(validator_imports)


def test_inv016_durable_completion_binding_authority_neutral_on_happy_path(
    wiring_evaluation,
) -> None:
    result = wiring_evaluation
    machine = result.to_machine_lines()
    assert result.orders_total == 0
    assert result.cancels_total == 0
    assert result.fills_total == 0
    assert result.positions_opened_total == 0
    assert result.dashboard_display_projection_digest
    assert result.replay_proof_classification == PROOF_CLASSIFICATION_FULL_E2E_BOUND
    assert machine["TESTNET_EXECUTES_CANONICAL_MASTER_V2"] is False
    assert machine["TESTNET_SIX_NODE_VALIDATION_GRAPH_PROVEN"] is False
    assert machine["TESTNET_PRIMARY_EVIDENCE_RETENTION_PROVEN"] is False
    assert "retention verification result required" in result.fail_reasons


def test_inv016_missing_market_input_fails_closed() -> None:
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(None)
    assert result.wiring_pass is False
    assert result.admission_pass is False
    assert result.missing_testnet_market_input_fails_closed is True
    assert any("testnet market input required" in reason for reason in result.fail_reasons)


def test_inv016_dashboard_display_projection_digest_drift_fails_closed(
    offline_replay_bundle,
) -> None:
    replay_result, six_node_binding, integration_input = offline_replay_bundle
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_dashboard_display_projection_digest="0" * 64,
    )
    _, fail_reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        bad,
        six_node_binding,
    )
    assert fail_reasons
    assert any("dashboard_display_projection_digest" in reason for reason in fail_reasons)


def test_inv016_replay_proof_classification_not_full_e2e_fails_closed(
    offline_replay_bundle,
) -> None:
    replay_result, six_node_binding, integration_input = offline_replay_bundle
    bad_binding = replace(
        six_node_binding,
        proof_classification="GRAPH_FAIL_CLOSED",
    )
    classification, fail_reasons = verify_replay_proof_classification_wiring(
        bad_binding,
        integration_input,
    )
    assert classification == "GRAPH_FAIL_CLOSED"
    assert fail_reasons
    assert any("replay_proof_classification" in reason for reason in fail_reasons)
    assert classification != PROOF_CLASSIFICATION_FULL_E2E_BOUND


def test_inv016_canonical_completion_owner_reference_consistent_on_happy_path(
    offline_replay_bundle,
) -> None:
    replay_result, six_node_binding, integration_input = offline_replay_bundle
    digest, fail_reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        integration_input,
        six_node_binding,
    )
    assert digest
    assert not fail_reasons
    assert CANONICAL_TESTNET_COMPLETION_OWNER == DURABLE_COMPLETION_CANONICAL_OWNER_PATH
    assert (
        integration_input.completion_proof_chain.completion_referenced_dashboard_display_projection_digest
        == digest
    )


def test_graph_inv016_canonical_binding_registry_aligns_with_wiring_owner() -> None:
    assert INV016_DURABLE_COMPLETION_BINDING_PACKAGE_MARKER.endswith("=true")
    assert len(INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY) == 3
    assert INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[0]["owner_path"] == (
        INV016_CANONICAL_OWNER_PATH
    )
    assert INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[1]["owner_path"] == (
        DURABLE_COMPLETION_CANONICAL_OWNER_PATH
    )
    assert INV016_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[2]["owner_path"] == (
        DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH
    )
    assert "pe42_durable_completion_facade" in INV016_DURABLE_COMPLETION_DEPENDENCY_DIRECTION


def test_graph_completion_chain_validator_imports_master_v2_digest_binding_only() -> None:
    completion_chain_source = (
        REPO_ROOT / DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH
    ).read_text(encoding="utf-8")
    assert "_validate_master_v2_completion_chain_digest_binding" in completion_chain_source
    assert "bounded_master_v2_testnet_completion_path_wiring_v0" not in completion_chain_source
    assert "src.execution.order_router" not in completion_chain_source


def test_graph_completion_chain_validator_is_canonical_inv016_binding_entrypoint() -> None:
    from src.ops.durable_completion_validation import graph

    validators = graph._load_validators()
    assert validators[VALIDATOR_COMPLETION_CHAIN].__name__ == (
        validate_completion_proof_chain_binding.__name__
    )
    assert VALIDATOR_COMPLETION_CHAIN in PROOF_BINDING_VALIDATION_ORDER
    assert VALIDATOR_EVENT_STREAM in PROOF_BINDING_VALIDATION_GRAPH[VALIDATOR_COMPLETION_CHAIN]


def test_graph_inv016_binding_authority_neutral_on_happy_path(wiring_evaluation) -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    context = ValidationContext(integration_input=integration_input)
    assert not validate_completion_proof_chain_binding(context).fail_reasons
    wiring_result = wiring_evaluation
    assert wiring_result.dashboard_display_projection_digest
    assert wiring_result.replay_proof_event_stream_non_authorizing is True


def test_graph_inv016_dashboard_display_projection_digest_drift_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_dashboard_display_projection_digest="0" * 64,
    )
    result = validate_completion_proof_chain_binding(ValidationContext(integration_input=bad))
    assert any(
        "completion_proof_chain.master_v2" in reason
        or "dashboard_display_projection_digest" in reason
        for reason in result.fail_reasons
    )


def test_graph_inv016_completion_chain_master_v2_digest_alignment_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_dashboard_display_projection_digest="0" * 64,
    )
    result = validate_completion_proof_chain_binding(ValidationContext(integration_input=bad))
    assert any(
        "completion_proof_chain.master_v2" in reason
        or "dashboard_display_projection_digest" in reason
        for reason in result.fail_reasons
    )


def test_inv016_f1_contract_only_scope_without_package_f_complete() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_F_COMPLETE_MARKER in text
    assert F2_COMPLETE_MARKER in text
    assert F1_CONTRACT_ONLY_COMPLETE_MARKER in text
    assert BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_LAYER_VERSION == "v0"


def test_inv016_f2_inv017_and_inv005_runtime_parking_unchanged() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert INV005_RUNTIME_PARKED_MARKER in text
    assert INTENT_9_BLOCKS_RUNTIME_ONLY_MARKER in text
    assert F2_COMPLETE_MARKER in text


def test_inv016_no_runtime_network_credential_or_trading_readiness_claimed() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert RUNTIME_GO_READY_MARKER in text
    assert RUNTIME_PROVEN_MARKER in text
    wiring_source = INV016_MODULE.read_text(encoding="utf-8")
    assert "Non-authorizing" in wiring_source
    assert "Does not execute testnet runtime" in wiring_source
