"""Train the offline market model from completed jobs in its original evidence store."""

from pathlib import Path

from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
    capture_order_key_v1,
)

from .forecast_measurement_integration_v1 import ACK_SCHEMA
from .independent_market_forecast_measurement_v1 import (
    MARKET_ACK_SCHEMA,
    read_independent_market_calibration_v1,
)
from .integration_contracts_v1 import (
    assert_offline_v1,
    digest_v1,
    require_v1,
    strict_json_v1,
    validate_seal_v1,
)
from .market_ols_next_forecast_v1 import _target_contract, train_market_ols_model_v1


def train_market_ols_model_from_store_v1(
    *,
    evidence_store_root,
    market_request,
    model_store_root,
    features,
    policy,
    trained_as_of,
    available_at,
    parent_model_ref,
):
    """Select the completed population for an explicit market target and cutoff."""
    assert_offline_v1()
    target = _target_contract(market_request)
    market_identity = target["market_identity"]
    cutoff = capture_order_key_v1(trained_as_of)
    job_root = Path(evidence_store_root) / ".intelligence-integration-v1"
    jobs = []
    # The existing measurement owner publishes this ACK after the original
    # forecast, measurement and triad are durable. In-flight jobs have no ACK.
    for path in sorted(job_root.glob("*/calibration_ack.json")):
        ack = strict_json_v1(path.read_bytes())
        if ack.get("schema_version") == ACK_SCHEMA:
            continue
        job = validate_seal_v1(ack, MARKET_ACK_SCHEMA)["job_key"]
        require_v1(digest_v1(job) == path.parent.name, "MARKET_STORE_JOB_ADDRESS_MISMATCH")
        if any(job.get(key) != value for key, value in market_identity.items()):
            continue
        locator = {"store_root": evidence_store_root, "job_key": job}
        observation = read_independent_market_calibration_v1(**locator)["measurement_inputs"][
            "market_observation"
        ]
        if (
            capture_order_key_v1(observation["evaluated_at_utc"]) <= cutoff
            and _target_contract(observation["request"]) == target
        ):
            jobs.append(locator)
    return train_market_ols_model_v1(
        model_store_root=model_store_root,
        evidence_jobs=jobs,
        features=features,
        policy=policy,
        trained_as_of=trained_as_of,
        available_at=available_at,
        parent_model_ref=parent_model_ref,
    )
