"""WP-FA-06 offline learning registry, validation packs, and shadow challenger tests."""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    DDO_EXECUTES_EXISTING_OWNER_ENGINES,
    DDO_EXISTING_OWNER_ARTIFACT_INGEST,
    DDO_TRADING_AUTHORITY,
    LEARNING_PRODUCTIVE_AUTHORITY,
    LEARNING_REGISTRY_ENGINE_PRESENT,
    MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY,
    PRODUCTIVE_DEPLOYMENT_ALLOWED,
    PRODUCTIVE_ROLLBACK_ALLOWED,
    PROMOTION_AUTHORITY_ACTIVATION,
    RUNTIME_EFFECT,
    SECOND_SAFETY_REPLAY_ENGINE_CREATED,
    SECOND_STORAGE_OWNER_CREATED,
    SECOND_WF_ENGINE_CREATED,
    SHADOW_CHALLENGER_ENGINE_PRESENT,
    SHADOW_PRODUCTIVE_AUTHORITY,
    VALIDATION_EXISTING_OWNER_BINDINGS,
    VALIDATION_PACK_ENGINE_PRESENT,
    VALIDATOR_PRODUCTIVE_AUTHORITY,
    WORKPACKAGE_ID,
)
from src.learning.deterministic_decision_outcome_v0.challenger_v0 import (
    compare_shadow_challenger_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN, VALIDATION_GATE_IDS_V0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    build_candidate_artifact_v0,
    build_learning_hypothesis_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.promotion_controller_v0 import (
    evaluate_promotion_eligibility_dry_run_v0,
    evaluate_promotion_eligibility_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_records_v0 import (
    build_promotion_policy_v0,
)
from src.learning.deterministic_decision_outcome_v0.registry_v0 import OfflineLearningRegistryV0
from src.learning.deterministic_decision_outcome_v0.validation_artifacts_v0 import (
    ARTIFACT_KIND_BY_GATE_V0,
    validate_validation_artifact_v0,
)
from src.learning.deterministic_decision_outcome_v0.validation_pack_engine_v0 import (
    VALIDATION_PACK_ENGINE_ID,
    evaluate_validation_evidence_pack_from_ingested_owners_v0,
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
    ingest_existing_owner_artifact_v0,
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


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _envelope(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "record_id": "rec-wp06-0001",
        "event_time_utc": "2026-09-01T20:00:00Z",
        "correlation_id": "cor-wp06-0001",
        "cycle_id": None,
        "causal_parent_ids": [],
        "producer_id": "offline-wp06-producer",
        "authority_owner": UNKNOWN,
        "code_sha": _sha("code"),
        "config_hash": _sha("config"),
        "evidence_hash": _sha("evidence"),
        "evidence_source_refs": ["src-evidence-wp06-1"],
    }
    payload.update(overrides)
    return payload


def _hypothesis(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="learning_hypothesis",
        schema_version="learning_hypothesis_v0",
        record_id="hyp-wp06-0001",
        proposal="offline fixture-only hypothesis",
        productive_authority="NONE",
    )
    payload.update(overrides)
    return payload


def _candidate(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="candidate_artifact",
        schema_version="candidate_artifact_v0",
        record_id="cand-wp06-0001",
        hypothesis_ref="hyp-wp06-0001",
        intended_scope="P0-offline-validation",
        expected_effect="reduce-false-positive-stale-blocks",
        promotion_class="P0",
        artifact_hash=_sha("candidate-v1"),
        dataset_ref="dataset-wp06-v1",
        experiment_ref="exp-wp06-0001",
        rejected=False,
        causal_parent_ids=["hyp-wp06-0001"],
    )
    payload.update(overrides)
    return payload


def _policy(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="promotion_policy",
        schema_version="promotion_policy_v0",
        record_id="pol-wp06-0001",
        policy_version="promotion_policy_v0_fixture",
        allowed_promotion_classes=["P0", "P1"],
        autonomous_promotion_classes=[],
        promotion_authority_activation=False,
    )
    payload.update(overrides)
    return payload


def _artifact(gate: str, *, status: str = "PASS", **overrides: Any) -> dict[str, Any]:
    payload = {
        "gate_id": gate,
        "artifact_kind": ARTIFACT_KIND_BY_GATE_V0[gate],
        "artifact_hash": _sha(f"artifact:{gate}:{status}"),
        "dataset_ref": "dataset-wp06-v1",
        "env_identity": "env-wp06-offline",
        "predicate_id": f"predicate.{gate}.v0",
        "status": status,
        "notes": None,
    }
    if status in {UNKNOWN, "INSUFFICIENT_EVIDENCE"}:
        payload["artifact_hash"] = UNKNOWN
    payload.update(overrides)
    return payload


def _artifacts(**status_overrides: str) -> list[dict[str, Any]]:
    return [
        _artifact(gate, status=status_overrides.get(gate, "PASS"))
        for gate in VALIDATION_GATE_IDS_V0
    ]


def _identity(**overrides: Any) -> dict[str, Any]:
    payload = {
        "record_id": "pack-wp06-0001",
        "event_time_utc": "2026-09-01T20:00:00Z",
        "correlation_id": "cor-wp06-0001",
        "code_sha": _sha("code"),
        "config_hash": _sha("config"),
        "dataset_ref": "dataset-wp06-v1",
        "environment_fingerprint": "env-wp06-offline",
    }
    payload.update(overrides)
    return payload


def test_wp_fa_06_authority_markers_remain_non_authorizing() -> None:
    assert WORKPACKAGE_ID == ("WP_FA_07_OFFLINE_OWNER_BINDINGS_AND_DRIFT_CONTRACTS_V1")
    assert LEARNING_REGISTRY_ENGINE_PRESENT is True
    assert VALIDATION_PACK_ENGINE_PRESENT is True
    assert SHADOW_CHALLENGER_ENGINE_PRESENT is True
    assert RUNTIME_EFFECT == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert VALIDATOR_PRODUCTIVE_AUTHORITY == "NONE"
    assert SHADOW_PRODUCTIVE_AUTHORITY == "NONE"
    assert PROMOTION_AUTHORITY_ACTIVATION is False


def test_pass_without_evidence_hash_is_forbidden() -> None:
    with pytest.raises(DdoValidationError, match="PASS_WITHOUT_EVIDENCE_FORBIDDEN"):
        validate_validation_artifact_v0(
            _artifact("deterministic_replay_pass", artifact_hash=UNKNOWN)
        )


def test_missing_gate_artifact_fails_closed() -> None:
    incomplete = _artifacts()[:-1]
    with pytest.raises(DdoValidationError, match="MISSING_EVIDENCE_ARTIFACT"):
        evaluate_validation_evidence_pack_v0(
            candidate=_candidate(),
            artifacts=incomplete,
            identity=_identity(),
        )


def test_unversioned_candidate_cannot_enter_evaluated_validation() -> None:
    with pytest.raises(DdoValidationError, match="UNVERSIONED_CANDIDATE_FORBIDDEN"):
        evaluate_validation_evidence_pack_v0(
            candidate=_candidate(artifact_hash=UNKNOWN),
            artifacts=_artifacts(),
            identity=_identity(),
        )


def test_unknown_gate_status_is_preserved_not_normalized() -> None:
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=_candidate(),
        artifacts=_artifacts(monte_carlo_pass=UNKNOWN),
        identity=_identity(),
    )
    pack = evaluated["validation_evidence_pack"]
    assert pack["gates"]["monte_carlo_pass"] == UNKNOWN
    assert evaluated["unknown_collapsed"] is False
    assert pack["gates"]["monte_carlo_pass"] not in {False, 0, ""}


def test_safety_regression_cannot_be_compensated_by_economic_pass() -> None:
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=_candidate(),
        artifacts=_artifacts(safety_regression_pass="FAIL", economic_policy_pass="PASS"),
        identity=_identity(),
    )
    pack = evaluated["validation_evidence_pack"]
    assert pack["gates"]["safety_regression_pass"] == "FAIL"
    assert pack["gates"]["economic_policy_pass"] == "PASS"
    assert "safety_regression_pass" in evaluated["hard_gate_failures"]
    assert evaluated["economic_improvement_cannot_compensate_hard_gates"] is True
    eligibility = evaluate_promotion_eligibility_v0(
        policy=build_promotion_policy_v0(_policy()),
        candidate=build_candidate_artifact_v0(_candidate()),
        evidence_pack=pack,
        eligibility_record_id="elig-wp06-0001",
        event_time_utc="2026-09-01T20:00:00Z",
        correlation_id="cor-wp06-0001",
        producer_id="offline-wp06-producer",
        causal_parent_ids=["cand-wp06-0001", "pack-wp06-0001", "pol-wp06-0001"],
    )
    assert eligibility["eligible"] is False
    assert eligibility["deployment_authorized"] is False
    assert "safety_regression_pass" in eligibility["failed_gates"]


def test_validation_pack_hash_is_stable_and_idempotent() -> None:
    first = evaluate_validation_evidence_pack_v0(
        candidate=_candidate(),
        artifacts=_artifacts(),
        identity=_identity(),
        incumbent=_candidate(record_id="cand-wp06-0002", intended_scope="incumbent"),
    )
    second = evaluate_validation_evidence_pack_v0(
        candidate=_candidate(),
        artifacts=_artifacts(),
        identity=_identity(),
        incumbent=_candidate(record_id="cand-wp06-0002", intended_scope="incumbent"),
    )
    assert (
        first["validation_evidence_pack"]["content_hash"]
        == (second["validation_evidence_pack"]["content_hash"])
    )
    assert first["validation_evidence_pack"]["producer_id"] == VALIDATION_PACK_ENGINE_ID
    assert first["validator_productive_authority"] == "NONE"
    assert first["runtime_wiring"] is False


def test_rejected_candidate_retention_and_supersession(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "registry.jsonl")
    registry = OfflineLearningRegistryV0(ledger)
    registry.register_hypothesis(_hypothesis())
    rejected = _candidate(rejected=True, artifact_hash=_sha("rejected-v1"))
    registry.register_candidate(rejected)
    successor = _candidate(
        record_id="cand-wp06-0003",
        artifact_hash=_sha("candidate-v2"),
        supersedes_id="cand-wp06-0001",
        causal_parent_ids=["hyp-wp06-0001", "cand-wp06-0001"],
    )
    registry.register_candidate(successor)
    kept = registry.candidates(include_rejected=True)
    assert any(row["record_id"] == "cand-wp06-0001" and row["rejected"] is True for row in kept)
    lineage = registry.candidate_lineage("cand-wp06-0003")
    assert lineage["hypothesis_ref"] == "hyp-wp06-0001"
    assert lineage["experiment_ref"] == "exp-wp06-0001"
    assert lineage["supersedes_id"] == "cand-wp06-0001"
    assert lineage["rejected"] is False
    superseded = registry.candidate_lineage("cand-wp06-0001")
    assert superseded["is_superseded"] is True
    assert superseded["rejected"] is True


def test_evaluated_pack_registration_requires_versioned_candidate(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "registry.jsonl")
    registry = OfflineLearningRegistryV0(ledger)
    registry.register_hypothesis(_hypothesis())
    registry.register_candidate(_candidate())
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=_candidate(),
        artifacts=_artifacts(),
        identity=_identity(),
    )
    result = registry.register_evaluated_validation_pack(evaluated["validation_evidence_pack"])
    assert result.status == "APPENDED"
    replay = registry.register_evaluated_validation_pack(evaluated["validation_evidence_pack"])
    assert replay.status == "IDEMPOTENT_REPLAY"
    with pytest.raises(DdoValidationError, match="UNVERSIONED_CANDIDATE_FORBIDDEN"):
        orphan = AppendOnlyDdoLedgerV0(tmp_path / "orphan.jsonl")
        bad = OfflineLearningRegistryV0(orphan)
        bad.register_hypothesis(_hypothesis())
        bad.register_candidate(_candidate(artifact_hash=UNKNOWN))
        bad.register_evaluated_validation_pack(evaluated["validation_evidence_pack"])


