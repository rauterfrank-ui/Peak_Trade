"""Contract tests for pit_futures_universe_manifest_generator_v1."""

from __future__ import annotations

import dataclasses
from typing import Callable

import pytest

from src.execution.replay_pack.canonical import dumps_canonical
from src.research.pit_futures_universe_manifest_v1 import (
    EXCLUSION_REASON_CODES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    compute_manifest_digest,
    compute_membership_digest,
    manifest_from_dict,
    manifest_to_dict,
    parse_pit_universe_manifest_reference_v1,
)
from src.research.pit_futures_universe_manifest_generator_v1 import (
    GENERATOR_VERSION,
    INPUT_CONTRACT_VERSION,
    GeneratorErrorCode,
    GeneratorEpochInputV1,
    PitFuturesUniverseManifestGeneratorInputV1,
    RawInstrumentRecordV1,
    compute_generator_config_digest,
    compute_generator_implementation_digest,
    generate_pit_futures_universe_manifest_v1,
)
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_universe_manifest_v1,
)

_SOURCE_REF = "synthetic:generator:test:record:v0"
_DATASET_REF = "synthetic:generator:dataset:v0"
_PERIOD_REF = "synthetic:generator:period:v0"
_GENERATED_AT = "2026-07-03T00:00:00Z"
_BAR_CLOSE_0 = "2024-06-01T01:00:00Z"
_BAR_CLOSE_1 = "2024-06-01T02:00:00Z"
_LISTING = "2024-01-01T00:00:00Z"
_MIN_HISTORY = 21


def _record_digest(payload: dict[str, object]) -> str:
    from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest

    return compute_sha256_digest(payload)


def _base_record(
    *,
    venue_id: str = "okx",
    market_type: str = "futures",
    contract_type: str = "linear_perpetual",
    base_asset: str = "ETH",
    venue_symbol: str = "ETH-USDT-SWAP",
    native_instrument_id: str | None = None,
    contract_expiry: str | None = None,
    listing_time: str = _LISTING,
    delisting_time: str | None = None,
    eligible_from: str = _LISTING,
    eligible_until: str | None = None,
    expiry_time: str | None = None,
    history_bars_available: int = 30,
    source_ref: str = _SOURCE_REF,
    digest_suffix: str = "eth",
) -> RawInstrumentRecordV1:
    payload = {
        "base_asset": base_asset,
        "contract_type": contract_type,
        "digest_suffix": digest_suffix,
        "source_ref": source_ref,
        "venue_id": venue_id,
        "venue_symbol": venue_symbol,
    }
    return RawInstrumentRecordV1(
        source_ref=source_ref,
        record_digest=_record_digest(payload),
        venue_id=venue_id,
        market_type=market_type,
        contract_type=contract_type,
        base_asset=base_asset,
        quote_asset="USDT",
        settlement_asset="USDT",
        venue_symbol=venue_symbol,
        native_instrument_id=native_instrument_id,
        contract_expiry=contract_expiry,
        listing_time=listing_time,
        delisting_time=delisting_time,
        eligible_from=eligible_from,
        eligible_until=eligible_until,
        expiry_time=expiry_time,
        history_bars_available=history_bars_available,
        required_history_bars=_MIN_HISTORY,
        data_availability_status="AVAILABLE",
    )


def _eligible_panel() -> tuple[RawInstrumentRecordV1, ...]:
    specs = [
        ("ETH", "ETH-USDT-SWAP", "eth"),
        ("SOL", "SOL-USDT-SWAP", "sol"),
        ("AVAX", "AVAX-USDT-SWAP", "avax"),
        ("LINK", "LINK-USDT-SWAP", "link"),
        ("DOT", "DOT-USDT-SWAP", "dot"),
        ("ADA", "ADAUSDT", "ada", "binance_usdm"),
    ]
    records = []
    for item in specs:
        base = item[0]
        symbol = item[1]
        suffix = item[2]
        venue = item[3] if len(item) > 3 else "okx"
        records.append(
            _base_record(
                venue_id=venue,
                base_asset=base,
                venue_symbol=symbol,
                digest_suffix=suffix,
                source_ref=f"{_SOURCE_REF}:{suffix}",
            )
        )
    return tuple(records)


