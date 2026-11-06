"""Bounded productive PL-TF-002 F1/F2 GET capture via K1 session executor."""

from __future__ import annotations

import time
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    FreshPretradeGetStatusV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    F1_REQUIRED_GET_ITEM_IDS,
    NE_TF_001_ENDPOINT_PATH,
    NE_TF_001_HTTP_METHOD,
    NE_TF_001_TASK_ID,
    DEFAULT_FRESHNESS_MAX_AGE_MS,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.verifier_v1 import (
    verify_pl_tf_002_network_evidence_v1,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import (
    FRESH_PRETRADE_INST_TYPE,
    FRESH_PRETRADE_TD_MODE,
    FRESH_PRETRADE_VENUE_INST_ID,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    PRODUCTIVE_TRANSPORT_CLASS,
    SESSION_OWNER_GO,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.errors_v1 import (
    PlTf002ProductiveReadOnlyGetCompleteError,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.pre_network_jit_v1 import (
    build_pl_tf_002_pre_network_jit_proof_v1,
    merge_session_k1_jit_facts_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    open_pl_tf_002_productive_read_only_get_session_v1,
)


def _assert_owner_gos_v1(*, wp_owner_go: str, session_owner_go: str) -> None:
    if str(wp_owner_go or "").strip() != OWNER_GO:
        raise PlTf002ProductiveReadOnlyGetCompleteError("WP_OWNER_GO_MISMATCH")
    if str(session_owner_go or "").strip() != SESSION_OWNER_GO:
        raise PlTf002ProductiveReadOnlyGetCompleteError("SESSION_OWNER_GO_MISMATCH")


def _venue_error_hint_v1(transport: FullCoreProductiveReadOnlyGetTransportV1) -> str:
    for path, payload in transport.payloads_by_path.items():
        if isinstance(payload, Mapping):
            code = str(payload.get("code") or "")
            if code and code != "0":
                msg = str(payload.get("msg") or "")[:120]
                return f"{path}:code={code}:{msg}"
    return "NO_VENUE_ERROR_HINT"


def _f1_items_from_fresh_evidence(
    evidence: Any,
    *,
    transport: FullCoreProductiveReadOnlyGetTransportV1,
) -> dict[str, dict[str, Any]]:
    by_id = {item.item_id: item for item in evidence.items}
    items: dict[str, dict[str, Any]] = {}
    for item_id in F1_REQUIRED_GET_ITEM_IDS:
        row = by_id.get(item_id)
        if row is None:
            raise PlTf002ProductiveReadOnlyGetCompleteError(f"F1_MISSING_ITEM:{item_id}")
        if row.get_performed is not True:
            raise PlTf002ProductiveReadOnlyGetCompleteError(
                f"F1_GET_NOT_PERFORMED:{item_id}:{_venue_error_hint_v1(transport)}"
            )
        if str(row.evidence_status or "") != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value:
            raise PlTf002ProductiveReadOnlyGetCompleteError(
                f"F1_ITEM_NOT_TRUSTED:{item_id}:{row.evidence_status}"
            )
        items[item_id] = {
            "get_performed": True,
            "method": str(row.method or "GET").upper(),
            "venue_live_contact": row.venue_live_contact is True,
            "transport_class": str(row.transport_class or ""),
        }
        if items[item_id]["transport_class"] != PRODUCTIVE_TRANSPORT_CLASS:
            raise PlTf002ProductiveReadOnlyGetCompleteError(f"F1_TRANSPORT_MISMATCH:{item_id}")
        if items[item_id]["method"] != "GET":
            raise PlTf002ProductiveReadOnlyGetCompleteError(f"F1_NON_GET:{item_id}")
    return items


def _raw_account_config_v1(
    transport: FullCoreProductiveReadOnlyGetTransportV1,
) -> Mapping[str, Any]:
    raw = transport.payloads_by_path.get(ENDPOINT_ACCOUNT_CONFIG)
    if raw is None:
        raw = transport.payloads_by_path.get(NE_TF_001_ENDPOINT_PATH)
    if not isinstance(raw, Mapping):
        raise PlTf002ProductiveReadOnlyGetCompleteError("F2_RAW_ACCOUNT_CONFIG_MISSING")
    return raw


def build_network_evidence_bundle_v1(
    *,
    f1_items: Mapping[str, Mapping[str, Any]],
    f2_raw: Mapping[str, Any],
    expected_credential_uid: str,
    observed_at_unix_ms: int,
) -> dict[str, Any]:
    return {
        "EVIDENCE_PROVENANCE": {
            "evidence_class": "PRODUCTIVE_VENUE_EVIDENCE",
            "transport_class": PRODUCTIVE_TRANSPORT_CLASS,
            "venue_live_contact": True,
            "fixture_or_injected": False,
            "historical_reuse": False,
            "observed_at_unix_ms": int(observed_at_unix_ms),
            "freshness_max_age_ms": DEFAULT_FRESHNESS_MAX_AGE_MS,
            "expected_credential_uid": str(expected_credential_uid),
        },
        "F1_PRODUCTIVE_VENUE_GET": {"items": dict(f1_items)},
        "F2_NE_TF_001": {
            "task_id": NE_TF_001_TASK_ID,
            "http_method": NE_TF_001_HTTP_METHOD,
            "endpoint_path": NE_TF_001_ENDPOINT_PATH,
            "get_performed": True,
            "raw_venue_response": dict(f2_raw),
        },
    }


def execute_pl_tf_002_productive_read_only_get_capture_v1(
    *,
    wp_owner_go: str,
    session_owner_go: str,
    origin_main_sha: str,
    execute_network: bool,
    integrity_backend: object | None = None,
    os_native_backend: object | None = None,
) -> dict[str, Any]:
    """Capture F1/F2 productive GET evidence or return pre-network JIT only."""

    _assert_owner_gos_v1(wp_owner_go=wp_owner_go, session_owner_go=session_owner_go)
    jit = build_pl_tf_002_pre_network_jit_proof_v1(
        session_owner_go=session_owner_go,
        origin_main_sha=origin_main_sha,
        integrity_backend=integrity_backend,
    )
    if execute_network is not True:
        return {
            "disposition": "PRE_NETWORK_JIT_ONLY",
            "jit_proof": jit,
            "NETWORK_REQUEST_COUNT": 0,
        }

    pretrade_decision_id = f"pl-tf-002-complete-{str(origin_main_sha or '')[:12]}"
    network_request_count = 0
    with open_pl_tf_002_productive_read_only_get_session_v1(
        owner_go=session_owner_go,
        origin_main_sha=origin_main_sha,
        acquire_credential=True,
        backend=os_native_backend,
        integrity_backend=integrity_backend,  # type: ignore[arg-type]
    ) as session:
        jit = merge_session_k1_jit_facts_v1(
            jit,
            credential_acquired=session.credential_acquired is True,
            k1_handle_bound=bool(session.k1_handle_id),
        )
        if jit["K1_ACQUISITION"] != "PASS":
            raise PlTf002ProductiveReadOnlyGetCompleteError("K1_ACQUISITION_FAIL_CLOSED")

        transport = session.transport
        if not isinstance(transport, FullCoreProductiveReadOnlyGetTransportV1):
            raise PlTf002ProductiveReadOnlyGetCompleteError("TRANSPORT_TYPE_MISMATCH")
        if transport.max_request_count > MAX_NETWORK_REQUEST_COUNT:
            raise PlTf002ProductiveReadOnlyGetCompleteError("TRANSPORT_MAX_REQUEST_BUDGET_DRIFT")

        evidence = collect_fresh_pretrade_runtime_get_v1(
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=FRESH_PRETRADE_VENUE_INST_ID,
            td_mode=FRESH_PRETRADE_TD_MODE,
            inst_type=FRESH_PRETRADE_INST_TYPE,
            transport=transport,
            require_collection=True,
        )
        network_request_count = int(transport.request_count)
        if network_request_count < 1:
            raise PlTf002ProductiveReadOnlyGetCompleteError("NETWORK_REQUEST_COUNT_ZERO")
        if "POST" in {m.upper() for m in transport.methods_used}:
            raise PlTf002ProductiveReadOnlyGetCompleteError("POST_METHOD_DETECTED")

        f1_items = _f1_items_from_fresh_evidence(evidence, transport=transport)
        f2_raw = _raw_account_config_v1(transport)
        data = f2_raw.get("data")
        uid = ""
        if isinstance(data, list) and data and isinstance(data[0], Mapping):
            uid = str(data[0].get("uid") or "").strip()
        if uid == "":
            raise PlTf002ProductiveReadOnlyGetCompleteError("F2_UID_MISSING")

        observed_ms = int(time.time() * 1000)
        bundle = build_network_evidence_bundle_v1(
            f1_items=f1_items,
            f2_raw=f2_raw,
            expected_credential_uid=uid,
            observed_at_unix_ms=observed_ms,
        )
        verification = verify_pl_tf_002_network_evidence_v1(bundle, now_unix_ms=observed_ms)
        return {
            "disposition": "NETWORK_CAPTURE_COMPLETE",
            "jit_proof": jit,
            "NETWORK_REQUEST_COUNT": network_request_count,
            "NETWORK_METHODS_USED": sorted({m.upper() for m in transport.methods_used}),
            "evidence_bundle": bundle,
            "verification": verification,
            "pretrade_evidence_status": evidence.evidence_status,
        }
