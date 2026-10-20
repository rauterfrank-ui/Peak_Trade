"""Independent tests for the Double Play GHOSV observation adapter."""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.double_play_ghosv_observation_adapter_v1.constants_v1 import (
    EXISTING_GHOSV_CODE_PIN,
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    FORBIDDEN_OUTPUT_KEYS,
)
from scripts.ops.double_play_ghosv_observation_adapter_v1.observe_v1 import (
    ObservationRequestV1,
    observe_double_play_catalog_v1,
)

PACKAGE = ROOT / "scripts/ops/double_play_ghosv_observation_adapter_v1"
GHOSV_PACKAGE = ROOT / "scripts/ops/ghosv_master_v2_bounded_context_v1"


def _observe(**kwargs: object):
    request = kwargs.pop("request", None)
    sha = str(kwargs.pop("current_sha", EXPECTED_BASELINE_SHA))
    tree = str(kwargs.pop("current_tree", EXPECTED_BASELINE_TREE))
    root = kwargs.pop("repository_root", ROOT)
    assert not kwargs
    return observe_double_play_catalog_v1(
        repository_root=root if isinstance(root, Path) else ROOT,
        current_sha=sha,
        current_tree=tree,
        request=request if isinstance(request, ObservationRequestV1) else None,
    )


def _finding(report: dict, requirement_id: str) -> dict:
    rows = [row for row in report["FINDINGS"] if row["REQUIREMENT_ID"] == requirement_id]
    assert len(rows) == 1
    return rows[0]


