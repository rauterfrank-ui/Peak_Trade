#!/usr/bin/env python3
"""Operator CLI: STEP 29U Economic Failure Closeout and Recovery Decision v0.

Offline, read-only, non-activating. Emits economic FAIL closeout status,
canonical blockers, and admissible recovery options. Never auto-selects a
recovery option and never claims activation eligibility.

Exit codes:
  0  successful closeout; operator selection required
  1  invalid input / evidence (fail-closed)
  3  internal execution failure
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from src.ops.step_29u_activation_eligibility_inventory_v0 import (  # noqa: E402
    Step29UActivationEligibilityInventoryError,
)
from src.ops.step_29u_audit_provenance_v0 import (  # noqa: E402
    Step29UAuditProvenanceError,
)
from src.ops.step_29u_economic_failure_closeout_recovery_decision_v0 import (  # noqa: E402
    EconomicFailureCloseoutOverridesV0,
    Step29UEconomicFailureCloseoutError,
    evaluate_step_29u_economic_failure_closeout_recovery_decision_v0,
    result_to_machine_lines,
    serialize_result_json_v0,
)
from src.ops.step_29u_economic_validity_readiness_v0 import (  # noqa: E402
    Step29UEconomicValidityReadinessError,
)

EXIT_OK = 0
EXIT_INVALID_INPUT = 1
EXIT_INTERNAL = 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Close out Step-29U economic FAIL and emit an operator recovery "
            "decision inventory (offline, fail-closed, non-activating)."
        )
    )
    p.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    p.add_argument(
        "--fleet-closeout",
        type=Path,
        default=None,
        help="Optional override path to fleet FAIL closeout JSON (read-only).",
    )
    p.add_argument(
        "--readiness-config",
        type=Path,
        default=None,
        help="Optional override path to readiness gate TOML (read-only).",
    )
    p.add_argument(
        "--sealed-economic-result",
        type=Path,
        default=None,
        help="Optional override path to sealed economic_validity_result.json.",
    )
    p.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional path to write deterministic JSON artifact.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON to stdout (default: machine lines).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    try:
        result = evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=repo_root,
            overrides=EconomicFailureCloseoutOverridesV0(
                fleet_closeout_path=args.fleet_closeout,
                readiness_config_path=args.readiness_config,
                sealed_economic_result_path=args.sealed_economic_result,
            ),
        )
    except (
        Step29UEconomicFailureCloseoutError,
        Step29UEconomicValidityReadinessError,
        Step29UAuditProvenanceError,
        Step29UActivationEligibilityInventoryError,
    ) as exc:
        print("STATUS=ERROR", file=sys.stderr)
        print("EVALUATOR_VALID=false", file=sys.stderr)
        print(f"ERROR={exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except Exception as exc:  # noqa: BLE001
        print("STATUS=ERROR", file=sys.stderr)
        print("EVALUATOR_VALID=false", file=sys.stderr)
        print(f"ERROR={type(exc).__name__}:{exc}", file=sys.stderr)
        return EXIT_INTERNAL

    if args.output_path is not None:
        out = args.output_path.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(serialize_result_json_v0(result), encoding="utf-8")

    if args.json:
        sys.stdout.write(serialize_result_json_v0(result))
    else:
        for line in result_to_machine_lines(result):
            print(line)

    if not (result.evaluator_valid and result.status == "PASS"):
        return EXIT_INVALID_INPUT
    if result.economic_closeout_status != "COMPLETE":
        return EXIT_INVALID_INPUT
    if result.automatic_next_research_action_allowed:
        return EXIT_INVALID_INPUT
    if not result.operator_selection_required:
        return EXIT_INVALID_INPUT
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
