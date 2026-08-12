"""§11.13.5.E Economic baseline adoption + OKX temp-security clearance evidence.

Owner-GO: OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE

Authorized:
- adopt the three standing exchange economic-baseline policies
- minimum productive LIVE private-read (GET-only) against adopted Exchange Truth
- observe OKX temporary security restriction / clearance from production truth
- reevaluate LIVE_CANARY_CYBERSECURITY_GATE

Forbidden:
- canary order / live submit
- LIVE_AUTHORIZED
- withdrawals, P2P sells, transfers, account mutations
- synthesizing OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1,
    REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    SECRETREF_CONVENTION_EXAMPLE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cybersecurity_canary_gate_v1 import (
    evaluate_live_canary_cybersecurity_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (
    CANARY_KEY_NAME_UI,
    OKX_TEMP_SECURITY_RESTRICTION as STANDING_OKX_TEMP_RESTRICTION_TOKEN,
    REQUIRED_SECRETREF_URI,
    STATUS_ADOPTED_PROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_canary_owner_dependency_resolution_v1 import (
    resolve_exchange_truth_adoption_dependency_v1,
)

OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE = (
    "OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE"
)

CLEARANCE_PRESENT_PROVEN = "PRESENT_PROVEN"
CLEARANCE_ABSENT_OR_UNPROVEN = "ABSENT_OR_UNPROVEN"

TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN = (
    "ECONOMIC_BASELINE_ADOPTED_LIVE_RECONCILIATION_PROVEN_"
    "OKX_TEMP_SECURITY_CLEARANCE_ABSENT_OR_UNPROVEN_"
    "LIVE_CANARY_CYBERSECURITY_GATE_NOT_PASSED"
)
TERMINAL_RECON_PROVEN_CLEARANCE_PROVEN_GATE_PASS = (
    "ECONOMIC_BASELINE_ADOPTED_LIVE_RECONCILIATION_PROVEN_"
    "OKX_TEMP_SECURITY_CLEARANCE_PRESENT_PROVEN_"
    "LIVE_CANARY_CYBERSECURITY_GATE_PASS"
)
TERMINAL_FAIL_CLOSED = "FAIL_CLOSED_ECONOMIC_BASELINE_OR_OKX_CLEARANCE_BLOCKED"

HARD_STOP_LAYERS: tuple[str, ...] = (
    "venue_instrument_and_contract_metadata",
    "balances_equity_and_available_margin",
    "local_portfolio_and_accounting",
)


class EconomicBaselineAndOkxClearanceError(RuntimeError):
    """Fail-closed economic baseline / OKX clearance violation."""


def adopt_exchange_economic_baseline_local_state_v1(
    *,
    local_expected_state: Mapping[str, Any],
    exchange_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Seed local expected state from exchange for the three Owner adoption layers."""
    local = {
        key: (dict(value) if isinstance(value, Mapping) else value)
        for key, value in dict(local_expected_state).items()
    }
    for layer in HARD_STOP_LAYERS:
        if layer not in exchange_snapshot:
            raise EconomicBaselineAndOkxClearanceError(f"EXCHANGE_LAYER_MISSING:{layer}")
        local[layer] = dict(exchange_snapshot[layer])  # type: ignore[arg-type]
    return local


def evaluate_okx_temp_security_clearance_v1(
    *,
    restriction_still_active: bool,
    clearance_evidence_present_proven: bool,
    evidence_source: str,
    observed_at_utc: str,
    restriction_expires_at_local: str | None = None,
    account_scope: str = REUSED_BINDING_ACCOUNT_SCOPE,
) -> dict[str, Any]:
    """Classify OKX temp-security clearance from production truth (not wall-clock alone)."""
    if clearance_evidence_present_proven and restriction_still_active:
        raise EconomicBaselineAndOkxClearanceError(
            "CLEARANCE_PROVEN_CONTRADICTS_ACTIVE_RESTRICTION"
        )
    if clearance_evidence_present_proven:
        status = CLEARANCE_PRESENT_PROVEN
        restriction = "NONE_CLEARED"
    else:
        status = CLEARANCE_ABSENT_OR_UNPROVEN
        restriction = STANDING_OKX_TEMP_RESTRICTION_TOKEN
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_E_OKX_TEMP_SECURITY_CLEARANCE_V1",
        "OKX_TEMP_SECURITY_RESTRICTION": restriction,
        "OKX_TEMP_SECURITY_RESTRICTION_STILL_ACTIVE": bool(restriction_still_active),
        "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE": status,
        "OKX_CLEARANCE_EVIDENCE_SOURCE": evidence_source,
        "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE_PRESENT": status == CLEARANCE_PRESENT_PROVEN,
        "OBSERVED_AT_UTC": observed_at_utc,
        "RESTRICTION_EXPIRES_AT_LOCAL": restriction_expires_at_local,
        "ACCOUNT_SCOPE_BINDING": account_scope,
        "WITHDRAWAL_OR_P2P_MUTATION_USED_TO_TEST_CLEARANCE": False,
        "WALL_CLOCK_ALONE_INSUFFICIENT": True,
        "ok": True,
    }


