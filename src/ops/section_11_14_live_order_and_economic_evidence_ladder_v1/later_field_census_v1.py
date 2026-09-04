"""Census of remaining §11.14 ladder fields after LIVE_ORDER_PLAN_OBSERVED."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
    LIVE_FEE_OBSERVED_PRODUCER,
    LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
    LIVE_FILL_OBSERVED_PRODUCER,
    LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
    LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
    LIVE_POSITION_RECONCILED_PRODUCER,
    LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_STATUS,
)


def build_later_field_census_v1() -> dict[str, Any]:
    return {
        "schema_version": "section_11_14_later_field_census.v1",
        "LIVE_PRIVATE_READ_ONLY_PROVEN": True,
        "LIVE_ORDER_PLAN_OBSERVED": True,
        "EARLIEST_UNRESOLVED_DEPENDENCY": "LIVE_ACCOUNTING_RECONSTRUCTED",
        "EARLIEST_MUTATION_BOUNDARY": "LIVE_ACCOUNTING_RECONSTRUCTED",
        "MINIMUM_EXTERNAL_ACTION_CLASS": "READ_ONLY_ACCOUNTING_RECONSTRUCTION",
        "rows": [
            {
                "field": "LIVE_ORDER_PLAN_OBSERVED",
                "claim_value": True,
                "canonical_definition": LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
                "producer": (
                    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                    "submit_transport_v1.py::run_canary_submit_transport_v1"
                ),
                "consumer": "§11.14 LIVE_SUBMIT_ACK_OBSERVED",
                "reuse_allowed": False,
                "external_observation_required": True,
                "private_get_required": True,
                "post_required": False,
                "productive_state_mutation_required": False,
                "live_gate_unlock_required": True,
            },
            {
                "field": "LIVE_SUBMIT_ACK_OBSERVED",
                "claim_value": True,
                "canonical_definition": LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_STATUS,
                "post_required": True,
                "minimum_external_action_class": "POST_ORDER_SUBMIT",
                "why_blocked": (
                    "Observed. Producer and criterion remain bound. "
                    "LIVE_ACCOUNTING_RECONSTRUCTED remains ineligible until a separate Owner-GO."
                ),
                "producer": (
                    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                    "submit_ack_observed_adjudication_v1.py::adjudicate_live_submit_ack_observed_v1"
                ),
                "producer_bound": True,
                "proof_criterion_bound": True,
            },
            {
                "field": "LIVE_FILL_OBSERVED",
                "claim_value": True,
                "canonical_definition": LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
                "post_required": False,
                "private_get_required": True,
                "minimum_external_action_class": "READ_ONLY_FILL_OBSERVATION",
                "why_blocked": (
                    "Observed. Producer and criterion remain bound. "
                    "LIVE_ACCOUNTING_RECONSTRUCTED remains ineligible until a separate Owner-GO."
                ),
                "producer": LIVE_FILL_OBSERVED_PRODUCER,
                "producer_bound": True,
                "proof_criterion_bound": True,
            },
            {
                "field": "LIVE_FEE_OBSERVED",
                "claim_value": True,
                "canonical_definition": LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
                "post_required": False,
                "private_get_required": True,
                "minimum_external_action_class": "READ_ONLY_FEE_OBSERVATION",
                "why_blocked": (
                    "Observed. Producer and criterion remain bound. "
                    "LIVE_ACCOUNTING_RECONSTRUCTED remains ineligible until a separate Owner-GO."
                ),
                "producer": LIVE_FEE_OBSERVED_PRODUCER,
                "producer_bound": True,
                "proof_criterion_bound": True,
            },
            {
                "field": "LIVE_POSITION_RECONCILED",
                "claim_value": True,
                "canonical_definition": LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
                "post_required": False,
                "private_get_required": True,
                "minimum_external_action_class": "READ_ONLY_POSITION_RECONCILIATION",
                "why_blocked": (
                    "Reconciled. Producer and criterion remain bound. "
                    "LIVE_ACCOUNTING_RECONSTRUCTED remains ineligible until a separate Owner-GO."
                ),
                "producer": LIVE_POSITION_RECONCILED_PRODUCER,
                "producer_bound": True,
                "proof_criterion_bound": True,
            },
            {
                "field": "LIVE_ACCOUNTING_RECONSTRUCTED",
                "claim_value": False,
                "canonical_definition": (
                    "Current Live accounting reconstructed from the observed Live economic path."
                ),
                "why_blocked": (
                    "Requires a separate Owner-GO after LIVE_POSITION_RECONCILED=true. "
                    "This GO forbids accounting reconstruction."
                ),
            },
            {
                "field": "LIVE_RESTART_RECONSTRUCTED",
                "claim_value": False,
                "canonical_definition": (
                    "Current Live restart reconstruction from persisted Live state."
                ),
                "why_blocked": "Predecessor accounting reconstruction is false.",
            },
            {
                "field": "LIVE_AUTONOMOUS_RECOVERY_OBSERVED",
                "claim_value": False,
                "canonical_definition": (
                    "Current Live autonomous recovery observation on the Live path."
                ),
                "why_blocked": "Predecessor restart reconstruction is false.",
            },
            {
                "field": "LIVE_END_TO_END_EVIDENCE_PROVEN",
                "claim_value": False,
                "canonical_definition": (
                    "Conjunction of the complete §11.14 Live evidence ladder."
                ),
                "why_blocked": "Earlier observed/proven fields remain false.",
            },
            {
                "field": "SECTION_11_14_COMPLETE",
                "claim_value": False,
                "canonical_definition": "True iff every §11.14 ladder field is true.",
                "why_blocked": "LIVE_END_TO_END_EVIDENCE_PROVEN is false.",
            },
        ],
    }