def _build_input(
    *,
    epochs: tuple[GeneratorEpochInputV1, ...] | None = None,
    artifact_id: str = "synthetic_pit_generator_manifest_v0",
    generated_at: str = _GENERATED_AT,
    config_digest: str | None = None,
    implementation_digest: str | None = None,
) -> PitFuturesUniverseManifestGeneratorInputV1:
    if epochs is None:
        epochs = (
            GeneratorEpochInputV1(
                score_epoch=0,
                finalized_bar_close=_BAR_CLOSE_0,
                raw_instrument_records=_eligible_panel(),
            ),
        )
    partial = PitFuturesUniverseManifestGeneratorInputV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        artifact_id=artifact_id,
        venue_id="okx",
        universe_id="synthetic_universe_v0",
        hypothesis_id="CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0",
        universe_policy_id="synthetic_cross_sectional_okx_non_btc_perp_v0",
        universe_policy_version="v0",
        inclusion_policy_version="v0",
        exclusion_policy_version="v0",
        generator_version=GENERATOR_VERSION,
        generated_at=generated_at,
        bar_interval="PT1H",
        minimum_history_bars=_MIN_HISTORY,
        minimum_required_member_count=5,
        venue_scope=("binance_usdm", "okx"),
        source_snapshot_refs=(_DATASET_REF,),
        source_digests=(_record_digest({"source_dataset_refs": [_DATASET_REF]}),),
        period_binding_ref=_PERIOD_REF,
        config_digest="0" * 64,
        implementation_digest="0" * 64,
        epochs=epochs,
    )
    resolved_config = config_digest or compute_generator_config_digest(partial)
    resolved_impl = implementation_digest or compute_generator_implementation_digest()
    return dataclasses.replace(
        partial,
        config_digest=resolved_config,
        implementation_digest=resolved_impl,
    )


def test_happy_path_full_validator_acceptance() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.success is True
    assert result.manifest is not None
    assert result.error_codes == ()
    assert result.manifest_reference is not None
    validation = validate_pit_futures_universe_manifest_v1(result.manifest)
    assert validation.verdict == ValidationVerdict.ACCEPTED


def test_input_contract_is_immutable_dataclass() -> None:
    inp = _build_input()
    with pytest.raises(dataclasses.FrozenInstanceError):
        inp.artifact_id = "mutated"  # type: ignore[misc]


@pytest.mark.parametrize(
    "mutator",
    [
        lambda inp: dataclasses.replace(inp, input_contract_version="wrong"),
        lambda inp: dataclasses.replace(inp, generator_version="wrong"),
        lambda inp: dataclasses.replace(inp, artifact_id=""),
        lambda inp: dataclasses.replace(inp, generated_at="not-a-time"),
        lambda inp: dataclasses.replace(inp, minimum_history_bars=0),
        lambda inp: dataclasses.replace(inp, minimum_required_member_count=4),
        lambda inp: dataclasses.replace(inp, config_digest="bad"),
    ],
)
def test_missing_or_invalid_required_fields_fail_closed(
    mutator: Callable[
        [PitFuturesUniverseManifestGeneratorInputV1], PitFuturesUniverseManifestGeneratorInputV1
    ],
) -> None:
    result = generate_pit_futures_universe_manifest_v1(mutator(_build_input()))
    assert result.success is False
    assert result.manifest is None
    assert GeneratorErrorCode.INVALID_INPUT_CONTRACT.value in result.error_codes


def test_empty_epochs_fail_closed() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input(epochs=()))
    assert result.success is False
    assert GeneratorErrorCode.EMPTY_EPOCH.value in result.error_codes


def test_invalid_epoch_sequence_non_contiguous() -> None:
    epochs = (
        GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel()),
        GeneratorEpochInputV1(2, _BAR_CLOSE_1, _eligible_panel()),
    )
    result = generate_pit_futures_universe_manifest_v1(_build_input(epochs=epochs))
    assert result.success is False
    assert GeneratorErrorCode.INVALID_EPOCH_ORDER.value in result.error_codes


