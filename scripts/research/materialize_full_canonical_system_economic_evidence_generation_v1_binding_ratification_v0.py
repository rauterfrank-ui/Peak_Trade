#!/usr/bin/env python3
"""Materialize FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1 binding ratification."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.full_canonical_system_economic_evidence_generation_v1 import (
    BINDING_CONFIG_REL_PATH,
    EVIDENCE_CLASS_CONFIG_REL_PATH,
    GO_TOKEN,
    RATIFICATION_CONFIG_REL_PATH,
    MaterializationVerdict,
    ValidationVerdict,
    materialize_and_validate_binding_ratification_v0,
    serialize_canonical_json_v0,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize evidence-class contract, versioned FULL_CANONICAL_SYSTEM binding, "
            "and ratification artifacts for generation v1."
        )
    )
    parser.add_argument("--go-token", required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    if args.go_token != GO_TOKEN:
        print(f"GO_TOKEN_INVALID expected={GO_TOKEN} got={args.go_token}", file=sys.stderr)
        return 2

    result = materialize_and_validate_binding_ratification_v0(repo_root=args.repo_root)
    if result.verdict != MaterializationVerdict.COMPLETE:
        print("MATERIALIZATION_INCOMPLETE", file=sys.stderr)
        for reason in result.fail_reasons:
            print(reason, file=sys.stderr)
        return 1
    if result.validation_verdict != ValidationVerdict.ACCEPTED:
        print("VALIDATION_REJECTED", file=sys.stderr)
        for reason in result.fail_reasons:
            print(reason, file=sys.stderr)
        return 1

    ratification = result.artifact
    evidence_class = ratification["evidence_class_contract"]
    binding = ratification["versioned_binding"]

    if args.write:
        targets = (
            (args.repo_root / EVIDENCE_CLASS_CONFIG_REL_PATH, evidence_class),
            (args.repo_root / BINDING_CONFIG_REL_PATH, binding),
            (args.repo_root / RATIFICATION_CONFIG_REL_PATH, ratification),
        )
        for path, payload in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(serialize_canonical_json_v0(payload), encoding="utf-8")
            print(f"WROTE={path}")

    print(f"STATUS=PASS")
    print(f"BINDING_ID={ratification['binding_id']}")
    print(f"EVIDENCE_CLASS_ID={ratification['evidence_class_id']}")
    print(f"BINDING_DIGEST={ratification['binding_digest']}")
    print(f"RATIFICATION_DIGEST={ratification['ratification_digest']}")
    print("ECONOMIC_EVALUATION_EXECUTED=false")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
