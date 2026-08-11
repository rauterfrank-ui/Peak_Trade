"""Offline verifier for LONG_RUNNING_TESTNET_PROVEN prep package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.constants_v1 import (
    CANONICAL_EXECUTE_OWNER_GO_SCOPE,
    CAPABILITY_ID,
    CAP_11_12_TESTNET_PROGRAM_CLOSED,
    CORE_LOGIC_CHANGE,
    EVIDENCE_DIRNAME,
    LIVE_AUTHORIZED,
    LONG_RUNNING_PATH_READY,
    LONG_RUNNING_TESTNET_PROVEN,
    LONG_RUNNING_TESTNET_PROVEN_DEFAULT,
    MANIFEST_FILENAME,
    OWNER,
    PRE_LIVE_CYBERSECURITY_GATE,
    SECTION_11_12_8_CLOSED,
    SECTION_11_12_8_REOPENED,
    SECTION_11_13_STARTED,
)
from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.evaluator_v1 import (
    LongRunningTestnetProvenEvalError,
    evaluate_long_running_testnet_proven_evidence_v1,
    prep_package_claims_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    SCOPED_OWNER_GO_SCOPE,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_manifest(evidence_dir: Path) -> int:
    manifest = evidence_dir / MANIFEST_FILENAME
    if not manifest.is_file():
        return 2
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            return 3
        digest, rel = parts[0], parts[-1]
        target = evidence_dir / rel
        if not target.is_file():
            return 4
        if _sha256_file(target) != digest:
            return 5
    return 0


def verify_capability_11_long_running_testnet_proven_prep_eval_v1(
    *,
    evidence_dir: Path,
) -> dict[str, Any]:
    claims = prep_package_claims_v1()
    residual: list[str] = []

    if not evidence_dir.is_dir():
        residual.append("EVIDENCE_DIR_MISSING")
    manifest_rc = _verify_manifest(evidence_dir) if evidence_dir.is_dir() else 99
    if manifest_rc != 0:
        residual.append(f"MANIFEST_VERIFY_RC_{manifest_rc}")

    claims_path = evidence_dir / "claims.json"
    if claims_path.is_file():
        on_disk = json.loads(claims_path.read_text(encoding="utf-8"))
        if on_disk.get("LONG_RUNNING_TESTNET_PROVEN") is not False:
            residual.append("PREP_PACKAGE_MUST_KEEP_PROVEN_FALSE")
        if on_disk.get("SECTION_11_12_8_REOPENED") is not False:
            residual.append("SECTION_11_12_8_MUST_NOT_REOPEN")
    else:
        residual.append("CLAIMS_JSON_MISSING")

    # Fail-closed evaluator self-checks (historical refuse + incomplete refuse).
    historical_refused = False
    try:
        hist = evaluate_long_running_testnet_proven_evidence_v1(
            evidence_root=Path(
                "evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/"
                "20260808T181528Z"
            ),
            campaign_payload={
                "BOUND_REACHED_REASON": "DURATION_BOUND",
                "completed": True,
                "ORDER_ACK_COUNT": 1,
                "FINAL_OPEN_ORDER_COUNT": 0,
                "FINAL_OPEN_POSITION_COUNT": 0,
                "LIVE_ORDER_EFFECT": "NONE",
                "LIVE_AUTHORIZED": False,
                "FINAL_EXCHANGE_RECONCILIATION": "PASS",
                "HTTP_STATUS": 403,
                "HTTP_403_CLASSIFICATION": (
                    "TRANSPORT_OR_GATEWAY_HTTP_403_NON_JSON_BODY_NOT_EXCHANGE_SEMANTIC_REJECT"
                ),
            },
        )
        historical_refused = bool(hist.get("HISTORICAL_PROMOTION_REFUSED")) or (
            hist.get("LONG_RUNNING_TESTNET_PROVEN") is False
        )
    except LongRunningTestnetProvenEvalError:
        historical_refused = True
    if not historical_refused:
        residual.append("HISTORICAL_REFUSE_SELF_CHECK_FAILED")

    incomplete_refused = False
    try:
        bad = evaluate_long_running_testnet_proven_evidence_v1(
            evidence_root=evidence_dir,
            campaign_payload={
                "BOUND_REACHED_REASON": "DURATION_BOUND",
                "completed": True,
                "ORDER_ACK_COUNT": 0,
                "FINAL_OPEN_ORDER_COUNT": 0,
                "FINAL_OPEN_POSITION_COUNT": 0,
                "LIVE_ORDER_EFFECT": "NONE",
                "FINAL_EXCHANGE_RECONCILIATION": "PASS",
            },
        )
        incomplete_refused = bad.get("LONG_RUNNING_TESTNET_PROVEN") is False
    except LongRunningTestnetProvenEvalError:
        incomplete_refused = True
    if not incomplete_refused:
        residual.append("INCOMPLETE_ACK_REFUSE_SELF_CHECK_FAILED")

    if SCOPED_OWNER_GO_SCOPE != CANONICAL_EXECUTE_OWNER_GO_SCOPE:
        residual.append("EXECUTE_TOKEN_NOT_PRIMARY_ON_CONSUMER")
    if LONG_RUNNING_TESTNET_PROVEN is not False:
        residual.append("PACKAGE_PROVEN_CONSTANT_DRIFT")
    if SECTION_11_12_8_REOPENED is not False:
        residual.append("SECTION_REOPEN_CONSTANT_DRIFT")
    if SECTION_11_13_STARTED is not False:
        residual.append("SECTION_11_13_STARTED")
    if LIVE_AUTHORIZED is not False:
        residual.append("LIVE_AUTHORIZED")
    if CORE_LOGIC_CHANGE is not False:
        residual.append("CORE_LOGIC_CHANGE")

    ok = len(residual) == 0 and manifest_rc == 0
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "EVIDENCE_DIRNAME": EVIDENCE_DIRNAME,
        "MANIFEST_VERIFY_RC": manifest_rc,
        "LONG_RUNNING_TESTNET_PROVEN": LONG_RUNNING_TESTNET_PROVEN,
        "LONG_RUNNING_TESTNET_PROVEN_DEFAULT": LONG_RUNNING_TESTNET_PROVEN_DEFAULT,
        "LONG_RUNNING_PATH_READY": LONG_RUNNING_PATH_READY,
        "SECTION_11_12_8_CLOSED": SECTION_11_12_8_CLOSED,
        "SECTION_11_12_8_REOPENED": SECTION_11_12_8_REOPENED,
        "CAP_11_12_TESTNET_PROGRAM_CLOSED": CAP_11_12_TESTNET_PROGRAM_CLOSED,
        "PRE_LIVE_CYBERSECURITY_GATE": PRE_LIVE_CYBERSECURITY_GATE,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "CANONICAL_EXECUTE_OWNER_GO_SCOPE": CANONICAL_EXECUTE_OWNER_GO_SCOPE,
        "SCOPED_OWNER_GO_SCOPE": SCOPED_OWNER_GO_SCOPE,
        "claims": claims,
        "residual_blockers": residual,
    }
