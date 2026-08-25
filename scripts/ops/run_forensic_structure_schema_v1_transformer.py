#!/usr/bin/env python3
"""Read-only FORENSIC_STRUCTURE_SCHEMA_V1 transformer validation runner.

Does not mutate source or sidecar. Default output is ephemeral / omitted.
Retained forensic datasets are not authorized.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from scripts.ops.forensic_structure_schema_v1.constants import (
    BOUND_SIDECAR_PATH,
    BOUND_SOURCE_PATH,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.transformer import transform_read_only


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FORENSIC_STRUCTURE_SCHEMA_V1 transformer (read-only)"
    )
    parser.add_argument("--source", default=BOUND_SOURCE_PATH)
    parser.add_argument("--sidecar", default=BOUND_SIDECAR_PATH)
    parser.add_argument(
        "--persist-test-artifact-dir",
        default="",
        help="Optional directory for TEST_ARTIFACT_ONLY output. Empty = no persist.",
    )
    parser.add_argument(
        "--ephemeral-artifact",
        action="store_true",
        help="Write a temp artifact and delete it after hashing (test only).",
    )
    args = parser.parse_args(argv)

    persist_dir: str | None = args.persist_test_artifact_dir or None
    tmp_ctx = None
    if args.ephemeral_artifact:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="pt_fssv1_")
        persist_dir = tmp_ctx.name
    try:
        result = transform_read_only(
            source_path=args.source,
            sidecar_path=args.sidecar,
            persist_test_artifact_dir=persist_dir,
        )
    except TransformationContractViolation as exc:
        print(f"TRANSFORMATION_CONTRACT_VIOLATION rule={exc.rule}")
        print(exc.message)
        print("OUTPUT_ELIGIBLE=false")
        print("OUTPUT_MUST_NOT_BE_TREATED_AS_VALID=true")
        return 2
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()

    print("OUTPUT_ROLE=TEST_ARTIFACT_ONLY")
    print("OUTPUT_AUTHORITY=NONE")
    print(f"OUTPUT_ELIGIBLE={str(result.output_eligible).lower()}")
    print(f"STAGES={','.join(result.state.stages_completed)}")
    print(f"SOURCE_SHA256_BEFORE={result.state.source_sha256_before}")
    print(f"SOURCE_SHA256_AFTER={result.state.source_sha256_after}")
    print(f"SIDECAR_SHA256_BEFORE={result.state.sidecar_sha256_before}")
    print(f"SIDECAR_SHA256_AFTER={result.state.sidecar_sha256_after}")
    print(f"PAYLOAD_SHA256_LEN={len(result.payload_bytes)}")
    return 0 if result.output_eligible else 1


if __name__ == "__main__":
    sys.exit(main())
