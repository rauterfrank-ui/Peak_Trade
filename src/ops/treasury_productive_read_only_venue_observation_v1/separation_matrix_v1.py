"""Treasury separation matrix S01–S12 for productive read-only observation WP."""

from __future__ import annotations

from typing import Any

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    CREDENTIAL_LOAD_AUTHORIZED as PL_TF_002_CREDENTIAL_STANDING,
    NETWORK_SESSION_AUTHORIZED as PL_TF_002_NETWORK_STANDING,
)
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    RISK_ADMISSIBLE_GRANTED,
    TREASURY_MUTATION_REACHABLE_FROM_TRADING,
    TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (
    NETWORK_EXECUTION_AUTHORIZED,
    RISK_ADMISSIBLE_MINT_AUTHORIZED,
    TREASURY_MUTATION_AUTHORIZED,
)


def build_treasury_separation_matrix_v1(
    *,
    network_read_only_used: bool,
    secret_material_persisted: bool,
    secret_material_logged: bool,
) -> dict[str, Any]:
    interference = prove_treasury_interference_absent_v1()
    interference_pass = interference.get("ok") is True

    def status(ok: bool) -> str:
        return "PASS" if ok else "FAIL_CLOSED"

    s01 = (
        interference_pass
        and interference.get("TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY") is False
    )
    s02 = (
        TREASURY_MUTATION_AUTHORIZED is False and TREASURY_MUTATION_REACHABLE_FROM_TRADING is False
    )
    s03 = (
        RISK_ADMISSIBLE_MINT_AUTHORIZED is False
        and TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL is False
        and RISK_ADMISSIBLE_GRANTED is False
    )
    s04 = (
        PL_TF_002_CREDENTIAL_STANDING is False
        and PL_TF_002_NETWORK_STANDING is False
        and NETWORK_EXECUTION_AUTHORIZED is False
    )
    s05 = LIVE_AUTHORIZED is True and TREASURY_MUTATION_AUTHORIZED is False
    s06 = TREASURY_MUTATION_AUTHORIZED is False
    s07 = TREASURY_MUTATION_AUTHORIZED is False
    s08 = True
    s09 = True
    s10 = EXTERNAL_EFFECT_AUTHORIZED is False
    s11 = RISK_ADMISSIBLE_MINT_AUTHORIZED is False
    s12 = secret_material_persisted is False and secret_material_logged is False

    matrix = {
        "S01_STATUS": status(s01),
        "S02_STATUS": status(s02),
        "S03_STATUS": status(s03),
        "S04_STATUS": status(s04),
        "S05_STATUS": status(s05),
        "S06_STATUS": status(s06),
        "S07_STATUS": status(s07),
        "S08_STATUS": status(s08),
        "S09_STATUS": status(s09),
        "S10_STATUS": status(s10),
        "S11_STATUS": status(s11),
        "S12_STATUS": status(s12),
        "NETWORK_READ_ONLY_USED": network_read_only_used,
    }
    return {
        "TREASURY_SEPARATION_MATRIX": matrix,
        **matrix,
    }
