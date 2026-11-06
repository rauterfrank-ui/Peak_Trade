# src/trading/master_v2/local_debug_cli_v1.py
"""
Master V2 — lokale Debug-/CLI-Surface (v1): JSON in -> strukturiertes JSON out.

Nur dünne Verdrahtung: input_adapter -> optional local_evaluator; kein produktives
I/O außer optionalem Dateilesen/stdout (beim -m-Entry).
"""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from .decision_packet_critic_v1 import critique_master_v2_decision_packet_v1
from .decision_packet_v1 import validate_master_v2_decision_packet_v1
from .input_adapter_v1 import MasterV2InputAdapterResultV1, adapt_inputs_to_master_v2_flow_v1
from .local_evaluator_v1 import MasterV2LocalFlowResultV1

LOCAL_DEBUG_CLI_LAYER_VERSION = "v1"


def _json_load(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"INVALID_JSON: {e}") from e


def _load_input(
    *,
    json_text: Optional[str],
    input_path: Optional[Union[str, Path]],
) -> str:
    if json_text is not None and input_path is not None:
        raise ValueError("provide only one of json_text or input_path")
    if input_path is not None:
        return Path(input_path).read_text(encoding="utf-8")
    if json_text is not None:
        return json_text
    raise ValueError("json_text or input_path is required")


def _enrich_from_packet(ar: MasterV2InputAdapterResultV1) -> dict[str, Any]:
    assert ar.packet is not None
    v = validate_master_v2_decision_packet_v1(ar.packet)
    cr = critique_master_v2_decision_packet_v1(ar.packet)
    return {
        "flow_ok": None,
        "local_flow_rejection": None,
        "validate_ok": v.ok,
        "validate_reason_codes": list(v.reason_codes),
        "critic_has_error_findings": cr.has_error_findings,
        "critic_finding_codes": [f.code for f in cr.findings],
        "snapshot": None,
    }


def master_v2_debug_result_to_dict(ar: MasterV2InputAdapterResultV1) -> dict[str, Any]:
    """Serialisierbares, flaches Result-Dict (keine I/O)."""
    base: dict[str, Any] = {
        "debug_cli_version": LOCAL_DEBUG_CLI_LAYER_VERSION,
        "input_adapter_version": ar.layer_version,
        "adapter_ok": ar.ok,
        "rejection_reason": ar.rejection_reason,
        "correlation_id": ar.correlation_id,
    }
    if not ar.ok:
        return base
    assert ar.correlation_id is not None
    lf: Optional[MasterV2LocalFlowResultV1] = ar.local_flow
    if lf is not None:
        v, cr = lf.validation, lf.critic_report
        base.update(
            {
                "flow_ok": lf.flow_ok,
                "local_flow_rejection": lf.rejection_reason,
                "validate_ok": v.ok if v is not None else None,
                "validate_reason_codes": list(v.reason_codes) if v is not None else [],
                "critic_has_error_findings": cr.has_error_findings if cr is not None else None,
                "critic_finding_codes": [f.code for f in cr.findings] if cr is not None else [],
                "snapshot": lf.snapshot,
            }
        )
    else:
        base.update(_enrich_from_packet(ar))
    return base


def run_master_v2_local_debug_cli_v1(
    *,
    json_text: Optional[str] = None,
    input_path: Optional[Union[str, Path]] = None,
    run_evaluator: bool = True,
    with_snapshot: bool = True,
) -> dict[str, Any]:
    """
    Liest JSON (String oder Datei), mappt per Adapter und optional Local-Flow-Evaluator.

    Raises:
        ValueError: bei Lade-Fehlern, fehlendem Modus, ungueltigem Top-Level-JSON
            (kein Object), `JSONDecodeError` gekapselt als `INVALID_JSON`.
    """
    raw_text = _load_input(json_text=json_text, input_path=input_path)
    if not raw_text.strip():
        raise ValueError("EMPTY_INPUT")
    parsed = _json_load(raw_text)
    if not isinstance(parsed, Mapping):
        raise ValueError("JSON_ROOT_MUST_BE_OBJECT")
    ar = adapt_inputs_to_master_v2_flow_v1(
        parsed,
        run_evaluator=run_evaluator,
        with_snapshot=with_snapshot,
    )
    return master_v2_debug_result_to_dict(ar)


def main(argv: Optional[list[str]] = None) -> int:
    """argparse-Entry: JSON von stdin oder --file, Ergebnis-JSON auf stdout."""
    p = ArgumentParser(
        description="Master V2: lokaler JSON-Dryflow (Adapter + optional Evaluator) -> JSON."
    )
    p.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="JSON-Datei; ohne diese Option: stdin",
    )
    p.add_argument(
        "--no-evaluator",
        action="store_true",
        help="Nur Input-Adapter/Packet, ohne evaluate_master_v2_local_flow_v1",
    )
    p.add_argument(
        "--no-snapshot",
        action="store_true",
        help="Evaluator ohne Snapshot (nur mit Evaluator).",
    )
    args = p.parse_args(argv)
    try:
        if args.file:
            out = run_master_v2_local_debug_cli_v1(
                input_path=args.file,
                run_evaluator=not args.no_evaluator,
                with_snapshot=not args.no_snapshot,
            )
        else:
            out = run_master_v2_local_debug_cli_v1(
                json_text=sys.stdin.read(),
                run_evaluator=not args.no_evaluator,
                with_snapshot=not args.no_snapshot,
            )
    except ValueError as e:
        _emit_error(e)
        return 1
    sys.stdout.write(json.dumps(out, indent=2) + "\n")
    if not out.get("adapter_ok", False):
        return 1
    return 0


def _emit_error(exc: ValueError) -> None:
    sys.stdout.write(
        json.dumps(
            {
                "debug_cli_version": LOCAL_DEBUG_CLI_LAYER_VERSION,
                "adapter_ok": False,
                "rejection_reason": str(exc),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
