"""BWP-1 normative blueprint field parity and adversarial contract proofs."""

from __future__ import annotations

import copy
import json
import typing
from enum import Enum
from pathlib import Path

import pydantic
import pytest

from src.evaluation.golden_vectors.constraints.matrix_loader_v1 import (
    load_canonical_constraint_matrix_v1,
)
from src.evaluation.golden_vectors.contracts import (
    GvefSchemaError,
    SCHEMA_FAILURE,
    SCHEMA_FAILURE_REPROOF_CLASS,
    contract_canonical_bytes,
    contract_to_canonical_mapping,
    parse_boundary_result_v1,
    parse_constraint_matrix_v1,
    parse_domain_evaluation_context_v1,
    parse_evidence_bundle_v1,
    parse_run_manifest_v1,
)
from src.evaluation.golden_vectors.contracts.enums import FanOutEvaluationClass
from src.evaluation.golden_vectors.contracts import models as contract_models
from tests.evaluation.golden_vectors import test_gvef_contracts_schema_v1 as bwp1_fixtures

_MANIFEST_PATH = (
    Path("evidence/research/gvef_blueprint_v15_build_ready_v1/20261004T083919Z")
    / "contract_schema_manifest.json"
)

_MODEL_MAP: dict[str, type[pydantic.BaseModel]] = {
    "RunManifest": contract_models.RunManifestV1,
    "VectorManifest": contract_models.VectorManifestV1,
    "CorpusManifest": contract_models.CorpusManifestV1,
    "ConstraintMatrix": contract_models.ConstraintMatrixV1,
    "DomainEvaluationContext": contract_models.DomainEvaluationContextV1,
    "DomainEvaluationResult": contract_models.DomainEvaluationResultV1,
    "MetricResult": contract_models.MetricResultV1,
    "InvariantResult": contract_models.InvariantResultV1,
    "BoundaryResult": contract_models.BoundaryResultV1,
    "ProtectedDigestManifest": contract_models.ProtectedDigestManifestV1,
    "DecisionDeltaManifest": contract_models.DecisionDeltaManifestV1,
    "RankingUniverseManifest": contract_models.RankingUniverseManifestV1,
    "RankingDeltaManifest": contract_models.RankingDeltaManifestV1,
    "CapitalRiskCrsSizingEvidenceBundle": contract_models.CapitalRiskCrsSizingEvidenceBundleV1,
    "EvidenceBundle": contract_models.EvidenceBundleV1,
    "PromotionEvidenceEnvelope": contract_models.PromotionEvidenceEnvelopeV1,
}

_NESTED_BRIDGE: dict[tuple[str, str], str] = {
    ("DomainEvaluationContext", "protected_digest_baseline"): "ProtectedSemanticDigests",
    ("EvidenceBundle", "protected_semantic_digests"): "ProtectedSemanticDigests",
}

def _json_field_name(attr: str, finfo: pydantic.fields.FieldInfo) -> str:
    if finfo.alias:
        return finfo.alias
    if attr == "pass_":
        return "pass"
    return attr


def _is_nullable(annotation: typing.Any, *, required: bool) -> bool:
    if not required:
        return True
    if typing.get_origin(annotation) is typing.Union:
        return type(None) in typing.get_args(annotation)
    return False


def _unwrap_optional(annotation: typing.Any) -> typing.Any:
    args = typing.get_args(annotation)
    if args and type(None) in args:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _blueprint_type_compatible(
    *,
    contract: str,
    field: str,
    bp_type: str,
    annotation: typing.Any,
    enum_domain: str,
) -> str:
    if (contract, field) in _NESTED_BRIDGE:
        bridge = _NESTED_BRIDGE[(contract, field)]
        if bridge in enum_domain or enum_domain.startswith(bridge):
            return "EXACT_MATCH"
    core = _unwrap_optional(annotation)
    if bp_type == "number|string":
        if core in (int, str):
            return "EXACT_MATCH"
        union_args = typing.get_args(core)
        if union_args:
            args = [a for a in union_args if a is not type(None)]
            if set(args) == {int, str}:
                return "EXACT_MATCH"
    if bp_type == "string":
        if core is str or (isinstance(core, type) and issubclass(core, Enum)):
            return "EXACT_MATCH"
    if bp_type == "boolean" and core is bool:
        return "EXACT_MATCH"
    if bp_type == "array" and typing.get_origin(core) is list:
        return "EXACT_MATCH"
    if bp_type == "object":
        if isinstance(core, type) and issubclass(core, pydantic.BaseModel):
            return "EXACT_MATCH"
        if typing.get_origin(core) is dict:
            return "EXACT_MATCH"
    return "TYPE_MISMATCH"


def _load_blueprint_schemas() -> dict[str, list[dict[str, typing.Any]]]:
    payload = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    return payload["schemas"]


