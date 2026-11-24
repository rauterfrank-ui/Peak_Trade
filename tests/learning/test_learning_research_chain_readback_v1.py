"""Bind actual owner executions across DDO, OPT, Meta and GVEF; reject aliases."""

import json
import shutil

import pytest

from src.experiments.canonical_experiment_identity_v1 import CanonicalCodeProvenanceV1
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, publish_v1, read_v1
from src.experiments.learning_research_chain_readback_v1 import read_learning_research_chain_v1
from src.experiments.offline_ddo_research_cycle_v1 import (
    OfflineDdoResearchProfileV1,
    run_offline_ddo_research_cycle_v1,
)
from tests.learning.test_offline_ddo_research_cycle_v1 import offline_cycle  # noqa: F401
from tests.learning.test_offline_ddo_learning_follow_up_v1 import _time


@pytest.fixture
def measured_chain(offline_cycle):
    root, _, _, plan_digest, bars, cfg, request = offline_cycle
    profile = OfflineDdoResearchProfileV1.model_validate(
        {
            **request.model_dump(exclude={"learning_evidence_digest"}),
            "schema_version": "offline_ddo_research_profile.v1",
            "follow_up_times": {
                "meta": _time(16, 8),
                "search": _time(16, 9),
                "measurement": _time(16, 10),
            },
        }
    )
    result = run_offline_ddo_research_cycle_v1(
        root,
        "first",
        plan_digest=plan_digest,
        request=profile,
        bars=bars,
        cfg=cfg,
        code=CanonicalCodeProvenanceV1("b" * 40, "CLEAN"),
    )
    assert result["status"] == "MECHANISM_PASS"
    digest = request.learning_evidence_digest
    original = root / "offline-ddo-research/first"
    run = root / "offline-ddo-research" / digest
    # Retain the original owner locators and bytes. This is a separate campaign
    # view, not a rewrite of scientific identities or original receipt paths.
    shutil.copytree(original, run)
    source = {"surface": "TEST_ONLY_SYNTHETIC", "cycle": "first"}
    publish_v1(
        root / "jobs" / (digest + ".json"),
        {
            "source": source,
            "code_sha": "b" * 40,
            "input_digest": "c" * 64,
            "history": [],
            "meta_digests": [],
        },
    )
    publish_v1(
        root / "completed" / (digest + ".json"),
        {
            "source": source,
            "authority": "NONE",
            "input_digest": "c" * 64,
            "learning_digest": digest,
            "result_digest": digest_v1(result),
            "instrument_id": request.instrument_id,
            "strategy_id": request.strategy_id,
            "strategy_version": request.strategy_version,
            "status": result["status"],
            "artifacts": [
                result["first_artifact_id"],
                result["next_artifact_id"],
                result["follow_up"]["artifact_id"],
            ],
        },
    )
    return root, run, digest


def _reseal(path, body):
    path.write_text(json.dumps({"body": body, "sha256": digest_v1(body)}))


def test_actual_owner_chain_has_bound_meta_and_no_economic_or_apply_claim(measured_chain):
    root, run, digest = measured_chain
    before = {p: p.read_bytes() for p in root.rglob("*.json")}
    chain = read_learning_research_chain_v1(root, digest)
    assert chain["meta_learning_universe"] == "SELF_LEARNING_UNIVERSE"
    assert len(chain["measurements"]) == 3
    assert len(chain["meta_bindings"]) == 2
    assert chain["evaluation"]["mechanism_status"] == "PASS"
    assert chain["evaluation"]["economic_status"] == "BLOCKED"
    assert chain["follow_up_status"] == "MEASURED"
    assert not chain["economic_acceptance_inferred"]
    assert not chain["productive_apply_authorized"]
    assert not chain["source_authentication_performed"]
    assert all(p.read_bytes() == body for p, body in before.items())