def test_shadow_requires_identical_pack_and_pins_candidate_identity() -> None:
    incumbent = _candidate(record_id="cand-wp06-0002", intended_scope="incumbent")
    candidate = _candidate()
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=candidate,
        artifacts=_artifacts(),
        identity=_identity(),
        incumbent=incumbent,
    )
    pack = evaluated["validation_evidence_pack"]
    comparison = compare_shadow_challenger_v0(
        incumbent=incumbent,
        candidate=candidate,
        evidence_pack=pack,
        incumbent_decisions=[
            {
                "record_id": "dec-1",
                "decision_type": "NO_ENTRY",
                "decision_result": "NO_ACTION",
            }
        ],
        candidate_decisions=[
            {
                "record_id": "dec-1",
                "decision_type": "STALE_BLOCK",
                "decision_result": "NO_ACTION",
            }
        ],
        incumbent_incidents=[{"record_id": "inc-1", "incident_class": "STALE"}],
        candidate_incidents=[],
        incumbent_metrics={"net_pnl_token": "BASELINE"},
        candidate_metrics={"net_pnl_token": "IMPROVED", "drawdown_token": UNKNOWN},
        incumbent_gates={gate: "PASS" for gate in VALIDATION_GATE_IDS_V0},
    )
    assert comparison["identical_evidence_pack"] is True
    assert comparison["candidate_artifact_hash"] == candidate["artifact_hash"]
    assert comparison["productive_authority"] == "NONE"
    assert comparison["becomes_authoritative"] is False
    assert comparison["incumbent_mutated"] is False
    assert comparison["comparison_cannot_authorize_promotion"] is True
    assert comparison["decision_deltas"][0]["changed"] is True
    assert comparison["incident_deltas"][0]["candidate_present"] is False
    assert comparison["incident_deltas"][0]["candidate_incident_class"] == UNKNOWN
    assert comparison["metric_deltas"]["drawdown_token"]["incumbent"] == UNKNOWN
    assert comparison["metric_deltas"]["drawdown_token"]["candidate"] == UNKNOWN


