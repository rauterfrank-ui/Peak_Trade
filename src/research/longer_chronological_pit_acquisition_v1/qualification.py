"""Qualification dry-run — plan/discover without downloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    TARGET_PERIOD_END,
    TARGET_PERIOD_START,
)
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    archive_layout,
    resolve_archive_root,
)
from src.research.longer_chronological_pit_acquisition_v1.manifest import (
    build_acquisition_manifest,
    write_manifest_atomic,
)
from src.research.longer_chronological_pit_acquisition_v1.partition_planner import (
    InstrumentLifecycleV1,
    plan_partitions,
)
from src.research.longer_chronological_pit_acquisition_v1.source_discovery import (
    list_public_sources,
)


def estimate_volume_gib(
    partition_count: int, *, bytes_per_partition: int = 250_000
) -> dict[str, Any]:
    """Heuristic estimate tagged as ASSUMPTION (not measured)."""
    total = partition_count * bytes_per_partition
    return {
        "partition_count": partition_count,
        "bytes_per_partition_assumption": bytes_per_partition,
        "estimated_bytes": total,
        "estimated_gib": round(total / (1024**3), 4),
        "tag": "ASSUMPTION_NOT_MEASURED",
    }


def run_qualification_dry_run(
    instruments: Sequence[InstrumentLifecycleV1 | Mapping[str, Any]],
    *,
    period_start: str = TARGET_PERIOD_START,
    period_end: str = TARGET_PERIOD_END,
    max_partitions: int | None = None,
    archive_root: str | Path | None = None,
    write_manifest: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Dry-run planner. Never opens network. Writes only with explicit flags + root."""
    plan = plan_partitions(
        instruments,
        period_start=period_start,
        period_end=period_end,
        max_partitions=max_partitions,
    )
    manifest = build_acquisition_manifest(plan["partitions"])
    planned_has_btc = any(
        "BTC" in p["native_instrument_id"].upper() or "XBT" in p["native_instrument_id"].upper()
        for p in plan["partitions"]
    )
    planned_has_spot = any(
        p["native_instrument_id"].upper().endswith("-USDT")
        and "SWAP" not in p["native_instrument_id"].upper()
        for p in plan["partitions"]
    )

    missing_coverage = [
        {
            "source_id": s["source_id"],
            "coverage_certainty": s["coverage_certainty"],
            "notes": s["notes"],
        }
        for s in list_public_sources()
        if s["coverage_certainty"] in {"UNCERTAIN", "PARTIAL"}
    ]

    root = None
    written_path = None
    if write_manifest:
        root = resolve_archive_root(explicit=archive_root, env=env, require_for_write=True)
        assert root is not None
        written_path = str(write_manifest_atomic(manifest, archive_root=root))
    else:
        # plan/discover may resolve root optionally for path display
        root = resolve_archive_root(explicit=archive_root, env=env, require_for_write=False)

    layout_paths = None
    if root is not None:
        layout_paths = {k: str(v) for k, v in archive_layout(root).items()}

    report = {
        "mode": "DRY_RUN",
        "network_used": False,
        "writes_enabled": bool(write_manifest),
        "dataset_id": DATASET_ID,
        "period_start": period_start,
        "period_end": period_end,
        "partition_scheme": plan["partition_scheme"],
        "partition_count": plan["partition_count"],
        "truncated": plan["truncated"],
        "excluded": plan["excluded"],
        "btc_excluded_attested": not planned_has_btc,
        "spot_excluded_attested": not planned_has_spot,
        "pit_universe_required": True,
        "missing_or_uncertain_source_coverage": missing_coverage,
        "volume_estimate": estimate_volume_gib(plan["partition_count"]),
        "expected_paths_sample": [m["expected_artifact_path"] for m in manifest["partitions"][:5]],
        "archive_layout": layout_paths,
        "manifest_digest": manifest["manifest_digest"],
        "manifest_written_to": written_path,
        "economic_gate_opened": False,
        "promotion_eligible": False,
        "partitions": plan["partitions"],
        "manifest": manifest,
    }
    return report


def render_dry_run_text(report: Mapping[str, Any]) -> str:
    lines = [
        f"MODE={report['mode']}",
        f"DATASET_ID={report['dataset_id']}",
        f"PERIOD={report['period_start']}..{report['period_end']}",
        f"PARTITION_COUNT={report['partition_count']}",
        f"PARTITION_SCHEME={report['partition_scheme']}",
        f"BTC_EXCLUDED_ATTESTED={report['btc_excluded_attested']}",
        f"SPOT_EXCLUDED_ATTESTED={report['spot_excluded_attested']}",
        f"NETWORK_USED={report['network_used']}",
        f"WRITES_ENABLED={report['writes_enabled']}",
        f"MANIFEST_DIGEST={report['manifest_digest']}",
        f"VOLUME_ESTIMATE_GIB={report['volume_estimate']['estimated_gib']} ({report['volume_estimate']['tag']})",
        f"EXCLUDED_COUNT={len(report['excluded'])}",
        "EXPECTED_PATHS_SAMPLE:",
    ]
    for p in report["expected_paths_sample"]:
        lines.append(f"  - {p}")
    lines.append("UNCERTAIN_SOURCES:")
    for s in report["missing_or_uncertain_source_coverage"]:
        lines.append(f"  - {s['source_id']}={s['coverage_certainty']}")
    lines.append(f"ECONOMIC_GATE_OPENED={report['economic_gate_opened']}")
    lines.append(f"PROMOTION_ELIGIBLE={report['promotion_eligible']}")
    return "\n".join(lines) + "\n"
