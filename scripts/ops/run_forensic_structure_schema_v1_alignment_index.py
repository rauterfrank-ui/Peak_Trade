#!/usr/bin/env python3
"""FORENSIC_STRUCTURE_SCHEMA_V1 binding-candidate alignment-index runner.

Additive derived/non-authoritative layer. Does not mutate source, sidecar,
A–L retained inputs, or PR #6063 disposition inputs. Does not close residuals.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_AUTHORITY,
    ALIGNMENT_OUTPUT_ROLE,
    EXTERNAL_ALIGNMENT_DATASET_DIR,
    REPO_ALIGNMENT_RELPATH,
)
from scripts.ops.forensic_structure_schema_v1.alignment_persist import (
    persist_alignment_index,
)
from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes


def _print_violation(exc: TransformationContractViolation) -> None:
    print(f"TRANSFORMATION_CONTRACT_VIOLATION rule={exc.rule}")
    print(exc.message)
    print("OUTPUT_ELIGIBLE=false")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FORENSIC_STRUCTURE_SCHEMA_V1 binding-candidate alignment-index runner"
    )
    parser.add_argument("--source", default=str(BOUND_SOURCE))
    parser.add_argument("--sidecar", default=str(BOUND_SIDECAR))
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--persist-dir", default="")
    parser.add_argument("--dataset-dir", default="")
    parser.add_argument("--two-run-determinism", action="store_true")
    args = parser.parse_args(argv)

    if not bound_inputs_available() and args.source == str(BOUND_SOURCE):
        print("BOUND_INPUTS_ABSENT=true")
        return 2

    tmp_ctx = None
    if args.persist_dir:
        reports_dir = args.persist_dir
    elif args.persist:
        reports_dir = REPO_ALIGNMENT_RELPATH
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="pt_fssv1_align_")
        reports_dir = tmp_ctx.name
    dataset_dir = args.dataset_dir or (
        EXTERNAL_ALIGNMENT_DATASET_DIR if args.persist else reports_dir
    )

    try:
        cached = run_bound_transformer()
        started = time.perf_counter()
        first = persist_alignment_index(
            source_path=args.source,
            sidecar_path=args.sidecar,
            reports_dir=reports_dir,
            dataset_dir=dataset_dir if args.persist or args.dataset_dir else reports_dir,
            result=cached,
        )
        print(f"OUTPUT_ROLE={ALIGNMENT_OUTPUT_ROLE}")
        print(f"OUTPUT_AUTHORITY={ALIGNMENT_AUTHORITY}")
        print("OUTPUT_CANONICAL=false")
        print("SEMANTIC_BINDING_PERFORMED=false")
        print("RESIDUAL_CLOSE_PERFORMED=false")
        print(f"T4_RECORD_COUNT={first.index.counts['T4_RECORD_COUNT']}")
        print(f"LAYER3_RELATION_COUNT={first.index.counts['LAYER3_RELATION_COUNT']}")
        print(f"ENDPOINT_RECORD_COUNT={first.index.counts['ENDPOINT_RECORD_COUNT']}")
        print(f"VIEW_COUNT={first.index.counts['VIEW_COUNT']}")
        print(f"INDEX_SHA256={first.index_sha256}")
        print(f"MANIFEST_SHA256={first.manifest_sha256}")
        print(f"REPORTS_DIR={first.reports_dir}")
        print(f"DATASET_DIR={first.dataset_dir}")
        print(f"WALLCLOCK_SECONDS_STDOUT_ONLY={time.perf_counter() - started:.3f}")
        if args.two_run_determinism:
            with tempfile.TemporaryDirectory(prefix="pt_fssv1_align2_") as tmp:
                second = persist_alignment_index(
                    source_path=args.source,
                    sidecar_path=args.sidecar,
                    reports_dir=tmp,
                    dataset_dir=tmp,
                    result=cached,
                )
                match = first.index_sha256 == second.index_sha256
                shard_match = first.shard_sha256s == second.shard_sha256s
                print(f"RUN_1_INDEX_SHA256={first.index_sha256}")
                print(f"RUN_2_INDEX_SHA256={second.index_sha256}")
                print(f"DETERMINISTIC_INDEX_BYTES={str(match).lower()}")
                print(f"DETERMINISTIC_SHARD_BYTES={str(shard_match).lower()}")
                payload_match = dumps_canonical_bytes(
                    first.index.to_canonical()
                ) == dumps_canonical_bytes(second.index.to_canonical())
                print(f"DETERMINISTIC_FULL_INDEX={str(payload_match).lower()}")
                if not (match and shard_match and payload_match):
                    print("DETERMINISM_FAILURE=true")
                    return 2
                print("DETERMINISM_TWO_RUN=PASS")
        return 0
    except TransformationContractViolation as exc:
        _print_violation(exc)
        return 2
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
