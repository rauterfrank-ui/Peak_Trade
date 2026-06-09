"""Read-only Kraken Futures metadata coverage diagnostics from governed archive bundles."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .futures_producer_packet_real_metadata_source_v1 import (
    FuturesProducerPacketRealMetadataSourceError,
    load_futures_producer_packet_governed,
)
from .types import KrakenMetadataCoverageCardV1

GOVERNED_METADATA_DIR = "governed_metadata"
GOVERNED_BUNDLE_FILENAME = "futures_producer_packet_governed.v1.json"
KRAKEN_FUTURES_PROVIDER = "kraken_futures"

LOAD_ERROR_GOVERNED_BUNDLE_NOT_FOUND = "GOVERNED_BUNDLE_NOT_FOUND"
LOAD_ERROR_MANIFEST_VERIFY_FAILED = "MANIFEST_VERIFY_FAILED"
LOAD_ERROR_GOVERNED_BUNDLE_INVALID = "GOVERNED_BUNDLE_INVALID"
LOAD_ERROR_PROVIDER_NOT_KRAKEN_FUTURES = "PROVIDER_NOT_KRAKEN_FUTURES"
LOAD_ERROR_OBSERVABILITY_TRUTH_CLAIMED = "OBSERVABILITY_TRUTH_CLAIMED"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _import_manifest_helpers() -> tuple[Any, Any]:
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import (
        parse_manifest_verify_log_rc,
        verify_manifest_sha256,
    )

    return parse_manifest_verify_log_rc, verify_manifest_sha256


def _empty_card(*load_errors: str) -> KrakenMetadataCoverageCardV1:
    return KrakenMetadataCoverageCardV1(
        loaded=False,
        load_errors=load_errors,
        diagnostic_only=True,
        not_truth=True,
        not_selected_future=True,
        strict_upstream_blocked=True,
        observability_truth_allowed=False,
    )


def _bundle_dir_manifest_verified(bundle_dir: Path) -> bool:
    parse_manifest_verify_log_rc, verify_manifest_sha256 = _import_manifest_helpers()
    parsed_rc, _, _ = parse_manifest_verify_log_rc(bundle_dir)
    if parsed_rc != 0:
        return False
    verify_ok, _ = verify_manifest_sha256(bundle_dir)
    return verify_ok


def _discover_kraken_governed_bundle_path(archive_root: Path) -> Path | None:
    governed_root = archive_root / GOVERNED_METADATA_DIR
    if not governed_root.is_dir():
        return None

    candidates: list[tuple[str, Path]] = []
    for bundle_dir in governed_root.iterdir():
        if not bundle_dir.is_dir():
            continue
        bundle_path = bundle_dir / GOVERNED_BUNDLE_FILENAME
        if not bundle_path.is_file():
            continue
        if not _bundle_dir_manifest_verified(bundle_dir):
            continue
        try:
            data = json.loads(bundle_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        if str(data.get("provider") or "") != KRAKEN_FUTURES_PROVIDER:
            continue
        generated_at = str(data.get("generated_at") or "")
        candidates.append((generated_at, bundle_path))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _read_completeness_summary(data: dict[str, Any]) -> dict[str, Any] | None:
    summary = data.get("instrument_completeness_summary")
    if not isinstance(summary, dict):
        return None
    return summary


def try_load_kraken_metadata_coverage_for_dashboard(
    archive_root: str | Path,
) -> KrakenMetadataCoverageCardV1:
    """Load diagnostic-only Kraken metadata coverage from manifest-verified governed bundles."""

    root = Path(archive_root).expanduser().resolve()
    bundle_path = _discover_kraken_governed_bundle_path(root)
    if bundle_path is None:
        return _empty_card(LOAD_ERROR_GOVERNED_BUNDLE_NOT_FOUND)

    bundle_dir = bundle_path.parent
    if not _bundle_dir_manifest_verified(bundle_dir):
        return _empty_card(LOAD_ERROR_MANIFEST_VERIFY_FAILED)

    try:
        raw = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_card(LOAD_ERROR_GOVERNED_BUNDLE_INVALID)

    if not isinstance(raw, dict):
        return _empty_card(LOAD_ERROR_GOVERNED_BUNDLE_INVALID)

    if str(raw.get("provider") or "") != KRAKEN_FUTURES_PROVIDER:
        return _empty_card(LOAD_ERROR_PROVIDER_NOT_KRAKEN_FUTURES)

    if raw.get("observability_truth_allowed") is True:
        return _empty_card(LOAD_ERROR_OBSERVABILITY_TRUTH_CLAIMED)

    summary = _read_completeness_summary(raw)
    if summary is None:
        return _empty_card(LOAD_ERROR_GOVERNED_BUNDLE_INVALID)

    try:
        load_futures_producer_packet_governed(bundle_path, archive_root=root)
    except FuturesProducerPacketRealMetadataSourceError:
        return _empty_card(LOAD_ERROR_GOVERNED_BUNDLE_INVALID)

    packet_count = int(summary.get("packet_count") or 0)
    candidate_validation_complete_count = int(summary.get("candidate_validation_complete_count") or 0)
    strict_instrument_complete_count = int(summary.get("strict_instrument_complete_count") or 0)
    missing_counts = summary.get("missing_provider_metadata_counts")
    min_notional_unknown_count = 0
    if isinstance(missing_counts, dict):
        min_notional_unknown_count = int(missing_counts.get("min_notional") or 0)

    evidence_links_raw = raw.get("evidence_links")
    evidence_links: tuple[str, ...] = ()
    if isinstance(evidence_links_raw, list):
        evidence_links = tuple(str(link) for link in evidence_links_raw if str(link))

    return KrakenMetadataCoverageCardV1(
        loaded=True,
        load_errors=(),
        provider=KRAKEN_FUTURES_PROVIDER,
        packet_count=packet_count,
        candidate_validation_complete_count=candidate_validation_complete_count,
        candidate_validation_total_count=packet_count,
        strict_instrument_complete_count=strict_instrument_complete_count,
        min_notional_unknown_count=min_notional_unknown_count,
        strict_upstream_blocked=True,
        observability_truth_allowed=False,
        diagnostic_only=True,
        not_truth=True,
        not_selected_future=True,
        source_run_id=str(raw.get("source_run_id") or "") or None,
        generated_at=str(raw.get("generated_at") or "") or None,
        evidence_links=evidence_links,
    )
