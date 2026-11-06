#!/usr/bin/env python3
"""Operator CLI: STEP 29U Terminal Unchanged Final Fleet Hypothesis Retirement v0.

Offline, fail-closed, non-activating. Applies the operator-selected recovery
option RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES against the canonical
Final Research Fleet terminal FAIL inventory.

Exit codes:
  0  retirement COMPLETE; economic FAIL unchanged; no activation
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

from src.ops.step_29u_economic_failure_closeout_recovery_decision_v0 import (  # noqa: E402
    Step29UEconomicFailureCloseoutError,
)
from src.ops.step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0 import (  # noqa: E402
    SELECTED_RECOVERY_OPTION,
    Step29UTerminalFleetHypothesisRetirementError,
    TerminalFleetHypothesisRetirementOverridesV0,
    evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0,
    result_to_machine_lines,
    serialize_result_json_v0,
)

EXIT_OK = 0
EXIT_INVALID_INPUT = 1
EXIT_INTERNAL = 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Retire terminal unchanged Final Research Fleet hypotheses after "
            "operator selection of RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES "
            "(offline, fail-closed, non-activating)."
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
        "--retirement-config",
        type=Path,
        default=None,
        help="Optional override path to retirement inventory SSOT JSON.",
    )
    p.add_argument(
        "--selected-recovery-option",
        type=str,
        default=SELECTED_RECOVERY_OPTION,
        help="Must equal RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES.",
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
        result = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=repo_root,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                fleet_closeout_path=args.fleet_closeout,
                retirement_config_path=args.retirement_config,
                selected_recovery_option=args.selected_recovery_option,
            ),
        )
    except (
        Step29UTerminalFleetHypothesisRetirementError,
        Step29UEconomicFailureCloseoutError,
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

    if not (result.evaluator_valid and result.status == "COMPLETE"):
        return EXIT_INVALID_INPUT
    if result.retirement_status != "COMPLETE":
        return EXIT_INVALID_INPUT
    if result.economic_validity_status != "FAIL":
        return EXIT_INVALID_INPUT
    if result.activation_eligible or result.activated:
        return EXIT_INVALID_INPUT
    if result.automatic_backlog_selection_allowed:
        return EXIT_INVALID_INPUT
    if result.next_research_candidate_selected:
        return EXIT_INVALID_INPUT
    if not result.operator_selection_required_for_next_material_research:
        return EXIT_INVALID_INPUT
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
