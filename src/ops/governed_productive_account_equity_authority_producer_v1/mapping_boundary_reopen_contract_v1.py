"""MAPPING_BOUNDARY_REOPEN_CONTRACT_V1.

Mechanism exists. Mapping remains closed in this persist.
Open only when an acceptable C17+ candidate is Owner-ratified by exact id.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.governed_productive_account_equity_authority_producer_v1.source_promotion_state_machine_v1 import (
    STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
    STATE_OWNER_RATIFIED,
    assert_owner_ratification_gate_v1,
)

SCHEMA_CLASS = "MAPPING_BOUNDARY_REOPEN_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
MAPPING_REOPEN_MECHANISM_EXISTS = True
MAPPING_BOUNDARY_CURRENTLY_OPEN = False
CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING = False
C01_C16_REJECTION_STILL_BINDING = True
C01_C16_REVIVAL_ALLOWED = False
OWNER_RATIFICATION_REQUIRED = True


class MappingBoundaryReopenContractError(ValueError):
    """Fail-closed mapping-boundary reopen violation."""


@dataclass(frozen=True)
class MappingBoundaryReopenContractV1:
    reopen_contract_id: str
    mapping_reopen_mechanism_exists: str
    mapping_boundary_currently_open: str
    canonically_valid_account_equity_source_mapping: str
    new_candidate_acceptable_for_owner_ratification: str
    owner_explicitly_ratifies_exact_candidate_id: str
    exact_candidate_id: str
    c01_c16_rejection_still_binding: str
    c01_c16_revival_allowed: str
    authority_effect: str
    source_selected: str
    mapping_proven: str
    governed_producer_created: str
    productive_runtime_binding_added: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise MappingBoundaryReopenContractError(f"REOPEN_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise MappingBoundaryReopenContractError(f"REOPEN_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise MappingBoundaryReopenContractError(f"REOPEN_FIELD_MISSING:{field}")
    return text


def evaluate_mapping_boundary_reopen_v1(
    *,
    reopen_contract_id: str,
    new_candidate_acceptable_for_owner_ratification: bool,
    owner_explicitly_ratifies_exact_candidate_id: bool,
    exact_candidate_id: str,
    persist_currently_open: bool = False,
) -> MappingBoundaryReopenContractV1:
    cid = _require_non_empty_str(field="reopen_contract_id", raw=reopen_contract_id)
    candidate_id = _require_non_empty_str(field="exact_candidate_id", raw=exact_candidate_id)
    acceptable = new_candidate_acceptable_for_owner_ratification is True
    owner_ratifies = owner_explicitly_ratifies_exact_candidate_id is True
    if persist_currently_open is True:
        raise MappingBoundaryReopenContractError("PR1_MAPPING_BOUNDARY_MUST_REMAIN_CLOSED")
    if owner_ratifies:
        assert_owner_ratification_gate_v1(
            current=STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
            nxt=STATE_OWNER_RATIFIED,
            owner_explicitly_ratifies_exact_candidate_id=True,
        )
        if not acceptable:
            raise MappingBoundaryReopenContractError(
                "OWNER_RATIFICATION_WITHOUT_ACCEPTABLE_CANDIDATE_FORBIDDEN"
            )
        raise MappingBoundaryReopenContractError(f"PR1_OWNER_RATIFICATION_FORBIDDEN:{candidate_id}")
    open_now = False
    return MappingBoundaryReopenContractV1(
        reopen_contract_id=cid,
        mapping_reopen_mechanism_exists="true",
        mapping_boundary_currently_open="true" if open_now else "false",
        canonically_valid_account_equity_source_mapping="false",
        new_candidate_acceptable_for_owner_ratification=("true" if acceptable else "false"),
        owner_explicitly_ratifies_exact_candidate_id="false",
        exact_candidate_id=candidate_id,
        c01_c16_rejection_still_binding="true",
        c01_c16_revival_allowed="false",
        authority_effect=AUTHORITY_EFFECT,
        source_selected="false",
        mapping_proven="false",
        governed_producer_created="false",
        productive_runtime_binding_added="false",
    )


def future_reopen_predicate_v1(
    *,
    new_candidate_acceptable_for_owner_ratification: bool,
    owner_explicitly_ratifies_exact_candidate_id: bool,
) -> bool:
    return (
        new_candidate_acceptable_for_owner_ratification is True
        and owner_explicitly_ratifies_exact_candidate_id is True
    )
