"""Treasury Phase-3 shadow enforcement tests. No network. No mutation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.http_client_v1 import (
    LiveShadowReconHttpError,
    assert_endpoint_allowlisted_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.authority_v1 import (
    trading_authority_cannot_mint_treasury_authority_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.engine_v1 import (
    record_treasury_intent_v1,
    restore_treasury_records_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.persistence_v1 import (
    InMemoryTreasuryIntentStoreV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryReconciliationClassV1,
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
    evaluate_treasury_read_only_reconciliation_v1,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.constants_v1 import (
    SHADOW_HTTP_SURFACE_11_13_3,
    TREASURY_MUTATION_REACHABLE,
    TREASURY_PHASE_3_STATUS,
    TREASURY_RISK_ADMISSIBLE_MINT,
    TREASURY_SEPARATION_GATE_WIRED,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.interference_proof_v1 import (
    prove_treasury_phase_3_interference_absent_v1,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.join_v1 import (
    evaluate_treasury_shadow_enforcement_missing_observation_v1,
    evaluate_treasury_shadow_read_only_enforcement_v1,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.shadow_http_v1 import (
    assert_treasury_shadow_http_endpoint_allowed_v1,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.errors_v1 import (
    TreasuryPhase3ShadowEnforcementError,
)
from tests.ops.test_treasury_phase_1_offline_contracts_v1 import _draft
from tests.ops.test_treasury_phase_2_read_only_reconciliation_v1 import _obs

_ACCOUNT = "acct-treasury-phase3-001"
_INSTRUMENT = "BTC-USDT-SWAP"
_PACKAGE = Path(__file__).resolve().parents[2] / "src/ops/treasury_phase_3_shadow_enforcement_v1"
_FULL_CORE = Path(__file__).resolve().parents[2] / "src/ops/full_core_live_path_composition_root_v1"


@pytest.fixture(autouse=True)
def _clear_phase2_cache() -> None:
    clear_treasury_reconciliation_idempotency_cache_v1()


def test_phase3_contract_constants() -> None:
    assert TREASURY_PHASE_3_STATUS == "SHADOW_ENFORCEMENT_BOUND"
    assert TREASURY_SEPARATION_GATE_WIRED is True
    assert TREASURY_MUTATION_REACHABLE is False
    assert TREASURY_RISK_ADMISSIBLE_MINT is False


def test_balance_increase_before_reconciliation_no_capital_uplift() -> None:
    observation = _obs(
        venue_balance_raw="150",
        prior_reconciled_capital_raw="100",
        deposit_history_confirms_increase=False,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
    )
    result = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=observation,
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert result.capital_uplift_permitted is False
    assert result.shadow_permitted is False
    assert result.fail_closed is True
    assert "OBSERVED_INCREASE_NO_SHADOW_CAPITAL_UPLIFT" in result.reason_codes


def test_credible_decrease_stale_cached_state_fail_closed() -> None:
    observation = _obs(
        venue_balance_raw="80",
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
        external_depletion_signal=TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value,
    )
    result = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=observation,
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert result.fail_closed is True
    assert result.shadow_permitted is False
    assert result.reconciliation_class == TreasuryReconciliationClassV1.STALE.value


def test_unknown_stale_ambiguous_fail_closed() -> None:
    unknown = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=_obs(
            evidence_id="tevidence-phase3-unknown",
            balance_freshness=TreasuryFreshnessSignalV1.UNKNOWN.value,
        ),
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert unknown.fail_closed is True
    assert unknown.shadow_permitted is False

    clear_treasury_reconciliation_idempotency_cache_v1()
    stale = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=_obs(
            evidence_id="tevidence-phase3-stale",
            balance_freshness=TreasuryFreshnessSignalV1.STALE.value,
        ),
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert stale.fail_closed is True

    clear_treasury_reconciliation_idempotency_cache_v1()
    ambiguous = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=_obs(
            evidence_id="tevidence-phase3-ambiguous",
            balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
            deposit_history_freshness=TreasuryDepositHistorySignalV1.STALE.value,
        ),
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert ambiguous.fail_closed is True
    assert ambiguous.reconciliation_class == TreasuryReconciliationClassV1.AMBIGUOUS.value


def test_contradictory_observations_no_optimistic_reconcile() -> None:
    first = evaluate_treasury_read_only_reconciliation_v1(_obs())
    second = evaluate_treasury_read_only_reconciliation_v1(
        _obs(evidence_id="tevidence-phase3-other")
    )
    assert first.evidence_fingerprint == second.evidence_fingerprint
    assert second.reconciliation_class == TreasuryReconciliationClassV1.AMBIGUOUS.value
    shadow = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=_obs(evidence_id="tevidence-phase3-other"),
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert shadow.shadow_permitted is False
    assert shadow.fail_closed is True


def test_phase1_restart_evidence_preserved_independent_of_phase3() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _draft())
    restored = restore_treasury_records_v1(store)
    assert restored[0].intent_id == record.intent_id
    missing = evaluate_treasury_shadow_enforcement_missing_observation_v1(
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert missing.fail_closed is True
    assert missing.shadow_permitted is False


def test_trading_authority_cannot_mint_treasury() -> None:
    assert trading_authority_cannot_mint_treasury_authority_v1() is True


def test_treasury_mutation_not_reachable_from_shadow_http_join() -> None:
    with pytest.raises(TreasuryPhase3ShadowEnforcementError, match="TREASURY_SHADOW_GATE_DENY"):
        assert_treasury_shadow_http_endpoint_allowed_v1(
            endpoint="/api/v5/asset/withdrawal",
            method="GET",
            shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
        )
    with pytest.raises(LiveShadowReconHttpError, match="MUTATION_ENDPOINT_HARD_BLOCK|TREASURY_SHADOW_GATE_DENY"):
        assert_endpoint_allowlisted_v1("/api/v5/asset/transfer")


def test_missing_observation_fail_closed() -> None:
    result = evaluate_treasury_shadow_enforcement_missing_observation_v1(
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert result.fail_closed is True
    assert "MISSING_OBSERVATION_FAIL_CLOSED" in result.reason_codes


def test_full_core_still_treasury_interference_free() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
    joined = "\n".join(path.read_text(encoding="utf-8") for path in _FULL_CORE.glob("*.py"))
    assert "treasury_phase_3_shadow_enforcement_v1" not in joined


def test_phase3_interference_proof() -> None:
    proof = prove_treasury_phase_3_interference_absent_v1()
    assert proof["ok"] is True
    assert proof["STEP_29P_AUTHORITY_UNCHANGED"] is True
    package_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in _PACKAGE.glob("*.py")
        if path.name not in {"constants_v1.py", "interference_proof_v1.py"}
    )
    assert "evaluate_step_29p_capital_risk_admissibility_v1" not in package_text
    assert "join_capital_admission_into_admission_inputs_v1" not in package_text


def test_reconciled_stable_capital_shadow_observe_only() -> None:
    observation = _obs(
        venue_balance_raw="100",
        prior_reconciled_capital_raw="100",
        deposit_history_confirms_increase=False,
    )
    result = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=observation,
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_3,
    )
    assert result.shadow_permitted is True
    assert result.capital_uplift_permitted is False
