"""Load the sealed FINAL_AUDIT holdout panel for Exit V8 holdout evaluation v1.

HOLDOUT-AUTHORIZED loader: does not call development-side holdout rejection.
Access remains fail-closed on dataset identity hashes recorded in the
holdout preregistration contract. Importing this module does not open the panel.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.constants_v1 import (
    DATASET_ID,
    EXPECTED_CONTENT_HASH,
    EXPECTED_MANIFEST_SHA256,
    INSTRUMENT_COUNT,
    PERIOD_END_EXCLUSIVE,
    PERIOD_START,
    SEALED_ARCHIVE_SUBDIR,
)

REQUIRED_DATASET_ID = DATASET_ID


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_holdout_archive_root(explicit: str | Path | None = None) -> Path:
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
    else:
        root = Path(
            "/var/folders/j7/823by_lx7jl026wrk5jpnkmh0000gn/T/peak_trade_data_archive/"
            f"{SEALED_ARCHIVE_SUBDIR}"
        ).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"HOLDOUT_ARCHIVE_MISSING:{root}")
    if SEALED_ARCHIVE_SUBDIR not in str(root):
        raise ValueError(f"HOLDOUT_ARCHIVE_NAME_MISMATCH:{root}")
    return root


def chrono_base(archive_root: Path) -> Path:
    return archive_root / "longer_chronological_pit" / "chrono_3y_v1"


def sealed_manifest_path(archive_root: Path) -> Path:
    return (
        chrono_base(archive_root)
        / "manifests"
        / "sealed_lifecycle_v1"
        / "sealed_lifecycle_manifest.json"
    )


def bars_root(archive_root: Path) -> Path:
    return chrono_base(archive_root) / "normalized" / "mv2_research_bars_v1"


def verify_holdout_panel_hashes(archive_root: Path) -> dict[str, Any]:
    man = sealed_manifest_path(archive_root)
    if not man.is_file():
        raise FileNotFoundError(f"SEALED_MANIFEST_MISSING:{man}")
    digest = _sha256_file(man)
    if digest != EXPECTED_MANIFEST_SHA256:
        raise ValueError(f"MANIFEST_HASH_MISMATCH:{digest}")
    payload = json.loads(man.read_text(encoding="utf-8"))
    if payload.get("dataset_id") != REQUIRED_DATASET_ID:
        raise ValueError("DATASET_ID_MISMATCH")
    content_hash = str(payload.get("content_hash") or "")
    if content_hash != EXPECTED_CONTENT_HASH:
        raise ValueError(f"CONTENT_HASH_MISMATCH:{content_hash}")
    if payload.get("common_panel_start") != PERIOD_START:
        raise ValueError("PANEL_START_MISMATCH")
    if payload.get("common_panel_end") != PERIOD_END_EXCLUSIVE:
        raise ValueError("PANEL_END_MISMATCH")
    if int(payload.get("instrument_count_long_panel_included") or 0) != INSTRUMENT_COUNT:
        raise ValueError("INSTRUMENT_COUNT_MISMATCH")
    if payload.get("btc_excluded") is not True:
        raise ValueError("BTC_MUST_BE_EXCLUDED")
    if payload.get("sealed") is not True:
        raise ValueError("MANIFEST_MUST_BE_SEALED")
    return {
        "dataset_id": REQUIRED_DATASET_ID,
        "manifest_sha256": digest,
        "content_hash": content_hash,
        "archive_root": str(archive_root),
    }


def included_panel_members(archive_root: Path) -> list[dict[str, str]]:
    payload = json.loads(sealed_manifest_path(archive_root).read_text(encoding="utf-8"))
    out: list[dict[str, str]] = []
    for inst in payload.get("instruments") or []:
        if str(inst.get("inclusion_decision")) != "INCLUDE_LONG_PANEL":
            continue
        canon = str(inst.get("canonical_instrument_id") or "")
        native = str(inst.get("native_instrument_id") or "")
        if not canon or not native:
            continue
        if "BTC" in canon.upper():
            raise ValueError(f"BTC_IN_HOLDOUT_PANEL:{canon}")
        out.append({"canonical_instrument_id": canon, "native_instrument_id": native})
    out = sorted(out, key=lambda x: x["canonical_instrument_id"])
    if len(out) != INSTRUMENT_COUNT:
        raise ValueError(f"EXPECTED_{INSTRUMENT_COUNT}_INCLUDED_GOT_{len(out)}")
    return out


def _canonical_id_to_dir_name(canonical_instrument_id: str) -> str:
    return canonical_instrument_id.replace(":", "_")


def load_member_bars(
    archive_root: Path,
    *,
    canonical_instrument_id: str,
    start_inclusive: str,
    end_exclusive: str,
) -> pd.DataFrame:
    if "BTC" in canonical_instrument_id.upper():
        raise ValueError(f"BTC_MEMBER_REJECTED:{canonical_instrument_id}")
    dir_name = _canonical_id_to_dir_name(canonical_instrument_id)
    parquet_path = bars_root(archive_root) / dir_name / "bars.parquet"
    if not parquet_path.is_file():
        raise FileNotFoundError(f"MEMBER_BARS_PARQUET_MISSING:{parquet_path}")
    bars = pd.read_parquet(parquet_path)
    if bars.index.name != "timestamp":
        if "timestamp" in bars.columns:
            bars = bars.set_index("timestamp")
        else:
            raise ValueError(f"BARS_MISSING_TIMESTAMP_INDEX:{canonical_instrument_id}")
    bars.index = pd.to_datetime(bars.index, utc=True)
    bars.index.name = "timestamp"
    bars = bars.sort_index()
    if bars.index.has_duplicates:
        bars = bars[~bars.index.duplicated(keep="last")]
    start = pd.Timestamp(start_inclusive)
    end = pd.Timestamp(end_exclusive)
    mask = (bars.index >= start) & (bars.index < end)
    out = bars.loc[mask]
    if out.empty:
        raise ValueError(f"EMPTY_BARS:{canonical_instrument_id}:{start_inclusive}..{end_exclusive}")
    return out


__all__ = [
    "EXPECTED_CONTENT_HASH",
    "EXPECTED_MANIFEST_SHA256",
    "INSTRUMENT_COUNT",
    "PERIOD_END_EXCLUSIVE",
    "PERIOD_START",
    "REQUIRED_DATASET_ID",
    "SEALED_ARCHIVE_SUBDIR",
    "bars_root",
    "chrono_base",
    "included_panel_members",
    "load_member_bars",
    "resolve_holdout_archive_root",
    "sealed_manifest_path",
    "verify_holdout_panel_hashes",
]
