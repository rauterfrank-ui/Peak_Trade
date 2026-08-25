#!/usr/bin/env python3
"""FORENSIC_STRUCTURE_SCHEMA_V1 binding-disposition layer runner.

Additive derived/non-authoritative layer for SW-R-002/004/009.
Does not mutate source or sidecar. Does not close residuals.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    DISPOSITION_AUTHORITY,
    DISPOSITION_OUTPUT_ROLE,
    REPO_DISPOSITION_RELPATH,
)
from scripts.ops.forensic_structure_schema_v1.disposition_persist import (
    persist_binding_disposition,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)


def _print_violation(exc: TransformationContractViolation) -> None:
    print(f"TRANSFORMATION_CONTRACT_VIOLATION rule={exc.rule}")
    print(exc.message)
    print("OUTPUT_ELIGIBLE=false")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FORENSIC_STRUCTURE_SCHEMA_V1 binding-disposition runner"
    )
    parser.add_argument("--source", default=str(BOUND_SOURCE))
    parser.add_argument("--sidecar", default=str(BOUND_SIDECAR))
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--persist-dir", default="")
    parser.add_argument("--two-run-determinism", action="store_true")
    args = parser.parse_args(argv)

    if not bound_inputs_available() and args.source == str(BOUND_SOURCE):
        print("BOUND_INPUTS_ABSENT=true")
        return 2

    tmp_ctx = None
    if args.persist_dir:
        reports_dir = args.persist_dir
    elif args.persist:
        reports_dir = REPO_DISPOSITION_RELPATH
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="pt_fssv1_disp_")
        reports_dir = tmp_ctx.name

    try:
        cached = run_bound_transformer()
        started = time.perf_counter()
        first = persist_binding_disposition(
            source_path=args.source,
            sidecar_path=args.sidecar,
            reports_dir=reports_dir,
            result=cached,
        )
        print(f"OUTPUT_ROLE={DISPOSITION_OUTPUT_ROLE}")
        print(f"OUTPUT_AUTHORITY={DISPOSITION_AUTHORITY}")
        print("OUTPUT_CANONICAL=false")
        print("SEMANTIC_BINDING_PERFORMED=false")
        print("RESIDUAL_CLOSE_PERFORMED=false")
        print(f"LAYER_SHA256={first.layer_sha256}")
        print(f"MANIFEST_SHA256={first.manifest_sha256}")
        print(f"REPORTS_DIR={first.reports_dir}")
        print(f"WALLCLOCK_SECONDS_STDOUT_ONLY={time.perf_counter() - started:.3f}")
        if args.two_run_determinism:
            with tempfile.TemporaryDirectory(prefix="pt_fssv1_disp2_") as tmp:
                second = persist_binding_disposition(
                    source_path=args.source,
                    sidecar_path=args.sidecar,
                    reports_dir=tmp,
                    result=cached,
                )
                match = first.layer_sha256 == second.layer_sha256
                print(f"RUN_1_LAYER_SHA256={first.layer_sha256}")
                print(f"RUN_2_LAYER_SHA256={second.layer_sha256}")
                print(f"DETERMINISTIC_LAYER_BYTES={str(match).lower()}")
                if not match:
                    print("DETERMINISM_FAILURE=true")
                    return 2
        return 0
    except TransformationContractViolation as exc:
        _print_violation(exc)
        return 2
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
