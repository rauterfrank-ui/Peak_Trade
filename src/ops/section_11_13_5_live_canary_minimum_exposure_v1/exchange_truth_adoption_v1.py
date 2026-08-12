"""§11.13.5.D Exchange Truth Adoption for LIVE canary path (governance; not execute).

Adopts productive OKX venue/account/credential truth already proven under
§11.13.5.C. Does not submit orders, clear BLOCKS_NEW_ENTRY, set LIVE_AUTHORIZED,
claim LIVE_RECONCILIATION_PROVEN, or consume a Canary execute GO.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    BLOCKS_NEW_ENTRY,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    LIVE_RECONCILIATION_PROVEN,
    POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    SECRETREF_CONVENTION_EXAMPLE,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cybersecurity_canary_gate_v1 import (
    evaluate_live_canary_cybersecurity_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_canary_owner_dependency_resolution_v1 import (
    resolve_exchange_truth_adoption_dependency_v1,
)

OWNER_GO_EXCHANGE_TRUTH_ADOPTION = "OWNER_GO_EXCHANGE_TRUTH_ADOPTION"
REQUIRED_SECRETREF_URI = SECRETREF_CONVENTION_EXAMPLE.replace("<venue>", "okx")
CANARY_KEY_NAME_UI = "PeakTrade-Live-Canary-MinExp"
OKX_TEMP_SECURITY_RESTRICTION = "24h_no_withdrawals_and_no_p2p_sell"
OKX_TEMP_SECURITY_RESTRICTION_SOURCE = (
    "PRODUCTIVE_OKX_SECURITY_STATE_AFTER_PASSKEY_RESET_BOUND_IN_SECTION_11_13_5_C"
)

STATUS_ADOPTED_PROVEN = "ADOPTED_PROVEN"
STATUS_NOT_ADOPTED = "OWNER_POLICIES_REQUIRED_NOT_ADOPTED"
TERMINAL_ADOPTED_CYBER_NOT_PASSED = (
    "EXCHANGE_TRUTH_ADOPTED_PROVEN_LIVE_CANARY_CYBERSECURITY_GATE_NOT_PASSED"
)
TERMINAL_ADOPTED_CYBER_PASS = "EXCHANGE_TRUTH_ADOPTED_PROVEN_LIVE_CANARY_CYBERSECURITY_GATE_PASS"
TERMINAL_FAIL_CLOSED = "FAIL_CLOSED_EXCHANGE_TRUTH_ADOPTION_BLOCKED"

# Distinct from venue/account/credential adoption: economic baseline policies
# from §11.13.3 / §11.13.5.B remain unresolved and must not be cleared here.
ECONOMIC_BASELINE_ADOPTION_STATUS_STANDING = "OWNER_POLICIES_REQUIRED_NOT_ADOPTED"


class LiveCanaryExchangeTruthAdoptionError(RuntimeError):
    """Fail-closed exchange-truth adoption violation."""


def _require_true(value: Any, label: str, blockers: list[str]) -> bool:
    ok = value is True
    if not ok:
        blockers.append(label)
    return ok


def evaluate_exchange_truth_adoption_v1(
    *,
    repo_root: str | Any,
    origin_main_sha: str,
    owner_go: str = OWNER_GO_EXCHANGE_TRUTH_ADOPTION,
    trade_key_attestation: Mapping[str, Any] | None = None,
    okx_temp_security_clearance_evidence_present: bool = False,
    productive_surface_merged_to_origin_main: bool = True,
) -> dict[str, Any]:
    """Adopt proven canary exchange/account/credential truth under this Owner-GO."""
    if str(owner_go or "").strip() != OWNER_GO_EXCHANGE_TRUTH_ADOPTION:
        raise LiveCanaryExchangeTruthAdoptionError("OWNER_GO_MISBOUND")

    att = dict(trade_key_attestation or {})
    blockers: list[str] = []

    if not att:
        blockers.append("TRADE_KEY_ATTESTATION_INPUT_ABSENT")

    read_ok = _require_true(att.get("READ_ATTESTATION"), "READ_ATTESTATION_NOT_PROVEN", blockers)
    trade_ok = _require_true(att.get("TRADE_ATTESTATION"), "TRADE_ATTESTATION_NOT_PROVEN", blockers)
    withdraw_false = att.get("WITHDRAW_ATTESTATION") is False
    if not withdraw_false:
        blockers.append("WITHDRAW_ATTESTATION_MUST_REMAIN_FALSE")

    key_binding = str(att.get("KEY_BINDING_STATUS") or att.get("CANARY_TRADE_KEY_BINDING") or "")
    if key_binding != "PROVEN":
        blockers.append("KEY_BINDING_STATUS_NOT_PROVEN")

    secretref_status = str(att.get("SECRETREF_STATUS") or "")
    if secretref_status != "RESOLVED":
        blockers.append("CANARY_SECRETREF_STATUS_NOT_RESOLVED")

    secretref_uri = str(att.get("SECRETREF_URI_CONTRACT") or att.get("secretref_uri") or "").strip()
    if secretref_uri != REQUIRED_SECRETREF_URI:
        blockers.append("CANARY_SECRETREF_URI_MISBOUND")

    venue = str(att.get("VENUE") or "")
    entity = str(att.get("LEGAL_ENTITY") or att.get("ENTITY") or "")
    region = str(att.get("REGION") or "")
    rest_host = str(att.get("REST_HOST") or "")
    account_scope = str(att.get("ACCOUNT_SCOPE") or "")
    if venue != REUSED_BINDING_VENUE:
        blockers.append("VENUE_BINDING_MISMATCH")
    if entity != REUSED_BINDING_ENTITY:
        blockers.append("LEGAL_ENTITY_BINDING_MISMATCH")
    if region != REUSED_BINDING_REGION:
        blockers.append("REGION_BINDING_MISMATCH")
    if rest_host != REUSED_BINDING_REST_HOST:
        blockers.append("REST_HOST_BINDING_MISMATCH")
    if account_scope != REUSED_BINDING_ACCOUNT_SCOPE:
        blockers.append("ACCOUNT_SCOPE_BINDING_MISMATCH")

    # Reject demo/simulation as productive truth.
    key_class = str(att.get("KEY_CLASS") or att.get("credential_class") or "")
    if key_class and key_class != REQUIRED_CREDENTIAL_CLASS:
        blockers.append("CREDENTIAL_CLASS_MISBOUND")
    for marker in ("DEMO", "TESTNET", "SIMULATED", "PAPER"):
        if marker in key_class.upper():
            blockers.append("DEMO_OR_SIMULATION_TRUTH_FORBIDDEN")
            break

    prior_reused = att.get("PRIOR_DRY_RUN_KEY_REUSED")
    if prior_reused is True:
        blockers.append("PRIOR_DRY_RUN_KEY_REUSED_FORBIDDEN")

    okx_restriction = str(
        att.get("OKX_RESTRICTIONS_AFTER_RESET")
        or att.get("OKX_TEMP_SECURITY_RESTRICTION")
        or OKX_TEMP_SECURITY_RESTRICTION
    )
    if okx_restriction != OKX_TEMP_SECURITY_RESTRICTION:
        blockers.append("OKX_TEMP_SECURITY_RESTRICTION_MISBOUND")

    # Economic baseline policies: encode standing NOT_ADOPTED; never auto-clear.
    economic = resolve_exchange_truth_adoption_dependency_v1(
        repo_root=repo_root,
        owner_adoption_decisions={
            POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1: False,
            POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1: False,
            POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1: False,
        },
    )
    if economic.get("EXCHANGE_TRUTH_ADOPTION_STATUS") != STATUS_NOT_ADOPTED:
        blockers.append("ECONOMIC_BASELINE_POLICY_STATUS_DRIFT")
    if economic.get("BLOCKS_NEW_ENTRY") is not True:
        blockers.append("BLOCKS_NEW_ENTRY_MUST_REMAIN_TRUE")
    if economic.get("LIVE_RECONCILIATION_PROVEN") is not False:
        blockers.append("LIVE_RECONCILIATION_PROVEN_MUST_REMAIN_FALSE")
    if economic.get("UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY") is not True:
        blockers.append("UNRESOLVED_ECONOMIC_DIVERGENCE_MUST_REMAIN_TRUE")

    # Deduplicate blockers.
    seen: set[str] = set()
    ordered_blockers: list[str] = []
    for b in blockers:
        if b not in seen:
            seen.add(b)
            ordered_blockers.append(b)

    adoption_ok = len(ordered_blockers) == 0 and read_ok and trade_ok and withdraw_false
    adoption_status = STATUS_ADOPTED_PROVEN if adoption_ok else STATUS_NOT_ADOPTED

    gate = evaluate_live_canary_cybersecurity_gate_v1(
        productive_surface_merged_to_origin_main=productive_surface_merged_to_origin_main,
        trade_attestation=bool(trade_ok and adoption_ok),
        withdraw_attestation=False if withdraw_false else True,
        read_attestation=bool(read_ok),
        permission_attestation=dict(REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT),
        exchange_truth_adoption_status=adoption_status,
        canary_key_binding_status=key_binding if adoption_ok else "NOT_PROVEN",
        secretref_status=secretref_status if adoption_ok else "MISSING_FAIL_CLOSED",
        okx_temp_security_restriction=okx_restriction,
        okx_temp_security_clearance_evidence_present=bool(
            okx_temp_security_clearance_evidence_present
        ),
        canary_credential_isolation_proven=bool(
            adoption_ok and prior_reused is not True and secretref_uri == REQUIRED_SECRETREF_URI
        ),
        live_testnet_isolation_proven=True,
        default_block_fail_closed_proven=True,
        one_shot_owner_go_separation_proven=True,
        canary_success_generalizes_to_general_live=False,
        # §11.13.5.D never clears economic/recon standing; pin historical blockers.
        live_reconciliation_proven=False,
        blocks_new_entry=True,
        unresolved_economic_divergence_blocks_new_entry=True,
    )

    if adoption_ok:
        terminal = (
            TERMINAL_ADOPTED_CYBER_PASS
            if gate["LIVE_CANARY_CYBERSECURITY_GATE"] == "PASS"
            else TERMINAL_ADOPTED_CYBER_NOT_PASSED
        )
    else:
        terminal = TERMINAL_FAIL_CLOSED

    gate_blockers = list(gate.get("BLOCKERS") or [])
    earliest = (
        "OWNER_GO_EXCHANGE_TRUTH_ADOPTION"
        if not adoption_ok
        else (
            gate_blockers[0]
            if gate_blockers
            else "NONE_AWAITING_SEPARATE_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
        )
    )
    if adoption_ok and gate["LIVE_CANARY_CYBERSECURITY_GATE"] != "PASS":
        # Prefer standing economic / reconciliation blocker as earliest dependency.
        if "LIVE_RECONCILIATION_PROVEN_FALSE" in gate_blockers:
            earliest = "LIVE_RECONCILIATION_PROVEN_FALSE"
        elif "BLOCKS_NEW_ENTRY_OR_UNRESOLVED_DIVERGENCE" in gate_blockers:
            earliest = "BLOCKS_NEW_ENTRY_OR_UNRESOLVED_ECONOMIC_DIVERGENCE"
        elif "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT" in gate_blockers:
            earliest = "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT"
        next_step = (
            "OWNER_ACTIONS_RESOLVE_UNRESOLVED_ECONOMIC_DIVERGENCE_BASELINE_AND_"
            "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE_THEN_REEVALUATE_LIVE_CANARY_CYBERSECURITY_GATE"
        )
    elif adoption_ok and gate["LIVE_CANARY_CYBERSECURITY_GATE"] == "PASS":
        next_step = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
    else:
        next_step = "OWNER_GO_EXCHANGE_TRUTH_ADOPTION"

    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_D_EXCHANGE_TRUTH_ADOPTION_V1",
        "OWNER_GO_BOUND": OWNER_GO_EXCHANGE_TRUTH_ADOPTION,
        "OWNER_GO_STATUS": "CONSUMED",
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "EXCHANGE_TRUTH_ADOPTION_STATUS": adoption_status,
        "EXCHANGE_TRUTH_ADOPTION_AUTHORIZED_BY_THIS_GO": True,
        "EXCHANGE_TRUTH_ADOPTION_IS_NOT_CANARY_AUTHORIZATION": True,
        "EXCHANGE_TRUTH_ADOPTION_IS_NOT_CYBERSECURITY_GATE_PASS": True,
        "EXCHANGE_TRUTH_ADOPTION_IS_NOT_GENERAL_LIVE_AUTHORIZATION": True,
        "LIVE_VENUE": REUSED_BINDING_VENUE,
        "LIVE_LEGAL_ENTITY": REUSED_BINDING_ENTITY,
        "REGION": REUSED_BINDING_REGION,
        "REST_HOST": REUSED_BINDING_REST_HOST,
        "ACCOUNT_SCOPE_BINDING": REUSED_BINDING_ACCOUNT_SCOPE,
        "ACCOUNT_SCOPE_BINDING_STATUS": "PROVEN_REUSED_FROM_SECTION_11_13_5_C",
        "CANARY_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "CANARY_KEY_NAME_UI": CANARY_KEY_NAME_UI,
        "KEY_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "CANARY_SECRETREF_URI": REQUIRED_SECRETREF_URI,
        "CANARY_SECRETREF_STATUS": "RESOLVED"
        if adoption_ok
        else secretref_status or "NOT_RESOLVED",
        "READ_ATTESTATION": bool(read_ok and adoption_ok),
        "TRADE_ATTESTATION": bool(trade_ok and adoption_ok),
        "WITHDRAW_ATTESTATION": False if adoption_ok else (att.get("WITHDRAW_ATTESTATION") is True),
        "KEY_BINDING_STATUS": "PROVEN" if adoption_ok else key_binding or "NOT_PROVEN",
        "CANARY_TRADE_KEY_BINDING": "PROVEN" if adoption_ok else "NOT_PROVEN",
        "REQUIRED_API_KEY_CAPABILITY": dict(REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT),
        "OKX_TEMP_SECURITY_RESTRICTION": OKX_TEMP_SECURITY_RESTRICTION,
        "OKX_TEMP_SECURITY_RESTRICTION_SOURCE": OKX_TEMP_SECURITY_RESTRICTION_SOURCE,
        "OKX_TEMP_SECURITY_RESTRICTION_BYPASS_FORBIDDEN": True,
        "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE_PRESENT": bool(
            okx_temp_security_clearance_evidence_present
        ),
        "OKX_TEMP_SECURITY_TRADING_PERMISSION_CLAIM": "NOT_ATTESTED_NO_INVENTION",
        "ECONOMIC_BASELINE_ADOPTION_STATUS": ECONOMIC_BASELINE_ADOPTION_STATUS_STANDING,
        "ECONOMIC_DIVERGENCE_STATUS": "UNRESOLVED_BLOCKS_NEW_ENTRY",
        "OWNER_ADOPTION_POLICIES_REQUIRED": list(
            economic.get("OWNER_ADOPTION_POLICIES_REQUIRED") or []
        ),
        "OWNER_ECONOMIC_BASELINE_POLICIES_ADOPTED_BY_THIS_GO": False,
        "ECONOMIC_BASELINE_RESOLUTION": economic,
        "DEMO_OR_SIMULATION_CONTEXT_ADOPTED_AS_PRODUCTIVE_TRUTH": False,
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "LIVE_CANARY_CYBERSECURITY_GATE_EVAL": gate,
        "ELIGIBLE_FOR_LIVE_CANARY_EVALUATION": gate.get("ELIGIBLE_FOR_LIVE_CANARY_EVALUATION"),
        "BLOCKS_NEW_ENTRY": True,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
        "LIVE_RECONCILIATION_PROVEN": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": "NONE",
        "PRIOR_CANARY_OWNER_GO_REUSED": False,
        "NEW_CANARY_OWNER_GO_GRANTED": False,
        "STANDING_INVARIANTS": {
            "BLOCKS_NEW_ENTRY": BLOCKS_NEW_ENTRY,
            "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": (
                UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY
            ),
            "LIVE_RECONCILIATION_PROVEN": LIVE_RECONCILIATION_PROVEN,
            "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
            "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
            "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
        },
        "TERMINAL_STATE": terminal,
        "BLOCKERS": ordered_blockers,
        "GATE_BLOCKERS": gate_blockers,
        "EARLIEST_UNRESOLVED_DEPENDENCY": earliest,
        "CANONICAL_NEXT_STEP": next_step,
        "HARD_STOP_REASONS": ordered_blockers + gate_blockers,
        "ok": True,
    }
