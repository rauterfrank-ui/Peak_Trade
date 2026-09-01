"""WP-FA-07 offline owner bindings and drift-contract foundation tests."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
    DDO_EXPERIMENT_IDENTITY_OWNER,
    DDO_VALIDATION_ENGINE_OWNER,
    DRIFT_CAN_AUTO_PROMOTE,
    DRIFT_CAN_AUTO_ROLLBACK,
    DRIFT_CAN_MUTATE_CORE,
    DRIFT_CAN_MUTATE_RISK,
    DRIFT_CAN_MUTATE_SAFETY,
    DRIFT_CONTRACT_FOUNDATION_CREATED,
    DRIFT_MONITOR_PRODUCTIVE_AUTHORITY,
    DRIFT_MONITOR_RUNTIME_REACHABILITY,
    LEARNING_PRODUCTIVE_AUTHORITY,
    PRODUCTIVE_DEPLOYMENT_ALLOWED,
    PRODUCTIVE_ROLLBACK_ALLOWED,
    PROMOTION_AUTHORITY_ACTIVATION,
    SECOND_EXPERIMENT_IDENTITY_OWNER_CREATED,
    SECOND_FAULT_ENGINE_CREATED,
    SECOND_MC_ENGINE_CREATED,
    SECOND_SAFETY_ENGINE_CREATED,
    SECOND_STRESS_ENGINE_CREATED,
    SECOND_WF_ENGINE_CREATED,
    WORKPACKAGE_ID,
)
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import CONTRACT_REGISTRY_V0
from src.learning.deterministic_decision_outcome_v0.drift_contracts_v0 import (
    build_drift_assessment_record_v0,
    build_drift_observation_record_v0,
    build_drift_policy_v0,
    build_known_good_reference_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN, VALIDATION_GATE_IDS_V0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.experiment_identity_binding_v0 import (
    CANONICAL_EXPERIMENT_IDENTITY_OWNER_PATH,
    DDO_MINTS_EXPERIMENT_IDENTITY,
    bind_canonical_experiment_identity_ref_v0,
    observe_unbound_experiment_ref_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    build_candidate_artifact_v0,
    build_learning_hypothesis_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.validation_artifacts_v0 import (
    ARTIFACT_KIND_BY_GATE_V0,
)
from src.learning.deterministic_decision_outcome_v0.validation_pack_engine_v0 import (
    evaluate_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.validation_producer_bindings_v0 import (
    PRODUCER_EXPERIMENT_MONTE_CARLO,
    PRODUCER_O6_FAULT_HEALTH,
    PRODUCER_PATH_BY_ID_V0,
    PRODUCER_ROLLBACK_READINESS,
    PRODUCER_SAFETY_REPLAY,
    PRODUCER_SCHEMA_BY_ID_V0,
    PRODUCER_STRESS,
    PRODUCER_WALK_FORWARD,
    admit_validation_producer_bindings_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.governance.promotion",
    "src.meta.learning_loop",
    "src.ops",
    "src.experiments",
    "src.backtest",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "http.client",
)
FORBIDDEN_ENGINE_NAMES = (
    "run_walkforward_for_config",
    "run_monte_carlo_from_returns",
    "run_stress_test_suite",
    "evaluate_offline_safety_kernel_boundary_v0",
    "build_canonical_experiment_identity_v1",
    "DDOExperimentIdentity",
)

_PRODUCER_FOR_GATE = {
    "walk_forward_pass": PRODUCER_WALK_FORWARD,
    "monte_carlo_pass": PRODUCER_EXPERIMENT_MONTE_CARLO,
    "stress_pass": PRODUCER_STRESS,
    "fault_injection_pass": PRODUCER_O6_FAULT_HEALTH,
    "safety_regression_pass": PRODUCER_SAFETY_REPLAY,
    "rollback_ready": PRODUCER_ROLLBACK_READINESS,
}


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _envelope(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "record_id": "rec-wp07-0001",
        "event_time_utc": "2026-09-01T21:00:00Z",
        "correlation_id": "cor-wp07-0001",
        "cycle_id": None,
        "causal_parent_ids": [],
        "producer_id": "offline-wp07-producer",
        "authority_owner": UNKNOWN,
        "code_sha": _sha("code"),
        "config_hash": _sha("config"),
        "evidence_hash": _sha("evidence"),
        "evidence_source_refs": ["src-evidence-wp07-1"],
    }
    payload.update(overrides)
    return payload


def _identity_request(**overrides: Any) -> CanonicalExperimentIdentityRequestV1:
    payload: dict[str, Any] = {
        "git_sha": "a7f4502e04e168b2dd12b56fecb745323bd6c783",
        "working_tree_status": "CLEAN",
        "strategy_identity": "ma_crossover.v1",
        "strategy_params": {"slow": 50, "fast": 10},
        "dataset_digest": _sha("dataset"),
        "feature_pipeline_digest": _sha("features"),
        "fee_model_digest": _sha("fee"),
        "slippage_model_digest": _sha("slippage"),
        "funding_model_digest": _sha("funding"),
        "risk_policy_digest": _sha("risk"),
        "portfolio_digest": _sha("portfolio"),
        "split_policy_digest": _sha("split"),
        "market_context_contract_digest": _sha("market-context"),
        "bull_bear_logic_digest": _sha("bull-bear"),
        "state_switch_logic_digest": _sha("state-switch"),
        "survival_logic_digest": _sha("survival"),
        "suitability_logic_digest": _sha("suitability"),
        "double_play_logic_digest": _sha("double-play"),
        "entry_position_exit_logic_digest": _sha("entry-position-exit"),
        "seed": 7,
        "environment": {
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    payload.update(overrides)
    return CanonicalExperimentIdentityRequestV1(**payload)


def _candidate(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="candidate_artifact",
        schema_version="candidate_artifact_v0",
        record_id="cand-wp07-0001",
        hypothesis_ref="hyp-wp07-0001",
        intended_scope="P0-offline-validation",
        promotion_class="P0",
        artifact_hash=_sha("candidate-v1"),
        dataset_ref="dataset-wp07-v1",
        experiment_ref=None,
        rejected=False,
        causal_parent_ids=["hyp-wp07-0001"],
    )
    payload.update(overrides)
    return payload


def _hypothesis() -> dict[str, Any]:
    return _envelope(
        schema_name="learning_hypothesis",
        schema_version="learning_hypothesis_v0",
        record_id="hyp-wp07-0001",
        proposal="offline fixture-only hypothesis",
        productive_authority="NONE",
    )


def _artifact(
    gate: str, *, status: str = "PASS", bound: bool = False, **overrides: Any
) -> dict[str, Any]:
    digest = _sha(f"artifact:{gate}:{status}")
    payload = {
        "gate_id": gate,
        "artifact_kind": ARTIFACT_KIND_BY_GATE_V0[gate],
        "artifact_hash": digest if status == "PASS" else UNKNOWN,
        "dataset_ref": "dataset-wp07-v1",
        "env_identity": "env-wp07-offline",
        "predicate_id": f"predicate.{gate}.v0",
        "status": status,
        "notes": None,
    }
    if bound and gate in _PRODUCER_FOR_GATE:
        producer_id = _PRODUCER_FOR_GATE[gate]
        payload.update(
            {
                "producer_id": producer_id,
                "producer_schema_version": PRODUCER_SCHEMA_BY_ID_V0[producer_id],
                "producer_path": PRODUCER_PATH_BY_ID_V0[producer_id],
                "run_identity": f"run-{gate}",
                "provenance_refs": [digest],
                "compatibility_status": "COMPATIBLE",
                "failure_semantics": "FAIL_CLOSED",
                "claimed_artifact_hash": digest if status == "PASS" else UNKNOWN,
            }
        )
    payload.update(overrides)
    return payload


def _artifacts(*, bound: bool = False, **status_overrides: str) -> list[dict[str, Any]]:
    return [
        _artifact(gate, status=status_overrides.get(gate, "PASS"), bound=bound)
        for gate in VALIDATION_GATE_IDS_V0
    ]


def _pack_identity(**overrides: Any) -> dict[str, Any]:
    payload = {
        "record_id": "pack-wp07-0001",
        "event_time_utc": "2026-09-01T21:00:00Z",
        "correlation_id": "cor-wp07-0001",
        "code_sha": _sha("code"),
        "config_hash": _sha("config"),
        "dataset_ref": "dataset-wp07-v1",
        "environment_fingerprint": "env-wp07-offline",
    }
    payload.update(overrides)
    return payload


def _false_authority() -> dict[str, Any]:
    return {
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
        "can_auto_rollback": False,
        "can_mutate_core": False,
        "can_mutate_risk": False,
        "can_mutate_safety": False,
        "can_deploy": False,
    }


def test_wp_fa_07_authority_markers() -> None:
    assert WORKPACKAGE_ID == "WP_FA_07_OFFLINE_OWNER_BINDINGS_AND_DRIFT_CONTRACTS_V1"
    assert DDO_EXPERIMENT_IDENTITY_OWNER == "EXISTING_CANONICAL_EXPERIMENT_IDENTITY_V1"
    assert SECOND_EXPERIMENT_IDENTITY_OWNER_CREATED is False
    assert DDO_MINTS_EXPERIMENT_IDENTITY is False
    assert DDO_VALIDATION_ENGINE_OWNER == "NONE"
    assert SECOND_WF_ENGINE_CREATED is False
    assert SECOND_MC_ENGINE_CREATED is False
    assert SECOND_STRESS_ENGINE_CREATED is False
    assert SECOND_FAULT_ENGINE_CREATED is False
    assert SECOND_SAFETY_ENGINE_CREATED is False
    assert DRIFT_CONTRACT_FOUNDATION_CREATED is True
    assert DRIFT_MONITOR_RUNTIME_REACHABILITY is False
    assert DRIFT_MONITOR_PRODUCTIVE_AUTHORITY == "NONE"
    assert DRIFT_CAN_AUTO_PROMOTE is False
    assert DRIFT_CAN_AUTO_ROLLBACK is False
    assert DRIFT_CAN_MUTATE_CORE is False
    assert DRIFT_CAN_MUTATE_RISK is False
    assert DRIFT_CAN_MUTATE_SAFETY is False
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is False
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert PRODUCTIVE_DEPLOYMENT_ALLOWED is False
    assert PRODUCTIVE_ROLLBACK_ALLOWED is False


def test_ddo_references_canonical_experiment_identity_and_does_not_mint() -> None:
    identity = dict(build_canonical_experiment_identity_v1(_identity_request()))
    bound = bind_canonical_experiment_identity_ref_v0(
        identity_payload=identity,
        envelope=_envelope(record_id="xref-wp07-0001"),
        claimed_experiment_ref=identity["identity_digest"],
        claimed_candidate_ref="cand-wp07-0001",
    )
    assert bound["binding_status"] == "BOUND"
    assert bound["equivalence_proven"] is True
    assert bound["identity_digest"] == identity["identity_digest"]
    assert bound["source_schema_version"] == "canonical_experiment_identity_v1"
    assert bound["source_owner_path"] == CANONICAL_EXPERIMENT_IDENTITY_OWNER_PATH
    assert bound["ddo_mints_identity"] is False
    assert bound["second_experiment_identity_owner_created"] is False
    candidate = build_candidate_artifact_v0(_candidate(experiment_ref=identity["identity_digest"]))
    assert candidate["experiment_ref"] == bound["identity_digest"]


def test_unbound_experiment_ref_remains_explicit_non_equivalence() -> None:
    observed = observe_unbound_experiment_ref_v0(
        envelope=_envelope(record_id="xref-wp07-0002"),
        claimed_experiment_ref="exp-opaque-wp06-0001",
    )
    assert observed["binding_status"] == UNKNOWN
    assert observed["equivalence_proven"] is False
    assert observed["identity_digest"] == UNKNOWN


def test_noncanonical_experiment_identity_fails_closed() -> None:
    with pytest.raises(DdoValidationError, match="NONCANONICAL_EXPERIMENT_IDENTITY_SCHEMA"):
        bind_canonical_experiment_identity_ref_v0(
            identity_payload={"schema_version": "ddo_experiment_identity_v0"},
            envelope=_envelope(record_id="xref-wp07-0003"),
        )
    with pytest.raises(DdoValidationError, match="NONCANONICAL_EXPERIMENT_IDENTITY_PACKAGE_N"):
        bind_canonical_experiment_identity_ref_v0(
            identity_payload={"schema_version": "experiment_identity_manifest_v1"},
            envelope=_envelope(record_id="xref-wp07-0004"),
        )


def test_experiment_ref_mismatch_fails_closed() -> None:
    identity = dict(build_canonical_experiment_identity_v1(_identity_request()))
    with pytest.raises(DdoValidationError, match="EXPERIMENT_REF_NOT_EQUIVALENT"):
        bind_canonical_experiment_identity_ref_v0(
            identity_payload=identity,
            envelope=_envelope(record_id="xref-wp07-0005"),
            claimed_experiment_ref="not-the-canonical-digest",
        )


def test_producer_bound_validation_pack_accepts_existing_owners() -> None:
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=_candidate(),
        artifacts=_artifacts(bound=True),
        identity=_pack_identity(),
        require_existing_owner_bindings=True,
    )
    pack = evaluated["validation_evidence_pack"]
    assert all(pack["gates"][gate] == "PASS" for gate in VALIDATION_GATE_IDS_V0)
    assert evaluated["validator_productive_authority"] == "NONE"


def test_producer_schema_and_hash_mismatch_fail_closed() -> None:
    artifacts = _artifacts(bound=True)
    rollback = dict(artifacts[VALIDATION_GATE_IDS_V0.index("rollback_ready")])
    rollback["producer_schema_version"] = "not-the-owner-schema"
    artifacts[VALIDATION_GATE_IDS_V0.index("rollback_ready")] = rollback
    with pytest.raises(DdoValidationError, match="PRODUCER_SCHEMA_MISMATCH"):
        admit_validation_producer_bindings_v0(artifacts)
    hashed = _artifacts(bound=True)
    walk = dict(hashed[VALIDATION_GATE_IDS_V0.index("walk_forward_pass")])
    walk["claimed_artifact_hash"] = _sha("different")
    hashed[VALIDATION_GATE_IDS_V0.index("walk_forward_pass")] = walk
    with pytest.raises(DdoValidationError, match="PRODUCER_HASH_MISMATCH"):
        admit_validation_producer_bindings_v0(hashed)


def test_missing_mandatory_producer_binding_fails_closed() -> None:
    with pytest.raises(DdoValidationError, match="MISSING_PRODUCER_BINDING"):
        evaluate_validation_evidence_pack_v0(
            candidate=_candidate(),
            artifacts=_artifacts(bound=False),
            identity=_pack_identity(),
            require_existing_owner_bindings=True,
        )


def test_safety_and_authority_regression_cannot_be_outweighed_by_economic_pass() -> None:
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=_candidate(),
        artifacts=_artifacts(
            bound=True,
            safety_regression_pass="FAIL",
            authority_invariants_pass="FAIL",
            economic_policy_pass="PASS",
        ),
        identity=_pack_identity(),
        require_existing_owner_bindings=True,
    )
    pack = evaluated["validation_evidence_pack"]
    assert pack["gates"]["safety_regression_pass"] == "FAIL"
    assert pack["gates"]["authority_invariants_pass"] == "FAIL"
    assert pack["gates"]["economic_policy_pass"] == "PASS"
    assert "safety_regression_pass" in evaluated["hard_gate_failures"]
    assert "authority_invariants_pass" in evaluated["hard_gate_failures"]
    assert evaluated["economic_improvement_cannot_compensate_hard_gates"] is True


def test_ddo_does_not_import_or_name_existing_validation_engines() -> None:
    hits: list[str] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                if any(
                    name == prefix or name.startswith(prefix + ".")
                    for prefix in FORBIDDEN_IMPORT_PREFIXES
                ):
                    hits.append(f"{path.name}:{name}")
        for engine_name in FORBIDDEN_ENGINE_NAMES:
            if engine_name in source and path.name != "validation_producer_bindings_v0.py":
                if engine_name == "DDOExperimentIdentity":
                    hits.append(f"{path.name}:{engine_name}")
                elif engine_name in {
                    "run_walkforward_for_config",
                    "run_monte_carlo_from_returns",
                    "run_stress_test_suite",
                    "evaluate_offline_safety_kernel_boundary_v0",
                    "build_canonical_experiment_identity_v1",
                }:
                    hits.append(f"{path.name}:{engine_name}")
    assert hits == []


def test_drift_records_serialize_and_hash_deterministically() -> None:
    payload = _envelope(
        schema_name="drift_observation_record",
        schema_version="drift_observation_record_v0",
        record_id="drift-obs-wp07-0001",
        drift_domain="DATA_DRIFT",
        observation_horizon="N_BARS",
        observation_window="2026-08-01/2026-09-01",
        observed_value_ref="obs-value-1",
        reference_value_ref="ref-value-1",
        **_false_authority(),
    )
    first = build_drift_observation_record_v0(payload)
    second = build_drift_observation_record_v0(payload)
    assert first["content_hash"] == second["content_hash"]
    assert first["runtime_reachability"] is False


def test_drift_correction_is_append_only_supersession(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "drift.jsonl")
    original = build_drift_observation_record_v0(
        _envelope(
            schema_name="drift_observation_record",
            schema_version="drift_observation_record_v0",
            record_id="drift-obs-wp07-0001",
            drift_domain="FEATURE_DRIFT",
            observation_horizon="DECISION_TIME",
            observation_window="window-a",
            observed_value_ref="obs-a",
            **_false_authority(),
        )
    )
    correction = build_drift_observation_record_v0(
        _envelope(
            schema_name="drift_observation_record",
            schema_version="drift_observation_record_v0",
            record_id="drift-obs-wp07-0002",
            drift_domain="FEATURE_DRIFT",
            observation_horizon="DECISION_TIME",
            observation_window="window-a",
            observed_value_ref="obs-a-corrected",
            supersedes_id="drift-obs-wp07-0001",
            corrects_id="drift-obs-wp07-0001",
            causal_parent_ids=["drift-obs-wp07-0001"],
            **_false_authority(),
        )
    )
    ledger.append(original)
    ledger.append(correction)
    lines = (tmp_path / "drift.jsonl").read_text(encoding="utf-8").splitlines()
    replay = [json.loads(line)["payload"] for line in lines]
    assert len(replay) == 2
    assert replay[0]["record_id"] == "drift-obs-wp07-0001"
    assert replay[1]["supersedes_id"] == "drift-obs-wp07-0001"
    assert replay[0]["observed_value_ref"] == "obs-a"


def test_authority_and_safety_drift_cannot_be_economically_compensated() -> None:
    observation = build_drift_observation_record_v0(
        _envelope(
            schema_name="drift_observation_record",
            schema_version="drift_observation_record_v0",
            record_id="drift-obs-wp07-0003",
            drift_domain="SAFETY_DRIFT",
            observation_horizon="EVENT_RECOVERY",
            observation_window="window-s",
            observed_value_ref="safety-obs",
            **_false_authority(),
        )
    )
    with pytest.raises(DdoValidationError, match="ECONOMIC_COMPENSATION_OF_HARD_DRIFT_FORBIDDEN"):
        build_drift_assessment_record_v0(
            _envelope(
                schema_name="drift_assessment_record",
                schema_version="drift_assessment_record_v0",
                record_id="drift-as-wp07-0001",
                observation_refs=[observation["record_id"]],
                drift_domain="SAFETY_DRIFT",
                drift_verdict="NO_DRIFT",
                reason_code="SAFETY_REGRESSION",
                economic_verdict="ECONOMIC_PASS",
                hard_non_compensable=True,
                causal_parent_ids=[observation["record_id"]],
                **_false_authority(),
            )
        )
    assessed = build_drift_assessment_record_v0(
        _envelope(
            schema_name="drift_assessment_record",
            schema_version="drift_assessment_record_v0",
            record_id="drift-as-wp07-0002",
            observation_refs=[observation["record_id"]],
            drift_domain="AUTHORITY_DRIFT",
            drift_verdict="DRIFT_DETECTED",
            reason_code="AUTHORITY_REGRESSION",
            economic_verdict="PASS",
            hard_non_compensable=True,
            causal_parent_ids=[observation["record_id"]],
            **_false_authority(),
        )
    )
    assert assessed["hard_non_compensable"] is True
    assert assessed["drift_verdict"] == "DRIFT_DETECTED"
    assert assessed["can_auto_promote"] is False


def test_drift_contracts_cannot_promote_deploy_rollback_or_mutate() -> None:
    policy = build_drift_policy_v0(
        _envelope(
            schema_name="drift_policy",
            schema_version="drift_policy_v0",
            record_id="drift-pol-wp07-0001",
            policy_version="drift_policy_v0_fixture",
            hard_non_compensable_domains=["AUTHORITY_DRIFT", "SAFETY_DRIFT"],
            **_false_authority(),
        )
    )
    known_good = build_known_good_reference_v0(
        _envelope(
            schema_name="known_good_reference",
            schema_version="known_good_reference_v0",
            record_id="drift-kg-wp07-0001",
            reference_kind="observation",
            bound_record_ref="drift-obs-wp07-0001",
            drift_domain="DATA_DRIFT",
            **_false_authority(),
        )
    )
    for record in (policy, known_good):
        assert record["can_auto_promote"] is False
        assert record["can_auto_rollback"] is False
        assert record["can_deploy"] is False
        assert record["can_mutate_core"] is False
        assert record["can_mutate_risk"] is False
        assert record["can_mutate_safety"] is False
        assert record["runtime_reachability"] is False
        assert record["productive_authority"] == "NONE"
    with pytest.raises(DdoValidationError, match="DRIFT_CAN_AUTO_PROMOTE_MUST_BE_FALSE"):
        build_drift_policy_v0(
            _envelope(
                schema_name="drift_policy",
                schema_version="drift_policy_v0",
                record_id="drift-pol-wp07-0002",
                policy_version="bad",
                hard_non_compensable_domains=["AUTHORITY_DRIFT", "SAFETY_DRIFT"],
                **{**_false_authority(), "can_auto_promote": True},
            )
        )


def test_supervisor_remains_runtime_unreachable() -> None:
    assert AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is False
    source = (PACKAGE_DIR / "supervisor_v0.py").read_text(encoding="utf-8")
    assert "Cap 7.2" not in source or "runtime" in source.lower()
    assert CONTRACT_REGISTRY_V0["learning_productive_authority"] == "NONE"


def test_no_second_authority_created_and_registry_owns_new_schemas() -> None:
    schemas = CONTRACT_REGISTRY_V0["schemas"]
    assert "canonical_experiment_identity_ref" in schemas
    assert "drift_observation_record" in schemas
    assert "drift_assessment_record" in schemas
    assert "known_good_reference" in schemas
    assert "drift_policy" in schemas
    assert "ddo_experiment_identity" not in schemas
    assert SECOND_EXPERIMENT_IDENTITY_OWNER_CREATED is False
    build_learning_hypothesis_v0(_hypothesis())


def test_wrong_producer_for_gate_fails_closed() -> None:
    artifacts = _artifacts(bound=True)
    walk = dict(artifacts[VALIDATION_GATE_IDS_V0.index("walk_forward_pass")])
    walk["producer_id"] = PRODUCER_EXPERIMENT_MONTE_CARLO
    walk["producer_path"] = PRODUCER_PATH_BY_ID_V0[PRODUCER_EXPERIMENT_MONTE_CARLO]
    artifacts[VALIDATION_GATE_IDS_V0.index("walk_forward_pass")] = walk
    with pytest.raises(DdoValidationError, match="PRODUCER_NOT_ALLOWED_FOR_GATE"):
        admit_validation_producer_bindings_v0(artifacts)
