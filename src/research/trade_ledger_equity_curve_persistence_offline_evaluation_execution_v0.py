"""Trade ledger equity curve persistence offline evaluation execution v0 owner contract.

Fail-closed owner contract for bounded offline evaluation with TRADE_LEDGER_V1.jsonl and
EQUITY_CURVE_V1.jsonl persistence under ratified evidence class
TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0. Reuses canonical evidence-class export
field contracts and primary evidence manifest policy. No runtime, order, credentials,
arming, or authority effect. Execution requires separate operator GO after binding
materialization merge and green checks.
"""

from __future__ import annotations

PACKAGE_MARKER = "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "trade_ledger_equity_curve_persistence_offline_evaluation_execution.v0"
EXECUTION_ID = "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0"
EXECUTION_VERSION = "v0"

OPERATOR_GO = "GO_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

EXECUTION_AUTHORIZED = False
EVALUATION_AUTHORIZED = False
RUNTIME_AUTHORIZED = False
ORDERS_ALLOWED = False
CREDENTIALS_REQUIRED = False

EVIDENCE_CLASS_ID = "TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0"
STRATEGY_BINDING_REF = "trend_following/v1"
STRATEGY_BINDING_DIGEST = "ea3bde558a2ffd903ed7b7f678cb0cf0a8a4b1f1bb7f5978f7b5bc8f69ab8478"

BINDING_MATERIALIZATION_CONFIG_REL = (
    "config/research/trade_ledger_equity_curve_execution_binding_materialization_v0.json"
)
PARENT_OFFLINE_EVALUATION_SCOPE_REL = (
    "config/research/trade_ledger_equity_curve_persistence_offline_evaluation_scope_v0.json"
)
EVIDENCE_CLASS_SCOPE_REL = "config/research/trade_ledger_equity_curve_evidence_class_scope_v0.json"
FLEET_BINDING_COMPLETION_REL = (
    "config/research/final_research_fleet_versioned_binding_completion_v0.json"
)
MANIFEST_POLICY_MODULE_REL = "scripts/ops/primary_evidence_retention_v0.py"

TRADE_LEDGER_V1_JSONL_EXPORT_OWNER_REF = (
    "config/research/trade_ledger_equity_curve_evidence_class_scope_v0.json"
)
EQUITY_CURVE_V1_JSONL_EXPORT_OWNER_REF = (
    "config/research/trade_ledger_equity_curve_evidence_class_scope_v0.json"
)

ALLOWED_OUTPUT_ARTIFACTS = ("TRADE_LEDGER_V1.jsonl", "EQUITY_CURVE_V1.jsonl")
NO_OUTPUT_JSONL_MATERIALIZED_IN_REPO = True

FAIL_CLOSED_REASON = "EXECUTION_BINDING_MATERIALIZED_NOT_AUTHORIZED"


def assert_execution_not_authorized_v0() -> None:
    """Fail closed until separate operator GO after binding materialization merge."""
    raise RuntimeError(FAIL_CLOSED_REASON)
