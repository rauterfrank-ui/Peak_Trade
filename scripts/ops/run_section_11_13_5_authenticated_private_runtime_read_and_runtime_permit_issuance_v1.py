#!/usr/bin/env python3
"""Authenticated private positions GET then runtime permit issuance. No POST."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (  # noqa: E402
    DEFAULT_VAULT_RELATIVE,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (  # noqa: E402
    AuthenticatedPrivateRuntimeReadError,
    execute_authenticated_private_runtime_read_and_permit_issuance_v1,
    secretref_identity_without_values_v1,
)

REPO_ROOT = _REPO_ROOT
DEFAULT_VAULT = REPO_ROOT / ".ops_local" / DEFAULT_VAULT_RELATIVE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", required=True)
    parser.add_argument("--vault-file", default=str(DEFAULT_VAULT))
    parser.add_argument("--execute-get", action="store_true")
    args = parser.parse_args(argv)
    if args.owner_go != OWNER_GO:
        print(f"OWNER_GO_MISMATCH:{args.owner_go}", file=sys.stderr)
        return 2
    if args.bound_origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        print(f"ORIGIN_MAIN_SHA_MISMATCH:{args.bound_origin_main_sha}", file=sys.stderr)
        return 2
    if not args.execute_get:
        print("EXECUTE_GET_FLAG_REQUIRED", file=sys.stderr)
        return 2
    try:
        identity = secretref_identity_without_values_v1(vault_file=Path(args.vault_file))
    except AuthenticatedPrivateRuntimeReadError as exc:
        print(f"SECRETREF_IDENTITY_FAIL:{exc}", file=sys.stderr)
        return 2
    print("SECRETREF_IDENTITY=")
    print(json.dumps(identity, indent=2, sort_keys=True))
    evidence_root = REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME
    evidence_root.mkdir(parents=True, exist_ok=True)
    try:
        result = execute_authenticated_private_runtime_read_and_permit_issuance_v1(
            owner_go=args.owner_go,
            origin_main_sha=args.bound_origin_main_sha,
            evidence_root=evidence_root,
            vault_file=Path(args.vault_file),
        )
    except AuthenticatedPrivateRuntimeReadError as exc:
        print(f"AUTHENTICATED_PRIVATE_RUNTIME_READ_FAILED:{exc}", file=sys.stderr)
        return 2
    print("AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_PERMIT_ISSUANCE_RESULT=")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    print(f"EVIDENCE_PACK={result.get('EVIDENCE_PACK')}")
    print(f"MANIFEST_VERIFY_RC={result.get('MANIFEST_VERIFY_RC')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