def test_unsorted_epoch_inputs_are_normalized() -> None:
    epochs = (
        GeneratorEpochInputV1(1, _BAR_CLOSE_1, _eligible_panel()),
        GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel()),
    )
    ordered = generate_pit_futures_universe_manifest_v1(_build_input(epochs=epochs))
    shuffled_epochs = (
        GeneratorEpochInputV1(0, _BAR_CLOSE_0, tuple(reversed(_eligible_panel()))),
        GeneratorEpochInputV1(1, _BAR_CLOSE_1, tuple(reversed(_eligible_panel()))),
    )
    reversed_records = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=shuffled_epochs)
    )
    assert ordered.success and reversed_records.success
    assert ordered.manifest is not None and reversed_records.manifest is not None
    assert ordered.manifest.manifest_digest == reversed_records.manifest.manifest_digest


def test_linear_perpetual_canonicalization_reuse() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.success
    assert result.manifest is not None
    assert any(
        member.contract_type == "linear_perpetual"
        for epoch in result.manifest.epochs
        for member in epoch.members
    )


def test_inverse_perpetual_member() -> None:
    record = _base_record(
        contract_type="inverse_perpetual",
        base_asset="ETH",
        venue_symbol="ETH-USD-SWAP",
        digest_suffix="inv",
    )
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert result.success
    assert result.manifest is not None
    assert any(
        member.contract_type == "inverse_perpetual"
        for epoch in result.manifest.epochs
        for member in epoch.members
    )


def test_dated_future_linear_and_inverse() -> None:
    linear = _base_record(
        contract_type="linear_dated_future",
        contract_expiry="20241227",
        expiry_time="2024-12-27T08:00:00Z",
        venue_symbol="ETH-USDT-241227",
        digest_suffix="dated-linear",
    )
    inverse = _base_record(
        contract_type="inverse_dated_future",
        contract_expiry="20241227",
        expiry_time="2024-12-27T08:00:00Z",
        venue_symbol="ETH-USD-241227",
        digest_suffix="dated-inverse",
    )
    panel = _eligible_panel()[:4] + (linear, inverse)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, panel),))
    )
    assert result.success
    assert result.manifest is not None
    types = {member.contract_type for epoch in result.manifest.epochs for member in epoch.members}
    assert "linear_dated_future" in types
    assert "inverse_dated_future" in types


def test_listing_boundary_inclusive() -> None:
    record = _base_record(
        base_asset="ATOM",
        venue_symbol="ATOM-USDT-SWAP",
        digest_suffix="atom-listing",
        listing_time=_BAR_CLOSE_0,
        eligible_from=_BAR_CLOSE_0,
    )
    panel = _eligible_panel() + (record,)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, panel),))
    )
    assert result.success


def test_delisting_boundary_exclusive() -> None:
    record = _base_record(
        base_asset="LTC",
        venue_symbol="LTC-USDT-SWAP",
        digest_suffix="ltc",
        delisting_time=_BAR_CLOSE_0,
    )
    panel = _eligible_panel() + (record,)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, panel),))
    )
    assert result.success
    assert result.manifest is not None
    excluded = result.manifest.epochs[0].excluded_members
    assert any("DELISTED_AT_SCORE_EPOCH" in item.reason_codes for item in excluded)


def test_expiry_boundary_exclusive() -> None:
    record = _base_record(
        contract_type="linear_dated_future",
        contract_expiry="20240601",
        expiry_time=_BAR_CLOSE_0,
        venue_symbol="ETH-USDT-240601",
        digest_suffix="expired",
    )
    panel = _eligible_panel() + (record,)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, panel),))
    )
    assert result.success
    assert any(
        "DELISTED_AT_SCORE_EPOCH" in item.reason_codes
        for item in result.manifest.epochs[0].excluded_members  # type: ignore[union-attr]
    )


def test_eligible_until_boundary_exclusive() -> None:
    record = _base_record(
        base_asset="LTC",
        venue_symbol="LTC-USDT-SWAP",
        digest_suffix="ltc2",
        eligible_until=_BAR_CLOSE_0,
    )
    panel = _eligible_panel() + (record,)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, panel),))
    )
    assert result.success
    assert any(
        "DELISTED_AT_SCORE_EPOCH" in item.reason_codes
        for item in result.manifest.epochs[0].excluded_members  # type: ignore[union-attr]
    )


def test_multi_epoch_generation() -> None:
    epochs = (
        GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel()),
        GeneratorEpochInputV1(1, _BAR_CLOSE_1, _eligible_panel()),
    )
    result = generate_pit_futures_universe_manifest_v1(_build_input(epochs=epochs))
    assert result.success
    assert result.manifest is not None
    assert len(result.manifest.epochs) == 2


