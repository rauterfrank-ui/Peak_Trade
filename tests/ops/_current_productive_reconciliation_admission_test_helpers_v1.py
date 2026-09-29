"""Test helpers for explicit non-productive Master-V2 reconciliation admission."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    ProductiveMasterV2ReconciliationAdmissionV1,
    build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1,
    build_explicit_non_productive_test_fixture_master_v2_reconciliation_admission_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def non_productive_test_master_v2_reconciliation_admission_v1(
    *,
    bound: BoundInstrumentV1,
    session_id: str = "explicit-non-productive-test-fixture",
) -> ProductiveMasterV2ReconciliationAdmissionV1:
    return build_explicit_non_productive_test_fixture_master_v2_reconciliation_admission_v1(
        bound_instrument_id=str(bound.instrument_id),
        session_id=session_id,
    )


def non_productive_harness_master_v2_reconciliation_admission_v1(
    *,
    bound: BoundInstrumentV1,
    session_id: str,
    repository_sha: str,
) -> ProductiveMasterV2ReconciliationAdmissionV1:
    return build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
        bound_instrument_id=str(bound.instrument_id),
        session_id=session_id,
        repository_sha=repository_sha,
    )
