"""Sanitized evidence persist and PL-TF-002 closure navigation updates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.pl_tf_002_network_evidence_contract_v1.redaction_v1 import (
    assert_evidence_redaction_invariant_v1,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import (
    CLOSURE_STATUS,
    OWNER_GO,
    SESSION_OWNER_GO,
    WP_ID,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.errors_v1 import (
    PlTf002ProductiveReadOnlyGetCompleteError,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)

TREASURY_CONSTANTS_PATH = Path("src/ops/treasury_phase_1_offline_contracts_v1/constants_v1.py")
RUNBOOK_PATH = Path("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md")
PRE_LIVE_SPEC_PATH = Path("docs/ops/specs/PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1.md")
TREASURY_PHASE1_SPEC_PATH = Path("docs/ops/specs/TREASURY_PHASE_1_OFFLINE_CONTRACTS_V1.md")


def _utc_stamp_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def persist_pl_tf_002_network_evidence_pack_v1(
    *,
    evidence_root: Path,
    origin_main_sha: str,
    capture_summary: Mapping[str, Any],
    verification: Mapping[str, Any],
    evidence_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    closure = verification.get("PL_TF_002_CLOSURE_RESULT")
    if not isinstance(closure, Mapping) or closure.get("closed") is not True:
        raise PlTf002ProductiveReadOnlyGetCompleteError("VERIFICATION_NOT_CLOSED")

    assert_evidence_redaction_invariant_v1(evidence_bundle)
    pack = evidence_root / _utc_stamp_v1()
    pack.mkdir(parents=True, exist_ok=False)

    adjudication = {
        "RAW_NETWORK_EVIDENCE": "evidence_bundle.sanitized.json",
        "VALIDATED_FACTS": verification.get("NORMALIZED_PERMISSION_FACTS"),
        "ADJUDICATED_CONCLUSIONS": {
            "PL_TF_002_CLOSURE_RESULT": closure,
            "VERIFICATION_RESULT": verification.get("VERIFICATION_RESULT"),
        },
        "NAVIGATION": {
            "WP_ID": WP_ID,
            "OWNER_GO": OWNER_GO,
            "SESSION_OWNER_GO": SESSION_OWNER_GO,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "CLOSURE_STATUS": CLOSURE_STATUS,
        },
        "OPEN_POINTS": [],
    }
    write_json_v1(pack / "capture_summary.json", dict(capture_summary))
    write_json_v1(pack / "verification_result.json", dict(verification))
    write_json_v1(pack / "evidence_bundle.sanitized.json", dict(evidence_bundle))
    write_json_v1(pack / "adjudication.json", adjudication)
    write_json_v1(
        pack / "claims.json",
        {
            "WP_ID": WP_ID,
            "OWNER_GO": OWNER_GO,
            "SESSION_OWNER_GO": SESSION_OWNER_GO,
            "HTTP_METHODS": ["GET"],
            "POST_REQUEST_COUNT": 0,
            "ORDER_REQUEST_COUNT": 0,
            "TREASURY_MUTATION_REQUEST_COUNT": 0,
            "SECRET_EXPOSURE": "NONE",
            "AUTHORITY_CHANGED": False,
            "K1_AUTHORITY_CHANGED": False,
            "TRADING_AUTHORITY_CHANGED": False,
        },
    )
    write_manifest_v1(pack)
    manifest_rc = verify_manifest_v1(pack)
    return {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_VERIFY_RC": manifest_rc,
    }


def apply_pl_tf_002_closure_status_navigation_v1(*, repo_root: Path) -> dict[str, str]:
    """Flip standing PL-TF-002 navigation tokens after productive verifier closure."""

    treasury = repo_root / TREASURY_CONSTANTS_PATH
    text = treasury.read_text(encoding="utf-8")
    replacements = {
        'PL_TF_002_STATUS = "FROZEN_PENDING_NETWORK_EVIDENCE"': (
            f'PL_TF_002_STATUS = "{CLOSURE_STATUS}"'
        ),
        "VENUE_PERMISSION_UNKNOWN = True": "VENUE_PERMISSION_UNKNOWN = False",
        "VENUE_PERMISSION_GET_PERFORMED = False": "VENUE_PERMISSION_GET_PERFORMED = True",
    }
    for old, new in replacements.items():
        if old not in text:
            raise PlTf002ProductiveReadOnlyGetCompleteError(
                f"TREASURY_CONSTANTS_PATTERN_MISSING:{old}"
            )
        text = text.replace(old, new, 1)
    treasury.write_text(text, encoding="utf-8")

    runbook = repo_root / RUNBOOK_PATH
    rb = runbook.read_text(encoding="utf-8")
    rb_old = "PL_TF_002_STATUS=FROZEN_PENDING_NETWORK_EVIDENCE"
    rb_new = f"PL_TF_002_STATUS={CLOSURE_STATUS}"
    if rb_old not in rb:
        raise PlTf002ProductiveReadOnlyGetCompleteError("RUNBOOK_PL_TF_002_STATUS_MISSING")
    runbook.write_text(rb.replace(rb_old, rb_new, 1), encoding="utf-8")

    for spec_path, token_old, token_new in (
        (PRE_LIVE_SPEC_PATH, rb_old, rb_new),
        (TREASURY_PHASE1_SPEC_PATH, rb_old, rb_new),
    ):
        spec = repo_root / spec_path
        body = spec.read_text(encoding="utf-8")
        if token_old not in body:
            raise PlTf002ProductiveReadOnlyGetCompleteError(f"SPEC_STATUS_MISSING:{spec_path}")
        spec.write_text(body.replace(token_old, token_new, 1), encoding="utf-8")

    pre_live = repo_root / PRE_LIVE_SPEC_PATH
    pl_body = pre_live.read_text(encoding="utf-8")
    pl_body = pl_body.replace("VENUE_PERMISSION_UNKNOWN=true", "VENUE_PERMISSION_UNKNOWN=false", 1)
    pl_body = pl_body.replace(
        "PL_TF_002=TRADING_KEY_EFFECTIVE_TREASURY_CAPABILITY_NOT_VENUE_PROVEN",
        "PL_TF_002=TRADING_KEY_TREASURY_CAPABILITY_VENUE_PROVEN",
        1,
    )
    pre_live.write_text(pl_body, encoding="utf-8")

    return {
        "PL_TF_002_STATUS": CLOSURE_STATUS,
        "VENUE_PERMISSION_UNKNOWN": "false",
        "VENUE_PERMISSION_GET_PERFORMED": "true",
    }
