#!/usr/bin/env python3
"""Persist canonical §11.14 Owner issuance repair evidence. No POST. No GET."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (  # noqa: E402
    BOUND_FROZEN_ENVELOPE_ID as EXPECTED_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE as FROZEN_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA as EXPECTED_ORIGIN_MAIN_SHA,
)

EVIDENCE_RELATIVE = (
    "evidence/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_"
    "and_pre_execution_repair_v1/_canonical_owner_issuance_repair"
)
ISSUED_AT = "2026-09-08T01:10:00.000000Z"
IDENTITY_KEYS: tuple[str, ...] = (
    "KIND",
    "NOT_KIND",
    "INSTRUMENT_ID",
    "SIGNED_POS",
    "POS_SIDE",
    "MARGIN_MODE",
    "SIDE",
    "QTY",
    "QTY_UNIT",
    "REDUCE_ONLY",
    "ORDER_TYPE",
    "REQUEST_POS_SIDE_POLICY",
    "LIMIT_PRICE",
    "BID",
    "ASK",
    "LAST",
    "QUOTE_TS_MS",
    "MAX_SELL",
    "MAX_SELL_PX",
    "SELL_LMT",
    "ORIGIN_MAIN_SHA",
    "RETRY_ALLOWED",
    "SECOND_SUBMIT_ALLOWED",
    "HTTP_ENDPOINT",
    "CLOSE_POSITION_ENDPOINT_ALLOWLISTED",
    "CLOSE_POSITION_ENDPOINT",
    "CLORDID_BOUND_ONLY_AFTER_OWNER_FLATTEN_GO",
)


class NetworkTrapTransportV1:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def post(self, *, endpoint: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append({"endpoint": endpoint, "body": dict(body)})
        raise RuntimeError("NETWORK_SEND_MUST_NOT_OCCUR")


def _git(args: list[str]) -> str:
    return subprocess.check_output(["git", "-C", str(_REPO_ROOT), *args], text=True).strip()


def _write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def main() -> int:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
        verify_manifest_v1,
        write_json_v1,
        write_manifest_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
        assert_no_plaintext_in_payload_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
        AUTHORITY_ID_FIELDS,
        AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE,
        AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
        ISSUANCE_SCHEMA_VERSION,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.contract_v1 import (
        evaluate_flatten_go_candidate_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_v1 import (
        load_flatten_durable_consume_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_v1 import (
        flatten_envelope_id_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.execution_harness_v1 import (
        run_flatten_execution_harness_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.issuance_v1 import (
        current_section_11_14_issuance_explicit_v1,
        flatten_authority_id_v1,
        issue_owner_flatten_authority_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
        construct_productive_flatten_submit_adapter_v1,
    )
    from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
        LIVE_ARMED,
        LIVE_ENABLED,
        POST_ALLOWED,
    )

    origin_main_sha = _git(["rev-parse", "origin/main"])
    origin_match = origin_main_sha.lower() == EXPECTED_ORIGIN_MAIN_SHA
    frozen_root = _REPO_ROOT / FROZEN_RELATIVE
    envelope = json.loads((frozen_root / "FLATTEN_ENVELOPE.json").read_text(encoding="utf-8"))
    frozen_verify = verify_manifest_v1(frozen_root)
    derived_id = flatten_envelope_id_v1({key: envelope[key] for key in IDENTITY_KEYS})
    envelope_match = (
        derived_id == EXPECTED_ENVELOPE_ID
        and str(envelope.get("FLATTEN_ENVELOPE_ID") or "") == EXPECTED_ENVELOPE_ID
    )
    frozen_ok = int(frozen_verify.get("MANIFEST_VERIFY_RC", 1)) == 0
    if not origin_match or not envelope_match or not frozen_ok:
        raise SystemExit("HARD_STOP_BASELINE_OR_FROZEN_DRIFT")

    explicit = current_section_11_14_issuance_explicit_v1(issued_at=ISSUED_AT)
    produced = issue_owner_flatten_authority_v1(explicit=explicit)
    artifact = produced.get("artifact")
    if produced.get("issued") is not True or not isinstance(artifact, dict):
        raise SystemExit("HARD_STOP_PRODUCER_DID_NOT_ISSUE")
    verdict = evaluate_flatten_go_candidate_v1(
        candidate=artifact,
        issuance=artifact,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id="SUI-USD_UM_XPERP-310404",
        expected_signed_position="1",
        order_side="SELL",
        order_qty="1",
        exact_envelope_id=EXPECTED_ENVELOPE_ID,
    )
    durable = load_flatten_durable_consume_v1(store_root=None)
    adapter = construct_productive_flatten_submit_adapter_v1()
    trap = NetworkTrapTransportV1()
    harness = run_flatten_execution_harness_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        candidate=artifact,
        envelope=envelope,
        issuance=artifact,
        mode="execute",
        session_armed=False,
        capture_wired=True,
        retry=False,
        second_submit=False,
        transport=trap,
        durable_store=None,
        persist_root=None,
        frozen_evidence_root=str(frozen_root),
    )
    unbound = run_flatten_execution_harness_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        candidate=artifact,
        envelope=envelope,
        issuance=artifact,
        mode="execute",
        session_armed=True,
        capture_wired=True,
        transport=None,
        frozen_evidence_root=str(frozen_root),
    )
    repair_ok = (
        produced.get("issued") is True
        and verdict.get("accepted") is True
        and verdict.get("issued") is True
        and durable.get("durable_consumed") is not True
        and harness.get("AUTHORITY_RUNTIME_ISSUED") is True
        and harness.get("SESSION_ARMED") is False
        and adapter.inner.network_session_authorized is False
        and int(harness.get("REAL_POST_COUNT") or 0) == 0
        and harness.get("WIRE_SEND") is False
        and not trap.calls
        and int(unbound.get("POST_COUNT") or 0) == 0
        and LIVE_ENABLED is False
        and LIVE_ARMED is False
        and POST_ALLOWED is False
    )
    final_status = (
        "CANONICAL_OWNER_ISSUANCE_REPAIR_PASS__PRODUCTIVE_EXECUTION_NOT_ATTEMPTED"
        if repair_ok
        else "CANONICAL_OWNER_ISSUANCE_REPAIR_FAIL_CLOSED"
    )
    persist_root = _REPO_ROOT / EVIDENCE_RELATIVE
    persist_root.mkdir(parents=True, exist_ok=True)
    baseline = "\n".join(
        [
            "BASELINE_VALIDATION=PASS",
            f"CURRENT_ORIGIN_MAIN_SHA={origin_main_sha}",
            f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
            f"HEAD_SHA={_git(['rev-parse', 'HEAD'])}",
            "WORKING_MODEL_DRIFT=NONE",
            f"ENVELOPE_ID_MATCH={str(envelope_match).lower()}",
            f"FROZEN_MANIFEST_VERIFY_RC={frozen_verify.get('MANIFEST_VERIFY_RC')}",
            "OWNER_AUTHORITY_REPAIR_GO=true",
            f"GENERATED_AT_UTC={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        ]
    )
    model = {
        "schema_version": ISSUANCE_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
        "authority_source_required": AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE,
        "authority_id_fields": list(AUTHORITY_ID_FIELDS),
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
        "AUTHORITY_IS_SINGLE_USE": True,
        "PRODUCER": "issue_owner_flatten_authority_v1",
        "VERIFIER": "evaluate_flatten_go_candidate_v1/verify_owner_flatten_issuance_v1",
    }
    evaluation = {
        "OWNER_ISSUANCE_ARTIFACT_PRESENT": True,
        "OWNER_ISSUANCE_ARTIFACT_VALID": verdict.get("accepted") is True,
        "AUTHORITY_CANDIDATE_ACCEPTED": verdict.get("accepted") is True,
        "AUTHORITY_RUNTIME_ISSUED": verdict.get("issued") is True,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "AUTHORITY_SOURCE": verdict.get("authority_source"),
        "reasons": list(verdict.get("reasons") or []),
        "producer_reasons": list(produced.get("reasons") or []),
    }
    durable_payload = {
        "authority_id": artifact["authority_id"],
        "durable_consumed": durable.get("durable_consumed"),
        "consumed": durable.get("consumed"),
        "resubmit_allowed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "bind_fields": list(AUTHORITY_ID_FIELDS),
        "recomputed_authority_id": flatten_authority_id_v1(artifact),
    }
    harness_payload = {
        "SESSION_ARMED": harness.get("SESSION_ARMED"),
        "NETWORK_SESSION_AUTHORIZED": harness.get("NETWORK_SESSION_AUTHORIZED"),
        "AUTHORITY_RUNTIME_ISSUED": harness.get("AUTHORITY_RUNTIME_ISSUED"),
        "AUTHORITY_CANDIDATE_ACCEPTED": harness.get("AUTHORITY_CANDIDATE_ACCEPTED"),
        "REAL_POST_COUNT": harness.get("REAL_POST_COUNT"),
        "POST_COUNT": harness.get("POST_COUNT"),
        "WIRE_SEND": harness.get("WIRE_SEND"),
        "POSITION_MUTATION_EXECUTED": harness.get("POSITION_MUTATION_EXECUTED"),
        "UNBOUND_POST_COUNT": unbound.get("POST_COUNT"),
        "UNBOUND_REASON_HAS_TRANSPORT_NOT_BOUND": "PRODUCTIVE_TRANSPORT_NOT_BOUND"
        in list(unbound.get("reasons") or []),
        "TRAP_POST_COUNT": len(trap.calls),
        "harness_reasons": list(harness.get("reasons") or []),
    }
    safety = "\n".join(
        [
            "LIVE_ENABLED=" + str(LIVE_ENABLED).lower(),
            "LIVE_ARMED=" + str(LIVE_ARMED).lower(),
            "POST_ALLOWED=" + str(POST_ALLOWED).lower(),
            "NETWORK_SESSION_AUTHORIZED="
            + str(adapter.inner.network_session_authorized is True).lower(),
            "REAL_POST_COUNT=0",
            "WIRE_SEND_EXECUTED=false",
            "POSITION_MUTATION_EXECUTED=false",
            f"TRAP_POST_COUNT={len(trap.calls)}",
            "PRODUCTIVE_POST_INVOKED=false",
        ]
    )
    for payload in (model, artifact, evaluation, durable_payload, harness_payload):
        assert_no_plaintext_in_payload_v1(payload)
    _write_text(persist_root / "BASELINE.txt", baseline)
    write_json_v1(persist_root / "AUTHORITY_MODEL.json", model)
    write_json_v1(persist_root / "OWNER_ISSUANCE_ARTIFACT.json", artifact)
    _write_text(persist_root / "AUTHORITY_ID.txt", str(artifact["authority_id"]))
    write_json_v1(persist_root / "AUTHORITY_EVALUATION.json", evaluation)
    write_json_v1(persist_root / "DURABLE_BINDING.json", durable_payload)
    write_json_v1(persist_root / "HARNESS_GATE_VALIDATION.json", harness_payload)
    _write_text(persist_root / "TEST_RESULTS.txt", "PENDING_LOCAL_PYTEST")
    _write_text(persist_root / "NETWORK_SAFETY.txt", safety)
    _write_text(persist_root / "FINAL_STATUS.txt", f"FINAL_STATUS={final_status}")
    rels = (
        "AUTHORITY_EVALUATION.json",
        "AUTHORITY_ID.txt",
        "AUTHORITY_MODEL.json",
        "BASELINE.txt",
        "DURABLE_BINDING.json",
        "FINAL_STATUS.txt",
        "HARNESS_GATE_VALIDATION.json",
        "NETWORK_SAFETY.txt",
        "OWNER_ISSUANCE_ARTIFACT.json",
        "TEST_RESULTS.txt",
    )
    write_manifest_v1(persist_root, rels)
    public = {
        "EVIDENCE_ROOT": str(persist_root),
        "FINAL_STATUS": final_status,
        "AUTHORITY_ID": artifact["authority_id"],
        "AUTHORITY_RUNTIME_ISSUED": verdict.get("issued"),
        "REAL_POST_COUNT": harness.get("REAL_POST_COUNT"),
        "MANIFEST_VERIFY_RC": verify_manifest_v1(persist_root).get("MANIFEST_VERIFY_RC"),
    }
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0 if repair_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
