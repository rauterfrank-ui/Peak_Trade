"""U2b — fail-closed governed real-metadata loader for FuturesProducerPacket bundles (explicit path only)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading.master_v2.double_play_futures_input import FuturesFreshnessState, FuturesMarketType
from trading.master_v2.double_play_futures_input_producer import (
    FuturesProducerPacket,
    producer_packet_has_runtime_handles,
)

from .futures_producer_packet_fixture_source_v1 import (
    FuturesProducerPacketFixtureSourceError,
    _parse_packet,
    _require_bool,
    _require_mapping,
    _require_str,
)
from .futures_universe_upstream_adapter_v1 import (
    ELIGIBLE_MARKET_TYPES,
    FORBIDDEN_UPSTREAM_SOURCE_MARKERS,
    FuturesUniverseUpstreamInputV1,
    INELIGIBLE_SPOT_SYMBOLS,
    is_forbidden_upstream_source,
)

GOVERNED_SCHEMA_NAME = "futures_producer_packet_governed.v1"
GOVERNED_SCHEMA_VERSION = 1
GOVERNED_SOURCE_KIND = "governed_metadata_snapshot"
GOVERNED_PRODUCER_ID = "futures_producer_packet_real_metadata_source_v1"
GOVERNED_SOURCE_CONTRACT = "futures_producer_packet_real_metadata_source.v1"

FORBIDDEN_SOURCE_KINDS = frozenset(
    {
        "fixture",
        "market_surface",
        "market_surface_dummy",
        "market_ranking_funnel_readmodel.v0",
        "get_market_dummy",
        "btc_usd_dummy_default",
    }
)

FORBIDDEN_GOVERNANCE_FIELDS = frozenset(
    {
        "approval",
        "approved",
        "live_authorized",
        "live_ready",
        "ready_for_operator_arming",
        "preflight_lift_authorized",
        "strategy_activation",
    }
)

FORBIDDEN_SOURCE_STAGES = frozenset({"live"})

REASON_PATH_NOT_ABSOLUTE = "PATH_NOT_ABSOLUTE"
REASON_PATH_UNDER_TMP = "PATH_UNDER_TMP"
REASON_PATH_OUTSIDE_ARCHIVE_ROOT = "PATH_OUTSIDE_ARCHIVE_ROOT"
REASON_PATH_UNDER_REPO_FIXTURES = "PATH_UNDER_REPO_FIXTURES"
REASON_GOVERNED_SCHEMA_INVALID = "GOVERNED_SCHEMA_INVALID"
REASON_GOVERNED_MISSING_REQUIRED_FIELD = "GOVERNED_MISSING_REQUIRED_FIELD"
REASON_FIXTURE_ONLY_MUST_BE_FALSE = "FIXTURE_ONLY_MUST_BE_FALSE"
REASON_OBSERVABILITY_TRUTH_CLAIMED = "OBSERVABILITY_TRUTH_CLAIMED"
REASON_NON_AUTHORIZING_REQUIRED = "NON_AUTHORIZING_REQUIRED"
REASON_FORBIDDEN_UPSTREAM_SOURCE = "FORBIDDEN_UPSTREAM_SOURCE"
REASON_FORBIDDEN_GOVERNANCE_FIELD = "FORBIDDEN_GOVERNANCE_FIELD"
REASON_FORBIDDEN_SOURCE_STAGE = "FORBIDDEN_SOURCE_STAGE"
REASON_EVIDENCE_LINKS_EMPTY = "EVIDENCE_LINKS_EMPTY"
REASON_METADATA_TABLE_REF_INVALID = "METADATA_TABLE_REF_INVALID"
REASON_MANIFEST_VERIFY_FAILED = "MANIFEST_VERIFY_FAILED"
REASON_MANIFEST_VERIFY_RC_INVALID = "MANIFEST_VERIFY_RC_INVALID"
REASON_INELIGIBLE_SPOT_SYMBOL = "INELIGIBLE_SPOT_SYMBOL"
REASON_INELIGIBLE_MARKET_TYPE = "INELIGIBLE_MARKET_TYPE"
REASON_INSTRUMENT_INCOMPLETE = "INSTRUMENT_INCOMPLETE"
REASON_MISSING_PROVIDER_METADATA = "MISSING_PROVIDER_METADATA"
REASON_PROVENANCE_INCOMPLETE = "PROVENANCE_INCOMPLETE"
REASON_FRESHNESS_NOT_FRESH = "FRESHNESS_NOT_FRESH"
REASON_PACKET_RUNTIME_HANDLE = "PACKET_RUNTIME_HANDLE"


class FuturesProducerPacketRealMetadataSourceError(ValueError):
    """Raised when a governed bundle violates U2b safety or schema rules."""


@dataclass(frozen=True)
class FuturesProducerPacketGovernedBundleV1:
    """Loaded governed bundle — never observability truth until separate Operator readiness."""

    source_kind: str
    producer_id: str
    generated_at: str
    source_run_id: str
    source_stage: str
    fixture_only: bool
    observability_truth_allowed: bool
    non_authorizing: bool
    real_metadata_source_marked: bool
    metadata_table_ref: str
    metadata_refresh_utc: str
    evidence_links: tuple[str, ...]
    universe: dict[str, Any]
    ranking: dict[str, Any]
    selected_future: dict[str, Any]
    packets: tuple[FuturesProducerPacket, ...]
    selected_candidate_id: str | None = None
    bundle_path: str | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _import_manifest_helpers() -> tuple[Any, Any, Any, Any]:
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import (
        is_under_tmp,
        parse_manifest_verify_log_rc,
        require_durable_archive_root,
        verify_manifest_sha256,
    )

    return (
        is_under_tmp,
        require_durable_archive_root,
        verify_manifest_sha256,
        parse_manifest_verify_log_rc,
    )


def _normalize_symbol(symbol: str) -> str:
    return symbol.upper().replace("-", "").replace("/", "")


def _is_spot_symbol(symbol: str) -> bool:
    if symbol in INELIGIBLE_SPOT_SYMBOLS:
        return True
    if _normalize_symbol(symbol) in INELIGIBLE_SPOT_SYMBOLS:
        return True
    if "/" in symbol:
        return True
    return False


def _reject_forbidden_governance_fields(data: dict[str, Any]) -> None:
    for key in data:
        if key in FORBIDDEN_GOVERNANCE_FIELDS:
            msg = f"{REASON_FORBIDDEN_GOVERNANCE_FIELD}: forbidden field '{key}'"
            raise FuturesProducerPacketRealMetadataSourceError(msg)


def _validate_bundle_path_under_archive_root(
    bundle_path: Path,
    archive_root: Path,
) -> None:
    is_under_tmp, require_durable_archive_root, _, _ = _import_manifest_helpers()

    if not bundle_path.is_absolute():
        msg = f"{REASON_PATH_NOT_ABSOLUTE}: bundle path must be absolute"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    resolved_bundle = bundle_path.expanduser().resolve()
    resolved_archive = archive_root.expanduser().resolve()

    if is_under_tmp(resolved_bundle) or is_under_tmp(resolved_archive):
        msg = f"{REASON_PATH_UNDER_TMP}: paths must be outside /tmp"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    ok, msg = require_durable_archive_root(resolved_archive)
    if not ok:
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    fixtures_root = (_repo_root() / "tests" / "fixtures").resolve()
    bundle_posix = resolved_bundle.as_posix()
    fixtures_posix = fixtures_root.as_posix()
    if bundle_posix == fixtures_posix or bundle_posix.startswith(f"{fixtures_posix}/"):
        detail = f"{REASON_PATH_UNDER_REPO_FIXTURES}: repo fixture paths forbidden for U2b"
        raise FuturesProducerPacketRealMetadataSourceError(detail)

    try:
        resolved_bundle.relative_to(resolved_archive)
    except ValueError as exc:
        detail = f"{REASON_PATH_OUTSIDE_ARCHIVE_ROOT}: bundle path must be under archive root"
        raise FuturesProducerPacketRealMetadataSourceError(detail) from exc


def _parse_evidence_links(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        msg = f"{REASON_EVIDENCE_LINKS_EMPTY}: evidence_links must be a non-empty string array"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    links: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            msg = f"{REASON_EVIDENCE_LINKS_EMPTY}: evidence_links must contain non-empty strings"
            raise FuturesProducerPacketRealMetadataSourceError(msg)
        links.append(item.strip())
    return tuple(links)


def _validate_metadata_table_ref(
    metadata_table_ref: str,
    archive_root: Path,
) -> None:
    ref_path = Path(metadata_table_ref).expanduser()
    if not ref_path.is_absolute():
        msg = f"{REASON_METADATA_TABLE_REF_INVALID}: metadata_table_ref must be absolute"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    resolved_ref = ref_path.resolve()
    resolved_archive = archive_root.expanduser().resolve()
    try:
        resolved_ref.relative_to(resolved_archive)
    except ValueError as exc:
        msg = f"{REASON_METADATA_TABLE_REF_INVALID}: metadata_table_ref must be under archive root"
        raise FuturesProducerPacketRealMetadataSourceError(msg) from exc

    if not resolved_ref.is_file():
        msg = f"{REASON_METADATA_TABLE_REF_INVALID}: metadata_table_ref file not found"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    metadata_dir = resolved_ref.parent
    _, _, verify_manifest_sha256, parse_manifest_verify_log_rc = _import_manifest_helpers()
    parsed_rc, rc_msg, _ = parse_manifest_verify_log_rc(metadata_dir)
    if parsed_rc is None:
        msg = f"{REASON_MANIFEST_VERIFY_RC_INVALID}: MANIFEST_VERIFY.log missing or invalid"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if parsed_rc != 0:
        msg = f"{REASON_MANIFEST_VERIFY_RC_INVALID}: MANIFEST_VERIFY_RC={parsed_rc} ({rc_msg})"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    verify_ok, verify_msg = verify_manifest_sha256(metadata_dir)
    if not verify_ok:
        msg = f"{REASON_MANIFEST_VERIFY_FAILED}: {verify_msg}"
        raise FuturesProducerPacketRealMetadataSourceError(msg)


def _parse_candidate_validation_policy(
    data: dict[str, Any],
) -> tuple[bool, frozenset[str]]:
    """Return candidate-validation-only flag and allowed missing provider metadata fields."""
    if not data.get("u2b_candidate_validation_only"):
        return False, frozenset()
    policy = data.get("missing_provider_metadata_policy")
    if not isinstance(policy, dict):
        msg = (
            f"{REASON_GOVERNED_SCHEMA_INVALID}: missing_provider_metadata_policy "
            "required when u2b_candidate_validation_only=true"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    allowed_raw = policy.get("allowed_missing_provider_metadata")
    if not isinstance(allowed_raw, list) or not allowed_raw:
        msg = (
            f"{REASON_GOVERNED_SCHEMA_INVALID}: "
            "allowed_missing_provider_metadata must be a non-empty array"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    allowed = frozenset(str(item) for item in allowed_raw if str(item))
    if not allowed:
        msg = (
            f"{REASON_GOVERNED_SCHEMA_INVALID}: "
            "allowed_missing_provider_metadata must contain non-empty strings"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if data.get("instrument_completeness_mode") != "candidate_validation":
        msg = (
            f"{REASON_GOVERNED_SCHEMA_INVALID}: instrument_completeness_mode must be "
            "candidate_validation when u2b_candidate_validation_only=true"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    return True, allowed


def _validate_packet_eligibility(packet: FuturesProducerPacket) -> None:
    symbol = packet.candidate.symbol
    if _is_spot_symbol(symbol):
        msg = f"{REASON_INELIGIBLE_SPOT_SYMBOL}: spot or slash symbol rejected: {symbol}"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if packet.candidate.market_type not in ELIGIBLE_MARKET_TYPES:
        msg = (
            f"{REASON_INELIGIBLE_MARKET_TYPE}: market_type "
            f"{packet.candidate.market_type} ineligible"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if packet.candidate.live_authorization:
        msg = f"{REASON_FORBIDDEN_GOVERNANCE_FIELD}: live_authorization forbidden"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    instrument = packet.instrument
    if not instrument.complete:
        msg = f"{REASON_INSTRUMENT_INCOMPLETE}: instrument.complete must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    known_flags = (
        instrument.contract_size_known,
        instrument.tick_size_known,
        instrument.step_size_known,
        instrument.min_qty_known,
        instrument.min_notional_known,
        instrument.margin_asset_known,
        instrument.settlement_asset_known,
        instrument.leverage_bounds_known,
    )
    if not all(known_flags):
        msg = f"{REASON_INSTRUMENT_INCOMPLETE}: all instrument *_known flags must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if instrument.missing_fields:
        msg = f"{REASON_INSTRUMENT_INCOMPLETE}: missing_fields must be empty"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    provenance = packet.provenance
    if not provenance.complete:
        msg = f"{REASON_PROVENANCE_INCOMPLETE}: provenance.complete must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if provenance.freshness_state != FuturesFreshnessState.FRESH:
        msg = f"{REASON_FRESHNESS_NOT_FRESH}: freshness_state must be fresh"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if provenance.missing_fields:
        msg = f"{REASON_PROVENANCE_INCOMPLETE}: provenance missing_fields must be empty"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if producer_packet_has_runtime_handles(packet):
        msg = f"{REASON_PACKET_RUNTIME_HANDLE}: packet contains runtime handles"
        raise FuturesProducerPacketRealMetadataSourceError(msg)


def _validate_packet_candidate_validation_eligibility(
    packet: FuturesProducerPacket,
    raw_packet: dict[str, Any],
    *,
    allowed_missing_provider_metadata: frozenset[str],
) -> None:
    """Validate paper-stage candidate bundles without weakening loader-write strictness."""
    symbol = packet.candidate.symbol
    if _is_spot_symbol(symbol):
        msg = f"{REASON_INELIGIBLE_SPOT_SYMBOL}: spot or slash symbol rejected: {symbol}"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if packet.candidate.market_type not in ELIGIBLE_MARKET_TYPES:
        msg = (
            f"{REASON_INELIGIBLE_MARKET_TYPE}: market_type "
            f"{packet.candidate.market_type} ineligible"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if packet.candidate.live_authorization:
        msg = f"{REASON_FORBIDDEN_GOVERNANCE_FIELD}: live_authorization forbidden"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    instrument_raw = raw_packet.get("instrument")
    if not isinstance(instrument_raw, dict):
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: packet instrument must be object"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if instrument_raw.get("candidate_validation_complete") is not True:
        msg = f"{REASON_INSTRUMENT_INCOMPLETE}: candidate_validation_complete must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    instrument = packet.instrument
    provider_known_flags = (
        instrument.contract_size_known,
        instrument.tick_size_known,
        instrument.step_size_known,
        instrument.min_qty_known,
        instrument.margin_asset_known,
        instrument.settlement_asset_known,
        instrument.leverage_bounds_known,
    )
    if not all(provider_known_flags):
        msg = f"{REASON_INSTRUMENT_INCOMPLETE}: provider instrument *_known flags must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if instrument.missing_fields:
        msg = f"{REASON_INSTRUMENT_INCOMPLETE}: missing_fields must be empty"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    missing_provider_raw = instrument_raw.get("missing_provider_metadata")
    if not isinstance(missing_provider_raw, list):
        msg = (
            f"{REASON_GOVERNED_SCHEMA_INVALID}: instrument.missing_provider_metadata "
            "must be an array"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    missing_provider = frozenset(str(item) for item in missing_provider_raw if str(item))
    if not missing_provider.issubset(allowed_missing_provider_metadata):
        extra = sorted(missing_provider - allowed_missing_provider_metadata)
        msg = (
            f"{REASON_MISSING_PROVIDER_METADATA}: unsupported missing provider metadata: "
            f"{','.join(extra)}"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    if not instrument.min_notional_known:
        if "min_notional" not in allowed_missing_provider_metadata:
            msg = (
                f"{REASON_INSTRUMENT_INCOMPLETE}: min_notional_known must be true "
                "outside candidate validation policy"
            )
            raise FuturesProducerPacketRealMetadataSourceError(msg)
        if "min_notional" not in missing_provider:
            msg = (
                f"{REASON_MISSING_PROVIDER_METADATA}: min_notional_known=false requires "
                "explicit missing_provider_metadata entry"
            )
            raise FuturesProducerPacketRealMetadataSourceError(msg)
    elif "min_notional" in missing_provider:
        msg = (
            f"{REASON_MISSING_PROVIDER_METADATA}: min_notional cannot be listed as missing "
            "when min_notional_known=true"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    provenance = packet.provenance
    if not provenance.complete:
        msg = f"{REASON_PROVENANCE_INCOMPLETE}: provenance.complete must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if provenance.freshness_state != FuturesFreshnessState.FRESH:
        msg = f"{REASON_FRESHNESS_NOT_FRESH}: freshness_state must be fresh"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if provenance.missing_fields:
        msg = f"{REASON_PROVENANCE_INCOMPLETE}: provenance missing_fields must be empty"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if producer_packet_has_runtime_handles(packet):
        msg = f"{REASON_PACKET_RUNTIME_HANDLE}: packet contains runtime handles"
        raise FuturesProducerPacketRealMetadataSourceError(msg)


def _validate_governed_governance(data: dict[str, Any]) -> tuple[str, str]:
    _reject_forbidden_governance_fields(data)

    schema_name = _require_str(data, "schema_name")
    if schema_name != GOVERNED_SCHEMA_NAME:
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: schema_name must be {GOVERNED_SCHEMA_NAME}"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if data.get("schema_version") != GOVERNED_SCHEMA_VERSION:
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: schema_version must be {GOVERNED_SCHEMA_VERSION}"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    fixture_only = _require_bool(data, "fixture_only")
    observability_truth_allowed = _require_bool(data, "observability_truth_allowed")
    non_authorizing = _require_bool(data, "non_authorizing")
    real_metadata_source_marked = _require_bool(data, "real_metadata_source_marked")

    if fixture_only:
        msg = f"{REASON_FIXTURE_ONLY_MUST_BE_FALSE}: fixture_only must be false"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if observability_truth_allowed:
        msg = f"{REASON_OBSERVABILITY_TRUTH_CLAIMED}: observability_truth_allowed must be false"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if not non_authorizing:
        msg = f"{REASON_NON_AUTHORIZING_REQUIRED}: non_authorizing must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if not real_metadata_source_marked:
        msg = f"{REASON_GOVERNED_MISSING_REQUIRED_FIELD}: real_metadata_source_marked must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    source_kind = _require_str(data, "source_kind")
    producer_id = _require_str(data, "producer_id")
    if source_kind in FORBIDDEN_SOURCE_KINDS or producer_id in FORBIDDEN_SOURCE_KINDS:
        msg = f"{REASON_FORBIDDEN_UPSTREAM_SOURCE}: source_kind/producer_id forbidden"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if is_forbidden_upstream_source(
        upstream_source_kind=source_kind,
        upstream_producer_id=producer_id,
    ):
        msg = f"{REASON_FORBIDDEN_UPSTREAM_SOURCE}: upstream markers forbidden"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if (
        source_kind in FORBIDDEN_UPSTREAM_SOURCE_MARKERS
        or producer_id in FORBIDDEN_UPSTREAM_SOURCE_MARKERS
    ):
        msg = f"{REASON_FORBIDDEN_UPSTREAM_SOURCE}: forbidden upstream marker"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    source_stage = _require_str(data, "source_stage").lower()
    if source_stage in FORBIDDEN_SOURCE_STAGES:
        msg = f"{REASON_FORBIDDEN_SOURCE_STAGE}: source_stage live forbidden"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    _require_str(data, "metadata_refresh_utc")
    return source_kind, producer_id


def governed_root_under(project_root: Path) -> Path:
    return (
        project_root
        / "tests"
        / "fixtures"
        / "workflow_dashboard_readmodel_v1"
        / "futures_producer_packet_governed_v1"
    )


def load_futures_producer_packet_governed(
    path: Path,
    *,
    archive_root: Path,
) -> FuturesProducerPacketGovernedBundleV1:
    """Load and validate a governed JSON bundle from an explicit path under archive_root."""
    bundle_path = path.expanduser()
    _validate_bundle_path_under_archive_root(bundle_path, archive_root)

    try:
        raw_text = bundle_path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: cannot read bundle path"
        raise FuturesProducerPacketRealMetadataSourceError(msg) from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: invalid JSON"
        raise FuturesProducerPacketRealMetadataSourceError(msg) from exc
    if not isinstance(data, dict):
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: root must be object"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    source_kind, producer_id = _validate_governed_governance(data)
    metadata_table_ref = _require_str(data, "metadata_table_ref")
    evidence_links = _parse_evidence_links(data.get("evidence_links"))
    _validate_metadata_table_ref(metadata_table_ref, archive_root)

    resolved_archive = archive_root.expanduser().resolve()
    for link in evidence_links:
        link_path = Path(link).expanduser()
        if not link_path.is_absolute():
            msg = f"{REASON_EVIDENCE_LINKS_EMPTY}: evidence link must be absolute: {link}"
            raise FuturesProducerPacketRealMetadataSourceError(msg)
        try:
            link_path.resolve().relative_to(resolved_archive)
        except ValueError as exc:
            msg = f"{REASON_EVIDENCE_LINKS_EMPTY}: evidence link outside archive root: {link}"
            raise FuturesProducerPacketRealMetadataSourceError(msg) from exc

    universe = _require_mapping(data, "universe")
    ranking = _require_mapping(data, "ranking")
    selected_future = _require_mapping(data, "selected_future")

    selected_symbol = selected_future.get("symbol")
    if isinstance(selected_symbol, str) and _is_spot_symbol(selected_symbol):
        msg = (
            f"{REASON_INELIGIBLE_SPOT_SYMBOL}: selected_future symbol forbidden: {selected_symbol}"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    packets_raw = data.get("packets")
    if packets_raw is None:
        msg = f"{REASON_GOVERNED_MISSING_REQUIRED_FIELD}: missing 'packets'"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if not isinstance(packets_raw, list) or not packets_raw:
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: 'packets' must be a non-empty array"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    candidate_validation_only, allowed_missing_provider_metadata = (
        _parse_candidate_validation_policy(data)
    )

    packets: list[FuturesProducerPacket] = []
    for item in packets_raw:
        if not isinstance(item, dict):
            msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: each packet must be an object"
            raise FuturesProducerPacketRealMetadataSourceError(msg)
        try:
            packet = _parse_packet(item)
        except FuturesProducerPacketFixtureSourceError as exc:
            raise FuturesProducerPacketRealMetadataSourceError(str(exc)) from exc
        if candidate_validation_only:
            _validate_packet_candidate_validation_eligibility(
                packet,
                item,
                allowed_missing_provider_metadata=allowed_missing_provider_metadata,
            )
        else:
            _validate_packet_eligibility(packet)
        packets.append(packet)

    selected_candidate_id = data.get("selected_candidate_id")
    if selected_candidate_id is not None and (
        not isinstance(selected_candidate_id, str) or not selected_candidate_id.strip()
    ):
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: selected_candidate_id must be non-empty string"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    return FuturesProducerPacketGovernedBundleV1(
        source_kind=source_kind,
        producer_id=producer_id,
        generated_at=_require_str(data, "generated_at"),
        source_run_id=_require_str(data, "source_run_id"),
        source_stage=_require_str(data, "source_stage"),
        fixture_only=False,
        observability_truth_allowed=False,
        non_authorizing=True,
        real_metadata_source_marked=True,
        metadata_table_ref=metadata_table_ref,
        metadata_refresh_utc=_require_str(data, "metadata_refresh_utc"),
        evidence_links=evidence_links,
        universe=universe,
        ranking=ranking,
        selected_future=selected_future,
        packets=tuple(packets),
        selected_candidate_id=selected_candidate_id.strip()
        if isinstance(selected_candidate_id, str)
        else None,
        bundle_path=str(bundle_path.resolve()),
    )


def bundle_to_upstream_input(
    bundle: FuturesProducerPacketGovernedBundleV1,
) -> FuturesUniverseUpstreamInputV1:
    """Map a validated governed bundle to U1 upstream input — never fixture_marked."""
    if bundle.observability_truth_allowed:
        msg = f"{REASON_OBSERVABILITY_TRUTH_CLAIMED}: observability truth not allowed"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    for packet in bundle.packets:
        _validate_packet_eligibility(packet)
    return FuturesUniverseUpstreamInputV1(
        source_run_id=bundle.source_run_id,
        source_stage=bundle.source_stage,
        generated_at=bundle.generated_at,
        packets=bundle.packets,
        upstream_source_kind=bundle.source_kind,
        upstream_producer_id=bundle.producer_id,
        selected_candidate_id=bundle.selected_candidate_id,
        evidence_links=bundle.evidence_links,
        fixture_marked=False,
    )


def assert_governed_not_observability_truth(bundle: FuturesProducerPacketGovernedBundleV1) -> None:
    """Fail closed when a bundle claims production observability truth."""
    if bundle.observability_truth_allowed:
        msg = f"{REASON_OBSERVABILITY_TRUTH_CLAIMED}: governed bundle must not claim observability truth"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if not bundle.non_authorizing:
        msg = f"{REASON_NON_AUTHORIZING_REQUIRED}: non_authorizing must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if not bundle.real_metadata_source_marked:
        msg = f"{REASON_GOVERNED_MISSING_REQUIRED_FIELD}: real_metadata_source_marked must be true"
        raise FuturesProducerPacketRealMetadataSourceError(msg)


LOADER_PERSIST_CONFIRM_TOKEN = "U2B_GOVERNED_SNAPSHOT_LOADER_WRITE_EXECUTE_SEPARATE_OPERATOR_GO"
LOADER_PERSIST_RECORD_SCHEMA = "loader_persist_record.v1"
LOADER_PERSIST_PRODUCER_ID = "u2b_governed_snapshot_loader_persist_v1"
REASON_CONFIRM_TOKEN_REQUIRED = "CONFIRM_TOKEN_REQUIRED"
REASON_CONFIRM_TOKEN_INVALID = "CONFIRM_TOKEN_INVALID"
REASON_OUTPUT_DIR_NOT_UNDER_ARCHIVE_ROOT = "OUTPUT_DIR_NOT_UNDER_ARCHIVE_ROOT"


def _resolve_governed_bundle_path(candidate_bundle_path: Path) -> Path:
    path = candidate_bundle_path.expanduser().resolve()
    if path.is_file():
        return path
    if path.is_dir():
        nested = path / "futures_producer_packet_governed.v1.json"
        if nested.is_file():
            return nested.resolve()
    msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: candidate bundle path not found"
    raise FuturesProducerPacketRealMetadataSourceError(msg)


def _summarize_candidate_validation(raw_packets: list[dict[str, Any]]) -> dict[str, int]:
    strict_complete = 0
    candidate_validation_complete = 0
    for packet in raw_packets:
        instrument = packet.get("instrument") or {}
        if instrument.get("complete"):
            strict_complete += 1
        if instrument.get("candidate_validation_complete"):
            candidate_validation_complete += 1
    return {
        "packet_count": len(raw_packets),
        "strict_instrument_complete_count": strict_complete,
        "candidate_validation_complete_count": candidate_validation_complete,
    }


def persist_governed_snapshot_loader_run_v1(
    *,
    confirm_token: str,
    candidate_bundle_path: Path,
    output_dir: Path,
    archive_root: Path,
    persist_bundle_id: str | None = None,
) -> dict[str, Any]:
    """Persist a durable U2b loader run record — not readmodel, dashboard, or truth."""
    if not confirm_token:
        msg = f"{REASON_CONFIRM_TOKEN_REQUIRED}: confirm token required"
        raise FuturesProducerPacketRealMetadataSourceError(msg)
    if confirm_token != LOADER_PERSIST_CONFIRM_TOKEN:
        msg = f"{REASON_CONFIRM_TOKEN_INVALID}: confirm token mismatch"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    bundle_path = _resolve_governed_bundle_path(candidate_bundle_path)
    resolved_archive = archive_root.expanduser().resolve()
    resolved_output = output_dir.expanduser().resolve()
    try:
        resolved_output.relative_to(resolved_archive)
    except ValueError as exc:
        msg = f"{REASON_OUTPUT_DIR_NOT_UNDER_ARCHIVE_ROOT}: output_dir must be under archive_root"
        raise FuturesProducerPacketRealMetadataSourceError(msg) from exc

    bundle = load_futures_producer_packet_governed(bundle_path, archive_root=resolved_archive)
    assert_governed_not_observability_truth(bundle)

    raw = json.loads(bundle_path.read_text(encoding="utf-8"))
    packets_raw = raw.get("packets") or []
    if not isinstance(packets_raw, list):
        msg = f"{REASON_GOVERNED_SCHEMA_INVALID}: packets must be array"
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    completeness = _summarize_candidate_validation(
        [item for item in packets_raw if isinstance(item, dict)]
    )
    bundle_id = persist_bundle_id or resolved_output.name
    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    resolved_output.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": LOADER_PERSIST_RECORD_SCHEMA,
        "persist_bundle_id": bundle_id,
        "producer_id": LOADER_PERSIST_PRODUCER_ID,
        "generated_at": generated_at,
        "source_candidate_bundle_path": str(bundle_path),
        "source_run_id": bundle.source_run_id,
        "source_stage": bundle.source_stage,
        "loader_persist_executed": True,
        "loader_can_parse_candidate": True,
        "observability_truth_allowed": False,
        "non_authorizing": True,
        "selected_candidate_id": bundle.selected_candidate_id,
        "completeness_summary": completeness,
        "notes": (
            "U2b governed snapshot loader persist record only — "
            "not readmodel write, dashboard wiring, truth-GO, or trading"
        ),
    }
    (resolved_output / "loader_persist_record.v1.json").write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )
    (resolved_output / "loader_safety_flags.v1.json").write_text(
        json.dumps(
            {
                "schema": "loader_safety_flags.v1",
                "LOADER_PERSIST_EXECUTED": True,
                "LOADER_RUN_EXECUTED": False,
                "READMODEL_WRITE_EXECUTED": False,
                "DASHBOARD_WIRING_EXECUTED": False,
                "TRUTH_GO_GRANTED": False,
                "LIVE_AUTHORIZED": False,
                "PREFLIGHT_LIFT_AUTHORIZED": False,
                "SELECTED_TRADABLE_FUTURE_CREATED": False,
                "NETWORK_CALL_EXECUTED": False,
                "NOT_READMODEL_WRITE": True,
                "NOT_DASHBOARD_WIRING": True,
                "NOT_TRUTH_GO": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (resolved_output / "source_candidate_bundle_ref.v1.json").write_text(
        json.dumps(
            {
                "schema": "source_candidate_bundle_ref.v1",
                "persist_bundle_id": bundle_id,
                "candidate_bundle_path": str(bundle_path),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import finalize_durable_bundle_manifest

    manifest_rc, manifest_msg = finalize_durable_bundle_manifest(resolved_output)
    if manifest_rc != 0:
        msg = (
            f"{REASON_MANIFEST_VERIFY_FAILED}: manifest finalize rc={manifest_rc} ({manifest_msg})"
        )
        raise FuturesProducerPacketRealMetadataSourceError(msg)

    return {
        "persist_bundle_id": bundle_id,
        "output_dir": str(resolved_output),
        "manifest_verify_rc": manifest_rc,
        "completeness_summary": completeness,
        "selected_candidate_id": bundle.selected_candidate_id,
    }
