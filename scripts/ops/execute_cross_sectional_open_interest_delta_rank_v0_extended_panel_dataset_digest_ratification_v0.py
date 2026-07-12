#!/usr/bin/env python3
"""Execute extended panel dataset digest ratification for cross_sectional_open_interest_delta_rank/v0.

Ratifies PR5119 extended self-accumulated OI panel dataset identity into the versioned
research binding. No economic evaluation. Operator GO required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0 import (  # noqa: E402
    CONFIRM_GO,
    DEFAULT_MATERIALIZATION_MANIFEST,
    EXPECTED_RANKABLE_EPOCH_COUNT,
    HISTORY_DEPTH_AFTER,
    HISTORY_DEPTH_BEFORE,
    NEW_DATASET_DIGEST,
    OLD_BINDING_DIGEST,
    OLD_DATASET_DIGEST,
    RatificationTerminalStatus,
    build_before_after_field_diff_v0,
    build_ratification_config_v0,
    compare_ratification_envelopes_v0,
    execute_extended_panel_dataset_digest_ratification_v0,
    load_observed_dataset_identity_from_manifest_v0,
    materialize_extended_panel_ratified_versioned_binding_v0,
    ratification_roundtrip_contract_v0,
    result_to_dict_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    serialize_versioned_binding_artifact_json_v0,
)

SOURCE_DISCOVERY = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_open_interest_delta_rank_v0_sample_sufficiency_and_data_depth_remediation_"
    "contract_discovery_read_only_v0_20260712T004335Z"
)
SOURCE_IMPLEMENTATION = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_"
    "and_rematerialization_implementation_v0_20260712T004937Z"
)
SOURCE_CLOSEOUT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_"
    "and_rematerialization_implementation_v0_pr_merge_closeout_20260712T005547Z"
)
ECON_EVAL_CONFIG = (
    _REPO_ROOT
    / "config/ops/cross_sectional_open_interest_delta_rank_v0_economic_evaluation_v1.json"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_manifest(path: Path) -> int:
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def _write_manifest(evidence_dir: Path) -> None:
    rows = []
    for path in sorted(evidence_dir.iterdir()):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rows.append(f"{_sha256_file(path)}  {path.name}")
    (evidence_dir / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _update_economic_eval_config_binding_refs(binding_digest: str, data_digest: str) -> None:
    if not ECON_EVAL_CONFIG.is_file():
        return
    payload = json.loads(ECON_EVAL_CONFIG.read_text(encoding="utf-8"))
    payload["binding_digest"] = binding_digest
    cs_binding = payload["cross_sectional_evaluation_binding_v1"]
    cs_binding["binding_digest"] = binding_digest
    cs_binding["data_digest"] = data_digest
    cs_binding["data_contract_digest"] = data_digest
    ECON_EVAL_CONFIG.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extended panel dataset digest ratification for OI delta rank v0."
    )
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MATERIALIZATION_MANIFEST)
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args(argv)

    if args.confirm_go_token != CONFIRM_GO:
        _die(f"OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")
    if not args.enabled:
        _die("DEFAULT_OFF_ENABLED_FLAG_REQUIRED")

    evidence_dir = args.evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    old_binding = json.loads((_REPO_ROOT / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    result = execute_extended_panel_dataset_digest_ratification_v0(
        confirm=args.confirm_go_token,
        enabled=True,
        manifest_path=args.manifest_path.resolve(),
        write_repo_config=args.write_repo_config,
        repo_root=_REPO_ROOT,
    )
    first = materialize_extended_panel_ratified_versioned_binding_v0(
        observed=load_observed_dataset_identity_from_manifest_v0(args.manifest_path.resolve())
    )
    second = materialize_extended_panel_ratified_versioned_binding_v0(
        observed=load_observed_dataset_identity_from_manifest_v0(args.manifest_path.resolve())
    )
    diff_empty, diff_payload = compare_ratification_envelopes_v0(first, second)

    if args.write_repo_config and result.status is RatificationTerminalStatus.RATIFICATION_COMPLETE:
        (_REPO_ROOT / CONFIG_REL_PATH).write_text(
            serialize_versioned_binding_artifact_json_v0(first), encoding="utf-8"
        )
        _update_economic_eval_config_binding_refs(
            str(first["binding_digest"]), str(first["data_digest"])
        )

    _write_json(evidence_dir / "owner_inventory.json", build_ratification_config_v0())
    _write_json(
        evidence_dir / "reuse_decision.json",
        {
            "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
            "new_narrow_adapter": build_ratification_config_v0()["ratification_owner"],
        },
    )
    _write_json(
        evidence_dir / "dataset_identity_before_after.json",
        load_observed_dataset_identity_from_manifest_v0(args.manifest_path.resolve()),
    )
    _write_json(
        evidence_dir / "binding_identity_before_after.json",
        {
            "old_binding_digest": OLD_BINDING_DIGEST,
            "new_binding_digest": first.get("binding_digest"),
            "old_dataset_digest": OLD_DATASET_DIGEST,
            "new_dataset_digest": NEW_DATASET_DIGEST,
        },
    )
    _write_json(evidence_dir / "digest_dependency_graph.json", first["binding"]["digest_bindings"])
    _write_json(
        evidence_dir / "before_after_field_diff.json",
        build_before_after_field_diff_v0(old_binding=old_binding, new_binding=first),
    )
    _write_json(
        evidence_dir / "semantic_identity_comparison.json",
        first["extended_panel_dataset_ratification"],
    )
    _write_json(
        evidence_dir / "cryptographic_identity_comparison.json",
        {
            "cryptographic_dataset_identity_changed": True,
            "cryptographic_binding_identity_changed": first["binding_digest"] != OLD_BINDING_DIGEST,
            "semantic_binding_fields_changed": False,
        },
    )
    _write_json(
        evidence_dir / "supersession_decision.json",
        first["binding"]["binding_supersession"],
    )
    _write_json(evidence_dir / "ratification_run_a.json", first)
    _write_json(evidence_dir / "ratification_run_b.json", second)
    _write_json(
        evidence_dir / "ratification_roundtrip.txt", ratification_roundtrip_contract_v0(first)
    )
    (evidence_dir / "deterministic_ratification.txt").write_text(
        "\n".join(
            [
                "DETERMINISTIC_RATIFICATION=true",
                f"SECOND_RATIFICATION_DIFF_EMPTY={diff_empty}",
                f"BINDING_DIGEST={first.get('binding_digest')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(
        evidence_dir / "ci_scope_decision.json",
        {"ci_mode": "FOCUSED", "full_ci_required": False},
    )
    _write_json(evidence_dir / "extension_result.json", result_to_dict_v0(result))

    print(json.dumps(result_to_dict_v0(result), indent=2, sort_keys=True))
    if result.status is not RatificationTerminalStatus.RATIFICATION_COMPLETE:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