def test_shadow_safety_fail_with_improved_pnl_remains_non_authoritative() -> None:
    incumbent = _candidate(record_id="cand-wp06-0002", intended_scope="incumbent")
    candidate = _candidate()
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=candidate,
        artifacts=_artifacts(safety_regression_pass="FAIL", economic_policy_pass="PASS"),
        identity=_identity(),
        incumbent=incumbent,
    )
    comparison = compare_shadow_challenger_v0(
        incumbent=incumbent,
        candidate=candidate,
        evidence_pack=evaluated["validation_evidence_pack"],
        incumbent_metrics={"net_pnl_token": "BASELINE"},
        candidate_metrics={"net_pnl_token": "IMPROVED"},
        incumbent_gates={gate: "PASS" for gate in VALIDATION_GATE_IDS_V0},
    )
    assert comparison["safety_regression"] is True
    assert comparison["metric_deltas"]["net_pnl_token"]["changed"] is True
    assert comparison["economic_improvement_cannot_compensate"] is True
    assert comparison["promotion_authority"] == "NONE"
    assert comparison["execution_effect"] == "NONE"


def test_shadow_rejects_mismatched_evidence_pack() -> None:
    incumbent = _candidate(record_id="cand-wp06-0002", intended_scope="incumbent")
    candidate = _candidate()
    other = _candidate(record_id="cand-wp06-0009", intended_scope="other")
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=candidate,
        artifacts=_artifacts(),
        identity=_identity(),
        incumbent=incumbent,
    )
    with pytest.raises(DdoValidationError, match="CHALLENGER_PACK_CANDIDATE_MISMATCH"):
        compare_shadow_challenger_v0(
            incumbent=incumbent,
            candidate=other,
            evidence_pack=evaluated["validation_evidence_pack"],
        )


