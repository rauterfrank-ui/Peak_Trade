"""Bounded tests for the isolated Master V2 GHOSV. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.ghosv_master_v2_bounded_context_v1.check_v1 import (
    assess_reproof_v1,
    run_ghosv_master_v2_bounded_context_v1,
)
from scripts.ops.ghosv_master_v2_bounded_context_v1.constants_v1 import (
    CONTRACT_DOCUMENT_PROVENANCE,
    CURRENT_CODE_PIN,
    CURRENT_TREE_PIN,
    NOT_TESTED_REQUIREMENTS,
    PILOT_BASELINE_EDGE_DIGEST,
)
from scripts.ops.ghosv_master_v2_bounded_context_v1.findings_v1 import canonical_sha256

PACKAGE = ROOT / "scripts/ops/ghosv_master_v2_bounded_context_v1"
CONTRACT_TEXT = "MASTER_V2_GHOSV_CONTRACT_V1 synthetic reference text"


def _contract(**overrides: object) -> dict:
    text = str(overrides.pop("contract_text", CONTRACT_TEXT))
    payload = {
        "contract_id": "MASTER_V2_GHOSV_CONTRACT_V1",
        "contract_text": text,
        "contract_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "document_provenance": CONTRACT_DOCUMENT_PROVENANCE,
        "current_code_pin": CURRENT_CODE_PIN,
    }
    payload.update(overrides)
    return payload


def _edge(**overrides: object) -> dict:
    payload = {
        "edge_type": "CALLS",
        "file": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_master_v2_runtime_cycle_v1.py"
        ),
        "symbol": "run_current_productive_master_v2_runtime_cycle_v1",
        "target_file": "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "target_symbol": "run_integrated_offline_trading_logic_replay_v1",
        "call_lines": [1056],
        "current_sha": CURRENT_CODE_PIN,
        "current_tree": CURRENT_TREE_PIN,
        "membership": "UNKNOWN_MEMBERSHIP",
    }
    payload.update(overrides)
    return payload


def _report(edges: list[dict] | None = None, **overrides: object) -> dict:
    baseline = edges if edges is not None else [_edge()]
    projection_edges = [_edge()]
    projection_nodes = [
        {"source_native_id": "cycle"},
        {"source_native_id": "replay"},
    ]
    projection = {
        "edges": projection_edges,
        "nodes": projection_nodes,
        "edge_count": len(projection_edges),
        "node_count": len(projection_nodes),
        "max_depth_enforced": 1,
        "trading_authority_implied": False,
        "graph_neighborhood_is_runtime_reachability": False,
        "projection_digest_sha256": canonical_sha256(
            {"edges": projection_edges, "nodes": projection_nodes}
        ),
    }
    payload = {
        "current_sha": CURRENT_CODE_PIN,
        "current_tree": CURRENT_TREE_PIN,
        "edges": baseline,
        "baseline_edge_count": len(baseline),
        "baseline_edge_digest_sha256": canonical_sha256(baseline),
        "ghv_projection": projection,
        "unresolved_dynamic_bindings": [],
    }
    payload.update(overrides)
    return payload


def _rules(**overrides: object) -> dict:
    payload = {
        "owner_lock": "LEVEL_3",
        "authority": "NONE",
        "trading_authority": "NONE",
        "safety_authority": "NONE",
        "execution_authority": "NONE",
        "lock_mutation_requested": False,
        "write_requested": False,
        "post_requested": False,
        "productive_import_requested": False,
    }
    payload.update(overrides)
    return payload


def _run(**overrides: object) -> dict:
    payload = {
        "current_sha": CURRENT_CODE_PIN,
        "current_tree": CURRENT_TREE_PIN,
        "adapter_report": _report(),
        "contract_reference": _contract(),
        "owner_rules": _rules(),
        "runtime_evidence": None,
        "foreign_findings": [],
    }
    payload.update(overrides)
    return run_ghosv_master_v2_bounded_context_v1(**payload)


def _finding(report: dict, requirement_id: str) -> dict:
    matches = [item for item in report["findings"] if item["requirement_id"] == requirement_id]
    assert len(matches) == 1
    return matches[0]


_IMPORT_OBSERVER = r"""
import builtins
import importlib
import json
import sys
import types

