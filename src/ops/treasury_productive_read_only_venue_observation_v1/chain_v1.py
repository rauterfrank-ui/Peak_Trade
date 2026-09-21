"""Productive observation → reconciliation → shadow → E4 orchestration (offline joins)."""

from __future__ import annotations

from typing import Any

from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.constants_v1 import (
    NETWORK_ALLOWED as E4_NETWORK_ALLOWED,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.join_v1 import (
    join_treasury_capital_admission_into_account_equity_orchestration_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    join_treasury_reconciliation_into_capital_admission_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.constants_v1 import (
    SHADOW_HTTP_SURFACE_11_13_2,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.join_v1 import (
    evaluate_treasury_shadow_read_only_enforcement_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (
    EARLIEST_NEW_REAL_BLOCKER_AFTER_WP,
    TREASURY_OBSERVATION_INSTRUMENT_ID,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
    TreasuryProductiveReadOnlyVenueObservationError,
)


def execute_treasury_productive_reconciliation_chain_v1(
    observation: TreasuryVenueObservationV1,
) -> dict[str, Any]:
    interference = prove_treasury_interference_absent_v1()
    if interference.get("ok") is not True:
        raise TreasuryProductiveReadOnlyVenueObservationError("TREASURY_INTERFERENCE_PROOF_FAIL")

    treasury_join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=str(observation.account_identity),
        expected_instrument_id=str(observation.instrument_id or TREASURY_OBSERVATION_INSTRUMENT_ID),
    )
    shadow = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=observation,
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_2,
    )
    orchestration = join_treasury_capital_admission_into_account_equity_orchestration_v1(
        treasury_join
    )

    productive_host_join_status = "OFFLINE_JOIN_REACHABLE_PRODUCTIVE_HOST_NOT_WIRED"
    if E4_NETWORK_ALLOWED is not False:
        productive_host_join_status = "UNEXPECTED_E4_NETWORK_ALLOWED_TRUE"

    return {
        "RECONCILIATION_STATUS": treasury_join.reconciliation.reconciliation_class,
        "CAPITAL_ADMISSION_STATUS": treasury_join.capital_admission_evidence.evidence_status,
        "CAPITAL_ADMISSION_RISK_ADMISSIBLE": treasury_join.capital_admission_evidence.risk_admissible,
        "SHADOW_ENFORCEMENT": {
            "shadow_permitted": shadow.shadow_permitted,
            "fail_closed": shadow.fail_closed,
            "reconciliation_class": shadow.reconciliation_class,
            "reason_codes": list(shadow.reason_codes),
        },
        "ACCOUNT_STATE_JOIN_STATUS": {
            "orchestration_admitted": orchestration.ingress.orchestration_admitted,
            "fail_closed": orchestration.ingress.fail_closed,
            "treasury_reconciliation_class": orchestration.ingress.treasury_reconciliation_class,
            "reason_codes": list(orchestration.ingress.reason_codes),
        },
        "PRODUCTIVE_HOST_JOIN_STATUS": productive_host_join_status,
        "RISK_ADMISSION_BINDING_STATUS": "NO_RISK_ADMISSIBLE_MINT",
        "EARLIEST_NEW_REAL_BLOCKER": EARLIEST_NEW_REAL_BLOCKER_AFTER_WP,
        "TREASURY_INTERFERENCE_PROOF": interference.get("TREASURY_INTERFERENCE_PROOF"),
    }
