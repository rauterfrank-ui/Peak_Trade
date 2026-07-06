#!/usr/bin/env python3
"""Materialize post-PR4921 versioned research bindings (no eval) v0.

Offline-only binding materialization. No economic evaluation, no backtest,
no walk-forward, Monte Carlo, stress, or runtime authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)

CONFIRM_GO = "GO_MATERIALIZE_POST_PR4921_VERSIONED_RESEARCH_BINDINGS_NO_EVAL_V0"
SCOPE_ID = "POST_PR4921_VERSIONED_RESEARCH_BINDINGS_NO_EVAL_V0"
PROCESS_CLASSIFICATION = "POST_PR4921_VERSIONED_RESEARCH_BINDINGS_MATERIALIZATION_NO_EVAL_V0"
SCOPE_CLASSIFICATION = "BINDING_MATERIALIZATION_ONLY_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
VERDICT = "BINDINGS_MATERIALIZED_NOT_EVALUATED"
NEXT_STEP = "SEPARATE_OPERATOR_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION"
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/post_pr4921_versioned_research_bindings_no_eval_v0.json"
)
DEFAULT_DOC = _REPO_ROOT / "docs/governance/POST_PR4921_VERSIONED_RESEARCH_BINDINGS_NO_EVAL_V0.md"
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4921_versioned_research_bindings_no_eval"
PARENT_CLOSEOUT_SUFFIX = (
    "post_pr4920_new_versioned_research_scope_definition_merge_closeout_20260706T081927Z"
)

REQUIRED_BINDING_FIELDS = (
    "candidate_id",
    "candidate_version",
    "strategy_archetype",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest_source",
    "config_digest_source",
    "data_digest_source",
    "excluded_failed_v1_binding",
    "evaluation_authorized",
    "retry_authorized",
    "promotion_admissible",
    "runtime_rewire_admissible",
)

REQUIRED_CONTRACT_FLAGS = (
    ("binding_materialization_only", True),
    ("economic_evaluation_authorized", False),
    ("backtest_execution_authorized", False),
    ("walk_forward_execution_authorized", False),
    ("monte_carlo_execution_authorized", False),
    ("stress_execution_authorized", False),
    ("retry_authorized", False),
    ("parameter_optimization_authorized", False),
    ("threshold_lowering_authorized", False),
    ("promotion_admissible", False),
    ("runtime_rewire_admissible", False),
    ("orders_allowed", False),
    ("live_authorized", False),
    ("failed_v1_bindings_excluded", True),
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "branch": _run(["branch", "--show-current"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if config.get("scope_id") != SCOPE_ID:
        errors.append("unexpected scope_id")
    if config.get("go_token") != CONFIRM_GO:
        errors.append("unexpected go_token")
    if config.get("next_step") != NEXT_STEP:
        errors.append("unexpected next_step")
    if config.get("verdict") != VERDICT:
        errors.append("unexpected verdict")

    for field, expected in REQUIRED_CONTRACT_FLAGS:
        if config.get(field) is not expected:
            errors.append(f"contract flag mismatch: {field} expected {expected}")

    bindings = config.get("versioned_bindings", [])
    if not isinstance(bindings, list) or len(bindings) != 3:
        errors.append("versioned_bindings must contain exactly 3 entries")

    for binding in bindings:
        for key in REQUIRED_BINDING_FIELDS:
            if key not in binding:
                errors.append(f"missing binding field {key} in {binding.get('candidate_id')}")
        if binding.get("evaluation_authorized") is not False:
            errors.append(f"evaluation_authorized must be false for {binding.get('candidate_id')}")

    excluded = {b.get("excluded_failed_v1_binding") for b in bindings}
    required_excluded = {"trend_following/v1", "bollinger_bands/v1", "momentum_1h/v1"}
    if excluded != required_excluded:
        errors.append("excluded_failed_v1_binding set mismatch")

    return errors


def _verify_source_manifest(source_dir: Path) -> tuple[int, str]:
    if not source_dir.is_dir():
        return -1, "missing"
    ok, msg = verify_manifest_sha256(source_dir)
    return (0 if ok else 1), msg or "ok"


def _build_authority_boundary(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "backtest_execution_authorized": False,
        "binding_materialization_only": True,
        "economic_evaluation_authorized": False,
        "failed_v1_bindings_excluded": True,
        "live_authorized": False,
        "monte_carlo_execution_authorized": False,
        "next_step": NEXT_STEP,
        "orders_allowed": False,
        "parameter_optimization_authorized": False,
        "promotion_admissible": False,
        "retry_authorized": False,
        "runtime_authority": "NONE",
        "runtime_rewire_admissible": False,
        "scheduler_runtime_allowed": False,
        "shadow_authorized": False,
        "stress_execution_authorized": False,
        "testnet_authorized": False,
        "threshold_lowering_authorized": False,
        "walk_forward_execution_authorized": False,
    }


def _build_source_evidence_index(
    config: dict[str, Any],
    *,
    parent_closeout_dir: Path,
    parent_closeout_rc: int,
    output_dir: Path,
) -> dict[str, Any]:
    return {
        "git_snapshot": _git_snapshot(),
        "parent_closeout_dir": str(parent_closeout_dir),
        "parent_closeout_manifest_verify_rc": parent_closeout_rc,
        "parent_scope_config": str(_REPO_ROOT / config["parent_scope_config"]),
        "parent_scope_doc": str(_REPO_ROOT / config["parent_scope_doc"]),
        "repo_binding_config": str(DEFAULT_CONFIG),
        "repo_binding_doc": str(DEFAULT_DOC),
        "source_evidence_refs": config.get("source_evidence_refs", []),
        "versioned_binding_count": len(config.get("versioned_bindings", [])),
        "durable_bundle_dir": str(output_dir),
    }


def run_post_pr4921_versioned_research_bindings_no_eval_v0(
    *,
    config_path: Path = DEFAULT_CONFIG,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        _die("ERR:config validation failed", code=1)

    parent_closeout_dir = Path(config["parent_closeout_dir"])
    parent_closeout_rc, parent_closeout_msg = _verify_source_manifest(parent_closeout_dir)
    required_rc = int(config.get("parent_closeout_manifest_verify_rc", 0))
    if parent_closeout_rc >= 0 and parent_closeout_rc != required_rc:
        _die(f"ERR:parent closeout manifest verify rc mismatch: {parent_closeout_dir}")

    if output_dir is None:
        output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        _die(f"ERR:output dir not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    versioned_bindings = {
        "binding_count": len(config["versioned_bindings"]),
        "excluded_failed_v1_bindings": config["excluded_failed_v1_bindings"],
        "shared_model_bindings": config["shared_model_bindings"],
        "versioned_bindings": config["versioned_bindings"],
    }
    authority_boundary = _build_authority_boundary(config)
    source_index = _build_source_evidence_index(
        config,
        parent_closeout_dir=parent_closeout_dir,
        parent_closeout_rc=parent_closeout_rc,
        output_dir=output_dir,
    )

    binding_summary_lines = [
        "# Binding Summary",
        "",
        f"- scope_id: `{SCOPE_ID}`",
        f"- verdict: `{VERDICT}`",
        f"- process_classification: `{PROCESS_CLASSIFICATION}`",
        f"- binding_materialization_only: `true`",
        f"- failed_v1_bindings_excluded: `true`",
        f"- next_step: `{NEXT_STEP}`",
        "",
        "## Versioned Bindings",
        "",
    ]
    for binding in config["versioned_bindings"]:
        binding_summary_lines.extend(
            [
                f"### `{binding['candidate_id']}` / `{binding['candidate_version']}`",
                "",
                f"- strategy_archetype: `{binding['strategy_archetype']}`",
                f"- replaces_failed_binding: `{binding['replaces_failed_binding']}`",
                f"- excluded_failed_v1_binding: `{binding['excluded_failed_v1_binding']}`",
                f"- binding_status: `{binding['binding_status']}`",
                f"- evaluation_authorized: `{binding['evaluation_authorized']}`",
                "",
            ]
        )
    (output_dir / "BINDING_SUMMARY.md").write_text(
        "\n".join(binding_summary_lines) + "\n",
        encoding="utf-8",
    )
    (output_dir / "VERSIONED_BINDINGS.json").write_text(
        json.dumps(versioned_bindings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "AUTHORITY_BOUNDARY.json").write_text(
        json.dumps(authority_boundary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "SOURCE_EVIDENCE_INDEX.json").write_text(
        json.dumps(source_index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "parent_closeout_manifest_verify.log").write_text(
        "\n".join(
            [
                f"PARENT_CLOSEOUT_DIR={parent_closeout_dir}",
                f"MANIFEST_VERIFY_RC={parent_closeout_rc}",
                f"MANIFEST_VERIFY_MSG={parent_closeout_msg}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    (output_dir / "MANIFEST.verify.txt").write_text(
        f"MANIFEST_VERIFY_RC={manifest_rc}\nMANIFEST_VERIFY_MSG={msg or 'ok'}\n",
        encoding="utf-8",
    )
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir}")

    return {
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "next_step": NEXT_STEP,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "verdict": VERDICT,
        "versioned_binding_count": len(config["versioned_bindings"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize post-PR4921 versioned research bindings (no eval) v0"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    result = run_post_pr4921_versioned_research_bindings_no_eval_v0(
        config_path=args.config,
        archive_root=args.durable_evidence_root,
        output_dir=args.out,
    )
    print(f"VERDICT={result['verdict']}")
    print(f"SCOPE_ID={result['scope_id']}")
    print(f"DURABLE_BUNDLE_DIR={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(f"NEXT_STEP={result['next_step']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
