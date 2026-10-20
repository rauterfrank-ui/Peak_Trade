"""Generic GHOSV kernel tests. Fixtures stay outside repository evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ops.generic_ghosv_kernel_v1.constants_v1 import (
    STATUS_MISSING_EVIDENCE,
    STATUS_UNKNOWN_FINDING_TYPE,
)
from scripts.ops.generic_ghosv_kernel_v1.observe_v1 import run_generic_ghosv_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    STATUS_ACCEPTED,
    STATUS_INPUT_SOURCE_STALE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_EMPTY,
)

CURRENT_COMMIT = "e1059ebea40399ca02ee1f303874f8e09b9d54b1"
CURRENT_TREE = "fb5bea3e2760a25b47efe05038821e1d1180e1bb"
OTHER_COMMIT = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_TREE = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
GRAPH_LEGACY_PIN = "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a"
KERNEL_DIR = Path(__file__).resolve().parents[2] / "scripts/ops/generic_ghosv_kernel_v1"
FORBIDDEN_IMPORTS = (
    "ghosv_bounded_context",
    "ghosv_master_v2_bounded_context",
    "double_play_ghosv",
    "socket",
    "urllib",
    "requests",
)
FORBIDDEN_PASS_KEYS = (
    "overall_pass",
    "coverage_pass",
    "guardian_pass",
    "universe_pass",
    "live_authorized",
)


def _provenance(**overrides: str) -> dict[str, dict[str, str]]:
    body = {
        "census": {"pin": CURRENT_COMMIT},
        "landscape": {"commit_pin": CURRENT_COMMIT, "tree_pin": CURRENT_TREE},
        "graph": {"pin": CURRENT_COMMIT},
    }
    if "graph_pin" in overrides:
        body["graph"]["pin"] = overrides["graph_pin"]
    return body


def _finding(
    finding_id: str, node: str, *, status: str = "OBSERVED", category: str = "PRESENCE"
) -> dict[str, str]:
    return {
        "finding_id": finding_id,
        "category": category,
        "observed_state": "recorded",
        "evidence_ref": "ev-1",
        "affected_scope": node,
        "status": status,
    }


def _run(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "authoritative_commit_sha": CURRENT_COMMIT,
        "authoritative_tree_sha": CURRENT_TREE,
        "declared_commit_sha": CURRENT_COMMIT,
        "declared_tree_sha": CURRENT_TREE,
        "provenance": _provenance(),
        "scope": {
            "allowed_nodes": ["node-a"],
            "exclusions": [],
            "unassigned": [],
        },
        "findings": [_finding("f-1", "node-a")],
        "evidence_refs": ["ev-1"],
    }
    payload.update(overrides)
    return run_generic_ghosv_v1(**payload)


def _assert_no_release(result: dict[str, Any]) -> None:
    assert result["status"] != "PASS"
    assert result["observation_proof"] is False
    assert result["coverage_proof"] is False
    assert result["implicit_release"] is False
    for key in FORBIDDEN_PASS_KEYS:
        assert key not in result


def test_valid_findings_stay_unproven() -> None:
    result = _run(
        scope={"allowed_nodes": ["node-a", "node-b"], "exclusions": [], "unassigned": []},
        findings=[_finding("f-b", "node-b", category="ABSENCE"), _finding("f-a", "node-a")],
    )
    assert result["status"] == STATUS_ACCEPTED
    assert result["findings_evaluated"] is True
    assert [item["finding_id"] for item in result["findings"]] == ["f-a", "f-b"]
    assert result["coverage_gap"] is False
    assert result["coverage_gaps"] == []
    assert result["pin_scope"]["status"] == STATUS_ACCEPTED
    assert result["provenance"]["declared_commit_sha"] == CURRENT_COMMIT
    assert result["provenance"]["declared_tree_sha"] == CURRENT_TREE
    assert all(item["counts_as_proof"] is False for item in result["findings"])
    _assert_no_release(result)


def test_wrong_commit_does_not_emit_findings() -> None:
    result = _run(declared_commit_sha=OTHER_COMMIT)
    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["findings"] == []
    assert result["findings_evaluated"] is False
    assert result["coverage_gap"] is True
    _assert_no_release(result)


def test_wrong_tree_does_not_emit_findings() -> None:
    result = _run(declared_tree_sha=OTHER_TREE)
    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["pin_scope"]["mismatches"] == ["tree"]
    assert result["findings_evaluated"] is False
    _assert_no_release(result)


def test_stale_graph_pin_does_not_emit_findings() -> None:
    result = _run(provenance=_provenance(graph_pin=GRAPH_LEGACY_PIN))
    assert result["status"] == STATUS_INPUT_SOURCE_STALE
    assert result["pin_scope"]["stale_sources"] == ["graph"]
    assert result["findings"] == []
    _assert_no_release(result)


def test_empty_scope_is_a_coverage_gap() -> None:
    result = _run(scope={"allowed_nodes": [], "exclusions": [], "unassigned": []})
    assert result["status"] == STATUS_SCOPE_EMPTY
    assert result["coverage_gap"] is True
    assert result["observation_proof"] is False
    assert result["findings_evaluated"] is False


def test_unknown_finding_is_not_observed_proof() -> None:
    result = _run(findings=[_finding("f-u", "node-a", status="UNKNOWN", category="ABSENCE")])

    assert result["status"] == STATUS_ACCEPTED
    assert result["findings"][0]["status"] == "UNKNOWN"
    assert result["findings"][0]["counts_as_proof"] is False
    assert result["observation_coverage_gap"] is True
    assert result["scope_coverage_gap"] is False
    assert result["graph_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["observation_proof"] is False
    assert result["coverage_proof"] is False
    assert result["status"] != "PASS"


def test_observed_findings_do_not_clear_unassigned_scope_gap() -> None:
    result = _run(
        scope={"allowed_nodes": ["node-a"], "exclusions": [], "unassigned": ["node-u"]},
        findings=[_finding("f-a", "node-a")],
    )

    assert result["status"] == STATUS_ACCEPTED
    assert result["findings"][0]["status"] == "OBSERVED"
    assert result["scope_coverage_gap"] is True
    assert result["observation_coverage_gap"] is False
    assert result["graph_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert {"kind": "UNASSIGNED_SCOPE", "affected_scope": "node-u"} in result["coverage_gaps"]
    assert result["observation_proof"] is False
    assert result["coverage_proof"] is False
    assert result["pin_scope"]["scope_coverage_gap"] is True


def test_exclusions_only_is_not_positive_observation_coverage() -> None:
    result = _run(
        scope={"allowed_nodes": [], "exclusions": ["node-x"], "unassigned": []},
        findings=[],
        evidence_refs=[],
    )

    assert result["status"] == STATUS_ACCEPTED
    assert result["findings"] == []
    assert result["scope_coverage_gap"] is True
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert {"kind": "EXCLUSION_NOT_COVERAGE", "affected_scope": "node-x"} in result["coverage_gaps"]
    assert result["observation_proof"] is False
    assert result["coverage_proof"] is False
    assert result["authority"] == "NONE"


def test_coverage_fields_are_deterministic() -> None:
    scope = {"allowed_nodes": ["node-a"], "exclusions": ["node-x"], "unassigned": ["node-u"]}
    findings = [
        _finding("f-b", "node-a", status="UNKNOWN"),
        _finding("f-a", "node-a"),
    ]
    first = _run(scope=scope, findings=findings)
    second = _run(scope=scope, findings=list(reversed(findings)))

    assert first == second
    assert first["coverage_gap"] is True
    assert first["scope_coverage_gap"] is True
    assert first["observation_coverage_gap"] is True


def test_unassigned_only_is_not_proof() -> None:
    result = _run(
        scope={"allowed_nodes": [], "exclusions": [], "unassigned": ["node-u"]},
        findings=[_finding("f-u", "node-u", status="UNASSIGNED")],
    )
    assert result["status"] == STATUS_ACCEPTED
    assert result["findings"][0]["status"] == "UNASSIGNED"
    assert result["findings"][0]["affected_scope"] == "node-u"
    assert result["coverage_gap"] is True
    assert result["coverage_gaps"][0]["kind"] == "UNASSIGNED"
    assert "unassigned_status:f-u:node-u" in result["uncertainties"]
    _assert_no_release(result)


def test_missing_evidence_fails_closed() -> None:
    result = _run(evidence_refs=[])
    assert result["status"] == STATUS_MISSING_EVIDENCE
    assert result["findings"] == []
    assert result["observation_proof"] is False
    assert result["findings_evaluated"] is False


def test_unknown_finding_type_fails_closed() -> None:
    result = _run(findings=[_finding("f-x", "node-a", category="GUARDIAN_RELEASE")])
    assert result["status"] == STATUS_UNKNOWN_FINDING_TYPE
    assert result["findings"] == []
    assert result["reasons"] == ["unknown_finding_type:f-x"]
    _assert_no_release(result)


def test_result_has_no_overall_pass() -> None:
    result = _run()
    _assert_no_release(result)
    assert result["status"] == STATUS_ACCEPTED


def test_result_has_no_authority_claims() -> None:
    result = _run()
    assert result["authority"] == "NONE"
    assert result["trading_authority"] == "NONE"
    assert result["safety_authority"] == "NONE"
    assert result["execution_authority"] == "NONE"
    assert result["runtime_authorization_effect"] == "NONE"
    assert result["guardian_identity"] is False
    assert result["graph_engine"] is False


def test_safety_escalation_stays_disabled() -> None:
    result = _run()
    assert result["safety_escalation_enabled"] is False
    assert result["network_access"] is False
    assert "safety_escalation" not in result


def test_output_is_deterministic() -> None:
    first = _run(
        findings=[_finding("f-b", "node-a", category="BOUNDARY"), _finding("f-a", "node-a")]
    )
    second = _run(
        findings=[_finding("f-a", "node-a"), _finding("f-b", "node-a", category="BOUNDARY")]
    )
    assert first == second
    assert [item["finding_id"] for item in first["findings"]] == ["f-a", "f-b"]


def test_kernel_has_no_productive_side_effects(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    before = sorted(path.name for path in tmp_path.iterdir())
    result = _run()
    after = sorted(path.name for path in tmp_path.iterdir())
    assert before == after
    assert result["repository_evidence_write"] is False
    source = "\n".join(path.read_text() for path in KERNEL_DIR.glob("*.py"))
    for banned in FORBIDDEN_IMPORTS:
        assert banned not in source
    assert "open(" not in source
