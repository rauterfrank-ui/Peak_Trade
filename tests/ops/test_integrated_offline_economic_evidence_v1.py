"""Contract tests for integrated offline economic evidence v1 (Increment A)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.integrated_offline_economic_evidence_v1.binding_v1 import (
    VerificationBindingContextV1,
    resolve_configured_integrated_offline_economic_evidence_relpath_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    ECONOMIC_METRICS_DOMAIN_SCHEMA_ID,
    ECONOMIC_METRICS_VERIFIER_ID,
    INTEGRATED_ARTIFACT,
    INTEGRATED_SCHEMA_ID,
    INTEGRATED_SCHEMA_VERSION,
    INTEGRATED_VERIFIER_ID,
    MONTE_CARLO_DOMAIN_SCHEMA_ID,
    MONTE_CARLO_VERIFIER_ID,
    STRESS_DOMAIN_SCHEMA_ID,
    STRESS_VERIFIER_ID,
    WALK_FORWARD_DOMAIN_SCHEMA_ID,
    WALK_FORWARD_VERIFIER_ID,
)
from src.ops.integrated_offline_economic_evidence_v1.discovery_v1 import (
    discover_verified_integrated_offline_economic_evidence_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_verifiers_v1 import (
    verify_economic_metrics_domain_evidence_v1,
    verify_monte_carlo_domain_evidence_v1,
    verify_stress_domain_evidence_v1,
    verify_walk_forward_domain_evidence_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.forbidden_substitution_v1 import (
    check_forbidden_substitution_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.integrated_verifier_v1 import (
    verify_integrated_offline_economic_evidence_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_TEST_PRODUCER = "ops.integrated_offline_economic_evidence_v1.contract_test.synthetic_v1"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, doc: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _domain_ref(*, repo_root: Path, relpath: str, schema_id: str, verifier_id: str) -> dict:
    digest = _digest(relpath)
    artifact_path = repo_root / relpath
    payload: dict = {
        "schema_id": schema_id,
        "schema_version": "v1",
        "authority_effect": "NONE",
        "contract_test_increment_a_mechanics_only": True,
    }
    if schema_id == ECONOMIC_METRICS_DOMAIN_SCHEMA_ID:
        payload["fee_model_binding_digest_sha256"] = _digest("fee")
        payload["slippage_model_binding_digest_sha256"] = _digest("slip")
    if schema_id == WALK_FORWARD_DOMAIN_SCHEMA_ID:
        payload["fold_binding_digest_sha256"] = _digest("wf")
    if schema_id == MONTE_CARLO_DOMAIN_SCHEMA_ID:
        payload.update(
            {
                "monte_carlo_method": "simple",
                "randomness_seed": 42,
                "num_runs": 16,
                "input_series_binding_digest_sha256": _digest("series"),
                "result_summary_digest_sha256": _digest("mc_summary"),
            }
        )
    if schema_id == STRESS_DOMAIN_SCHEMA_ID:
        payload["stress_suite_binding_digest_sha256"] = _digest("stress")
    artifact_digest = _write_json(artifact_path, payload)
    return {
        "schema_id": schema_id,
        "schema_version": "v1",
        "authority_effect": "NONE",
        "artifact_relpath": relpath,
        "artifact_digest_sha256": artifact_digest,
        "producer_id": CONTRACT_TEST_PRODUCER,
        "verifier_id": verifier_id,
        "proven_source_sha": "0" * 40,
        "implementation_surface_digest_sha256": _digest("impl"),
        "config_digest_sha256": _digest("cfg"),
        "dataset_input_binding_digest_sha256": _digest("dataset"),
    }


def _build_synthetic_index(tmp_path: Path) -> Path:
    root = tmp_path / "evidence"
    base = "tests/fixtures/ops/integrated_offline_economic_evidence_contract_v1/synthetic_v1"
    metrics_rel = f"{base}/economic_metrics_domain_v1.json"
    wf_rel = f"{base}/walk_forward_domain_v1.json"
    mc_rel = f"{base}/monte_carlo_domain_v1.json"
    stress_rel = f"{base}/stress_domain_v1.json"
    for rel in (metrics_rel, wf_rel, mc_rel, stress_rel):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)

    index_dir = root / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema_id": INTEGRATED_SCHEMA_ID,
        "schema_version": INTEGRATED_SCHEMA_VERSION,
        "authority_effect": "NONE",
        "producer_id": CONTRACT_TEST_PRODUCER,
        "verifier_id": INTEGRATED_VERIFIER_ID,
        "evidence_root_relpath": str(index_dir.relative_to(tmp_path)),
        "economic_metrics_domain_ref": _domain_ref(
            repo_root=tmp_path,
            relpath=metrics_rel,
            schema_id=ECONOMIC_METRICS_DOMAIN_SCHEMA_ID,
            verifier_id=ECONOMIC_METRICS_VERIFIER_ID,
        ),
        "walk_forward_domain_ref": _domain_ref(
            repo_root=tmp_path,
            relpath=wf_rel,
            schema_id=WALK_FORWARD_DOMAIN_SCHEMA_ID,
            verifier_id=WALK_FORWARD_VERIFIER_ID,
        ),
        "monte_carlo_domain_ref": _domain_ref(
            repo_root=tmp_path,
            relpath=mc_rel,
            schema_id=MONTE_CARLO_DOMAIN_SCHEMA_ID,
            verifier_id=MONTE_CARLO_VERIFIER_ID,
        ),
        "stress_domain_ref": _domain_ref(
            repo_root=tmp_path,
            relpath=stress_rel,
            schema_id=STRESS_DOMAIN_SCHEMA_ID,
            verifier_id=STRESS_VERIFIER_ID,
        ),
    }
    _write_json(index_dir / INTEGRATED_ARTIFACT, doc)
    return index_dir


def _binding_context_from_index_doc(doc: dict) -> VerificationBindingContextV1:
    ref = doc["economic_metrics_domain_ref"]
    return VerificationBindingContextV1(
        expected_implementation_surface_digest_sha256=ref["implementation_surface_digest_sha256"],
        expected_config_digest_sha256=ref["config_digest_sha256"],
    )


def _binding_kwargs_from_index_doc(doc: dict) -> dict:
    ctx = _binding_context_from_index_doc(doc)
    return {"binding_context": ctx}


def test_config_default_unset_fail_closed() -> None:
    rel = resolve_configured_integrated_offline_economic_evidence_relpath_v1(repo_root=REPO_ROOT)
    assert rel == ""
    ok, note = discover_verified_integrated_offline_economic_evidence_v1(repo_root=REPO_ROOT)
    assert ok is False
    assert "unset" in note


def test_synthetic_domain_mechanics_pass(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    index_doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(index_doc)
    m = verify_economic_metrics_domain_evidence_v1(
        repo_root=tmp_path,
        reference=index_doc["economic_metrics_domain_ref"],
        **bind,
    )
    assert m.verified is True
    r1 = verify_integrated_offline_economic_evidence_v1(
        repo_root=tmp_path, evidence_root=index_dir, **bind
    )
    r2 = verify_integrated_offline_economic_evidence_v1(
        repo_root=tmp_path, evidence_root=index_dir, **bind
    )
    assert r1.blockers == r2.blockers
    assert r1.verified is True


@pytest.mark.parametrize(
    "mutator,expected_substr",
    [
        (
            lambda d: d["economic_metrics_domain_ref"].__delitem__("artifact_digest_sha256"),
            "DIGEST",
        ),
        (lambda d: d.update({"schema_id": "wrong"}), "SCHEMA_ID_MISMATCH"),
        (
            lambda d: d["monte_carlo_domain_ref"].update(
                {"artifact_relpath": "evidence/ops/current_6h_paper_shadow_soak_v1/x"}
            ),
            "FORBIDDEN",
        ),
        (
            lambda d: d.update({"walk_forward_monte_carlo_stress_requirements_met": True}),
            "FORBIDDEN_MANUAL",
        ),
        (lambda d: d.update({"B10_RANKING_ROBUSTNESS_ONLY": True}), "FORBIDDEN_EVIDENCE_CLASS"),
    ],
)
def test_integrated_negative_mutations(tmp_path: Path, mutator, expected_substr: str) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    mutator(doc)
    (index_dir / INTEGRATED_ARTIFACT).write_text(
        json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    result = verify_integrated_offline_economic_evidence_v1(
        repo_root=tmp_path,
        evidence_root=index_dir,
        **_binding_kwargs_from_index_doc(doc),
    )
    assert result.verified is False
    joined = " ".join(result.blockers)
    assert expected_substr.split("_")[0] in joined or expected_substr in joined


def test_mc_missing_seed_fail_closed(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(doc)
    mc_rel = doc["monte_carlo_domain_ref"]["artifact_relpath"]
    mc_doc = json.loads((tmp_path / mc_rel).read_text())
    mc_doc.pop("randomness_seed")
    _write_json(tmp_path / mc_rel, mc_doc)
    doc["monte_carlo_domain_ref"]["artifact_digest_sha256"] = hashlib.sha256(
        (tmp_path / mc_rel).read_bytes()
    ).hexdigest()
    _write_json(index_dir / INTEGRATED_ARTIFACT, doc)
    result = verify_monte_carlo_domain_evidence_v1(
        repo_root=tmp_path,
        reference=doc["monte_carlo_domain_ref"],
        **bind,
    )
    assert result.verified is False
    assert any("RANDOMNESS_SEED" in b for b in result.blockers)


def test_forbidden_substitution_classes() -> None:
    b10 = check_forbidden_substitution_v1(
        artifact_relpath="evidence/ops/peak_trade_b10/report.json",
        producer_id="peak_trade_robustness_and_stress_v1.producer",
    )
    assert b10
    step29m = check_forbidden_substitution_v1(
        artifact_relpath="evidence/x.json",
        producer_id="x",
        domain_doc={"status": "ECONOMICALLY_VIABLE_OFFLINE"},
    )
    assert any("STEP29M" in x for x in step29m)


def test_productive_discovery_disabled_outside_fixture_prefix(tmp_path: Path) -> None:
    ok, note = discover_verified_integrated_offline_economic_evidence_v1(repo_root=REPO_ROOT)
    assert ok is False
    assert note == "canonical_evidence_relpath_unset_fail_closed" or "disabled" in note


def test_missing_domain_reference_fail_closed(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(doc)
    doc.pop("stress_domain_ref")
    _write_json(index_dir / INTEGRATED_ARTIFACT, doc)
    result = verify_integrated_offline_economic_evidence_v1(
        repo_root=tmp_path, evidence_root=index_dir, **bind
    )
    assert result.verified is False
    assert any("STRESS_DOMAIN_REF_MISSING" in b for b in result.blockers)


def test_wrong_producer_fail_closed(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(doc)
    doc["economic_metrics_domain_ref"]["producer_id"] = "backtest.economic_viability_evidence_v1"
    _write_json(index_dir / INTEGRATED_ARTIFACT, doc)
    result = verify_economic_metrics_domain_evidence_v1(
        repo_root=tmp_path,
        reference=doc["economic_metrics_domain_ref"],
        **bind,
    )
    assert result.verified is False


def test_v11_bundle_only_substitution_fail_closed() -> None:
    blockers = check_forbidden_substitution_v1(
        artifact_relpath=(
            "evidence/ops/integrated_paper_shadow_economic_bundle_head_bound_v1/run/x.json"
        ),
        producer_id="ops.integrated_paper_shadow_economic_evidence_v1.contract_test.x",
    )
    assert blockers


def test_mc_missing_method_and_runs(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(doc)
    mc_rel = doc["monte_carlo_domain_ref"]["artifact_relpath"]
    mc_doc = json.loads((tmp_path / mc_rel).read_text())
    mc_doc.pop("monte_carlo_method")
    mc_doc.pop("num_runs")
    _write_json(tmp_path / mc_rel, mc_doc)
    doc["monte_carlo_domain_ref"]["artifact_digest_sha256"] = hashlib.sha256(
        (tmp_path / mc_rel).read_bytes()
    ).hexdigest()
    result = verify_monte_carlo_domain_evidence_v1(
        repo_root=tmp_path,
        reference=doc["monte_carlo_domain_ref"],
        **bind,
    )
    assert result.verified is False
    assert any("MONTE_CARLO_METHOD" in b for b in result.blockers)
    assert any("NUM_RUNS" in b for b in result.blockers)


def test_live_binding_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    index_doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    wrong_ctx = VerificationBindingContextV1(
        expected_implementation_surface_digest_sha256="f" * 64,
        expected_config_digest_sha256=index_doc["economic_metrics_domain_ref"][
            "config_digest_sha256"
        ],
    )
    result = verify_economic_metrics_domain_evidence_v1(
        repo_root=tmp_path,
        reference=index_doc["economic_metrics_domain_ref"],
        binding_context=wrong_ctx,
    )
    assert result.verified is False
    assert any("IMPLEMENTATION_SURFACE_DIGEST_MISMATCH" in b for b in result.blockers)


def test_in_repo_symlink_to_forbidden_soak_fail_closed(tmp_path: Path) -> None:
    forbidden = tmp_path / "evidence/ops/current_6h_paper_shadow_soak_v1/secret.json"
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text('{"forbidden": true}\n', encoding="utf-8")
    alias = (
        tmp_path / "tests/fixtures/ops/integrated_offline_economic_evidence_contract_v1/alias.json"
    )
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(forbidden)
    blockers = check_forbidden_substitution_v1(
        artifact_relpath=str(alias.relative_to(tmp_path)),
        producer_id=CONTRACT_TEST_PRODUCER,
        repo_root=tmp_path,
    )
    assert any("current_6h_paper_shadow_soak" in b or "FORBIDDEN" in b for b in blockers)


def test_productive_discovery_config_under_evidence_ops_fail_closed(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "config/ops"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "integrated_offline_economic_evidence_v1.toml").write_text(
        'canonical_evidence_relpath = "evidence/ops/future_productive_offline_economic_v1/run"\n',
        encoding="utf-8",
    )
    ok, note = discover_verified_integrated_offline_economic_evidence_v1(repo_root=tmp_path)
    assert ok is False
    assert note == "productive_discovery_disabled_until_increment_b"


@pytest.mark.parametrize("num_runs", [0, -1])
def test_mc_invalid_num_runs_fail_closed(tmp_path: Path, num_runs: int) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(doc)
    mc_rel = doc["monte_carlo_domain_ref"]["artifact_relpath"]
    mc_doc = json.loads((tmp_path / mc_rel).read_text())
    mc_doc["num_runs"] = num_runs
    _write_json(tmp_path / mc_rel, mc_doc)
    doc["monte_carlo_domain_ref"]["artifact_digest_sha256"] = hashlib.sha256(
        (tmp_path / mc_rel).read_bytes()
    ).hexdigest()
    result = verify_monte_carlo_domain_evidence_v1(
        repo_root=tmp_path,
        reference=doc["monte_carlo_domain_ref"],
        **bind,
    )
    assert result.verified is False
    assert any("NUM_RUNS" in b for b in result.blockers)


def test_mc_empty_method_fail_closed(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(doc)
    mc_rel = doc["monte_carlo_domain_ref"]["artifact_relpath"]
    mc_doc = json.loads((tmp_path / mc_rel).read_text())
    mc_doc["monte_carlo_method"] = ""
    _write_json(tmp_path / mc_rel, mc_doc)
    doc["monte_carlo_domain_ref"]["artifact_digest_sha256"] = hashlib.sha256(
        (tmp_path / mc_rel).read_bytes()
    ).hexdigest()
    result = verify_monte_carlo_domain_evidence_v1(
        repo_root=tmp_path,
        reference=doc["monte_carlo_domain_ref"],
        **bind,
    )
    assert result.verified is False
    assert any("MONTE_CARLO_METHOD" in b for b in result.blockers)


def test_mc_seed_zero_structurally_accepted(tmp_path: Path) -> None:
    index_dir = _build_synthetic_index(tmp_path)
    doc = json.loads((index_dir / INTEGRATED_ARTIFACT).read_text())
    bind = _binding_kwargs_from_index_doc(doc)
    mc_rel = doc["monte_carlo_domain_ref"]["artifact_relpath"]
    mc_doc = json.loads((tmp_path / mc_rel).read_text())
    mc_doc["randomness_seed"] = 0
    _write_json(tmp_path / mc_rel, mc_doc)
    doc["monte_carlo_domain_ref"]["artifact_digest_sha256"] = hashlib.sha256(
        (tmp_path / mc_rel).read_bytes()
    ).hexdigest()
    result = verify_monte_carlo_domain_evidence_v1(
        repo_root=tmp_path,
        reference=doc["monte_carlo_domain_ref"],
        **bind,
    )
    assert result.verified is True
