"""CURRENT_PRODUCTIVE post-flatten evidence adjudication and SSOT advance.

Consumes Owner-GO
OWNER_GO_POST_FLATTEN_EVIDENCE_ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_V1.

Offline adjudication of the sealed one-shot flatten POST pack plus optional
injected READ-ONLY recon payloads. Does not POST. Does not issue or consume a
permit. Does not rewrite §11.14 ladder fields. Does not normalize bills into
fills. Historical ownership remains UNKNOWN_NOT_PROVEN.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ONE_SHOT_REAL_POST_AUTHORITY_REFS,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    CurrentProductiveFreshCap23Cap24ReadinessError,
    _assert_no_secrets,
    _persist_json,
    _token,
    _utc_now_iso_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_POST_FLATTEN_EVIDENCE_ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_V1"
CONSUMED_POST_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_EXACT_OBJECT_FLATTEN_"
    "ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
THIS_SLICE = (
    "11.2.1.DM.FULL_CORE_CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_ADJUDICATION_"
    "AND_CANONICAL_STATE_ADVANCE"
)
EXPECTED_ORIGIN_MAIN_SHA = "2105a0fdea633640fc0ffb810f55c4a46e74271e"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_post_flatten_evidence_adjudication_and_canonical_"
    "state_advance_v1/20260916T001500Z"
)
SOURCE_POST_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_actual_venue_post_with_fresh_exact_"
    "object_flatten_envelope_bound_single_use_permit_v1/20260915T220112Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
GRANTED_INST_ID = "SUI-USD_UM_XPERP-310404"
GRANTED_INST_TYPE = "FUTURES"
GRANTED_POS_ID = "3891385768441942017"
EXPECTED_ORD_ID = "3926112627662393344"
EXPECTED_CL_ORD_ID = "ptokxeprod7a3f7e7deacbecfa00"
EXPECTED_PERMIT_ID = "eep-541c6727e12b9d1e75c48da187630017"
EXPECTED_ENVELOPE_ID = "env-d5f04fb4963f0bbdd9fa11cb251a083a"
STANDING_SEAM_REMAINDER = (
    "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
)
CURRENT_PRODUCTIVE_FIRST_BLOCKER = (
    "FRESH_CURRENT_PRODUCTIVE_MASTER_V2_RUNTIME_CYCLE_AND_CAP23_CAP24_BINDING_"
    "REQUIRED_AFTER_OCCUPANCY_ABSENT"
)
NEXT_OWNER_GO = (
    "SEPARATE_OWNER_GO_FOR_FRESH_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_FLATTEN_OCCUPANCY_ABSENT"
)
SECTION_11_14_FLAGS_UNCHANGED = (
    "LIVE_SUBMIT_ACK_OBSERVED=true;"
    "LIVE_FILL_OBSERVED=true;"
    "LIVE_FEE_OBSERVED=true;"
    "LIVE_POSITION_RECONCILED=true;"
    "LIVE_ACCOUNTING_RECONSTRUCTED=true;"
    "LIVE_RESTART_RECONSTRUCTED=false;"
    "LIVE_AUTONOMOUS_RECOVERY_OBSERVED=false;"
    "LIVE_END_TO_END_EVIDENCE_PROVEN=false;"
    "SECTION_11_14_COMPLETE=false"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)
SOURCE_FILES = (
    "REPORT.json",
    "RAW_VENUE_ACK.json",
    "POST_SUBMIT_RAW.json",
    "POST_SUBMIT_GET_META.json",
    "SEND_SEAM.json",
    "PERMIT.json",
    "full_core_external_effect_permit_consume_v1.json",
    "ENVELOPE.json",
    "MANIFEST.sha256",
)


class CurrentProductivePostFlattenAdjudicationError(CurrentProductiveFreshCap23Cap24ReadinessError):
    """Fail-closed post-flatten adjudication violation."""


@dataclass(frozen=True)
class CurrentProductivePostFlattenAdjudicationResultV1:
    store_root: str
    submit_ack_class: str
    fill_observed: str
    fee_observed: str
    order_history_observed: str
    position_flat_observed: str
    target_occupancy_absent: str
    flatten_reconciliation_class: str
    first_real_current_productive_blocker: str
    section_11_14_flags_after: str
    venue_mutation_performed: str
    post_count: str
    evidence_manifest: str
    manifest_verify_rc: int


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _data_rows(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _open_nonzero_rows(payload: Any) -> list[Mapping[str, Any]]:
    open_rows: list[Mapping[str, Any]] = []
    for row in _data_rows(payload):
        text = str(row.get("pos") or "").strip()
        if not text:
            continue
        try:
            if Decimal(text) == 0:
                continue
        except Exception:
            continue
        open_rows.append(row)
    return open_rows


def _identity_rows(
    payload: Any, *, ord_id: str, cl_ord_id: str, inst_id: str
) -> list[Mapping[str, Any]]:
    matched: list[Mapping[str, Any]] = []
    for row in _data_rows(payload):
        if str(row.get("ordId") or "") != ord_id:
            continue
        if str(row.get("clOrdId") or "") != cl_ord_id:
            continue
        if str(row.get("instId") or "") != inst_id:
            continue
        matched.append(row)
    return matched


def _submit_ack_class(*, ack: Mapping[str, Any], report: Mapping[str, Any]) -> str:
    http_status = str(ack.get("http_status") or "")
    payload = ack.get("payload") if isinstance(ack.get("payload"), Mapping) else {}
    code = str(payload.get("code") or "")
    data = payload.get("data")
    s_code = ""
    ord_id = ""
    cl_ord_id = ""
    if isinstance(data, list) and data and isinstance(data[0], Mapping):
        s_code = str(data[0].get("sCode") or "")
        ord_id = str(data[0].get("ordId") or "")
        cl_ord_id = str(data[0].get("clOrdId") or "")
    report_ack = str(report.get("RAW_VENUE_ACK_STATUS") or "")
    if (
        http_status == "200"
        and code == "0"
        and s_code == "0"
        and ord_id == EXPECTED_ORD_ID
        and cl_ord_id == EXPECTED_CL_ORD_ID
        and "http=200;code=0;sCode=0" in report_ack
    ):
        return "ACCEPTED_SUBMITTED_NOT_FILL"
    return "ACK_NOT_PROVEN_FAIL_CLOSED"


def adjudicate_post_flatten_evidence_v1(
    *,
    report: Mapping[str, Any],
    ack: Mapping[str, Any],
    post_submit_raw: Mapping[str, Any],
    fresh_recon: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Classify sealed POST facts. Bills never become fills. §11.14 unchanged."""
    if str(report.get("POST_COUNT") or "") != "1":
        raise CurrentProductivePostFlattenAdjudicationError("SOURCE_POST_COUNT_NOT_ONE")
    if str(report.get("SECOND_SUBMIT_PERFORMED") or FALSE_TOKEN) != FALSE_TOKEN:
        raise CurrentProductivePostFlattenAdjudicationError("SOURCE_SECOND_SUBMIT_NOT_FALSE")
    if str(report.get("VENUE_ORDER_ID") or "") != EXPECTED_ORD_ID:
        raise CurrentProductivePostFlattenAdjudicationError("SOURCE_ORD_ID_MISMATCH")
    if str(report.get("CLIENT_ORDER_ID") or "") != EXPECTED_CL_ORD_ID:
        raise CurrentProductivePostFlattenAdjudicationError("SOURCE_CLORD_ID_MISMATCH")
    if str(report.get("PERMIT_ID") or "") != EXPECTED_PERMIT_ID:
        raise CurrentProductivePostFlattenAdjudicationError("SOURCE_PERMIT_MISMATCH")
    if str(report.get("FINAL_ENVELOPE_ID") or "") != EXPECTED_ENVELOPE_ID:
        raise CurrentProductivePostFlattenAdjudicationError("SOURCE_ENVELOPE_MISMATCH")

    ack_class = _submit_ack_class(ack=ack, report=report)
    sealed_positions = post_submit_raw.get("POSITIONS")
    sealed_pending = post_submit_raw.get("PENDING")
    sealed_history = post_submit_raw.get("ORDERS_HISTORY")
    sealed_fills = post_submit_raw.get("FILLS")
    sealed_bills = post_submit_raw.get("BILLS")
    recon = fresh_recon if isinstance(fresh_recon, Mapping) else {}
    positions = recon.get("POSITIONS", sealed_positions)
    pending = recon.get("PENDING", sealed_pending)
    sealed_fill_rows = _identity_rows(
        sealed_fills,
        ord_id=EXPECTED_ORD_ID,
        cl_ord_id=EXPECTED_CL_ORD_ID,
        inst_id=GRANTED_INST_ID,
    )
    sealed_fill_sz = [row for row in sealed_fill_rows if str(row.get("fillSz") or "").strip()]
    sealed_history_rows = _identity_rows(
        sealed_history,
        ord_id=EXPECTED_ORD_ID,
        cl_ord_id=EXPECTED_CL_ORD_ID,
        inst_id=GRANTED_INST_ID,
    )
    sealed_bill_rows = _identity_rows(
        sealed_bills,
        ord_id=EXPECTED_ORD_ID,
        cl_ord_id=EXPECTED_CL_ORD_ID,
        inst_id=GRANTED_INST_ID,
    )
    sealed_fee_rows = [
        row for row in sealed_bill_rows if str(row.get("fee") or "").strip() not in {"", "0"}
    ]
    fresh_fill_sz: list[Mapping[str, Any]] = []
    fresh_history_rows: list[Mapping[str, Any]] = []
    if "FILLS" in recon:
        fresh_fill_rows = _identity_rows(
            recon.get("FILLS"),
            ord_id=EXPECTED_ORD_ID,
            cl_ord_id=EXPECTED_CL_ORD_ID,
            inst_id=GRANTED_INST_ID,
        )
        fresh_fill_sz = [row for row in fresh_fill_rows if str(row.get("fillSz") or "").strip()]
    if "ORDERS_HISTORY" in recon:
        fresh_history_rows = _identity_rows(
            recon.get("ORDERS_HISTORY"),
            ord_id=EXPECTED_ORD_ID,
            cl_ord_id=EXPECTED_CL_ORD_ID,
            inst_id=GRANTED_INST_ID,
        )

    open_rows = _open_nonzero_rows(positions)
    target_present = any(
        str(row.get("posId") or "") == GRANTED_POS_ID
        or str(row.get("instId") or "") == GRANTED_INST_ID
        for row in open_rows
    )
    position_flat = _token(len(open_rows) == 0 and target_present is False)
    occupancy_absent = position_flat
    pending_rows = _data_rows(pending)
    fill_observed = _token(len(sealed_fill_sz) > 0)
    fee_observed = _token(len(sealed_fee_rows) > 0)
    history_observed = _token(len(sealed_history_rows) > 0)
    fresh_fill_observed = _token(len(fresh_fill_sz) > 0)
    fresh_history_observed = _token(len(fresh_history_rows) > 0)
    if fill_observed == TRUE_TOKEN:
        recon_class = "FILL_ENDPOINT_PROVEN_NOT_REACHED_IN_THIS_PACK"
    elif position_flat == TRUE_TOKEN and ack_class == "ACCEPTED_SUBMITTED_NOT_FILL":
        recon_class = "OCCUPANCY_ABSENT_WITHOUT_FILL_ENDPOINT_PROOF"
    else:
        recon_class = "FLATTEN_NOT_RECONCILED_FAIL_CLOSED"
    standing_remainder = current_productive_first_real_blocker_v1()
    if standing_remainder != STANDING_SEAM_REMAINDER:
        raise CurrentProductivePostFlattenAdjudicationError("STANDING_SEAM_REMAINDER_DRIFT")
    return {
        "SUBMIT_ACK_CLASS": ack_class,
        "FILL_OBSERVED": fill_observed,
        "FEE_OBSERVED": fee_observed,
        "ORDER_HISTORY_OBSERVED": history_observed,
        "POSITION_FLAT_OBSERVED": position_flat,
        "TARGET_OCCUPANCY_ABSENT": occupancy_absent,
        "POST_SUBMIT_OPEN_ORDERS": "NONE_OBSERVED" if not pending_rows else "PENDING_ROWS_PRESENT",
        "FLATTEN_RECONCILIATION_CLASS": recon_class,
        "FLATTEN_RECONCILED": _token(recon_class == "OCCUPANCY_ABSENT_WITHOUT_FILL_ENDPOINT_PROOF"),
        "HISTORICAL_POSITION_OWNERSHIP": "UNKNOWN_NOT_PROVEN",
        "SECTION_11_14_FLAGS_BEFORE": SECTION_11_14_FLAGS_UNCHANGED,
        "SECTION_11_14_FLAGS_AFTER": SECTION_11_14_FLAGS_UNCHANGED,
        "SECTION_11_14_REWRITTEN": FALSE_TOKEN,
        "BILLS_NORMALIZED_TO_FILL": FALSE_TOKEN,
        "STANDING_SEAM_REMAINDER": standing_remainder,
        "STANDING_SEAM_REMAINDER_CLASS": "LEGACY_NON_BLOCKING_FOR_POST_FLATTEN_OCCUPANCY_ABSENT",
        "FIRST_REAL_CURRENT_PRODUCTIVE_BLOCKER": CURRENT_PRODUCTIVE_FIRST_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "FRESH_RECON_USED": _token(bool(recon)),
        "FRESH_FILL_OBSERVED": fresh_fill_observed,
        "FRESH_ORDER_HISTORY_OBSERVED": fresh_history_observed,
        "GRANTED_INST_TYPE": GRANTED_INST_TYPE,
    }