def test_shadow_hash_stability() -> None:
    incumbent = _candidate(record_id="cand-wp06-0002", intended_scope="incumbent")
    candidate = _candidate()
    pack = evaluate_validation_evidence_pack_v0(
        candidate=candidate,
        artifacts=_artifacts(),
        identity=_identity(),
        incumbent=incumbent,
    )["validation_evidence_pack"]
    first = compare_shadow_challenger_v0(
        incumbent=incumbent,
        candidate=candidate,
        evidence_pack=pack,
        incumbent_metrics={"net_pnl_token": UNKNOWN},
        candidate_metrics={"net_pnl_token": UNKNOWN},
    )
    second = compare_shadow_challenger_v0(
        incumbent=incumbent,
        candidate=candidate,
        evidence_pack=pack,
        incumbent_metrics={"net_pnl_token": UNKNOWN},
        candidate_metrics={"net_pnl_token": UNKNOWN},
    )
    assert first == second


def test_wp_fa_06_modules_have_no_forbidden_imports() -> None:
    hits: list[str] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
    assert hits == []


def test_learning_hypothesis_roundtrip_hash_stable() -> None:
    first = build_learning_hypothesis_v0(_hypothesis())
    second = build_learning_hypothesis_v0(_hypothesis())
    assert first["content_hash"] == second["content_hash"]
    assert first["productive_authority"] == "NONE"


