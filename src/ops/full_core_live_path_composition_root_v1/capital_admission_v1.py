"""Typed Full-Core Pre-Live Capital Admission seam. No POST. No wire. No arming.

OBSERVED_CAPITAL != RISK_ADMISSIBLE_CAPITAL.

Validates typed capital-evidence envelopes before STEP-29P / Venue-Capital
sizing may consume them. Does not invent equity formulas, haircuts, reserves,
or scope_capital derivation. RISK_ADMISSIBLE is never granted in this persist.

Fresh GET success alone does not mint capital authority.
LIVE_ACCOUNT_BOUND identity alone does not mint capital authority.
OFFLINE_ALGEBRA remains non-productive and cannot be Live capital evidence.
Balance increase is not automatic sizing capacity.
Stale higher previously-admitted capital cannot survive a credible decrease.

Does not set LIVE_ENABLED / LIVE_ARMED / WIRE_SEND_PERMITTED.
Does not rewrite STEP-29P OFFLINE_ALGEBRA mathematics.
Does not POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OFFLINE_BOUNDARY_ROLE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_AUTHORITY_NONE,
    CAPITAL_AUTHORITY_NON_PRODUCTIVE_OFFLINE_ALGEBRA,
    CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CAPITAL_SOURCE_FIXTURE,
    CAPITAL_SOURCE_HISTORICAL,
    CAPITAL_SOURCE_OFFLINE_ALGEBRA,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    CAPITAL_SOURCE_REPLAY,
    CapitalAdmissionStatusV1,
    ExecutionAdmissionInputsV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    contains_fixture_or_historical_marker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1 import (
    JOIN_SEAM_ID as LIVE_ACCOUNT_BOUND_JOIN_SEAM_ID,
    join_live_account_bound_into_admission_inputs_v1,
)

JOIN_SEAM_ID = "FULL_CORE_PRE_LIVE_CAPITAL_ADMISSION_SEAM_V1"
CAPITAL_ADMISSION_AUTHORITY = "capital_admission_contract_v1"
BINDING_SEMANTIC_CLASS = "TYPED_CAPITAL_ADMISSION_ENVELOPE"
STEP_29P_CONSUMER = "capital_risk_sizing_v1/STEP_29P"
EXECUTION_ADMISSION_CONSUMER = "evaluate_execution_admission_v1"

EVIDENCE_CLASS_LIVE_TYPED = "LIVE_TYPED"
EVIDENCE_CLASS_FIXTURE = "FIXTURE"
EVIDENCE_CLASS_REPLAY = "REPLAY"
EVIDENCE_CLASS_HISTORICAL = "HISTORICAL"
EVIDENCE_CLASS_OFFLINE_ALGEBRA = "OFFLINE_ALGEBRA"

_FORBIDDEN_AUTHORITY_FIELD_MARKERS = (
    "totaleq",
    "adjeq",
    "availeq",
    "availbal",
    "cashbal",
)
_BARE_EQ_FIELD = "eq"
_ALLOWED_SOURCE_CLASSES = frozenset(
    {
        CAPITAL_SOURCE_OFFLINE_ALGEBRA,
        CAPITAL_SOURCE_OBSERVED_VENUE,
        CAPITAL_SOURCE_FIXTURE,
        CAPITAL_SOURCE_REPLAY,
        CAPITAL_SOURCE_HISTORICAL,
    }
)
_NON_PRODUCTIVE_EVIDENCE_CLASSES = frozenset(
    {
        EVIDENCE_CLASS_FIXTURE,
        EVIDENCE_CLASS_REPLAY,
        EVIDENCE_CLASS_HISTORICAL,
        EVIDENCE_CLASS_OFFLINE_ALGEBRA,
    }
)


@dataclass(frozen=True)
class CapitalAdmissionClaimV1:
    """Caller-supplied typed envelope. Observation is not risk-admissible capital."""

    source_class: str
    account_identity: str
    instrument_id: str
    observed_capital_raw: str = ""
    observed_field_name: str = ""
    claimed_risk_admissible_capital: str = ""
    claimed_source_field: str = ""
    previously_admitted_risk_capital: str = ""
    evidence_class: str = EVIDENCE_CLASS_LIVE_TYPED
    evidence_id: str = ""


@dataclass(frozen=True)
class CapitalAdmissionEvidenceV1:
    evidence_status: str
    capital_source_class: str
    capital_authority_class: str
    risk_admissible: bool
    observed_capital_raw: str
    claimed_risk_admissible_capital: str
    previously_admitted_risk_capital: str
    expected_account_identity: str
    observed_account_identity: str
    expected_instrument_id: str
    observed_instrument_id: str
    reason_codes: Tuple[str, ...]
    live_enabled: bool
    live_armed: bool
    wire_send_permitted: bool
    step_29p_live_venue_capital_bound: bool = False
    join_seam_id: str = JOIN_SEAM_ID
    authority: str = CAPITAL_ADMISSION_AUTHORITY
    semantic_class: str = BINDING_SEMANTIC_CLASS


def _standing_extra() -> Tuple[str, ...]:
    if LIVE_ENABLED is True or LIVE_ARMED is True or WIRE_SEND_PERMITTED is True:
        return ("STANDING_LIVE_GATE_TRUE",)
    return ()


def _denied(
    *,
    status: str,
    claim: CapitalAdmissionClaimV1 | None,
    expected_account_identity: str,
    expected_instrument_id: str,
    source_class: str,
    authority: str,
    reasons: Tuple[str, ...],
) -> CapitalAdmissionEvidenceV1:
    extra = _standing_extra()
    observed_account = "" if claim is None else str(claim.account_identity or "")
    observed_inst = "" if claim is None else str(claim.instrument_id or "")
    observed_raw = "" if claim is None else str(claim.observed_capital_raw or "")
    claimed = "" if claim is None else str(claim.claimed_risk_admissible_capital or "")
    previous = "" if claim is None else str(claim.previously_admitted_risk_capital or "")
    return CapitalAdmissionEvidenceV1(
        evidence_status=status,
        capital_source_class=source_class,
        capital_authority_class=authority,
        risk_admissible=False,
        observed_capital_raw=observed_raw,
        claimed_risk_admissible_capital=claimed,
        previously_admitted_risk_capital=previous,
        expected_account_identity=expected_account_identity,
        observed_account_identity=observed_account,
        expected_instrument_id=expected_instrument_id,
        observed_instrument_id=observed_inst,
        reason_codes=tuple(dict.fromkeys((*reasons, JOIN_SEAM_ID, *extra))),
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        step_29p_live_venue_capital_bound=False,
    )


def _parse_non_negative_decimal(raw: str, *, field: str) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "":
        return None
    if text != str(raw):
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    _ = field
    return value


def _field_is_forbidden_authority(name: str) -> bool:
    folded = str(name or "").strip().lower().replace("_", "").replace("-", "")
    if not folded:
        return False
    if folded == _BARE_EQ_FIELD:
        return True
    return any(marker in folded for marker in _FORBIDDEN_AUTHORITY_FIELD_MARKERS)


def live_venue_capital_may_bind_step_29p_v1(evidence: CapitalAdmissionEvidenceV1) -> bool:
    """STEP-29P may consume venue capital only as RISK_ADMISSIBLE. Never true here."""
    return (
        evidence.evidence_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
        and evidence.capital_authority_class == CAPITAL_AUTHORITY_RISK_ADMISSIBLE
        and evidence.risk_admissible is True
        and LIVE_ENABLED is True
        and LIVE_ARMED is True
        and WIRE_SEND_PERMITTED is True
    )


def evaluate_capital_admission_v1(
    *,
    claim: CapitalAdmissionClaimV1 | None,
    expected_account_identity: Any = "",
    expected_instrument_id: Any = "",
    admission_context: str = ADMISSION_CONTEXT_LIVE,
) -> CapitalAdmissionEvidenceV1:
    expected_account = (
        expected_account_identity if isinstance(expected_account_identity, str) else ""
    )
    expected_instrument = expected_instrument_id if isinstance(expected_instrument_id, str) else ""
    live_context = admission_context == ADMISSION_CONTEXT_LIVE

    if not isinstance(expected_account_identity, str) or not isinstance(
        expected_instrument_id, str
    ):
        empty = CapitalAdmissionClaimV1(
            source_class="",
            account_identity="",
            instrument_id="",
        )
        return _denied(
            status=CapitalAdmissionStatusV1.MALFORMED.value,
            claim=empty,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_MALFORMED",
                "CAPITAL_ADMISSION_EXPECTED_NOT_STRING",
            ),
        )

    if claim is None:
        if live_context:
            return _denied(
                status=CapitalAdmissionStatusV1.MISSING.value,
                claim=None,
                expected_account_identity=expected_account,
                expected_instrument_id=expected_instrument,
                source_class="",
                authority=CAPITAL_AUTHORITY_NONE,
                reasons=(
                    "CAPITAL_ADMISSION_MISSING",
                    "FRESH_GET_ALONE_NOT_CAPITAL_AUTHORITY",
                    "LIVE_ACCOUNT_BOUND_ALONE_NOT_CAPITAL_AUTHORITY",
                ),
            )
        extra = _standing_extra()
        return CapitalAdmissionEvidenceV1(
            evidence_status=CapitalAdmissionStatusV1.NOT_REQUIRED_OFFLINE.value,
            capital_source_class=CAPITAL_SOURCE_OFFLINE_ALGEBRA,
            capital_authority_class=CAPITAL_AUTHORITY_NON_PRODUCTIVE_OFFLINE_ALGEBRA,
            risk_admissible=False,
            observed_capital_raw="",
            claimed_risk_admissible_capital="",
            previously_admitted_risk_capital="",
            expected_account_identity=expected_account,
            observed_account_identity="",
            expected_instrument_id=expected_instrument,
            observed_instrument_id="",
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        "CAPITAL_ADMISSION_NOT_REQUIRED_OFFLINE",
                        "OFFLINE_ALGEBRA_NOT_LIVE_CAPITAL_AUTHORITY",
                        JOIN_SEAM_ID,
                        *extra,
                    )
                )
            ),
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
            step_29p_live_venue_capital_bound=False,
        )

    source = str(claim.source_class or "").strip()
    evidence_class = str(claim.evidence_class or "").strip()
    account = str(claim.account_identity or "")
    instrument = str(claim.instrument_id or "")
    evidence_id = str(claim.evidence_id or "")

    if (
        account != account.strip()
        or instrument != instrument.strip()
        or str(claim.source_class or "") != source
        or str(claim.evidence_class or "") != evidence_class
    ):
        return _denied(
            status=CapitalAdmissionStatusV1.MALFORMED.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=("CAPITAL_ADMISSION_MALFORMED", "CAPITAL_ADMISSION_WHITESPACE"),
        )

    marker_blob = " ".join((evidence_id, account, instrument))
    if contains_fixture_or_historical_marker_v1(marker_blob):
        return _denied(
            status=CapitalAdmissionStatusV1.STALE.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source or CAPITAL_SOURCE_HISTORICAL,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_STALE",
                "CAPITAL_ADMISSION_FIXTURE_REPLAY_NOT_PRODUCTIVE",
                "CAPITAL_ADMISSION_HISTORICAL_NOT_PRODUCTIVE",
            ),
        )

    if evidence_class == EVIDENCE_CLASS_FIXTURE or source == CAPITAL_SOURCE_FIXTURE:
        return _denied(
            status=CapitalAdmissionStatusV1.STALE.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=CAPITAL_SOURCE_FIXTURE,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_STALE",
                "CAPITAL_ADMISSION_FIXTURE_NOT_PRODUCTIVE",
                "CAPITAL_ADMISSION_FIXTURE_REPLAY_NOT_PRODUCTIVE",
            ),
        )
    if evidence_class == EVIDENCE_CLASS_REPLAY or source == CAPITAL_SOURCE_REPLAY:
        return _denied(
            status=CapitalAdmissionStatusV1.STALE.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=CAPITAL_SOURCE_REPLAY,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_STALE",
                "CAPITAL_ADMISSION_REPLAY_NOT_PRODUCTIVE",
                "CAPITAL_ADMISSION_FIXTURE_REPLAY_NOT_PRODUCTIVE",
            ),
        )
    if evidence_class == EVIDENCE_CLASS_HISTORICAL or source == CAPITAL_SOURCE_HISTORICAL:
        return _denied(
            status=CapitalAdmissionStatusV1.STALE.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=CAPITAL_SOURCE_HISTORICAL,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_STALE",
                "CAPITAL_ADMISSION_HISTORICAL_NOT_PRODUCTIVE",
                "CAPITAL_ADMISSION_FIXTURE_REPLAY_NOT_PRODUCTIVE",
            ),
        )
    if source == CAPITAL_SOURCE_OFFLINE_ALGEBRA or evidence_class == EVIDENCE_CLASS_OFFLINE_ALGEBRA:
        return _denied(
            status=CapitalAdmissionStatusV1.STALE.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=CAPITAL_SOURCE_OFFLINE_ALGEBRA,
            authority=CAPITAL_AUTHORITY_NON_PRODUCTIVE_OFFLINE_ALGEBRA,
            reasons=(
                "CAPITAL_ADMISSION_STALE",
                "OFFLINE_ALGEBRA_NOT_LIVE_CAPITAL_AUTHORITY",
                "CAPITAL_ADMISSION_OFFLINE_ALGEBRA_NOT_LIVE",
            ),
        )

    if source not in _ALLOWED_SOURCE_CLASSES or source == "":
        return _denied(
            status=CapitalAdmissionStatusV1.MALFORMED.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=("CAPITAL_ADMISSION_MALFORMED", "CAPITAL_ADMISSION_SOURCE_CLASS_UNKNOWN"),
        )
    if evidence_class not in {EVIDENCE_CLASS_LIVE_TYPED, ""}:
        if evidence_class in _NON_PRODUCTIVE_EVIDENCE_CLASSES:
            pass
        else:
            return _denied(
                status=CapitalAdmissionStatusV1.MALFORMED.value,
                claim=claim,
                expected_account_identity=expected_account,
                expected_instrument_id=expected_instrument,
                source_class=source,
                authority=CAPITAL_AUTHORITY_NONE,
                reasons=(
                    "CAPITAL_ADMISSION_MALFORMED",
                    "CAPITAL_ADMISSION_EVIDENCE_CLASS_UNKNOWN",
                ),
            )

    if account == "" or expected_account == "":
        return _denied(
            status=CapitalAdmissionStatusV1.MISSING.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_MISSING",
                "CAPITAL_ADMISSION_ACCOUNT_IDENTITY_MISSING",
            ),
        )
    if account != expected_account:
        return _denied(
            status=CapitalAdmissionStatusV1.WRONG_CONTEXT.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_WRONG_CONTEXT",
                "CAPITAL_ADMISSION_WRONG_ACCOUNT",
            ),
        )
    if expected_instrument == "":
        return _denied(
            status=CapitalAdmissionStatusV1.MISSING.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_MISSING",
                "CAPITAL_ADMISSION_INSTRUMENT_SCOPE_MISSING",
            ),
        )
    if instrument != "" and instrument != expected_instrument:
        return _denied(
            status=CapitalAdmissionStatusV1.WRONG_CONTEXT.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_WRONG_CONTEXT",
                "CAPITAL_ADMISSION_WRONG_INSTRUMENT",
            ),
        )

    if _field_is_forbidden_authority(claim.claimed_source_field):
        return _denied(
            status=CapitalAdmissionStatusV1.CONTRADICTORY.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_CONTRADICTORY",
                "CAPITAL_ADMISSION_OPTIMISTIC_FIELD_FALLBACK",
            ),
        )

    observed = _parse_non_negative_decimal(claim.observed_capital_raw, field="observed_capital_raw")
    if str(claim.observed_capital_raw or "") != "" and observed is None:
        return _denied(
            status=CapitalAdmissionStatusV1.MALFORMED.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=("CAPITAL_ADMISSION_MALFORMED", "CAPITAL_ADMISSION_OBSERVED_NOT_DECIMAL"),
        )
    claimed = _parse_non_negative_decimal(
        claim.claimed_risk_admissible_capital, field="claimed_risk_admissible_capital"
    )
    if str(claim.claimed_risk_admissible_capital or "") != "" and claimed is None:
        return _denied(
            status=CapitalAdmissionStatusV1.MALFORMED.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=("CAPITAL_ADMISSION_MALFORMED", "CAPITAL_ADMISSION_CLAIMED_NOT_DECIMAL"),
        )
    previous = _parse_non_negative_decimal(
        claim.previously_admitted_risk_capital, field="previously_admitted_risk_capital"
    )
    if str(claim.previously_admitted_risk_capital or "") != "" and previous is None:
        return _denied(
            status=CapitalAdmissionStatusV1.MALFORMED.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=("CAPITAL_ADMISSION_MALFORMED", "CAPITAL_ADMISSION_PREVIOUS_NOT_DECIMAL"),
        )

    if claimed is not None:
        return _denied(
            status=CapitalAdmissionStatusV1.CONTRADICTORY.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_CONTRADICTORY",
                "CAPITAL_ADMISSION_RISK_ADMISSIBLE_POLICY_FROZEN",
                "CAPITAL_INCREASE_NOT_AUTO_ADMITTED",
            ),
        )

    if previous is not None and observed is not None and previous > observed:
        return _denied(
            status=CapitalAdmissionStatusV1.STALE.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_STALE",
                "CAPITAL_DECREASE_STALE_HIGHER_DENIED",
                "CAPITAL_ADMISSION_RECONCILIATION_REQUIRED",
            ),
        )
    if previous is not None and observed is not None and observed > previous:
        return _denied(
            status=CapitalAdmissionStatusV1.CONTRADICTORY.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
            reasons=(
                "CAPITAL_ADMISSION_CONTRADICTORY",
                "CAPITAL_INCREASE_NOT_AUTO_ADMITTED",
            ),
        )

    extra = _standing_extra()
    trusted = CapitalAdmissionEvidenceV1(
        evidence_status=CapitalAdmissionStatusV1.TRUSTED_PRESENT.value,
        capital_source_class=source,
        capital_authority_class=CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
        risk_admissible=False,
        observed_capital_raw=str(claim.observed_capital_raw or ""),
        claimed_risk_admissible_capital="",
        previously_admitted_risk_capital=str(claim.previously_admitted_risk_capital or ""),
        expected_account_identity=expected_account,
        observed_account_identity=account,
        expected_instrument_id=expected_instrument,
        observed_instrument_id=instrument or expected_instrument,
        reason_codes=tuple(
            dict.fromkeys(
                (
                    "CAPITAL_ADMISSION_TRUSTED_PRESENT",
                    "OBSERVED_CAPITAL_NOT_RISK_ADMISSIBLE",
                    "FRESH_GET_ALONE_NOT_CAPITAL_AUTHORITY",
                    "LIVE_ACCOUNT_BOUND_ALONE_NOT_CAPITAL_AUTHORITY",
                    JOIN_SEAM_ID,
                    CAPITAL_ADMISSION_AUTHORITY,
                    *extra,
                )
            )
        ),
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        step_29p_live_venue_capital_bound=False,
    )
    if live_venue_capital_may_bind_step_29p_v1(trusted) is True:
        return _denied(
            status=CapitalAdmissionStatusV1.CONTRADICTORY.value,
            claim=claim,
            expected_account_identity=expected_account,
            expected_instrument_id=expected_instrument,
            source_class=source,
            authority=CAPITAL_AUTHORITY_NONE,
            reasons=(
                "CAPITAL_ADMISSION_CONTRADICTORY",
                "CAPITAL_ADMISSION_CANNOT_BIND_STEP_29P",
            ),
        )
    return trusted


def join_capital_admission_into_admission_inputs_v1(
    *,
    plan_identity: str,
    venue_plan_identity: str,
    instrument_identity_ok: bool,
    pretrade_admissible: bool,
    pretrade_source_kind: str,
    pretrade_freshness_status: str,
    capital_risk_mode: str,
    owner_go: Any,
    admission_context: str,
    provenance_refs: Tuple[str, ...] = (),
    state_path: Optional[str] = None,
    transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    pretrade_decision_id: str = "",
    instrument_id: str = "",
    td_mode: str = "",
    limit_px: str = "",
    inst_type: str = "FUTURES",
    expected_account_identity: Any = "",
    capital_admission_claim: CapitalAdmissionClaimV1 | None = None,
) -> ExecutionAdmissionInputsV1:
    inputs = join_live_account_bound_into_admission_inputs_v1(
        plan_identity=plan_identity,
        venue_plan_identity=venue_plan_identity,
        instrument_identity_ok=instrument_identity_ok,
        pretrade_admissible=pretrade_admissible,
        pretrade_source_kind=pretrade_source_kind,
        pretrade_freshness_status=pretrade_freshness_status,
        capital_risk_mode=capital_risk_mode,
        owner_go=owner_go,
        admission_context=admission_context,
        provenance_refs=provenance_refs,
        state_path=state_path,
        transport=transport,
        pretrade_decision_id=pretrade_decision_id,
        instrument_id=instrument_id,
        td_mode=td_mode,
        limit_px=limit_px,
        inst_type=inst_type,
        expected_account_identity=expected_account_identity,
    )
    evidence = evaluate_capital_admission_v1(
        claim=capital_admission_claim,
        expected_account_identity=expected_account_identity,
        expected_instrument_id=instrument_id,
        admission_context=admission_context,
    )
    return ExecutionAdmissionInputsV1(
        plan_identity=inputs.plan_identity,
        venue_plan_identity=inputs.venue_plan_identity,
        instrument_identity_ok=inputs.instrument_identity_ok,
        pretrade_admissible=inputs.pretrade_admissible,
        pretrade_source_kind=inputs.pretrade_source_kind,
        pretrade_freshness_status=inputs.pretrade_freshness_status,
        capital_risk_mode=inputs.capital_risk_mode,
        durable_kill_switch_evidence_status=inputs.durable_kill_switch_evidence_status,
        durable_kill_switch_blocked=inputs.durable_kill_switch_blocked,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        owner_authorization_present=inputs.owner_authorization_present,
        owner_one_shot_permit_status=inputs.owner_one_shot_permit_status,
        admission_context=inputs.admission_context,
        fresh_pretrade_get_status=inputs.fresh_pretrade_get_status,
        live_account_bound_status=inputs.live_account_bound_status,
        capital_admission_status=evidence.evidence_status,
        capital_authority_class=evidence.capital_authority_class,
        provenance_refs=inputs.provenance_refs
        + (
            OFFLINE_BOUNDARY_ROLE,
            JOIN_SEAM_ID,
            CAPITAL_ADMISSION_AUTHORITY,
            LIVE_ACCOUNT_BOUND_JOIN_SEAM_ID,
            *evidence.reason_codes,
        ),
    )