def test_semantically_identical_input_permutation_invariant() -> None:
    first = generate_pit_futures_universe_manifest_v1(_build_input())
    shuffled = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(
                GeneratorEpochInputV1(
                    0,
                    _BAR_CLOSE_0,
                    tuple(reversed(_eligible_panel())),
                ),
            )
        )
    )
    assert first.success and shuffled.success
    assert first.manifest is not None and shuffled.manifest is not None
    assert first.manifest.manifest_digest == shuffled.manifest.manifest_digest
    assert first.manifest_reference == shuffled.manifest_reference


def test_conflicting_source_records_fail_closed() -> None:
    first = _base_record(base_asset="NEAR", venue_symbol="NEAR-USDT-SWAP", digest_suffix="near-a")
    second = _base_record(
        base_asset="NEAR",
        venue_symbol="NEAR-USDT-SWAP",
        digest_suffix="near-b",
        history_bars_available=10,
    )
    panel = _eligible_panel() + (first, second)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, panel),))
    )
    assert result.success is False
    assert GeneratorErrorCode.CONFLICTING_SOURCE_RECORDS.value in result.error_codes


def test_missing_listing_time_fail_closed() -> None:
    record = _base_record(listing_time=None)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert result.success is False
    assert GeneratorErrorCode.MISSING_LISTING_TIME.value in result.error_codes


def test_missing_expiry_for_dated_future_fail_closed() -> None:
    record = _base_record(
        contract_type="linear_dated_future",
        contract_expiry=None,
        expiry_time=None,
        venue_symbol="ETH-USDT-241227",
        digest_suffix="no-expiry",
    )
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert result.success is False
    assert GeneratorErrorCode.MISSING_EXPIRY_OR_PERPETUAL_CLASSIFICATION.value in result.error_codes


@pytest.mark.parametrize(
    ("market_type", "expected"),
    [
        ("spot", GeneratorErrorCode.SPOT_INSTRUMENT_BLOCKED),
        ("synthetic_spot", GeneratorErrorCode.SYNTHETIC_SPOT_BLOCKED),
        ("equity", GeneratorErrorCode.NON_FUTURES_INSTRUMENT),
    ],
)
def test_non_futures_and_spot_negative_cases(
    market_type: str, expected: GeneratorErrorCode
) -> None:
    record = _base_record(market_type=market_type, digest_suffix=market_type)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert result.success is False
    assert expected.value in result.error_codes


@pytest.mark.parametrize("base_asset", ["BTC", "XBT", "WBTC"])
def test_bitcoin_direction_blocked(base_asset: str) -> None:
    record = _base_record(
        base_asset=base_asset,
        venue_symbol=f"{base_asset}-USDT-SWAP",
        digest_suffix=base_asset.lower(),
    )
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert result.success is False
    assert GeneratorErrorCode.BITCOIN_INSTRUMENT_BLOCKED.value in result.error_codes


def test_exclusion_codes_remain_exactly_sixteen() -> None:
    assert len(EXCLUSION_REASON_CODES) == 16


def test_generator_error_code_taxonomy_has_exactly_seventeen_codes() -> None:
    assert len(GeneratorErrorCode) == 17


def test_generator_errors_occur_before_output() -> None:
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, ()),))
    )
    assert result.success is False
    assert result.manifest is None
    assert result.manifest_reference is None


def test_validator_round_trip_accepted() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.manifest is not None
    round_trip = manifest_from_dict(manifest_to_dict(result.manifest))
    validation = validate_pit_futures_universe_manifest_v1(round_trip)
    assert validation.verdict == ValidationVerdict.ACCEPTED


def test_output_validation_failed_when_validator_rejects() -> None:
    inp = _build_input()
    broken = dataclasses.replace(inp, minimum_required_member_count=5)
    result = generate_pit_futures_universe_manifest_v1(broken)
    assert result.success
    assert result.manifest is not None
    tampered = dataclasses.replace(result.manifest, futures_only=False)
    validation = validate_pit_futures_universe_manifest_v1(tampered)
    assert validation.verdict == ValidationVerdict.REJECTED