_MANDATORY_INGEST_PRODUCER = {
    "walk_forward_pass": PRODUCER_WALK_FORWARD,
    "monte_carlo_pass": PRODUCER_EXPERIMENT_MONTE_CARLO,
    "stress_pass": PRODUCER_STRESS,
    "fault_injection_pass": PRODUCER_O6_FAULT_HEALTH,
    "safety_regression_pass": PRODUCER_SAFETY_REPLAY,
    "rollback_ready": PRODUCER_ROLLBACK_READINESS,
}

_BANNED_OWNER_ENGINE_MODULES = (
    "src.backtest.walkforward",
    "src.experiments.monte_carlo",
    "src.risk.monte_carlo",
    "src.experiments.stress_tests",
    "src.experiments.canonical_robustness_suite_v1",
    "src.execution.fault_injection",
    "src.trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0",
    "src.meta.learning_loop.runtime_eligibility_v1",
    "src.ops.runtime_health_recovery_and_failure_injection_closure_v1",
)


def _ingest_envelope(gate: str, *, status: str = "PASS", **overrides: Any) -> dict[str, Any]:
    digest = _sha(f"ingest:{gate}:{status}")
    payload: dict[str, Any] = {
        "gate_id": gate,
        "artifact_kind": ARTIFACT_KIND_BY_GATE_V0[gate],
        "status": status,
        "content_hash": digest if status == "PASS" else UNKNOWN,
        "artifact_ref": f"ref-{gate}",
        "artifact_id": f"id-{gate}",
        "predicate_id": f"predicate.{gate}.v0",
        "dataset_ref": "dataset-wp06-v1",
        "environment_fingerprint": "env-wp06-offline",
        "env_identity": "env-wp06-offline",
        "opaque_payload": {"owner_token": f"opaque-{gate}", "nested": {"kept": "as-is"}},
        "metric_refs": [f"metric-{gate}"],
    }
    if status in {UNKNOWN, "INSUFFICIENT_EVIDENCE"}:
        payload["content_hash"] = UNKNOWN
        payload["artifact_ref"] = UNKNOWN
    producer_id = _MANDATORY_INGEST_PRODUCER.get(gate)
    if producer_id is not None:
        payload.update(
            {
                "producer_id": producer_id,
                "producer_path": PRODUCER_PATH_BY_ID_V0[producer_id],
                "producer_schema_version": PRODUCER_SCHEMA_BY_ID_V0[producer_id],
                "source_owner": producer_id,
                "compatibility_status": "COMPATIBLE",
                "failure_semantics": "FAIL_CLOSED",
                "claimed_artifact_hash": payload["content_hash"],
                "run_identity": f"run-{gate}",
            }
        )
    else:
        payload.update(
            {
                "producer_id": UNKNOWN,
                "compatibility_status": UNKNOWN,
                "failure_semantics": UNKNOWN,
            }
        )
    payload.update(overrides)
    return payload


