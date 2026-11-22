"""Native MI projection and full-triad consumers must agree on their declared context."""

from dataclasses import replace
import json

import pytest

from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    run_mi_enriched_optimization_universe_experiment_plane_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoError
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
    validate_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_persist_v1 import (
    MiOfflineDurableEvidencePersistRequestV1,
    persist_mi_offline_durable_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_record_v1 import (
    build_mi_offline_durable_evidence_record_v1,
    derive_mi_offline_durable_evidence_id_v1,
    validate_mi_offline_durable_evidence_record_v1,
    validate_research_evidence_record_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
    RECORD_FILENAME,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    project_market_intelligence_research_evidence_v1,
)
from tests.experiments.test_canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    _intake_request,
)
from tests.learning.test_forecast_probability_semantic_admission_v1 import (
    native_forecast,
    original_result,
)
from tests.learning.test_mi_attribution_query_reference_binding_v1 import reseal_calibration

CONTEXT_FAULTS = ("domain", "n_bars", "numeric_count_alias", "bar_spec_ref", "forecast_kind")
RESEARCH_FAULTS = (
    "n_bars",
    "bar_spec_ref",
    "forecast_kind",
    "evaluability",
    "missing_evaluability",
)


def originals(variant="plain"):
    request, _ = original_result()
    forecast = native_forecast(
        request,
        support_disposition="INSUFFICIENT_EVIDENCE"
        if variant == "insufficient"
        else "SUFFICIENT_EVIDENCE",
    )
    observation = None if variant == "missing" else request.evaluation_observation
    calibration = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=observation,
        realized_direction="UP",
        support_disposition="INSUFFICIENT_EVIDENCE" if variant == "explicit_abstention" else None,
    )
    research = project_market_intelligence_research_evidence_v1(
        forecast_evidence=forecast,
        calibration_evidence=calibration,
        drift_assessment_refs=["drift.original.second", "drift.original.first"]
        if variant == "annotations"
        else None,
        legacy_learning_evidence_ref="lev.original.optional" if variant == "annotations" else None,
    )
    return dict(
        forecast_evidence=forecast, calibration_evidence=calibration, research_evidence=research
    )


def changed_context(calibration, fault):
    key = "n_bars" if fault == "numeric_count_alias" else fault
    value = {
        "domain": "OTHER_MI_UNIVERSE",
        "n_bars": calibration["n_bars"] + 1,
        "numeric_count_alias": float(calibration["n_bars"]),
        "bar_spec_ref": "bar.spec.other.original",
        "forecast_kind": "RETURN_DISTRIBUTION_SUMMARY",
    }[fault]
    return reseal_calibration(calibration, **{key: value})


def reseal_research(research, **changes):
    body = {
        k: v
        for k, v in plain_v1(research).items()
        if k not in {"research_evidence_id", "content_digest"}
    }
    body.update(changes)
    if body.get("evaluability") == "REMOVE_FIELD":
        body.pop("evaluability")
    digest = compute_content_hash_v0(body)
    result = {
        **body,
        "research_evidence_id": f"mi.research.{digest[:48]}",
        "content_digest": digest,
    }
    validate_research_evidence_record_v1(result)
    return result


def incompatible_inputs(family, fault):
    args = originals()
    if family == "calibration":
        args["calibration_evidence"] = changed_context(args["calibration_evidence"], fault)
        args["research_evidence"] = reseal_research(
            args["research_evidence"],
            calibration_evidence_id=args["calibration_evidence"]["calibration_evidence_id"],
        )
    else:
        values = {
            "n_bars": args["forecast_evidence"]["n_bars"] + 1,
            "bar_spec_ref": "bar.spec.other.original",
            "forecast_kind": "RETURN_DISTRIBUTION_SUMMARY",
            "evaluability": "NOT_EVALUABLE",
            "missing_evaluability": "REMOVE_FIELD",
        }
        key = "evaluability" if fault == "missing_evaluability" else fault
        args["research_evidence"] = reseal_research(
            args["research_evidence"], **{key: values[fault]}
        )
    validate_calibration_evidence_v1(args["calibration_evidence"])
    validate_research_evidence_record_v1(args["research_evidence"])
    return args


