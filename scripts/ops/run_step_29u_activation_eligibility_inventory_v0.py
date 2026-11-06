#!/usr/bin/env python3
"""Operator CLI: STEP 29U Activation Eligibility Inventory v0.

Offline, read-only, non-activating. Distinguishes evaluator health / evidence
validity (exit code) from eligibility result (ACTIVATION_ELIGIBLE; expected
false while future Operator-GO is absent).

Exit codes:
  0  successful evaluation; activation ineligible
  2  successful evaluation; non-operator prerequisites complete but GO absent
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
    EligibilityInventoryOverridesV0,
    Step29UActivationEligibilityInventoryError,
    evaluate_step_29u_activation_eligibility_inventory_v0,
    result_to_machine_lines,
    serialize_result_json_v0,
)
from src.ops.step_29u_audit_provenance_v0 import (  # noqa: E402
    Step29UAuditProvenanceError,
)
from src.ops.step_29u_economic_validity_readiness_v0 import (  # noqa: E402
    Step29UEconomicValidityReadinessError,
)

EXIT_OK_INELIGIBLE = 0
EXIT_INVALID_INPUT = 1
EXIT_OK_NON_OPERATOR_COMPLETE_GO_ABSENT = 2
EXIT_INTERNAL = 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Evaluate STEP 29U activation eligibility inventory (offline, "
            "fail-closed, non-activating). Composes audit/provenance and "
            "economic-validity readiness. Inventory only — not Activation."
        )
    )
    p.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    p.add_argument(
        "--soak-dir",
        type=Path,
        default=None,
        help="Optional override path to soak evidence directory (read-only).",
    )
    p.add_argument(
        "--binding-evidence-dir",
        type=Path,
        default=None,
        help="Optional override path to Step 29U binding evidence (read-only).",
    )
    p.add_argument(
        "--readiness-config",
        type=Path,
        default=None,
        help="Optional override path to readiness gate TOML (read-only).",
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
        result = evaluate_step_29u_activation_eligibility_inventory_v0(
            repo_root=repo_root,
            overrides=EligibilityInventoryOverridesV0(
                soak_dir=args.soak_dir,
                binding_evidence_dir=args.binding_evidence_dir,
                readiness_config_path=args.readiness_config,
            ),
        )
    except (
        Step29UActivationEligibilityInventoryError,
        Step29UAuditProvenanceError,
        Step29UEconomicValidityReadinessError,
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
    if (
        result.non_operator_prerequisites_complete
        and not result.future_operator_go_present
        and not result.activation_eligible
    ):
        return EXIT_OK_NON_OPERATOR_COMPLETE_GO_ABSENT
    return EXIT_OK_INELIGIBLE


if __name__ == "__main__":
    raise SystemExit(main())
