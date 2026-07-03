#!/usr/bin/env python3
"""Materialize production point-in-time OKX futures universe manifest v1.

Offline-first: reads lifecycle registry + PT1H panel artifacts from an explicit
staging root produced by materialize_okx_production_lifecycle_and_pt1h_panel_v1.
No network, no orders, no runtime effect.
Operator GO: GO_BOUNDED_PIT_FUTURES_UNIVERSE_MANIFEST_PRODUCTION_MATERIALIZATION_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_TOKEN = "GO_BOUNDED_PIT_FUTURES_UNIVERSE_MANIFEST_PRODUCTION_MATERIALIZATION_V0"

from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (  # noqa: E402
    read_registry_snapshot_v1,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import SOURCE_ID  # noqa: E402
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (  # noqa: E402
    DEFAULT_MINIMUM_HISTORY_BARS,
    DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT,
    EVALUATION_PERIOD_BINDING,
    EXCLUSION_POLICY_VERSION,
    INCLUSION_POLICY_VERSION,
    INPUT_CONTRACT_VERSION,
    MATERIALIZATION_VERSION,
    ProductionMaterializationEpochV1,
    PitFuturesUniverseManifestProductionMaterializationInputV1,
    REGISTRY_ARTIFACT_ID,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
    materialize_production_pit_futures_universe_manifest_v1,
    production_materialization_envelope_to_dict,
    production_materialization_result_to_dict,
)
from src.research.pit_futures_universe_manifest_v1 import manifest_to_dict  # noqa: E402
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (  # noqa: E402
    InstrumentPanelSeriesV1,
    PanelBarV1,
    compute_series_digest,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_panel_series(staging_root: Path) -> tuple[tuple[InstrumentPanelSeriesV1, ...], str, str]:
    panel_dir = staging_root / "panel"
    manifest_path = panel_dir / "panel_dataset_manifest.json"
    bars_path = panel_dir / "normalized_panel_bars.json"
    if not manifest_path.is_file():
        _die(f"ERR: missing_panel_manifest:{manifest_path}")
    if not bars_path.is_file():
        _die(f"ERR: missing_panel_bars:{bars_path}")
    manifest = _load_json(manifest_path)
    rows = json.loads(bars_path.read_text(encoding="utf-8"))
    grouped: dict[str, list[PanelBarV1]] = {}
    for row in rows:
        bar = PanelBarV1(
            instrument_id=str(row["instrument_id"]),
            timestamp_utc=str(row["timestamp_utc"]),
            open=str(row["open"]),
            high=str(row["high"]),
            low=str(row["low"]),
            close=str(row["close"]),
            volume=str(row["volume"]),
            is_final=bool(row["is_final"]),
        )
        grouped.setdefault(bar.instrument_id, []).append(bar)
    series_list: list[InstrumentPanelSeriesV1] = []
    native_by_id = dict(
        zip(manifest["instrument_ids"], manifest["native_instrument_ids"], strict=True)
    )
    for instrument_id in sorted(grouped):
        bars = tuple(sorted(grouped[instrument_id], key=lambda item: item.timestamp_utc))
        interim = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=native_by_id.get(instrument_id, instrument_id),
            bars=bars,
            series_digest="0" * 64,
        )
        series_list.append(
            InstrumentPanelSeriesV1(
                instrument_id=interim.instrument_id,
                native_instrument_id=interim.native_instrument_id,
                bars=interim.bars,
                series_digest=compute_series_digest(interim),
            )
        )
    panel_ref = (
        f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{manifest['panel_id']}:"
        f"sha256:{manifest['manifest_digest']}"
    )
    return tuple(series_list), panel_ref, str(manifest["manifest_digest"])


def _load_lifecycle_inputs(staging_root: Path) -> tuple[Any, str, str, str, str]:
    lifecycle_dir = staging_root / "lifecycle"
    registry_path = lifecycle_dir / "registry_snapshot_v1.json"
    source_reg_path = lifecycle_dir / "SOURCE_REGISTRATION.json"
    if not registry_path.is_file():
        _die(f"ERR: missing_registry_snapshot:{registry_path}")
    if not source_reg_path.is_file():
        _die(f"ERR: missing_source_registration:{source_reg_path}")
    read_result = read_registry_snapshot_v1(
        root_dir=lifecycle_dir,
        relative_path="registry_snapshot_v1.json",
    )
    if not read_result.success or read_result.snapshot is None:
        _die(f"ERR: registry_read_failed:{read_result.error_codes}")
    source_reg = _load_json(source_reg_path)
    return (
        read_result.snapshot,
        str(source_reg["source_snapshot_ref"]),
        str(source_reg["source_snapshot_digest"]),
        str(read_result.snapshot.config_digest),
        str(read_result.snapshot.implementation_digest),
    )


def _load_period_binding(staging_root: Path) -> tuple[str, str, str]:
    period_path = staging_root / "reports" / "PERIOD_BINDING.json"
    if period_path.is_file():
        payload = _load_json(period_path)
        return (
            str(payload.get("evaluation_period_binding", EVALUATION_PERIOD_BINDING)),
            str(payload["period_start_utc"]),
            str(payload["period_end_utc"]),
        )
    panel_manifest = _load_json(staging_root / "panel" / "panel_dataset_manifest.json")
    return (
        EVALUATION_PERIOD_BINDING,
        str(panel_manifest["period_start_utc"]),
        str(panel_manifest["period_end_utc"]),
    )


def run_materialization(
    *,
    confirm: str,
    staging_root: Path,
    durable_evidence_root: Path,
    generated_at: str | None = None,
    finalized_bar_close: str | None = None,
) -> dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required")
    if not staging_root.is_dir():
        _die(f"ERR: staging_root_missing:{staging_root}")

    registry_snapshot, source_ref, source_digest, registry_config_digest, registry_impl_digest = (
        _load_lifecycle_inputs(staging_root)
    )
    panel_series, panel_ref, panel_digest = _load_panel_series(staging_root)
    period_binding_ref, period_start, period_end = _load_period_binding(staging_root)

    panel_manifest = _load_json(staging_root / "panel" / "panel_dataset_manifest.json")
    score_close = finalized_bar_close or str(panel_manifest["period_end_utc"])
    materialized_at = generated_at or _utc_now_z()

    materialization_input = PitFuturesUniverseManifestProductionMaterializationInputV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        materialization_version=MATERIALIZATION_VERSION,
        generated_at=materialized_at,
        universe_policy_id=UNIVERSE_POLICY_ID,
        universe_policy_version=UNIVERSE_POLICY_VERSION,
        inclusion_policy_version=INCLUSION_POLICY_VERSION,
        exclusion_policy_version=EXCLUSION_POLICY_VERSION,
        lifecycle_source_id=SOURCE_ID,
        lifecycle_source_snapshot_ref=source_ref,
        lifecycle_source_snapshot_digest=source_digest,
        registry_artifact_id=REGISTRY_ARTIFACT_ID,
        registry_snapshot=registry_snapshot,
        panel_series=panel_series,
        panel_dataset_ref=panel_ref,
        panel_dataset_digest=panel_digest,
        period_binding_ref=period_binding_ref,
        period_start_utc=period_start,
        period_end_utc=period_end,
        minimum_history_bars=DEFAULT_MINIMUM_HISTORY_BARS,
        minimum_required_member_count=DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT,
        registry_config_digest=registry_config_digest,
        registry_implementation_digest=registry_impl_digest,
        epochs=(
            ProductionMaterializationEpochV1(
                score_epoch=0,
                finalized_bar_close=score_close,
            ),
        ),
    )
    result = materialize_production_pit_futures_universe_manifest_v1(materialization_input)
    if not result.success or result.manifest is None or result.envelope is None:
        _die(f"ERR: production_manifest_materialization_failed:{result.error_codes}")

    universe_dir = staging_root / "universe"
    universe_dir.mkdir(parents=True, exist_ok=True)
    (universe_dir / "pit_futures_universe_manifest_v1.json").write_text(
        json.dumps(manifest_to_dict(result.manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (universe_dir / "production_materialization_envelope_v1.json").write_text(
        json.dumps(
            production_materialization_envelope_to_dict(result.envelope), indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    (universe_dir / "MANIFEST_REFERENCE.txt").write_text(
        (result.envelope.manifest_reference or "") + "\n",
        encoding="utf-8",
    )

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "planning"
        / f"bounded_pit_futures_universe_manifest_production_materialization_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for rel in (
        "universe/pit_futures_universe_manifest_v1.json",
        "universe/production_materialization_envelope_v1.json",
        "universe/MANIFEST_REFERENCE.txt",
        "lifecycle/registry_snapshot_v1.json",
        "panel/panel_dataset_manifest.json",
    ):
        src = staging_root / rel
        if src.is_file():
            dst = evidence_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "PIT_FUTURES_UNIVERSE_MANIFEST_PRODUCTION_MATERIALIZATION_COMPLETE",
        "universe_policy_id": UNIVERSE_POLICY_ID,
        "universe_policy_version": UNIVERSE_POLICY_VERSION,
        "manifest_digest": result.envelope.manifest_digest,
        "manifest_reference": result.envelope.manifest_reference,
        "eligible_instrument_count": result.envelope.eligible_instrument_count,
        "excluded_instrument_count": result.envelope.excluded_instrument_count,
        "registry_snapshot_digest": result.envelope.registry_snapshot_digest,
        "panel_dataset_ref": result.envelope.panel_dataset_ref,
        "panel_dataset_digest": result.envelope.panel_dataset_digest,
        "staging_root": str(staging_root),
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "materialization_result": production_materialization_result_to_dict(result),
    }
    (evidence_dir / "MATERIALIZATION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _emit_machine_lines(payload)
    return payload


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "universe_policy_id",
        "universe_policy_version",
        "manifest_digest",
        "manifest_reference",
        "eligible_instrument_count",
        "excluded_instrument_count",
        "manifest_verify_rc",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize production PIT futures universe manifest v1 from staging artifacts."
    )
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument("--generated-at", default=None)
    parser.add_argument("--finalized-bar-close", default=None)
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm,
        staging_root=args.staging_root,
        durable_evidence_root=args.durable_evidence_root,
        generated_at=args.generated_at,
        finalized_bar_close=args.finalized_bar_close,
    )


if __name__ == "__main__":
    main()