def _ingested_artifacts(**status_overrides: str) -> list[dict[str, Any]]:
    return [
        _ingest_envelope(gate, status=status_overrides.get(gate, "PASS"))
        for gate in VALIDATION_GATE_IDS_V0
    ]


def test_existing_owner_ingest_accepts_valid_artifact_identity() -> None:
    envelope = _ingest_envelope("walk_forward_pass")
    ingested = ingest_existing_owner_artifact_v0(envelope)
    assert ingested["producer_id"] == PRODUCER_WALK_FORWARD
    assert ingested["content_hash"] == envelope["content_hash"]
    assert ingested["opaque_payload"] == {
        "owner_token": "opaque-walk_forward_pass",
        "nested": {"kept": "as-is"},
    }
    assert ingested["ddo_executes_existing_owner_engines"] is False
    assert ingested["ingest_identity_hash"] != UNKNOWN
    again = ingest_existing_owner_artifact_v0(envelope)
    assert again["ingest_identity_hash"] == ingested["ingest_identity_hash"]
    assert VALIDATION_EXISTING_OWNER_BINDINGS == "BOUND_ARTIFACT_INGEST_NO_ENGINE_EXECUTE"
    assert DDO_EXISTING_OWNER_ARTIFACT_INGEST is True
    assert DDO_EXECUTES_EXISTING_OWNER_ENGINES is False


def test_existing_owner_ingest_rejects_unknown_producer() -> None:
    with pytest.raises(DdoValidationError, match="UNKNOWN_EXISTING_OWNER_PRODUCER"):
        ingest_existing_owner_artifact_v0(
            _ingest_envelope("walk_forward_pass", producer_id="src.invented.second_wf_engine")
        )


def test_existing_owner_ingest_schema_mismatch_is_explicit() -> None:
    with pytest.raises(DdoValidationError, match="PRODUCER_SCHEMA_MISMATCH"):
        ingest_existing_owner_artifact_v0(
            _ingest_envelope(
                "rollback_ready",
                producer_schema_version="not-the-owner-schema",
                artifact_schema_version="not-the-owner-schema",
            )
        )


def test_existing_owner_ingest_missing_required_path_is_explicit() -> None:
    with pytest.raises(DdoValidationError, match="MISSING_REQUIRED_REF:producer_path"):
        ingest_existing_owner_artifact_v0(
            _ingest_envelope("walk_forward_pass", producer_path=UNKNOWN)
        )


def test_existing_owner_ingest_keeps_opaque_payload_opaque() -> None:
    ingested = ingest_existing_owner_artifact_v0(
        _ingest_envelope(
            "stress_pass",
            opaque_payload={"raw_owner_blob": "do-not-reinterpret", "status_token": "PASS"},
        )
    )
    assert ingested["opaque_payload"]["raw_owner_blob"] == "do-not-reinterpret"
    assert ingested["status"] == "PASS"
    assert "raw_owner_blob" not in ingested["producer_id"]


def test_ingest_path_does_not_import_or_execute_owner_engines() -> None:
    before = {name for name in _BANNED_OWNER_ENGINE_MODULES if name in sys.modules}
    ingest_existing_owner_artifact_v0(_ingest_envelope("walk_forward_pass"))
    evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(),
        identity=_identity(),
    )
    after = {name for name in _BANNED_OWNER_ENGINE_MODULES if name in sys.modules}
    assert after == before
    hits: list[str] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "mutation_critical_control_state_storage_v1" in source and path.name in {
            "validation_producer_bindings_v0.py",
            "validation_pack_engine_v0.py",
            "promotion_controller_v0.py",
            "promotion_records_v0.py",
        }:
            hits.append(path.name)
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
                    for prefix in _BANNED_OWNER_ENGINE_MODULES
                ):
                    hits.append(f"{path.name}:{name}")
    assert hits == []