mode = sys.argv[1]
root = sys.argv[2]
if root not in sys.path:
    sys.path.insert(0, root)
seen = []
real_import = builtins.__import__


def _recording_import(name, globals=None, locals=None, fromlist=(), level=0):
    seen.append(name)
    return real_import(name, globals, locals, fromlist, level)


builtins.__import__ = _recording_import
real_import_module = importlib.import_module


def _recording_import_module(name, package=None):
    seen.append(name)
    return real_import_module(name, package)


importlib.import_module = _recording_import_module


def _stub(name):
    sys.modules[name] = types.ModuleType(name)


def _forbidden(names):
    found = []
    for name in names:
        if name.split(".", 1)[0] in {"trading", "execution", "risk"}:
            found.append(name)
        elif "ghv_master_v2_current_tree_adapter" in name:
            found.append(name)
        elif (
            name == "scripts.ops.ghosv_bounded_context_v1"
            or name.startswith("scripts.ops.ghosv_bounded_context_v1.")
        ):
            found.append(name)
    return found


if mode == "adapter_first":
    import scripts.ops.ghv_master_v2_current_tree_adapter_v1

    seen.clear()
elif mode in {"preloaded", "negative"}:
    for module_name in (
        "trading",
        "execution",
        "risk",
        "scripts.ops.ghosv_bounded_context_v1",
        "scripts.ops.ghv_master_v2_current_tree_adapter_v1",
    ):
        _stub(module_name)

if mode == "negative":
    import trading
    importlib.import_module("execution")
    importlib.import_module("risk")
    importlib.import_module("scripts.ops.ghosv_bounded_context_v1")
    importlib.import_module("scripts.ops.ghv_master_v2_current_tree_adapter_v1")
else:
    import scripts.ops.ghosv_master_v2_bounded_context_v1
    if mode == "ghosv_then_adapter":
        ghosv_names = list(seen)
        seen.clear()
        import scripts.ops.ghv_master_v2_current_tree_adapter_v1
        print(json.dumps({"ghosv": _forbidden(ghosv_names), "adapter_seen": "ghv_master_v2_current_tree_adapter_v1" in "".join(seen)}))
        raise SystemExit(0)

