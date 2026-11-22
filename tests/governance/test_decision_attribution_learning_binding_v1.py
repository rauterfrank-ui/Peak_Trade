"""Phase-14 attribution must identify the original bundle consumed by learning."""

from dataclasses import fields, replace
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from src.governance import unified_blueprint_decision_attribution_evidence_v1 as attribution
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonical_json_dumps_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from tests.learning.test_dp_attribution_original_evidence_binding_v1 import native_request


def original_result(kind="original"):
    request, snapshot = native_request()
    request = request.attribution_request
    if kind != "original":
        if kind == "opposite_return":
            snapshot["o4_bars"][-1]["close"] = 90.0
        else:
            for bar in snapshot["o4_bars"]:
                bar["session_id"] = "other-original-attribution-session"
        observation = run_offline_n_bars_horizon_pipeline_v1(
            request.decision_event,
            snapshot,
            outcome_scalar_kind="LOG_RETURN",
            economic_score="OTHER_OPAQUE_LABEL",
        )["evaluation_observation"]
        request = replace(request, evaluation_observation=observation)
    result = attribution.build_decision_attribution_evidence_v1(request)
    assert result.disposition == attribution.DecisionAttributionDisposition.ATTRIBUTED
    return request, result


def result_json(result):
    return canonical_json_dumps_v0(
        {field.name: getattr(result, field.name) for field in fields(result)}
    )


def json_roundtrip(result):
    packet = json.loads(result_json(result))
    return replace(
        result,
        decision_attribution_evidence=packet["decision_attribution_evidence"],
        offline_evaluation_bundle=packet["offline_evaluation_bundle"],
        mi_attribution_query=packet["mi_attribution_query"],
    )


def ledger_with_originals(path, request, result, *, decision=None):
    ledger = AppendOnlyDdoLedgerV0(path)
    ledger.append(request.decision_event if decision is None else decision)
    for key in ("outcome_record", "attribution_record", "counterfactual_record"):
        ledger.append(result.offline_evaluation_bundle[key])
    return ledger


def ingest(ledger, result):
    return attribution.ingest_decision_attribution_to_learning_state_v1(
        ledger=ledger,
        attribution_result=result,
        session_id="attribution-original-binding",
        event_time_utc="2026-09-01T16:00:00Z",
        correlation_id="attribution-original-binding",
    )


def reseal(result, **updates):
    body = dict(result.decision_attribution_evidence)
    body.update(updates)
    body["evidence_digest"] = attribution.compute_decision_attribution_evidence_digest_v1(body)
    return replace(
        result,
        decision_attribution_evidence=MappingProxyType(body),
        evidence_digest=body["evidence_digest"],
    )


def assert_rejected_before_ingest(ledger, result, monkeypatch):
    before = ledger.ledger_path.read_bytes()
    packet = result_json(result)
    calls = []
    native = attribution.ingest_evaluation_bundle_into_learning_state_v1

    def consumer(*args, **kwargs):
        calls.append("learning_consumer")
        return native(*args, **kwargs)

    monkeypatch.setattr(attribution, "ingest_evaluation_bundle_into_learning_state_v1", consumer)
    with pytest.raises(attribution.UnifiedBlueprintDecisionAttributionError, match="ATTRIBUTION_"):
        ingest(ledger, result)
    assert calls == []
    assert ledger.ledger_path.read_bytes() == before
    assert result_json(result) == packet


@pytest.mark.parametrize("kind", ["opposite_return", "same_return_other_provenance"])
def test_foreign_valid_bundle_cannot_replace_attributed_original(tmp_path, monkeypatch, kind):
    _, original = original_result()
    request, other = original_result(kind)
    assert original.evidence_digest != other.evidence_digest
    assert (
        original.offline_evaluation_bundle["outcome_record"]["record_id"]
        == other.offline_evaluation_bundle["outcome_record"]["record_id"]
    )
    ledger = ledger_with_originals(tmp_path / "ledger.jsonl", request, other)
    replaced = replace(original, offline_evaluation_bundle=other.offline_evaluation_bundle)
    assert_rejected_before_ingest(ledger, replaced, monkeypatch)