def test_no_successful_return_when_post_validation_would_reject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.research.pit_futures_universe_manifest_generator_v1 as generator_module

    def _reject(_manifest: object) -> object:
        from src.research.pit_futures_universe_manifest_validator_v1 import (
            PitFuturesUniverseManifestValidationResultV1,
            ValidationVerdict,
        )

        return PitFuturesUniverseManifestValidationResultV1(
            ValidationVerdict.REJECTED,
            False,
            ("POLICY_FLAG_VIOLATION",),
        )

    monkeypatch.setattr(generator_module, "validate_pit_futures_universe_manifest_v1", _reject)
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.success is False
    assert GeneratorErrorCode.OUTPUT_VALIDATION_FAILED.value in result.error_codes
    assert result.manifest is None


def test_attach_computed_digests_and_reference_reuse() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.success
    assert result.manifest is not None
    assert result.manifest_reference is not None
    parsed = parse_pit_universe_manifest_reference_v1(result.manifest_reference)
    assert parsed.success
    assert parsed.reference is not None
    assert parsed.reference.manifest_digest == result.manifest.manifest_digest


def test_source_snapshot_refs_and_digests_bound() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.success
    assert result.manifest is not None
    assert result.manifest.source_dataset_refs == (_DATASET_REF,)


def test_config_and_implementation_digest_binding() -> None:
    inp = _build_input()
    assert inp.config_digest == compute_generator_config_digest(inp)
    assert inp.implementation_digest == compute_generator_implementation_digest()
    wrong = dataclasses.replace(inp, config_digest="f" * 64)
    result = generate_pit_futures_universe_manifest_v1(wrong)
    assert result.success is False
    assert GeneratorErrorCode.INVALID_INPUT_CONTRACT.value in result.error_codes


def test_generated_at_is_input_bound_only() -> None:
    first = generate_pit_futures_universe_manifest_v1(
        _build_input(generated_at="2026-01-01T00:00:00Z")
    )
    second = generate_pit_futures_universe_manifest_v1(
        _build_input(generated_at="2026-02-01T00:00:00Z")
    )
    assert first.success and second.success
    assert first.manifest is not None and second.manifest is not None
    assert first.manifest.generated_at != second.manifest.generated_at
    assert compute_membership_digest(first.manifest) == compute_membership_digest(second.manifest)


def test_manifest_schema_constants_unchanged() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.manifest is not None
    assert result.manifest.schema_name == SCHEMA_NAME
    assert result.manifest.schema_version == SCHEMA_VERSION


def test_stable_canonical_serialization() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.manifest is not None
    first = dumps_canonical(manifest_to_dict(result.manifest))
    second = dumps_canonical(manifest_to_dict(result.manifest))
    assert first == second


def test_stable_manifest_digest_semantics() -> None:
    result = generate_pit_futures_universe_manifest_v1(_build_input())
    assert result.manifest is not None
    assert compute_manifest_digest(result.manifest) == result.manifest.manifest_digest


def test_input_records_not_mutated() -> None:
    record = _base_record()
    original = dataclasses.asdict(record)
    generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert dataclasses.asdict(record) == original


def test_unknown_venue_fail_closed() -> None:
    record = _base_record(venue_id="unknown_venue", digest_suffix="unknown")
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert result.success is False
    assert GeneratorErrorCode.UNKNOWN_VENUE.value in result.error_codes


def test_invalid_lifecycle_interval_fail_closed() -> None:
    record = _base_record(
        listing_time="2024-06-02T00:00:00Z",
        delisting_time="2024-06-01T00:00:00Z",
        digest_suffix="bad-interval",
    )
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(
            epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, _eligible_panel() + (record,)),)
        )
    )
    assert result.success is False
    assert GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL.value in result.error_codes


def test_excluded_members_use_only_existing_exclusion_codes() -> None:
    record = _base_record(
        base_asset="LTC",
        venue_symbol="LTC-USDT-SWAP",
        digest_suffix="ltc3",
        delisting_time=_BAR_CLOSE_0,
    )
    panel = _eligible_panel() + (record,)
    result = generate_pit_futures_universe_manifest_v1(
        _build_input(epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE_0, panel),))
    )
    assert result.success
    assert result.manifest is not None
    for item in result.manifest.epochs[0].excluded_members:
        assert set(item.reason_codes).issubset(EXCLUSION_REASON_CODES)
