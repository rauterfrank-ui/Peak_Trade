"""BWP-0C canonical constraint matrix + production pre/post gate tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.constraints.errors import GvefConstraintMatrixError
from src.evaluation.golden_vectors.constraints.matrix_loader_v1 import (
    BWP_ID,
    CANONICAL_MATRIX_REL,
    load_canonical_constraint_matrix_v1,
)
from src.evaluation.golden_vectors.constraints.post_constraint_gate_v1 import (
    ConstraintMatrixPostGateV1,
)
from src.evaluation.golden_vectors.constraints.pre_constraint_gate_v1 import (
    ConstraintMatrixPreGateV1,
)
from src.evaluation.golden_vectors.contracts.validation import parse_run_manifest_v1
from src.evaluation.golden_vectors.evaluators.productive_trading_path_v1 import (
    ProductiveTradingPathEvaluatorV1,
)
from src.evaluation.golden_vectors.integration.whole_system_v1 import whole_system_runner_v1
from src.evaluation.golden_vectors.runner.generic_runner_v1 import GvefRunRequestV1
from tests.evaluation.golden_vectors.constraint_matrix_fixtures_v1 import (
    canonical_constraint_matrix_dict,
    canonical_constraint_matrix_v1,
)
from tests.evaluation.golden_vectors.runner_fixtures_v1 import protected_digests, run_manifest
from tests.evaluation.golden_vectors.whole_system_fixtures_v1 import (
    whole_system_deps,
    whole_system_success_request,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_canonical_matrix_loads_and_digest_stable() -> None:
    matrix = canonical_constraint_matrix_v1()
    assert matrix.matrix_version == "1.5.0"
    assert len(matrix.rows) == 8
    assert matrix.baseline_sha == "9539b55ee4e572b3a0607e97008375bccb36814e"


def test_pre_gate_fail_closed_on_digest_mismatch() -> None:
    matrix = canonical_constraint_matrix_v1()
    run_payload = run_manifest()
    run_payload["constraint_matrix_digest"] = "f" * 64
    run_payload["constraint_matrix_version"] = matrix.matrix_version
    run = parse_run_manifest_v1(run_payload)
    ok, boundaries = ConstraintMatrixPreGateV1(repo_root=_REPO_ROOT).evaluate_pre(run)
    assert ok is False
    assert boundaries[0].edge_id == "CONSTRAINT_MATRIX_DIGEST"


def test_pre_gate_passes_with_canonical_binding() -> None:
    matrix = canonical_constraint_matrix_v1()
    run_payload = run_manifest()
    run_payload["constraint_matrix_digest"] = matrix.matrix_digest
    run_payload["constraint_matrix_version"] = matrix.matrix_version
    run = parse_run_manifest_v1(run_payload)
    ok, boundaries = ConstraintMatrixPreGateV1(repo_root=_REPO_ROOT).evaluate_pre(run)
    assert ok is True
    assert len(boundaries) == len(matrix.rows)


def test_post_gate_enforces_ranking_selection_separation() -> None:
    matrix = canonical_constraint_matrix_v1()
    run_payload = run_manifest()
    run_payload["constraint_matrix_digest"] = matrix.matrix_digest
    run_payload["constraint_matrix_version"] = matrix.matrix_version
    run = parse_run_manifest_v1(run_payload)
    from src.evaluation.golden_vectors.contracts.validation import (
        parse_protected_semantic_digests_v1,
    )

    bad = parse_protected_semantic_digests_v1(
        {
            "ranking_universe": {"digest_hex": "a" * 64, "schema_version": "1.0.0"},
            "selection": {"digest_hex": "a" * 64, "schema_version": "1.0.0"},
        }
    )
    ok, _ = ConstraintMatrixPostGateV1(repo_root=_REPO_ROOT).evaluate_post(
        run=run,
        post_gate_pass_required=True,
        protected_digests=bad,
    )
    assert ok is False


def test_whole_system_with_production_constraint_gates() -> None:
    matrix = canonical_constraint_matrix_v1()
    ctx = whole_system_success_request(unique_run=True)
    ctx_dict = ctx.evaluation_context.model_dump(mode="json", by_alias=True)
    ctx_dict["run_manifest"]["constraint_matrix_digest"] = matrix.matrix_digest
    ctx_dict["run_manifest"]["constraint_matrix_version"] = matrix.matrix_version
    ctx_dict["constraint_identity"] = canonical_constraint_matrix_dict()
    from src.evaluation.golden_vectors.contracts.validation import (
        parse_domain_evaluation_context_v1,
    )

    request = GvefRunRequestV1(parse_domain_evaluation_context_v1(ctx_dict))
    record = whole_system_runner_v1().execute(
        request,
        whole_system_deps(
            pre_gate=ConstraintMatrixPreGateV1(repo_root=_REPO_ROOT),
            post_gate=ConstraintMatrixPostGateV1(repo_root=_REPO_ROOT),
            evaluator=ProductiveTradingPathEvaluatorV1(),
            bind_corpus=True,
        ),
        verify_deterministic_replay=True,
    )
    from src.evaluation.golden_vectors.runner.states import RunnerState

    assert record.state is RunnerState.REGISTERED


def test_bwp0c_no_productive_side_effects_in_module() -> None:
    root = Path("src/evaluation/golden_vectors/constraints")
    forbidden = ("requests.post", "keychain", "subprocess", "live_", "testnet")
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        src = ast.dump(tree).lower()
        for token in forbidden:
            assert token not in src, f"{path.name} must not reference {token}"


def test_matrix_path_matches_blueprint() -> None:
    assert CANONICAL_MATRIX_REL.endswith(
        "authority_signal_flow_constraints/constraint_matrix_v1.json"
    )
    assert BWP_ID == "BWP-0C"


def test_loader_fail_closed_if_matrix_missing(tmp_path: Path) -> None:
    load_canonical_constraint_matrix_v1.cache_clear()
    with pytest.raises(GvefConstraintMatrixError):
        load_canonical_constraint_matrix_v1(repo_root=tmp_path)
    load_canonical_constraint_matrix_v1.cache_clear()
