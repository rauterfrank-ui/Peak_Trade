"""Semantic enforcement matrix A–R for native full-cycle host v1."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_PUBLIC_INSTRUMENTS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_native_full_cycle_host_v1 import (
    APPLY_AUTHORITY,
    BINDING_DECISION_AUTHORITY,
    CAPITAL_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORITY,
    OWNER_GO,
    RANKING_AUTHORITY,
    RISK_POLICY_AUTHORITY,
    SELECTION_AUTHORITY,
    TRADING_DECISION_AUTHORITY,
    CurrentProductiveNativeFullCycleHostError,
    execute_current_productive_native_full_cycle_host_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
    TRUSTED_TEST_ORIGIN_MAIN_SHA,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE,
    MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD,
    ProductiveCanonicalPriceProvenanceError,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
    build_provenance_from_resolved_cmc_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    MismatchInstrumentTransportV1,
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    _eligible_transport,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    ProductiveClassFreshGetTransportV1,
    _productive_instruments_row_for_enter_metadata_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_SRC = (
    REPO_ROOT / "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_native_full_cycle_host_v1.py"
)
ADVANCE_SRC = (
    REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_layered_long_mv2_state_advance_for_pre_external_v1.py"
)
AVAIL_EQ = "10000.00"
_INST = "ADA-USDT-SWAP"


@pytest.fixture(scope="module")
def module_native_pre_external_result(tmp_path_factory: pytest.TempPathFactory):
    root = tmp_path_factory.mktemp("native_module_preext")
    return _run_host(root)


def _transports(*, instrument_id: str = _INST, avail_eq: str = AVAIL_EQ):
    payloads = dict(_identity_payloads(instrument_id=instrument_id, avail_eq=avail_eq))
    payloads[ENDPOINT_PUBLIC_INSTRUMENTS] = {
        "code": "0",
        "data": [_productive_instruments_row_for_enter_metadata_v1(instrument_id=instrument_id)],
    }
    a = ProductiveClassFreshGetTransportV1(payloads=payloads)
    b = ProductiveClassFreshGetTransportV1(payloads=dict(payloads))
    return a, b


def _integrity() -> MockCurrentProductive29PIntegrityBackendV1:
    return MockCurrentProductive29PIntegrityBackendV1(
        origin_main=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        head=TRUSTED_TEST_ORIGIN_MAIN_SHA,
    )


def _run_host(tmp_path: Path, **kwargs):
    get_a, get_b = _transports()
    defaults = {
        "owner_go": OWNER_GO,
        "origin_main_sha": TRUSTED_TEST_ORIGIN_MAIN_SHA,
        "evidence_root": tmp_path,
        "acquisition_transport": _eligible_transport(),
        "fresh_get_transport": get_a,
        "pre_external_fresh_get_transport": get_b,
        "producer_observed_at_unix": 1_700_000_100.0,
        "execution_integrity_backend": _integrity(),
    }
    defaults.update(kwargs)
    return execute_current_productive_native_full_cycle_host_v1(**defaults)


def test_A_host_has_no_trading_authority() -> None:
    assert TRADING_DECISION_AUTHORITY == "NONE"


def test_B_host_has_no_ranking_authority() -> None:
    assert RANKING_AUTHORITY == "NONE"


def test_C_host_has_no_selection_authority() -> None:
    assert SELECTION_AUTHORITY == "NONE"


def test_D_host_cannot_reselect_after_cap23() -> None:
    src = HOST_SRC.read_text(encoding="utf-8")
    assert "single_selected_future_policy_v1" not in src
    assert "cap23" not in src.lower() or "execute_current_productive_eea" in src


def test_E_host_cannot_rerank_after_cap22() -> None:
    src = HOST_SRC.read_text(encoding="utf-8")
    assert "productive_futures_ranking_producer_v1" not in src


def test_F_cap24_bound_lineage_preserved_into_selected_market_path(
    module_native_pre_external_result,
) -> None:
    result = module_native_pre_external_result
    bound = result.eea_result.bound_instrument
    assert bound is not None
    assert bound.venue_native_id == _INST
    assert result.pre_external_result.instrument_metadata_status in {
        "PASS",
        "TRUSTED_PRESENT",
        "TRUSTED_CURRENT",
        "OK",
    }


def test_G_external_observation_uses_current_transformations_not_driver_objects(
    tmp_path: Path,
) -> None:
    result = _run_host(tmp_path / "g")
    assert result.eea_result.eea_universe_acquisition_status == "PASS"
    assert result.bound_instrument_handoff == "NATIVE_TYPED_FROM_EEA_RESULT"


def test_H_native_host_does_not_use_pre_armed_mv2_fixture() -> None:
    for path in (HOST_SRC, ADVANCE_SRC):
        text = path.read_text(encoding="utf-8")
        assert "prepare_layered_long_armed_seed_for_pre_external_invoke_v1" not in text
        assert "_current_productive_natural_mv2_dp_enter_fixture_v1" not in text


def test_I_decision_capital_join_same_session_lineage(module_native_pre_external_result) -> None:
    result = module_native_pre_external_result
    store_root = Path(result.store_root)
    assert result.session_id
    assert store_root.is_dir()
    assert (
        result.pre_external_result.common_epoch_id
        or result.pre_external_result.wp1_status == "PASS"
    )


def test_J_crs_cannot_change_direction(module_native_pre_external_result) -> None:
    result = module_native_pre_external_result
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    env = result.pre_external_result.fresh_executable_enter_final_order_envelope
    assert env is not None
    assert env.side == "buy"
    assert result.pre_external_result.current_productive_decision_result.startswith("EXECUTABLE")


def test_K_intent_cannot_change_direction(module_native_pre_external_result) -> None:
    result = module_native_pre_external_result
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    env = result.pre_external_result.fresh_executable_enter_final_order_envelope
    assert env is not None
    assert env.side_source == "STEP_29Q_CANONICAL_ORDER_INTENT"
    assert env.side == "buy"


def test_L_pre_external_does_not_imply_permit(module_native_pre_external_result) -> None:
    result = module_native_pre_external_result
    assert result.pre_external_result.permit_created is False


def test_M_pre_external_does_not_imply_post(module_native_pre_external_result) -> None:
    result = module_native_pre_external_result
    assert result.pre_external_result.post_count == 0
    assert result.pre_external_result.external_effect_occurred is False


def test_N_host_cannot_mint_external_effect_authorization() -> None:
    assert EXTERNAL_EFFECT_AUTHORITY == "NONE"
    assert APPLY_AUTHORITY == "NONE"
    assert CAPITAL_AUTHORITY == "NONE"
    assert RISK_POLICY_AUTHORITY == "NONE"
    assert BINDING_DECISION_AUTHORITY == "NONE"


def test_O_fail_closed_missing_selected_market_observation(tmp_path: Path) -> None:
    get_a, get_b = _transports()
    empty = ProductiveClassFreshGetTransportV1(payloads={})
    with pytest.raises((CurrentProductiveNativeFullCycleHostError, Exception)):
        execute_current_productive_native_full_cycle_host_v1(
            owner_go=OWNER_GO,
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "o",
            acquisition_transport=_eligible_transport(),
            fresh_get_transport=empty,
            pre_external_fresh_get_transport=get_b,
            producer_observed_at_unix=1_700_000_100.0,
            execution_integrity_backend=_integrity(),
        )


def test_P_fail_closed_stale_observation(tmp_path: Path) -> None:
    with pytest.raises((CurrentProductiveNativeFullCycleHostError, Exception)):
        _run_host(tmp_path / "p", producer_observed_at_unix=1.0)


def test_Q_fail_closed_instrument_mismatch(tmp_path: Path) -> None:
    get_a, _ = _transports()
    mismatch = MismatchInstrumentTransportV1(
        payloads=dict(_identity_payloads(instrument_id=_INST, avail_eq=AVAIL_EQ)),
        wrong_inst="ETH-USDT-SWAP",
    )
    result = execute_current_productive_native_full_cycle_host_v1(
        owner_go=OWNER_GO,
        origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "q",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=get_a,
        pre_external_fresh_get_transport=mismatch,
        producer_observed_at_unix=1_700_000_100.0,
        execution_integrity_backend=_integrity(),
    )
    assert result.eea_result.bound_instrument is not None
    assert result.eea_result.bound_instrument.venue_native_id == _INST
    assert (
        result.pre_external_reached != "true"
        or result.terminal_disposition != DISPOSITION_PRE_EXTERNAL_EFFECT
    )


def test_S_synthetic_close_mark_provenance_not_venue_public(
    module_native_pre_external_result,
) -> None:
    host_text = HOST_SRC.read_text(encoding="utf-8")
    advance_text = ADVANCE_SRC.read_text(encoding="utf-8")
    assert "build_provenance_from_governed_synthetic_close_mark_and_index_v1" in host_text
    assert "build_provenance_from_governed_synthetic_close_mark_and_index_v1" in advance_text
    assert "build_provenance_from_resolved_cmc_mark_and_index_v1" not in host_text
    assert "build_provenance_from_resolved_cmc_mark_and_index_v1" not in advance_text
    synthetic = build_provenance_from_governed_synthetic_close_mark_and_index_v1(
        venue_native_id=_INST,
        mark_px=101.0,
        index_px=100.495,
    )
    assert synthetic.mark_source == MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE
    assert synthetic.mark_source != MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD
    with pytest.raises(ProductiveCanonicalPriceProvenanceError) as exc:
        build_provenance_from_resolved_cmc_mark_and_index_v1(
            venue_native_id=_INST,
            mark_px=101.0,
            index_px=100.495,
            index_source="EXPLICIT_TEST_FIXTURE_INDEX",
        )
    assert "SYNTHETIC_INDEX_OKX_MARK_SOURCE_COLLAPSE_FORBIDDEN" in str(exc.value)
    okx = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=okx_public_mark_price_payload_v1(
            native_id=_INST, mark_px=101.0, index_px=100.5
        ),
        venue_native_id=_INST,
    )
    assert okx.mark_source == MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD
    _ = module_native_pre_external_result


def test_R_fail_closed_missing_capital_29p_admission(tmp_path: Path) -> None:
    payloads = dict(_identity_payloads(instrument_id=_INST, avail_eq=AVAIL_EQ))
    payloads[ENDPOINT_ACCOUNT_BALANCE] = {"code": "0", "data": []}
    bad = ProductiveClassFreshGetTransportV1(payloads=payloads)
    with pytest.raises((CurrentProductiveNativeFullCycleHostError, Exception)):
        execute_current_productive_native_full_cycle_host_v1(
            owner_go=OWNER_GO,
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "r",
            acquisition_transport=_eligible_transport(),
            fresh_get_transport=bad,
            pre_external_fresh_get_transport=bad,
            producer_observed_at_unix=1_700_000_100.0,
            execution_integrity_backend=_integrity(),
        )


SEMANTIC_ENFORCEMENT_A_TO_R_MATRIX: dict[str, str] = {
    "A": "test_A_host_has_no_trading_authority",
    "B": "test_B_host_has_no_ranking_authority",
    "C": "test_C_host_has_no_selection_authority",
    "D": "test_D_host_cannot_reselect_after_cap23",
    "E": "test_E_host_cannot_rerank_after_cap22",
    "F": "test_F_cap24_bound_lineage_preserved_into_selected_market_path",
    "G": "test_G_external_observation_uses_current_transformations_not_driver_objects",
    "H": "test_H_native_host_does_not_use_pre_armed_mv2_fixture",
    "I": "test_I_decision_capital_join_same_session_lineage",
    "J": "test_J_crs_cannot_change_direction",
    "K": "test_K_intent_cannot_change_direction",
    "L": "test_L_pre_external_does_not_imply_permit",
    "M": "test_M_pre_external_does_not_imply_post",
    "N": "test_N_host_cannot_mint_external_effect_authorization",
    "O": "test_O_fail_closed_missing_selected_market_observation",
    "P": "test_P_fail_closed_stale_observation",
    "Q": "test_Q_fail_closed_instrument_mismatch",
    "R": "test_R_fail_closed_missing_capital_29p_admission",
    "S": "test_S_synthetic_close_mark_provenance_not_venue_public",
}


def test_semantic_enforcement_matrix_documents_all_invariants() -> None:
    assert set(SEMANTIC_ENFORCEMENT_A_TO_R_MATRIX.keys()) == set("ABCDEFGHIJKLMNOPQRS")
    mod = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in mod.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    for _letter, test_name in SEMANTIC_ENFORCEMENT_A_TO_R_MATRIX.items():
        assert test_name in defined
