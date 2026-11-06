"""CLI entry: ./scripts/pt -m src.ops.full_core_step_29p_fresh_venue_evidence_v1"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ops.full_core_step_29p_fresh_venue_evidence_v1.constants_v1 import (
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.execute_v1 import (
    Step29PFreshVenueEvidenceGetError,
    execute_step_29p_fresh_venue_evidence_gets_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", required=True)
    parser.add_argument("--vault-file", required=True)
    parser.add_argument("--expected-account-identity", default="")
    parser.add_argument("--execute-gets", action="store_true")
    args = parser.parse_args(argv)
    if args.owner_go != OWNER_GO:
        print(f"OWNER_GO_MISMATCH:{args.owner_go}")
        return 2
    if args.bound_origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        print(f"ORIGIN_MAIN_SHA_MISMATCH:{args.bound_origin_main_sha}")
        return 2
    if not args.execute_gets:
        print("EXECUTE_GETS_FLAG_REQUIRED")
        return 2
    repo_root = Path(__file__).resolve().parents[3]
    evidence_root = repo_root / "evidence" / "ops" / EVIDENCE_DIRNAME
    try:
        result = execute_step_29p_fresh_venue_evidence_gets_v1(
            owner_go=args.owner_go,
            origin_main_sha=args.bound_origin_main_sha,
            evidence_root=evidence_root,
            vault_file=Path(args.vault_file),
            expected_account_identity=args.expected_account_identity,
        )
    except Step29PFreshVenueEvidenceGetError as exc:
        print(f"STEP_29P_FRESH_GET_FAIL_CLOSED:{exc}")
        return 2
    print("STEP_29P_FRESH_GET_RESULT=")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    print(f"EVIDENCE_PACK={result['EVIDENCE_PACK']}")
    print(f"MANIFEST_VERIFY_RC={result['MANIFEST_VERIFY_RC']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
