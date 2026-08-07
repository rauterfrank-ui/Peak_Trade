"""Canonical Intent schema parity — consume existing CanonicalOrderIntentV1 unchanged."""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from src.governance.canonical_order_intent_v1 import (
    CONTRACT_NAME as INTENT_CONTRACT_NAME,
    CONTRACT_VERSION as INTENT_CONTRACT_VERSION,
    CanonicalOrderIntentV1,
    SCHEMA_VERSION as INTENT_SCHEMA_VERSION,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.constants_v1 import (
    CANONICAL_INTENT_OWNER,
    ONE_CANONICAL_INTENT_SCHEMA,
)

# Cap 11.1 does not introduce a parallel intent schema. The sole canonical
# intent schema remains CanonicalOrderIntentV1.
CANONICAL_INTENT_SCHEMA_ID = INTENT_CONTRACT_NAME
CANONICAL_INTENT_SCHEMA_VERSION = INTENT_SCHEMA_VERSION
CANONICAL_INTENT_CONTRACT_VERSION = INTENT_CONTRACT_VERSION


REQUIRED_INTENT_FIELDS: tuple[str, ...] = (
    "intent_id",
    "intent_version",
    "decision_id",
    "instrument_id",
    "trading_epoch",
    "canonical_trading_logic_version",
    "side",
    "intent_action",
    "quantity",
    "reduce_only",
    "position_effect",
    "execution_eligible",
    "submission_authorized",
    "authority_effect",
    "network_effect",
    "credential_effect",
    "semantic_digest",
)


def canonical_intent_field_names_v1() -> tuple[str, ...]:
    return tuple(f.name for f in fields(CanonicalOrderIntentV1))


def prove_one_canonical_intent_schema_v1() -> dict[str, Any]:
    names = canonical_intent_field_names_v1()
    missing = [f for f in REQUIRED_INTENT_FIELDS if f not in names]
    return {
        "ok": ONE_CANONICAL_INTENT_SCHEMA and not missing,
        "ONE_CANONICAL_INTENT_SCHEMA": True,
        "schema_id": CANONICAL_INTENT_SCHEMA_ID,
        "schema_version": CANONICAL_INTENT_SCHEMA_VERSION,
        "contract_version": CANONICAL_INTENT_CONTRACT_VERSION,
        "owner": CANONICAL_INTENT_OWNER,
        "parallel_intent_schema_introduced": False,
        "required_fields_present": not missing,
        "missing_required_fields": missing,
        "field_count": len(names),
        "CORE_LOGIC_CHANGE": False,
    }


def assert_intent_is_canonical_order_intent_v1(intent: object) -> CanonicalOrderIntentV1:
    if not isinstance(intent, CanonicalOrderIntentV1):
        raise TypeError(
            "PHASE11_INTENT_SCHEMA_VIOLATION:"
            "only CanonicalOrderIntentV1 is the canonical intent schema"
        )
    return intent
