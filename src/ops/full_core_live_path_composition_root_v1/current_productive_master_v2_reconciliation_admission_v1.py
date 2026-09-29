"""Upstream reconciliation admission provenance for productive Master-V2 entry.

Witnesses successful Cap-1.1 reconciliation at the Cap-2.4 admission seam (or
equivalent upstream gate). Does not run reconciliation, mint authority, or
transfer reconciliation ownership to Master V2 / Double Play.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    OWNER,
)
from src.ops.productive_reconciliation_runtime_binding_v1.master_v2_entry_reconciliation_contract_v1 import (
    RECONCILIATION_AUTHORITY_TRANSFER,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    ProductiveReconciliationGateResultV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ReconciliationState

_MV2_RECONCILED = "reconciled"


class ProductiveMasterV2ReconciliationAdmissionError(ValueError):
    """Fail-closed Master-V2 reconciliation admission violation."""


class ProductiveMasterV2ReconciliationAdmissionContextV1(str, Enum):
    PRODUCTIVE_UPSTREAM_GATE = "PRODUCTIVE_UPSTREAM_GATE"
    EXPLICIT_NON_PRODUCTIVE_TEST_FIXTURE = "EXPLICIT_NON_PRODUCTIVE_TEST_FIXTURE"
    EXPLICIT_NON_PRODUCTIVE_BOUNDED_HARNESS = "EXPLICIT_NON_PRODUCTIVE_BOUNDED_HARNESS"


@dataclass(frozen=True)
class ProductiveMasterV2ReconciliationAdmissionV1:
    """Immutable witness that upstream reconciliation succeeded for this cycle."""

    context_class: ProductiveMasterV2ReconciliationAdmissionContextV1
    reconciliation_owner: str
    session_id: str
    repository_sha: str
    bound_instrument_id: str
    master_v2_reconciliation_state: str
    gate_ok: bool
    alpha_enabled: bool
    evidence_digest: str
    reconciliation_classification: str = ""

    def validate_for_productive_master_v2_entry_v1(self, *, instrument_id: str) -> None:
        native = str(instrument_id or "").strip()
        bound = str(self.bound_instrument_id or "").strip()
        if not native or not bound or native != bound:
            raise ProductiveMasterV2ReconciliationAdmissionError(
                "MASTER_V2_RECONCILIATION_ADMISSION_INSTRUMENT_MISMATCH"
            )
        if RECONCILIATION_AUTHORITY_TRANSFER is not False:
            raise ProductiveMasterV2ReconciliationAdmissionError(
                "RECONCILIATION_AUTHORITY_TRANSFER_FORBIDDEN"
            )
        if (
            self.context_class
            is ProductiveMasterV2ReconciliationAdmissionContextV1.PRODUCTIVE_UPSTREAM_GATE
        ):
            if str(self.reconciliation_owner or "").strip() != AUTHORITY_OWNER:
                raise ProductiveMasterV2ReconciliationAdmissionError(
                    "MASTER_V2_RECONCILIATION_ADMISSION_OWNER_MISMATCH"
                )
            if not self.gate_ok or not self.alpha_enabled:
                raise ProductiveMasterV2ReconciliationAdmissionError(
                    "MASTER_V2_RECONCILIATION_UPSTREAM_GATE_NOT_SUCCESSFUL"
                )
            if self.master_v2_reconciliation_state != _MV2_RECONCILED:
                raise ProductiveMasterV2ReconciliationAdmissionError(
                    "MASTER_V2_RECONCILIATION_STATE_NOT_RECONCILED"
                )
            if not str(self.evidence_digest or "").strip():
                raise ProductiveMasterV2ReconciliationAdmissionError(
                    "MASTER_V2_RECONCILIATION_EVIDENCE_DIGEST_MISSING"
                )
            return
        if self.context_class in {
            ProductiveMasterV2ReconciliationAdmissionContextV1.EXPLICIT_NON_PRODUCTIVE_TEST_FIXTURE,
            ProductiveMasterV2ReconciliationAdmissionContextV1.EXPLICIT_NON_PRODUCTIVE_BOUNDED_HARNESS,
        }:
            return
        raise ProductiveMasterV2ReconciliationAdmissionError(
            "MASTER_V2_RECONCILIATION_ADMISSION_CONTEXT_UNCLASSIFIED"
        )

    def integrated_replay_reconciliation_state_v1(self) -> ReconciliationState:
        self.validate_for_productive_master_v2_entry_v1(instrument_id=self.bound_instrument_id)
        if self.master_v2_reconciliation_state != _MV2_RECONCILED:
            return ReconciliationState.RECONCILIATION_REQUIRED
        return ReconciliationState.RECONCILED

    def is_productive_upstream_provenance_v1(self) -> bool:
        return (
            self.context_class
            is ProductiveMasterV2ReconciliationAdmissionContextV1.PRODUCTIVE_UPSTREAM_GATE
        )


def build_productive_master_v2_reconciliation_admission_from_gate_v1(
    *,
    gate: ProductiveReconciliationGateResultV1,
    session_id: str,
    repository_sha: str,
    bound_instrument_id: str,
) -> ProductiveMasterV2ReconciliationAdmissionV1:
    return ProductiveMasterV2ReconciliationAdmissionV1(
        context_class=ProductiveMasterV2ReconciliationAdmissionContextV1.PRODUCTIVE_UPSTREAM_GATE,
        reconciliation_owner=OWNER,
        session_id=str(session_id or "").strip(),
        repository_sha=str(repository_sha or "").strip(),
        bound_instrument_id=str(bound_instrument_id or "").strip(),
        master_v2_reconciliation_state=str(gate.master_v2_reconciliation_state or ""),
        gate_ok=bool(gate.ok),
        alpha_enabled=bool(gate.alpha_enabled),
        evidence_digest=str(gate.evidence.digest()),
        reconciliation_classification=str(gate.classification.value),
    )


def build_productive_master_v2_reconciliation_admission_from_cap24_reconciliation_result_v1(
    *,
    reconciliation_result: Mapping[str, Any] | None,
    session_id: str,
    repository_sha: str,
    bound_instrument_id: str,
    binding_gate_ok: bool,
    binding_alpha_enabled: bool,
) -> ProductiveMasterV2ReconciliationAdmissionV1 | None:
    if reconciliation_result is None or binding_gate_ok is not True:
        return None
    evidence_digest = str(reconciliation_result.get("evidence_digest") or "").strip()
    if not evidence_digest:
        return None
    return ProductiveMasterV2ReconciliationAdmissionV1(
        context_class=ProductiveMasterV2ReconciliationAdmissionContextV1.PRODUCTIVE_UPSTREAM_GATE,
        reconciliation_owner=OWNER,
        session_id=str(session_id or "").strip(),
        repository_sha=str(repository_sha or "").strip(),
        bound_instrument_id=str(bound_instrument_id or "").strip(),
        master_v2_reconciliation_state=str(
            reconciliation_result.get("master_v2_reconciliation_state") or ""
        ),
        gate_ok=bool(reconciliation_result.get("ok")),
        alpha_enabled=bool(reconciliation_result.get("alpha_enabled")),
        evidence_digest=evidence_digest,
        reconciliation_classification=str(reconciliation_result.get("classification") or ""),
    )


def build_explicit_non_productive_test_fixture_master_v2_reconciliation_admission_v1(
    *,
    bound_instrument_id: str,
    session_id: str = "explicit-non-productive-test-fixture",
    repository_sha: str = "explicit-non-productive-test-fixture",
) -> ProductiveMasterV2ReconciliationAdmissionV1:
    return ProductiveMasterV2ReconciliationAdmissionV1(
        context_class=(
            ProductiveMasterV2ReconciliationAdmissionContextV1.EXPLICIT_NON_PRODUCTIVE_TEST_FIXTURE
        ),
        reconciliation_owner=AUTHORITY_OWNER,
        session_id=session_id,
        repository_sha=repository_sha,
        bound_instrument_id=str(bound_instrument_id or "").strip(),
        master_v2_reconciliation_state=_MV2_RECONCILED,
        gate_ok=False,
        alpha_enabled=False,
        evidence_digest="",
        reconciliation_classification="EXPLICIT_NON_PRODUCTIVE_TEST_FIXTURE",
    )


def build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
    *,
    bound_instrument_id: str,
    session_id: str,
    repository_sha: str,
) -> ProductiveMasterV2ReconciliationAdmissionV1:
    return ProductiveMasterV2ReconciliationAdmissionV1(
        context_class=(
            ProductiveMasterV2ReconciliationAdmissionContextV1.EXPLICIT_NON_PRODUCTIVE_BOUNDED_HARNESS
        ),
        reconciliation_owner=AUTHORITY_OWNER,
        session_id=str(session_id or "").strip(),
        repository_sha=str(repository_sha or "").strip(),
        bound_instrument_id=str(bound_instrument_id or "").strip(),
        master_v2_reconciliation_state=_MV2_RECONCILED,
        gate_ok=False,
        alpha_enabled=False,
        evidence_digest="",
        reconciliation_classification="EXPLICIT_NON_PRODUCTIVE_BOUNDED_HARNESS",
    )
