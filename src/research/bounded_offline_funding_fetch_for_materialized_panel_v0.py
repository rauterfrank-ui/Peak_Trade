"""Bounded offline funding fetch for already materialized extended_chronological_v1 panel v0.

Reuses canonical bound-panel funding materialization owners to fetch OKX public funding
history for panel members already bound in extended_chronological_v1 staging. Does not
expand beyond panel manifest, touch partial tmp OHLCV sources, or start evaluation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    INFRASTRUCTURE_GO_TOKEN,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
    PANEL_DATASET_ID,
)
from src.research.csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0 import (
    preflight_result_to_dict,
    run_dataset_funding_binding_materialization_preflight_v0,
)
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
)
from src.research.offline_panel_materialization_from_partial_tmp_no_fetch_v0 import (
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    DEFAULT_OUTPUT_STAGING_REL,
    REASON_FUNDING_SCOPE_DRIFT,
    load_offline_panel_materialization_config_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)

PACKAGE_MARKER = "BOUNDED_OFFLINE_FUNDING_FETCH_FOR_MATERIALIZED_PANEL_V0=true"
MATERIALIZATION_VERSION = "bounded_offline_funding_fetch_for_materialized_panel.v0"
CONFIRM_GO = "GO_BOUNDED_OFFLINE_FUNDING_FETCH_FOR_MATERIALIZED_PANEL_V0"
CONFIG_REL_PATH = "config/ops/bounded_offline_funding_fetch_for_materialized_panel_v0.json"

FUNDING_MANIFEST_REL = Path("panel/panel_funding_dataset_manifest.json")
FUNDING_BARS_REL = Path("panel/normalized_panel_bars_with_funding.json")

REASON_STAGING_MISSING = "STAGING_MISSING"
REASON_PANEL_MANIFEST_MISSING = "PANEL_MANIFEST_MISSING"
REASON_FUNDING_ALREADY_FETCHED = "FUNDING_ALREADY_FETCHED_FROM_OKX_PUBLIC"
REASON_FETCH_GUARD_BLOCKED = "FETCH_GUARD_BLOCKED"
REASON_OKX_PUBLIC_FUNDING_API_HORIZON_INSUFFICIENT = (
    "OKX_PUBLIC_FUNDING_API_HORIZON_INSUFFICIENT_FOR_PANEL_PERIOD"
)


class BoundedFundingFetchVerdict(str, Enum):
    FUNDING_FETCHED_PREFLIGHT_COMPLETE = "FUNDING_FETCHED_PREFLIGHT_COMPLETE"
    FAIL_CLOSED_STAGING = "FAIL_CLOSED_STAGING"
    FAIL_CLOSED_PANEL_BINDING = "FAIL_CLOSED_PANEL_BINDING"
    FAIL_CLOSED_FETCH = "FAIL_CLOSED_FETCH"
    FAIL_CLOSED_PREFLIGHT = "FAIL_CLOSED_PREFLIGHT"
    FAIL_CLOSED_ALREADY_FETCHED = "FAIL_CLOSED_ALREADY_FETCHED"


@dataclass(frozen=True)
class PanelMemberBindingV0:
    staging_root: str
    panel_member_count: int
    instrument_ids: tuple[str, ...]
    native_instrument_ids: tuple[str, ...]
    panel_calendar_start_utc: str
    panel_calendar_end_utc: str
    panel_dataset_manifest_path: str


@dataclass(frozen=True)
class FundingCoverageReportV0:
    row_count_total: int
    missing_funding_count: int
    populated_funding_count: int
    coverage_ratio: float
    fetched_from_okx_public: bool | None
    instrument_count: int
    manifest_verified: bool


@dataclass(frozen=True)
class BoundedOfflineFundingFetchScopeResultV0:
    verdict: BoundedFundingFetchVerdict
    panel_binding: PanelMemberBindingV0 | None
    coverage_before: FundingCoverageReportV0 | None
    coverage_after: FundingCoverageReportV0 | None
    fetch_result: dict[str, Any] | None
    preflight_before: dict[str, Any] | None
    preflight_after: dict[str, Any] | None
    fetch_run: bool
    network_fetch_run: bool
    full_universe_fetch_run: bool
    economic_evaluation_run: bool
    reason_codes: tuple[str, ...]


def load_bounded_funding_fetch_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return {
            "schema_version": MATERIALIZATION_VERSION,
            "output_staging_rel": DEFAULT_OUTPUT_STAGING_REL,
            "funding_owner": CANONICAL_FUNDING_OWNER,
            "preflight_owner": CANONICAL_PREFLIGHT_OWNER,
            "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
            "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def load_panel_member_binding_v0(staging_root: Path) -> PanelMemberBindingV0:
    staging_root = staging_root.resolve()
    panel_manifest_path = staging_root / "panel" / "panel_dataset_manifest.json"
    if not staging_root.is_dir():
        raise FileNotFoundError(REASON_STAGING_MISSING)
    if not panel_manifest_path.is_file():
        raise FileNotFoundError(REASON_PANEL_MANIFEST_MISSING)

    manifest = json.loads(panel_manifest_path.read_text(encoding="utf-8"))
    raw_instrument_ids = manifest.get("instrument_ids")
    raw_native_ids = manifest.get("native_instrument_ids")
    if isinstance(raw_instrument_ids, list) and isinstance(raw_native_ids, list):
        instrument_ids = tuple(sorted(str(item) for item in raw_instrument_ids))
        native_ids = tuple(sorted(str(item) for item in raw_native_ids))
    else:
        panel_series, _ = load_panel_series_from_staging(staging_root)
        instrument_ids = tuple(sorted(series.instrument_id for series in panel_series))
        native_ids = tuple(sorted(series.native_instrument_id for series in panel_series))
    return PanelMemberBindingV0(
        staging_root=str(staging_root),
        panel_member_count=len(instrument_ids),
        instrument_ids=instrument_ids,
        native_instrument_ids=native_ids,
        panel_calendar_start_utc=str(
            manifest.get("panel_calendar_start_utc", PANEL_CALENDAR_START_UTC)
        ),
        panel_calendar_end_utc=str(manifest.get("panel_calendar_end_utc", PANEL_CALENDAR_END_UTC)),
        panel_dataset_manifest_path=str(panel_manifest_path),
    )


def compute_funding_coverage_report_v0(staging_root: Path) -> FundingCoverageReportV0:
    staging_root = staging_root.resolve()
    manifest_path = staging_root / FUNDING_MANIFEST_REL
    if not manifest_path.is_file():
        return FundingCoverageReportV0(
            row_count_total=0,
            missing_funding_count=0,
            populated_funding_count=0,
            coverage_ratio=0.0,
            fetched_from_okx_public=None,
            instrument_count=0,
            manifest_verified=False,
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row_count = int(manifest.get("row_count_total", 0))
    missing_count = int(manifest.get("missing_funding_count", row_count))
    populated = max(row_count - missing_count, 0)
    ratio = (populated / row_count) if row_count else 0.0
    raw_ids = manifest.get("instrument_ids")
    instrument_count = len(raw_ids) if isinstance(raw_ids, list) else 0
    fetched = manifest.get("fetched_from_okx_public")
    fetched_bool = bool(fetched) if isinstance(fetched, bool) else None

    manifest_verified = False
    bars_path = staging_root / FUNDING_BARS_REL
    if bars_path.is_file() and row_count > 0:
        from scripts.ops import (
            materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 as funding_mod,
        )

        manifest_verified = funding_mod._verify_existing_manifest(staging_root)

    return FundingCoverageReportV0(
        row_count_total=row_count,
        missing_funding_count=missing_count,
        populated_funding_count=populated,
        coverage_ratio=round(ratio, 6),
        fetched_from_okx_public=fetched_bool,
        instrument_count=instrument_count,
        manifest_verified=manifest_verified,
    )


def funding_coverage_report_to_dict(report: FundingCoverageReportV0) -> dict[str, Any]:
    return {
        "row_count_total": report.row_count_total,
        "missing_funding_count": report.missing_funding_count,
        "populated_funding_count": report.populated_funding_count,
        "coverage_ratio": report.coverage_ratio,
        "fetched_from_okx_public": report.fetched_from_okx_public,
        "instrument_count": report.instrument_count,
        "manifest_verified": report.manifest_verified,
    }


def panel_member_binding_to_dict(binding: PanelMemberBindingV0) -> dict[str, Any]:
    return {
        "staging_root": binding.staging_root,
        "panel_member_count": binding.panel_member_count,
        "instrument_ids": list(binding.instrument_ids),
        "native_instrument_ids": list(binding.native_instrument_ids),
        "panel_calendar_start_utc": binding.panel_calendar_start_utc,
        "panel_calendar_end_utc": binding.panel_calendar_end_utc,
        "panel_dataset_manifest_path": binding.panel_dataset_manifest_path,
    }


def clear_stale_skip_fetch_funding_artifacts_v0(staging_root: Path) -> tuple[bool, tuple[str, ...]]:
    """Remove skip-fetch funding artifacts so network fetch can proceed."""
    staging_root = staging_root.resolve()
    manifest_path = staging_root / FUNDING_MANIFEST_REL
    if not manifest_path.is_file():
        return False, ()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("fetched_from_okx_public") is True:
        row_count = int(manifest.get("row_count_total", 0))
        missing_count = int(manifest.get("missing_funding_count", row_count))
        if row_count > 0 and missing_count < row_count:
            return False, (REASON_FUNDING_ALREADY_FETCHED,)

    removed: list[str] = []
    for rel in (FUNDING_MANIFEST_REL, FUNDING_BARS_REL):
        path = staging_root / rel
        if path.is_file():
            path.unlink()
            removed.append(str(rel))
    raw_funding_dir = staging_root / "raw" / "funding_history"
    if raw_funding_dir.is_dir():
        for path in raw_funding_dir.glob("*.json"):
            path.unlink()
            removed.append(str(path.relative_to(staging_root)))
    return bool(removed), tuple(removed)


def _verify_panel_binding_scope_v0(
    binding: PanelMemberBindingV0,
    staging_root: Path,
) -> tuple[bool, tuple[str, ...]]:
    panel_series, _ = load_panel_series_from_staging(staging_root)
    panel_ids = {series.instrument_id for series in panel_series}
    if set(binding.instrument_ids) != panel_ids:
        return False, (REASON_FUNDING_SCOPE_DRIFT,)
    return True, ()


def run_bounded_offline_funding_fetch_scope_v0(
    *,
    repo_root: Path,
    durable_evidence_root: Path,
    staging_root: Path | None = None,
    binding_origin_main_sha: str | None = None,
    confirm_go: str = CONFIRM_GO,
    execute_fetch: bool = True,
) -> BoundedOfflineFundingFetchScopeResultV0:
    if confirm_go != CONFIRM_GO:
        return BoundedOfflineFundingFetchScopeResultV0(
            verdict=BoundedFundingFetchVerdict.FAIL_CLOSED_FETCH,
            panel_binding=None,
            coverage_before=None,
            coverage_after=None,
            fetch_result=None,
            preflight_before=None,
            preflight_after=None,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            economic_evaluation_run=False,
            reason_codes=(REASON_FETCH_GUARD_BLOCKED,),
        )

    config = load_bounded_funding_fetch_config_v0(repo_root)
    offline_config = load_offline_panel_materialization_config_v0(repo_root)
    output_root = staging_root or (
        durable_evidence_root / str(config.get("output_staging_rel", DEFAULT_OUTPUT_STAGING_REL))
    )

    try:
        panel_binding = load_panel_member_binding_v0(output_root)
    except FileNotFoundError as exc:
        return BoundedOfflineFundingFetchScopeResultV0(
            verdict=BoundedFundingFetchVerdict.FAIL_CLOSED_STAGING,
            panel_binding=None,
            coverage_before=None,
            coverage_after=None,
            fetch_result=None,
            preflight_before=None,
            preflight_after=None,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            economic_evaluation_run=False,
            reason_codes=(str(exc),),
        )

    if panel_binding.panel_member_count == 0:
        return BoundedOfflineFundingFetchScopeResultV0(
            verdict=BoundedFundingFetchVerdict.FAIL_CLOSED_PANEL_BINDING,
            panel_binding=panel_binding,
            coverage_before=None,
            coverage_after=None,
            fetch_result=None,
            preflight_before=None,
            preflight_after=None,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            economic_evaluation_run=False,
            reason_codes=(REASON_EMPTY_PANEL,),
        )

    scope_ok, scope_reasons = _verify_panel_binding_scope_v0(panel_binding, output_root)
    if not scope_ok:
        return BoundedOfflineFundingFetchScopeResultV0(
            verdict=BoundedFundingFetchVerdict.FAIL_CLOSED_PANEL_BINDING,
            panel_binding=panel_binding,
            coverage_before=compute_funding_coverage_report_v0(output_root),
            coverage_after=None,
            fetch_result=None,
            preflight_before=None,
            preflight_after=None,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            economic_evaluation_run=False,
            reason_codes=scope_reasons,
        )

    resolved_binding_sha = (
        binding_origin_main_sha
        or str(config.get("binding_origin_main_sha", "")).strip()
        or str(offline_config.get("binding_origin_main_sha", "")).strip()
    )

    preflight_before = preflight_result_to_dict(
        run_dataset_funding_binding_materialization_preflight_v0(
            repo_root=repo_root,
            staging_root=output_root,
            expected_origin_main_sha=resolved_binding_sha,
            binding_origin_main_sha=resolved_binding_sha,
        )
    )
    coverage_before = compute_funding_coverage_report_v0(output_root)

    if coverage_before.fetched_from_okx_public is True and coverage_before.coverage_ratio >= 1.0:
        return BoundedOfflineFundingFetchScopeResultV0(
            verdict=BoundedFundingFetchVerdict.FAIL_CLOSED_ALREADY_FETCHED,
            panel_binding=panel_binding,
            coverage_before=coverage_before,
            coverage_after=coverage_before,
            fetch_result={"verdict": "BOUND_FUNDING_PANEL_READY_REUSED"},
            preflight_before=preflight_before,
            preflight_after=preflight_before,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            economic_evaluation_run=False,
            reason_codes=(REASON_FUNDING_ALREADY_FETCHED,),
        )

    fetch_result: dict[str, Any] | None = None
    network_fetch_run = False
    fetch_run = False
    fetch_reasons: tuple[str, ...] = ()

    if execute_fetch:
        cleared, clear_notes = clear_stale_skip_fetch_funding_artifacts_v0(output_root)
        if REASON_FUNDING_ALREADY_FETCHED in clear_notes:
            return BoundedOfflineFundingFetchScopeResultV0(
                verdict=BoundedFundingFetchVerdict.FAIL_CLOSED_ALREADY_FETCHED,
                panel_binding=panel_binding,
                coverage_before=coverage_before,
                coverage_after=coverage_before,
                fetch_result=None,
                preflight_before=preflight_before,
                preflight_after=None,
                fetch_run=False,
                network_fetch_run=False,
                full_universe_fetch_run=False,
                economic_evaluation_run=False,
                reason_codes=(REASON_FUNDING_ALREADY_FETCHED,),
            )

        from scripts.ops import (
            materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 as funding_mod,
        )
        from scripts.ops import (
            materialize_cross_sectional_funding_rate_delta_momentum_v0_bound_panel_funding_dataset_v0 as rdm_funding_mod,
        )

        funding_mod.CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
        rdm_funding_mod.CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
        fetch_run = True
        network_fetch_run = True
        fetch_result = funding_mod.materialize_bound_panel_funding_dataset_v0(
            confirm=INFRASTRUCTURE_GO_TOKEN,
            staging_root=output_root,
            skip_fetch=False,
        )

        manifest_path = output_root / FUNDING_MANIFEST_REL
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["dataset_extension"] = "extended_chronological_with_funding_v1"
            manifest["panel_id"] = PANEL_DATASET_ID
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        funding_ids = fetch_result.get("instrument_ids")
        if isinstance(funding_ids, list):
            if set(str(item) for item in funding_ids) != set(panel_binding.instrument_ids):
                fetch_reasons = (REASON_FUNDING_SCOPE_DRIFT,)

    coverage_after = compute_funding_coverage_report_v0(output_root)
    preflight_after = preflight_result_to_dict(
        run_dataset_funding_binding_materialization_preflight_v0(
            repo_root=repo_root,
            staging_root=output_root,
            expected_origin_main_sha=resolved_binding_sha,
            binding_origin_main_sha=resolved_binding_sha,
        )
    )

    ready = bool(preflight_after.get("ready_for_next_pre_evaluation_gate"))
    reason_codes_list: list[str] = list(fetch_reasons)
    if (
        fetch_run
        and coverage_after.populated_funding_count == 0
        and coverage_after.row_count_total > 0
    ):
        reason_codes_list.append(REASON_OKX_PUBLIC_FUNDING_API_HORIZON_INSUFFICIENT)
    if fetch_reasons:
        verdict = BoundedFundingFetchVerdict.FAIL_CLOSED_FETCH
        reason_codes = tuple(reason_codes_list)
    elif ready:
        verdict = BoundedFundingFetchVerdict.FUNDING_FETCHED_PREFLIGHT_COMPLETE
        reason_codes = ()
    else:
        verdict = BoundedFundingFetchVerdict.FAIL_CLOSED_PREFLIGHT
        raw_reasons = preflight_after.get("reason_codes")
        reason_codes = tuple(
            dict.fromkeys(
                [
                    *reason_codes_list,
                    *(str(item) for item in raw_reasons if isinstance(raw_reasons, list)),
                ]
            )
        )

    return BoundedOfflineFundingFetchScopeResultV0(
        verdict=verdict,
        panel_binding=panel_binding,
        coverage_before=coverage_before,
        coverage_after=coverage_after,
        fetch_result=fetch_result,
        preflight_before=preflight_before,
        preflight_after=preflight_after,
        fetch_run=fetch_run,
        network_fetch_run=network_fetch_run,
        full_universe_fetch_run=False,
        economic_evaluation_run=False,
        reason_codes=reason_codes,
    )


def bounded_offline_funding_fetch_scope_result_to_dict(
    result: BoundedOfflineFundingFetchScopeResultV0,
) -> dict[str, Any]:
    return {
        "schema_version": MATERIALIZATION_VERSION,
        "verdict": result.verdict.value,
        "confirm_go": CONFIRM_GO,
        "package_marker": PACKAGE_MARKER,
        "panel_binding": (
            panel_member_binding_to_dict(result.panel_binding)
            if result.panel_binding is not None
            else None
        ),
        "coverage_before": (
            funding_coverage_report_to_dict(result.coverage_before)
            if result.coverage_before is not None
            else None
        ),
        "coverage_after": (
            funding_coverage_report_to_dict(result.coverage_after)
            if result.coverage_after is not None
            else None
        ),
        "fetch_result": result.fetch_result,
        "preflight_before_status": (
            result.preflight_before.get("status") if result.preflight_before else None
        ),
        "preflight_after_status": (
            result.preflight_after.get("status") if result.preflight_after else None
        ),
        "ready_for_next_pre_evaluation_gate": bool(
            result.preflight_after
            and result.preflight_after.get("ready_for_next_pre_evaluation_gate")
        ),
        "fetch_run": result.fetch_run,
        "network_fetch_run": result.network_fetch_run,
        "full_universe_fetch_run": result.full_universe_fetch_run,
        "economic_evaluation_run": result.economic_evaluation_run,
        "reason_codes": list(result.reason_codes),
        "reuse_decisions": {
            "funding_owner": CANONICAL_FUNDING_OWNER,
            "preflight_owner": CANONICAL_PREFLIGHT_OWNER,
            "source_panel_materialization_owner": (
                "src/research/offline_panel_materialization_from_partial_tmp_no_fetch_v0.py"
            ),
        },
    }


__all__ = [
    "CONFIRM_GO",
    "CONFIG_REL_PATH",
    "DEFAULT_DURABLE_ARCHIVE_ROOT",
    "BoundedFundingFetchVerdict",
    "BoundedOfflineFundingFetchScopeResultV0",
    "FundingCoverageReportV0",
    "MATERIALIZATION_VERSION",
    "PanelMemberBindingV0",
    "bounded_offline_funding_fetch_scope_result_to_dict",
    "clear_stale_skip_fetch_funding_artifacts_v0",
    "compute_funding_coverage_report_v0",
    "funding_coverage_report_to_dict",
    "load_bounded_funding_fetch_config_v0",
    "load_panel_member_binding_v0",
    "panel_member_binding_to_dict",
    "run_bounded_offline_funding_fetch_scope_v0",
]