def _ghosv_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted(GHOSV_PACKAGE.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(GHOSV_PACKAGE).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_catalog_observation_keeps_effect_and_writer_blocked() -> None:
    before = _ghosv_digest()
    report = _observe()
    assert _ghosv_digest() == before
    assert report["PROJECTION_STATUS"] == "OBSERVED"
    assert report["REJECTION_REASONS"] == []
    assert report["AUTHORITY"] == "NONE"
    assert report["EXISTING_CHECKER_MUTATED"] is False
    assert report["EXISTING_GHOSV_CODE_PIN"] == EXISTING_GHOSV_CODE_PIN
    assert report["GHOSV_PIN_IS_CURRENT_BASELINE"] is False
    assert report["POLICY_BODY_EXECUTED"] is False
    assert report["PERSISTENCE_BINDER_WRITTEN"] is False
    assert [row["REQUIREMENT_ID"] for row in report["FINDINGS"]] == [
        "MV2-04",
        "MV2-05",
        "MV2-06",
        "MV2-08",
    ]
    role = _finding(report, "MV2-04")
    assert role["EXISTING_CHECKER_STATUS"] == "NOT_TESTED"
    assert role["OBSERVATION_STATUS"] == "INTERNAL_ROLE_FLAGS_OBSERVED"
    assert role["EVIDENCE_STATUS"] == "PARTIAL"
    assert role["REACTION"] is None
    assert role["PERSISTENCE_INFERRED_FROM_REPLACE"] is False
    assert role["DECISION_AUTHORITY_GRANTED"] is False
    lock = _finding(report, "MV2-05")
    assert lock["OBSERVATION_STATUS"] == "LOCK_TEXT_OBSERVED"
    assert lock["PYTHON_ENFORCEMENT"] == "NOT_CLAIMED"
    assert lock["TOOL_RUN_IS_OWNER_GO"] is False
    assert lock["GATE_CREATED"] is False
    effect = _finding(report, "MV2-06")
    assert effect["EVIDENCE_STATUS"] == "NOT_PROVEN"
    assert effect["BLOCKED"] is True
    assert effect["EFFECT_PASS"] is False
    assert effect["POLICY_BODY_EXECUTED"] is False
    assert effect["SYMBOL_MENTIONED_IN_CATALOG"] is True
    persistence = _finding(report, "MV2-08")
    assert persistence["EVIDENCE_STATUS"] == "NOT_PROVEN"
    assert persistence["BINDER_RUNTIME_ACTIVATED"] is False
    assert persistence["PRODUCTIVE_WRITER_REFUTED"] is False
    assert persistence["WRITER_REFUTATION"] == "BLOCKED"
    assert persistence["REACTION"] is None
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(report)


def test_repeated_output_is_identical() -> None:
    assert _observe() == _observe()


@pytest.mark.parametrize(
    ("observation_request", "reason"),
    [
        (ObservationRequestV1(separate_universe_claimed=True), "DYNAMIC_SCOPE_ROLE_VIOLATION"),
        (ObservationRequestV1(decision_authority_claimed=True), "DYNAMIC_SCOPE_ROLE_VIOLATION"),
        (ObservationRequestV1(replace_implies_persistence=True), "DYNAMIC_SCOPE_ROLE_VIOLATION"),
        (ObservationRequestV1(lock_mutation_requested=True), "OWNER_LOCK_VIOLATION"),
        (ObservationRequestV1(tool_run_claimed_as_owner_go=True), "OWNER_LOCK_VIOLATION"),
        (ObservationRequestV1(effect_pass_requested=True), "EFFECT_PASS_BLOCKED"),
        (ObservationRequestV1(persists_claimed=True), "PERSISTENCE_EVIDENCE_ABSENT"),
        (ObservationRequestV1(writer_refutation_requested=True), "WRITER_REFUTATION_BLOCKED"),
        (ObservationRequestV1(authority="LIVE"), "UNAUTHORIZED_AUTHORITY_CLAIM"),
    ],
)
def test_negative_claims_fail_closed(
    observation_request: ObservationRequestV1, reason: str
) -> None:
    report = _observe(request=observation_request)
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert reason in report["REJECTION_REASONS"]
    assert report["POLICY_BODY_EXECUTED"] is False
    assert report["PERSISTENCE_BINDER_WRITTEN"] is False
    assert _finding(report, "MV2-06")["EVIDENCE_STATUS"] == "NOT_PROVEN"
    assert _finding(report, "MV2-08")["PRODUCTIVE_WRITER_REFUTED"] is False
    assert report["EXISTING_GHOSV_CODE_PIN"] == EXISTING_GHOSV_CODE_PIN


def test_writer_flag_is_not_writer_evidence() -> None:
    report = _observe(request=ObservationRequestV1(persists_claimed=True))
    assert _finding(report, "MV2-08")["REACTION"] == "PERSISTENCE_EVIDENCE_ABSENT"
    assert _finding(report, "MV2-08")["PRODUCTIVE_WRITER_REFUTED"] is False


def test_missing_repository_evidence_rejects(tmp_path: Path) -> None:
    report = _observe(repository_root=tmp_path)
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert "MISSING_REQUIRED_EVIDENCE" in report["REJECTION_REASONS"]
    assert _finding(report, "MV2-04")["OBSERVATION_STATUS"] == "MISSING"
    assert _finding(report, "MV2-06")["EVIDENCE_STATUS"] == "NOT_PROVEN"


def test_baseline_mismatch_rejects() -> None:
    report = _observe(current_sha="0" * 40, current_tree="1" * 40)
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert "BASELINE_SHA_MISMATCH" in report["REJECTION_REASONS"]
    assert "BASELINE_TREE_MISMATCH" in report["REJECTION_REASONS"]
    assert report["GHOSV_PIN_IS_CURRENT_BASELINE"] is False


def test_adapter_does_not_import_existing_checker_or_trading() -> None:
    banned = {
        "trading",
        "execution",
        "risk",
        "scripts.ops.ghosv_master_v2_bounded_context_v1",
        "scripts.ops.ghosv_master_v2_bounded_context_v1.check_v1",
    }
    for path in PACKAGE.glob("*.py"):
        parsed = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                assert name not in banned
                assert not name.startswith("trading.")
    before = set(sys.modules)
    import scripts.ops.double_play_ghosv_observation_adapter_v1 as adapter

    loaded = set(sys.modules) - before
    assert banned.isdisjoint(loaded)
    assert adapter.observe_double_play_catalog_v1 is observe_double_play_catalog_v1
