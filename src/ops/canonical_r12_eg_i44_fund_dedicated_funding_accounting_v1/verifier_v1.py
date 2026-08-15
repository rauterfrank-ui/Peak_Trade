"""Fail-closed verifier for R12 EG-I44 dedicated funding accounting v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.constants_v1 import (
    ACCOUNTING_LOGIC_CHANGE,
    ACCOUNTING_WRITER,
    ACTIVATED,
    AUTHORITY_EFFECT,
    BACKTEST_FUNDING_MODEL_IS_G16_PROOF,
    CANARY_EXECUTE,
    CANONICAL_ACCOUNTING_KERNEL,
    CANONICAL_ACCOUNTING_OWNER,
    CAPABILITY_ID,
    COMPARISON_G16_ID,
    COMPARISON_G16_SEMANTICALLY_DISTINCT,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    DONE_CRITERION_STRUCTURAL,
    FIELD_PRESENT_DOES_NOT_PROVE_ACCOUNTING,
    FUNDING_ACCOUNTING_ACTIVATED,
    FUNDING_ACCOUNTING_PROVEN,
    FUNDING_APPLICATION_OWNER,
    FUNDING_CLAIM_FAIL_CLOSED,
    FUNDING_ECONOMICS_PROVEN,
    FUNDING_FIELD_OWNER,
    FUNDING_IMPLEMENTATION_AUTHORIZED,
    FUNDING_OBSERVATION_OWNER,
    FUNDING_PNL_PROVEN,
    FUNDING_RECON_OWNER,
    G13_STATUS,
    G13_UNCHANGED,
    G16_CLOSED,
    I17_SHADOW_FUNDING_IS_G16_PROOF,
    I44_OUT_OF_SCOPE_FOREVER,
    I44_STATUS,
    IG_I44_FUNDING_IF_ACTIVATED_IMPLEMENTED,
    LIVE_AUTHORIZED,
    MASTER_G16_STATUS,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    NETWORK_EFFECT,
    OD_I44_DECISION,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PRODUCTIVE_CALLER_EXISTS,
    R6_RUNTIME_AUTHORIZED,
    R6_S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    REMEDIATION_ID,
    REQUIRED_OWNER_RELPATHS,
    RESEARCH_FUNDING_IS_PRODUCTIVE_PROOF,
    RESEARCH_TO_ACCOUNTING_BYPASS_FORBIDDEN,
    RISK_LOGIC_CHANGE,
    RUNTIME_EFFECT,
    SINGLE_FUTURE_LIVE_PROOF,
    SINGLE_SELECTED_FUTURE,
    SOURCE_GAP_IDS,
    TARGET_BINDING,
    TARGET_DAG_DONE_CRITERION,
    TESTNET_AUTHORIZED,
    TRADING_GRANT,
    ZERO_FUNDING_IMPLICIT_FALLBACK_FORBIDDEN,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.contract_v1 import (
    REQUIRED_CONTRACT_ITEM_IDS,
    STRUCTURAL_CONTRACT,
    require_contract_item,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.dimensions_v1 import (
    FUNDING_DIMENSIONS,
    REQUIRED_DIMENSION_IDS,
    require_dimension,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.evidence_pack_v1 import (
    EVIDENCE_PACK_CHAIN,
    REQUIRED_EVIDENCE_STEP_IDS,
    require_evidence_step,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.models_v1 import (
    ContractItemStatus,
    R12EgI44FundError,
    STRUCTURAL_CLOSABLE_STATUSES,
)
from src.ops.productive_futures_accounting_runtime_binding_v1 import constants_v1 as cap31
from src.ops.productive_reconciliation_runtime_binding_v1 import constants_v1 as cap11
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23

_PACKAGE_REL = Path("src") / "ops" / "canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1"
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.orders",
        "src.live",
        "src.intents",
        "src.execution_simple",
        "src.research",
        "src.backtest.funding_model_v1",
    }
)


def _reject(message: str) -> None:
    raise R12EgI44FundError(message)


def _require(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        _reject(f"config_field_mismatch:{key}:expected={expected!r}:actual={actual!r}")


def _iter_import_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return tuple(names)


def validate_layer_config_v1(payload: Mapping[str, Any]) -> None:
    _require(payload, "activated", False)
    _require(payload, "authority_effect", AUTHORITY_EFFECT)
    _require(payload, "canary_execute", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "comparison_g16_semantically_distinct", True)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", False)
    _require(payload, "accounting_logic_change", False)
    _require(payload, "done_criterion_structural", DONE_CRITERION_STRUCTURAL)
    _require(payload, "field_present_does_not_prove_accounting", True)
    _require(payload, "funding_accounting_activated", False)
    _require(payload, "funding_accounting_proven", False)
    _require(payload, "funding_implementation_authorized", False)
    _require(payload, "g16_closed", False)
    _require(payload, "g13_unchanged", True)
    _require(payload, "i44_out_of_scope_forever", False)
    _require(payload, "ig_i44_funding_if_activated_implemented", False)
    _require(payload, "live_authorized", False)
    _require(payload, "max_positions_effective", 1)
    _require(payload, "multi_future_runtime_authorized", False)
    _require(payload, "multi_future_runtime_implemented", False)
    _require(payload, "network_effect", False)
    _require(payload, "od_i44_decision", OD_I44_DECISION)
    _require(payload, "order_effect", ORDER_EFFECT)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "r6_s3_runtime_implementation_authorized", False)
    _require(payload, "research_funding_is_productive_proof", False)
    _require(payload, "runtime_effect", False)
    _require(payload, "single_future_live_proof", False)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "target_binding", TARGET_BINDING)
    _require(payload, "testnet_authorized", False)
    _require(payload, "trading_grant", False)


def assert_package_import_boundary_v1(root: Path | None = None) -> None:
    package = (root or repo_root()) / _PACKAGE_REL
    for path in sorted(package.glob("*.py")):
        for name in _iter_import_names(path):
            for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                if name == forbidden or name.startswith(f"{forbidden}."):
                    _reject(f"forbidden_import:{path.name}:{name}")


def assert_required_owners_present_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    for rel in REQUIRED_OWNER_RELPATHS:
        if not (base / rel).is_file():
            _reject(f"owner_file_missing:{rel}")


def assert_g16_naming_collision_is_distinct_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    master = (base / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    if "`G16` Funding proof" not in master and "G16` Funding proof" not in master:
        if "G16 Funding proof" not in master:
            _reject("master_g16_funding_proof_missing")
    if "INSUFFICIENT_EVIDENCE" not in master:
        _reject("master_g16_insufficient_evidence_missing")
    gates = (base / "src/meta/learning_loop/comparison_ssot_v1/comparison_gates_v1.py").read_text(
        encoding="utf-8"
    )
    if COMPARISON_G16_ID not in gates:
        _reject("comparison_g16_id_missing")
    if COMPARISON_G16_ID in master and "Funding proof" in master:
        # Master may mention the collision in overlays; identity strings must stay distinct.
        pass
    if COMPARISON_G16_ID == "G16 Funding proof":
        _reject("comparison_g16_collapsed_into_master_g16")


def assert_cap31_does_not_apply_funding_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    engine = (
        base / "src/ops/productive_futures_accounting_runtime_binding_v1/accounting_engine_v1.py"
    )
    text = engine.read_text(encoding="utf-8")
    if "apply_funding_payment" in text:
        _reject("cap31_engine_calls_apply_funding_payment")
    kernel = (base / "src/execution/paper/futures_accounting.py").read_text(encoding="utf-8")
    if "def apply_funding_payment" not in kernel:
        _reject("kernel_helper_missing")
    if "funding_pnl" not in kernel:
        _reject("kernel_funding_pnl_field_missing")
    recon = (
        base / "src/ops/productive_reconciliation_runtime_binding_v1/constants_v1.py"
    ).read_text(encoding="utf-8")
    if "funding" in recon.lower():
        _reject("cap11_unexpected_funding_owner")


def assert_existing_runtime_bindings_v1() -> None:
    if cap23.MAX_POSITIONS_EFFECTIVE != 1:
        _reject("max_positions_not_1")
    if cap11.PHASE1_MAX_OPEN_POSITIONS != 1:
        _reject("recon_max_open_positions_not_1")
    if any(
        (
            cap23.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap31.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap11.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap72.MULTI_FUTURE_RUNTIME_AUTHORIZED,
        )
    ):
        _reject("multi_future_runtime_authorized_true")
    if cap31.SINGLE_WRITER_IDENTITY != ACCOUNTING_WRITER:
        _reject("accounting_writer_drift")
    if cap31.CANONICAL_KERNEL_OWNER != CANONICAL_ACCOUNTING_KERNEL:
        _reject("accounting_kernel_drift")
    if cap23.LIVE_AUTHORIZED or cap72.LIVE_ORDERS:
        _reject("live_or_orders_authorized")


def assert_structural_contract_complete_v1() -> None:
    present = tuple(row.item_id for row in STRUCTURAL_CONTRACT)
    if present != REQUIRED_CONTRACT_ITEM_IDS:
        _reject(f"structural_item_mismatch:expected={REQUIRED_CONTRACT_ITEM_IDS}:actual={present}")
    for item_id in REQUIRED_CONTRACT_ITEM_IDS:
        row = require_contract_item(item_id)
        if row.status not in STRUCTURAL_CLOSABLE_STATUSES:
            _reject(f"structural_item_not_closable:{item_id}:{row.status.value}")
    if require_contract_item("fail_closed_behavior").status is not ContractItemStatus.CLOSED_PROVEN:
        _reject("fail_closed_not_proven")
    if require_contract_item("actual_vs_estimated_funding").status is not (
        ContractItemStatus.CLOSED_PROVEN
    ):
        _reject("actual_vs_estimated_not_proven")


def assert_dimensions_and_evidence_do_not_close_g16_v1() -> None:
    present = tuple(row.dimension_id for row in FUNDING_DIMENSIONS)
    if present != REQUIRED_DIMENSION_IDS:
        _reject(f"dimension_mismatch:expected={REQUIRED_DIMENSION_IDS}:actual={present}")
    for dim_id in REQUIRED_DIMENSION_IDS:
        row = require_dimension(dim_id)
        if row.claim_allowed_today:
            _reject(f"claim_allowed_today:{dim_id}")
        if row.current_authority_effect != "NONE":
            _reject(f"dimension_authority_not_none:{dim_id}")
    if require_dimension("ACTUAL_FUNDING_PAYMENT").status is not ContractItemStatus.MISSING:
        _reject("actual_payment_not_missing")
    if require_dimension("PRODUCTIVE_ACCOUNTING_CLAIM").claim_allowed_today:
        _reject("productive_claim_allowed")
    steps = tuple(row.item_id for row in EVIDENCE_PACK_CHAIN)
    if steps != REQUIRED_EVIDENCE_STEP_IDS:
        _reject(f"evidence_step_mismatch:expected={REQUIRED_EVIDENCE_STEP_IDS}:actual={steps}")
    if require_evidence_step("verifier_pass").status is ContractItemStatus.CLOSED_PROVEN:
        _reject("g16_verifier_pass_claimed")
    if require_evidence_step("actual_venue_account_funding_event").status is not (
        ContractItemStatus.MISSING
    ):
        _reject("actual_event_not_missing")


def evaluate_r12_eg_i44_fund_dedicated_funding_accounting_v1(
    *, root: Path | None = None
) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_import_boundary_v1(root)
    assert_required_owners_present_v1(root)
    assert_g16_naming_collision_is_distinct_v1(root)
    assert_cap31_does_not_apply_funding_v1(root)
    assert_existing_runtime_bindings_v1()
    assert_structural_contract_complete_v1()
    assert_dimensions_and_evidence_do_not_close_g16_v1()
    if any(
        (
            ACTIVATED,
            PRODUCTIVE_CALLER_EXISTS,
            TRADING_GRANT,
            LIVE_AUTHORIZED,
            TESTNET_AUTHORIZED,
            CANARY_EXECUTE,
            NETWORK_EFFECT,
            R6_RUNTIME_AUTHORIZED,
            R6_S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
            MULTI_FUTURE_RUNTIME_AUTHORIZED,
            MULTI_FUTURE_RUNTIME_IMPLEMENTED,
            SINGLE_FUTURE_LIVE_PROOF,
            CORE_LOGIC_CHANGE,
            RISK_LOGIC_CHANGE,
            ACCOUNTING_LOGIC_CHANGE,
            FUNDING_ACCOUNTING_ACTIVATED,
            FUNDING_IMPLEMENTATION_AUTHORIZED,
            FUNDING_ACCOUNTING_PROVEN,
            FUNDING_ECONOMICS_PROVEN,
            FUNDING_PNL_PROVEN,
            G16_CLOSED,
            I44_OUT_OF_SCOPE_FOREVER,
            IG_I44_FUNDING_IF_ACTIVATED_IMPLEMENTED,
            RESEARCH_FUNDING_IS_PRODUCTIVE_PROOF,
            I17_SHADOW_FUNDING_IS_G16_PROOF,
            BACKTEST_FUNDING_MODEL_IS_G16_PROOF,
            RUNTIME_EFFECT,
        )
    ):
        _reject("authority_or_g16_or_activation_flag_raised")
    if MAX_POSITIONS_EFFECTIVE != 1:
        _reject("single_future_binding_lost")
    if not (
        COMPARISON_G16_SEMANTICALLY_DISTINCT
        and FIELD_PRESENT_DOES_NOT_PROVE_ACCOUNTING
        and FUNDING_CLAIM_FAIL_CLOSED
        and RESEARCH_TO_ACCOUNTING_BYPASS_FORBIDDEN
        and ZERO_FUNDING_IMPLICIT_FALLBACK_FORBIDDEN
        and G13_UNCHANGED
    ):
        _reject("doctrine_flags_missing")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "canonical_accounting_owner": CANONICAL_ACCOUNTING_OWNER,
        "capability_id": CAPABILITY_ID,
        "comparison_g16_semantically_distinct": COMPARISON_G16_SEMANTICALLY_DISTINCT,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "accounting_logic_change": ACCOUNTING_LOGIC_CHANGE,
        "done_criterion_structural": DONE_CRITERION_STRUCTURAL,
        "duplicate_accounting_writer_found": False,
        "duplicate_execution_writer_found": False,
        "eg_i44_fund_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY_STRUCTURAL_G16_STILL_OPEN",
        "field_present_does_not_prove_accounting": FIELD_PRESENT_DOES_NOT_PROVE_ACCOUNTING,
        "funding_accounting_activated": FUNDING_ACCOUNTING_ACTIVATED,
        "funding_application_owner": FUNDING_APPLICATION_OWNER,
        "funding_claim_fail_closed": FUNDING_CLAIM_FAIL_CLOSED,
        "funding_evidence_identity_status": require_contract_item(
            "evidence_identity_lineage"
        ).status.value,
        "funding_field_owner": FUNDING_FIELD_OWNER,
        "funding_implementation_authorized": FUNDING_IMPLEMENTATION_AUTHORIZED,
        "funding_observation_owner": FUNDING_OBSERVATION_OWNER,
        "funding_paid_or_received_status": require_dimension(
            "FUNDING_PAID_OR_RECEIVED"
        ).status.value,
        "funding_pnl_status": require_dimension("FUNDING_PNL").status.value,
        "funding_rate_observation_status": require_dimension(
            "FUNDING_RATE_OBSERVATION"
        ).status.value,
        "funding_recon_owner": FUNDING_RECON_OWNER,
        "funding_restart_recon_status": require_contract_item(
            "restart_persistence_reconstruction"
        ).status.value,
        "funding_structural_contract_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "funding_verifier_status": require_evidence_step("verifier_pass").status.value,
        "actual_funding_payment_status": require_dimension("ACTUAL_FUNDING_PAYMENT").status.value,
        "g13_status": G13_STATUS,
        "g13_unchanged": G13_UNCHANGED,
        "g16_closed": G16_CLOSED,
        "i44_status": I44_STATUS,
        "master_g16_status": MASTER_G16_STATUS,
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "multi_future_runtime_implemented": MULTI_FUTURE_RUNTIME_IMPLEMENTED,
        "network_effect": NETWORK_EFFECT,
        "od_i44_decision": OD_I44_DECISION,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "r6_s3_runtime_implementation_authorized": R6_S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
        "research_funding_is_productive_proof": RESEARCH_FUNDING_IS_PRODUCTIVE_PROOF,
        "research_to_accounting_bypass_found": False,
        "research_to_intent_bypass_found": False,
        "runtime_effect": RUNTIME_EFFECT,
        "single_future_live_proof": SINGLE_FUTURE_LIVE_PROOF,
        "single_selected_future": SINGLE_SELECTED_FUTURE,
        "smallest_missing_contract_gap": "NONE_FOR_STRUCTURAL_CONTRACT",
        "target_binding": TARGET_BINDING,
        "target_dag_done_criterion": TARGET_DAG_DONE_CRITERION,
        "target_dag_done_criterion_met": False,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "verdict": "PASS_R12_EG_I44_FUND_STRUCTURAL_CONTRACT_V1",
        "canonical_accounting_kernel": CANONICAL_ACCOUNTING_KERNEL,
    }
    return MappingProxyType(claims)
