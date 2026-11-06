#!/usr/bin/env python3
"""FORENSIC_STRUCTURE_SCHEMA_V1 transformer runner.

Default path remains TEST_ARTIFACT_ONLY validation.
``--persist-retained-derived`` writes a derived, non-authoritative dataset.
Does not mutate source or sidecar. Does not promote authority.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time

from scripts.ops.forensic_structure_schema_v1.constants import (
    BOUND_SIDECAR_PATH,
    BOUND_SOURCE_PATH,
    EXTERNAL_RETAINED_DATASET_DIR,
    OUTPUT_AUTHORITY,
    REPO_RETAINED_REPORTS_RELPATH,
    RETAINED_OUTPUT_ROLE,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.retained_output import persist_retained_derived
from scripts.ops.forensic_structure_schema_v1.transformer import transform_read_only


def _print_violation(exc: TransformationContractViolation) -> None:
    print(f"TRANSFORMATION_CONTRACT_VIOLATION rule={exc.rule}")
    print(exc.message)
    print("OUTPUT_ELIGIBLE=false")
    print("OUTPUT_MUST_NOT_BE_TREATED_AS_VALID=true")


def _print_test_artifact(result) -> None:
    print("OUTPUT_ROLE=TEST_ARTIFACT_ONLY")
    print(f"OUTPUT_AUTHORITY={OUTPUT_AUTHORITY}")
    print(f"OUTPUT_ELIGIBLE={str(result.output_eligible).lower()}")
    print(f"STAGES={','.join(result.state.stages_completed)}")
    print(f"SOURCE_SHA256_BEFORE={result.state.source_sha256_before}")
    print(f"SOURCE_SHA256_AFTER={result.state.source_sha256_after}")
    print(f"SIDECAR_SHA256_BEFORE={result.state.sidecar_sha256_before}")
    print(f"SIDECAR_SHA256_AFTER={result.state.sidecar_sha256_after}")
    print(f"PAYLOAD_SHA256_LEN={len(result.payload_bytes)}")


def _print_retained(persist, *, run_label: str, wallclock_seconds: float) -> None:
    state = persist.result.state
    print(f"RUN={run_label}")
    print(f"OUTPUT_ROLE={RETAINED_OUTPUT_ROLE}")
    print(f"OUTPUT_AUTHORITY={OUTPUT_AUTHORITY}")
    print("OUTPUT_IS_CANONICAL=false")
    print(f"OUTPUT_ELIGIBLE={str(persist.result.output_eligible).lower()}")
    print(f"STAGES={','.join(state.stages_completed)}")
    print(f"DATASET_SHA256={persist.dataset_sha256}")
    print(f"DATASET_BYTES={persist.dataset_bytes}")
    print(f"DATASET_RECORD_COUNT={persist.dataset_record_count}")
    print(f"DATASET_GIT_PERSISTENCE={persist.dataset_git_persistence}")
    print(f"MANIFEST_SHA256={persist.manifest_sha256}")
    print(f"MANIFEST_SEMANTIC_PAYLOAD_SHA256={persist.manifest_semantic_payload_sha256}")
    print(f"REPORTS_DIR={persist.reports_dir}")
    print(f"DATASET_DIR={persist.dataset_dir}")
    print(f"WALLCLOCK_SECONDS_STDOUT_ONLY={wallclock_seconds:.3f}")
    print("DETERMINISM_EXCLUDED_ARTIFACT_FIELDS=none")
    print("DETERMINISM_EXCLUDED_STDOUT_FIELDS=WALLCLOCK_SECONDS_STDOUT_ONLY")
    print(f"SOURCE_SHA256_BEFORE={persist.source_stat_before.sha256}")
    print(f"SOURCE_SHA256_AFTER={persist.source_stat_after.sha256}")
    print(f"SIDECAR_SHA256_BEFORE={persist.sidecar_stat_before.sha256}")
    print(f"SIDECAR_SHA256_AFTER={persist.sidecar_stat_after.sha256}")
    print(
        "SOURCE_MTIME_CHANGED_WITHOUT_BYTE_CHANGE="
        f"{str(persist.source_mtime_changed_without_byte_change).lower()}"
    )
    print(
        "SIDECAR_MTIME_CHANGED_WITHOUT_BYTE_CHANGE="
        f"{str(persist.sidecar_mtime_changed_without_byte_change).lower()}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FORENSIC_STRUCTURE_SCHEMA_V1 transformer runner")
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
    parser.add_argument(
        "--persist-retained-derived",
        action="store_true",
        help="Persist derived non-authoritative transformation artifacts.",
    )
    parser.add_argument(
        "--persist-retained-reports-dir",
        default="",
        help="Git-suitable reports directory. Empty = repo derived reports path.",
    )
    parser.add_argument(
        "--persist-retained-dataset-dir",
        default="",
        help="Dataset directory. Empty = external Documents derived path.",
    )
    parser.add_argument(
        "--two-run-determinism",
        action="store_true",
        help="Run retained persist twice and compare deterministic payloads.",
    )
    args = parser.parse_args(argv)

    if args.persist_retained_derived:
        reports_dir = args.persist_retained_reports_dir or REPO_RETAINED_REPORTS_RELPATH
        dataset_dir = args.persist_retained_dataset_dir or EXTERNAL_RETAINED_DATASET_DIR
        try:
            started = time.perf_counter()
            first = persist_retained_derived(
                source_path=args.source,
                sidecar_path=args.sidecar,
                reports_dir=reports_dir,
                dataset_dir=dataset_dir,
            )
            _print_retained(
                first,
                run_label="1",
                wallclock_seconds=time.perf_counter() - started,
            )
            if args.two_run_determinism:
                with tempfile.TemporaryDirectory(prefix="pt_fssv1_run2_") as tmp:
                    started2 = time.perf_counter()
                    second = persist_retained_derived(
                        source_path=args.source,
                        sidecar_path=args.sidecar,
                        reports_dir=f"{tmp}/reports",
                        dataset_dir=f"{tmp}/dataset",
                    )
                    _print_retained(
                        second,
                        run_label="2",
                        wallclock_seconds=time.perf_counter() - started2,
                    )
                    match = first.dataset_sha256 == second.dataset_sha256
                    print(f"RUN_1_DATASET_SHA256={first.dataset_sha256}")
                    print(f"RUN_2_DATASET_SHA256={second.dataset_sha256}")
                    print(f"RUN_SHA_MATCH={str(match).lower()}")
                    print(
                        "DETERMINISTIC_DATASET_BYTES="
                        f"{str(first.dataset_sha256 == second.dataset_sha256).lower()}"
                    )
                    print(
                        "DETERMINISTIC_RECORD_COUNTS="
                        f"{str(first.record_counts == second.record_counts).lower()}"
                    )
                    ids_match = [
                        env["transformation_local_id"]
                        for env in first.dataset["semantic_envelopes"]
                    ] == [
                        env["transformation_local_id"]
                        for env in second.dataset["semantic_envelopes"]
                    ]
                    print(f"DETERMINISTIC_IDS={str(ids_match).lower()}")
                    print(
                        "MANIFEST_SEMANTIC_PAYLOAD_MATCH="
                        f"{str(first.manifest_semantic_payload_sha256 == second.manifest_semantic_payload_sha256).lower()}"
                    )
                    if not match or first.record_counts != second.record_counts or not ids_match:
                        print("DETERMINISM_FAILURE=true")
                        return 2
            return 0 if first.result.output_eligible else 1
        except TransformationContractViolation as exc:
            _print_violation(exc)
            return 2

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
        _print_violation(exc)
        return 2
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()

    _print_test_artifact(result)
    return 0 if result.output_eligible else 1


if __name__ == "__main__":
    sys.exit(main())