def test_ingested_pack_complete_passing_and_failed_gate() -> None:
    passing = evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(),
        identity=_identity(),
    )
    pack = passing["validation_evidence_pack"]
    assert all(pack["gates"][gate] == "PASS" for gate in VALIDATION_GATE_IDS_V0)
    assert passing["unknown_preserved"] is True
    assert passing["missing_evidence_fails_closed"] is True
    assert passing["ddo_executes_existing_owner_engines"] is False
    assert passing["gate_source_refs"]["walk_forward_pass"]["producer_id"] == PRODUCER_WALK_FORWARD
    failed = evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(safety_regression_pass="FAIL"),
        identity=_identity(record_id="pack-wp06-fail1"),
    )
    assert failed["validation_evidence_pack"]["gates"]["safety_regression_pass"] == "FAIL"
    assert "safety_regression_pass" in failed["hard_gate_failures"]
    assert failed["validation_evidence_pack"]["gates"]["economic_policy_pass"] == "PASS"


def test_ingested_pack_missing_mandatory_gate_is_not_pass() -> None:
    incomplete = [item for item in _ingested_artifacts() if item["gate_id"] != "walk_forward_pass"]
    with pytest.raises(DdoValidationError, match="MISSING_EVIDENCE_ARTIFACT"):
        evaluate_validation_evidence_pack_from_ingested_owners_v0(
            candidate=_candidate(),
            ingested_artifacts=incomplete,
            identity=_identity(),
        )


def test_ingested_pack_unknown_is_preserved_and_hash_is_stable() -> None:
    first = evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(monte_carlo_pass=UNKNOWN),
        identity=_identity(),
    )
    second = evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(monte_carlo_pass=UNKNOWN),
        identity=_identity(),
    )
    assert first["validation_evidence_pack"]["gates"]["monte_carlo_pass"] == UNKNOWN
    assert first["unknown_collapsed"] is False
    assert "monte_carlo_pass" in first["unknown_gates"]
    assert (
        first["validation_evidence_pack"]["content_hash"]
        == second["validation_evidence_pack"]["content_hash"]
    )