def declaration_with_native_identities(args):
    """Re-signed declaration using native identity owners, not a source-authenticity claim."""
    base = plain_v1(build_mi_offline_durable_evidence_record_v1(**originals()))
    base.update(plain_v1(args))
    base.update(
        calibration_evidence_id=args["calibration_evidence"]["calibration_evidence_id"],
        calibration_content_digest=args["calibration_evidence"]["content_digest"],
        research_evidence_id=args["research_evidence"]["research_evidence_id"],
        research_content_digest=args["research_evidence"]["content_digest"],
    )
    identity = {
        k: v
        for k, v in base.items()
        if k
        not in {
            "durable_evidence_id",
            "content_digest",
            "forecast_evidence",
            "calibration_evidence",
            "research_evidence",
            "provenance",
        }
    }
    digest = compute_content_hash_v0(identity)
    base.update(
        content_digest=digest,
        durable_evidence_id=derive_mi_offline_durable_evidence_id_v1(content_digest=digest),
    )
    return base


@pytest.mark.parametrize(
    "fault", ["schema", "authority", "class", "id", "digest", "missing", "score"]
)
def test_projection_revalidates_native_calibration_before_minting_research(fault):
    args = originals()
    calibration = plain_v1(args["calibration_evidence"])
    if fault == "missing":
        calibration.pop("n_bars")
    elif fault == "score":
        calibration["calibration_result"]["score"] = 0.99
    else:
        key = {
            "schema": "schema_version",
            "authority": "calibration_evidence_authority",
            "class": "evidence_class",
            "id": "calibration_evidence_id",
            "digest": "content_digest",
        }[fault]
        calibration[key] = "OTHER"
    before = bytes_v1(calibration)
    with pytest.raises((DdoError, ValueError), match="CALIBRATION_"):
        project_market_intelligence_research_evidence_v1(
            forecast_evidence=args["forecast_evidence"], calibration_evidence=calibration
        )
    assert bytes_v1(calibration) == before


@pytest.mark.parametrize("fault", CONTEXT_FAULTS)
def test_native_calibration_identity_cannot_hide_a_different_context(fault):
    args = incompatible_inputs("calibration", fault)
    before = bytes_v1(args)
    with pytest.raises((DdoError, ValueError), match="CALIBRATION_.*MISMATCH"):
        project_market_intelligence_research_evidence_v1(
            forecast_evidence=args["forecast_evidence"],
            calibration_evidence=args["calibration_evidence"],
        )
    assert bytes_v1(args) == before


@pytest.mark.parametrize("entry", ["build", "persist", "validate", "get", "list"])
@pytest.mark.parametrize(
    "family,fault",
    [
        ("calibration", "n_bars"),
        ("calibration", "numeric_count_alias"),
        ("research", "evaluability"),
        ("research", "missing_evaluability"),
    ],
)
def test_full_triad_consumers_reject_individually_valid_but_conflicting_members(
    tmp_path, entry, family, fault
):
    args = incompatible_inputs(family, fault)
    packet = declaration_with_native_identities(args)
    before = bytes_v1(packet)
    root = tmp_path / "synthetic-triad"
    if entry in {"get", "list"}:
        destination = root / packet["durable_evidence_id"] / RECORD_FILENAME
        destination.parent.mkdir(parents=True)
        destination.write_bytes(bytes_v1(packet))
    files_before = {
        str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }
    with pytest.raises((DdoError, ValueError), match="(CALIBRATION|RESEARCH)_.*MISMATCH"):
        if entry == "build":
            build_mi_offline_durable_evidence_record_v1(**args)
        elif entry == "persist":
            persist_mi_offline_durable_evidence_v1(
                root, MiOfflineDurableEvidencePersistRequestV1(**args)
            )
        elif entry == "validate":
            validate_mi_offline_durable_evidence_record_v1(packet)
        elif entry == "get":
            MiOfflineDurableEvidenceStoreV1(root).get(packet["durable_evidence_id"])
        else:
            MiOfflineDurableEvidenceStoreV1(root).list_records()
    assert bytes_v1(packet) == before
    assert {
        str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    } == files_before
    if entry not in {"get", "list"}:
        assert not root.exists()


