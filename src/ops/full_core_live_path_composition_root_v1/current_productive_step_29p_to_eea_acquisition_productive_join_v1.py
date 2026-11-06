"""Join STEP-29P admitted capital lineage into EEA universe acquisition.

Proves Treasury/C08/B05 → 29P admission precedes productive EEA GET acquisition
via machine-checkable lineage on the acquisition provenance envelope. Does not
extend acquire_eea_universe_inventory_v1 semantics; wraps it after admission gate.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Mapping

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
    acquire_eea_universe_inventory_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicUniverseGetPortV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    CurrentProductiveTreasurySingleSourceCapitalHandoffV1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_STEP_29P_TO_EEA_ACQUISITION_PRODUCTIVE_JOIN_V1"
CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE = "SYNTHETIC_TEST_FIXTURE"
SYNTHETIC_TEST_VALUE_HAS_PRODUCTIVE_AUTHORITY = False


@dataclass(frozen=True)
class Step29pToEeaAcquisitionProductiveJoinRequestV1:
    handoff: CurrentProductiveTreasurySingleSourceCapitalHandoffV1
    e2e_run_id: str
    capital_lineage_class: str
    expected_account_identity: str
    expected_instrument_id: str


@dataclass(frozen=True)
class Step29pToEeaAcquisitionProductiveJoinResultV1:
    ok: bool
    join_seam_id: str
    fail_closed: bool
    reason_codes: tuple[str, ...]
    step_29p_decision_epoch: str
    producer_input_set_digest: str
    lineage_binding_digest: str
    acquisition: EeaUniverseAcquisitionResultV1 | None


class Step29pToEeaAcquisitionProductiveJoinError(RuntimeError):
    """Fail-closed productive join violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _lineage_binding_digest_v1(
    *,
    e2e_run_id: str,
    decision_epoch: str,
    input_set_digest: str,
    account_identity: str,
    instrument_id: str,
) -> str:
    material = _canonical_json(
        {
            "join_seam_id": JOIN_SEAM_ID,
            "e2e_run_id": e2e_run_id,
            "decision_epoch": decision_epoch,
            "input_set_digest": input_set_digest,
            "account_identity": account_identity,
            "instrument_id": instrument_id,
        }
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _validate_admission_v1(
    request: Step29pToEeaAcquisitionProductiveJoinRequestV1,
) -> tuple[bool, tuple[str, ...], str, str]:
    reasons: list[str] = []
    handoff = request.handoff
    if handoff.fail_closed is True:
        reasons.append("HANDOFF_FAIL_CLOSED")
    adm = handoff.step_29p_admissibility
    if adm.risk_admissible is not True:
        reasons.extend(str(c) for c in adm.reason_codes)
        reasons.append("STEP_29P_NOT_RISK_ADMISSIBLE")
    output = handoff.producer_output
    if str(output.produced or "") != "true":
        reasons.append("PRODUCER_OUTPUT_NOT_PRODUCED")
    epoch = str(output.decision_epoch or "").strip()
    digest = str(output.input_set_digest or "").strip().lower()
    if epoch == "":
        reasons.append("DECISION_EPOCH_MISSING")
    if len(digest) != 64:
        reasons.append("INPUT_SET_DIGEST_INVALID")
    if str(output.bound_account_identity or "") != str(request.expected_account_identity or ""):
        reasons.append("ACCOUNT_IDENTITY_MISMATCH")
    claim = handoff.step_29p_claim
    if str(claim.expected_instrument_id or "") != str(request.expected_instrument_id or ""):
        reasons.append("INSTRUMENT_SCOPE_MISMATCH")
    lineage_class = str(request.capital_lineage_class or "").strip()
    if lineage_class == "":
        reasons.append("CAPITAL_LINEAGE_CLASS_MISSING")
    if lineage_class == CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE:
        if SYNTHETIC_TEST_VALUE_HAS_PRODUCTIVE_AUTHORITY is True:
            reasons.append("SYNTHETIC_FIXTURE_AUTHORITY_INVARIANT_BROKEN")
    if str(request.e2e_run_id or "").strip() == "":
        reasons.append("E2E_RUN_ID_MISSING")
    ok = not reasons
    return ok, tuple(dict.fromkeys(reasons)), epoch, digest


def join_step_29p_admitted_capital_into_eea_universe_acquisition_v1(
    request: Step29pToEeaAcquisitionProductiveJoinRequestV1,
    *,
    transport: EeaPublicUniverseGetPortV1 | None = None,
    observed_at: str | None = None,
) -> Step29pToEeaAcquisitionProductiveJoinResultV1:
    """Gate EEA acquisition on validated STEP-29P admission; stamp lineage on result."""
    admitted, reasons, epoch, input_digest = _validate_admission_v1(request)
    binding_digest = _lineage_binding_digest_v1(
        e2e_run_id=str(request.e2e_run_id),
        decision_epoch=epoch,
        input_set_digest=input_digest,
        account_identity=str(request.expected_account_identity),
        instrument_id=str(request.expected_instrument_id),
    )
    if not admitted:
        return Step29pToEeaAcquisitionProductiveJoinResultV1(
            ok=False,
            join_seam_id=JOIN_SEAM_ID,
            fail_closed=True,
            reason_codes=reasons,
            step_29p_decision_epoch=epoch,
            producer_input_set_digest=input_digest,
            lineage_binding_digest=binding_digest,
            acquisition=None,
        )

    acquisition = acquire_eea_universe_inventory_v1(
        transport=transport,
        observed_at=str(observed_at or epoch),
    )
    provenance = dict(acquisition.provenance)
    provenance.update(
        {
            "PRODUCTIVE_JOIN_SEAM_ID": JOIN_SEAM_ID,
            "E2E_RUN_ID": str(request.e2e_run_id),
            "STEP_29P_DECISION_EPOCH": epoch,
            "STEP_29P_PRODUCER_INPUT_SET_DIGEST": input_digest,
            "STEP_29P_LINEAGE_BINDING_DIGEST": binding_digest,
            "CAPITAL_LINEAGE_CLASS": str(request.capital_lineage_class),
            "SYNTHETIC_TEST_FIXTURE": str(
                request.capital_lineage_class == CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE
            ).lower(),
            "SYNTHETIC_TEST_VALUE_HAS_PRODUCTIVE_AUTHORITY": "false",
            "TREASURY_RECONCILIATION_CLASS": str(request.handoff.treasury_reconciliation_class),
        }
    )
    stamped = replace(acquisition, provenance=provenance)
    join_ok = acquisition.ok is True
    join_reasons: tuple[str, ...] = ()
    if not join_ok:
        join_reasons = tuple(acquisition.failure_codes) + ("EEA_ACQUISITION_FAIL_CLOSED",)
    return Step29pToEeaAcquisitionProductiveJoinResultV1(
        ok=join_ok,
        join_seam_id=JOIN_SEAM_ID,
        fail_closed=not join_ok,
        reason_codes=join_reasons,
        step_29p_decision_epoch=epoch,
        producer_input_set_digest=input_digest,
        lineage_binding_digest=binding_digest,
        acquisition=stamped,
    )


__all__ = [
    "CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE",
    "JOIN_SEAM_ID",
    "SYNTHETIC_TEST_VALUE_HAS_PRODUCTIVE_AUTHORITY",
    "Step29pToEeaAcquisitionProductiveJoinError",
    "Step29pToEeaAcquisitionProductiveJoinRequestV1",
    "Step29pToEeaAcquisitionProductiveJoinResultV1",
    "join_step_29p_admitted_capital_into_eea_universe_acquisition_v1",
]
