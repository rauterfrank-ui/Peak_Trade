"""Original market evidence → versioned OLS baseline → computed offline forecast."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import hashlib
from pathlib import Path
import re
import sys

import numpy as np

from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import fit_ols_lstsq
from .context_admission_v1 import replay_admitted_market_context_v1
from .forecast_evidence_v1 import mint_forecast_evidence_v1
from .forecast_measurement_integration_v1 import (
    MARKET_FROZEN_SCHEMA,
    _append,
    _lease,
    _read,
    freeze_existing_market_forecast_v1,
)
from .independent_market_forecast_measurement_v1 import (
    _prepare,
    read_independent_market_calibration_v1,
)
from .integration_contracts_v1 import (
    assert_offline_v1,
    bytes_v1,
    digest_v1,
    finite_v1,
    instant_v1,
    plain_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
    text_v1,
    validate_seal_v1,
)
from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
)

MODEL_SCHEMA = "independent_market_ols_model_v1"
REQUEST_RECEIPT_SCHEMA = "independent_market_ols_request_receipt_v1"
PROVIDER_SCHEMA = "independent_market_ols_forecast_provider_v1"
PROVIDER_REF = "offline.independent_market_ols_next_forecast_v1"
_MODEL_PATTERN = re.compile(r"mi\.market\.ols\.[0-9a-f]{64}\Z")
_FIELDS = {
    "FinalizedPt1mMarkFactV1": {"mark_px": "price"},
    "MarkPriceFactV1": {"mark_px": "price"},
    "IndexPriceFactV1": {"index_px": "price"},
    "LastTradePriceFactV1": {"last_px": "price"},
    "TradeFactV1": {"price": "price", "size": "size"},
    "OhlcvIntervalFactV1": {
        "open_px": "price",
        "high_px": "price",
        "low_px": "price",
        "close_px": "price",
        "volume": "volume",
    },
    "FundingRateFactV1": {"funding_rate": "funding_rate"},
    "OpenInterestFactV1": {"open_interest": "open_interest"},
    "FinalizedPt1hO4BarFactV1": {"close": "price"},
}


@dataclass(frozen=True)
class MarketOlsFeatureV1:
    name: str
    role: str
    ordinal: int
    fact_kind: str
    field: str
    unit: str


@dataclass(frozen=True)
class MarketOlsPolicyV1:
    validation_fraction: float
    min_training_rows: int
    min_validation_rows: int
    max_context_age_seconds: int
    max_training_evidence_age_seconds: int


def _features(specs):
    result = [asdict(s) if isinstance(s, MarketOlsFeatureV1) else plain_v1(s) for s in specs]
    require_v1(bool(result), "MODEL_FEATURES_REQUIRED")
    names = []
    for s in result:
        require_v1(set(s) == set(MarketOlsFeatureV1.__annotations__), "FEATURE_FIELDS_MISMATCH")
        require_v1(
            isinstance(s["name"], str)
            and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*", s["name"]) is not None,
            "FEATURE_NAME_INVALID",
        )
        require_v1(
            s["name"] not in {"intercept", "realized_log_return", "forecast_time"},
            "FEATURE_NAME_RESERVED",
        )
        text_v1(s["role"], "FEATURE_ROLE")
        text_v1(s["unit"], "FEATURE_UNIT")
        require_v1(type(s["ordinal"]) is int and s["ordinal"] >= 0, "FEATURE_ORDINAL_REQUIRED")
        require_v1(
            s["field"] in _FIELDS.get(s["fact_kind"], {}), "FEATURE_NUMERIC_FIELD_UNSUPPORTED"
        )
        names.append(s["name"])
    require_v1(len(names) == len(set(names)), "DUPLICATE_FEATURE_NAME")
    selectors = [(s["role"], s["ordinal"], s["field"]) for s in result]
    require_v1(len(selectors) == len(set(selectors)), "DUPLICATE_FEATURE_SELECTOR")
    return result


def _policy(value):
    p = asdict(value) if isinstance(value, MarketOlsPolicyV1) else plain_v1(value)
    require_v1(set(p) == set(MarketOlsPolicyV1.__annotations__), "MODEL_POLICY_FIELDS_MISMATCH")
    fraction = finite_v1(p["validation_fraction"], "VALIDATION_FRACTION")
    require_v1(0 < fraction < 1, "VALIDATION_FRACTION_DOMAIN")
    for name in set(p) - {"validation_fraction"}:
        require_v1(type(p[name]) is int and p[name] >= 0, "MODEL_POLICY_INTEGER_REQUIRED")
    require_v1(
        p["min_training_rows"] >= 2 and p["min_validation_rows"] >= 2, "MODEL_MINIMUM_COUNTS"
    )
    return p


def _extract(context, specs):
    values = {}
    for s in specs:
        matches = [
            b
            for b in context["source_bindings"]
            if b["role"] == s["role"] and b["ordinal"] == s["ordinal"]
        ]
        require_v1(len(matches) == 1, "MODEL_FEATURE_MISSING_OR_AMBIGUOUS")
        b = matches[0]
        require_v1(b["fact_kind"] == s["fact_kind"], "MODEL_FEATURE_KIND_MISMATCH")
        unit_field = _FIELDS[s["fact_kind"]][s["field"]]
        require_v1(b["units"].get(unit_field) == s["unit"], "MODEL_FEATURE_UNIT_MISMATCH")
        payload = (
            b["payload"]["bar"] if s["fact_kind"] == "FinalizedPt1hO4BarFactV1" else b["payload"]
        )
        raw = payload.get(s["field"])
        require_v1(type(raw) in (str, int, float), "MODEL_FEATURE_NUMERIC_REQUIRED")
        try:
            number = float(raw)
        except (ValueError, OverflowError) as exc:
            raise ValueError("MODEL_FEATURE_NUMERIC_INVALID") from exc
        values[s["name"]] = finite_v1(number, "MODEL_FEATURE")
    return values


def _target_contract(request):
    build_independent_market_return_target_v1(request)
    return {
        k: plain_v1(v)
        for k, v in request.items()
        if k not in {"schema_version", "horizon_start_time_utc"}
    }


def _samples(jobs, specs, trained_as_of):
    cutoff = instant_v1(trained_as_of)
    rows = []
    contract = None
    for job in jobs:
        require_v1(set(job) == {"store_root", "job_key"}, "ORIGINAL_MARKET_JOB_LOCATOR_REQUIRED")
        packet = read_independent_market_calibration_v1(**job)
        frozen, forecast, observation, calibration, research = _prepare(
            packet["frozen"], packet["measurement_inputs"]["market_observation"]
        )
        original = packet["original_record"]
        require_v1(
            bytes_v1(original["forecast_evidence"]) == bytes_v1(forecast)
            and bytes_v1(original["calibration_evidence"]) == bytes_v1(calibration)
            and bytes_v1(original["research_evidence"]) == bytes_v1(research),
            "MODEL_ORIGINAL_TRIAD_MISMATCH",
        )
        context = replay_admitted_market_context_v1(frozen["context_package"])
        require_v1(
            instant_v1(context["as_of"])
            <= instant_v1(forecast["forecast_created_at_utc"])
            <= instant_v1(observation["request"]["horizon_start_time_utc"]),
            "MODEL_TRAINING_FORECAST_TIME_INVALID",
        )
        current = _target_contract(observation["request"])
        contract = current if contract is None else contract
        require_v1(current == contract, "MODEL_TRAINING_TARGET_OR_MARKET_MISMATCH")
        available = observation["evaluated_at_utc"]
        require_v1(instant_v1(available) <= cutoff, "MODEL_LABEL_NOT_AVAILABLE_AT_CUTOFF")
        body = {
            "job_key": plain_v1(job["job_key"]),
            "context_digest": context["exact_content_digest"],
            "context_as_of": context["as_of"],
            "forecast_time": forecast["forecast_created_at_utc"],
            "frozen_digest": frozen["exact_content_digest"],
            "original_triad_digest": digest_v1(original),
            "market_observation_digest": observation["exact_content_digest"],
            "actual_outcome_ref": observation["measurement"]["actual_outcome_ref"],
            "calibration_evidence_id": calibration["calibration_evidence_id"],
            "label_available_at": available,
            "realized_log_return": finite_v1(
                calibration["calibration_result"]["realized_return"], "MODEL_LABEL"
            ),
            "original_forecast_error": finite_v1(
                calibration["calibration_result"]["error"], "MODEL_ORIGINAL_ERROR"
            ),
            "features": _extract(context, specs),
        }
        rows.append({**body, "sample_id": digest_v1(body)})
    require_v1(bool(rows), "MODEL_TRAINING_EVIDENCE_REQUIRED")
    rows.sort(key=lambda r: (instant_v1(r["forecast_time"]), r["sample_id"]))
    for key in ["sample_id", "actual_outcome_ref"]:
        require_v1(len(rows) == len({r[key] for r in rows}), "MODEL_DUPLICATE_EVIDENCE")
    for previous, current in zip(rows, rows[1:]):
        require_v1(
            instant_v1(previous["label_available_at"]) <= instant_v1(current["context_as_of"]),
            "MODEL_OVERLAPPING_OR_NONCAUSAL_SAMPLES",
        )
    return rows, contract


def _model_path(root, ref):
    require_v1(
        isinstance(ref, str) and _MODEL_PATTERN.fullmatch(ref) is not None,
        "MODEL_REFERENCE_INVALID",
    )
    return Path(root) / "models" / (ref + ".json")


def _read_model_artifact(model_store_root, model_ref):
    path = _model_path(model_store_root, model_ref)
    require_v1(path.is_file(), "MODEL_ARTIFACT_NOT_FOUND")
    model = validate_seal_v1(strict_json_v1(path.read_bytes()), MODEL_SCHEMA)
    body = {k: v for k, v in model.items() if k not in {"exact_content_digest", "model_ref"}}
    require_v1(
        model["model_ref"] == model_ref == "mi.market.ols." + digest_v1(body),
        "MODEL_NUMERIC_CONTENT_MISMATCH",
    )
    request = model["request"]
    require_v1(model["request_digest"] == digest_v1(request), "MODEL_REQUEST_MISMATCH")
    specs = _features(request["features"])
    _policy(request["policy"])
    require_v1(
        set(model["coefficients"]) == {"intercept", *(s["name"] for s in specs)},
        "MODEL_COEFFICIENT_SCHEMA_MISMATCH",
    )
    for value in model["coefficients"].values():
        finite_v1(value, "MODEL_COEFFICIENT")
    require_v1(
        finite_v1(model["residual_std"], "MODEL_RESIDUAL_STD") >= 0, "MODEL_RESIDUAL_STD_NEGATIVE"
    )
    require_v1(
        type(model["model_version"]) is int and model["model_version"] >= 1, "MODEL_VERSION_INVALID"
    )
    return model


def read_market_ols_model_v1(*, model_store_root, model_ref):
    """Cold numeric state/lineage read, without fitting or recursive stack growth."""
    assert_offline_v1()
    result, child, seen = None, None, set()
    current = model_ref
    while current is not None:
        require_v1(current not in seen, "MODEL_PARENT_CYCLE")
        seen.add(current)
        model = _read_model_artifact(model_store_root, current)
        if result is None:
            result = model
        if child is not None:
            require_v1(
                child["model_version"] == model["model_version"] + 1,
                "MODEL_PARENT_VERSION_MISMATCH",
            )
            _assert_extension(child["request"], model["request"])
        current = model["request"]["parent_model_ref"]
        if current is None:
            require_v1(model["model_version"] == 1, "MODEL_BOOTSTRAP_VERSION_INVALID")
        child = model
    require_v1(result is not None, "MODEL_REFERENCE_REQUIRED")
    return result


def _assert_extension(request, prior):
    for key in ["features", "policy", "target_contract"]:
        require_v1(request[key] == prior[key], "MODEL_PARENT_CONTRACT_MISMATCH")
    old = prior["samples"]
    new = request["samples"]
    require_v1(
        len(new) > len(old) and new[: len(old)] == old,
        "MODEL_PARENT_REQUIRES_NEW_CUMULATIVE_EVIDENCE",
    )
    require_v1(
        instant_v1(request["trained_as_of"]) >= instant_v1(prior["available_at"]),
        "MODEL_PARENT_KNOWLEDGE_LOOKAHEAD",
    )


@contextmanager
def _training_lease(root, key):
    folder = Path(root) / ".requests" / key
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "lease").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield folder
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _implementation_binding():
    repo = Path(__file__).resolve().parents[2]
    files = [
        Path(__file__),
        repo / "research/linear_evidence/fitters.py",
        repo / "research/linear_evidence/feature_matrix.py",
    ]
    return {
        "python": sys.version,
        "numpy": np.__version__,
        "sources": {
            str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
        },
    }


def _fit_request(request):
    rows = [
        {
            "forecast_time": instant_v1(s["forecast_time"]).isoformat(timespec="microseconds"),
            "realized_log_return": s["realized_log_return"],
            **s["features"],
        }
        for s in request["samples"]
    ]
    names = tuple(s["name"] for s in request["features"])
    x, y, binding = build_feature_matrix_binding(
        rows, feature_names=names, target_name="realized_log_return", time_name="forecast_time"
    )
    fraction = request["policy"]["validation_fraction"]
    split = max(1, min(len(rows) - 1, int(round(len(rows) * (1.0 - fraction)))))
    require_v1(
        split >= max(request["policy"]["min_training_rows"], len(names) + 1),
        "MODEL_INSUFFICIENT_TRAINING_ROWS",
    )
    require_v1(
        len(rows) - split >= request["policy"]["min_validation_rows"],
        "MODEL_INSUFFICIENT_VALIDATION_ROWS",
    )
    fitted = fit_ols_lstsq(
        x,
        y,
        binding,
        fit_intercept=True,
        validation_fraction=fraction,
        evidence_type="IndependentMarketLogReturnOlsBaselineV1",
        instrument_universe_digest=digest_v1(request["target_contract"]["market_identity"]),
    )
    require_v1(
        fitted.status == "CALIBRATION_CANDIDATE" and fitted.diagnostics.rank == len(names) + 1,
        "MODEL_FIT_NUMERICALLY_BLOCKED",
    )
    coefficients = {k: finite_v1(v, "MODEL_COEFFICIENT") for k, v in fitted.coefficients.items()}
    predicted = coefficients["intercept"] + x[split:] @ np.array([coefficients[n] for n in names])
    residuals = y[split:] - predicted
    historical = np.array([s["original_forecast_error"] for s in request["samples"][split:]])
    validation = {
        "training_rows": split,
        "validation_rows": len(rows) - split,
        "heldout_rmse": float(np.sqrt(np.mean(residuals**2))),
        "heldout_mae": float(np.mean(np.abs(residuals))),
        "heldout_residual_mean": float(np.mean(residuals)),
        "heldout_residual_population_std": float(np.std(residuals, ddof=0)),
        "historical_supplied_forecasts_rmse": float(np.sqrt(np.mean(historical**2))),
        "independent_quality_proven": False,
    }
    for key, value in validation.items():
        if type(value) is float:
            finite_v1(value, key)
    return coefficients, validation, fitted.status


def train_market_ols_model_v1(
    *,
    model_store_root,
    evidence_jobs,
    features,
    policy,
    trained_as_of,
    available_at,
    parent_model_ref,
):
    """Explicit batch fit of unique original outcomes; immutable parent extension."""
    assert_offline_v1()
    specs, p = _features(features), _policy(policy)
    require_v1(
        instant_v1(trained_as_of) <= instant_v1(available_at), "MODEL_AVAILABILITY_BEFORE_TRAINING"
    )
    samples, contract = _samples(evidence_jobs, specs, trained_as_of)
    request = {
        "samples": samples,
        "target_contract": contract,
        "features": specs,
        "policy": p,
        "trained_as_of": trained_as_of,
        "available_at": available_at,
        "parent_model_ref": parent_model_ref,
        "implementation": _implementation_binding(),
    }
    parent = None
    if parent_model_ref is not None:
        parent = read_market_ols_model_v1(
            model_store_root=model_store_root, model_ref=parent_model_ref
        )
        _assert_extension(request, parent["request"])
    request_digest = digest_v1(request)
    with _training_lease(model_store_root, request_digest) as folder:
        receipt_path = folder / "model_receipt.json"
        if receipt_path.exists():
            receipt = _read(receipt_path, REQUEST_RECEIPT_SCHEMA)
            require_v1(
                receipt["request_digest"] == request_digest, "MODEL_RECEIPT_REQUEST_MISMATCH"
            )
            model = read_market_ols_model_v1(
                model_store_root=model_store_root, model_ref=receipt["model_ref"]
            )
            require_v1(model["request"] == request, "MODEL_RETRY_REQUEST_MISMATCH")
            return model
        # Recover a complete artifact if publication stopped before its receipt.
        recovered = []
        for path in sorted((Path(model_store_root) / "models").glob("*.json")):
            candidate = read_market_ols_model_v1(
                model_store_root=model_store_root, model_ref=path.stem
            )
            if candidate["request_digest"] == request_digest:
                require_v1(candidate["request"] == request, "MODEL_PREPARED_REQUEST_MISMATCH")
                recovered.append(candidate)
        require_v1(len(recovered) <= 1, "MODEL_MULTIPLE_ARTIFACTS_FOR_REQUEST")
        if recovered:
            model = recovered[0]
        else:
            coefficients, validation, fit_status = _fit_request(request)
            body = {
                "schema_version": MODEL_SCHEMA,
                "authority": "NONE",
                "request": request,
                "request_digest": request_digest,
                "model_version": parent["model_version"] + 1 if parent else 1,
                "coefficients": coefficients,
                "validation": validation,
                "residual_std": validation["heldout_residual_population_std"],
                "fitter_status": fit_status,
                "model_family": "OLS_CONDITIONAL_LOG_RETURN_MEAN_V1",
                "distribution_calibration_proven": False,
                "productive_apply_authorized": False,
            }
            ref = "mi.market.ols." + digest_v1(body)
            model = seal_v1({**body, "model_ref": ref})
            path = _model_path(model_store_root, ref)
            path.parent.mkdir(parents=True, exist_ok=True)
            _append(path, model)
        _append(
            receipt_path,
            seal_v1(
                {
                    "schema_version": REQUEST_RECEIPT_SCHEMA,
                    "authority": "NONE",
                    "request_digest": request_digest,
                    "model_ref": model["model_ref"],
                }
            ),
        )
        return read_market_ols_model_v1(
            model_store_root=model_store_root, model_ref=model["model_ref"]
        )


def forecast_from_market_ols_model_v1(
    *,
    model_store_root,
    model_ref,
    store_root,
    context_package,
    market_request,
    forecast_created_at,
    attempt_generation,
):
    """Load stored numeric weights, consume admitted features, compute and freeze."""
    assert_offline_v1()
    model = read_market_ols_model_v1(model_store_root=model_store_root, model_ref=model_ref)
    context = replay_admitted_market_context_v1(context_package)
    request, policy = model["request"], model["request"]["policy"]
    require_v1(
        _target_contract(market_request) == request["target_contract"],
        "MODEL_FORECAST_TARGET_OR_MARKET_MISMATCH",
    )
    require_v1(
        context["identity"] == market_request["market_identity"],
        "MODEL_FORECAST_CONTEXT_IDENTITY_MISMATCH",
    )
    as_of, created = instant_v1(context["as_of"]), instant_v1(forecast_created_at)
    require_v1(
        instant_v1(request["available_at"]) <= as_of <= created,
        "MODEL_FORECAST_KNOWLEDGE_LOOKAHEAD",
    )
    require_v1(
        (created - as_of).total_seconds() <= policy["max_context_age_seconds"],
        "MODEL_FORECAST_CONTEXT_STALE",
    )
    last_label = max(instant_v1(s["label_available_at"]) for s in request["samples"])
    require_v1(
        (as_of - last_label).total_seconds() <= policy["max_training_evidence_age_seconds"],
        "MODEL_TRAINING_EVIDENCE_STALE",
    )
    values = _extract(context, request["features"])
    coefficients = model["coefficients"]
    mean = finite_v1(
        coefficients["intercept"] + sum(coefficients[k] * v for k, v in values.items()),
        "COMPUTED_MODEL_MEAN",
    )
    target = build_independent_market_return_target_v1(market_request)
    computation = {
        "model_ref": model_ref,
        "model_exact_digest": model["exact_content_digest"],
        "context_digest": context["exact_content_digest"],
        "forecast_created_at": forecast_created_at,
        "target_spec_digest": digest_v1(target),
        "feature_values": values,
        "computed_payload": {"mean_return": mean, "std_return": model["residual_std"]},
        "requested_attempt_generation": text_v1(attempt_generation, "ATTEMPT_GENERATION"),
    }
    computation_digest = digest_v1(computation)
    forecast = mint_forecast_evidence_v1(
        information_set_ref=context["market_context"]["information_set_ref"],
        forecast_created_at_utc=forecast_created_at,
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        n_bars=market_request["n_bars"],
        bar_spec_ref=target["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload=computation["computed_payload"],
        market_state_refs=[context["market_context"]["context_id"]],
        forecast_model_ref=model_ref,
        support_disposition="SUFFICIENT_EVIDENCE",
        selected_instrument_ref=context["identity"]["instrument_ref"],
        provenance={
            "TEST_ONLY_SYNTHETIC": market_request["source_kind"] == "SYNTHETIC_OFFLINE",
            "measured_return_target_v1": target,
            "numerical_provider_ref": PROVIDER_REF,
            "model_exact_digest": model["exact_content_digest"],
            "feature_values_exact_digest": digest_v1(values),
            "model_computation_digest": computation_digest,
            "distribution_calibration_proven": False,
        },
    )
    model_bytes = bytes_v1(model)
    frozen = freeze_existing_market_forecast_v1(
        store_root=store_root,
        context_package=context,
        forecast_evidence=forecast,
        original_probabilistic_payload=bytes_v1(forecast["probabilistic_payload"]),
        model_artifact_bytes=model_bytes,
        attempt_generation="market.ols.inference." + computation_digest,
        provider_admission={
            "provider_ref": PROVIDER_REF,
            "model_ref": model_ref,
            "feature_schema_ref": digest_v1(request["features"]),
            "training_dataset_ref": model["request_digest"],
            "validation_ref": digest_v1(model["validation"]),
            "admitted_by_ref": "EXPLICIT_OFFLINE_OLS_BASELINE_POLICY_V1",
            "model_artifact_sha256": hashlib.sha256(model_bytes).hexdigest(),
            "training_end": request["trained_as_of"],
            "available_at": request["available_at"],
            "context_package_digest": context["exact_content_digest"],
            "max_context_age_seconds": policy["max_context_age_seconds"],
            "target_spec_digest": digest_v1(target),
        },
    )
    receipt = seal_v1(
        {
            "schema_version": PROVIDER_SCHEMA,
            "authority": "NONE",
            "model_ref": model_ref,
            "model_exact_digest": model["exact_content_digest"],
            "job_key": frozen["job_key"],
            "frozen_digest": frozen["exact_content_digest"],
            "feature_values": values,
            "computed_payload": plain_v1(forecast["probabilistic_payload"]),
            "computation": computation,
            "model_inference_performed": True,
            "numeric_feature_consumption_proven": True,
            "independent_quality_proven": False,
            "productive_apply_authorized": False,
        }
    )
    with _lease(store_root, digest_v1(frozen["job_key"])) as folder:
        _append(folder / "model_inference.json", receipt)
    return {"provider": receipt, "frozen": frozen}


def read_market_model_forecast_v1(*, model_store_root, store_root, job_key):
    """Exact provider/freeze/model cold read; never fit or recompute a forecast."""
    assert_offline_v1()
    folder = Path(store_root) / ".intelligence-integration-v1" / digest_v1(job_key)
    frozen = _read(folder / "forecast.json", MARKET_FROZEN_SCHEMA)
    receipt = _read(folder / "model_inference.json", PROVIDER_SCHEMA)
    require_v1(
        frozen["job_key"] == receipt["job_key"] == dict(job_key), "MODEL_PROVIDER_JOB_MISMATCH"
    )
    require_v1(
        receipt["frozen_digest"] == frozen["exact_content_digest"], "MODEL_PROVIDER_FREEZE_MISMATCH"
    )
    computation = receipt["computation"]
    require_v1(
        job_key["attempt_generation"] == "market.ols.inference." + digest_v1(computation),
        "MODEL_PROVIDER_COMPUTATION_IDENTITY_MISMATCH",
    )
    forecast = frozen["forecast_evidence"]
    require_v1(
        forecast["provenance"]["model_computation_digest"] == digest_v1(computation),
        "MODEL_PROVIDER_COMPUTATION_DIGEST_MISMATCH",
    )
    require_v1(
        computation["context_digest"] == frozen["context_package"]["exact_content_digest"]
        and computation["forecast_created_at"] == forecast["forecast_created_at_utc"]
        and computation["target_spec_digest"]
        == digest_v1(forecast["provenance"]["measured_return_target_v1"]),
        "MODEL_PROVIDER_COMPUTATION_CONTEXT_MISMATCH",
    )
    require_v1(
        computation["model_ref"] == receipt["model_ref"]
        and computation["model_exact_digest"] == receipt["model_exact_digest"]
        and computation["feature_values"] == receipt["feature_values"]
        and computation["computed_payload"] == receipt["computed_payload"],
        "MODEL_PROVIDER_COMPUTATION_VALUES_MISMATCH",
    )
    require_v1(
        receipt["model_inference_performed"] is True
        and receipt["numeric_feature_consumption_proven"] is True
        and receipt["productive_apply_authorized"] is False,
        "MODEL_PROVIDER_CAPABILITY_MISMATCH",
    )
    model = read_market_ols_model_v1(
        model_store_root=model_store_root, model_ref=receipt["model_ref"]
    )
    require_v1(
        receipt["model_exact_digest"] == model["exact_content_digest"],
        "MODEL_PROVIDER_ARTIFACT_MISMATCH",
    )
    require_v1(
        frozen["forecast_evidence"]["forecast_model_ref"] == model["model_ref"],
        "MODEL_PROVIDER_REFERENCE_MISMATCH",
    )
    require_v1(
        frozen["provider_admission"]["model_artifact_sha256"]
        == hashlib.sha256(bytes_v1(model)).hexdigest(),
        "MODEL_PROVIDER_BYTES_MISMATCH",
    )
    require_v1(
        bytes_v1(receipt["computed_payload"])
        == bytes_v1(frozen["forecast_evidence"]["probabilistic_payload"]),
        "MODEL_PROVIDER_NUMBERS_MISMATCH",
    )
    require_v1(
        digest_v1(receipt["feature_values"])
        == frozen["forecast_evidence"]["provenance"]["feature_values_exact_digest"],
        "MODEL_PROVIDER_FEATURES_MISMATCH",
    )
    return {"provider": receipt, "frozen": frozen}
