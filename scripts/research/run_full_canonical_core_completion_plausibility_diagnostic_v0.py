#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_CONFIRM = "GO_FULL_CANONICAL_CORE_COMPLETION_AND_PLAUSIBILITY_EVALUATION_DIAGNOSTIC_V0"
EVIDENCE_CLASS = "FULL_CANONICAL_CORE_COMPLETION_AND_PLAUSIBILITY_EVALUATION_V0"

AUTHORITY_FALSE_FIELDS = (
    "promotion_admissible",
    "runtime_admissible",
    "live_authorized",
    "orders_allowed",
    "economic_validity_claim_allowed",
    "scheduler_runtime_allowed",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "canary_authorized",
    "credential_access_allowed",
)


def _repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"POLICY_MISSING: {path}")
    data = json.loads(path.read_text())
    digest_keys = (
        "policy_digest",
        "config_digest",
        "implementation_digest",
        "semantic_digest",
        "source_policy_digest",
        "owner_policy_decision_digest",
    )
    if not any(data.get(k) for k in digest_keys):
        raise SystemExit("POLICY_DIGEST_MISSING")
    return data


def _as_mapping(result: Any) -> dict[str, Any]:
    if hasattr(result, "to_dict"):
        value = result.to_dict()
    elif hasattr(result, "__dict__"):
        value = dict(result.__dict__)
    elif isinstance(result, dict):
        value = result
    else:
        value = {"result_repr": repr(result)}
    return dict(value)


def _authority_false_or_block(result: dict[str, Any]) -> None:
    violations = []
    for key in AUTHORITY_FALSE_FIELDS:
        if result.get(key) is True:
            violations.append(key)
    if violations:
        raise SystemExit("AUTHORITY_FLAG_TRUE_BLOCKED: " + ",".join(sorted(violations)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--repo-root", type=Path, default=_repo_root_from_file())
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(
            "config/research/full_canonical_core_completion_plausibility_evaluation_policy_v0.json"
        ),
    )
    parser.add_argument(
        "--binding-completion",
        type=Path,
        default=Path("config/research/final_research_fleet_versioned_binding_completion_v0.json"),
    )
    parser.add_argument("--evidence-class", default=EVIDENCE_CLASS)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    if args.confirm != REQUIRED_CONFIRM:
        raise SystemExit("INVALID_CONFIRM_TOKEN")
    if args.evidence_class != EVIDENCE_CLASS:
        raise SystemExit("INVALID_EVIDENCE_CLASS")

    policy_path = args.policy if args.policy.is_absolute() else repo_root / args.policy
    binding_path = (
        args.binding_completion
        if args.binding_completion.is_absolute()
        else repo_root / args.binding_completion
    )
    _load_policy(policy_path)
    if not binding_path.exists():
        raise SystemExit(f"BINDING_COMPLETION_MISSING: {binding_path}")

    from src.research.full_canonical_core_completion_plausibility_evaluation_v0 import (
        run_diagnostic_evaluation_v0,
    )

    result = run_diagnostic_evaluation_v0(
        confirm=args.confirm,
        repo_root=repo_root,
        durable_evidence_root=args.durable_evidence_root.resolve(),
    )

    payload = _as_mapping(result)
    payload.setdefault("status", "SYSTEM_DIAGNOSTIC_ONLY")
    payload["evidence_class"] = EVIDENCE_CLASS
    payload["promotion_admissible"] = False
    payload["runtime_admissible"] = False
    payload["live_authorized"] = False
    payload["orders_allowed"] = False
    payload["economic_validity_claim_allowed"] = False
    payload["system_economic_evidence_admissible"] = False
    payload.setdefault(
        "promotion_boundary_status",
        "DIAGNOSTIC_ONLY_NOT_PROMOTION_EVIDENCE",
    )
    payload.setdefault("promotion_boundary_reason_codes", [])
    payload["scheduler_runtime_allowed"] = False
    payload["shadow_authorized"] = False
    payload["paper_authorized"] = False
    payload["testnet_authorized"] = False
    payload["canary_authorized"] = False
    payload["credential_access_allowed"] = False
    _authority_false_or_block(payload)

    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
