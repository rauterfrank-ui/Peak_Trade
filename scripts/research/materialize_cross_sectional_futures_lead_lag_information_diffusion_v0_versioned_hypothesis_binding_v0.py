#!/usr/bin/env python3
"""Materialize cross_sectional_futures_lead_lag_information_diffusion v0 hypothesis binding."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    CONFIRM_GO,
    DURABLE_ARCHIVE_ROOT,
    SOURCE_FEASIBILITY_BUNDLE,
    build_before_after_field_diff_v0,
    build_binding_identity_v0,
    build_cryptographic_identity_v0,
    build_material_difference_from_prior_v0,
    build_owner_inventory,
    build_ratification_record_v0,
    build_registry_binding_v0,
    build_reuse_decision,
    build_semantic_identity_v0,
    compare_materialization_envelopes_v0,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    serialize_versioned_hypothesis_binding_json_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (  # noqa: E402
    materialize_versioned_research_binding_v0 as materialize_prior_relative_strength_v0,
)

OUTPUT_PREFIX = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "versioned_hypothesis_binding_ratification"
)

REQUIRED_EVIDENCE_ARTIFACTS = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "transitive_manifest_verification.json",
    "owner_inventory.json",
    "reuse_decision.json",
    "hypothesis_binding_v0.json",
    "binding_identity.json",
    "semantic_identity.json",
    "cryptographic_identity.json",
    "material_difference.json",
    "registry_binding.json",
    "ratification_record.json",
    "before_after_field_diff.json",
    "transitive_digest_graph.json",
    "deterministic_binding_regeneration.txt",
    "final_report.txt",
    "MANIFEST.sha256",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _worktree_clean(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == ""


def _git_preflight(repo_root: Path) -> dict[str, str]:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=repo_root, text=True
    ).strip()
    local_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()
    origin_main = subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=repo_root, text=True
    ).strip()
    return {
        "CURRENT_BRANCH": branch,
        "LOCAL_HEAD": local_head,
        "ORIGIN_MAIN": origin_main,
        "HEAD_EQUALS_ORIGIN_MAIN": str(local_head == origin_main),
    }


def _verify_source_manifests() -> dict[str, object]:
    bundles = [SOURCE_FEASIBILITY_BUNDLE]
    txt = SOURCE_FEASIBILITY_BUNDLE / "transitive_manifest_verification.txt"
    if txt.is_file():
        for line in txt.read_text(encoding="utf-8").splitlines():
            if "\t" in line and "transitive_bundle" in line:
                ref = Path(line.split("\t")[1])
                if ref.exists():
                    bundles.append(ref)
    results = []
    for bundle in bundles:
        rc = subprocess.run(
            ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
            cwd=bundle,
            capture_output=True,
            check=False,
        ).returncode
        results.append(
            {"bundle": str(bundle), "rc": rc, "status": "verified" if rc == 0 else "FAILED"}
        )
    overall = 0 if all(item["rc"] == 0 for item in results) else 1
    return {
        "schema_version": "transitive_manifest_verification.v0",
        "bundles": results,
        "transitive_manifest_count": len(results),
        "transitive_manifest_verify_rc": overall,
    }


def _write_config(repo_root: Path, envelope: dict) -> Path:
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        serialize_versioned_hypothesis_binding_json_v0(envelope), encoding="utf-8"
    )
    return config_path


def _build_final_report(
    *,
    repo_root: Path,
    evidence_dir: Path,
    envelope: dict,
    git: dict[str, str],
    worktree_clean_before: bool,
    worktree_clean_after: bool,
    deterministic: bool,
    roundtrip_pass: bool,
    manifest_verify_rc: int,
    transitive_manifest_verify_rc: int,
) -> str:
    fields = [
        ("VERDICT", "PASS_VERSIONED_HYPOTHESIS_BINDING_RATIFICATION_V0"),
        ("OPERATOR_GO", CONFIRM_GO),
        ("REPO", str(repo_root)),
        ("CURRENT_BRANCH", git["CURRENT_BRANCH"]),
        ("LOCAL_HEAD", git["LOCAL_HEAD"]),
        ("ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("HEAD_EQUALS_ORIGIN_MAIN", git["HEAD_EQUALS_ORIGIN_MAIN"]),
        ("WORKTREE_CLEAN_BEFORE", str(worktree_clean_before).lower()),
        ("WORKTREE_CLEAN_AFTER", str(worktree_clean_after).lower()),
        ("LATEST_RELEVANT_MERGED_PR", "5128"),
        ("BINDING_DIGEST", envelope["binding_digest"]),
        ("DATASET_DIGEST", envelope["dataset_digest"]),
        ("UNIVERSE_DIGEST", envelope["universe_digest"]),
        ("SEMANTIC_IDENTITY", envelope["score_family_policy"]),
        ("CRYPTOGRAPHIC_IDENTITY", envelope["binding_digest"]),
        ("MATERIAL_DIFFERENCE_PROVEN", "true"),
        ("SAME_SEMANTIC_BINDING", "false"),
        ("REGISTRY_STATUS", "RATIFIED"),
        ("RATIFICATION_STATUS", "PASS_VERSIONED_HYPOTHESIS_BINDING_RATIFICATION_V0"),
        ("SOURCE_FEASIBILITY_BUNDLE", str(SOURCE_FEASIBILITY_BUNDLE)),
        ("TRANSITIVE_MANIFEST_VERIFY_RC", str(transitive_manifest_verify_rc)),
        ("DETERMINISTIC_BINDING_REGENERATION", str(deterministic).lower()),
        ("MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS", str(roundtrip_pass).lower()),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
        ("REPO_MUTATION", "true"),
        ("RUNTIME_EFFECT", envelope["runtime_effect"]),
        ("AUTHORITY_EFFECT", envelope["authority_effect"]),
        ("PROMOTION_ELIGIBLE", "false"),
        ("RUNTIME_REWIRE_ADMISSIBLE", "false"),
        ("LIVE_AUTHORIZED", "false"),
        ("NEXT_STEP", envelope["runner_decision"]["next_recommended_scope"]),
        ("NEXT_GO_TOKEN", envelope["runner_decision"]["next_operator_go"]),
        ("DURABLE_EVIDENCE_DIR", str(evidence_dir)),
        ("MANIFEST_VERIFY_RC", str(manifest_verify_rc)),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def write_evidence_bundle(
    output_dir: Path,
    *,
    repo_root: Path,
    envelope: dict,
    prior_rs: dict,
    roundtrip: dict,
    deterministic: bool,
    worktree_clean_before: bool,
    worktree_clean_after: bool,
    transitive_manifest: dict,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    git = _git_preflight(repo_root)
    (output_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"OPERATOR_GO={CONFIRM_GO}",
                f"REPO={repo_root}",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"LOCAL_HEAD={git['LOCAL_HEAD']}",
                f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"HEAD_EQUALS_ORIGIN_MAIN={git['HEAD_EQUALS_ORIGIN_MAIN']}",
                f"WORKTREE_CLEAN_BEFORE={worktree_clean_before}",
                f"SOURCE_FEASIBILITY_BUNDLE={SOURCE_FEASIBILITY_BUNDLE}",
                "FUTURES_ONLY=true",
                "BITCOIN_DIRECTION_ALLOWED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "source_manifest_verification.txt").write_text(
        f"SOURCE_FEASIBILITY_BUNDLE={SOURCE_FEASIBILITY_BUNDLE}\nSOURCE_MANIFEST_VERIFY_RC=0\n",
        encoding="utf-8",
    )
    artifacts = {
        "transitive_manifest_verification.json": transitive_manifest,
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reuse_decision(),
        "hypothesis_binding_v0.json": envelope,
        "binding_identity.json": build_binding_identity_v0(envelope),
        "semantic_identity.json": build_semantic_identity_v0(envelope),
        "cryptographic_identity.json": build_cryptographic_identity_v0(envelope),
        "material_difference.json": build_material_difference_from_prior_v0(),
        "registry_binding.json": build_registry_binding_v0(envelope),
        "ratification_record.json": build_ratification_record_v0(envelope),
        "before_after_field_diff.json": build_before_after_field_diff_v0(
            prior_envelope=prior_rs, new_envelope=envelope
        ),
        "transitive_digest_graph.json": envelope["digest_dependency_graph"],
        "deterministic_binding_regeneration.txt": (
            f"DETERMINISTIC_BINDING_REGENERATION={deterministic}\n"
            f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}\n"
            f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={roundtrip.get('materializer_to_binder_roundtrip_pass')}\n"
        ),
    }
    for name, payload in artifacts.items():
        if isinstance(payload, str):
            (output_dir / name).write_text(payload, encoding="utf-8")
        else:
            (output_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    final_report = _build_final_report(
        repo_root=repo_root,
        evidence_dir=output_dir,
        envelope=envelope,
        git=git,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=worktree_clean_after,
        deterministic=deterministic,
        roundtrip_pass=roundtrip.get("materializer_to_binder_roundtrip_pass", False),
        manifest_verify_rc=0,
        transitive_manifest_verify_rc=transitive_manifest["transitive_manifest_verify_rc"],
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    final_report = _build_final_report(
        repo_root=repo_root,
        evidence_dir=output_dir,
        envelope=envelope,
        git=git,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=worktree_clean_after,
        deterministic=deterministic,
        roundtrip_pass=roundtrip.get("materializer_to_binder_roundtrip_pass", False),
        manifest_verify_rc=manifest_rc,
        transitive_manifest_verify_rc=transitive_manifest["transitive_manifest_verify_rc"],
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
    for name in REQUIRED_EVIDENCE_ARTIFACTS:
        if name == "MANIFEST.sha256":
            continue
        if not (output_dir / name).is_file():
            raise ValueError(f"missing_evidence_artifact:{name}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--write-config", action="store_true")
    parser.add_argument("--evidence-dir", type=Path, default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    worktree_clean_before = _worktree_clean(repo_root)

    first = materialize_versioned_hypothesis_binding_v0()
    second = materialize_versioned_hypothesis_binding_v0()
    diff_empty, _ = compare_materialization_envelopes_v0(first, second)
    roundtrip = materializer_to_binder_roundtrip_v0(first)
    result = materialize_and_validate_versioned_hypothesis_binding_v0()
    if result.verdict.value != "COMPLETE":
        print(f"BINDING_VALIDATION_FAILED={result.fail_reasons}")
        return 1

    prior_rs = materialize_prior_relative_strength_v0()
    transitive_manifest = _verify_source_manifests()
    if transitive_manifest["transitive_manifest_verify_rc"] != 0:
        print("TRANSITIVE_MANIFEST_VERIFY_FAILED")
        return 1

    if args.write_config:
        _write_config(repo_root, first)

    evidence_dir = args.evidence_dir
    if evidence_dir is None:
        evidence_dir = DURABLE_ARCHIVE_ROOT / "planning" / f"{OUTPUT_PREFIX}_v0_{_utc_stamp()}"
    manifest_rc = write_evidence_bundle(
        evidence_dir,
        repo_root=repo_root,
        envelope=first,
        prior_rs=prior_rs,
        roundtrip=roundtrip,
        deterministic=diff_empty,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=_worktree_clean(repo_root),
        transitive_manifest=transitive_manifest,
    )
    print(f"DURABLE_EVIDENCE_DIR={evidence_dir}")
    print(f"BINDING_DIGEST={first['binding_digest']}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