def test_promotion_eligibility_dry_run_fail_closed_and_no_deployment() -> None:
    passing = evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(),
        identity=_identity(),
    )
    eligible = evaluate_promotion_eligibility_dry_run_v0(
        policy=build_promotion_policy_v0(_policy()),
        candidate=build_candidate_artifact_v0(_candidate()),
        evidence_pack=passing["validation_evidence_pack"],
        eligibility_record_id="elig-wp06-dry1",
        event_time_utc="2026-09-01T20:00:00Z",
        correlation_id="cor-wp06-0001",
        producer_id="offline-wp06-producer",
        code_sha=_sha("code"),
        config_hash=_sha("config"),
        evidence_hash=passing["validation_evidence_pack"]["evidence_hash"],
        release_record_id="rel-wp06-dry1",
        checksum=_sha("release"),
        previous_known_good_ref="rel-wp06-good",
        environment=UNKNOWN,
    )
    assert eligible["eligibility_record"]["eligible"] is True
    assert eligible["deployment_authorized"] is False
    assert eligible["execution_authorized"] is False
    assert eligible["productive_activation"] is False
    assert eligible["promotion_authority_activation"] is False
    lineage = eligible["release_deployment_rollback_dry_run"]
    assert lineage["candidate_artifact_ref"] == "cand-wp06-0001"
    assert lineage["validation_evidence_pack_ref"] == "pack-wp06-0001"
    assert lineage["eligibility_record_ref"] == "elig-wp06-dry1"
    assert lineage["deployment_authorized"] is False
    assert lineage["productive_activation"] is False
    assert lineage["deployment_record"]["activation_authorized"] is False
    assert lineage["rollback_record"]["productive_rollback_authorized"] is False
    failed = evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(authority_invariants_pass="FAIL"),
        identity=_identity(record_id="pack-wp06-authf"),
    )
    ineligible = evaluate_promotion_eligibility_dry_run_v0(
        policy=build_promotion_policy_v0(_policy()),
        candidate=build_candidate_artifact_v0(_candidate()),
        evidence_pack=failed["validation_evidence_pack"],
        eligibility_record_id="elig-wp06-dry2",
        event_time_utc="2026-09-01T20:00:00Z",
        correlation_id="cor-wp06-0001",
        producer_id="offline-wp06-producer",
    )
    assert ineligible["eligibility_record"]["eligible"] is False
    assert "authority_invariants_pass" in ineligible["hard_gate_failures"]
    unknown = evaluate_validation_evidence_pack_from_ingested_owners_v0(
        candidate=_candidate(),
        ingested_artifacts=_ingested_artifacts(rollback_ready=UNKNOWN),
        identity=_identity(record_id="pack-wp06-unk1"),
    )
    unknown_elig = evaluate_promotion_eligibility_dry_run_v0(
        policy=build_promotion_policy_v0(_policy()),
        candidate=build_candidate_artifact_v0(_candidate()),
        evidence_pack=unknown["validation_evidence_pack"],
        eligibility_record_id="elig-wp06-dry3",
        event_time_utc="2026-09-01T20:00:00Z",
        correlation_id="cor-wp06-0001",
        producer_id="offline-wp06-producer",
    )
    assert unknown_elig["eligibility_record"]["eligible"] is False
    assert "rollback_ready" in unknown_elig["unknown_gates"]


def test_authority_and_durability_invariants_remain_fail_closed() -> None:
    from src.learning.deterministic_decision_outcome_v0.a1_crash_durability_proof_or_explicit_nonprovability_closure_v1 import (
        DURABILITY_PROVEN_TRUE_MANUFACTURABLE,
        HOST_CRASH_DURABILITY,
        POWER_LOSS_DURABILITY,
    )
    from src.learning.mutation_critical_control_state_storage_v1.authority_v1 import (
        ADMISSION_TRUE,
        DEPENDENT_MUTATION_ALLOWED,
        PRODUCTIVE_HOST_BINDING,
    )
    from src.learning.mutation_critical_control_state_storage_v1.crash_reproof_v1 import (
        DEPENDENT_MUTATION_ALLOWED as CRASH_DEPENDENT_MUTATION_ALLOWED,
        HOST_CRASH_DURABILITY as CRASH_HOST_CRASH_DURABILITY,
        POWER_LOSS_DURABILITY as CRASH_POWER_LOSS_DURABILITY,
    )

    assert WORKPACKAGE_ID == "WP_FA_07_OFFLINE_OWNER_BINDINGS_AND_DRIFT_CONTRACTS_V1"
    assert DDO_TRADING_AUTHORITY == "NONE"
    assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True
    assert SECOND_WF_ENGINE_CREATED is False
    assert SECOND_SAFETY_REPLAY_ENGINE_CREATED is False
    assert SECOND_STORAGE_OWNER_CREATED is False
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert PRODUCTIVE_DEPLOYMENT_ALLOWED is False
    assert PRODUCTIVE_ROLLBACK_ALLOWED is False
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert DURABILITY_PROVEN_TRUE_MANUFACTURABLE is False
    assert DEPENDENT_MUTATION_ALLOWED is False
    assert PRODUCTIVE_HOST_BINDING is False
    assert ADMISSION_TRUE is False
    assert CRASH_HOST_CRASH_DURABILITY == "UNPROVEN"
    assert CRASH_POWER_LOSS_DURABILITY == "UNPROVEN"
    assert CRASH_DEPENDENT_MUTATION_ALLOWED is False
