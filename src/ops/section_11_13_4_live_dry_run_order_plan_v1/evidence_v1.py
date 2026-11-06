"""Evidence generator + manifest helpers for §11.13.4."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    AUTHORIZATION_FILENAME,
    CLAIMS_FILENAME,
    CONFIG_DIGEST_FILENAME,
    EVIDENCE_CONTRACT_VERSION,
    EXCHANGE_SNAPSHOT_FILENAME,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_AUTHORIZED,
    LIVE_DRY_RUN_ORDER_PLAN_PROVEN,
    LOCAL_EXPECTED_STATE_FILENAME,
    MANIFEST_FILENAME,
    MUTATION_BOUNDARY_FILENAME,
    ORDER_PLAN_FILENAME,
    PROOF_FILENAME,
    RECONCILIATION_FILENAME,
    REDACTION_FILENAME,
    SUMMARY_FILENAME,
    ZERO_WRITE_FILENAME,
)


class LiveDryRunOrderPlanEvidenceError(RuntimeError):
    """Fail-closed evidence violation."""


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_manifest_v1(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = _sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return _sha256_hex(body.encode("utf-8"))


def verify_manifest_v1(root: Path) -> dict[str, Any]:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        raise LiveDryRunOrderPlanEvidenceError("MANIFEST_MISSING")
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = _sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    if errors:
        raise LiveDryRunOrderPlanEvidenceError(";".join(errors))
    return {"ok": True, "MANIFEST_VERIFY_RC": 0, "manifest_path": str(manifest)}


def build_claims_v1(
    *,
    origin_main_sha: str,
    config_digest: str,
    environment: str,
    venue: str,
    entity: str,
    region: str,
    rest_host: str,
    account_identity_redacted: str,
    secretref_log_safe_id: str,
    secretref_credential_class: str,
    authorization_scope: str,
    methods_used: list[str],
    endpoints_used: list[str],
    request_count: int,
    http_result_classes: list[str],
    authenticated_read_success: bool,
    write_request_count: int,
    order_request_count: int,
    cancel_request_count: int,
    amend_request_count: int,
    withdraw_request_count: int,
    transfer_request_count: int,
    demo_simulation_marker_absent: bool,
    cross_binding_checks_pass: bool,
    redaction_check_pass: bool,
    transport_class: str,
    venue_live_contact: bool,
    fixture_or_demo_or_testnet: bool,
    productive_live_transport: bool,
    mode: str,
    permission_attestation: Mapping[str, Any] | None = None,
    account_scope_match: bool = False,
    executed_code_sha: str | None = None,
    okx_code_success: bool = False,
    order_plan_result: str | None = None,
    blocks_new_entry: bool = True,
    live_reconciliation_proven: bool = False,
) -> dict[str, Any]:
    attestation = dict(permission_attestation or {})
    attestation_ok = (
        attestation.get("READ") is True
        and attestation.get("TRADE") is False
        and attestation.get("WITHDRAW") is False
    )
    proven = bool(
        productive_live_transport
        and venue_live_contact
        and not fixture_or_demo_or_testnet
        and authenticated_read_success
        and write_request_count == 0
        and order_request_count == 0
        and cancel_request_count == 0
        and amend_request_count == 0
        and withdraw_request_count == 0
        and transfer_request_count == 0
        and demo_simulation_marker_absent
        and cross_binding_checks_pass
        and redaction_check_pass
        and environment == "LIVE"
        and mode == "execute"
        and attestation_ok
        and account_scope_match
        and okx_code_success
        and order_plan_result in {"BLOCKED_NO_EXECUTE", "NO_EXECUTE", "CONSTRUCTED_BLOCKED"}
    )
    if mode in {"preflight", "fixture", "unit"}:
        proven = False

    return {
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "origin_main_sha": origin_main_sha,
        "executed_code_sha": executed_code_sha or origin_main_sha,
        "config_digest": config_digest,
        "ENVIRONMENT": environment,
        "venue": venue,
        "entity": entity,
        "region": region,
        "rest_host": rest_host,
        "account_identity_redacted": account_identity_redacted,
        "account_scope_match": bool(account_scope_match),
        "secretref_log_safe_id": secretref_log_safe_id,
        "secretref_credential_class": secretref_credential_class,
        "authorization_scope": authorization_scope,
        "permission_attestation": {
            "READ": attestation.get("READ"),
            "TRADE": attestation.get("TRADE"),
            "WITHDRAW": attestation.get("WITHDRAW"),
        },
        "permission_attestation_PASS": attestation_ok,
        "methods_used": methods_used,
        "endpoints_used": endpoints_used,
        "REQUEST_COUNT": request_count,
        "http_result_classes": http_result_classes,
        "authenticated_read_success": authenticated_read_success,
        "okx_code_success": bool(okx_code_success),
        "WRITE_REQUEST_COUNT": write_request_count,
        "ORDER_REQUEST_COUNT": order_request_count,
        "CANCEL_REQUEST_COUNT": cancel_request_count,
        "AMEND_REQUEST_COUNT": amend_request_count,
        "WITHDRAW_REQUEST_COUNT": withdraw_request_count,
        "TRANSFER_REQUEST_COUNT": transfer_request_count,
        "demo_simulation_marker_absent": demo_simulation_marker_absent,
        "cross_binding_checks_PASS": cross_binding_checks_pass,
        "redaction_check_PASS": redaction_check_pass,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": FULLY_AUTONOMOUS_LIVE_TRADING_READY,
        "transport_class": transport_class,
        "venue_live_contact": venue_live_contact,
        "fixture_or_demo_or_testnet": fixture_or_demo_or_testnet,
        "mode": mode,
        "LIVE_DRY_RUN_ORDER_PLAN_PROVEN": proven,
        "LIVE_DRY_RUN_ORDER_PLAN_PROVEN_DEFAULT": LIVE_DRY_RUN_ORDER_PLAN_PROVEN,
        "LIVE_DRY_RUN_ORDER_PLAN_EXECUTED": bool(mode == "execute" and productive_live_transport),
        "ORDER_PLAN_RESULT": order_plan_result,
        "LIVE_RECONCILIATION_PROVEN": bool(live_reconciliation_proven),
        "BLOCKS_NEW_ENTRY": bool(blocks_new_entry),
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
        "SECTION_11_13_LIVE_SHADOW_CANARY_PROGRESSION_STARTED": False,
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "CAPABILITY_11_8_REMAINS_FIXTURE_ONLY": True,
    }


def persist_evidence_bundle_v1(
    *,
    evidence_root: Path,
    claims: Mapping[str, Any],
    summary: Mapping[str, Any],
    proof: Mapping[str, Any],
    config_digest_doc: Mapping[str, Any],
    authorization_doc: Mapping[str, Any],
    zero_write_doc: Mapping[str, Any],
    redaction_doc: Mapping[str, Any],
    order_plan_doc: Mapping[str, Any] | None = None,
    mutation_boundary_doc: Mapping[str, Any] | None = None,
    reconciliation_doc: Mapping[str, Any] | None = None,
    exchange_snapshot_doc: Mapping[str, Any] | None = None,
    local_expected_state_doc: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)

    files: dict[str, Mapping[str, Any]] = {
        CLAIMS_FILENAME: claims,
        SUMMARY_FILENAME: summary,
        PROOF_FILENAME: proof,
        CONFIG_DIGEST_FILENAME: config_digest_doc,
        AUTHORIZATION_FILENAME: authorization_doc,
        ZERO_WRITE_FILENAME: zero_write_doc,
        REDACTION_FILENAME: redaction_doc,
    }
    if order_plan_doc is not None:
        files[ORDER_PLAN_FILENAME] = order_plan_doc
    if mutation_boundary_doc is not None:
        files[MUTATION_BOUNDARY_FILENAME] = mutation_boundary_doc
    if reconciliation_doc is not None:
        files[RECONCILIATION_FILENAME] = reconciliation_doc
    if exchange_snapshot_doc is not None:
        files[EXCHANGE_SNAPSHOT_FILENAME] = exchange_snapshot_doc
    if local_expected_state_doc is not None:
        files[LOCAL_EXPECTED_STATE_FILENAME] = local_expected_state_doc
    for name, payload in files.items():
        text = json.dumps(dict(payload), sort_keys=True, indent=2) + "\n"
        _atomic_write_text(root / name, text)

    relative = tuple(files.keys())
    manifest_digest = write_manifest_v1(root, relative)
    verify = verify_manifest_v1(root)
    return {
        "evidence_root": str(root),
        "manifest_sha256": manifest_digest,
        "MANIFEST_VERIFY_RC": verify["MANIFEST_VERIFY_RC"],
        "files": list(relative) + [MANIFEST_FILENAME],
    }