def execute_current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    source_pack_root: Path | str | None = None,
    report: Mapping[str, Any] | None = None,
    ack: Mapping[str, Any] | None = None,
    post_submit_raw: Mapping[str, Any] | None = None,
    fresh_recon: Mapping[str, Any] | None = None,
    execute_network: bool = False,
) -> CurrentProductivePostFlattenAdjudicationResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductivePostFlattenAdjudicationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductivePostFlattenAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if execute_network is True:
        raise CurrentProductivePostFlattenAdjudicationError(
            "NETWORK_FORBIDDEN_OFFLINE_ADJUDICATION"
        )
    if (
        CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_CREATED
        is not True
    ):
        raise CurrentProductivePostFlattenAdjudicationError("ADAPTER_NOT_CREATED")
    if OWNER_GO in ONE_SHOT_REAL_POST_AUTHORITY_REFS:
        raise CurrentProductivePostFlattenAdjudicationError(
            "ADJUDICATION_GO_MUST_NOT_AUTHORIZE_POST"
        )
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductivePostFlattenAdjudicationError("STANDING_EXTERNAL_EFFECT_NOT_FALSE")
    if REAL_EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductivePostFlattenAdjudicationError("REAL_EXTERNAL_EFFECT_NOT_FALSE")
    if REAL_VENUE_POST_ALLOWED is not False or POST_ALLOWED is not False:
        raise CurrentProductivePostFlattenAdjudicationError("POST_ALLOWED_NOT_FALSE")
    if ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is not True:
        raise CurrentProductivePostFlattenAdjudicationError("ENVELOPE_BOUND_SEAM_NOT_TRUE")

    source_root = Path(source_pack_root) if source_pack_root is not None else None
    source_digests: dict[str, str] = {}
    loaded_report = dict(report or {})
    loaded_ack = dict(ack or {})
    loaded_raw = dict(post_submit_raw or {})
    if source_root is not None:
        if not source_root.is_dir():
            raise CurrentProductivePostFlattenAdjudicationError("SOURCE_PACK_MISSING")
        for name in SOURCE_FILES:
            path = source_root / name
            if not path.is_file():
                raise CurrentProductivePostFlattenAdjudicationError(f"SOURCE_FILE_MISSING:{name}")
            source_digests[name] = _file_digest(path)
        if not loaded_report:
            loaded_report = _load_json(source_root / "REPORT.json")
        if not loaded_ack:
            loaded_ack = _load_json(source_root / "RAW_VENUE_ACK.json")
        if not loaded_raw:
            loaded_raw = _load_json(source_root / "POST_SUBMIT_RAW.json")
        manifest_rc = verify_manifest_sha256_v1(store_root=source_root)
        if int(manifest_rc) != 0:
            raise CurrentProductivePostFlattenAdjudicationError("SOURCE_MANIFEST_VERIFY_FAILED")
    if not loaded_report or not loaded_ack or not loaded_raw:
        raise CurrentProductivePostFlattenAdjudicationError("SEALED_FACTS_MISSING")

    started = _utc_now_iso_v1()
    classified = adjudicate_post_flatten_evidence_v1(
        report=loaded_report,
        ack=loaded_ack,
        post_submit_raw=loaded_raw,
        fresh_recon=fresh_recon,
    )
    if classified["SUBMIT_ACK_CLASS"] != "ACCEPTED_SUBMITTED_NOT_FILL":
        raise CurrentProductivePostFlattenAdjudicationError("SUBMIT_ACK_NOT_PROVEN")
    if classified["FILL_OBSERVED"] != FALSE_TOKEN:
        raise CurrentProductivePostFlattenAdjudicationError("FILL_MUST_REMAIN_UNOBSERVED")
    if classified["BILLS_NORMALIZED_TO_FILL"] != FALSE_TOKEN:
        raise CurrentProductivePostFlattenAdjudicationError("BILLS_MUST_NOT_BECOME_FILL")
    if classified["SECTION_11_14_REWRITTEN"] != FALSE_TOKEN:
        raise CurrentProductivePostFlattenAdjudicationError("SECTION_11_14_MUST_REMAIN_UNCHANGED")

    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    finished = _utc_now_iso_v1()
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "CONSUMED_POST_OWNER_GO": CONSUMED_POST_OWNER_GO,
        "CONSUMED_POST_OWNER_GO_STATUS": "CONSUMED",
        "THIS_SLICE": THIS_SLICE,
        "CURRENT_PHASE": THIS_SLICE,
        "CANONICAL_PHASE_BEFORE": (
            "11.2.1.DL.FULL_CORE_CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_"
            "TO_ONE_SHOT_FLATTEN_POST_BOUNDARY"
        ),
        "CANONICAL_PHASE_AFTER": THIS_SLICE,
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "PACKAGE_STARTED_UTC": started,
        "PACKAGE_FINISHED_UTC": finished,
        "SOURCE_POST_PACK_RELPATH": SOURCE_POST_PACK_RELPATH,
        "SOURCE_ORD_ID": EXPECTED_ORD_ID,
        "SOURCE_CL_ORD_ID": EXPECTED_CL_ORD_ID,
        "SOURCE_PERMIT_ID": EXPECTED_PERMIT_ID,
        "SOURCE_ENVELOPE_ID": EXPECTED_ENVELOPE_ID,
        "HISTORICAL_POSITION_OWNERSHIP": "UNKNOWN_NOT_PROVEN",
        "FLATTEN_PREPARATION_AUTHORIZED": TRUE_TOKEN,
        "FLATTEN_POST_AUTHORIZED": FALSE_TOKEN,
        "ONE_SHOT_FLATTEN_POST_PERFORMED": TRUE_TOKEN,
        "STANDING_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED": FALSE_TOKEN,
        "POST_ALLOWED": FALSE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "MAX_POST_COUNT": "1",
        "POST_COUNT": "1",
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "SECOND_SUBMIT_PERFORMED": FALSE_TOKEN,
        "AUTOMATIC_RETRY_PERFORMED": FALSE_TOKEN,
        "FOLLOW_ON_SUBMIT_PERFORMED": FALSE_TOKEN,
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "CANARY_OR_SECTION_11_14_IMPORTED_AS_OWNERSHIP": FALSE_TOKEN,
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
        **classified,
    }
    _assert_no_secrets(claims)
    summary = {
        "DOCUMENT_CLASS": "CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_V1",
        "SUBMIT_ACK_CLASS": classified["SUBMIT_ACK_CLASS"],
        "FILL_OBSERVED": classified["FILL_OBSERVED"],
        "FRESH_FILL_OBSERVED": classified["FRESH_FILL_OBSERVED"],
        "FEE_OBSERVED": classified["FEE_OBSERVED"],
        "POSITION_FLAT_OBSERVED": classified["POSITION_FLAT_OBSERVED"],
        "FLATTEN_RECONCILIATION_CLASS": classified["FLATTEN_RECONCILIATION_CLASS"],
        "POST_COUNT": "1",
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "FIRST_REAL_CURRENT_PRODUCTIVE_BLOCKER": CURRENT_PRODUCTIVE_FIRST_BLOCKER,
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "CONSUMED_POST_OWNER_GO": CONSUMED_POST_OWNER_GO,
        "SOURCE_POST_PACK_RELPATH": SOURCE_POST_PACK_RELPATH,
        "HISTORICAL_POSITION_OWNERSHIP": "UNKNOWN_NOT_PROVEN",
        "SECTION_11_14_REWRITTEN": FALSE_TOKEN,
        "AUTHORITY_CLASS": "POST_FLATTEN_EVIDENCE_ADJUDICATION_NO_VENUE_MUTATION",
    }
    protected = {
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "LEARNING_UNCHANGED": TRUE_TOKEN,
        "RANKING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_AUTONOMY_UNCHANGED": TRUE_TOKEN,
        "SECTION_11_14_LADDER_UNCHANGED": TRUE_TOKEN,
        "PROTECTED_ALGORITHM_FILES": list(PROTECTED_ALGORITHM_FILES),
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "SOURCE_PACK_DIGESTS.json", payload=source_digests)
    if fresh_recon:
        fresh_meta = {
            key: {
                "CODE": str((payload or {}).get("code") or "")
                if isinstance(payload, Mapping)
                else "",
                "N": str(len(_data_rows(payload))),
            }
            for key, payload in fresh_recon.items()
        }
        _persist_json(path=store / "FRESH_RECON_META.json", payload=fresh_meta)
    persist_manifest_sha256_v1(store_root=store)
    verify_rc = int(verify_manifest_sha256_v1(store_root=store))
    return CurrentProductivePostFlattenAdjudicationResultV1(
        store_root=str(store),
        submit_ack_class=classified["SUBMIT_ACK_CLASS"],
        fill_observed=classified["FILL_OBSERVED"],
        fee_observed=classified["FEE_OBSERVED"],
        order_history_observed=classified["ORDER_HISTORY_OBSERVED"],
        position_flat_observed=classified["POSITION_FLAT_OBSERVED"],
        target_occupancy_absent=classified["TARGET_OCCUPANCY_ABSENT"],
        flatten_reconciliation_class=classified["FLATTEN_RECONCILIATION_CLASS"],
        first_real_current_productive_blocker=CURRENT_PRODUCTIVE_FIRST_BLOCKER,
        section_11_14_flags_after=SECTION_11_14_FLAGS_UNCHANGED,
        venue_mutation_performed=FALSE_TOKEN,
        post_count="1",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=verify_rc,
    )
