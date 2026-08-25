#!/usr/bin/env python3
"""FORENSIC_STRUCTURE_SCHEMA_V1 adjudication-contract runner.

Derived/non-authoritative infrastructure. Does not mutate source, sidecar,
A-L retained inputs, disposition inputs, or the alignment index. Does not
close residuals or emit PROVEN_OCCURRENCE_IDENTITY.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    ADJUDICATION_AUTHORITY,
    ADJUDICATION_OUTPUT_ROLE,
    REPO_ADJUDICATION_RELPATH,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_persist import (
    persist_adjudication_contract,
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
        description="FORENSIC_STRUCTURE_SCHEMA_V1 adjudication-contract runner"
    )
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--persist-dir", default="")
    parser.add_argument("--two-run-determinism", action="store_true")
    args = parser.parse_args(argv)

    tmp_ctx = None
    if args.persist_dir:
        reports_dir = args.persist_dir
    elif args.persist:
        reports_dir = REPO_ADJUDICATION_RELPATH
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="pt_fssv1_adj_")
        reports_dir = tmp_ctx.name

    try:
        started = time.perf_counter()
        first = persist_adjudication_contract(reports_dir=reports_dir)
        counts = first.contract.counts
        print(f"OUTPUT_ROLE={ADJUDICATION_OUTPUT_ROLE}")
        print(f"OUTPUT_AUTHORITY={ADJUDICATION_AUTHORITY}")
        print("OUTPUT_CANONICAL=false")
        print("SEMANTIC_BINDING_PERFORMED=false")
        print("RESIDUAL_CLOSE_PERFORMED=false")
        print(f"OCCURRENCE_BINDING_CANDIDATE_COUNT={counts['OCCURRENCE_BINDING_CANDIDATE_COUNT']}")
        print(f"CANDIDATE_FAMILY_COUNT={counts['CANDIDATE_FAMILY_COUNT']}")
        print(f"COMPETING_CANDIDATE_SET_COUNT={counts['COMPETING_CANDIDATE_SET_COUNT']}")
        print(f"COMPETING_CANDIDATE_MEMBER_COUNT={counts['COMPETING_CANDIDATE_MEMBER_COUNT']}")
        print(
            "ORIGINAL_AMBIGUOUS_BINDING_CANDIDATE_COUNT="
            f"{counts['ORIGINAL_AMBIGUOUS_BINDING_CANDIDATE_COUNT']}"
        )
        print(f"PROVEN_OCCURRENCE_IDENTITY_COUNT={counts['PROVEN_OCCURRENCE_IDENTITY_COUNT']}")
        print(f"DECISION_RECORD_COUNT={counts['DECISION_RECORD_COUNT']}")
        print(f"NEGATIVE_EVIDENCE_RECORD_COUNT={counts['NEGATIVE_EVIDENCE_RECORD_COUNT']}")
        print(f"CONTRACT_SHA256={first.contract_sha256}")
        print(f"MANIFEST_SHA256={first.manifest_sha256}")
        print(f"REPORTS_DIR={first.reports_dir}")
        print(f"WALLCLOCK_SECONDS_STDOUT_ONLY={time.perf_counter() - started:.3f}")
        if args.two_run_determinism:
            with tempfile.TemporaryDirectory(prefix="pt_fssv1_adj2_") as tmp:
                second = persist_adjudication_contract(reports_dir=tmp)
                match = first.contract_sha256 == second.contract_sha256
                shard_match = first.shard_sha256s == second.shard_sha256s
                print(f"RUN_1_CONTRACT_SHA256={first.contract_sha256}")
                print(f"RUN_2_CONTRACT_SHA256={second.contract_sha256}")
                print(f"DETERMINISTIC_CONTRACT_BYTES={str(match).lower()}")
                print(f"DETERMINISTIC_SHARD_BYTES={str(shard_match).lower()}")
                payload_match = dumps_canonical_bytes(
                    first.contract.to_canonical()
                ) == dumps_canonical_bytes(second.contract.to_canonical())
                print(f"DETERMINISTIC_FULL_CONTRACT={str(payload_match).lower()}")
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
