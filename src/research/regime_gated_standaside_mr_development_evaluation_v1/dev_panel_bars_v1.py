"""Load sealed DEVELOPMENT panel OKX page JSON into MV2 research bars.

Holdout paths are rejected. Only the preregistered DEVELOPMENT dataset may be read.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (
    merge_okx_candle_rows_with_dedup_v1,
)
from src.research.cross_sectional_bounded_panel_fetch_v0 import _candle_is_final
from src.research.regime_gated_standaside_mr_hypothesis_preregistration_v1 import (
    HOLDOUT_OPAQUE_ID,
    HypothesisPreregistrationError,
    reject_holdout_dataset_or_path,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    _materialize_research_panel_volatility_estimate_columns_v0,
)

REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
EXPECTED_MANIFEST_SHA256 = "be953c559ac3dd797961bdda8cbc190076353c91d3299b9031ae1ee767d4b594"
EXPECTED_CONTENT_HASH = "4a1978fe0e69a6cd7b19b32f5f95882cfdc3e36397aaec87bce2c4139ab1cfca"
DEV_PANEL_SUBDIR = "dev_pre_holdout_panel_v1_20260720T2052Z"


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_not_holdout_path(path: Path | str) -> None:
    text = str(path)
    reject_holdout_dataset_or_path(text)
    lowered = text.lower()
    if HOLDOUT_OPAQUE_ID.lower() in lowered:
        raise HypothesisPreregistrationError(f"HOLDOUT_PATH_OR_ID_REJECTED:{text}")
    if "sealed_long_panel" in lowered and "dev_pre_holdout" not in lowered:
        # Fail closed on known sealed holdout archive naming outside development panel.
        if "offline_economic_reevaluation" in lowered:
            raise HypothesisPreregistrationError(f"HOLDOUT_PATH_OR_ID_REJECTED:{text}")


def resolve_development_archive_root(explicit: str | Path | None = None) -> Path:
    """Resolve the sealed independent DEVELOPMENT panel archive root."""
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
    else:
        # Contract evidence path (acquisition sealed this exact archive).
        root = Path(
            "/var/folders/j7/823by_lx7jl026wrk5jpnkmh0000gn/T/peak_trade_data_archive/"
            f"{DEV_PANEL_SUBDIR}"
        ).resolve()
    assert_not_holdout_path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"DEVELOPMENT_ARCHIVE_MISSING:{root}")
    if DEV_PANEL_SUBDIR not in str(root):
        raise ValueError(f"DEVELOPMENT_ARCHIVE_NAME_MISMATCH:{root}")
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


def verify_development_panel_hashes(archive_root: Path) -> dict[str, Any]:
    assert_not_holdout_path(archive_root)
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
            raise ValueError(f"BTC_IN_DEVELOPMENT_PANEL:{canon}")
        out.append({"canonical_instrument_id": canon, "native_instrument_id": native})
    out = sorted(out, key=lambda x: x["canonical_instrument_id"])
    if len(out) != 46:
        raise ValueError(f"EXPECTED_46_INCLUDED_GOT_{len(out)}")
    return out


def load_native_swap_pages_to_mv2_bars(raw_inst_dir: Path) -> pd.DataFrame:
    assert_not_holdout_path(raw_inst_dir)
    rows: list[list[Any]] = []
    pages = sorted(raw_inst_dir.glob("page_*.json"))
    if not pages:
        raise FileNotFoundError(f"NO_OHLCV_PAGES:{raw_inst_dir}")
    for page in pages:
        payload = json.loads(page.read_text(encoding="utf-8"))
        data = payload.get("data") or []
        for row in data:
            if isinstance(row, list) and _candle_is_final(row):
                rows.append(list(row))
    merged, err = merge_okx_candle_rows_with_dedup_v1(rows)
    if err:
        raise ValueError(f"CANDLE_MERGE_ERROR:{err}")
    recs: list[dict[str, Any]] = []
    for r in merged:
        ts = pd.Timestamp(int(r[0]), unit="ms", tz="UTC")
        close = float(r[4])
        recs.append(
            {
                "timestamp": ts,
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": close,
                "volume": float(r[5]),
                "mark_price": close,
                "index_price": close,
                "funding_rate": 0.0,
                "is_final": True,
            }
        )
    bars = pd.DataFrame(recs).set_index("timestamp").sort_index()
    if bars.index.has_duplicates:
        bars = bars[~bars.index.duplicated(keep="last")]
    # PT1H research panel uses the research volatility materializer (not PT1M canonical).
    return _materialize_research_panel_volatility_estimate_columns_v0(bars)


def load_member_bars(
    archive_root: Path,
    *,
    native_instrument_id: str,
    start_inclusive: str,
    end_exclusive: str,
) -> pd.DataFrame:
    raw_dir = chrono_base(archive_root) / "raw" / "ohlcv_pt1h" / native_instrument_id
    bars = load_native_swap_pages_to_mv2_bars(raw_dir)
    start = pd.Timestamp(start_inclusive)
    end = pd.Timestamp(end_exclusive)
    idx = pd.to_datetime(bars.index, utc=True)
    mask = (idx >= start) & (idx < end)
    out = bars.loc[mask]
    if out.empty:
        raise ValueError(f"EMPTY_BARS:{native_instrument_id}:{start_inclusive}..{end_exclusive}")
    return out


__all__ = [
    "DEV_PANEL_SUBDIR",
    "EXPECTED_CONTENT_HASH",
    "EXPECTED_MANIFEST_SHA256",
    "REQUIRED_DATASET_ID",
    "assert_not_holdout_path",
    "included_panel_members",
    "load_member_bars",
    "load_native_swap_pages_to_mv2_bars",
    "resolve_development_archive_root",
    "sealed_manifest_path",
    "verify_development_panel_hashes",
]