print(json.dumps({"forbidden": _forbidden(seen)}))
"""


def _observe_imports(mode: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "-c", _IMPORT_OBSERVER, mode, str(ROOT)],
        cwd=ROOT,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_package_imports_without_productive_or_adapter_modules() -> None:
    alone = _observe_imports("ghosv_alone")
    adapter_first = _observe_imports("adapter_first")
    ordered = _observe_imports("ghosv_then_adapter")
    preloaded = _observe_imports("preloaded")
    negative = _observe_imports("negative")
    assert alone["forbidden"] == []
    assert adapter_first["forbidden"] == []
    assert ordered["ghosv"] == []
    assert ordered["adapter_seen"] is True
    assert preloaded["forbidden"] == []
    assert negative["forbidden"] == [
        "trading",
        "execution",
        "risk",
        "scripts.ops.ghosv_bounded_context_v1",
        "scripts.ops.ghv_master_v2_current_tree_adapter_v1",
    ]


def test_bounded_checks_are_deterministic_and_do_not_aggregate() -> None:
    first = _run()
    second = _run()
    assert first == second
    assert assess_reproof_v1(first, second)["reaction"] == "REPROOF_MATCH"
    assert first["reaction"] is None
    assert first["authority"] == "NONE"
    assert first["execution_authority"] == "NONE"
    assert first["active"] == "NOT_PROVEN"
    assert first["full_universe_boundary_ratified"] is False
    assert first["execution_ghosv"] == "NOT_APPLICABLE"
    assert first["current_causal_graph"] == "NOT_MATERIALIZED"
    for forbidden in ("overall_pass", "guardian_pass", "universe_pass", "live_authorized"):
        assert forbidden not in first
    owner = _finding(first, "MV2-01")
    graph = _finding(first, "MV2-09")
    aggregate = _finding(first, "MV2-10")
    assert owner["finding_type"] == "DECLARED_DECISION_OWNER_WIRED"
    assert owner["evidence_status"] == "PARTIAL"
    assert owner["authority_effect"] == "NONE"
    assert "PILOT_DIGEST_NOT_BOUND" in owner["uncertainty"]
    assert "ACTIVE_NOT_PROVEN" in owner["uncertainty"]
    assert graph["finding_type"] == "GRAPH_NEIGHBORHOOD_NOT_RUNTIME"
    assert graph["evidence_status"] == "PARTIAL"
    assert aggregate["finding_type"] == "NO_OVERALL_PASS"
    assert aggregate["evidence_status"] == "PROVEN"
    assert {
        item["requirement_id"]
        for item in first["findings"]
        if item["evidence_status"] == "NOT_TESTED"
    } == set(NOT_TESTED_REQUIREMENTS)
    assert first["findings"] == sorted(first["findings"], key=lambda item: item["finding_id"])
    assert all(item["domain"] == "MASTER_V2" for item in first["findings"])


def test_reproof_detects_nondeterminism_without_overwriting_previous() -> None:
    previous = _run()
    snapshot = previous["findings"][0]["finding_id"]
    mutated = dict(previous)
    mutated["findings"] = previous["findings"][1:]
    assessed = assess_reproof_v1(previous, mutated)
    assert assessed["reaction"] == "TOOL_NONDETERMINISM"
    assert previous["findings"][0]["finding_id"] == snapshot
    other_tree = _run(current_tree="b" * 40)
    assert other_tree["reaction"] == "TREE_MISMATCH"
    assert assess_reproof_v1(previous, other_tree)["reaction"] == "REPROOF_DELTA"


@pytest.mark.parametrize(
    ("kwargs", "reaction"),
    [
        ({"current_sha": "a" * 40}, "SHA_MISMATCH"),
        ({"current_tree": "b" * 40}, "TREE_MISMATCH"),
        ({"current_sha": None}, "PROVENANCE_ABSENT"),
        (
            {"contract_reference": _contract(contract_text_sha256="0" * 64)},
            "CONTRACT_TEXT_NOT_VERIFIED",
        ),
        ({"adapter_report": _report(ghv_projection=None)}, "REQUIRED_TOOL_ABSENT"),
        (
            {"adapter_report": _report(submitted_claims=[{"type": "MEMBERSHIP", "symbol": "x"}])},
            "UNKNOWN_MEMBERSHIP",
        ),
        ({"owner_rules": _rules(trading_authority="GRANTED")}, "AUTHORITY_CLAIM_REJECTED"),
        ({"owner_rules": _rules(lock_mutation_requested=True)}, "OWNER_LOCK_VIOLATION"),
        (
            {"adapter_report": _report(submitted_claims=[{"type": "ACTIVE"}])},
            "ACTIVE_WITHOUT_CAPTURE",
        ),
        (
            {
                "adapter_report": _report(
                    submitted_claims=[{"type": "GRAPH_NEIGHBORHOOD_IS", "value": "ACTIVE"}]
                )
            },
            "RUNTIME_STAGE_COLLAPSE",
        ),
        (
            {"adapter_report": _report(submitted_claims=[{"type": "PERSISTS"}])},
            "PERSISTENCE_EVIDENCE_ABSENT",
        ),
        (
            {
                "adapter_report": _report(
                    unresolved_dynamic_bindings=[{"status": "UNRESOLVED_DYNAMIC_BINDING"}],
                    submitted_claims=[{"type": "RESOLVED_DYNAMIC_EDGE"}],
                )
            },
            "UNRESOLVED_DYNAMIC_BINDING",
        ),
        ({"adapter_report": _report(requested_depth=32)}, "DEPTH_NOT_AUTHORIZED"),
        ({"owner_rules": _rules(write_requested=True)}, "WRITE_REJECTED"),
        ({"owner_rules": _rules(post_requested=True)}, "POST_REJECTED"),
        ({"owner_rules": _rules(productive_import_requested=True)}, "PRODUCTIVE_IMPORT_REJECTED"),
        ({"adapter_report": _report(overall_pass=True)}, "OVERALL_PASS_FORBIDDEN"),
        (
            {"adapter_report": _report(edges=[_edge(target_symbol="other_symbol")])},
            "DECISION_OWNER_MISMATCH",
        ),
    ],
)
def test_negative_reactions_emit_no_proven_findings(kwargs: dict, reaction: str) -> None:
    result = _run(**kwargs)
    assert result["reaction"] == reaction
    assert all(item["evidence_status"] != "PROVEN" for item in result["findings"])
    assert result["runtime_authorization_effect"] == "NONE"
    assert {item["requirement_id"] for item in result["findings"]}.isdisjoint(
        set(NOT_TESTED_REQUIREMENTS)
    )


def test_foreign_contradiction_remains_open_and_keeps_local_status() -> None:
    foreign = {
        "conflicts_with": "MV2-01",
        "text": "other owner",
        "topic": "owner",
    }
    supplied = [dict(foreign)]
    result = _run(foreign_findings=supplied)
    assert supplied == [foreign]
    assert result["reaction"] == "CONFLICT_OPEN"
    owner = _finding(result, "MV2-01")
    assert owner["evidence_status"] == "PARTIAL"
    assert owner["conflict_status"] == "CONFLICT_OPEN"
    assert owner["foreign_finding_reference"] == canonical_sha256(foreign)
    assert "other owner" not in owner["uncertainty"]


def test_pilot_digest_is_not_accepted_for_a_different_edge_list() -> None:
    report = _report()
    report["baseline_edge_digest_sha256"] = PILOT_BASELINE_EDGE_DIGEST
    report["baseline_edge_count"] = 130
    result = _run(adapter_report=report)
    assert result["reaction"] == "PROVENANCE_ABSENT"
    assert result["reaction_detail"] == "BASELINE_DIGEST_MISMATCH"
    assert all(item["evidence_status"] != "PROVEN" for item in result["findings"])


def test_equated_document_and_code_pins_are_rejected() -> None:
    result = _run(
        contract_reference=_contract(
            document_provenance=CURRENT_CODE_PIN,
            current_code_pin=CURRENT_CODE_PIN,
        )
    )
    assert result["reaction"] == "PROVENANCE_ABSENT"
    assert result["reaction_detail"] == "CONTRACT_PROVENANCE_MISMATCH"


def test_write_and_post_requests_do_not_touch_files_or_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("side effect")

    monkeypatch.setattr(Path, "write_text", boom)
    monkeypatch.setattr(Path, "write_bytes", boom)
    marker = tmp_path / "must-not-exist"
    assert _run(owner_rules=_rules(write_requested=True))["reaction"] == "WRITE_REJECTED"
    assert _run(owner_rules=_rules(post_requested=True))["reaction"] == "POST_REJECTED"
    assert not marker.exists()


def test_source_has_no_productive_imports_or_graph_engine() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    for banned in (
        "ghv_master_v2_current_tree_adapter",
        "ghosv_bounded_context_v1",
        "from trading",
        "import trading",
        "import execution",
        "import risk",
        "census_flow_to_typed_edge",
        "urllib",
        "socket",
    ):
        assert banned not in text
