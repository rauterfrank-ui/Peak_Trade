"""Productive observation → reconciliation → shadow → E4 orchestration (offline joins)."""

from __future__ import annotations

from typing import Any

from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.constants_v1 import (
    NETWORK_ALLOWED as E4_NETWORK_ALLOWED,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.join_v1 import (
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1,
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

    shadow = evaluate_treasury_shadow_read_only_enforcement_v1(
        observation=observation,
        shadow_surface=SHADOW_HTTP_SURFACE_11_13_2,
    )
    instrument_id = str(observation.instrument_id or TREASURY_OBSERVATION_INSTRUMENT_ID)
    productive_host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=str(observation.account_identity),
        expected_instrument_id=instrument_id,
    )
    treasury_join = productive_host.treasury_join
    orchestration = productive_host.orchestration_join
    host_eval = productive_host.host_evaluation

    productive_host_join_status = (
        "PRODUCTIVE_HOST_JOIN_WIRED"
        if host_eval.productive_host_reachable is True
        else "PRODUCTIVE_HOST_JOIN_UNREACHABLE"
    )
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
        "PRODUCTIVE_HOST_EVALUATION": {
            "productive_host_reachable": host_eval.productive_host_reachable,
            "fail_closed": host_eval.fail_closed,
            "treasury_capital_admitted": host_eval.treasury_capital_admitted,
            "orchestration_ingress_admitted": host_eval.orchestration_ingress_admitted,
            "observed_equity_minted": host_eval.observed_equity_minted,
            "reconciled_equity_minted": host_eval.reconciled_equity_minted,
            "risk_admissible_mint": host_eval.risk_admissible_mint,
            "sizing_authority_changed": host_eval.sizing_authority_changed,
            "treasury_reconciliation_status": host_eval.treasury_reconciliation_status,
            "reason_codes": list(host_eval.reason_codes),
        },
        "RISK_ADMISSION_BINDING_STATUS": "NO_RISK_ADMISSIBLE_MINT",
        "EARLIEST_NEW_REAL_BLOCKER": EARLIEST_NEW_REAL_BLOCKER_AFTER_WP,
        "TREASURY_INTERFERENCE_PROOF": interference.get("TREASURY_INTERFERENCE_PROOF"),
    }