def _reconcile() -> list[dict[str, typing.Any]]:
    schemas = _load_blueprint_schemas()
    rows: list[dict[str, typing.Any]] = []
    for contract, fields in schemas.items():
        model = _MODEL_MAP[contract]
        current_by_json: dict[str, pydantic.fields.FieldInfo] = {}
        for attr, finfo in model.model_fields.items():
            current_by_json[_json_field_name(attr, finfo)] = finfo

        for bf in fields:
            name = bf["NAME"]
            finfo = current_by_json.get(name)
            if finfo is None:
                rows.append(
                    {
                        "CONTRACT": contract,
                        "FIELD": name,
                        "VERDICT": "MISSING",
                    }
                )
                continue
            required = finfo.is_required()
            nullable = _is_nullable(finfo.annotation, required=required)
            verdict = "EXACT_MATCH"
            if bf["REQUIRED"] != required:
                verdict = "REQUIRED_MISMATCH"
            elif bf["NULLABLE"] != nullable:
                verdict = "NULLABILITY_MISMATCH"
            else:
                type_verdict = _blueprint_type_compatible(
                    contract=contract,
                    field=name,
                    bp_type=bf["TYPE"],
                    annotation=finfo.annotation,
                    enum_domain=str(bf.get("ENUM_OR_DOMAIN", "")),
                )
                if type_verdict != "EXACT_MATCH":
                    verdict = type_verdict
            rows.append({"CONTRACT": contract, "FIELD": name, "VERDICT": verdict})

        for json_name in current_by_json:
            if json_name not in {f["NAME"] for f in fields}:
                rows.append(
                    {
                        "CONTRACT": contract,
                        "FIELD": json_name,
                        "VERDICT": "EXTRA",
                    }
                )
    return rows


def test_blueprint_manifest_field_parity_all_sixteen_contracts() -> None:
    rows = _reconcile()
    bad = [r for r in rows if r["VERDICT"] != "EXACT_MATCH"]
    assert not bad, bad


@pytest.mark.parametrize("name,parser,factory", bwp1_fixtures.CONTRACT_FIXTURES)
def test_contract_roundtrip_canonical_stable(name: str, parser, factory) -> None:
    model = parser(factory())
    payload_a = contract_to_canonical_mapping(model)
    roundtrip = parser(payload_a)
    payload_b = contract_to_canonical_mapping(roundtrip)
    assert contract_canonical_bytes(model) == contract_canonical_bytes(roundtrip)
    assert payload_a == payload_b


@pytest.mark.parametrize("name,parser,factory", bwp1_fixtures.CONTRACT_FIXTURES)
def test_each_required_field_rejection(name: str, parser, factory) -> None:
    base = factory()
    if not isinstance(base, dict):
        pytest.skip(f"{name} factory must return dict")
    schemas = _load_blueprint_schemas()
    required_fields = [f["NAME"] for f in schemas[name] if f["REQUIRED"]]
    for field in required_fields:
        payload = copy.deepcopy(base)
        if field not in payload:
            continue
        del payload[field]
        with pytest.raises(GvefSchemaError):
            parser(payload)


def test_schema_failure_fail_closed_and_reproof_class() -> None:
    assert SCHEMA_FAILURE == "SCHEMA_FAILURE"
    assert SCHEMA_FAILURE_REPROOF_CLASS == FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION.value
    try:
        parse_run_manifest_v1({"experiment_id": "x"})
    except GvefSchemaError as exc:
        assert exc.failure_classification == SCHEMA_FAILURE
    else:
        raise AssertionError("expected GvefSchemaError")


def test_invalid_run_id_uuid_rejected() -> None:
    payload = bwp1_fixtures._run_manifest()
    payload["run_id"] = "not-a-uuid"
    with pytest.raises(GvefSchemaError):
        parse_run_manifest_v1(payload)


def test_invalid_boundary_current_verdict_rejected() -> None:
    with pytest.raises(GvefSchemaError):
        parse_boundary_result_v1(
            {
                "edge_id": "e",
                "pass": True,
                "producer": "p",
                "consumer": "c",
                "current_verdict": "NOT_A_VERDICT",
            }
        )


def test_bwp0c_canonical_matrix_parses_via_bwp1_constraint_schema() -> None:
    matrix = load_canonical_constraint_matrix_v1()
    reparsed = parse_constraint_matrix_v1(
        json.loads(
            json.dumps(
                contract_to_canonical_mapping(matrix),
                sort_keys=True,
            )
        )
    )
    assert reparsed.matrix_digest == matrix.matrix_digest


def test_bwp0d_protected_semantic_digests_nested_in_domain_context() -> None:
    ctx = parse_domain_evaluation_context_v1(bwp1_fixtures._domain_context())
    assert ctx.protected_digest_baseline.ranking_universe.digest_hex != (
        ctx.protected_digest_baseline.selection.digest_hex
    )


def test_evidence_bundle_run_id_uuid_and_bwp0d_digest_shape() -> None:
    bundle = parse_evidence_bundle_v1(bwp1_fixtures._evidence_bundle())
    assert bundle.protected_semantic_digests.ranking_universe.schema_version == "1.0.0"
