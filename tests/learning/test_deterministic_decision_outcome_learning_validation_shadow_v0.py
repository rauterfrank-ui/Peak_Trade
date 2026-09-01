"""WP-FA-06 offline learning registry, validation packs, and shadow challenger tests."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    LEARNING_REGISTRY_ENGINE_PRESENT,
    PROMOTION_AUTHORITY_ACTIVATION,
    RUNTIME_EFFECT,
    SHADOW_CHALLENGER_ENGINE_PRESENT,
    SHADOW_PRODUCTIVE_AUTHORITY,
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
    evaluate_validation_evidence_pack_v0,
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
