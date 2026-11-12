"""Connect recorded mark archive files to the existing offline market consumers."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
    validate_market_horizon_request_v1,
)
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    materialize_independent_market_horizon_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
    capture_order_key_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    FinalizedPt1hO4BarFactV1,
)
from src.research.offline_recorded_mark_horizon_source_v1 import (
    load_archive_source,
    read_bound_json,
)

from .context_admission_v1 import (
    ContextAdmissionPolicyV1,
    FactAdmissionReceiptV1,
    compose_admitted_market_context_v1,
)
from .forecast_measurement_integration_v1 import read_frozen_market_forecast_v1
from .independent_market_forecast_measurement_v1 import calibrate_frozen_market_forecast_v1
from .integration_contracts_v1 import (
    MarketIdentityV1,
    assert_offline_v1,
    bytes_v1,
    digest_v1,
    instant_v1,
    require_v1,
)
from .market_context_existing_fact_materialization_v1 import (
    WP_A_PRODUCER,
    ExistingFactMaterializationRequestV1,
    GovernedCanonicalFactV1,
)
from .market_ols_next_forecast_v1 import forecast_from_market_ols_model_v1


@dataclass(frozen=True)
class RecordedMarkArchiveV1:
    raw_path: Path
    raw_sha256: str
    request_log_path: Path
    request_log_sha256: str
    binding_path: Path
    binding_sha256: str
    repository_sha: str


def _require_received(archive, cutoff):
    log = read_bound_json(archive.request_log_path, archive.request_log_sha256)
    matching = [row for row in log if row.get("raw_response_sha256") == archive.raw_sha256]
    require_v1(len(matching) == 1, "EXACT_UNIQUE_ARCHIVED_REQUEST_REQUIRED")
    received = capture_order_key_v1(matching[0]["response_time_utc"])
    require_v1(received <= capture_order_key_v1(cutoff), "ARCHIVE_RESPONSE_NOT_YET_AVAILABLE")
    require_v1(received[1] % 1000 == 0, "ARCHIVE_RESPONSE_CLOCK_PRECISION_UNSUPPORTED")


def _load(archive, identity, *, start, count, cutoff):
    assert_offline_v1()
    identity.payload()
    instant_v1(cutoff)
    # Check the pinned log before reading the response. The original source
    # loader verifies the same pin again when it binds the full source.
    _require_received(archive, cutoff)
    source = load_archive_source(
        **asdict(archive),
        canonical_instrument_id=identity.instrument_ref,
        native_instrument_id=identity.native_instrument_ref,
        horizon_start_utc=start,
        n_bars=count,
    )
    require_v1(source["venue"] == identity.venue, "ARCHIVE_MARKET_VENUE_MISMATCH")
    files = {key: info["sha256"] for key, info in source["archive_file_bindings"].items()}
    return source, "archive.sha256:" + digest_v1(files)


def compose_recorded_market_context_v1(
    *,
    archive: RecordedMarkArchiveV1,
    identity: MarketIdentityV1,
    bar_open_utc: str,
    observed_at: str,
    policy: ContextAdmissionPolicyV1,
) -> dict[str, Any]:
    """Admit the explicitly requested final archive hour as a forecast input."""
    source, ref = _load(archive, identity, start=bar_open_utc, count=1, cutoff=observed_at)
    record = source["bar_receipts"][0]
    captured = record["available_at_utc"]
    payload = FinalizedPt1hO4BarFactV1(record["bar"]).to_dict()
    payload["timestamps"] = {"captured_at": captured}
    payload["quality"] = {"finalized": True, "missing": False}
    fact = GovernedCanonicalFactV1(
        payload["fact_kind"], fact_digest(payload), payload, WP_A_PRODUCER
    )
    return compose_admitted_market_context_v1(
        identity=identity,
        request=ExistingFactMaterializationRequestV1(
            observed_at, identity.instrument_ref, (ref,), price_o4_bar_fact=fact
        ),
        receipts_by_digest={
            fact.fact_digest: FactAdmissionReceiptV1(
                ref,
                identity.dataset_generation,
                bytes_v1(payload),
                captured,
                captured,
                {"price": source["price_unit"]},
            )
        },
        policy=policy,
    )


def _recorded_target_identity(request: Mapping[str, Any]) -> MarketIdentityV1:
    identity, _, interval, _ = validate_market_horizon_request_v1(request)
    require_v1(interval == "PT1H", "ARCHIVE_PT1H_TARGET_REQUIRED")
    require_v1(request["source_kind"] == "RECORDED_PUBLIC_MD", "MARKET_SOURCE_KIND_MISMATCH")
    return MarketIdentityV1(**identity)


def measure_recorded_market_horizon_v1(
    *, archive: RecordedMarkArchiveV1, request: Mapping[str, Any], evaluated_at_utc: str
) -> dict[str, Any]:
    """Supply recorded receipts to the N_BARS measurement owner for an explicit target."""
    identity = _recorded_target_identity(request)
    source, ref = _load(
        archive,
        identity,
        start=request["horizon_start_time_utc"],
        count=request["n_bars"],
        cutoff=evaluated_at_utc,
    )
    receipts = []
    for row in source["bar_receipts"]:
        bar = row["bar"]
        captured = row["available_at_utc"]
        receipts.append(
            {
                "source_ref": f"{ref}:{int(bar['bar_open_time'])}",
                "dataset_generation": identity.dataset_generation,
                "original_bar_json": bytes_v1(bar).decode("utf-8"),
                "original_bar_sha256": digest_v1(bar),
                "known_at_utc": captured,
                "available_at_utc": captured,
                "source_kind": source["source_kind"],
                "price_unit": source["price_unit"],
                "price_family": source["price_family"],
            }
        )
    return materialize_independent_market_horizon_v1(
        request=request, source_receipts=receipts, evaluated_at_utc=evaluated_at_utc
    )


def forecast_from_recorded_market_context_v1(
    *,
    archive: RecordedMarkArchiveV1,
    bar_open_utc: str,
    observed_at: str,
    context_policy: ContextAdmissionPolicyV1,
    model_store_root: Path | str,
    model_ref: str,
    store_root: Path | str,
    market_request: Mapping[str, Any],
    forecast_created_at: str,
    attempt_generation: str,
) -> dict[str, Any]:
    """Admit an archived context and freeze a forecast from a specified stored OLS model."""
    identity = _recorded_target_identity(market_request)
    context = compose_recorded_market_context_v1(
        archive=archive,
        identity=identity,
        bar_open_utc=bar_open_utc,
        observed_at=observed_at,
        policy=context_policy,
    )
    return forecast_from_market_ols_model_v1(
        model_store_root=model_store_root,
        model_ref=model_ref,
        store_root=store_root,
        context_package=context,
        market_request=market_request,
        forecast_created_at=forecast_created_at,
        attempt_generation=attempt_generation,
    )


def complete_recorded_market_forecast_v1(
    *,
    store_root: Path | str,
    job_key: Mapping[str, Any],
    archive: RecordedMarkArchiveV1,
    evaluated_at_utc: str,
) -> dict[str, Any]:
    """Resume measurement from a durable forecast and its original target only."""
    frozen = read_frozen_market_forecast_v1(store_root=store_root, job_key=job_key)
    target = frozen["forecast_evidence"]["provenance"].get("measured_return_target_v1")
    require_v1(isinstance(target, Mapping), "EXPLICIT_LOG_RETURN_TARGET_REQUIRED")
    request = target.get("market_request")
    require_v1(
        isinstance(request, Mapping)
        and digest_v1(target) == job_key.get("target_spec_digest")
        and build_independent_market_return_target_v1(request) == target,
        "MARKET_MEASUREMENT_TARGET_MISMATCH",
    )
    observation = measure_recorded_market_horizon_v1(
        archive=archive, request=request, evaluated_at_utc=evaluated_at_utc
    )
    return calibrate_frozen_market_forecast_v1(
        store_root=store_root, frozen=frozen, market_observation=observation
    )
