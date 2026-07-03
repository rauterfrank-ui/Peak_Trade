"""Production materialization for point-in-time OKX futures universe manifest v1.

Research-only, non-authorizing. Pure offline binding: no I/O, no network, no clock.
Wires ratified universe policy, OKX production lifecycle registry, PT1H panel
supplementary market data, and registry consumer binding into a validated manifest.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.okx_production_instrument_lifecycle_source_v1 import (
    SOURCE_ID as OKX_PRODUCTION_LIFECYCLE_SOURCE_ID,
    UNIVERSE_POLICY_ID as RATIFIED_UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION as RATIFIED_UNIVERSE_POLICY_VERSION,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1,
    RegistrySnapshotV1,
    SourceObservationRecordV1,
    _REGISTERED_SOURCES_V0,
    assemble_registry_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    ValidationVerdict as RegistryValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)
from src.research.pit_futures_universe_manifest_generator_registry_consumer_binding_v1 import (
    BINDING_INPUT_CONTRACT_VERSION,
    BINDING_VERSION,
    PitFuturesUniverseManifestGeneratorRegistryBindingInputV1,
    PitFuturesUniverseManifestGeneratorRegistryBindingResultV1,
    RegistryBoundEpochInputV1,
    SupplementaryInstrumentMarketDataV1,
    compute_binding_implementation_digest,
    generate_pit_futures_universe_manifest_from_registry_binding_v1,
)
from src.research.pit_futures_universe_manifest_generator_v1 import (
    GENERATOR_VERSION,
    INPUT_CONTRACT_VERSION as GENERATOR_INPUT_CONTRACT_VERSION,
    PitFuturesUniverseManifestGeneratorInputV1,
    compute_generator_config_digest,
    compute_generator_implementation_digest,
)
from src.research.pit_futures_universe_manifest_v1 import (
    PointInTimeFuturesUniverseManifestV1,
    compute_sha256_digest,
    is_valid_digest,
    is_valid_rfc3339_utc,
    manifest_to_dict,
)
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidationVerdict as ManifestValidationVerdict,
    validate_pit_futures_universe_manifest_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    BAR_GRANULARITY,
    InstrumentPanelSeriesV1,
)

PACKAGE_MARKER = "PIT_FUTURES_UNIVERSE_MANIFEST_PRODUCTION_MATERIALIZATION_V1=true"
MATERIALIZATION_VERSION = "pit_futures_universe_manifest_production_materialization.v1"
INPUT_CONTRACT_VERSION = "pit_futures_universe_manifest_production_materialization_input.v1"
MODULE_NAME = "pit_futures_universe_manifest_production_materialization_v1"
POLICY_CONFIG_REL_PATH = (
    "config/research/pit_futures_universe_manifest_production_materialization_policy_v1.json"
)

UNIVERSE_POLICY_ID = RATIFIED_UNIVERSE_POLICY_ID
UNIVERSE_POLICY_VERSION = RATIFIED_UNIVERSE_POLICY_VERSION
INCLUSION_POLICY_VERSION = "pit_okx_linear_usdt_non_bitcoin_perpetual_inclusion.v1"
EXCLUSION_POLICY_VERSION = "pit_okx_linear_usdt_non_bitcoin_perpetual_exclusion.v1"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False
PERPETUAL_ONLY = True
LINEAR_CONTRACT = True

VENUE_ID = "okx"
VENUE_FAMILY = "okx_linear_usdt_perpetuals"
VENUE_SCOPE = ("okx",)
MARKET_TYPE = "futures"
CONTRACT_TYPE = "linear_perpetual"
SETTLEMENT_ASSET = "USDT"
QUOTE_ASSET = "USDT"

REGISTRY_ARTIFACT_ID = "okx_production_lifecycle_v1"
MANIFEST_ARTIFACT_ID = "pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1"
UNIVERSE_ID = "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe_v1"
HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"
BAR_INTERVAL = BAR_GRANULARITY
DEFAULT_MINIMUM_HISTORY_BARS = 21
DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT = 5
EVALUATION_PERIOD_BINDING = "pit_cross_sectional_panel_common_coverage_period.v1"

_CURRENT_STATE_FALLBACK_MARKERS = frozenset(
    {"current_state", "use_current_state", "fallback_to_current", "now()", "latest"}
)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")


class ProductionMaterializationErrorCode(str, Enum):
    INVALID_INPUT_CONTRACT = "INVALID_INPUT_CONTRACT"
    UNKNOWN_UNIVERSE_POLICY = "UNKNOWN_UNIVERSE_POLICY"
    UNKNOWN_UNIVERSE_POLICY_VERSION = "UNKNOWN_UNIVERSE_POLICY_VERSION"
    UNKNOWN_INCLUSION_POLICY_VERSION = "UNKNOWN_INCLUSION_POLICY_VERSION"
    UNKNOWN_EXCLUSION_POLICY_VERSION = "UNKNOWN_EXCLUSION_POLICY_VERSION"
    UNREGISTERED_LIFECYCLE_SOURCE = "UNREGISTERED_LIFECYCLE_SOURCE"
    REGISTRY_ASSEMBLY_FAILED = "REGISTRY_ASSEMBLY_FAILED"
    REGISTRY_VALIDATION_FAILED = "REGISTRY_VALIDATION_FAILED"
    INSUFFICIENT_PANEL_INSTRUMENTS = "INSUFFICIENT_PANEL_INSTRUMENTS"
    PANEL_INSTRUMENT_NOT_IN_REGISTRY = "PANEL_INSTRUMENT_NOT_IN_REGISTRY"
    CURRENT_STATE_FALLBACK_BLOCKED = "CURRENT_STATE_FALLBACK_BLOCKED"
    BINDING_FAILED = "BINDING_FAILED"
    MANIFEST_VALIDATION_FAILED = "MANIFEST_VALIDATION_FAILED"
    INSUFFICIENT_ELIGIBLE_INSTRUMENTS = "INSUFFICIENT_ELIGIBLE_INSTRUMENTS"


@dataclass(frozen=True)
class ProductionMaterializationEpochV1:
    score_epoch: int
    finalized_bar_close: str


@dataclass(frozen=True)
class PitFuturesUniverseManifestProductionMaterializationInputV1:
    input_contract_version: str
    materialization_version: str
    generated_at: str
    universe_policy_id: str
    universe_policy_version: str
    inclusion_policy_version: str
    exclusion_policy_version: str
    lifecycle_source_id: str
    lifecycle_source_snapshot_ref: str
    lifecycle_source_snapshot_digest: str
    registry_artifact_id: str
    registry_snapshot: RegistrySnapshotV1
    panel_series: tuple[InstrumentPanelSeriesV1, ...]
    panel_dataset_ref: str
    panel_dataset_digest: str
    period_binding_ref: str
    period_start_utc: str
    period_end_utc: str
    minimum_history_bars: int
    minimum_required_member_count: int
    registry_config_digest: str
    registry_implementation_digest: str
    epochs: tuple[ProductionMaterializationEpochV1, ...]


@dataclass(frozen=True)
class ProductionManifestMaterializationEnvelopeV1:
    materialization_version: str
    universe_policy_id: str
    universe_policy_version: str
    inclusion_policy_version: str
    exclusion_policy_version: str
    venue_id: str
    venue_family: str
    market_type: str
    settlement_asset: str
    quote_asset: str
    contract_type: str
    perpetual_only: bool
    linear_contract: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    spot_allowed: bool
    synthetic_spot_allowed: bool
    instrument_metadata_source_id: str
    lifecycle_source_snapshot_ref: str
    lifecycle_source_snapshot_digest: str
    registry_reference: str
    registry_snapshot_digest: str
    panel_dataset_ref: str
    panel_dataset_digest: str
    period_binding_ref: str
    period_start_utc: str
    period_end_utc: str
    materialization_config_digest: str
    materialization_implementation_digest: str
    binding_implementation_digest: str
    reproducibility_inputs_digest: str
    manifest_reference: str | None
    manifest_digest: str | None
    generated_at: str
    eligible_instrument_count: int
    excluded_instrument_count: int
    pit_semantics_enforced: bool
    non_authorizing: bool
    no_runtime_effect: bool


@dataclass(frozen=True)
class PitFuturesUniverseManifestProductionMaterializationResultV1:
    success: bool
    manifest: PointInTimeFuturesUniverseManifestV1 | None
    envelope: ProductionManifestMaterializationEnvelopeV1 | None
    binding_result: PitFuturesUniverseManifestGeneratorRegistryBindingResultV1 | None
    error_codes: tuple[str, ...]
    binding_error_codes: tuple[str, ...] = ()
    validator_reason_codes: tuple[str, ...] = ()


def _add(errors: list[str], code: ProductionMaterializationErrorCode) -> None:
    value = code.value
    if value not in errors:
        errors.append(value)


def _validate_ref(value: str, errors: list[str]) -> bool:
    if not value.strip():
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
        return False
    if _ABSOLUTE_PATH_PATTERN.search(value):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
        return False
    lowered = value.strip().lower()
    for marker in _CURRENT_STATE_FALLBACK_MARKERS:
        if marker in lowered:
            _add(errors, ProductionMaterializationErrorCode.CURRENT_STATE_FALLBACK_BLOCKED)
            return False
    return True


def compute_materialization_config_digest_payload() -> dict[str, Any]:
    return {
        "bar_interval": BAR_INTERVAL,
        "exclusion_policy_version": EXCLUSION_POLICY_VERSION,
        "futures_only": FUTURES_ONLY,
        "inclusion_policy_version": INCLUSION_POLICY_VERSION,
        "lifecycle_source_id": OKX_PRODUCTION_LIFECYCLE_SOURCE_ID,
        "manifest_artifact_id": MANIFEST_ARTIFACT_ID,
        "minimum_history_bars": DEFAULT_MINIMUM_HISTORY_BARS,
        "minimum_required_member_count": DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT,
        "universe_policy_id": UNIVERSE_POLICY_ID,
        "universe_policy_version": UNIVERSE_POLICY_VERSION,
        "venue_family": VENUE_FAMILY,
        "venue_id": VENUE_ID,
        "venue_scope": list(VENUE_SCOPE),
    }


def compute_materialization_config_digest() -> str:
    return compute_sha256_digest(compute_materialization_config_digest_payload())


def compute_materialization_implementation_digest() -> str:
    return compute_sha256_digest(
        {
            "materialization_version": MATERIALIZATION_VERSION,
            "module": MODULE_NAME,
        }
    )


def compute_reproducibility_inputs_digest(
    inp: PitFuturesUniverseManifestProductionMaterializationInputV1,
) -> str:
    return compute_sha256_digest(
        {
            "epochs": [
                {
                    "finalized_bar_close": epoch.finalized_bar_close,
                    "score_epoch": epoch.score_epoch,
                }
                for epoch in sorted(inp.epochs, key=lambda item: item.score_epoch)
            ],
            "generated_at": inp.generated_at,
            "lifecycle_source_snapshot_digest": inp.lifecycle_source_snapshot_digest,
            "panel_dataset_digest": inp.panel_dataset_digest,
            "registry_snapshot_digest": inp.registry_snapshot.registry_snapshot_digest,
            "universe_policy_id": inp.universe_policy_id,
            "universe_policy_version": inp.universe_policy_version,
        }
    )


def _validate_ratified_policy(
    inp: PitFuturesUniverseManifestProductionMaterializationInputV1,
) -> list[str]:
    errors: list[str] = []
    if inp.input_contract_version != INPUT_CONTRACT_VERSION:
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if inp.materialization_version != MATERIALIZATION_VERSION:
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if not is_valid_rfc3339_utc(inp.generated_at):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if inp.universe_policy_id != UNIVERSE_POLICY_ID:
        _add(errors, ProductionMaterializationErrorCode.UNKNOWN_UNIVERSE_POLICY)
    if inp.universe_policy_version != UNIVERSE_POLICY_VERSION:
        _add(errors, ProductionMaterializationErrorCode.UNKNOWN_UNIVERSE_POLICY_VERSION)
    if inp.inclusion_policy_version != INCLUSION_POLICY_VERSION:
        _add(errors, ProductionMaterializationErrorCode.UNKNOWN_INCLUSION_POLICY_VERSION)
    if inp.exclusion_policy_version != EXCLUSION_POLICY_VERSION:
        _add(errors, ProductionMaterializationErrorCode.UNKNOWN_EXCLUSION_POLICY_VERSION)
    if inp.lifecycle_source_id != OKX_PRODUCTION_LIFECYCLE_SOURCE_ID:
        _add(errors, ProductionMaterializationErrorCode.UNREGISTERED_LIFECYCLE_SOURCE)
    elif inp.lifecycle_source_id not in _REGISTERED_SOURCES_V0:
        _add(errors, ProductionMaterializationErrorCode.UNREGISTERED_LIFECYCLE_SOURCE)
    if inp.registry_artifact_id != REGISTRY_ARTIFACT_ID:
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if inp.minimum_history_bars <= 0:
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if inp.minimum_required_member_count < DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT:
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if not is_valid_digest(inp.lifecycle_source_snapshot_digest.strip().lower()):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if not is_valid_digest(inp.panel_dataset_digest.strip().lower()):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if not is_valid_digest(inp.registry_config_digest.strip().lower()):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if not is_valid_digest(inp.registry_implementation_digest.strip().lower()):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    for ref in (
        inp.lifecycle_source_snapshot_ref,
        inp.panel_dataset_ref,
        inp.period_binding_ref,
    ):
        _validate_ref(ref, errors)
    if not is_valid_rfc3339_utc(inp.period_start_utc):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if not is_valid_rfc3339_utc(inp.period_end_utc):
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if not inp.epochs:
        _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    for epoch in inp.epochs:
        if not is_valid_rfc3339_utc(epoch.finalized_bar_close):
            _add(errors, ProductionMaterializationErrorCode.INVALID_INPUT_CONTRACT)
    if len(inp.panel_series) < inp.minimum_required_member_count:
        _add(errors, ProductionMaterializationErrorCode.INSUFFICIENT_PANEL_INSTRUMENTS)
    return sorted(errors)


def _count_final_bars_at_or_before(series: InstrumentPanelSeriesV1, as_of: str) -> int:
    return sum(1 for bar in series.bars if bar.is_final and bar.timestamp_utc <= as_of)


def _data_availability_status(*, history_bars_available: int, required_history_bars: int) -> str:
    if history_bars_available >= required_history_bars:
        return "AVAILABLE"
    if history_bars_available > 0:
        return "PARTIAL"
    return "UNAVAILABLE"


def build_supplementary_market_data_from_panel_v1(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    finalized_bar_close: str,
    minimum_history_bars: int,
    panel_dataset_ref: str,
) -> tuple[SupplementaryInstrumentMarketDataV1, ...]:
    """Derive registry-binding supplementary market data from PT1H panel series."""
    items: list[tuple[str, SupplementaryInstrumentMarketDataV1]] = []
    for series in panel_series:
        history = _count_final_bars_at_or_before(series, finalized_bar_close)
        record_digest = compute_sha256_digest(
            {
                "finalized_bar_close": finalized_bar_close,
                "history_bars_available": history,
                "instrument_id": series.instrument_id,
                "panel_dataset_ref": panel_dataset_ref.strip(),
            }
        )
        items.append(
            (
                series.instrument_id,
                SupplementaryInstrumentMarketDataV1(
                    instrument_id=series.instrument_id,
                    source_ref=panel_dataset_ref.strip(),
                    record_digest=record_digest,
                    market_type=MARKET_TYPE,
                    history_bars_available=history,
                    required_history_bars=minimum_history_bars,
                    data_availability_status=_data_availability_status(
                        history_bars_available=history,
                        required_history_bars=minimum_history_bars,
                    ),
                ),
            )
        )
    return tuple(item for _, item in sorted(items, key=lambda row: row[0]))


def assemble_production_registry_from_observations_v1(
    observations: Sequence[SourceObservationRecordV1],
    *,
    generated_at: str,
    lifecycle_source_snapshot_digest: str,
    config_digest: str,
    implementation_digest: str,
) -> tuple[RegistrySnapshotV1 | None, tuple[str, ...]]:
    assembly = assemble_registry_snapshot_v1(
        observations,
        generated_at=generated_at,
        venue_scope=VENUE_SCOPE,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        registered_sources=frozenset({OKX_PRODUCTION_LIFECYCLE_SOURCE_ID}),
        approved_snapshot_digests=frozenset({lifecycle_source_snapshot_digest.strip().lower()}),
    )
    if not assembly.success or assembly.snapshot is None:
        return None, tuple(sorted({issue.error_code for issue in assembly.issues}))
    validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(assembly.snapshot)
    if validation.verdict != RegistryValidationVerdict.ACCEPTED:
        return None, (ProductionMaterializationErrorCode.REGISTRY_VALIDATION_FAILED.value,)
    return assembly.snapshot, ()


def materialize_production_pit_futures_universe_manifest_v1(
    inp: PitFuturesUniverseManifestProductionMaterializationInputV1,
) -> PitFuturesUniverseManifestProductionMaterializationResultV1:
    """Materialize a validated production universe manifest from explicit offline inputs."""
    errors = _validate_ratified_policy(inp)
    if errors:
        return PitFuturesUniverseManifestProductionMaterializationResultV1(
            False, None, None, None, tuple(errors)
        )

    snapshot = inp.registry_snapshot
    registry_validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot)
    if registry_validation.verdict != RegistryValidationVerdict.ACCEPTED:
        return PitFuturesUniverseManifestProductionMaterializationResultV1(
            False,
            None,
            None,
            None,
            (ProductionMaterializationErrorCode.REGISTRY_VALIDATION_FAILED.value,),
        )

    active_ids = {
        interval.instrument_id
        for interval in snapshot.intervals
        if interval.superseded_by_version is None
    }
    panel_ids = {series.instrument_id for series in inp.panel_series}
    if not panel_ids.issuperset(active_ids):
        return PitFuturesUniverseManifestProductionMaterializationResultV1(
            False,
            None,
            None,
            None,
            (ProductionMaterializationErrorCode.PANEL_INSTRUMENT_NOT_IN_REGISTRY.value,),
        )

    first_epoch = sorted(inp.epochs, key=lambda item: item.score_epoch)[0]
    supplementary = build_supplementary_market_data_from_panel_v1(
        inp.panel_series,
        finalized_bar_close=first_epoch.finalized_bar_close,
        minimum_history_bars=inp.minimum_history_bars,
        panel_dataset_ref=inp.panel_dataset_ref,
    )

    gen_partial = PitFuturesUniverseManifestGeneratorInputV1(
        input_contract_version=GENERATOR_INPUT_CONTRACT_VERSION,
        artifact_id=MANIFEST_ARTIFACT_ID,
        venue_id=VENUE_ID,
        universe_id=UNIVERSE_ID,
        hypothesis_id=HYPOTHESIS_ID,
        universe_policy_id=inp.universe_policy_id,
        universe_policy_version=inp.universe_policy_version,
        inclusion_policy_version=inp.inclusion_policy_version,
        exclusion_policy_version=inp.exclusion_policy_version,
        generator_version=GENERATOR_VERSION,
        generated_at=inp.generated_at,
        bar_interval=BAR_INTERVAL,
        minimum_history_bars=inp.minimum_history_bars,
        minimum_required_member_count=inp.minimum_required_member_count,
        venue_scope=VENUE_SCOPE,
        source_snapshot_refs=(inp.panel_dataset_ref.strip(),),
        source_digests=(inp.panel_dataset_digest.strip().lower(),),
        period_binding_ref=inp.period_binding_ref.strip(),
        config_digest="0" * 64,
        implementation_digest="0" * 64,
        epochs=(),
    )
    config_digest = compute_generator_config_digest(gen_partial)
    implementation_digest = compute_generator_implementation_digest()

    binding_epochs = tuple(
        RegistryBoundEpochInputV1(
            score_epoch=epoch.score_epoch,
            finalized_bar_close=epoch.finalized_bar_close,
            historical_as_of_time=epoch.finalized_bar_close,
        )
        for epoch in sorted(inp.epochs, key=lambda item: item.score_epoch)
    )
    binding_input = PitFuturesUniverseManifestGeneratorRegistryBindingInputV1(
        binding_input_contract_version=BINDING_INPUT_CONTRACT_VERSION,
        binding_version=BINDING_VERSION,
        registry_artifact_id=inp.registry_artifact_id.strip(),
        bound_registry_schema_version=snapshot.schema_version,
        bound_registry_snapshot_version=snapshot.registry_snapshot_version,
        bound_registry_snapshot_digest=snapshot.registry_snapshot_digest,
        registry_snapshot=snapshot,
        input_contract_version=GENERATOR_INPUT_CONTRACT_VERSION,
        artifact_id=MANIFEST_ARTIFACT_ID,
        venue_id=VENUE_ID,
        universe_id=UNIVERSE_ID,
        hypothesis_id=HYPOTHESIS_ID,
        universe_policy_id=inp.universe_policy_id,
        universe_policy_version=inp.universe_policy_version,
        inclusion_policy_version=inp.inclusion_policy_version,
        exclusion_policy_version=inp.exclusion_policy_version,
        generator_version=GENERATOR_VERSION,
        generated_at=inp.generated_at,
        bar_interval=BAR_INTERVAL,
        minimum_history_bars=inp.minimum_history_bars,
        minimum_required_member_count=inp.minimum_required_member_count,
        venue_scope=VENUE_SCOPE,
        source_snapshot_refs=(inp.panel_dataset_ref.strip(),),
        source_digests=(inp.panel_dataset_digest.strip().lower(),),
        period_binding_ref=inp.period_binding_ref.strip(),
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        supplementary_market_data=supplementary,
        epochs=binding_epochs,
    )

    binding_result = generate_pit_futures_universe_manifest_from_registry_binding_v1(binding_input)
    if not binding_result.success or binding_result.manifest is None:
        return PitFuturesUniverseManifestProductionMaterializationResultV1(
            False,
            None,
            None,
            binding_result,
            (ProductionMaterializationErrorCode.BINDING_FAILED.value,),
            binding_result.error_codes,
            binding_result.validator_reason_codes,
        )

    manifest = binding_result.manifest
    manifest_validation = validate_pit_futures_universe_manifest_v1(manifest)
    if manifest_validation.verdict != ManifestValidationVerdict.ACCEPTED:
        return PitFuturesUniverseManifestProductionMaterializationResultV1(
            False,
            manifest,
            None,
            binding_result,
            (ProductionMaterializationErrorCode.MANIFEST_VALIDATION_FAILED.value,),
            binding_result.error_codes,
            manifest_validation.reason_codes,
        )

    epoch0 = manifest.epochs[0]
    if epoch0.eligible_member_count < inp.minimum_required_member_count:
        return PitFuturesUniverseManifestProductionMaterializationResultV1(
            False,
            manifest,
            None,
            binding_result,
            (ProductionMaterializationErrorCode.INSUFFICIENT_ELIGIBLE_INSTRUMENTS.value,),
            binding_result.error_codes,
            binding_result.validator_reason_codes,
        )

    provenance_ref = ""
    if binding_result.provenance is not None:
        provenance_ref = binding_result.provenance.registry_reference
    envelope = ProductionManifestMaterializationEnvelopeV1(
        materialization_version=MATERIALIZATION_VERSION,
        universe_policy_id=manifest.universe_policy_id,
        universe_policy_version=manifest.universe_policy_version,
        inclusion_policy_version=inp.inclusion_policy_version,
        exclusion_policy_version=inp.exclusion_policy_version,
        venue_id=VENUE_ID,
        venue_family=VENUE_FAMILY,
        market_type=manifest.market_type,
        settlement_asset=SETTLEMENT_ASSET,
        quote_asset=QUOTE_ASSET,
        contract_type=CONTRACT_TYPE,
        perpetual_only=PERPETUAL_ONLY,
        linear_contract=LINEAR_CONTRACT,
        futures_only=manifest.futures_only,
        bitcoin_direction_allowed=manifest.bitcoin_direction_allowed,
        spot_allowed=manifest.spot_allowed,
        synthetic_spot_allowed=manifest.synthetic_spot_allowed,
        instrument_metadata_source_id=OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1,
        lifecycle_source_snapshot_ref=inp.lifecycle_source_snapshot_ref.strip(),
        lifecycle_source_snapshot_digest=inp.lifecycle_source_snapshot_digest.strip().lower(),
        registry_reference=provenance_ref,
        registry_snapshot_digest=snapshot.registry_snapshot_digest,
        panel_dataset_ref=inp.panel_dataset_ref.strip(),
        panel_dataset_digest=inp.panel_dataset_digest.strip().lower(),
        period_binding_ref=inp.period_binding_ref.strip(),
        period_start_utc=inp.period_start_utc,
        period_end_utc=inp.period_end_utc,
        materialization_config_digest=compute_materialization_config_digest(),
        materialization_implementation_digest=compute_materialization_implementation_digest(),
        binding_implementation_digest=compute_binding_implementation_digest(),
        reproducibility_inputs_digest=compute_reproducibility_inputs_digest(inp),
        manifest_reference=binding_result.manifest_reference,
        manifest_digest=manifest.manifest_digest,
        generated_at=inp.generated_at,
        eligible_instrument_count=epoch0.eligible_member_count,
        excluded_instrument_count=len(epoch0.excluded_members),
        pit_semantics_enforced=True,
        non_authorizing=True,
        no_runtime_effect=True,
    )

    return PitFuturesUniverseManifestProductionMaterializationResultV1(
        True,
        manifest,
        envelope,
        binding_result,
        (),
        binding_result.error_codes,
        binding_result.validator_reason_codes,
    )


def production_materialization_envelope_to_dict(
    envelope: ProductionManifestMaterializationEnvelopeV1,
) -> dict[str, Any]:
    return {
        "bitcoin_direction_allowed": envelope.bitcoin_direction_allowed,
        "binding_implementation_digest": envelope.binding_implementation_digest,
        "contract_type": envelope.contract_type,
        "eligible_instrument_count": envelope.eligible_instrument_count,
        "excluded_instrument_count": envelope.excluded_instrument_count,
        "exclusion_policy_version": envelope.exclusion_policy_version,
        "futures_only": envelope.futures_only,
        "generated_at": envelope.generated_at,
        "inclusion_policy_version": envelope.inclusion_policy_version,
        "instrument_metadata_source_id": envelope.instrument_metadata_source_id,
        "lifecycle_source_snapshot_digest": envelope.lifecycle_source_snapshot_digest,
        "lifecycle_source_snapshot_ref": envelope.lifecycle_source_snapshot_ref,
        "linear_contract": envelope.linear_contract,
        "manifest_digest": envelope.manifest_digest,
        "manifest_reference": envelope.manifest_reference,
        "market_type": envelope.market_type,
        "materialization_config_digest": envelope.materialization_config_digest,
        "materialization_implementation_digest": envelope.materialization_implementation_digest,
        "materialization_version": envelope.materialization_version,
        "no_runtime_effect": envelope.no_runtime_effect,
        "non_authorizing": envelope.non_authorizing,
        "panel_dataset_digest": envelope.panel_dataset_digest,
        "panel_dataset_ref": envelope.panel_dataset_ref,
        "period_binding_ref": envelope.period_binding_ref,
        "period_end_utc": envelope.period_end_utc,
        "period_start_utc": envelope.period_start_utc,
        "perpetual_only": envelope.perpetual_only,
        "pit_semantics_enforced": envelope.pit_semantics_enforced,
        "quote_asset": envelope.quote_asset,
        "registry_reference": envelope.registry_reference,
        "registry_snapshot_digest": envelope.registry_snapshot_digest,
        "reproducibility_inputs_digest": envelope.reproducibility_inputs_digest,
        "settlement_asset": envelope.settlement_asset,
        "spot_allowed": envelope.spot_allowed,
        "synthetic_spot_allowed": envelope.synthetic_spot_allowed,
        "universe_policy_id": envelope.universe_policy_id,
        "universe_policy_version": envelope.universe_policy_version,
        "venue_family": envelope.venue_family,
        "venue_id": envelope.venue_id,
    }


def production_materialization_result_to_dict(
    result: PitFuturesUniverseManifestProductionMaterializationResultV1,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error_codes": list(result.error_codes),
        "success": result.success,
    }
    if result.envelope is not None:
        payload["envelope"] = production_materialization_envelope_to_dict(result.envelope)
    if result.manifest is not None:
        payload["manifest"] = manifest_to_dict(result.manifest)
    return payload


__all__ = [
    "BAR_INTERVAL",
    "BITCOIN_DIRECTION_ALLOWED",
    "CONTRACT_TYPE",
    "DEFAULT_MINIMUM_HISTORY_BARS",
    "DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT",
    "EVALUATION_PERIOD_BINDING",
    "EXCLUSION_POLICY_VERSION",
    "FUTURES_ONLY",
    "HYPOTHESIS_ID",
    "INCLUSION_POLICY_VERSION",
    "INPUT_CONTRACT_VERSION",
    "LINEAR_CONTRACT",
    "MANIFEST_ARTIFACT_ID",
    "MARKET_TYPE",
    "MATERIALIZATION_VERSION",
    "PERPETUAL_ONLY",
    "POLICY_CONFIG_REL_PATH",
    "ProductionManifestMaterializationEnvelopeV1",
    "ProductionMaterializationEpochV1",
    "ProductionMaterializationErrorCode",
    "PitFuturesUniverseManifestProductionMaterializationInputV1",
    "PitFuturesUniverseManifestProductionMaterializationResultV1",
    "QUOTE_ASSET",
    "REGISTRY_ARTIFACT_ID",
    "SETTLEMENT_ASSET",
    "SPOT_ALLOWED",
    "SYNTHETIC_SPOT_ALLOWED",
    "UNIVERSE_ID",
    "UNIVERSE_POLICY_ID",
    "UNIVERSE_POLICY_VERSION",
    "VENUE_FAMILY",
    "VENUE_ID",
    "VENUE_SCOPE",
    "assemble_production_registry_from_observations_v1",
    "build_supplementary_market_data_from_panel_v1",
    "compute_materialization_config_digest",
    "compute_materialization_implementation_digest",
    "compute_reproducibility_inputs_digest",
    "materialize_production_pit_futures_universe_manifest_v1",
    "production_materialization_envelope_to_dict",
    "production_materialization_result_to_dict",
]
