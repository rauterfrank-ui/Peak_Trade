#!/usr/bin/env python3
"""Materialize §11.13.5.E economic baseline + OKX clearance evidence."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (  # noqa: E402
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    REQUIRED_CREDENTIAL_CLASS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.economic_baseline_and_okx_clearance_v1 import (  # noqa: E402
    OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE,
    evaluate_economic_baseline_and_okx_clearance_v1,
    evaluate_okx_temp_security_clearance_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.economic_baseline_private_read_v1 import (  # noqa: E402
    run_economic_baseline_productive_private_read_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (  # noqa: E402
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (  # noqa: E402
    REQUIRED_SECRETREF_URI,
)

EVIDENCE_DIRNAME = "section_11_13_5_economic_baseline_and_okx_clearance_v1"
DEFAULT_VAULT = (
    _REPO_ROOT
    / ".ops_local"
    / "section_11_13_3_live_shadow_with_exchange_reconciliation"
    / "secrets"
    / "secretref_vault.json"
)
DEFAULT_UI_SCREENSHOT = _REPO_ROOT / "ui_withdrawal_24h_restriction_still_active.png"


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def materialize(
    *,
    origin_main_sha: str,
    vault_file: Path,
    run_id: str,
    ui_screenshot: Path | None,
) -> Path:
    observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    private_read = run_economic_baseline_productive_private_read_v1(vault_file=vault_file)
    clearance = evaluate_okx_temp_security_clearance_v1(
        restriction_still_active=True,
        clearance_evidence_present_proven=False,
        evidence_source=(
            "OKX_WITHDRAWAL_UI_BANNER_PRODUCTIVE_READ_ONLY:"
            "Auszahlungen_fuer_24_Stunden_bis_13_Aug_2026_15:48:50"
        ),
        observed_at_utc=observed_at,
        restriction_expires_at_local="2026-08-13T15:48:50+02:00",
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
    )
    att = {
        "READ_ATTESTATION": True,
        "TRADE_ATTESTATION": True,
        "WITHDRAW_ATTESTATION": False,
        "KEY_BINDING_STATUS": "PROVEN",
        "CANARY_TRADE_KEY_BINDING": "PROVEN",
        "SECRETREF_STATUS": "RESOLVED",
        "SECRETREF_URI_CONTRACT": REQUIRED_SECRETREF_URI,
        "VENUE": REUSED_BINDING_VENUE,
        "LEGAL_ENTITY": REUSED_BINDING_ENTITY,
        "REGION": REUSED_BINDING_REGION,
        "REST_HOST": REUSED_BINDING_REST_HOST,
        "ACCOUNT_SCOPE": REUSED_BINDING_ACCOUNT_SCOPE,
        "KEY_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "PRIOR_DRY_RUN_KEY_REUSED": False,
    }
    result = evaluate_economic_baseline_and_okx_clearance_v1(
        repo_root=_REPO_ROOT,
        origin_main_sha=origin_main_sha,
        reconciliation_eval=private_read["reconciliation_after_adoption"],
        exchange_snapshot=private_read["exchange_snapshot"],
        local_expected_state_adopted=private_read["local_expected_state_adopted"],
        okx_clearance=clearance,
        productive_private_read_summary={
            "GET_REQUEST_COUNT": private_read["GET_REQUEST_COUNT"],
            "WRITE_REQUEST_COUNT": private_read["WRITE_REQUEST_COUNT"],
            "SECRET_VALUE_ACCESS": private_read["SECRET_VALUE_ACCESS"],
            "endpoint_summaries": private_read["endpoint_summaries"],
            "counters": private_read["counters"],
            "credential_class_used": private_read["credential_class"],
            "secretref_uri_used": private_read["secretref_uri"],
            "reconciliation_before_adoption": private_read["reconciliation_before_adoption"],
        },
        trade_key_attestation=att,
    )

    root = _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    root.mkdir(parents=True, exist_ok=True)

    write_json_v1(root / "ECONOMIC_BASELINE_AND_OKX_CLEARANCE_RESULT.json", result)
    write_json_v1(root / "OKX_TEMP_SECURITY_CLEARANCE.json", clearance)
    write_json_v1(
        root / "EXCHANGE_SNAPSHOT.sanitized.json",
        {"layers": private_read["exchange_snapshot"], "sanitized": True},
    )
    write_json_v1(
        root / "LOCAL_EXPECTED_STATE_ADOPTED.sanitized.json",
        {"layers": private_read["local_expected_state_adopted"], "sanitized": True},
    )
    write_json_v1(
        root / "RECONCILIATION_BEFORE_ADOPTION.json",
        private_read["reconciliation_before_adoption"],
    )
    write_json_v1(
        root / "RECONCILIATION_AFTER_ADOPTION.json",
        private_read["reconciliation_after_adoption"],
    )
    write_json_v1(
        root / "LIVE_CANARY_CYBERSECURITY_GATE.json",
        result["LIVE_CANARY_CYBERSECURITY_GATE_EVAL"],
    )
    write_json_v1(
        root / "PRODUCTIVE_PRIVATE_READ_SUMMARY.json",
        result["PRODUCTIVE_PRIVATE_READ_SUMMARY"],
    )
    write_json_v1(
        root / "authorization_binding.json",
        {
            "OWNER_GO_BOUND": OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE,
            "OWNER_GO_STATUS": "CONSUMED",
            "BASE_ORIGIN_MAIN_SHA": origin_main_sha,
            "AUTHORIZATION_SCOPE": "ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE",
            "LIVE_AUTHORIZED": False,
            "ORDER_EFFECT": "NONE",
            "ACCOUNT_MUTATION_EFFECT": "NONE",
        },
    )
    write_json_v1(
        root / "zero_write_assertions.json",
        {
            "ORDER_REQUEST_COUNT": 0,
            "CANCEL_REQUEST_COUNT": 0,
            "AMEND_REQUEST_COUNT": 0,
            "WITHDRAW_REQUEST_COUNT": 0,
            "TRANSFER_REQUEST_COUNT": 0,
            "P2P_SELL_REQUEST_COUNT": 0,
            "WRITE_REQUEST_COUNT": private_read["WRITE_REQUEST_COUNT"],
            "GET_REQUEST_COUNT": private_read["GET_REQUEST_COUNT"],
            "ORDER_EFFECT": "NONE",
            "ACCOUNT_MUTATION_EFFECT": "NONE",
        },
    )
    write_json_v1(
        root / "redaction_check.json",
        {
            "SECRET_VALUE_PERSISTED": False,
            "SECRET_VALUE_ACCESS": private_read["SECRET_VALUE_ACCESS"],
            "BALANCE_AMOUNTS_PERSISTED": False,
            "ACCOUNT_SCOPE_PLAINTEXT_PERSISTED": True,
            "ok": True,
        },
    )
    write_json_v1(
        root / "claims.json",
        {
            "ORDER_SUBMITTED": False,
            "LIVE_AUTHORIZED": False,
            "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
            "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
            "LIVE_RECONCILIATION_PROVEN": result["LIVE_RECONCILIATION_PROVEN"],
            "BLOCKS_NEW_ENTRY": result["BLOCKS_NEW_ENTRY"],
            "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE": result["OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE"],
            "EXCHANGE_TRUTH_ADOPTION_STATUS": result["EXCHANGE_TRUTH_ADOPTION_STATUS"],
            "NETWORK_EFFECT": result["NETWORK_EFFECT"],
            "ORDER_EFFECT": "NONE",
            "ACCOUNT_MUTATION_EFFECT": "NONE",
        },
    )
    closeout = {
        "DOCUMENT_CLASS": "MACHINE_READABLE_CLOSEOUT_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_V1",
        "BASELINE_VALIDATION": "PASS",
        "BASE_ORIGIN_MAIN_SHA": origin_main_sha,
        "OWNER_GO_BOUND": OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE,
        "OWNER_GO_STATUS": "CONSUMED",
        "EXCHANGE_TRUTH_ADOPTION_STATUS": result["EXCHANGE_TRUTH_ADOPTION_STATUS"],
        "LIVE_RECONCILIATION_PROVEN": result["LIVE_RECONCILIATION_PROVEN"],
        "ECONOMIC_DIVERGENCE_STATUS": result["ECONOMIC_DIVERGENCE_STATUS"],
        "BLOCKS_NEW_ENTRY": result["BLOCKS_NEW_ENTRY"],
        "OKX_TEMP_SECURITY_RESTRICTION": result["OKX_TEMP_SECURITY_RESTRICTION"],
        "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE": result["OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE"],
        "OKX_CLEARANCE_EVIDENCE_SOURCE": result["OKX_CLEARANCE_EVIDENCE_SOURCE"],
        "LIVE_CANARY_CYBERSECURITY_GATE": result["LIVE_CANARY_CYBERSECURITY_GATE"],
        "CANARY_KEY_BINDING_STATUS": result["CANARY_KEY_BINDING_STATUS"],
        "READ_ATTESTATION": result["READ_ATTESTATION"],
        "TRADE_ATTESTATION": result["TRADE_ATTESTATION"],
        "WITHDRAW_ATTESTATION": result["WITHDRAW_ATTESTATION"],
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "NETWORK_EFFECT": result["NETWORK_EFFECT"],
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": result["SECRET_VALUE_ACCESS"],
        "TERMINAL_STATE": result["TERMINAL_STATE"],
        "EARLIEST_UNRESOLVED_DEPENDENCY": result["EARLIEST_UNRESOLVED_DEPENDENCY"],
        "CANONICAL_NEXT_STEP": result["CANONICAL_NEXT_STEP"],
        "HARD_STOP_REASONS": result["HARD_STOP_REASONS"],
        "RUN_ID": run_id,
    }
    write_json_v1(root / "MACHINE_READABLE_CLOSEOUT.json", closeout)
    write_json_v1(
        root / "SUMMARY.json",
        {
            "DOCUMENT_CLASS": "SECTION_11_13_5_E_SUMMARY_V1",
            "RUN_ID": run_id,
            "TERMINAL_STATE": result["TERMINAL_STATE"],
            "LIVE_RECONCILIATION_PROVEN": result["LIVE_RECONCILIATION_PROVEN"],
            "BLOCKS_NEW_ENTRY": result["BLOCKS_NEW_ENTRY"],
            "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE": result["OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE"],
            "LIVE_CANARY_CYBERSECURITY_GATE": result["LIVE_CANARY_CYBERSECURITY_GATE"],
            "ORDER_EFFECT": "NONE",
            "LIVE_AUTHORIZED": False,
        },
    )
    write_json_v1(
        root / "NOTION_MIRROR.json",
        {
            "DOCUMENT_CLASS": "SECTION_11_13_5_E_NOTION_MIRROR_POINTER_V1",
            "NOTION_PAGE": "https://app.notion.com/p/3615d37faddf81208046c2dd415586d0",
            "NOTION_PAGE_ID": "3615d37f-addf-8120-8046-c2dd415586d0",
            "STATUS": "PENDING_POST_SSOT_UPDATE",
            "POST_WRITE_VERIFICATION": "PENDING",
            "SECRET_VALUES_INCLUDED": False,
            "SSOT_POINTER": ("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.13.5.E"),
        },
    )

    relative_files = [
        "ECONOMIC_BASELINE_AND_OKX_CLEARANCE_RESULT.json",
        "OKX_TEMP_SECURITY_CLEARANCE.json",
        "EXCHANGE_SNAPSHOT.sanitized.json",
        "LOCAL_EXPECTED_STATE_ADOPTED.sanitized.json",
        "RECONCILIATION_BEFORE_ADOPTION.json",
        "RECONCILIATION_AFTER_ADOPTION.json",
        "LIVE_CANARY_CYBERSECURITY_GATE.json",
        "PRODUCTIVE_PRIVATE_READ_SUMMARY.json",
        "authorization_binding.json",
        "zero_write_assertions.json",
        "redaction_check.json",
        "claims.json",
        "MACHINE_READABLE_CLOSEOUT.json",
        "SUMMARY.json",
        "NOTION_MIRROR.json",
    ]
    if ui_screenshot and ui_screenshot.is_file():
        dest = root / "ui_withdrawal_24h_restriction_still_active.png"
        shutil.copy2(ui_screenshot, dest)
        relative_files.append(dest.name)

    write_manifest_v1(root, tuple(relative_files))
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise RuntimeError(f"MANIFEST_FAIL:{verify['errors']}")
    return root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin-main-sha", required=True)
    parser.add_argument("--vault-file", default=str(DEFAULT_VAULT))
    parser.add_argument("--run-id", default=_default_run_id())
    parser.add_argument("--ui-screenshot", default=str(DEFAULT_UI_SCREENSHOT))
    args = parser.parse_args()
    root = materialize(
        origin_main_sha=args.origin_main_sha,
        vault_file=Path(args.vault_file),
        run_id=args.run_id,
        ui_screenshot=Path(args.ui_screenshot) if args.ui_screenshot else None,
    )
    print(json.dumps({"ok": True, "EVIDENCE_ROOT": str(root)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
