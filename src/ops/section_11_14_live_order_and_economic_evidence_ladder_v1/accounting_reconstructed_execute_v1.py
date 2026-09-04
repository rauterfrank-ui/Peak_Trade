"""Load persisted fill/fee/position artifacts and adjudicate accounting. No GET. No POST."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from json import loads
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_adjudication_v1 import (
    adjudicate_live_accounting_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_RAW_RELPATH,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    BOUND_POSITION_RAW_RELPATH,
    BOUND_TRADE_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_v1 import (
    assert_no_secrets_in_payload_v1,
)

EVIDENCE_DIRNAME = "section_11_14_live_order_and_economic_evidence_ladder_v1"


def _utc_now_compact_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _file_sha256_v1(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def load_persisted_raw_exchange_v1(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise Section1114OfflineSurfaceError(f"PERSISTED_RAW_MISSING:{path}")
    artifact = loads(path.read_text(encoding="utf-8"))
    if not isinstance(artifact, Mapping):
        raise Section1114OfflineSurfaceError("PERSISTED_RAW_NOT_OBJECT")
    body_text = artifact.get("BODY_UTF8_EXACT")
    if not isinstance(body_text, str) or not body_text.strip():
        raise Section1114OfflineSurfaceError("PERSISTED_RAW_BODY_MISSING")
    body = loads(body_text)
    if not isinstance(body, Mapping):
        raise Section1114OfflineSurfaceError("PERSISTED_RAW_BODY_NOT_OBJECT")
    data = body.get("data")
    rows = [item for item in data] if isinstance(data, list) else []
    object_rows = [item for item in rows if isinstance(item, Mapping)]
    return {
        "path": str(path),
        "file_sha256": _file_sha256_v1(path),
        "artifact_document_class": artifact.get("DOCUMENT_CLASS"),
        "artifact_role": artifact.get("DOCUMENT_ROLE"),
        "endpoint": artifact.get("ENDPOINT"),
        "endpoint_path": artifact.get("ENDPOINT_PATH"),
        "http_status": artifact.get("HTTP_STATUS"),
        "request_time_utc": artifact.get("REQUEST_TIME_UTC"),
        "response_time_utc": artifact.get("RESPONSE_TIME_UTC"),
        "body_sha256": artifact.get("BODY_SHA256"),
        "okx_code": body.get("code"),
        "rows": object_rows,
        "raw_row_count": len(rows),
    }


def _exactly_one_identity_bound_fill_row_v1(
    rows: list[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    matches = [
        row
        for row in rows
        if str(row.get("ordId") or "") == BOUND_ORDID
        and str(row.get("clOrdId") or "") == BOUND_CLORDID
        and str(row.get("instId") or "") == BOUND_INSTID
        and str(row.get("tradeId") or "") == BOUND_TRADE_ID
    ]
    return matches[0] if len(matches) == 1 else None


def _exactly_one_identity_bound_position_row_v1(
    rows: list[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    matches = [
        row
        for row in rows
        if str(row.get("instId") or "") == BOUND_INSTID
        and str(row.get("posSide") or "") == BOUND_POS_SIDE
        and str(row.get("tradeId") or "") == BOUND_TRADE_ID
    ]
    return matches[0] if len(matches) == 1 else None


def bind_accounting_evidence_from_persisted_path_v1(*, repo_root: Path) -> dict[str, Any]:
    fill_path = Path(repo_root) / BOUND_FILL_RAW_RELPATH
    position_path = Path(repo_root) / BOUND_POSITION_RAW_RELPATH
    fill_pack = load_persisted_raw_exchange_v1(fill_path)
    position_pack = load_persisted_raw_exchange_v1(position_path)
    fill_row = _exactly_one_identity_bound_fill_row_v1(fill_pack["rows"])
    position_row = _exactly_one_identity_bound_position_row_v1(position_pack["rows"])
    return {
        "source_kind": ADMISSIBLE_SOURCE_KIND,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "fill_row": dict(fill_row) if isinstance(fill_row, Mapping) else None,
        "position_row": dict(position_row) if isinstance(position_row, Mapping) else None,
        "fill_source_path": BOUND_FILL_RAW_RELPATH,
        "position_source_path": BOUND_POSITION_RAW_RELPATH,
        "RESPONSE_TIME_UTC": position_pack.get("response_time_utc")
        or fill_pack.get("response_time_utc"),
        "fill_pack": fill_pack,
        "position_pack": position_pack,
    }


def execute_live_accounting_reconstructed_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID or _utc_now_compact_v1())
    evidence = bind_accounting_evidence_from_persisted_path_v1(repo_root=Path(repo_root))
    assert_no_secrets_in_payload_v1(evidence)
    adjudication = adjudicate_live_accounting_reconstructed_v1(accounting_evidence=evidence)
    assert_no_secrets_in_payload_v1(adjudication)
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    identity = dict(adjudication.get("path_classification") or {})
    source_references = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_SOURCE_REFERENCES_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "RAW_EVIDENCE_MODIFIED": False,
        "fill": {
            "path": evidence["fill_source_path"],
            "file_sha256": evidence["fill_pack"]["file_sha256"],
            "body_sha256": evidence["fill_pack"]["body_sha256"],
            "document_class": evidence["fill_pack"]["artifact_document_class"],
            "observed_at": evidence["fill_pack"]["response_time_utc"],
        },
        "position": {
            "path": evidence["position_source_path"],
            "file_sha256": evidence["position_pack"]["file_sha256"],
            "body_sha256": evidence["position_pack"]["body_sha256"],
            "document_class": evidence["position_pack"]["artifact_document_class"],
            "observed_at": evidence["position_pack"]["response_time_utc"],
        },
    }
    summary = {
        "OWNER_GO": OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "LIVE_POSITION_RECONCILED": True,
        "LIVE_ACCOUNTING_RECONSTRUCTED": adjudication.get("LIVE_ACCOUNTING_RECONSTRUCTED"),
        "LIVE_RESTART_RECONSTRUCTED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "CASE_ADJUDICATION": adjudication.get("CASE_ADJUDICATION"),
        "ACCOUNTING_RESULT": adjudication.get("ACCOUNTING_RESULT"),
        "ACCOUNTING_RESULT_UNIT": adjudication.get("ACCOUNTING_RESULT_UNIT"),
        "ACCOUNTING_RESIDUAL": adjudication.get("ACCOUNTING_RESIDUAL"),
        "ACCOUNTING_RESIDUAL_UNIT": adjudication.get("ACCOUNTING_RESIDUAL_UNIT"),
        "ACCOUNTING_TOLERANCE": adjudication.get("ACCOUNTING_TOLERANCE"),
        "ACCOUNTING_TOLERANCE_AUTHORITY": adjudication.get("ACCOUNTING_TOLERANCE_AUTHORITY"),
        "ACCOUNTING_IDENTITY_EQUATION": adjudication.get("ACCOUNTING_IDENTITY_EQUATION"),
        "LIVE_ACCOUNTING_RECONSTRUCTION_REASON": adjudication.get(
            "LIVE_ACCOUNTING_RECONSTRUCTION_REASON"
        ),
        "ACCOUNTING_SEMANTICS_STATUS": adjudication.get("ACCOUNTING_SEMANTICS_STATUS"),
        "UNRESOLVED_REASON": adjudication.get("UNRESOLVED_REASON"),
        "BOUND_ORDID": adjudication.get("BOUND_ORDID"),
        "BOUND_CLORDID": adjudication.get("BOUND_CLORDID"),
        "BOUND_INSTID": adjudication.get("BOUND_INSTID"),
        "BOUND_POS_SIDE": adjudication.get("BOUND_POS_SIDE"),
        "BOUND_FILL_SZ": adjudication.get("BOUND_FILL_SZ"),
        "BOUND_ACK_SOURCE_KIND": adjudication.get("BOUND_ACK_SOURCE_KIND"),
        "BOUND_ACK_EVIDENCE_RUN_ID": adjudication.get("BOUND_ACK_EVIDENCE_RUN_ID"),
        "RAW_FILL_FEE_IF_OBSERVED": adjudication.get("RAW_FILL_FEE_IF_OBSERVED"),
        "RAW_REALIZED_PNL_IF_OBSERVED": adjudication.get("RAW_REALIZED_PNL_IF_OBSERVED"),
        "RAW_UPL_IF_OBSERVED": adjudication.get("RAW_UPL_IF_OBSERVED"),
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "PUBLIC_GET_USED": False,
        "CREDENTIAL_USE": False,
        "RETRY_USED": False,
        "SECOND_SUBMIT_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "FUNDING_USED": False,
        "RAW_EVIDENCE_MODIFIED": False,
        "SECRET_VALUES_INCLUDED": False,
        "accounting_adjudication": adjudication,
        "accounting_identity": identity,
        "source_references": source_references,
    }
    assert_no_secrets_in_payload_v1(summary)
    pack = Path(repo_root) / "evidence" / "ops" / EVIDENCE_DIRNAME / pack_run_id
    return {
        "pack": str(pack),
        "summary": summary,
        "adjudication": adjudication,
        "identity": identity,
        "source_references": source_references,
        "raw_exchanges": [],
    }
