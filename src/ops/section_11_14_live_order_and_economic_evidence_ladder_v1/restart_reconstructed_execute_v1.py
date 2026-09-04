"""Census persisted Live evidence for a restart handoff. No GET. No POST."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO,
    HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID,
    HISTORICAL_RESTART_RECONSTRUCTED_SHA,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_v1 import (
    assert_no_secrets_in_payload_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    CENSUS_SOURCE_KIND,
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_ACCOUNTING_EVIDENCE_RUN_ID,
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_CLORDID,
    BOUND_FILL_RAW_RELPATH,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POSITION_RAW_RELPATH,
    DURABLE_HANDOFF_RELATIVE_MARKERS,
    KNOWN_LIVE_EVIDENCE_RUN_IDS,
    LIVE_EVIDENCE_DIRNAME,
    TESTNET_RESTART_PROVEN_ENVIRONMENT,
    TESTNET_RESTART_PROVEN_EVIDENCE_RELPATH,
    TESTNET_RESTART_PROVEN_INSTID,
)

EVIDENCE_DIRNAME = LIVE_EVIDENCE_DIRNAME


def _utc_now_compact_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _file_sha256_v1(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def census_live_restart_handoff_v1(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root)
    live_root = root / "evidence" / "ops" / LIVE_EVIDENCE_DIRNAME
    inspected_packs: list[dict[str, Any]] = []
    durable_hits: list[str] = []
    for run_id in KNOWN_LIVE_EVIDENCE_RUN_IDS:
        pack = live_root / run_id
        exists = pack.is_dir()
        names = sorted(item.name for item in pack.iterdir()) if exists else []
        marker_hits = [
            marker
            for marker in DURABLE_HANDOFF_RELATIVE_MARKERS
            if marker in names or any(marker in name for name in names)
        ]
        durable_dir = pack / "durable_state"
        if durable_dir.is_dir():
            marker_hits.append("durable_state")
            durable_hits.extend(
                str(path.relative_to(root)) for path in durable_dir.rglob("*") if path.is_file()
            )
        inspected_packs.append(
            {
                "run_id": run_id,
                "exists": exists,
                "names": names,
                "durable_handoff_markers": marker_hits,
            }
        )
    fill_path = root / BOUND_FILL_RAW_RELPATH
    position_path = root / BOUND_POSITION_RAW_RELPATH
    testnet_path = root / TESTNET_RESTART_PROVEN_EVIDENCE_RELPATH
    testnet_durable = testnet_path / "durable_state"
    testnet_files = (
        sorted(str(path.relative_to(root)) for path in testnet_durable.rglob("*") if path.is_file())
        if testnet_durable.is_dir()
        else []
    )
    present = bool(durable_hits)
    return {
        "DURABLE_PRE_RESTART_HANDOFF_PRESENT": present,
        "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": False,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "inspected_live_packs": inspected_packs,
        "durable_handoff_paths": durable_hits,
        "fill_raw_exists": fill_path.is_file(),
        "position_raw_exists": position_path.is_file(),
        "fill_raw_relpath": BOUND_FILL_RAW_RELPATH,
        "position_raw_relpath": BOUND_POSITION_RAW_RELPATH,
        "fill_raw_sha256": _file_sha256_v1(fill_path) if fill_path.is_file() else None,
        "position_raw_sha256": _file_sha256_v1(position_path) if position_path.is_file() else None,
        "accounting_artifacts_are_not_restart_handoff": True,
        "testnet_restart_proven_relpath": TESTNET_RESTART_PROVEN_EVIDENCE_RELPATH,
        "testnet_restart_proven_exists": testnet_path.is_dir(),
        "testnet_restart_instId": TESTNET_RESTART_PROVEN_INSTID,
        "testnet_restart_environment": TESTNET_RESTART_PROVEN_ENVIRONMENT,
        "testnet_restart_clOrdId": "",
        "testnet_durable_paths": testnet_files,
        "testnet_restart_is_not_this_field": True,
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_ACK_EVIDENCE_RUN_ID": BOUND_ACK_EVIDENCE_RUN_ID,
        "BOUND_ACCOUNTING_EVIDENCE_RUN_ID": BOUND_ACCOUNTING_EVIDENCE_RUN_ID,
    }


def bind_restart_evidence_from_persisted_census_v1(*, repo_root: Path) -> dict[str, Any]:
    census = census_live_restart_handoff_v1(repo_root=Path(repo_root))
    return {
        "source_kind": CENSUS_SOURCE_KIND,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "RESTART_EXECUTION": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "durable_handoff": None,
        "census": census,
    }


def execute_live_restart_reconstructed_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != HISTORICAL_RESTART_RECONSTRUCTED_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID or _utc_now_compact_v1())
    evidence = bind_restart_evidence_from_persisted_census_v1(repo_root=Path(repo_root))
    assert_no_secrets_in_payload_v1(evidence)
    adjudication = adjudicate_live_restart_reconstructed_v1(restart_evidence=evidence)
    assert_no_secrets_in_payload_v1(adjudication)
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    census = dict(evidence.get("census") or {})
    source_references = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_SOURCE_REFERENCES_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "RAW_EVIDENCE_MODIFIED": False,
        "live_fill": {
            "path": census.get("fill_raw_relpath"),
            "file_sha256": census.get("fill_raw_sha256"),
            "role": "ACCOUNTING_PATH_NOT_RESTART_HANDOFF",
        },
        "live_position": {
            "path": census.get("position_raw_relpath"),
            "file_sha256": census.get("position_raw_sha256"),
            "role": "ACCOUNTING_PATH_NOT_RESTART_HANDOFF",
        },
        "testnet_restart_proven": {
            "path": census.get("testnet_restart_proven_relpath"),
            "role": "SEMANTICALLY_DIFFERENT_TESTNET_RESTART",
            "instId": census.get("testnet_restart_instId"),
            "environment": census.get("testnet_restart_environment"),
        },
        "durable_live_pre_restart_handoff": {
            "present": False,
            "paths": [],
        },
    }
    summary = {
        "OWNER_GO": HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "LIVE_RESTART_RECONSTRUCTED": adjudication.get("LIVE_RESTART_RECONSTRUCTED"),
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "CASE_ADJUDICATION": adjudication.get("CASE_ADJUDICATION"),
        "RESTART_SEMANTICS_STATUS": adjudication.get("RESTART_SEMANTICS_STATUS"),
        "LIVE_RESTART_RECONSTRUCTION_REASON": adjudication.get(
            "LIVE_RESTART_RECONSTRUCTION_REASON"
        ),
        "UNRESOLVED_REASON": adjudication.get("UNRESOLVED_REASON"),
        "EARLIEST_MISSING_FACT": adjudication.get("EARLIEST_MISSING_FACT"),
        "BOUND_ORDID": adjudication.get("BOUND_ORDID"),
        "BOUND_CLORDID": adjudication.get("BOUND_CLORDID"),
        "BOUND_INSTID": adjudication.get("BOUND_INSTID"),
        "BOUND_POS_SIDE": adjudication.get("BOUND_POS_SIDE"),
        "BOUND_FILL_SZ": adjudication.get("BOUND_FILL_SZ"),
        "BOUND_ACK_SOURCE_KIND": adjudication.get("BOUND_ACK_SOURCE_KIND"),
        "BOUND_ACK_EVIDENCE_RUN_ID": adjudication.get("BOUND_ACK_EVIDENCE_RUN_ID"),
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
        "RESTART_EXECUTION": False,
        "RAW_EVIDENCE_MODIFIED": False,
        "SECRET_VALUES_INCLUDED": False,
        "restart_adjudication": adjudication,
        "restart_handoff_census": census,
        "source_references": source_references,
    }
    assert_no_secrets_in_payload_v1(summary)
    pack = Path(repo_root) / "evidence" / "ops" / EVIDENCE_DIRNAME / pack_run_id
    return {
        "pack": str(pack),
        "summary": summary,
        "adjudication": adjudication,
        "census": census,
        "source_references": source_references,
        "raw_exchanges": [],
    }
