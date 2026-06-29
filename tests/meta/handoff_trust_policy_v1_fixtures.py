"""Fixtures for handoff_trust_policy_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.handoff_trust_policy_v1 import (
    CONSUMER_CONTRACT_ID,
    CONSUMER_CONTRACT_NAME,
    CONSUMER_CONTRACT_VERSION,
    HANDOFF_TYPE,
    HandoffTrustPolicyInputs,
    produce_handoff_trust_policy_v1,
)
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    ARTIFACT_SCHEMA_VERSION as UPSTREAM_ARTIFACT_SCHEMA_VERSION,
    CONTRACT_NAME as UPSTREAM_CONTRACT_NAME,
    CONTRACT_VERSION as UPSTREAM_CONTRACT_VERSION,
    CREATION_CONTRACT_VERSION as UPSTREAM_CREATION_CONTRACT_VERSION,
)
from tests.meta.versioned_strategy_model_parameter_artifact_v1_fixtures import (
    produce_versioned_artifact_fixture,
)


@dataclass(frozen=True)
class HandoffTrustPolicyFixtureBundle:
    versioned_artifact_bundle_dir: Path
    consumer_contract_path: Path | None = None
    handoff_trust_policy_bundle_dir: Path | None = None


def embedded_consumer_contract_payload() -> dict[str, object]:
    return {
        "consumer_contract_id": CONSUMER_CONTRACT_ID,
        "contract_name": CONSUMER_CONTRACT_NAME,
        "contract_version": CONSUMER_CONTRACT_VERSION,
        "handoff_type": HANDOFF_TYPE,
        "accepted_producer_contract_name": UPSTREAM_CONTRACT_NAME,
        "accepted_producer_contract_version": UPSTREAM_CONTRACT_VERSION,
        "accepted_artifact_schema_version": UPSTREAM_ARTIFACT_SCHEMA_VERSION,
        "accepted_creation_contract_version": UPSTREAM_CREATION_CONTRACT_VERSION,
        "minimum_artifact_version": UPSTREAM_CONTRACT_VERSION,
        "required_binding_status": "PASS",
        "required_completion_flags": [
            "versioned_strategy_model_parameter_artifact_complete",
            "strategy_identity_bound",
            "model_identity_bound",
            "parameter_set_identity_bound",
            "cross_domain_lineage_bound",
        ],
        "forbidden_upstream_capabilities": [
            "CAN_CHANGE_RISK_POLICY",
            "CAN_COMPUTE_SIGNALS",
            "CAN_CREATE_ORDER_INTENTS",
            "CAN_DEPLOY_INACTIVE",
            "CAN_INCREASE_CAPITAL",
            "CAN_PROMOTE_ARTIFACT",
            "CAN_SUBMIT_LIVE_ORDERS",
            "CAN_SUBMIT_TESTNET_ORDERS",
        ],
        "offline_only_required": True,
    }


def write_consumer_contract_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        deterministic_json_dumps(embedded_consumer_contract_payload()),
        encoding="utf-8",
    )
    return path


def produce_handoff_trust_policy_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    include_ai_assessment: bool = False,
    include_consumer_contract_file: bool = False,
    handoff_trust_policy_name: str = "handoff_trust_policy",
    produce_output: bool = True,
) -> HandoffTrustPolicyFixtureBundle:
    versioned = produce_versioned_artifact_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
    )
    assert versioned.versioned_artifact_bundle_dir is not None
    consumer_path: Path | None = None
    if include_consumer_contract_file:
        consumer_path = write_consumer_contract_file(
            durable_root / "offline_strategy_model_parameter_consumer_capability_v1.json"
        )
    trust_dir: Path | None = None
    if produce_output:
        trust_dir = durable_root / handoff_trust_policy_name
        produce_handoff_trust_policy_v1(
            inputs=HandoffTrustPolicyInputs(
                versioned_artifact_bundle_dir=versioned.versioned_artifact_bundle_dir,
                consumer_contract_ref=consumer_path,
            ),
            output_dir=trust_dir,
        )
    return HandoffTrustPolicyFixtureBundle(
        versioned_artifact_bundle_dir=versioned.versioned_artifact_bundle_dir,
        consumer_contract_path=consumer_path,
        handoff_trust_policy_bundle_dir=trust_dir,
    )