@pytest.mark.parametrize("fault", RESEARCH_FAULTS)
def test_research_declarations_must_match_the_full_triad_originals(fault):
    args = incompatible_inputs("research", fault)
    with pytest.raises((DdoError, ValueError), match="RESEARCH_.*MISMATCH"):
        build_mi_offline_durable_evidence_record_v1(**args)


@pytest.mark.parametrize("fault", ["digest", "horizon", "domain"])
def test_projection_stops_bad_originals_before_actual_m4_call(tmp_path, fault):
    template = _intake_request(tmp_path / "legacy")
    args = originals()
    calibration = plain_v1(args["calibration_evidence"])
    if fault == "digest":
        calibration["calibration_result"]["score"] = 0.99
    else:
        calibration = changed_context(calibration, "n_bars" if fault == "horizon" else "domain")
    calls = []

    def actual_consumer(research):
        calls.append("m4")
        return run_mi_enriched_optimization_universe_experiment_plane_v1(
            replace(template, market_intelligence_research_evidence=research)
        )

    with pytest.raises((DdoError, ValueError), match="CALIBRATION_"):
        research = project_market_intelligence_research_evidence_v1(
            forecast_evidence=args["forecast_evidence"],
            calibration_evidence=calibration,
            legacy_learning_evidence_ref=template.legacy_learning_evidence["record_id"],
        )
        actual_consumer(research)
    assert not calls


VARIANTS = ("plain", "annotations", "missing", "insufficient", "explicit_abstention")


def valid_packet(root, variant):
    args = originals(variant)
    before = bytes_v1(args)
    packet = build_mi_offline_durable_evidence_record_v1(**args)
    assert bytes_v1(
        validate_mi_offline_durable_evidence_record_v1(json.loads(bytes_v1(packet)))
    ) == bytes_v1(packet)
    request = MiOfflineDurableEvidencePersistRequestV1(**args)
    first = persist_mi_offline_durable_evidence_v1(root, request)
    stored = MiOfflineDurableEvidenceStoreV1(root).get(first["durable_evidence_id"])
    files_before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.json")}
    replay = persist_mi_offline_durable_evidence_v1(root, request)
    assert replay == {**first, "persist_status": "IDEMPOTENT_REPLAY"}
    assert {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.json")} == files_before
    assert bytes_v1(args) == before
    return plain_v1(dict(inputs=args, packet=packet, first=first, stored=stored, replay=replay))


@pytest.mark.parametrize("variant", VARIANTS)
def test_original_full_triad_roundtrip_and_evidence_meaning_survive(tmp_path, variant):
    packet = valid_packet(tmp_path / "native-triad", variant)
    original = packet["inputs"]["calibration_evidence"]
    assert packet["stored"]["calibration_evidence"] == original
    assert packet["inputs"]["research_evidence"]["evaluability"] == original["evaluability"]
    assert packet["stored"]["productive_authority"] == "NONE"
    assert packet["stored"]["can_auto_promote"] is False
    if variant == "missing":
        assert original["actual_outcome_ref"] is None
        assert original["evaluability"] == "NOT_EVALUABLE"
    if variant in {"insufficient", "explicit_abstention"}:
        assert original["evaluability"] == "INSUFFICIENT_EVIDENCE"


def test_already_rejected_foreign_forecast_id_stays_rejected():
    args = originals()
    foreign = reseal_calibration(
        args["calibration_evidence"], forecast_evidence_id="mi.forecast.other.original"
    )
    with pytest.raises(ValueError, match="CALIBRATION_FORECAST_ID_MISMATCH"):
        project_market_intelligence_research_evidence_v1(
            forecast_evidence=args["forecast_evidence"], calibration_evidence=foreign
        )


def test_already_rejected_research_digest_stays_rejected():
    args = originals()
    args["research_evidence"] = {**args["research_evidence"], "content_digest": "wrong"}
    with pytest.raises(ValueError, match="RESEARCH_CONTENT_DIGEST_MISMATCH"):
        build_mi_offline_durable_evidence_record_v1(**args)
