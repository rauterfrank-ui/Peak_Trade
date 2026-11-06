"""Offline integrity contract for vendored Chart.js 4.4.1 UMD asset (no network)."""

from __future__ import annotations

import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHARTJS_VERSION = "4.4.1"
VENDOR_DIR = PROJECT_ROOT / "static" / "vendor" / "chartjs" / CHARTJS_VERSION
ASSET_PATH = VENDOR_DIR / "chart.umd.min.js"
LICENSE_PATH = VENDOR_DIR / "LICENSE.chartjs.txt"
SOURCE_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
PINNED_SHA256 = "d2af8974e95271638772e9e9524db5b9a6f58d6ec2d5d781400447b4a31c681e"
PINNED_SIZE_BYTES = 205399


def _sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_chartjs_vendor_asset_path_exists_v0() -> None:
    assert ASSET_PATH.is_file()
    assert ASSET_PATH.stat().st_size > 0


def test_chartjs_vendor_asset_sha256_matches_pinned_v0() -> None:
    assert _sha256_hex(ASSET_PATH) == PINNED_SHA256


def test_chartjs_vendor_asset_size_matches_pinned_v0() -> None:
    assert ASSET_PATH.stat().st_size == PINNED_SIZE_BYTES


def test_chartjs_vendor_license_attribution_present_v0() -> None:
    license_text = LICENSE_PATH.read_text(encoding="utf-8")
    assert LICENSE_PATH.is_file()
    assert "MIT" in license_text
    assert CHARTJS_VERSION in license_text
    assert SOURCE_URL in license_text
    assert "chartjs/Chart.js" in license_text