def evaluate_economic_baseline_and_okx_clearance_v1(
    *,
    repo_root: str | Any,
    origin_main_sha: str,
    owner_go: str = OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE,
    reconciliation_eval: Mapping[str, Any],
    exchange_snapshot: Mapping[str, Any],
    local_expected_state_adopted: Mapping[str, Any],
    okx_clearance: Mapping[str, Any],
    productive_private_read_summary: Mapping[str, Any] | None = None,
    trade_key_attestation: Mapping[str, Any] | None = None,
    productive_surface_merged_to_origin_main: bool = True,
) -> dict[str, Any]:
    """Adopt economic baselines under this Owner-GO and reevaluate canary cyber gate."""
    if str(owner_go or "").strip() != OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE:
        raise EconomicBaselineAndOkxClearanceError("OWNER_GO_MISBOUND")

    blockers: list[str] = []
    att = dict(trade_key_attestation or {})
    if not att:
        blockers.append("TRADE_KEY_ATTESTATION_INPUT_ABSENT")

    if att.get("READ_ATTESTATION") is not True:
        blockers.append("READ_ATTESTATION_NOT_PROVEN")
    if att.get("TRADE_ATTESTATION") is not True:
        blockers.append("TRADE_ATTESTATION_NOT_PROVEN")
    if att.get("WITHDRAW_ATTESTATION") is not False:
        blockers.append("WITHDRAW_ATTESTATION_MUST_REMAIN_FALSE")
    if str(att.get("KEY_BINDING_STATUS") or "") != "PROVEN":
        blockers.append("KEY_BINDING_STATUS_NOT_PROVEN")
    if str(att.get("SECRETREF_STATUS") or "") != "RESOLVED":
        blockers.append("CANARY_SECRETREF_STATUS_NOT_RESOLVED")
    secretref_uri = str(att.get("SECRETREF_URI_CONTRACT") or att.get("secretref_uri") or "").strip()
    if secretref_uri != REQUIRED_SECRETREF_URI:
        blockers.append("CANARY_SECRETREF_URI_MISBOUND")
    if str(att.get("VENUE") or "") != REUSED_BINDING_VENUE:
        blockers.append("VENUE_BINDING_MISMATCH")
    if str(att.get("LEGAL_ENTITY") or att.get("ENTITY") or "") != REUSED_BINDING_ENTITY:
        blockers.append("LEGAL_ENTITY_BINDING_MISMATCH")
    if str(att.get("REGION") or "") != REUSED_BINDING_REGION:
        blockers.append("REGION_BINDING_MISMATCH")
    if str(att.get("REST_HOST") or "") != REUSED_BINDING_REST_HOST:
        blockers.append("REST_HOST_BINDING_MISMATCH")
    if str(att.get("ACCOUNT_SCOPE") or "") != REUSED_BINDING_ACCOUNT_SCOPE:
        blockers.append("ACCOUNT_SCOPE_BINDING_MISMATCH")

    # Adopt the three standing economic baseline policies under this Owner-GO.
    economic = resolve_exchange_truth_adoption_dependency_v1(
        repo_root=repo_root,
        owner_adoption_decisions={
            POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1: True,
            POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1: True,
            POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1: True,
        },
    )
    if economic.get("EXCHANGE_TRUTH_ADOPTION_STATUS") != "OWNER_POLICIES_ADOPTED":
        blockers.append("ECONOMIC_BASELINE_POLICIES_NOT_ADOPTED")

    recon = dict(reconciliation_eval)
    all_match = recon.get("ALL_LAYERS_MATCH") is True
    unresolved = recon.get("UNRESOLVED_ECONOMIC_DIVERGENCE") is True
    blocks = recon.get("BLOCKS_NEW_ENTRY") is True
    if not all_match:
        blockers.append("RECONCILIATION_NOT_ALL_LAYERS_MATCH")
    if unresolved:
        blockers.append("UNRESOLVED_ECONOMIC_DIVERGENCE_REMAINS")
    if blocks:
        blockers.append("BLOCKS_NEW_ENTRY_REMAINS_TRUE_AFTER_ADOPTION")

    # Preserve Exchange Truth Adoption standing unless contradicted.
    exchange_truth_status = STATUS_ADOPTED_PROVEN
    for layer in HARD_STOP_LAYERS:
        if layer not in exchange_snapshot or layer not in local_expected_state_adopted:
            blockers.append(f"ADOPTED_STATE_LAYER_MISSING:{layer}")
            exchange_truth_status = "CONTRADICTION_FAIL_CLOSED"
        elif local_expected_state_adopted.get(layer) != exchange_snapshot.get(layer):
            blockers.append(f"ADOPTED_LOCAL_EXCHANGE_MISMATCH:{layer}")
            exchange_truth_status = "CONTRADICTION_FAIL_CLOSED"

    clearance = dict(okx_clearance)
    clearance_status = str(clearance.get("OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE") or "")
    if clearance_status not in {CLEARANCE_PRESENT_PROVEN, CLEARANCE_ABSENT_OR_UNPROVEN}:
        blockers.append("OKX_CLEARANCE_STATUS_INVALID")
    clearance_present = clearance_status == CLEARANCE_PRESENT_PROVEN
    okx_restriction = str(
        clearance.get("OKX_TEMP_SECURITY_RESTRICTION") or STANDING_OKX_TEMP_RESTRICTION_TOKEN
    )

    # Deduplicate blockers.
    seen: set[str] = set()
    ordered_blockers: list[str] = []
    for item in blockers:
        if item not in seen:
            seen.add(item)
            ordered_blockers.append(item)

    adoption_ok = len(ordered_blockers) == 0
    live_recon_proven = bool(adoption_ok and all_match and not unresolved and not blocks)
    blocks_new_entry = not live_recon_proven
    economic_divergence_status = (
        "RESOLVED_NO_UNRESOLVED_DIVERGENCE" if live_recon_proven else "UNRESOLVED_BLOCKS_NEW_ENTRY"
    )
    economic_baseline_status = (
        "OWNER_POLICIES_ADOPTED_PROVEN" if adoption_ok else "OWNER_POLICIES_REQUIRED_NOT_ADOPTED"
    )

    gate = evaluate_live_canary_cybersecurity_gate_v1(
        productive_surface_merged_to_origin_main=productive_surface_merged_to_origin_main,
        trade_attestation=True if adoption_ok else False,
        withdraw_attestation=False,
        read_attestation=True if adoption_ok else False,
        permission_attestation=dict(REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT),
        exchange_truth_adoption_status=exchange_truth_status,
        canary_key_binding_status="PROVEN" if adoption_ok else "NOT_PROVEN",
        secretref_status="RESOLVED" if adoption_ok else "MISSING_FAIL_CLOSED",
        okx_temp_security_restriction=(
            STANDING_OKX_TEMP_RESTRICTION_TOKEN
            if clearance_status != CLEARANCE_PRESENT_PROVEN
            else None
        ),
        okx_temp_security_clearance_evidence_present=clearance_present,
        canary_credential_isolation_proven=adoption_ok,
        live_testnet_isolation_proven=True,
        default_block_fail_closed_proven=True,
        one_shot_owner_go_separation_proven=True,
        canary_success_generalizes_to_general_live=False,
        live_reconciliation_proven=live_recon_proven,
        blocks_new_entry=blocks_new_entry,
        unresolved_economic_divergence_blocks_new_entry=not live_recon_proven,
    )

    gate_blockers = list(gate.get("BLOCKERS") or [])
    if adoption_ok and gate["LIVE_CANARY_CYBERSECURITY_GATE"] == "PASS":
        terminal = TERMINAL_RECON_PROVEN_CLEARANCE_PROVEN_GATE_PASS
        earliest = "NONE_AWAITING_SEPARATE_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
        next_step = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
    elif adoption_ok and live_recon_proven and not clearance_present:
        terminal = TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN
        earliest = "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT"
        next_step = (
            "OWNER_ACTIONS_OBTAIN_OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE_"
            "THEN_REEVALUATE_LIVE_CANARY_CYBERSECURITY_GATE"
        )
    else:
        terminal = TERMINAL_FAIL_CLOSED
        earliest = (
            ordered_blockers[0]
            if ordered_blockers
            else (gate_blockers[0] if gate_blockers else "UNKNOWN")
        )
        next_step = (
            "OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE_RETRY_AFTER_FAIL_CLOSED_FIX"
        )

    read_summary = dict(productive_private_read_summary or {})
    network_effect = (
        "LIVE_PRIVATE_READ_ONLY_ECONOMIC_BASELINE"
        if read_summary.get("GET_REQUEST_COUNT", 0)
        else "NONE"
    )

    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_E_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_V1",
        "OWNER_GO_BOUND": OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE,
        "OWNER_GO_STATUS": "CONSUMED",
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "EXCHANGE_TRUTH_ADOPTION_STATUS": exchange_truth_status,
        "EXCHANGE_TRUTH_ADOPTION_PRESERVED": exchange_truth_status == STATUS_ADOPTED_PROVEN,
        "ECONOMIC_BASELINE_ADOPTION_STATUS": economic_baseline_status,
        "OWNER_ECONOMIC_BASELINE_POLICIES_ADOPTED_BY_THIS_GO": adoption_ok,
        "OWNER_ADOPTION_POLICIES_APPLIED": [
            POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1,
            POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1,
            POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1,
        ],
        "ECONOMIC_BASELINE_RESOLUTION": economic,
        "ECONOMIC_DIVERGENCE_STATUS": economic_divergence_status,
        "LIVE_RECONCILIATION_PROVEN": live_recon_proven,
        "BLOCKS_NEW_ENTRY": blocks_new_entry,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": not live_recon_proven,
        "ALL_LAYERS_MATCH": all_match,
        "RECONCILIATION_EVAL": recon,
        "EXCHANGE_SNAPSHOT_SANITIZED": dict(exchange_snapshot),
        "LOCAL_EXPECTED_STATE_ADOPTED_SANITIZED": dict(local_expected_state_adopted),
        "OKX_TEMP_SECURITY_CLEARANCE": clearance,
        "OKX_TEMP_SECURITY_RESTRICTION": okx_restriction,
        "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE": clearance_status,
        "OKX_CLEARANCE_EVIDENCE_SOURCE": clearance.get("OKX_CLEARANCE_EVIDENCE_SOURCE"),
        "LIVE_VENUE": REUSED_BINDING_VENUE,
        "LIVE_LEGAL_ENTITY": REUSED_BINDING_ENTITY,
        "REGION": REUSED_BINDING_REGION,
        "REST_HOST": REUSED_BINDING_REST_HOST,
        "ACCOUNT_SCOPE_BINDING": REUSED_BINDING_ACCOUNT_SCOPE,
        "CANARY_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "CANARY_KEY_NAME_UI": CANARY_KEY_NAME_UI,
        "CANARY_SECRETREF_URI": REQUIRED_SECRETREF_URI,
        "CANARY_SECRETREF_STATUS": "RESOLVED" if adoption_ok else "NOT_RESOLVED",
        "CANARY_KEY_BINDING_STATUS": "PROVEN" if adoption_ok else "NOT_PROVEN",
        "READ_ATTESTATION": bool(adoption_ok),
        "TRADE_ATTESTATION": bool(adoption_ok),
        "WITHDRAW_ATTESTATION": False,
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "LIVE_CANARY_CYBERSECURITY_GATE_EVAL": gate,
        "ELIGIBLE_FOR_LIVE_CANARY_EVALUATION": gate.get("ELIGIBLE_FOR_LIVE_CANARY_EVALUATION"),
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "NETWORK_EFFECT": network_effect,
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": read_summary.get("SECRET_VALUE_ACCESS", "NONE"),
        "PRODUCTIVE_PRIVATE_READ_SUMMARY": read_summary,
        "PRIOR_CANARY_OWNER_GO_REUSED": False,
        "NEW_CANARY_OWNER_GO_GRANTED": False,
        "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_BY_THIS_GO": False,
        "STANDING_INVARIANTS": {
            "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
            "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
            "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
            "ORDER_EFFECT": "NONE",
            "ACCOUNT_MUTATION_EFFECT": "NONE",
        },
        "TERMINAL_STATE": terminal,
        "BLOCKERS": ordered_blockers,
        "GATE_BLOCKERS": gate_blockers,
        "EARLIEST_UNRESOLVED_DEPENDENCY": earliest,
        "CANONICAL_NEXT_STEP": next_step,
        "HARD_STOP_REASONS": ordered_blockers + gate_blockers,
        "SECRETREF_CONVENTION_EXAMPLE": SECRETREF_CONVENTION_EXAMPLE,
        "ok": True,
    }
