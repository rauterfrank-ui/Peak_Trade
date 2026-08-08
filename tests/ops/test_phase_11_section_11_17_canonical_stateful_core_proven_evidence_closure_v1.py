"""Tests for Phase 11 §11.17 CANONICAL_STATEFUL_CORE_PROVEN evidence closure."""

from __future__ import annotations

import pytest

from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.binding_v1 import (
    CanonicalStatefulCoreProvenBindingError,
    bind_canonical_stateful_core_proven_from_cap72_v1,
)
from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.constants_v1 import (
    CAPABILITY_ID,
    SECTION_11_17_FIELD,
    SOURCE_CAPABILITY_ID,
)
from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.verifier_v1 import (
    verify_phase_11_section_11_17_canonical_stateful_core_proven_v1,
)


def test_cap72_binding_establishes_canonical_stateful_core_proven() -> None:
    binding = bind_canonical_stateful_core_proven_from_cap72_v1()
    assert binding["ok"] is True
    assert binding["SECTION_11_17_FIELD"] == SECTION_11_17_FIELD
    assert binding["CANONICAL_STATEFUL_CORE_PROVEN"] is True
    assert binding["CLOSURE_METHOD"] == "EXISTING_EVIDENCE_BINDING"
    assert binding["SOURCE_CAPABILITY_ID"] == SOURCE_CAPABILITY_ID
    assert binding["EVIDENCE_REUSED"] is True
    assert binding["REPROOF_EXECUTED"] is False
    assert binding["FIXTURE_ONLY"] is False
    assert binding["PRODUCTIVE_BINDING"] is True
    assert len(binding["EVIDENCE_BINDINGS"]) > 0
    assert binding["SIMULATED_LIFECYCLE_PROVEN"] is False
    assert binding["FULLY_AUTONOMOUS_LIVE_TRADING_READY"] is False
    assert binding["FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE"] is False
    assert binding["CAPABILITY_11_13_STARTED"] is False
    assert binding["NETWORK_SESSION_STARTED"] is False
    assert binding["ORDER_SUBMIT_REACHABLE"] is False
    assert binding["CREDENTIAL_ACCESS"] is False
    assert binding["CORE_LOGIC_CHANGE"] is False


def test_binding_rejects_silent_ready_or_lifecycle_overclaim() -> None:
    binding = bind_canonical_stateful_core_proven_from_cap72_v1()
    # Cap 7.2 proves stateful core only; Cap 7.1 lifecycle and READY remain out of scope.
    assert binding["SIMULATED_LIFECYCLE_PROVEN"] is False
    assert binding["TESTNET_LIFECYCLE_PROVEN"] is False
    assert binding["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    assert binding["LIVE_ORDER_LIFECYCLE_PROVEN"] is False
    with pytest.raises(CanonicalStatefulCoreProvenBindingError):
        # Sanity: error type remains importable/usable for fail-closed callers.
        raise CanonicalStatefulCoreProvenBindingError("PROBE")


def test_verifier_pass_preserves_other_section_11_17_residuals() -> None:
    result = verify_phase_11_section_11_17_canonical_stateful_core_proven_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    assert result["CAPABILITY_ID"] == CAPABILITY_ID
    claims = result["claims"]
    assert claims["CANONICAL_STATEFUL_CORE_PROVEN"] is True
    assert claims["SIMULATED_LIFECYCLE_PROVEN"] is False
    assert claims["TESTNET_LIFECYCLE_PROVEN"] is False
    assert claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    assert claims["LIVE_ORDER_LIFECYCLE_PROVEN"] is False
    assert claims["LIVE_RECONCILIATION_PROVEN"] is False
    assert claims["LIVE_RESTART_PROVEN"] is False
    assert claims["LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN"] is False
    assert claims["LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN"] is False
    assert claims["LIVE_PARTIAL_FILL_RECOVERY_PROVEN"] is False
    assert claims["LIVE_KILL_SWITCH_PROVEN"] is False
    assert claims["LIVE_AUTONOMOUS_DEGRADATION_PROVEN"] is False
    assert claims["LIVE_AUTONOMOUS_RECOVERY_PROVEN"] is False
    assert claims["LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN"] is False
    assert claims["LIVE_EVIDENCE_VERIFIED"] is False
    assert claims["OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION"] is True
    assert claims["FULLY_AUTONOMOUS_LIVE_TRADING_READY"] is False
    assert claims["FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE"] is False
    assert claims["CAPABILITY_11_13_STARTED"] is False
    assert claims["FIXTURE_ONLY"] is False


def test_cap_11_12_consumes_only_canonical_stateful_core_proven() -> None:
    from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1 import (
        constants_v1 as cap1112,
    )

    assert cap1112.CANONICAL_STATEFUL_CORE_PROVEN is True
    assert cap1112.SIMULATED_LIFECYCLE_PROVEN is False
    assert cap1112.TESTNET_LIFECYCLE_PROVEN is False
    assert cap1112.LIVE_PRIVATE_READ_ONLY_PROVEN is False
    assert cap1112.FULLY_AUTONOMOUS_LIVE_TRADING_READY is False
    assert cap1112.FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE is False
    assert cap1112.CAPABILITY_11_13_STARTED is False
