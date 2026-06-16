#!/usr/bin/env python3
"""Order-Capability fixture normalizer→binding dry-validation runner v1.

Plan-only default. Offline repo-local fixture validation via existing contracts.
No network, secrets, provider truth flip, binding pass, or runtime execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    require_durable_archive_root,
    validate_order_capability_offline_durable_run_root,
    write_manifest_sha256,
)
from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.order_capability_demo_instrument_rules_binding_contract_v1 import (
    ALLOWED_CREDENTIAL_CLASS,
    AUTHORITY_IMPACT,
    DemoInstrumentRulesBindingVerdictKind,
    OrderCapabilityDemoInstrumentRulesBindingInput,
    REQUIRED_DEMO_HOST,
    evaluate_order_capability_demo_instrument_rules_binding,
    serialize_order_capability_demo_instrument_rules_binding_result,
)
from src.ops.order_capability_demo_instrument_rules_fixture_normalizer_contract_v1 import (
    BROWSER_RENDER_DISPOSITION_KEY,
    BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE,
    FIXTURE_SCHEMA_VERSION,
    REASON_MISSING_MIN_SIZE,
    REASON_MISSING_QTY_STEP,
    REASON_TICKSIZE_CONFLICT_UNRESOLVED,
    DemoInstrumentRulesFixtureNormalizerInput,
    DemoInstrumentRulesFixtureProvenance,
    DemoInstrumentRulesNormalizedFields,
    FixtureNormalizerError,
    FixtureSourceClass,
    compute_canonical_payload_hash,
    evaluate_demo_instrument_rules_fixture_normalization,
    map_normalizer_to_binding_offline_rules,
    serialize_demo_instrument_rules_fixture_normalizer_result,
)

RUNNER_VERSION = "order_capability_fixture_binding_dry_validation_runner_v1"
REPORT_SCHEMA_VERSION = "order_capability_fixture_binding_dry_validation_report.v1"
RUN_TYPE = "ORDER_CAPABILITY_FIXTURE_BINDING_OFFLINE_V1"
REQUIRED_OPERATOR_GO_TOKEN = "GO_ORDER_CAPABILITY_FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_IMPL_OPERATOR_GO_AUTOFILL_NO_RUN_V1"
BROWSER_RENDER_GO = (
    "GO_ORDER_CAPABILITY_BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_EXECUTE_WEB_READONLY_V1"
)

USAGE_EXIT = 2
RUNNER_ERROR_EXIT = 1


class FixtureBindingDryValidationError(ValueError):
    """Fail-closed fixture binding dry-validation runner error."""


def _parse_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except Exception as exc:
        raise FixtureBindingDryValidationError(f"invalid decimal value: {value!r}") from exc
    return parsed


def _parse_rules(data: object) -> DemoInstrumentRulesNormalizedFields | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise FixtureBindingDryValidationError("rules must be an object or null")
    return DemoInstrumentRulesNormalizedFields(
        min_size=_parse_decimal(data.get("min_size")),
        qty_step=_parse_decimal(data.get("qty_step")),
        price_tick=_parse_decimal(data.get("price_tick")),
        qty_precision=data.get("qty_precision"),
        price_precision=data.get("price_precision"),
        min_notional=_parse_decimal(data.get("min_notional")),
        cap_feasibility_rule=data.get("cap_feasibility_rule"),
    )


def _parse_provenance(data: object) -> DemoInstrumentRulesFixtureProvenance:
    if not isinstance(data, dict):
        raise FixtureBindingDryValidationError("provenance must be an object")
    required = (
        "source_type",
        "source_uri_or_origin",
        "captured_at",
        "captured_by_flow",
        "network_authorized_by_go_token",
        "raw_payload_hash",
        "normalized_payload_hash",
        "schema_version",
        "venue",
        "host",
        "instrument",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise FixtureBindingDryValidationError(
            f"provenance missing required fields: {', '.join(missing)}"
        )
    return DemoInstrumentRulesFixtureProvenance(
        source_type=str(data["source_type"]),
        source_uri_or_origin=str(data["source_uri_or_origin"]),
        captured_at=str(data["captured_at"]),
        captured_by_flow=str(data["captured_by_flow"]),
        network_authorized_by_go_token=str(data["network_authorized_by_go_token"]),
        raw_payload_hash=str(data["raw_payload_hash"]),
        normalized_payload_hash=str(data["normalized_payload_hash"]),
        schema_version=str(data["schema_version"]),
        venue=str(data["venue"]),
        host=str(data["host"]),
        instrument=str(data["instrument"]),
        value_redacted=bool(data.get("value_redacted", True)),
        no_secret_material=bool(data.get("no_secret_material", True)),
        repo_versioned=bool(data.get("repo_versioned", False)),
    )


def _parse_source_class(value: object) -> FixtureSourceClass:
    if not isinstance(value, str) or not value.strip():
        raise FixtureBindingDryValidationError("source_class must be a non-empty string")
    try:
        return FixtureSourceClass(value.strip())
    except ValueError as exc:
        raise FixtureBindingDryValidationError(f"unknown source_class: {value!r}") from exc


def _browser_render_input_from_disposition(
    payload: dict[str, Any],
    *,
    fixture_path: Path,
) -> DemoInstrumentRulesFixtureNormalizerInput:
    raw_hash = compute_canonical_payload_hash(payload)
    provenance = DemoInstrumentRulesFixtureProvenance(
        source_type=BROWSER_RENDERED_VENDOR_DOCS_SNAPSHOT_SOURCE,
        source_uri_or_origin=str(fixture_path),
        captured_at="2026-06-10T08:01:30Z",
        captured_by_flow="fixture_binding_dry_validation_runner_v1",
        network_authorized_by_go_token=BROWSER_RENDER_GO,
        raw_payload_hash=raw_hash,
        normalized_payload_hash=raw_hash,
        schema_version=FIXTURE_SCHEMA_VERSION,
        venue="kraken_futures_demo",
        host=REQUIRED_DEMO_HOST,
        instrument=DEFAULT_INSTRUMENT,
        value_redacted=True,
        no_secret_material=True,
        repo_versioned=True,
    )
    return DemoInstrumentRulesFixtureNormalizerInput(
        source_class=FixtureSourceClass.ACCEPTABLE_IF_VERSIONED,
        provenance=provenance,
        rules=None,
        raw_payload=payload,
    )


def load_fixture_input(fixture_path: Path) -> DemoInstrumentRulesFixtureNormalizerInput:
    if not fixture_path.is_file():
        raise FixtureBindingDryValidationError(f"fixture not found: {fixture_path}")

    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FixtureBindingDryValidationError(f"fixture JSON parse error: {exc}") from exc

    if not isinstance(payload, dict):
        raise FixtureBindingDryValidationError("fixture root must be a JSON object")

    if payload.get("schema_version") == FIXTURE_SCHEMA_VERSION:
        return DemoInstrumentRulesFixtureNormalizerInput(
            source_class=_parse_source_class(payload["source_class"]),
            provenance=_parse_provenance(payload["provenance"]),
            rules=_parse_rules(payload.get("rules")),
            raw_payload=payload.get("raw_payload")
            if isinstance(payload.get("raw_payload"), dict)
            else None,
            cancelallorders=bool(payload.get("cancelallorders", False)),
            batchorder=bool(payload.get("batchorder", False)),
            execute_authorized=bool(payload.get("execute_authorized", False)),
            order_authorized=bool(payload.get("order_authorized", False)),
            cancel_authorized=bool(payload.get("cancel_authorized", False)),
        )

    if BROWSER_RENDER_DISPOSITION_KEY in payload:
        return _browser_render_input_from_disposition(payload, fixture_path=fixture_path)

    raise FixtureBindingDryValidationError(
        "fixture must include schema_version "
        f"{FIXTURE_SCHEMA_VERSION!r} or {BROWSER_RENDER_DISPOSITION_KEY!r}"
    )


def _assert_repo_local_fixture(fixture_path: Path) -> None:
    resolved = fixture_path.resolve()
    repo_root = _REPO_ROOT.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise FixtureBindingDryValidationError(
            f"fixture must be repo-local under {repo_root}: {fixture_path}"
        ) from exc


def _binding_pass_possible_now(binding_result: object) -> bool:
    return (
        binding_result.verdict  # type: ignore[attr-defined]
        == DemoInstrumentRulesBindingVerdictKind.BINDING_SATISFIED_FOR_DRY_ONLY
    )


def _fail_closed_status_recognized(
    *,
    normalizer_result: object,
    binding_result: object,
) -> bool:
    return (
        normalizer_result.provider_truth_bound is False  # type: ignore[attr-defined]
        and normalizer_result.blocker_min_size_not_verified_offline is True  # type: ignore[attr-defined]
        and binding_result.execute_authorized_now is False  # type: ignore[attr-defined]
        and binding_result.order_authorized_now is False  # type: ignore[attr-defined]
        and binding_result.cancel_authorized_now is False  # type: ignore[attr-defined]
        and not _binding_pass_possible_now(binding_result)
    )


def build_fixture_binding_dry_validation_report(fixture_path: Path) -> dict[str, Any]:
    _assert_repo_local_fixture(fixture_path)
    inp = load_fixture_input(fixture_path)

    normalizer_result = evaluate_demo_instrument_rules_fixture_normalization(inp)
    source_type = inp.provenance.source_type if inp.provenance is not None else ""
    source_ref = source_type or str(fixture_path)

    offline_rules = map_normalizer_to_binding_offline_rules(
        normalizer_result,
        rules=inp.rules,
        source_ref=source_ref,
    )
    instrument = inp.provenance.instrument if inp.provenance is not None else DEFAULT_INSTRUMENT
    binding_result = evaluate_order_capability_demo_instrument_rules_binding(
        OrderCapabilityDemoInstrumentRulesBindingInput(
            demo_host=REQUIRED_DEMO_HOST,
            credential_class=ALLOWED_CREDENTIAL_CLASS,
            instrument=instrument,
            offline_rules=offline_rules,
            cap_max_notional_eur=Decimal("10.0"),
            reference_price_usd=Decimal("100.0"),
            fx_rate_usd_per_eur=Decimal("1.0"),
        )
    )

    reason_codes = list(
        dict.fromkeys(list(normalizer_result.reason_codes) + list(binding_result.reason_codes))
    )
    missing_min_size = REASON_MISSING_MIN_SIZE in reason_codes
    missing_qty_step = REASON_MISSING_QTY_STEP in reason_codes
    ticksize_conflict_fail_closed = REASON_TICKSIZE_CONFLICT_UNRESOLVED in reason_codes
    binding_pass_possible = _binding_pass_possible_now(binding_result)

    if binding_pass_possible:
        raise FixtureBindingDryValidationError(
            "binding_pass_possible_now must remain false in this slice"
        )
    if normalizer_result.provider_truth_bound:
        raise FixtureBindingDryValidationError("provider_truth_bound must remain false")
    if (
        normalizer_result.execute_authorized_now
        or normalizer_result.order_authorized_now
        or normalizer_result.cancel_authorized_now
        or binding_result.execute_authorized_now
        or binding_result.order_authorized_now
        or binding_result.cancel_authorized_now
    ):
        raise FixtureBindingDryValidationError("authority flags must remain false")

    fail_closed_recognized = _fail_closed_status_recognized(
        normalizer_result=normalizer_result,
        binding_result=binding_result,
    )

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "runner_version": RUNNER_VERSION,
        "mode": "plan-only",
        "fixture_path": str(fixture_path.resolve()),
        "verdict": "DRY_VALIDATION_COMPLETE",
        "source_type": source_type,
        "provider_truth_bound": False,
        "provider_truth_flipped": False,
        "binding_pass_possible_now": False,
        "order_capability_lane_parked": True,
        "missing_min_size": missing_min_size,
        "missing_qty_step": missing_qty_step,
        "ticksize_conflict_fail_closed": ticksize_conflict_fail_closed,
        "reason_codes": reason_codes,
        "fail_closed_status_recognized": fail_closed_recognized,
        "normalizer_verdict": normalizer_result.verdict.value,
        "binding_verdict": binding_result.verdict.value,
        "authority_impact": AUTHORITY_IMPACT,
        "normalizer": serialize_demo_instrument_rules_fixture_normalizer_result(normalizer_result),
        "binding": serialize_order_capability_demo_instrument_rules_binding_result(binding_result),
        "safety_flags": {
            "no_network": True,
            "no_secrets": True,
            "no_authority_change": True,
            "order_capability_execute_authorized": False,
        },
    }


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _validate_write_evidence_flags(args: argparse.Namespace) -> list[str]:
    reasons: list[str] = []
    if args.archive_root is None:
        reasons.append("--archive-root required for --write-evidence")
    if args.operator_go_token and args.operator_go_token != REQUIRED_OPERATOR_GO_TOKEN:
        reasons.append(f"operator_go_token must be {REQUIRED_OPERATOR_GO_TOKEN!r}")
    if args.write_evidence and not args.operator_go_token:
        reasons.append("operator_go_token required for --write-evidence")
    return reasons


def _closeout_markdown(report: dict[str, Any]) -> str:
    safety = report["safety_flags"]
    lines = [
        "# ORDER_CAPABILITY_FIXTURE_BINDING_DRY_VALIDATION CLOSEOUT",
        "",
        f"**Verdict:** `{report['verdict']}`",
        f"**Run ID:** `{report.get('run_id', '')}`",
        "",
        "## Safety",
        "",
        f"- no_network={safety['no_network']}",
        f"- no_secrets={safety['no_secrets']}",
        f"- no_authority_change={safety['no_authority_change']}",
        f"- order_capability_execute_authorized={safety['order_capability_execute_authorized']}",
        f"- order_capability_lane_parked={report['order_capability_lane_parked']}",
        f"- binding_pass_possible_now={report['binding_pass_possible_now']}",
        "",
        "Offline fixture-binding validation only. Does not authorize execute.",
    ]
    return "\n".join(lines) + "\n"


def write_durable_evidence(args: argparse.Namespace) -> tuple[int, str]:
    safety_reasons = _validate_write_evidence_flags(args)
    if safety_reasons:
        return RUNNER_ERROR_EXIT, "; ".join(safety_reasons)

    assert args.archive_root is not None
    ok, reason = require_durable_archive_root(args.archive_root)
    if not ok:
        return RUNNER_ERROR_EXIT, reason

    try:
        report = build_fixture_binding_dry_validation_report(args.fixture)
    except (FixtureBindingDryValidationError, FixtureNormalizerError) as exc:
        return RUNNER_ERROR_EXIT, str(exc)

    if not report.get("fail_closed_status_recognized"):
        return RUNNER_ERROR_EXIT, "fail-closed status not recognized"

    run_id = args.run_id or f"order_capability_fixture_binding_{_utc_stamp()}"
    dest = args.archive_root / "runs" / "testnet" / run_id
    dest.mkdir(parents=True, exist_ok=True)

    result_payload = dict(report)
    result_payload["run_id"] = run_id
    result_payload["archive_root"] = str(args.archive_root)
    result_payload["mode"] = "write-evidence"
    result_payload["run_type"] = RUN_TYPE
    result_payload["operator_go_token_class"] = REQUIRED_OPERATOR_GO_TOKEN

    metadata = {
        "run_id": run_id,
        "run_type": RUN_TYPE,
        "runner_version": RUNNER_VERSION,
        "utc_timestamp": _utc_stamp(),
        "archive_root": str(args.archive_root),
        "fixture_path": str(args.fixture.resolve()),
        "no_network": True,
        "no_secrets": True,
        "order_submission_executed": False,
        "network_api_called": False,
    }
    (dest / "RUN_METADATA.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dest / "ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json").write_text(
        json.dumps(result_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dest / "CLOSEOUT.md").write_text(_closeout_markdown(result_payload), encoding="utf-8")
    write_manifest_sha256(dest)
    layout_ok, layout_issues = validate_order_capability_offline_durable_run_root(dest)
    if not layout_ok:
        return RUNNER_ERROR_EXIT, "; ".join(layout_issues)
    return 0, str(dest)


def _format_text(report: dict[str, Any]) -> str:
    lines = [
        f"verdict={report['verdict']}",
        f"source_type={report['source_type']}",
        f"provider_truth_bound={report['provider_truth_bound']}",
        f"binding_pass_possible_now={report['binding_pass_possible_now']}",
        f"missing_min_size={report['missing_min_size']}",
        f"missing_qty_step={report['missing_qty_step']}",
        f"ticksize_conflict_fail_closed={report['ticksize_conflict_fail_closed']}",
        f"reason_codes={','.join(report['reason_codes'])}",
    ]
    return "\n".join(lines) + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Order-Capability fixture normalizer→binding dry-validation v1. "
            "Plan-only default; offline repo-local fixtures only."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan-only",
        action="store_true",
        help="Emit validation report only (default when --write-evidence omitted).",
    )
    mode.add_argument(
        "--write-evidence",
        action="store_true",
        help="Write durable offline validation evidence (requires operator GO token).",
    )
    parser.add_argument("--fixture", type=Path, required=True, help="Repo-local fixture JSON path")
    parser.add_argument("--archive-root", type=Path, default=None)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--operator-go-token", type=str, default="")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional flat output path for plan-only mode; stdout used when omitted.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.write_evidence:
        safety_reasons = _validate_write_evidence_flags(args)
        if safety_reasons:
            print("; ".join(safety_reasons), file=sys.stderr)
            return RUNNER_ERROR_EXIT
        rc, message = write_durable_evidence(args)
        if rc != 0:
            print(message, file=sys.stderr)
            return rc
        if args.format == "json":
            print(json.dumps({"mode": "write-evidence", "dest": message}, indent=2) + "\n", end="")
        else:
            print(message)
        return 0

    try:
        report = build_fixture_binding_dry_validation_report(args.fixture)
    except FixtureBindingDryValidationError as exc:
        print(str(exc), file=sys.stderr)
        return RUNNER_ERROR_EXIT
    except FixtureNormalizerError as exc:
        print(str(exc), file=sys.stderr)
        return RUNNER_ERROR_EXIT

    if args.format == "json":
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    else:
        rendered = _format_text(report)

    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if not report.get("fail_closed_status_recognized"):
        print("fail-closed status not recognized", file=sys.stderr)
        return RUNNER_ERROR_EXIT

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
