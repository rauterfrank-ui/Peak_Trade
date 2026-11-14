#!/usr/bin/env python3
"""CLI for Paper-Shadow wallclock MD-observe capability.

preflight / verify-evidence / measure-shadow-outcome: offline only.
run: delegates to productive successor path
  INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1
  — requires verified productive (non-fixture) authorization; real network additionally
  requires PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1 (never sufficient alone).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (  # noqa: E402
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CONFIRM_TOKEN_ENV,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (  # noqa: E402
    preflight_wallclock_session_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E402,E501
    REAL_NETWORK_ENV,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (  # noqa: E402,E501
    load_confirm_token_from_file_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (  # noqa: E402,E501
    run_productive_wallclock_session_from_paths_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Paper-Shadow wallclock observation CLI. "
            "run requires productive non-fixture authorization; "
            f"real network also requires {REAL_NETWORK_ENV}=1 (never alone). "
            "No orders/paper/testnet/live/credentials."
        )
    )
    p.add_argument(
        "command", choices=("preflight", "verify-evidence", "measure-shadow-outcome", "run")
    )
    p.add_argument("--preregistration", type=Path, default=None)
    p.add_argument("--operator-go", type=Path, default=None)
    p.add_argument("--authorization-artifact", type=Path, default=None)
    p.add_argument("--confirm-token-file", type=Path, default=None)
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument(
        "--require-typed-ddo",
        action="store_true",
        help="Require a completed archive with DDO and market evidence for every typed cycle.",
    )
    p.add_argument("--decision-event-ref")
    p.add_argument("--o4-mark-archive", type=Path)
    p.add_argument("--n-bars", type=int)
    p.add_argument("--evaluated-at-utc")
    p.add_argument("--max-end-age-seconds", type=int)
    receipts = p.add_mutually_exclusive_group()
    receipts.add_argument(
        "--outcome-receipt-out",
        type=Path,
        help="Save the Shadow outcome receipt outside both source archives.",
    )
    receipts.add_argument(
        "--verify-outcome-receipt",
        type=Path,
        help="Recompute a saved Shadow receipt against both source archives.",
    )
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--fingerprint-ledger", type=Path, default=None)
    p.add_argument(
        "--real-network",
        action="store_true",
        help=f"Open real public MD transport after consumption (requires {REAL_NETWORK_ENV}=1).",
    )
    p.add_argument("--json", action="store_true")
    return p


def _load_confirm_token(args: argparse.Namespace) -> str:
    env_token = os.environ.get(CONFIRM_TOKEN_ENV, "").strip()
    if env_token and args.confirm_token_file is not None:
        raise SystemExit("CONFIRM_TOKEN_DUAL_SOURCE_FORBIDDEN")
    if env_token:
        return env_token
    if args.confirm_token_file is not None:
        return load_confirm_token_from_file_v1(args.confirm_token_file)
    raise SystemExit("CONFIRM_TOKEN_SOURCE_REQUIRED")


SHADOW_OUTCOME_RECEIPT_SCHEMA = "i17_shadow_o4_market_measurement_readback_v1"


def _measure_shadow_outcome(args: argparse.Namespace) -> dict:
    from scripts.ops.capture_offline_learning_mark_window_v1 import read_captured_mark_archive_v1
    from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
        REQUEST_SCHEMA,
    )
    from src.learning.deterministic_decision_outcome_v0.learning_state_record_v0 import (
        learning_event_time_key_v0,
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
        seal_v1,
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
        measure_recorded_market_horizon_v1,
    )
    from src.research.offline_recorded_mark_horizon_source_v1 import (
        read_bound_json,
        recorded_mark_price_unit_v1,
    )

    verification = verify_wallclock_evidence_bundle_v1(
        evidence_root=args.evidence_root, select_shadow_decision_ref=args.decision_event_ref
    )
    if not verification.typed_ddo_requirement_met:
        raise ValueError("COMPLETED_TYPED_SHADOW_EVIDENCE_REQUIRED")
    decision = verification.selected_shadow_decision
    if decision is None:
        raise ValueError("DECISION_NOT_IN_VERIFIED_TYPED_SHADOW_CYCLE")

    archive = read_captured_mark_archive_v1(args.o4_mark_archive)
    binding = read_bound_json(archive.binding_path, archive.binding_sha256)
    canonical = decision["canonical_instrument_id"]
    native = decision["venue_instrument_id"]
    if not isinstance(binding, dict) or binding.get("mapping_digest") != decision["mapping_digest"]:
        raise ValueError("SHADOW_O4_MAPPING_MISMATCH")
    price_unit = recorded_mark_price_unit_v1(
        instrument_binding=binding, canonical_instrument_id=canonical, native_instrument_id=native
    )
    # The record has up to nine fractional digits. Avoid rounding a just-after-hour
    # decision back onto the hour, which would include a bar already underway.
    seconds, fraction = learning_event_time_key_v0(decision["decision_event_time_utc"])
    start = seconds.replace(minute=0, second=0)
    if start != seconds or int(fraction) != 0:
        start += timedelta(hours=1)
    measurement = measure_recorded_market_horizon_v1(
        archive=archive,
        request={
            "schema_version": REQUEST_SCHEMA,
            "market_identity": {
                "dataset_generation": "archived-okx-mark-minute-replay-v1",
                "venue": binding["venue"],
                "instrument_ref": canonical,
                "native_instrument_ref": native,
            },
            "horizon_start_time_utc": start.isoformat() + "Z",
            "n_bars": args.n_bars,
            "o4_interval_id": "PT1H",
            "price_unit": price_unit,
            "price_family": "MARK_PRICE",
            "source_kind": "RECORDED_PUBLIC_MD",
            "max_end_age_seconds": args.max_end_age_seconds,
            "expected_price_basis_kind": "O4_BAR_CLOSE_FINALIZED",
        },
        evaluated_at_utc=args.evaluated_at_utc,
    )
    return seal_v1(
        {
            "schema_version": SHADOW_OUTCOME_RECEIPT_SCHEMA,
            "authority": "NONE",
            "ok": True,
            "shadow_decision": decision,
            "market_observation": measurement,
            "market_archive": {
                "repository_sha": archive.repository_sha,
                "instrument_binding_sha256": archive.binding_sha256,
                "request_log_sha256": archive.request_log_sha256,
                "page_sha256": [
                    archive.raw_sha256,
                    *(page.raw_sha256 for page in archive.additional_pages),
                ],
            },
            "meaning": "FORWARD_MARK_PRICE_LOG_RETURN_ONLY",
            "fill_source_type": "NO_FILL",
            "source_authenticated": False,
            "learning_input_authorized": False,
        }
    )


def _shadow_outcome_receipt(args: argparse.Namespace) -> dict:
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
        _append,
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
        strict_json_v1,
        validate_seal_v1,
    )

    def read_receipt(path: Path) -> dict:
        if path.is_symlink() or not path.is_file():
            raise ValueError("SHADOW_OUTCOME_RECEIPT_FILE_REQUIRED")
        return validate_seal_v1(strict_json_v1(path.read_bytes()), SHADOW_OUTCOME_RECEIPT_SCHEMA)

    if args.verify_outcome_receipt is not None:
        saved = read_receipt(args.verify_outcome_receipt)
        observation = saved["market_observation"]
        args.decision_event_ref = saved["shadow_decision"]["decision_event_ref"]
        args.n_bars = observation["request"]["n_bars"]
        args.max_end_age_seconds = observation["request"]["max_end_age_seconds"]
        args.evaluated_at_utc = observation["evaluated_at_utc"]
        if (
            not isinstance(args.decision_event_ref, str)
            or not args.decision_event_ref
            or type(args.n_bars) is not int
            or not 2 <= args.n_bars <= 24
        ):
            raise ValueError("SHADOW_OUTCOME_RECEIPT_REQUEST_INVALID")
        actual = _measure_shadow_outcome(args)
        if actual["exact_content_digest"] != saved["exact_content_digest"]:
            raise ValueError("SHADOW_OUTCOME_RECEIPT_SOURCE_MISMATCH")
        return actual

    output = args.outcome_receipt_out
    if output is not None:
        if output.is_symlink() or (output.exists() and not output.is_file()):
            raise ValueError("SHADOW_OUTCOME_RECEIPT_FILE_REQUIRED")
        output = output.resolve()
        if any(
            output.is_relative_to(root.resolve())
            for root in (args.evidence_root, args.o4_mark_archive)
        ):
            raise ValueError("SHADOW_OUTCOME_RECEIPT_INSIDE_SOURCE_ARCHIVE")
    actual = _measure_shadow_outcome(args)
    if output is not None:
        _append(output, actual)
        if read_receipt(output)["exact_content_digest"] != actual["exact_content_digest"]:
            raise ValueError("SHADOW_OUTCOME_RECEIPT_WRITE_MISMATCH")
    return actual


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.require_typed_ddo and args.command != "verify-evidence":
        parser.error("--require-typed-ddo requires verify-evidence")
    if (
        args.outcome_receipt_out is not None or args.verify_outcome_receipt is not None
    ) and args.command != "measure-shadow-outcome":
        parser.error("outcome receipt options require measure-shadow-outcome")
    outcome_args = (
        args.decision_event_ref,
        args.o4_mark_archive,
        args.n_bars,
        args.evaluated_at_utc,
        args.max_end_age_seconds,
    )
    if args.command == "measure-shadow-outcome":
        if args.evidence_root is None or args.o4_mark_archive is None:
            parser.error("measure-shadow-outcome requires --evidence-root and --o4-mark-archive")
        if args.real_network:
            parser.error("measure-shadow-outcome is offline")
        measurement_args = (
            args.decision_event_ref,
            args.n_bars,
            args.evaluated_at_utc,
            args.max_end_age_seconds,
        )
        if args.verify_outcome_receipt is not None:
            if any(val is not None for val in measurement_args):
                parser.error("--verify-outcome-receipt uses the saved measurement arguments")
        else:
            if any(val is None for val in measurement_args):
                parser.error(
                    "measurement requires --decision-event-ref, --n-bars, "
                    "--evaluated-at-utc and --max-end-age-seconds"
                )
            if not 2 <= args.n_bars <= 24:
                parser.error("measure-shadow-outcome requires 2 to 24 bars")
        try:
            payload = _shadow_outcome_receipt(args)
        except ValueError as exc:
            print(json.dumps({"ok": False, "blockers": [str(exc)]}))
            return 1
        except (OSError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            print(
                json.dumps({"ok": False, "blockers": [f"SHADOW_O4_READBACK:{type(exc).__name__}"]})
            )
            return 1
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0
    if any(val is not None for val in outcome_args):
        parser.error("outcome options require measure-shadow-outcome")
    if args.command == "preflight":
        payload = preflight_wallclock_session_v1(repo_root=_REPO_ROOT)
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "verify-evidence":
        if args.evidence_root is None:
            print(json.dumps({"ok": False, "blockers": ["EVIDENCE_ROOT_REQUIRED"]}))
            return 2
        result = verify_wallclock_evidence_bundle_v1(evidence_root=args.evidence_root)
        payload = result.to_dict()
        if args.require_typed_ddo:
            payload["typed_ddo_requirement_met"] = result.typed_ddo_requirement_met
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if result.verified and payload.get("typed_ddo_requirement_met", True) else 1

    # run — productive successor path (fixtures rejected; env alone insufficient).
    missing = []
    for name, val in (
        ("preregistration", args.preregistration),
        ("operator-go", args.operator_go),
        ("authorization-artifact", args.authorization_artifact),
        ("evidence-root", args.evidence_root),
        ("expected-repository-sha", args.expected_repository_sha),
        ("fingerprint-ledger", args.fingerprint_ledger),
    ):
        if val is None:
            missing.append(name)
    try:
        token = _load_confirm_token(args)
    except SystemExit as exc:
        missing.append(str(exc))
        token = ""
    if missing:
        payload = {
            "ok": False,
            "blockers": [f"MISSING_ARG:{m}" for m in missing],
            "capability_id": CAPABILITY_ID,
            "network_used": False,
            "session_executed": False,
            "notes": [
                "PRODUCTIVE_RUN_REQUIRES_FULL_AUTH_BUNDLE",
                "FIXTURE_AUTH_REJECTED",
                f"ENV_FLAG_ALONE_INSUFFICIENT ({REAL_NETWORK_ENV})",
            ],
        }
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 2

    result = run_productive_wallclock_session_from_paths_v1(
        preregistration_path=args.preregistration,
        operator_go_path=args.operator_go,
        authorization_artifact_path=args.authorization_artifact,
        confirm_token=token,
        evidence_root=args.evidence_root,
        expected_repository_sha=str(args.expected_repository_sha),
        fingerprint_ledger_path=args.fingerprint_ledger,
        use_real_network=bool(args.real_network),
        repo_root=_REPO_ROOT,
        environ=os.environ,
    )
    print(json.dumps(redact_mapping_for_logs(result.to_dict()), sort_keys=True, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
