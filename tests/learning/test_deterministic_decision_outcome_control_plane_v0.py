"""Offline DDO WP-FA-03 remaining record contracts and control-plane tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTONOMY_SUPERVISOR_EXECUTION_AUTHORITY,
    AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
    PROMOTION_AUTHORITY_ACTIVATION,
    PROMOTION_AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
)
from src.learning.deterministic_decision_outcome_v0.challenger_v0 import compare_challenger_v0
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import CONTRACT_REGISTRY_V0
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN, VALIDATION_GATE_IDS_V0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoLineageError,
    DdoValidationError,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    build_attribution_record_v0,
    build_counterfactual_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_v0 import (
    evaluate_attribution_v0,
    evaluate_counterfactual_v0,
    evaluate_outcome_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    build_candidate_artifact_v0,
    build_learning_hypothesis_v0,
    build_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_controller_v0 import (
    evaluate_promotion_eligibility_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_records_v0 import (
    build_deployment_record_v0,
    build_promotion_policy_v0,
    build_release_artifact_v0,
)
from src.learning.deterministic_decision_outcome_v0.registry_v0 import OfflineLearningRegistryV0
from src.learning.deterministic_decision_outcome_v0.replay_evaluator_v0 import (
    classify_decision_event_v0,
    replay_same_inputs_same_classification_v0,
)
from src.learning.deterministic_decision_outcome_v0.supervisor_records_v0 import (
    build_health_snapshot_v0,
)
from src.learning.deterministic_decision_outcome_v0.supervisor_v0 import (
    DeterministicAutonomySupervisorV0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
SECTION_24_SCHEMAS = (
    "decision_event",
    "incident_record",
    "outcome_record",
    "counterfactual_record",
    "attribution_record",
    "learning_hypothesis",
    "candidate_artifact",
    "validation_evidence_pack",
    "promotion_eligibility_record",
    "promotion_policy",
    "release_artifact",
    "deployment_record",
    "rollback_record",
    "autonomy_cycle_record",
    "health_snapshot",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.governance.promotion",
    "src.meta.learning_loop",
    "src.ops",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "http.client",
)


def _envelope(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "record_id": "rec-0001",
        "event_time_utc": "2026-09-01T12:00:00Z",
        "correlation_id": "cor-0001",
        "cycle_id": None,
        "causal_parent_ids": [],
        "producer_id": "offline-test-producer",
        "authority_owner": UNKNOWN,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "evidence_hash": UNKNOWN,
        "evidence_source_refs": ["src-evidence-1"],
    }
    payload.update(overrides)
    return payload


def _decision(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="decision_event",
        schema_version="decision_event_v0",
        record_id="dec-0001",
        event_id="evt-0001",
        decision_type="NO_ENTRY",
        decision_result="NO_ACTION",
        reason_codes=[
            {
                "taxonomy_id": "blueprint.ddo.reason_v0",
                "code": "NO_ENTRY",
                "source_taxonomy_ref": None,
            }
        ],
        hard_block_reasons=[],
        decision_time_information_set_ref="info-set-1",
        market_snapshot_ref=None,
        feature_snapshot_ref=None,
        data_quality_ref=None,
        risk_snapshot_ref=None,
        position_snapshot_ref=None,
        selected_instrument_ref=None,
    )
    payload.update(overrides)
    return payload


def _health(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="health_snapshot",
        schema_version="health_snapshot_v0",
        record_id="hlth-0001",
        freshness_readiness=UNKNOWN,
        dependency_readiness=UNKNOWN,
        venue_account_readiness=UNKNOWN,
        permission_readiness=UNKNOWN,
        safety_readiness=UNKNOWN,
        clock_trust=UNKNOWN,
        ledger_integrity=UNKNOWN,
        execution_permit=False,
    )
    payload.update(overrides)
    return payload


def _hypothesis(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="learning_hypothesis",
        schema_version="learning_hypothesis_v0",
        record_id="hyp-0001",
        proposal="fixture-only hypothesis",
        productive_authority="NONE",
    )
    payload.update(overrides)
    return payload


def _candidate(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="candidate_artifact",
        schema_version="candidate_artifact_v0",
        record_id="cand-0001",
        hypothesis_ref="hyp-0001",
        intended_scope="P0-evidence-only",
        promotion_class="P0",
        artifact_hash=UNKNOWN,
        rejected=False,
        causal_parent_ids=["hyp-0001"],
    )
    payload.update(overrides)
    return payload


def _gates(*, safety: str = "PASS", economic: str = "PASS", **overrides: str) -> dict[str, str]:
    values = {gate: "PASS" for gate in VALIDATION_GATE_IDS_V0}
    values["safety_regression_pass"] = safety
    values["economic_policy_pass"] = economic
    values.update(overrides)
    return values


def _pack(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="validation_evidence_pack",
        schema_version="validation_evidence_pack_v0",
        record_id="pack-0001",
        candidate_artifact_ref="cand-0001",
        incumbent_artifact_ref="cand-0002",
        gates=_gates(),
        causal_parent_ids=["cand-0001"],
    )
    payload.update(overrides)
    return payload


def _policy(**overrides: Any) -> dict[str, Any]:
    payload = _envelope(
        schema_name="promotion_policy",
        schema_version="promotion_policy_v0",
        record_id="pol-0001",
        policy_version="promotion_policy_v0_fixture",
        allowed_promotion_classes=["P0", "P1"],
        autonomous_promotion_classes=[],
        promotion_authority_activation=False,
    )
    payload.update(overrides)
    return payload


def test_authority_markers_remain_non_activating() -> None:
    assert RUNTIME_EFFECT == "NONE"
    assert PROMOTION_AUTHORITY_EFFECT == "NONE"
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is False
    assert AUTONOMY_SUPERVISOR_EXECUTION_AUTHORITY is False


def test_section_24_schemas_are_registered_with_nullability_and_hash_scope() -> None:
    schemas = CONTRACT_REGISTRY_V0["schemas"]
    for name in SECTION_24_SCHEMAS:
        assert name in schemas
        fields = schemas[name]["fields"]
        field_names = {field["name"] for field in fields}
        assert "record_id" in field_names or name == "outcome_record"
        assert all(
            field["nullability"] in {"REQUIRED", "OPTIONAL", "CONDITIONALLY_REQUIRED"}
            for field in fields
        )
        assert any(
            field["name"] == "content_hash" and field["in_content_hash"] is False
            for field in fields
        )


def test_unknown_and_unavailable_are_first_class() -> None:
    record = build_counterfactual_record_v0(
        _envelope(
            schema_name="counterfactual_record",
            schema_version="counterfactual_record_v0",
            record_id="cfactual-0001",
            decision_event_ref="dec-0001",
            counterfactual_admissibility="UNAVAILABLE",
            alternative_result_ref=None,
            causal_parent_ids=["dec-0001"],
        )
    )
    assert record["counterfactual_admissibility"] == "UNAVAILABLE"
    with pytest.raises(DdoValidationError, match="UNAVAILABLE_COUNTERFACTUAL"):
        build_counterfactual_record_v0(
            _envelope(
                schema_name="counterfactual_record",
                schema_version="counterfactual_record_v0",
                record_id="cfactual-0002",
                decision_event_ref="dec-0001",
                counterfactual_admissibility="UNAVAILABLE",
                alternative_result_ref="alt-1",
            )
        )
    with pytest.raises(DdoValidationError, match="MODELLED_COUNTERFACTUAL_REQUIRES_ASSUMPTIONS"):
        build_counterfactual_record_v0(
            _envelope(
                schema_name="counterfactual_record",
                schema_version="counterfactual_record_v0",
                record_id="cfactual-0003",
                decision_event_ref="dec-0001",
                counterfactual_admissibility="MODELLED",
            )
        )


def test_replay_is_deterministic_and_core_unreachable() -> None:
    first = build_decision_event_v0(_decision())
    second = build_decision_event_v0(_decision())
    left = classify_decision_event_v0(first)
    right = replay_same_inputs_same_classification_v0(first, second)
    assert left["decision_type"] == "NO_ENTRY"
    assert left["content_hash"] == right["content_hash"]
    assert left["hindsight_leakage"] is False
    changed = build_decision_event_v0(_decision(decision_type="NO_EXIT"))
    with pytest.raises(DdoValidationError, match="REPLAY_CLASSIFICATION_DIVERGED"):
        replay_same_inputs_same_classification_v0(first, changed)


def test_hindsight_cannot_relabel_safety_correctness() -> None:
    decision = build_decision_event_v0(_decision())
    attribution = build_attribution_record_v0(
        _envelope(
            schema_name="attribution_record",
            schema_version="attribution_record_v0",
            record_id="attr-0001",
            decision_event_ref="dec-0001",
            kill_switch_correctness="TRUE_POSITIVE",
            safety_correctness_uses_decision_time_information_set=True,
            causal_parent_ids=["dec-0001"],
        )
    )
    evaluated = evaluate_attribution_v0(attribution)
    assert evaluated["kill_switch_correctness"] == "TRUE_POSITIVE"
    with pytest.raises(DdoValidationError, match="HINDSIGHT_CANNOT_RELABEL"):
        evaluate_attribution_v0(
            attribution,
            later_economic_path={"kill_switch_correctness": "FALSE_POSITIVE"},
        )
    counterfactual = build_counterfactual_record_v0(
        _envelope(
            schema_name="counterfactual_record",
            schema_version="counterfactual_record_v0",
            record_id="cfactual-0004",
            decision_event_ref="dec-0001",
            counterfactual_admissibility="REPLAYABLE",
            decision_time_information_set_ref="info-set-1",
            causal_parent_ids=["dec-0001"],
        )
    )
    replayed = evaluate_counterfactual_v0(counterfactual, decision_event=decision)
    assert replayed["uses_decision_time_information_set"] is True


def test_learning_registry_requires_hypothesis_lineage(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "registry.jsonl")
    registry = OfflineLearningRegistryV0(ledger)
    registry.register_hypothesis(_hypothesis())
    registry.register_candidate(_candidate())
    assert len(registry.candidates()) == 1
    with pytest.raises(DdoLineageError, match="HYPOTHESIS_REF_MISSING"):
        orphan = AppendOnlyDdoLedgerV0(tmp_path / "orphan.jsonl")
        OfflineLearningRegistryV0(orphan).register_candidate(_candidate(causal_parent_ids=[]))


def test_rejected_candidates_remain_auditable(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "registry.jsonl")
    registry = OfflineLearningRegistryV0(ledger)
    registry.register_hypothesis(_hypothesis())
    registry.register_candidate(_candidate(rejected=True))
    kept = registry.candidates(include_rejected=True)
    assert kept[0]["rejected"] is True
    assert registry.candidates(include_rejected=False) == ()


def test_validation_pack_and_challenger_share_identical_evidence(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "registry.jsonl")
    registry = OfflineLearningRegistryV0(ledger)
    registry.register_hypothesis(_hypothesis())
    incumbent = _candidate(record_id="cand-0002", intended_scope="incumbent")
    candidate = _candidate(record_id="cand-0001")
    registry.register_candidate(incumbent)
    registry.register_candidate(candidate)
    pack = build_validation_evidence_pack_v0(_pack(causal_parent_ids=["cand-0001", "cand-0002"]))
    registry.register_validation_pack(pack)
    comparison = compare_challenger_v0(incumbent=incumbent, candidate=candidate, evidence_pack=pack)
    assert comparison["identical_evidence_pack"] is True
    assert comparison["productive_authority"] == "NONE"


def test_eligibility_is_deterministic_and_safety_cannot_be_compensated() -> None:
    hypothesis = build_learning_hypothesis_v0(_hypothesis())
    candidate = build_candidate_artifact_v0(_candidate())
    policy = build_promotion_policy_v0(_policy())
    passing = build_validation_evidence_pack_v0(_pack(incumbent_artifact_ref=None))
    first = evaluate_promotion_eligibility_v0(
        policy=policy,
        candidate=candidate,
        evidence_pack=passing,
        eligibility_record_id="elig-0001",
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="cor-0001",
        producer_id="offline-test-producer",
    )
    second = evaluate_promotion_eligibility_v0(
        policy=policy,
        candidate=candidate,
        evidence_pack=passing,
        eligibility_record_id="elig-0001",
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="cor-0001",
        producer_id="offline-test-producer",
    )
    assert first["eligible"] is True
    assert first["deployment_authorized"] is False
    assert first["execution_authorized"] is False
    assert first["content_hash"] == second["content_hash"]
    unsafe = build_validation_evidence_pack_v0(
        _pack(record_id="pack-0002", incumbent_artifact_ref=None, gates=_gates(safety="FAIL"))
    )
    rejected = evaluate_promotion_eligibility_v0(
        policy=policy,
        candidate=candidate,
        evidence_pack=unsafe,
        eligibility_record_id="elig-0002",
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="cor-0001",
        producer_id="offline-test-producer",
        causal_parent_ids=["cand-0001", "pack-0002", "pol-0001"],
    )
    assert rejected["eligible"] is False
    assert "safety_regression_pass" in rejected["failed_gates"]
    _ = hypothesis


def test_p3_autonomous_promotion_and_activation_remain_forbidden() -> None:
    with pytest.raises(DdoValidationError, match="P3_AUTONOMOUS_PROMOTION_FORBIDDEN"):
        build_promotion_policy_v0(_policy(autonomous_promotion_classes=["P3"]))
    with pytest.raises(DdoValidationError, match="PROMOTION_AUTHORITY_ACTIVATION_FORBIDDEN"):
        build_promotion_policy_v0(_policy(promotion_authority_activation=True))
    with pytest.raises(DdoValidationError, match="DEPLOYMENT_ACTIVATION_FORBIDDEN"):
        build_deployment_record_v0(
            _envelope(
                schema_name="deployment_record",
                schema_version="deployment_record_v0",
                record_id="dep-0001",
                release_artifact_ref="rel-0001",
                previous_known_good_ref="rel-0000",
                environment=UNKNOWN,
                activation_authorized=True,
            )
        )


def test_health_snapshot_cannot_grant_execution() -> None:
    snapshot = build_health_snapshot_v0(_health())
    assert snapshot["execution_permit"] is False
    with pytest.raises(DdoValidationError, match="HEALTH_SNAPSHOT_MUST_NOT_GRANT_EXECUTION"):
        build_health_snapshot_v0(_health(execution_permit=True))


def test_supervisor_no_order_cycle_and_permission_cannot_submit() -> None:
    health = build_health_snapshot_v0(_health())
    supervisor = DeterministicAutonomySupervisorV0(fencing_token="fence-1")
    steps = [
        ("authorized_start", "INITIALIZING"),
        ("invariants_valid", "SYNCING"),
        ("fresh_state_proven", "READY"),
        ("cycle_due", "EVALUATING"),
        ("canonical_no_action", "WAITING"),
    ]
    for index, (event, expected) in enumerate(steps, start=1):
        result = supervisor.transition(
            event=event,
            health_snapshot=health,
            authority_snapshot={"execution_authority": False},
            record_id=f"cyc-{index:04d}",
            event_time_utc="2026-09-01T12:00:00Z",
            correlation_id="cor-0001",
            cycle_id="cycle-0001",
            producer_id="offline-test-producer",
        )
        assert result.rejected is False
        assert result.to_state == expected
        assert result.record["execution_reachable"] is False
    assert supervisor.state == "WAITING"
    planned = DeterministicAutonomySupervisorV0(fencing_token="fence-2")
    planned.reconstruct(
        (
            {
                "to_state": "PERMISSION_CHECK",
                "cycle_id": "cycle-0002",
            },
        )
    )
    denied = planned.transition(
        event="ephemeral_predicates_true",
        health_snapshot=health,
        authority_snapshot={"execution_authority": False},
        record_id="cyc-0099",
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="cor-0001",
        cycle_id="cycle-0002",
        producer_id="offline-test-producer",
    )
    assert denied.to_state == "WAITING"
    assert "no_wire" in denied.actions
    assert denied.record["to_state"] != "SUBMITTING"


def test_supervisor_crash_after_submit_does_not_resend() -> None:
    health = build_health_snapshot_v0(_health())
    supervisor = DeterministicAutonomySupervisorV0(fencing_token="fence-3")
    supervisor.reconstruct(({"to_state": "SUBMITTING", "cycle_id": "cycle-0003"},))
    result = supervisor.transition(
        event="transport_outcome_ambiguous",
        health_snapshot=health,
        authority_snapshot={"execution_authority": False},
        record_id="cyc-0100",
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="cor-0001",
        cycle_id="cycle-0003",
        producer_id="offline-test-producer",
    )
    assert result.to_state == "RECONCILING"
    assert "forbid_resend_mark_ambiguity" in result.actions
    duplicate = supervisor.transition(
        event="cycle_due",
        health_snapshot=health,
        authority_snapshot={"execution_authority": False},
        record_id="cyc-0101",
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="cor-0001",
        cycle_id="cycle-0003",
        producer_id="offline-test-producer",
    )
    assert duplicate.rejected is True
    assert "collapse_duplicate_cycle" in duplicate.actions


def test_release_and_deployment_lineage(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ledger.jsonl")
    ledger.append(_hypothesis())
    ledger.append(_candidate())
    ledger.append(_pack(incumbent_artifact_ref=None, causal_parent_ids=["cand-0001"]))
    previous = build_release_artifact_v0(
        _envelope(
            schema_name="release_artifact",
            schema_version="release_artifact_v0",
            record_id="rel-0000",
            candidate_artifact_ref="cand-0001",
            validation_evidence_pack_ref="pack-0001",
            checksum=UNKNOWN,
            causal_parent_ids=["cand-0001", "pack-0001"],
        )
    )
    current = build_release_artifact_v0(
        _envelope(
            schema_name="release_artifact",
            schema_version="release_artifact_v0",
            record_id="rel-0001",
            candidate_artifact_ref="cand-0001",
            validation_evidence_pack_ref="pack-0001",
            checksum=UNKNOWN,
            causal_parent_ids=["cand-0001", "pack-0001"],
        )
    )
    ledger.append(previous)
    ledger.append(current)
    deployment = build_deployment_record_v0(
        _envelope(
            schema_name="deployment_record",
            schema_version="deployment_record_v0",
            record_id="dep-0001",
            release_artifact_ref="rel-0001",
            previous_known_good_ref="rel-0000",
            environment=UNKNOWN,
            activation_authorized=False,
            causal_parent_ids=["rel-0001", "rel-0000"],
        )
    )
    result = ledger.append(deployment)
    assert result.status == "APPENDED"


def test_outcome_observation_separated_from_inference() -> None:
    split = evaluate_outcome_record_v0(
        {
            "schema_name": "outcome_record",
            "schema_version": "outcome_record_v0",
            "record_id": "out-0001",
            "decision_event_ref": "dec-0001",
            "evaluation_horizon": UNKNOWN,
            "actual_outcome_ref": UNKNOWN,
            "counterfactual_admissibility": "UNAVAILABLE",
            "event_time_utc": "2026-09-01T12:00:02Z",
            "correlation_id": "cor-0001",
            "cycle_id": None,
            "causal_parent_ids": [],
            "producer_id": "offline-test-producer",
            "authority_owner": UNKNOWN,
            "code_sha": UNKNOWN,
            "config_hash": UNKNOWN,
            "evidence_hash": UNKNOWN,
            "evidence_source_refs": ["src-evidence-1"],
            "safety_score": UNKNOWN,
        }
    )
    assert split["observation"]["actual_outcome_ref"] == UNKNOWN
    assert split["inference"]["safety_score"] == UNKNOWN
    assert split["unknown_collapsed"] is False


def test_control_plane_has_no_forbidden_imports() -> None:
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
