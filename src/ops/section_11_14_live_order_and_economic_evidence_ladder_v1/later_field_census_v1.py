"""Census of remaining §11.14 ladder fields after LIVE_ORDER_PLAN_OBSERVED."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
)


def build_later_field_census_v1() -> dict[str, Any]:
    return {
        "schema_version": "section_11_14_later_field_census.v1",
        "LIVE_PRIVATE_READ_ONLY_PROVEN": True,
        "LIVE_ORDER_PLAN_OBSERVED": True,
        "EARLIEST_UNRESOLVED_DEPENDENCY": "LIVE_SUBMIT_ACK_OBSERVED",
        "EARLIEST_MUTATION_BOUNDARY": "LIVE_SUBMIT_ACK_OBSERVED",
        "MINIMUM_EXTERNAL_ACTION_CLASS": "POST_ORDER_SUBMIT",
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
                "claim_value": False,
                "canonical_definition": (
                    "Current venue acknowledgement of a Peak_Trade Live canary submit "
                    "bound to the observed order plan. Requires POST."
                ),
                "post_required": True,
                "minimum_external_action_class": "POST_ORDER_SUBMIT",
                "why_blocked": (
                    "LIVE_ORDER_PLAN_OBSERVED is true. Canonical ACK requires POST of "
                    "the observed plan. This GO forbids POST."
                ),
            },
            {
                "field": "LIVE_FILL_OBSERVED",
                "claim_value": False,
                "canonical_definition": (
                    "Current venue fill bound to the Peak_Trade Live submit identity."
                ),
                "post_required": True,
                "why_blocked": "Requires a Live fill after submit ACK. POST unauthorized.",
            },
            {
                "field": "LIVE_FEE_OBSERVED",
                "claim_value": False,
                "canonical_definition": (
                    "Current venue fee bound to the observed Live fill/submit identity."
                ),
                "post_required": True,
                "why_blocked": "Requires a Live fee after fill. POST unauthorized.",
            },
            {
                "field": "LIVE_POSITION_RECONCILED",
                "claim_value": False,
                "canonical_definition": (
                    "Current Live position reconciled to the observed fill/fee path. "
                    "LIVE_RECONCILIATION_PROVEN is not this field."
                ),
                "why_blocked": "Predecessor fill/fee observations are false.",
            },
            {
                "field": "LIVE_ACCOUNTING_RECONSTRUCTED",
                "claim_value": False,
                "canonical_definition": (
                    "Current Live accounting reconstructed from the observed Live economic path."
                ),
                "why_blocked": "Predecessor position reconciliation is false.",
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