@pytest.mark.parametrize(
    "fault,edge",
    [
        ("source", "CAMPAIGN_SOURCE"),
        ("instrument", "INSTRUMENT_AND_STRATEGY"),
        ("code", "CAMPAIGN_SOURCE"),
        ("order", "MEASURED_ARTIFACT_ORDER"),
        ("request", "REQUEST_AND_RESULT"),
        ("economics", "GVEF_PLAN_AND_CLAIM_SCOPE"),
        ("follow_up", "GVEF_RECEIPT_TO_FOLLOW_UP"),
        ("meta", "MEASURED_RESULTS_TO_META"),
        ("missing_meta", "REQUIRED_HANDOFF_MISSING"),
        ("missing_follow_up", "REQUIRED_HANDOFF_MISSING"),
        ("missing_measurement", "FOLLOW_UP_TO_MEASUREMENT"),
    ],
)
def test_resealed_locally_valid_packets_cannot_cross_causal_edges(measured_chain, fault, edge):
    root, run, digest = measured_chain
    completed_path = root / "completed" / (digest + ".json")
    completed = read_v1(completed_path)
    result = read_v1(run / "result.json")
    if fault == "source":
        completed["source"] = {"surface": "TESTNET", "cycle": "foreign"}
    elif fault == "instrument":
        completed["instrument_id"] = "foreign-instrument"
    elif fault == "code":
        path = root / "jobs" / (digest + ".json")
        job = read_v1(path)
        job["code_sha"] = "d" * 40
        _reseal(path, job)
    elif fault == "order":
        completed["artifacts"].reverse()
    elif fault == "request":
        result["request_digest"] = "e" * 64
    elif fault == "economics":
        result["evaluation"]["economic_status"] = "PASS"
    elif fault == "follow_up":
        result["follow_up"]["decision"]["action"] = "HOLD"
        path = run / "follow-up-decisions" / (result["evaluation"]["receipt_id"] + ".json")
        _reseal(path, result["follow_up"]["decision"])
    elif fault == "missing_meta":
        result["meta_feedback"] = None
    elif fault == "missing_follow_up":
        result["follow_up"] = None
    elif fault == "missing_measurement":
        result["follow_up"]["status"] = "SEARCH_EXHAUSTED"
    else:
        result["meta_feedback"]["meta_input_binding"]["meta_learning_record"][
            "autonomous_promotion"
        ] = True
    _reseal(run / "result.json", result)
    completed["result_digest"] = digest_v1(result)
    _reseal(completed_path, completed)
    # Every changed outer record has a fresh valid content hash. Rejection is
    # about the original producer/consumer relationship, not a stale checksum.
    assert read_v1(completed_path) == completed
    with pytest.raises(ValueError, match=edge):
        read_learning_research_chain_v1(root, digest)


@pytest.mark.parametrize("observed,rejected", [(0.0, False), (-0.02, True)])
def test_late_shadow_gap_enters_next_meta_once(measured_chain, observed, rejected):
    from datetime import datetime, timedelta, timezone

    from src.experiments.campaign_reality_gap_return_v1 import (
        known_returns_v1,
        publish_gap_return_v1,
        with_returns_v1,
    )
    from src.experiments.canonical_native_research_session_v1 import (
        NativeResearchExecutionArchiveV1,
    )
    from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
    from src.experiments.canonical_research_result_to_meta_input_v1 import (
        build_meta_learning_from_research_results_v1,
    )

    root, run, digest = measured_chain
    artifact = read_v1(run / "result.json")["next_artifact_id"]
    execution, measurement = NativeResearchExecutionArchiveV1(run / "native-archive")._read_packet(
        artifact
    )
    unit = execution.next_meta_input
    profile = {
        "packet": artifact,
        "experiment_id": measurement["experiment_id"],
        "parameters": dict(measurement["parameters"]),
    }
    plan = {"learning_digest": digest, "profiles": {"candidate": profile}}
    dimensions = {
        "profiles": {
            "candidate": {
                "packet": artifact,
                "gap_dimensions": [
                    dict(name="pnl", unit="ratio", expected=0.0, observed=observed, threshold=0.001)
                ],
            }
        },
        "observed_plan_digest": digest_v1(plan),
        "observed_surface": "SHADOW",
        "source_data_known_at_utc": "2026-01-01T00:00:00+00:00",
        "metric_definitions": "NET_RETURN_ON_BEGINNING_EQUITY_V1",
        "threshold_policy_digest": "a" * 64,
    }
    before = datetime.now(timezone.utc) - timedelta(seconds=1)
    key = publish_gap_return_v1(root, plan, dimensions)
    assert publish_gap_return_v1(root, plan, dimensions) == key
    assert not known_returns_v1(root, [digest], before)
    now = datetime.now(timezone.utc)
    keys = known_returns_v1(root, [digest], now)
    assert keys == [key] and not known_returns_v1(root, [], now)
    updated = with_returns_v1(unit, root, keys)
    assert len(updated.late_gaps) == 1 and len(updated.late_failures) == int(rejected)
    result = build_meta_learning_from_research_results_v1(
        [updated],
        created_at=now.isoformat().replace("+00:00", "Z"),
        policy=canonical_meta_learning_policy_v1(),
    )
    lineage = result["meta_learning_record"]["input_lineage"]
    assert updated.late_gaps[0]["reality_gap_record_id"] in lineage["reality_gap_record_ids"]
    if rejected:
        assert updated.late_failures[0]["failure_record_id"] in lineage["failure_record_ids"]
