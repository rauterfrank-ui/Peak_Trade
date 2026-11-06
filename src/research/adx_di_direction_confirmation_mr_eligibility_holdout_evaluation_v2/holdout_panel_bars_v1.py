"""Load the sealed FINAL_AUDIT holdout panel for ADX DI direction-confirmation MR eligibility v1.

This module is HOLDOUT-AUTHORIZED: unlike the development-side panel loaders
it deliberately does NOT call ``reject_holdout_dataset_or_path`` (that helper
exists to keep the sealed holdout out of *development* evaluation code; it
would incorrectly block the one preregistered holdout run if reused here).
Access is still fail-closed on dataset identity: the sealed manifest sha256,
its declared ``content_hash``, ``dataset_id``, common panel bounds, and
included-instrument count must exactly match the values recorded in
``config/research/adx_di_direction_confirmation_mr_eligibility_holdout_preregistered_measurement_contract_v2.json``.

Reads the already-normalized MV2 research bars (parquet, one file per
included instrument) sealed under the ``longer_chronological_pit/chrono_3y_v1``
archive layout. Bitcoin instruments are rejected fail-closed if ever present.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1"
EXPECTED_CONTENT_HASH = "7bcda794ae2a355c6f36b2ea04703f39078063458f52034add44bec5644206bb"
EXPECTED_MANIFEST_SHA256 = "f4c616c556ff3f2500bb5deff2070c5ee9c4b6a5d5d6ca5da3dc7aca1e8a3e56"
PERIOD_START = "2023-08-16T05:55:00Z"
PERIOD_END_EXCLUSIVE = "2024-09-01T00:00:00Z"
INSTRUMENT_COUNT = 65
SEALED_ARCHIVE_SUBDIR = "sealed_lifecycle_long_panel_v1_d884a000_20260720T1832Z"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_holdout_archive_root(explicit: str | Path | None = None) -> Path:
    """Resolve the sealed FINAL_AUDIT holdout panel archive root.

    Returns the ``sealed_lifecycle_long_panel_v1_...`` directory that is the
    parent of ``longer_chronological_pit``.
    """
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
    """Fail-closed identity check of the sealed holdout manifest.

    Returns opaque registry-derived proof fields only (dataset_id, hashes,
    archive_root) — no economic content is read here.
    """
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
    """Exactly ``INSTRUMENT_COUNT`` INCLUDE_LONG_PANEL members; Bitcoin rejected fail-closed."""
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
    """Load one member's sealed normalized MV2 research bars, sliced to ``[start, end)``."""
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
