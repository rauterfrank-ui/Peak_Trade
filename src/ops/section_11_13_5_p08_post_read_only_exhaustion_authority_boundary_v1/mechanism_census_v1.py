"""Exhaustive repository-backed census of P08 state-appearance mechanisms.

Each record is bound to an existing contract, standing constant, or
persisted evidence pack. No network I/O. No invented producers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    G_POSMODE_SUBMIT_BODY_PROVEN,
    HISTORICAL_P08_EMPTY_DATA_PACK,
    HISTORICAL_P08_READ_ONLY_PACK,
    HISTORICAL_Z2DP_PACK,
    TARGET_INSTRUMENT_ID,
)


DISPOSITION_AVAILABLE_WITHOUT_MUTATION = "AVAILABLE_WITHOUT_MUTATION"
DISPOSITION_EXTERNAL_ONLY = "EXTERNAL_STATE_APPEARANCE_ONLY"
DISPOSITION_TESTNET = "TESTNET_STATE_CREATION"
DISPOSITION_CANARY = "CANARY_STATE_CREATION"
DISPOSITION_LIVE = "LIVE_STATE_CREATION"
DISPOSITION_BLOCKED_PRETRADE = "BLOCKED_BY_PRETRADE"
DISPOSITION_BLOCKED_AUTH = "BLOCKED_BY_AUTH"
DISPOSITION_BLOCKED_NETWORK = "BLOCKED_BY_NETWORK"
DISPOSITION_BLOCKED_FUNDING = "BLOCKED_BY_FUNDING"
DISPOSITION_BLOCKED_CONTRACT = "BLOCKED_BY_CONTRACT"
DISPOSITION_NOT_P08_CAPABLE = "NOT_P08_CAPABLE"
DISPOSITION_INSUFFICIENT = "SEMANTICALLY_INSUFFICIENT"


@dataclass(frozen=True)
class StateAppearanceMechanismV1:
    mechanism_id: str
    description: str
    authority_class: str
    implemented: bool
    enabled: bool
    owner_authorized: bool
    credentials_network_permit: bool
    funding_margin_prerequisites_exist: bool
    pretrade_gates_pass: bool
    changes_real_account_state: bool
    financial_loss_exposure: bool
    would_create_exact_p08_observation: bool
    compatible_single_selected_future_max_positions_1: bool
    touches_canonical_core_trading_logic: bool
    requires_new_pr_before_execution: bool
    disposition: str
    currently_viable_for_p08: bool
    upstream_evidence: str
    blocked_by: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanism_id": self.mechanism_id,
            "description": self.description,
            "authority_class": self.authority_class,
            "implemented": self.implemented,
            "enabled": self.enabled,
            "owner_authorized": self.owner_authorized,
            "credentials_network_permit": self.credentials_network_permit,
            "funding_margin_prerequisites_exist": self.funding_margin_prerequisites_exist,
            "pretrade_gates_pass": self.pretrade_gates_pass,
            "changes_real_account_state": self.changes_real_account_state,
            "financial_loss_exposure": self.financial_loss_exposure,
            "would_create_exact_p08_observation": self.would_create_exact_p08_observation,
            "compatible_single_selected_future_max_positions_1": (
                self.compatible_single_selected_future_max_positions_1
            ),
            "touches_canonical_core_trading_logic": self.touches_canonical_core_trading_logic,
            "requires_new_pr_before_execution": self.requires_new_pr_before_execution,
            "disposition": self.disposition,
            "currently_viable_for_p08": self.currently_viable_for_p08,
            "upstream_evidence": self.upstream_evidence,
            "blocked_by": self.blocked_by,
        }


MECHANISMS: tuple[StateAppearanceMechanismV1, ...] = (
    StateAppearanceMechanismV1(
        mechanism_id="M01_CURRENTLY_OBSERVED_TARGET_NONZERO_ROW",
        description=(
            "A fresh unfiltered GET /account/positions already showing exactly one "
            f"nonzero {TARGET_INSTRUMENT_ID} row"
        ),
        authority_class="READ_ONLY_PRIVATE_GET",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=True,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=False,
        disposition=DISPOSITION_AVAILABLE_WITHOUT_MUTATION,
        currently_viable_for_p08=False,
        upstream_evidence=HISTORICAL_P08_EMPTY_DATA_PACK,
        blocked_by="CASE_C_EMPTY_DATA_NOT_ZERO;TARGET_ROW_ABSENT_THIS_WINDOW",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M02_EXTERNAL_MANUAL_VENUE_UI_POSITION",
        description=(
            "Owner-created position on eea.okx.com for the bound target instrument "
            "outside Peak_Trade POST; Z2DN source-irrelevant observation policy"
        ),
        authority_class="EXTERNAL_MANUAL_POSITION_APPEARANCE",
        implemented=True,
        enabled=True,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=True,
        financial_loss_exposure=True,
        would_create_exact_p08_observation=True,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=False,
        disposition=DISPOSITION_EXTERNAL_ONLY,
        currently_viable_for_p08=True,
        upstream_evidence="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "prerequisite_08_position_source_policy_rebind_v1.py",
        blocked_by="OWNER_VENUE_ACTION_NOT_YET_PERFORMED;NO_UNCONSUMED_P08_GET_GO",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M03_PREEXISTING_OR_INHERITED_ACCOUNT_POSITION",
        description="Inherited or pre-existing venue position on the live-canary account",
        authority_class="EXTERNAL_MANUAL_POSITION_APPEARANCE",
        implemented=True,
        enabled=True,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=True,
        would_create_exact_p08_observation=True,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=False,
        disposition=DISPOSITION_EXTERNAL_ONLY,
        currently_viable_for_p08=False,
        upstream_evidence=HISTORICAL_P08_EMPTY_DATA_PACK,
        blocked_by="NOT_OBSERVED_THIS_WINDOW;EMPTY_DATA_IS_NOT_INHERITED_POSITION",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M04_LIVE_CANARY_MINIMUM_EXPOSURE_ENTRY_SUBMIT",
        description="SP-01/SP-02/SP-03 Peak_Trade canary POST /api/v5/trade/order entry",
        authority_class="CANARY_STATE_CREATION",
        implemented=CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
        enabled=bool(SUBMIT_UNLOCKED or LIVE_ENABLED or LIVE_ARMED),
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=True,
        financial_loss_exposure=True,
        would_create_exact_p08_observation=True,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_BLOCKED_CONTRACT,
        currently_viable_for_p08=False,
        upstream_evidence=HISTORICAL_Z2DP_PACK,
        blocked_by=(
            f"G_POSMODE_SUBMIT_BODY_PROVEN={G_POSMODE_SUBMIT_BODY_PROVEN};"
            f"LIVE_AUTHORIZED={LIVE_AUTHORIZED};LIVE_ENABLED={LIVE_ENABLED};"
            f"LIVE_ARMED={LIVE_ARMED};SUBMIT_UNLOCKED={SUBMIT_UNLOCKED};"
            "VENUE_NONZERO_CAPACITY=PROVEN_ZERO_HISTORICAL"
        ),
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M05_GENERAL_LIVE_AUTHORIZED_SUBMIT",
        description="Standing LIVE_AUTHORIZED / GENERAL_LIVE_SUBMIT_UNLOCKED live path",
        authority_class="LIVE_STATE_CREATION",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=True,
        financial_loss_exposure=True,
        would_create_exact_p08_observation=True,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_BLOCKED_AUTH,
        currently_viable_for_p08=False,
        upstream_evidence="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py",
        blocked_by=f"LIVE_AUTHORIZED={LIVE_AUTHORIZED};STANDING_GATES_FALSE",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M06_OKX_EEA_DEMO_TESTNET_EXECUTION",
        description="SP-04/SP-05/SP-06 demo/testnet productive execution port",
        authority_class="TESTNET_STATE_CREATION",
        implemented=True,
        enabled=False,
        owner_authorized=bool(TESTNET_AUTHORIZED),
        credentials_network_permit=False,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=False,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_NOT_P08_CAPABLE,
        currently_viable_for_p08=False,
        upstream_evidence="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py",
        blocked_by="FORBIDDEN_ENVIRONMENTS=DEMO,TESTNET;P08_BOUND_TO_EEA_OKX_LIVE_CANARY_ACCOUNT",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M07_PAPER_SHADOW_SIMULATED_EXECUTION",
        description="Paper, shadow, fixture, or simulated execution ports",
        authority_class="NON_PRODUCTIVE_SIMULATION",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=False,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=False,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=False,
        disposition=DISPOSITION_NOT_P08_CAPABLE,
        currently_viable_for_p08=False,
        upstream_evidence="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py",
        blocked_by="FORBIDDEN_ENVIRONMENTS=PAPER,SHADOW,SIMULATED,FIXTURE",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M08_KRAKEN_LIVE_OR_TESTNET",
        description="SP-10/SP-11 Kraken AddOrder / testnet create_order",
        authority_class="FOREIGN_VENUE",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=False,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=False,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_NOT_P08_CAPABLE,
        currently_viable_for_p08=False,
        upstream_evidence="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#4.9.4",
        blocked_by="WRONG_VENUE;P08_BOUND_TO_OKX_EEA_LIVE_CANARY",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M09_EXECUTION_PIPELINE_SUBMIT_ORDER",
        description="SP-07/SP-08/SP-09 ExecutionPipeline / ExchangeOrderExecutor",
        authority_class="CORE_ADJACENT_EXECUTION_PORT",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=False,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=True,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_NOT_P08_CAPABLE,
        currently_viable_for_p08=False,
        upstream_evidence="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#4.9.4",
        blocked_by="NOT_THE_CANONICAL_P08_LIVE_CANARY_OBSERVATION_ACCOUNT;LIVE_AUTHORIZED=false",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M10_FLATTEN_OR_CLOSE_POSITION",
        description="Dedicated flatten / close-position path",
        authority_class="FLATTEN_RECOVERY",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=True,
        financial_loss_exposure=True,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_NOT_P08_CAPABLE,
        currently_viable_for_p08=False,
        upstream_evidence="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "flatten_submit_transport_v1.py",
        blocked_by="FLATTEN_REDUCES_OR_EXITS;DOES_NOT_CREATE_NONZERO_ENTRY;P08_UNRESOLVED",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M11_UNFILLED_WORKING_ORDER",
        description="Unfilled limit/algo order as a substitute for a position row",
        authority_class="ORDER_STATE_NOT_POSITION",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=True,
        financial_loss_exposure=True,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_INSUFFICIENT,
        currently_viable_for_p08=False,
        upstream_evidence="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.13.5.Z2X",
        blocked_by="Z2X_UNFILLED_ORDER_DOES_NOT_PRODUCE_INDEPENDENT_ACCOUNT_IM_OR_POSITION",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M12_FUNDING_OR_TRANSFER_ONLY",
        description="Account funding, transfer, or asset-balance movement without a fill",
        authority_class="FUNDING_OR_VENUE_STATE",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=True,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_NOT_P08_CAPABLE,
        currently_viable_for_p08=False,
        upstream_evidence=HISTORICAL_Z2DP_PACK,
        blocked_by="FUNDING_IS_NOT_A_POSITION_ROW;MAY_BE_OWNER_PREREQUISITE_FOR_EXTERNAL_CREATE",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M13_OFFLINE_FIXTURE_NONZERO_PAYLOAD",
        description="Fixture or synthetic nonzero positions payload",
        authority_class="OFFLINE_FIXTURE",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=False,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=False,
        disposition=DISPOSITION_INSUFFICIENT,
        currently_viable_for_p08=False,
        upstream_evidence="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "prerequisite_08_resolution_authority_adjudication_v1.py",
        blocked_by="FIXTURE_NONZERO_IS_NOT_PRODUCTIVE_08_PROOF",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M14_IDENTIFIER_RECOVERY_ORDERS_FILLS_ALGO",
        description="Orders-pending/history, fills, or Category-C algo-pending empty channels",
        authority_class="READ_ONLY_IDENTIFIER_RECOVERY",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=False,
        financial_loss_exposure=False,
        would_create_exact_p08_observation=False,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=False,
        disposition=DISPOSITION_INSUFFICIENT,
        currently_viable_for_p08=False,
        upstream_evidence=HISTORICAL_P08_READ_ONLY_PACK,
        blocked_by="CHANNEL_IS_NOT_CANONICAL_P08_AUTHORITY;EMPTY_IS_NOT_CURRENT_NONZERO",
    ),
    StateAppearanceMechanismV1(
        mechanism_id="M15_ROUTE_C_GATED_ENTRY_AFTER_G_POSMODE_AND_FUNDING",
        description="Architecturally complete Route-C create path after remaining blockers close",
        authority_class="CANARY_STATE_CREATION",
        implemented=True,
        enabled=False,
        owner_authorized=False,
        credentials_network_permit=True,
        funding_margin_prerequisites_exist=False,
        pretrade_gates_pass=False,
        changes_real_account_state=True,
        financial_loss_exposure=True,
        would_create_exact_p08_observation=True,
        compatible_single_selected_future_max_positions_1=True,
        touches_canonical_core_trading_logic=False,
        requires_new_pr_before_execution=True,
        disposition=DISPOSITION_BLOCKED_CONTRACT,
        currently_viable_for_p08=False,
        upstream_evidence="src/ops/offline_execution_permission_and_position_creation_"
        "producer_wiring_v1/route_c_create_path_blocker_census_v1.py",
        blocked_by="G_POSMODE_EVIDENCE_EXHAUSTION_FAIL_CLOSED;CREATE_PATH_NOT_AUTHORIZED",
    ),
)


def census_state_appearance_mechanisms_v1() -> dict[str, Any]:
    """Return the bound mechanism census. Not GET and not create."""
    rows = [item.to_dict() for item in MECHANISMS]
    viable = [item for item in MECHANISMS if item.currently_viable_for_p08]
    capable = [item for item in MECHANISMS if item.would_create_exact_p08_observation]
    dispositions = sorted({item.disposition for item in MECHANISMS})
    return {
        "STATE_APPEARANCE_MECHANISM_COUNT": len(MECHANISMS),
        "VIABLE_MECHANISM_COUNT": len(viable),
        "P08_CAPABLE_MECHANISM_COUNT": len(capable),
        "VIABLE_MECHANISM_IDS": [item.mechanism_id for item in viable],
        "DISPOSITIONS_PRESENT": dispositions,
        "MECHANISMS": rows,
        "EXTERNAL_POSITION_ALLOWED_GENERAL": False,
        "EXTERNAL_MAY_SATISFY_P08_IF_CANONICAL_NONZERO_OBSERVED": True,
        "PEAK_TRADE_CREATION_REQUIRED_FOR_P08": False,
        "TESTNET_CAN_SATISFY_P08": False,
        "CANARY_FIRST_PARTY_CREATE_CURRENTLY_VIABLE": False,
        "LIVE_FIRST_PARTY_CREATE_CURRENTLY_VIABLE": False,
        "AVAILABLE_WITHOUT_MUTATION_CURRENTLY_TRUE": False,
    }