@pytest.mark.parametrize(
    "change",
    [
        "missing_body",
        "body_without_reseal",
        "result_digest",
        "body_digest",
        "outcome_ref",
        "realized_ref",
        "horizon",
        "fingerprint",
        "evidence_id",
        "authority",
    ],
)
def test_inconsistent_attribution_stops_before_learning(tmp_path, monkeypatch, change):
    request, original = original_result()
    ledger = ledger_with_originals(tmp_path / "ledger.jsonl", request, original)
    if change == "missing_body":
        changed = replace(original, decision_attribution_evidence=None)
    elif change == "result_digest":
        changed = replace(original, evidence_digest="0" * 64)
    elif change in {"body_without_reseal", "body_digest"}:
        body = dict(original.decision_attribution_evidence)
        body["side_state_ref" if change == "body_without_reseal" else "evidence_digest"] = (
            "different"
        )
        changed = replace(original, decision_attribution_evidence=body)
    else:
        key, value = {
            "outcome_ref": ("outcome_record_ref", "other-outcome"),
            "realized_ref": ("realized_outcome_ref", "other-original-measurement"),
            "horizon": ("evaluation_horizon", "IMMEDIATE"),
            "fingerprint": ("evaluation_bundle_fingerprint", "0" * 64),
            "evidence_id": ("decision_attribution_evidence_id", "other-attribution"),
            "authority": ("attribution_authority", "TRADING"),
        }[change]
        changed = reseal(original, **{key: value})
    assert_rejected_before_ingest(ledger, changed, monkeypatch)


def test_original_decision_content_is_required_even_with_same_id(tmp_path, monkeypatch):
    request, result = original_result()
    raw = dict(request.decision_event)
    raw.pop("content_hash")
    raw["decision_time_information_set_ref"] = "different-original-information-set"
    other_decision = build_decision_event_v0(raw)
    assert other_decision["record_id"] == request.decision_event["record_id"]
    assert other_decision["content_hash"] != request.decision_event["content_hash"]
    ledger = ledger_with_originals(
        tmp_path / "ledger.jsonl", request, result, decision=other_decision
    )
    assert_rejected_before_ingest(ledger, result, monkeypatch)


@pytest.mark.parametrize("kind", ["original", "opposite_return", "same_return_other_provenance"])
@pytest.mark.parametrize("roundtrip", [False, True])
def test_matching_originals_reach_persisted_learning_and_idempotent_cold_read(
    tmp_path, kind, roundtrip
):
    request, result = original_result(kind)
    if roundtrip:
        result = json_roundtrip(result)
    assert attribution.replay_decision_attribution_evidence_v1(request, result)
    ledger = ledger_with_originals(tmp_path / "ledger.jsonl", request, result)
    packet = result_json(result)
    first = ingest(ledger, result)
    assert first["ok"] and not first["external_effect_authorized"]
    state = first["learning_state_record"]
    source = result.offline_evaluation_bundle["outcome_record"]
    assert state["decision_event_ref"] == request.decision_event["record_id"]
    assert state["last_actual_outcome_ref"] == source["actual_outcome_ref"]
    assert state["last_economic_score"] == source["economic_score"]
    assert state["outcome_scalar_kind"] == "LOG_RETURN"
    assert not state["can_mutate_core"] and not state["can_auto_promote"]
    saved = ledger.ledger_path.read_bytes()
    restored = AppendOnlyDdoLedgerV0(ledger.ledger_path)
    assert ingest(restored, result)["idempotent_replay"]
    assert ledger.ledger_path.read_bytes() == saved
    assert result_json(result) == packet


@pytest.mark.parametrize(
    "change", ["foreign_bundle", "record_content", "mi_query", "body", "body_digest", "reason"]
)
def test_replay_checks_original_result_content_instead_of_cached_digest(change):
    request, original = original_result()
    if change == "foreign_bundle":
        changed = replace(
            original,
            offline_evaluation_bundle=original_result("opposite_return")[
                1
            ].offline_evaluation_bundle,
        )
    elif change == "record_content":
        bundle = plain_v1(original.offline_evaluation_bundle)
        bundle["outcome_record"]["economic_score"] = "FOREIGN_LABEL_WITH_OLD_HASH"
        changed = replace(original, offline_evaluation_bundle=bundle)
    elif change == "mi_query":
        query = dict(original.mi_attribution_query)
        query["decision_event_ref"] = "different-decision"
        changed = replace(original, mi_attribution_query=query)
    elif change == "reason":
        changed = replace(original, reason_codes=("DIFFERENT_SEMANTIC_REASON",))
    else:
        body = dict(original.decision_attribution_evidence)
        body["side_state_ref" if change == "body" else "evidence_digest"] = "different"
        changed = replace(original, decision_attribution_evidence=body)
    assert not attribution.replay_decision_attribution_evidence_v1(request, changed)


@pytest.mark.parametrize("kind", ["insufficient", "rejected"])
def test_non_attributed_inputs_still_cannot_write_learning(tmp_path, kind):
    request, original = original_result()
    disposition = attribution.DecisionAttributionDisposition(kind.upper())
    result = replace(
        original,
        disposition=disposition,
        decision_attribution_evidence=None,
        offline_evaluation_bundle=None,
        evidence_digest=None,
    )
    ledger = ledger_with_originals(tmp_path / "ledger.jsonl", request, original)
    before = ledger.ledger_path.read_bytes()
    with pytest.raises(
        attribution.UnifiedBlueprintDecisionAttributionError, match="ATTRIBUTION_NOT_ATTRIBUTED"
    ):
        ingest(ledger, result)
    assert ledger.ledger_path.read_bytes() == before
