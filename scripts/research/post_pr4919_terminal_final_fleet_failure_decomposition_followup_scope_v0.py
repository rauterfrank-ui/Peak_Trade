#!/usr/bin/env python3
"""Materialize post-PR4919 terminal final fleet failure decomposition follow-up scope v0.

Offline-only scope-definition evidence bundle. No economic evaluation, no evidence execution,
no runtime authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)

SCOPE_ID = "POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_V0"
PROCESS_CLASSIFICATION = (
    "POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_DEFINITION_ONLY_V0"
)
SCOPE_CLASSIFICATION = (
    "POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_DEFINITION_ONLY_V0"
)
CONFIRM_GO = (
    "GO_POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_DEFINITION_V0"
)
NEXT_STEP = (
    "OPERATOR_RATIFIED_NEW_VERSIONED_RESEARCH_SCOPE_OR_FAILURE_DECOMPOSITION_FOLLOWUP_REQUIRED"
)
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0.json"
)
DEFAULT_DOC = (
    _REPO_ROOT
    / "docs/governance/POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_V0.md"
)

FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.adapters",
    "src.broker",
    "src.exchange",
    "src.order",
    "src.shadow",
    "src.paper",
    "src.testnet",
    "src.credentials",
)

REQUIRED_CONFIG_KEYS = (
    "scope_id",
    "scope_version",
    "base_head",
    "parent_pr",
    "parent_closeout_dir",
    "fleet_verdict",
    "economic_validity_offline_gate_pass",
    "promotion_admissible",
    "runtime_rewire_admissible",
    "operator_go_required_for_next_scope",
    "allowed_actions",
    "forbidden_actions",
    "terminal_failure_inputs",
    "followup_taxonomy",
    "required_final_report_fields",
    "next_step",
    "governance_ref",
)

FORBIDDEN_AUTHORITY_FLAGS = (
    "economic_evaluation_authorized",
    "economic_evaluation_executed",
    "runtime_authority_created",
    "new_candidate_ratified",
    "new_candidates_ratified",
    "live_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "orders_allowed",
    "promotion_authority",
    "retry_unchanged_binding_allowed",
    "same_binding_retry_allowed",
    "failed_bindings_retry_allowed",
)


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            errors.append(f"missing required config key: {key}")

    if config.get("scope_id") != SCOPE_ID:
        errors.append("unexpected scope_id")
    if config.get("process_classification") != PROCESS_CLASSIFICATION:
        errors.append("unexpected process_classification")
    if config.get("scope_classification") != SCOPE_CLASSIFICATION:
        errors.append("unexpected scope_classification")
    if config.get("go_token") != CONFIRM_GO:
        errors.append("unexpected go_token")
    if config.get("parent_pr") != 4919:
        errors.append("unexpected parent_pr")
    if config.get("next_step") != NEXT_STEP:
        errors.append("unexpected next_step")
    if config.get("fleet_verdict") != "FLEET_ECONOMIC_VALIDITY_FAIL":
        errors.append("unexpected fleet_verdict")
    if config.get("economic_validity_offline_gate_pass") is not False:
        errors.append("economic_validity_offline_gate_pass must be false")
    if config.get("promotion_admissible") is not False:
        errors.append("promotion_admissible must be false")
    if config.get("runtime_rewire_admissible") is not False:
        errors.append("runtime_rewire_admissible must be false")
    if config.get("operator_go_required_for_next_scope") is not True:
        errors.append("operator_go_required_for_next_scope must be true")

    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        if config.get(flag) is not False:
            errors.append(f"forbidden authority flag must be false: {flag}")

    taxonomy = config.get("followup_taxonomy", [])
    if not isinstance(taxonomy, list) or len(taxonomy) < 8:
        errors.append("followup_taxonomy must contain at least 8 entries")

    return errors


def _verify_optional_manifest(source_dir: Path) -> tuple[int, str]:
    manifest_path = source_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return -1, "manifest_missing"
    ok, msg = verify_manifest_sha256(source_dir)
    return (0 if ok else 1), msg or "ok"


def _build_followup_scope_summary(config: dict[str, Any], doc_sha256: str) -> dict[str, Any]:
    return {
        "authority_effect": config.get("authority_effect", "NONE"),
        "base_head": config["base_head"],
        "config_sha256": _sha256_text(json.dumps(config, indent=2, sort_keys=True) + "\n"),
        "doc_sha256": doc_sha256,
        "economic_validity_offline_gate_pass": False,
        "fleet_verdict": config["fleet_verdict"],
        "followup_class_count": len(config["followup_taxonomy"]),
        "go_token": CONFIRM_GO,
        "go_token_consumption": "CONSUMED_ONCE_FOR_SCOPE_DEFINITION_ONLY",
        "next_step": config["next_step"],
        "non_authorizing": True,
        "offline_only": True,
        "operator_go_required_for_next_scope": True,
        "parent_closeout_dir": config["parent_closeout_dir"],
        "parent_pr": config["parent_pr"],
        "post_merge_head": config.get("post_merge_head"),
        "pre_merge_head": config.get("pre_merge_head"),
        "pr_head": config.get("pr_head"),
        "process_classification": PROCESS_CLASSIFICATION,
        "promotion_admissible": False,
        "runtime_rewire_admissible": False,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "scope_version": config["scope_version"],
        "status": "SCOPE_DEFINED_NOT_EXECUTED",
        "terminal_failure_inputs": config["terminal_failure_inputs"],
        "verdict": "SCOPE_DEFINED_NOT_EXECUTED",
    }


def _build_authority_boundary(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "adapter_submission_allowed": False,
        "arming_allowed": False,
        "canary_allowed": False,
        "core_system_mutation_allowed": False,
        "credentials_required": False,
        "double_play_mutation_allowed": False,
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "evidence_execution_in_this_scope": False,
        "evaluation_execution_in_this_scope": False,
        "failed_bindings_retry_allowed": False,
        "forbidden_actions": sorted(config["forbidden_actions"]),
        "live_authorized": False,
        "master_v2_mutation_allowed": False,
        "new_candidate_ratified": False,
        "new_candidates_ratified": False,
        "no_evaluation_authority": True,
        "no_runtime_authority": True,
        "offline_only": True,
        "operator_go_required_for_next_scope": True,
        "orders_allowed": False,
        "paper_authorized": False,
        "parameter_optimization_allowed": False,
        "policy_threshold_rescue_allowed": False,
        "promotion_admissible": False,
        "promotion_authority": False,
        "runtime_authority": "NONE",
        "runtime_authority_created": False,
        "runtime_rewire_admissible": False,
        "same_binding_retry_allowed": False,
        "scheduler_runtime_allowed": False,
        "shadow_authorized": False,
        "testnet_authorized": False,
        "threshold_lowering_allowed": False,
        "unchanged_retry_allowed": False,
    }


def _build_failure_taxonomy(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "failed_evidence_is_terminal": config.get("failed_evidence_is_terminal", True),
        "fleet_verdict": config["fleet_verdict"],
        "followup_taxonomy": config["followup_taxonomy"],
        "next_step": config["next_step"],
        "not_a_new_candidate": True,
        "not_a_rerun": True,
        "scope_id": SCOPE_ID,
        "terminal_failure_inputs": config["terminal_failure_inputs"],
    }


def run_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0(
    *,
    config_path: Path = DEFAULT_CONFIG,
    governance_doc_path: Path = DEFAULT_DOC,
    output_dir: Path,
) -> dict[str, Any]:
    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")
    if not governance_doc_path.is_file():
        _die(f"ERR:missing governance doc: {governance_doc_path}")

    config = _load_json(config_path)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        _die("ERR:config validation failed", code=1)

    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        _die(f"ERR:output dir not empty: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    parent_closeout_dir = Path(config["parent_closeout_dir"])
    parent_manifest_rc, parent_manifest_msg = _verify_optional_manifest(parent_closeout_dir)
    required_parent_rc = int(config.get("required_parent_manifest_rc", 0))
    if parent_manifest_rc >= 0 and parent_manifest_rc != required_parent_rc:
        _die(f"ERR:parent manifest verify rc mismatch: {parent_closeout_dir}")

    doc_sha256 = _sha256_path(governance_doc_path)
    followup_summary = _build_followup_scope_summary(config, doc_sha256)
    authority_boundary = _build_authority_boundary(config)
    failure_taxonomy = _build_failure_taxonomy(config)

    (output_dir / "FOLLOWUP_SCOPE_SUMMARY.json").write_text(
        json.dumps(followup_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "AUTHORITY_BOUNDARY.json").write_text(
        json.dumps(authority_boundary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "FAILURE_TAXONOMY.json").write_text(
        json.dumps(failure_taxonomy, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "parent_manifest_verify.log").write_text(
        "\n".join(
            [
                f"PARENT_CLOSEOUT_DIR={parent_closeout_dir}",
                f"MANIFEST_VERIFY_RC={parent_manifest_rc}",
                f"MANIFEST_VERIFY_MSG={parent_manifest_msg}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir} ({manifest_msg})")

    return {
        "authority_boundary_path": str(output_dir / "AUTHORITY_BOUNDARY.json"),
        "durable_evidence_path": str(output_dir),
        "failure_taxonomy_path": str(output_dir / "FAILURE_TAXONOMY.json"),
        "followup_scope_summary_path": str(output_dir / "FOLLOWUP_SCOPE_SUMMARY.json"),
        "fleet_verdict": config["fleet_verdict"],
        "manifest_verify_rc": manifest_rc,
        "next_step": config["next_step"],
        "parent_manifest_verify_rc": parent_manifest_rc,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "verdict": "SCOPE_DEFINED_NOT_EXECUTED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize post-PR4919 terminal final fleet failure decomposition follow-up scope v0"
        )
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--governance-doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = run_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0(
        config_path=args.config,
        governance_doc_path=args.governance_doc,
        output_dir=args.out,
    )
    print("VERDICT=SCOPE_DEFINED_NOT_EXECUTED")
    print(f"SCOPE_ID={result['scope_id']}")
    print(f"DURABLE_EVIDENCE_BUNDLE={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(f"NEXT_STEP={result['next_step']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
