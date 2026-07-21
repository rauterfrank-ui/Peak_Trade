"""Byte-identical quarantine → RELEASED_DEVELOPMENT_ONLY panel release v1.

Canonical release of the sealed independent DEVELOPMENT panel from quarantine into
the default archive layout. Does not transform bytes. Does not authorize evaluation.
Does not touch holdout. Does not start runners or claim run slots.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.research.longer_chronological_pit_acquisition_v1.sealed_lifecycle_v1 import (
    load_production_registry_from_json_path,
    verify_sealed_manifest,
)
from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
    parse_registry_snapshot_dict_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    attach_snapshot_digest,
)

PACKAGE_MARKER = "INDEPENDENT_DEV_PANEL_QUARANTINE_RELEASE_V1=true"
SCHEMA_VERSION = "independent_dev_panel_quarantine_release_contract.v1"
CONTRACT_REL_PATH = "config/research/independent_dev_panel_quarantine_release_contract_v1.json"
EVIDENCE_REL_PATH = "docs/evidence/release_independent_dev_panel_quarantine_byte_identical_v1/"
GOVERNANCE_REL_PATH = "docs/governance/INDEPENDENT_DEV_PANEL_QUARANTINE_RELEASE_V1.md"
CLI_REL_PATH = "scripts/research/run_release_independent_dev_panel_quarantine_v1.py"

DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
DATASET_INSTANCE = "dev_pre_holdout_panel_v1_20260720T2052Z"
DATASET_ROLE = "DEVELOPMENT_ONLY"
DEV_PANEL_SUBDIR = DATASET_INSTANCE
QUARANTINE_REL = f"quarantine/{DEV_PANEL_SUBDIR}"
SOURCE_STATUS = "QUARANTINE_BYTE_IDENTICAL_RESTORE"
RELEASED_STATUS = "RELEASED_DEVELOPMENT_ONLY"

EXPECTED_MANIFEST_SHA256 = "be953c559ac3dd797961bdda8cbc190076353c91d3299b9031ae1ee767d4b594"
EXPECTED_CONTENT_HASH = "4a1978fe0e69a6cd7b19b32f5f95882cfdc3e36397aaec87bce2c4139ab1cfca"
EXPECTED_UNIVERSE_DIGEST = "ddcdec738ff5661f3e2f6bd3dcc97a1bcddbf0b9254faa344b318558f1dbe289"
EXPECTED_INSTRUMENT_COUNT = 46
EXPECTED_RAW_FILE_COUNT = 4876
EXPECTED_INTERVAL = "PT1H"
EXPECTED_START = "2022-06-01T03:55:17Z"
EXPECTED_END = "2023-08-16T05:55:00Z"
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"


class PanelQuarantineReleaseError(ValueError):
    """Fail-closed quarantine release error."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_archive_root(explicit: str | Path | None = None) -> Path:
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
    else:
        env = os.environ.get("PEAK_TRADE_DATA_ARCHIVE_ROOT")
        if not env:
            raise PanelQuarantineReleaseError("PEAK_TRADE_DATA_ARCHIVE_ROOT_UNSET")
        root = Path(env).expanduser().resolve()
    if not root.is_dir():
        raise PanelQuarantineReleaseError(f"ARCHIVE_ROOT_MISSING:{root}")
    return root


def quarantine_source_path(archive_root: Path) -> Path:
    return Path(archive_root).resolve() / "quarantine" / DEV_PANEL_SUBDIR


def release_target_path(archive_root: Path) -> Path:
    return Path(archive_root).resolve() / DEV_PANEL_SUBDIR


def sealed_manifest_path(panel_root: Path) -> Path:
    return (
        panel_root
        / "longer_chronological_pit"
        / "chrono_3y_v1"
        / "manifests"
        / "sealed_lifecycle_v1"
        / "sealed_lifecycle_manifest.json"
    )


