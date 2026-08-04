#!/usr/bin/env python3
"""Thin CLI for CAPABILITY_PRESENTATION_PROJECTION_OCTET_ORCHESTRATOR_V1.

Explicit arguments only. No archive discovery. No implicit clock.
Does not invent family inputs. Exit nonzero only for contract/CLI errors.

PR-C adds an optional source-sibling exporter mode that dispatches only the
integrated exporter family (dynamic_scope) via the existing exporter CLI.
Default remains dry-run; write requires --no-dry-run and --write-authorized.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.ops.presentation_projection_octet_orchestrator_v1.constants_v1 import (
    DEFAULT_DRY_RUN,
    EXPORTER_INTEGRATED_FAMILIES,
    FAMILY_ORDER,
)
from src.ops.presentation_projection_octet_orchestrator_v1.family_exporter_dispatch_v1 import (
    run_octet_family_exporters_v1,
)
from src.ops.presentation_projection_octet_orchestrator_v1.orchestrator_v1 import (
    run_presentation_projection_octet_orchestrator_v1,
)


def _load_json_object(path: str | None) -> Any | None:
    if path is None:
        return None
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manual one-shot presentation projection octet orchestrator. "
            "Requires explicit --archive-root. Materializer mode also requires "
            "--generated-at. Optional --export-source-siblings dispatches the "
            "integrated exporter family (dynamic_scope) via its CLI only. "
            "Does not discover archives, latest artifacts, or invent timestamps."
        )
    )
    parser.add_argument(
        "--archive-root",
        required=True,
        help="Explicit Workflow Dashboard archive root (no discovery).",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help=(
            "Caller-provided ISO-8601 timestamp for materializer mode "
            "(required unless --export-source-siblings)."
        ),
    )
    parser.add_argument(
        "--families",
        default=None,
        help=(
            "Optional comma-separated family ids. "
            f"Materializer default: all eight octet families ({','.join(FAMILY_ORDER)}). "
            "Exporter mode default: integrated exporter families only "
            f"({','.join(EXPORTER_INTEGRATED_FAMILIES)})."
        ),
    )
    parser.add_argument("--effective-at", default=None)
    parser.add_argument("--source-reference", default=None)
    parser.add_argument("--dynamic-scope-json", default=None)
    parser.add_argument("--regime-bull-bear-switch-json", default=None)
    parser.add_argument("--evidence-json", default=None)
    parser.add_argument("--display-json", default=None)
    parser.add_argument("--safety-authority-json", default=None)
    parser.add_argument("--risk-sizing-capital-json", default=None)
    parser.add_argument("--execution-reconciliation-json", default=None)
    parser.add_argument("--economic-summary-json", default=None)
    parser.add_argument(
        "--per-family-overrides-json",
        default=None,
        help="Optional JSON object mapping family_id -> override object.",
    )
    parser.add_argument(
        "--export-source-siblings",
        action="store_true",
        default=False,
        help=(
            "Dispatch integrated source-sibling exporter families via their CLIs "
            "(PR-C: dynamic_scope only). Does not run materializers."
        ),
    )
    parser.add_argument(
        "--dynamic-scope-state-root",
        default=None,
        help=(
            "Required for dynamic_scope exporter dispatch: durable Dynamic Scope "
            "state root (no discovery)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_DRY_RUN,
        help=f"Exporter dry-run mode (default: {str(DEFAULT_DRY_RUN).lower()}).",
    )
    parser.add_argument(
        "--write-authorized",
        action="store_true",
        default=False,
        help="Exporter write authorization; required together with --no-dry-run.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    families = None
    if args.families is not None and str(args.families).strip():
        families = [part.strip() for part in str(args.families).split(",") if part.strip()]

    try:
        if args.export_source_siblings:
            results = run_octet_family_exporters_v1(
                archive_root=args.archive_root,
                families=families,
                dynamic_scope_state_root=args.dynamic_scope_state_root,
                dry_run=bool(args.dry_run),
                write_authorized=bool(args.write_authorized),
            )
            ok = all(item.ok for item in results)
            payload = {
                "mode": "export_source_siblings",
                "archive_root": str(Path(args.archive_root).expanduser()),
                "dry_run": bool(args.dry_run),
                "write_authorized": bool(args.write_authorized),
                "default_dry_run": DEFAULT_DRY_RUN,
                "integrated_families": list(EXPORTER_INTEGRATED_FAMILIES),
                "family_results": [item.to_dict() for item in results],
                "ok": ok,
                "contract_ok": ok,
            }
            print(json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2))
            return 0 if ok else 1

        if args.generated_at is None or not str(args.generated_at).strip():
            print(
                json.dumps(
                    {
                        "contract_ok": False,
                        "error": "generated_at_required_unless_export_source_siblings",
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 2

        overrides = _load_json_object(args.per_family_overrides_json)
        if overrides is not None and not isinstance(overrides, dict):
            print(
                json.dumps(
                    {
                        "contract_ok": False,
                        "error": "per_family_overrides_json must be a JSON object",
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 2

        result = run_presentation_projection_octet_orchestrator_v1(
            archive_root=args.archive_root,
            generated_at=args.generated_at,
            families=families,
            dynamic_scope=_load_json_object(args.dynamic_scope_json),
            regime_bull_bear_switch=_load_json_object(args.regime_bull_bear_switch_json),
            evidence=_load_json_object(args.evidence_json),
            display=_load_json_object(args.display_json),
            safety_authority=_load_json_object(args.safety_authority_json),
            risk_sizing_capital=_load_json_object(args.risk_sizing_capital_json),
            execution_reconciliation=_load_json_object(args.execution_reconciliation_json),
            economic_summary=_load_json_object(args.economic_summary_json),
            effective_at=args.effective_at,
            source_reference=args.source_reference,
            per_family_overrides=overrides,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "contract_ok": False,
                    "error": type(exc).__name__,
                    "detail": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=False, indent=2))
    return 0 if result.contract_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