def assert_not_holdout_path(path: Path | str) -> None:
    text = str(path)
    lowered = text.lower()
    if HOLDOUT_OPAQUE_ID.lower() in lowered:
        raise PanelQuarantineReleaseError(f"HOLDOUT_PATH_REJECTED:{text}")
    if "sealed_long_panel" in lowered and "dev_pre_holdout" not in lowered:
        if "offline_economic_reevaluation" in lowered:
            raise PanelQuarantineReleaseError(f"HOLDOUT_PATH_REJECTED:{text}")


def _assert_no_symlinks(root: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        for name in dirnames + filenames:
            p = base / name
            if p.is_symlink():
                raise PanelQuarantineReleaseError(f"SYMLINK_FORBIDDEN:{p}")


def _count_raw_files(panel_root: Path) -> int:
    raw = panel_root / "longer_chronological_pit" / "chrono_3y_v1" / "raw" / "ohlcv_pt1h"
    if not raw.is_dir():
        raise PanelQuarantineReleaseError(f"RAW_DIR_MISSING:{raw}")
    count = 0
    for _dirpath, _dirnames, filenames in os.walk(raw):
        count += len(filenames)
    return count


def _included_instrument_dirs(panel_root: Path, manifest: Mapping[str, Any]) -> int:
    raw = panel_root / "longer_chronological_pit" / "chrono_3y_v1" / "raw" / "ohlcv_pt1h"
    included = [
        i
        for i in (manifest.get("instruments") or [])
        if str(i.get("inclusion_decision")) == "INCLUDE_LONG_PANEL"
    ]
    if len(included) != EXPECTED_INSTRUMENT_COUNT:
        raise PanelQuarantineReleaseError(
            f"INSTRUMENT_COUNT_MISMATCH:{len(included)}!={EXPECTED_INSTRUMENT_COUNT}"
        )
    for inst in included:
        native = str(inst.get("native_instrument_id") or "")
        if not native or not (raw / native).is_dir():
            raise PanelQuarantineReleaseError(f"INSTRUMENT_DIR_MISSING:{native}")
        if "BTC" in str(inst.get("canonical_instrument_id") or "").upper():
            raise PanelQuarantineReleaseError(f"BTC_IN_PANEL:{native}")
    return len(included)


def recompute_universe_digest(manifest: Mapping[str, Any]) -> str:
    reg_path = Path(str(manifest.get("production_registry_path") or ""))
    if not reg_path.is_file():
        raise PanelQuarantineReleaseError(f"PRODUCTION_REGISTRY_MISSING:{reg_path}")
    # Validate via sealed-lifecycle loader (fail-closed parse/validate).
    raw = load_production_registry_from_json_path(reg_path)
    snapshot, errors = parse_registry_snapshot_dict_v1(raw)
    if snapshot is None:
        raise PanelQuarantineReleaseError(f"PRODUCTION_REGISTRY_PARSE_FAILED:{','.join(errors)}")
    attached = attach_snapshot_digest(snapshot)
    digest = str(attached.registry_snapshot_digest)
    if digest != EXPECTED_UNIVERSE_DIGEST:
        raise PanelQuarantineReleaseError(
            f"UNIVERSE_DIGEST_MISMATCH:{digest}!={EXPECTED_UNIVERSE_DIGEST}"
        )
    # Cross-check sealed manifest field.
    if str(manifest.get("production_registry_digest") or "") != digest:
        raise PanelQuarantineReleaseError("MANIFEST_UNIVERSE_DIGEST_FIELD_MISMATCH")
    return digest


def verify_panel_identity(panel_root: Path) -> dict[str, Any]:
    assert_not_holdout_path(panel_root)
    if not panel_root.is_dir():
        raise PanelQuarantineReleaseError(f"PANEL_MISSING:{panel_root}")
    if DEV_PANEL_SUBDIR not in str(panel_root):
        raise PanelQuarantineReleaseError(f"PANEL_NAME_MISMATCH:{panel_root}")
    _assert_no_symlinks(panel_root)
    man_path = sealed_manifest_path(panel_root)
    if not man_path.is_file():
        raise PanelQuarantineReleaseError(f"SEALED_MANIFEST_MISSING:{man_path}")
    manifest_sha = _sha256_file(man_path)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise PanelQuarantineReleaseError(
            f"MANIFEST_SHA_MISMATCH:{manifest_sha}!={EXPECTED_MANIFEST_SHA256}"
        )
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    if str(manifest.get("dataset_id")) != DATASET_ID:
        raise PanelQuarantineReleaseError("DATASET_ID_MISMATCH")
    content = verify_sealed_manifest(manifest)
    if content != EXPECTED_CONTENT_HASH:
        raise PanelQuarantineReleaseError(
            f"CONTENT_HASH_MISMATCH:{content}!={EXPECTED_CONTENT_HASH}"
        )
    universe = recompute_universe_digest(manifest)
    if str(manifest.get("frequency")) != EXPECTED_INTERVAL:
        raise PanelQuarantineReleaseError("INTERVAL_MISMATCH")
    if str(manifest.get("common_panel_start")) != EXPECTED_START:
        raise PanelQuarantineReleaseError("START_MISMATCH")
    if str(manifest.get("common_panel_end")) != EXPECTED_END:
        raise PanelQuarantineReleaseError("END_MISMATCH")
    instruments = _included_instrument_dirs(panel_root, manifest)
    raw_count = _count_raw_files(panel_root)
    if raw_count != EXPECTED_RAW_FILE_COUNT:
        raise PanelQuarantineReleaseError(
            f"RAW_FILE_COUNT_MISMATCH:{raw_count}!={EXPECTED_RAW_FILE_COUNT}"
        )
    return {
        "panel_root": str(panel_root),
        "dataset_id": DATASET_ID,
        "dataset_instance": DATASET_INSTANCE,
        "dataset_role": DATASET_ROLE,
        "manifest_sha256": manifest_sha,
        "content_hash": content,
        "universe_digest": universe,
        "instrument_count": instruments,
        "raw_file_count": raw_count,
        "interval": EXPECTED_INTERVAL,
        "start": EXPECTED_START,
        "end": EXPECTED_END,
        "holdout_boundary_ok": True,
    }


def tree_file_inventory(root: Path) -> dict[str, tuple[int, str]]:
    """Relative path → (size, sha256) for regular files only."""
    out: dict[str, tuple[int, str]] = {}
    root = root.resolve()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            if p.is_symlink():
                raise PanelQuarantineReleaseError(f"SYMLINK_FORBIDDEN:{p}")
            if not p.is_file():
                continue
            rel = str(p.relative_to(root))
            out[rel] = (p.stat().st_size, _sha256_file(p))
    return out


def assert_trees_byte_identical(source: Path, target: Path) -> dict[str, Any]:
    a = tree_file_inventory(source)
    b = tree_file_inventory(target)
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    mismatches = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    if only_a or only_b or mismatches:
        raise PanelQuarantineReleaseError(
            "TREE_NOT_BYTE_IDENTICAL:"
            f"only_source={len(only_a)}:only_target={len(only_b)}:mismatch={len(mismatches)}"
        )
    return {
        "file_count": len(a),
        "only_source": 0,
        "only_target": 0,
        "sha_or_size_mismatch": 0,
    }


def preflight_quarantine_release(
    *,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Read-only release preflight. No copy. No mutation."""
    repo = repo_root or _repo_root()
    root = resolve_archive_root(archive_root)
    source = quarantine_source_path(root)
    target = release_target_path(root)
    assert_not_holdout_path(source)
    assert_not_holdout_path(target)
    source_proof = verify_panel_identity(source)
    target_exists = target.exists()
    target_proof = None
    identical_existing = False
    if target_exists:
        if target.is_symlink():
            raise PanelQuarantineReleaseError(f"TARGET_SYMLINK_FORBIDDEN:{target}")
        target_proof = verify_panel_identity(target)
        tree = assert_trees_byte_identical(source, target)
        identical_existing = True
    else:
        tree = None
    return {
        "schema_version": "independent_dev_panel_quarantine_release_preflight.v1",
        "passed": True,
        "archive_root": str(root),
        "source_path": str(source),
        "target_path": str(target),
        "source_status": SOURCE_STATUS,
        "target_exists": target_exists,
        "identical_existing_target": identical_existing,
        "source_proof": source_proof,
        "target_proof": target_proof,
        "tree_compare": tree,
        "repo_contract_present": (repo / CONTRACT_REL_PATH).is_file(),
        "evaluation_not_started": True,
        "holdout_data_accessed": False,
    }


def release_quarantine_panel(
    *,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
    write_repo_evidence: bool = True,
) -> dict[str, Any]:
    """Atomically release quarantine panel to default DEVELOPMENT path."""
    repo = repo_root or _repo_root()
    preflight = preflight_quarantine_release(archive_root=archive_root, repo_root=repo)
    root = Path(preflight["archive_root"])
    source = Path(preflight["source_path"])
    target = Path(preflight["target_path"])

    if preflight.get("identical_existing_target"):
        evidence = _build_evidence(
            preflight=preflight,
            release_mode="IDEMPOTENT_ALREADY_RELEASED_BYTE_IDENTICAL",
            released=True,
        )
        if write_repo_evidence:
            _write_repo_evidence(repo, evidence)
        return evidence

    staging_parent = root / ".release_staging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f"{DEV_PANEL_SUBDIR}_", dir=str(staging_parent)))
    try:
        # copytree into empty staging dir content: use staging as destination root
        staging_panel = staging / DEV_PANEL_SUBDIR
        shutil.copytree(source, staging_panel, symlinks=False)
        staging_proof = verify_panel_identity(staging_panel)
        tree = assert_trees_byte_identical(source, staging_panel)
        if target.exists():
            raise PanelQuarantineReleaseError("TARGET_APPEARED_DURING_RELEASE")
        os.rename(staging_panel, target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    final_proof = verify_panel_identity(target)
    tree_final = assert_trees_byte_identical(source, target)
    evidence = _build_evidence(
        preflight={
            **preflight,
            "source_proof": staging_proof,
            "target_proof": final_proof,
            "tree_compare": {**tree, **tree_final},
            "target_exists": True,
            "identical_existing_target": True,
        },
        release_mode="BYTE_IDENTICAL_ATOMIC_RENAME_RELEASE",
        released=True,
    )
    # Durable release marker outside git (operator-local).
    marker_dir = root / "operator_local"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = {
        "schema_version": "independent_dev_panel_release_marker.v1",
        "status": RELEASED_STATUS,
        "dataset_id": DATASET_ID,
        "dataset_instance": DATASET_INSTANCE,
        "dataset_role": DATASET_ROLE,
        "source_path": str(source),
        "target_path": str(target),
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "content_hash": EXPECTED_CONTENT_HASH,
        "universe_digest": EXPECTED_UNIVERSE_DIGEST,
        "released_at_utc": _utc_now(),
        "evaluation_authorized": False,
        "holdout_data_accessed": False,
    }
    marker_path = marker_dir / "independent_dev_panel_release_marker_v1.json"
    tmp = marker_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, marker_path)

    if write_repo_evidence:
        _write_repo_evidence(repo, evidence)
    return evidence


def _build_evidence(
    *,
    preflight: Mapping[str, Any],
    release_mode: str,
    released: bool,
) -> dict[str, Any]:
    source_proof = dict(preflight.get("source_proof") or {})
    target_proof = dict(preflight.get("target_proof") or {})
    return {
        "schema_version": "independent_dev_panel_quarantine_release_evidence.v1",
        "artifact_kind": "independent_dev_panel_quarantine_release_evidence",
        "status": RELEASED_STATUS if released else SOURCE_STATUS,
        "release_mode": release_mode,
        "panel_released": released,
        "dataset_id": DATASET_ID,
        "dataset_instance": DATASET_INSTANCE,
        "dataset_role": DATASET_ROLE,
        "source_status": SOURCE_STATUS,
        "source_path": preflight.get("source_path"),
        "target_path": preflight.get("target_path"),
        "archive_root": preflight.get("archive_root"),
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "content_hash": EXPECTED_CONTENT_HASH,
        "universe_digest": EXPECTED_UNIVERSE_DIGEST,
        "instrument_count": EXPECTED_INSTRUMENT_COUNT,
        "raw_file_count": EXPECTED_RAW_FILE_COUNT,
        "interval": EXPECTED_INTERVAL,
        "start": EXPECTED_START,
        "end": EXPECTED_END,
        "source_proof": source_proof,
        "target_proof": target_proof,
        "tree_compare": preflight.get("tree_compare"),
        "dataset_identity_revalidated": True,
        "manifest_digest_match": True,
        "content_digest_recomputed_match": True,
        "universe_digest_recomputed_match": True,
        "instrument_count_match": True,
        "raw_file_count_match": True,
        "interval_match": True,
        "time_range_match": True,
        "holdout_boundary_proven": True,
        "holdout_data_accessed": False,
        "evaluation_authorized": False,
        "evaluation_run_count": 0,
        "runner_started": False,
        "run_slot_consumed": False,
        "live_authorized": False,
        "orders": False,
        "shadow": False,
        "testnet": False,
        "released_at_utc": _utc_now(),
        "contract_ref": CONTRACT_REL_PATH,
        "evidence_ref": EVIDENCE_REL_PATH,
    }


def _write_repo_evidence(repo: Path, evidence: Mapping[str, Any]) -> None:
    out = repo / EVIDENCE_REL_PATH
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        "\n".join(
            [
                "---",
                "docs_token: DOCS_TOKEN_INDEPENDENT_DEV_PANEL_QUARANTINE_RELEASE_V1",
                "STATUS: RELEASED_DEVELOPMENT_ONLY",
                "LIVE_AUTHORIZED: false",
                "ORDERS_ALLOWED: false",
                "---",
                "",
                "# Independent DEVELOPMENT panel quarantine release v1",
                "",
                "Byte-identical release from quarantine to default archive layout.",
                "Does not authorize evaluation. Does not access holdout.",
                "",
                f"- Dataset: `{DATASET_ID}`",
                f"- Instance: `{DATASET_INSTANCE}`",
                f"- Role: `{DATASET_ROLE}`",
                f"- Status: `{RELEASED_STATUS}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def is_panel_released(*, archive_root: Path | None = None) -> bool:
    root = resolve_archive_root(archive_root)
    target = release_target_path(root)
    if not target.is_dir():
        return False
    try:
        verify_panel_identity(target)
    except PanelQuarantineReleaseError:
        return False
    marker = root / "operator_local" / "independent_dev_panel_release_marker_v1.json"
    if marker.is_file():
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if payload.get("status") != RELEASED_STATUS:
            return False
        if payload.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
            return False
    return True


def load_contract(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    path = repo / CONTRACT_REL_PATH
    if not path.is_file():
        raise PanelQuarantineReleaseError("RELEASE_CONTRACT_MISSING")
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "CONTRACT_REL_PATH",
    "DATASET_ID",
    "DATASET_INSTANCE",
    "DATASET_ROLE",
    "DEV_PANEL_SUBDIR",
    "EVIDENCE_REL_PATH",
    "EXPECTED_CONTENT_HASH",
    "EXPECTED_INSTRUMENT_COUNT",
    "EXPECTED_MANIFEST_SHA256",
    "EXPECTED_RAW_FILE_COUNT",
    "EXPECTED_UNIVERSE_DIGEST",
    "PACKAGE_MARKER",
    "PanelQuarantineReleaseError",
    "QUARANTINE_REL",
    "RELEASED_STATUS",
    "SOURCE_STATUS",
    "assert_trees_byte_identical",
    "is_panel_released",
    "load_contract",
    "preflight_quarantine_release",
    "quarantine_source_path",
    "release_quarantine_panel",
    "release_target_path",
    "resolve_archive_root",
    "verify_panel_identity",
]
