"""Bounded fixtures for the isolated Master V2 boundary projection."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.ops.master_v2_boundary_projection_v1.project_v1 import (
    STALE_GRAPH_GIT_HEAD,
    main,
    project_master_v2_boundary_v1,
)

HEAD = "1007b31ab0d1aa27d557efb0ce0d922c1c6eafbd"
TREE = "87108b671cd132c1357d3184d9d239739913df8a"
OTHER = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
INTERNAL = "SO-SRC-FILE:src/trading/master_v2/double_play_entry_exit_policy_v0.py"
EXTERNAL = "SO-SRC-FILE:src/ops/example_immediate_counterparty_v1.py"
FURTHER = "SO-SRC-FILE:src/ops/further_external_dependency_v1.py"
COARSE = "SO-SRC-PKG:trading"
UNKNOWN = "SO-SRC-FILE:src/trading/master_v2/unknown_component_v1.py"
CLOSURE_FLAGS = (
    "CROSS_UNIVERSE_CAUSALITY_PROVEN",
    "CURRENT_COMPONENT_COVERAGE_COMPLETE",
    "EDGE_COVERAGE_COMPLETE",
    "GLOBAL_CAUSAL_CLOSURE_PROVEN",
    "IDENTITY_COVERAGE_COMPLETE",
)
REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = REPO_ROOT / "scripts" / "ops" / "master_v2_boundary_projection_v1"


def _pin(head: str = HEAD, tree: str = TREE) -> dict[str, str]:
    return {"git_head": head, "tree": tree}


def _artifact(
    artifact_id: str,
    role: str,
    payload: dict,
    *,
    provenance: dict | None = None,
    omit_provenance: bool = False,
) -> dict:
    item: dict = {"artifact_id": artifact_id, "role": role, "payload": payload}
    if not omit_provenance:
        item["provenance"] = _pin() if provenance is None else provenance
    return item


def _membership(records: list[dict]) -> dict:
    return _artifact("membership", "MEMBERSHIP_EVIDENCE", {"records": records})


def _internal(endpoint_ref: str = INTERNAL, subject: str = "DOUBLE_PLAY") -> dict:
    return {
        "endpoint_ref": endpoint_ref,
        "endpoint_precision": "PRECISE",
        "proposed_class": "MASTER_V2_INTERNAL",
        "owner_architecture_subject": subject,
        "evidence_bases": ["OWNER_ARCHITECTURE_BINDING", "CURRENT_CONTRACT"],
    }


def _external(endpoint_ref: str = EXTERNAL) -> dict:
    return {
        "endpoint_ref": endpoint_ref,
        "endpoint_precision": "PRECISE",
        "proposed_class": "DIRECT_EXTERNAL_COUNTERPARTY",
        "evidence_bases": ["IMMEDIATE_COUNTERPARTY_EVIDENCE", "BOUNDARY_REFERENCE"],
    }


def _edge(
    edge_id: str,
    source: str,
    target: str,
    *,
    hop: int = 1,
    edge_type: str | None = "HANDOFF",
    authority_constant: bool | None = None,
    state: dict | None = None,
    extra: dict | None = None,
) -> dict:
    typed: dict = {}
    if edge_type is not None:
        typed["edge_type"] = edge_type
    if authority_constant is not None:
        typed["trading_authority_implied"] = authority_constant
    edge = {
        "edge_id": edge_id,
        "hop_distance": hop,
        "typed_edge": typed,
        "source_endpoint_provenance": {"endpoint_ref": source, "precision": "PRECISE"},
        "target_endpoint_provenance": {"endpoint_ref": target, "precision": "PRECISE"},
    }
    if state is not None:
        edge["state_evidence"] = state
    if extra:
        edge.update(extra)
    return edge


def _graph(artifact_id: str, edges: list[dict], *, provenance: dict | None = None) -> dict:
    return _artifact(artifact_id, "GHV_GRAPH", {"edges": edges}, provenance=provenance)


def _bundle(*artifacts: dict, flags: dict | None = None, baseline: dict | None = None) -> dict:
    body = {
        "requested_baseline": baseline or _pin(),
        "artifacts": list(artifacts),
        "impact_reachability": [UNKNOWN],
    }
    if flags is not None:
        body["global_closure_flags"] = flags
    return body


def _ids(rows: list[dict]) -> list[str]:
    return [row["edge_id"] for row in rows]


def _membership_of(report: dict, endpoint_ref: str) -> dict:
    matches = [
        row for row in report["MEMBERSHIP_CLASSIFICATION"] if row["endpoint_ref"] == endpoint_ref
    ]
    assert matches
    return matches[0]


def test_t01_matching_provenance_pin_is_accepted() -> None:
    report = project_master_v2_boundary_v1(
        _bundle(_artifact("prov-current", "PROVENANCE", {"note": "current"}))
    )
    accepted = report["INPUT_PROVENANCE"]["accepted"]
    assert [row["artifact_id"] for row in accepted] == ["prov-current"]
    assert accepted[0]["git_head"] == HEAD
    assert accepted[0]["tree"] == TREE
    assert report["INPUT_PROVENANCE"]["quarantined"] == []
    assert report["BASELINE"]["baseline_status"] == "ACCEPTED"


def test_t02_stale_provenance_rejected() -> None:
    stale = _graph(
        "stale-wrapper",
        [_edge("stale-edge", EXTERNAL, INTERNAL)],
        provenance=_pin(STALE_GRAPH_GIT_HEAD, TREE),
    )
    embedded = _artifact(
        "embedded-stale",
        "GHV_GRAPH",
        {
            "code_snapshot": {"git_head": STALE_GRAPH_GIT_HEAD},
            "edges": [_edge("embedded-stale-edge", EXTERNAL, INTERNAL)],
        },
    )
    mismatched = _graph(
        "other-pin",
        [_edge("other-pin-edge", EXTERNAL, INTERNAL)],
        provenance=_pin(OTHER, TREE),
    )
    current = _graph("current-edge-source", [_edge("keep-me", EXTERNAL, INTERNAL)])
    report = project_master_v2_boundary_v1(
        _bundle(
            stale,
            embedded,
            mismatched,
            current,
            _membership([_internal(), _external()]),
        )
    )
    reasons = {
        row["artifact_id"]: row["reason"] for row in report["INPUT_PROVENANCE"]["quarantined"]
    }
    assert reasons["stale-wrapper"] == "STALE_GRAPH_NOT_PROMOTED"
    assert reasons["embedded-stale"] == "STALE_GRAPH_NOT_PROMOTED"
    assert reasons["other-pin"] == "STALE_PROVENANCE"
    accepted = {row["artifact_id"] for row in report["INPUT_PROVENANCE"]["accepted"]}
    assert "current-edge-source" in accepted
    assert "stale-wrapper" not in accepted
    visible = _ids(report["INBOUND_BOUNDARY_EDGES"])
    assert visible == ["keep-me"]
    assert "stale-edge" not in visible
    assert "embedded-stale-edge" not in visible
    assert report["BOUNDARY_COMPLETENESS"] == "NOT_PROVEN"


def test_t03_missing_provenance_rejected() -> None:
    missing = _graph("no-pin", [_edge("missing-pin-edge", EXTERNAL, INTERNAL)], provenance=None)
    missing["provenance"] = {}
    omitted = _artifact(
        "omitted-pin",
        "GHV_GRAPH",
        {"edges": [_edge("omitted-pin-edge", EXTERNAL, INTERNAL)]},
        omit_provenance=True,
    )
    report = project_master_v2_boundary_v1(
        _bundle(missing, omitted, _membership([_internal(), _external()]))
    )
    reasons = {
        row["artifact_id"]: row["reason"] for row in report["INPUT_PROVENANCE"]["quarantined"]
    }
    assert reasons["no-pin"] == "MISSING_PROVENANCE"
    assert reasons["omitted-pin"] == "MISSING_PROVENANCE"
    assert _ids(report["INBOUND_BOUNDARY_EDGES"]) == []
    assert _ids(report["OUTBOUND_BOUNDARY_EDGES"]) == []


def test_t04_precise_inbound_edge() -> None:
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([_internal(), _external()]),
            _graph(
                "inbound",
                [
                    _edge(
                        "in-1",
                        EXTERNAL,
                        INTERNAL,
                        state={"EXISTS": {"supported": True, "evidence_ref": "exists-1"}},
                    )
                ],
            ),
        )
    )
    assert _ids(report["INBOUND_BOUNDARY_EDGES"]) == ["in-1"]
    edge = report["INBOUND_BOUNDARY_EDGES"][0]
    assert edge["classification"] == "INBOUND_BOUNDARY_EDGE"
    assert edge["source_membership"] == "DIRECT_EXTERNAL_COUNTERPARTY"
    assert edge["target_membership"] == "MASTER_V2_INTERNAL"
    assert edge["EXISTS"] == "TRUE"
    assert edge["WIRED"] == "UNKNOWN"
    assert edge["ACTIVE"] == "UNKNOWN"
    assert report["OUTBOUND_BOUNDARY_EDGES"] == []


def test_t05_precise_outbound_edge() -> None:
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([_internal(), _external()]),
            _graph("outbound", [_edge("out-1", INTERNAL, EXTERNAL)]),
        )
    )
    assert _ids(report["OUTBOUND_BOUNDARY_EDGES"]) == ["out-1"]
    edge = report["OUTBOUND_BOUNDARY_EDGES"][0]
    assert edge["classification"] == "OUTBOUND_BOUNDARY_EDGE"
    assert edge["source_membership"] == "MASTER_V2_INTERNAL"
    assert edge["target_membership"] == "DIRECT_EXTERNAL_COUNTERPARTY"
    assert report["INBOUND_BOUNDARY_EDGES"] == []


def test_t06_coarse_package_endpoint_remains_unclassified() -> None:
    coarse_record = _internal(COARSE)
    coarse_record["endpoint_precision"] = "PRECISE"
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([coarse_record, _external()]),
            _graph("coarse", [_edge("coarse-edge", COARSE, EXTERNAL)]),
        )
    )
    row = _membership_of(report, COARSE)
    assert row["membership"] == "UNCLASSIFIED"
    assert row["reason"] == "COARSE_ENDPOINT"
    assert _ids(report["INBOUND_BOUNDARY_EDGES"]) == []
    assert _ids(report["OUTBOUND_BOUNDARY_EDGES"]) == []
    assert _ids(report["UNCLASSIFIED_BOUNDARY_CANDIDATES"]) == ["coarse-edge"]
    assert report["UNCLASSIFIED_BOUNDARY_CANDIDATES"][0]["classification"] == (
        "UNCLASSIFIED_BOUNDARY_CANDIDATE"
    )


def test_t07_transitive_external_dependency_excluded() -> None:
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([_internal(), _external(), _external(FURTHER)]),
            _graph(
                "transitive",
                [
                    _edge("direct-out", INTERNAL, EXTERNAL),
                    _edge("beyond-1", EXTERNAL, FURTHER, hop=2),
                ],
            ),
        )
    )
    assert _ids(report["OUTBOUND_BOUNDARY_EDGES"]) == ["direct-out"]
    assert "beyond-1" not in _ids(report["INBOUND_BOUNDARY_EDGES"])
    assert "beyond-1" not in _ids(report["OUTBOUND_BOUNDARY_EDGES"])
    assert "beyond-1" not in _ids(report["UNCLASSIFIED_BOUNDARY_CANDIDATES"])
    assert _ids(report["EXCLUDED_TRANSITIVE_EDGES"]) == ["beyond-1"]


def test_t08_unknown_membership_remains_unclassified() -> None:
    unknown = _internal(UNKNOWN)
    unknown["evidence_bases"] = ["CENSUS_LABEL_ALONE", "IMPORT_RELATIONSHIP", "GRAPH_REACHABILITY"]
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([unknown, _external()]),
            _graph("unknown-edge", [_edge("unknown-1", EXTERNAL, UNKNOWN)]),
        )
    )
    row = _membership_of(report, UNKNOWN)
    assert row["membership"] == "UNCLASSIFIED"
    assert row["reason"] == "FORBIDDEN_MEMBERSHIP_BASIS"
    assert _ids(report["INBOUND_BOUNDARY_EDGES"]) == []
    assert _ids(report["UNCLASSIFIED_BOUNDARY_CANDIDATES"]) == ["unknown-1"]
    assert all(
        item["endpoint_ref"] != UNKNOWN or item["membership"] == "UNCLASSIFIED"
        for item in report["MEMBERSHIP_CLASSIFICATION"]
    )


def test_t09_constant_authority_flag_is_not_proof() -> None:
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([_internal(), _external()]),
            _graph(
                "authority",
                [_edge("auth-1", EXTERNAL, INTERNAL, authority_constant=False)],
            ),
        )
    )
    authority = report["AUTHORITY_EVIDENCE"][0]
    assert authority["trading_authority_implied_constant"] is False
    assert authority["constant_is_proof"] is False
    assert authority["authority_transfer"] == "NOT_PROVEN"
    assert authority["data_transfer"] == "UNKNOWN"
    assert authority["authority_transfer"] != authority["data_transfer"]


def test_t10_static_evidence_does_not_become_active() -> None:
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([_internal(), _external()]),
            _graph(
                "static-edge",
                [
                    _edge(
                        "static-1",
                        EXTERNAL,
                        INTERNAL,
                        state={
                            "EXISTS": {"supported": True, "evidence_ref": "exists-static"},
                            "ACTIVE": {"supported": True, "evidence_ref": "static-active"},
                        },
                    )
                ],
            ),
            _artifact(
                "static-observation",
                "RUNTIME_OBSERVATION",
                {
                    "observations": [
                        {
                            "edge_id": "static-1",
                            "evidence_class": "STATIC_CONTRACT",
                            "observation_valid": True,
                            "active_observed": True,
                            "static_or_contract": True,
                            "evidence_ref": "contract-constant",
                        }
                    ]
                },
            ),
        )
    )
    edge = report["INBOUND_BOUNDARY_EDGES"][0]
    assert edge["EXISTS"] == "TRUE"
    assert edge["ACTIVE"] == "UNKNOWN"
    assert edge["ACTIVE"] is not False
    assert report["RUNTIME_EVIDENCE"][0]["static_evidence_is_active"] is False


def test_t11_missing_edge_types_preserve_not_proven() -> None:
    flags = {name: True for name in CLOSURE_FLAGS}
    report = project_master_v2_boundary_v1(
        _bundle(
            _membership([_internal(), _external()]),
            _graph("missing-type", [_edge("typed-gap", EXTERNAL, INTERNAL, edge_type=None)]),
            flags=flags,
        )
    )
    assert "MISSING_EDGE_TYPE" in report["COVERAGE_GAPS"]["UNSUPPORTED_EDGE_TYPES"]
    assert report["COVERAGE_GAPS"]["BOUNDARY_COMPLETENESS"] == "NOT_PROVEN"
    assert report["BOUNDARY_COMPLETENESS"] == "NOT_PROVEN"
    assert flags == {name: True for name in CLOSURE_FLAGS}


def test_t12_existing_global_closure_flags_remain_unchanged() -> None:
    flags = {name: True for name in CLOSURE_FLAGS}
    bundle = _bundle(
        _membership([_internal(), _external()]),
        _graph("flags", [_edge("flag-edge", EXTERNAL, INTERNAL)]),
        flags=flags,
    )
    report = project_master_v2_boundary_v1(bundle)
    assert report["EXISTING_GLOBAL_CLOSURE_FLAGS"] == flags
    report["EXISTING_GLOBAL_CLOSURE_FLAGS"]["EDGE_COVERAGE_COMPLETE"] = False
    assert flags["EDGE_COVERAGE_COMPLETE"] is True
    assert bundle["global_closure_flags"]["GLOBAL_CAUSAL_CLOSURE_PROVEN"] is True
    assert report["BOUNDARY_COMPLETENESS"] == "NOT_PROVEN"
    source = (MODULE_DIR / "project_v1.py").read_text(encoding="utf-8")
    decision = source.split("def _boundary_completeness", 1)[1].split("\ndef ", 1)[0]
    for name in CLOSURE_FLAGS:
        assert name not in decision


def test_t13_deterministic_output() -> None:
    bundle = _bundle(
        _graph(
            "z-edges",
            [
                _edge("b-edge", INTERNAL, EXTERNAL),
                _edge("a-edge", EXTERNAL, INTERNAL),
            ],
        ),
        _membership([_external(), _internal()]),
    )
    first = project_master_v2_boundary_v1(bundle)
    second = project_master_v2_boundary_v1(bundle)
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert _ids(first["INBOUND_BOUNDARY_EDGES"]) == ["a-edge"]
    assert _ids(first["OUTBOUND_BOUNDARY_EDGES"]) == ["b-edge"]
    assert [row["endpoint_ref"] for row in first["MEMBERSHIP_CLASSIFICATION"]] == sorted(
        row["endpoint_ref"] for row in first["MEMBERSHIP_CLASSIFICATION"]
    )


def test_t14_default_execution_writes_no_files(tmp_path: Path, capsys) -> None:
    fixture = {
        "requested_baseline": _pin(STALE_GRAPH_GIT_HEAD, TREE),
        "artifacts": [
            _artifact("caller-current", "PROVENANCE", {"note": "pin matches cli baseline"})
        ],
    }
    source = tmp_path / "input.json"
    source.write_text(json.dumps(fixture), encoding="utf-8")
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    module_before = sorted(path.name for path in MODULE_DIR.rglob("*"))
    exit_code = main(
        [
            "--baseline-head",
            HEAD,
            "--baseline-tree",
            TREE,
            "--input",
            str(source),
        ]
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    module_after = sorted(path.name for path in MODULE_DIR.rglob("*"))
    captured = capsys.readouterr()
    assert exit_code == 0
    assert after == before
    assert module_after == module_before
    assert captured.err == ""
    report = json.loads(captured.out)
    assert report["BASELINE"]["requested_git_head"] == HEAD
    assert report["BASELINE"]["requested_git_head"] != STALE_GRAPH_GIT_HEAD
    assert report["BOUNDARY_COMPLETENESS"] == "NOT_PROVEN"
    assert [row["artifact_id"] for row in report["INPUT_PROVENANCE"]["accepted"]] == [
        "caller-current"
    ]


def test_t15_no_productive_trading_modules_imported() -> None:
    forbidden_prefixes = (
        "execution",
        "scripts.ops.ghv_",
        "src.execution",
        "src.trading",
        "trading",
    )
    for path in MODULE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module or "")
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id != "__import__"
                if isinstance(func, ast.Attribute):
                    assert func.attr != "import_module"
            for module_name in modules:
                for prefix in forbidden_prefixes:
                    assert module_name != prefix
                    assert not module_name.startswith(prefix + ".")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONPATH", None)
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
        "before = set(sys.modules)\n"
        "import scripts.ops.master_v2_boundary_projection_v1.project_v1\n"
        "delta = set(sys.modules) - before\n"
        "bad = sorted(\n"
        "    name for name in delta\n"
        "    if name == 'trading' or name.startswith('trading.')\n"
        "    or name.startswith('src.trading') or name.startswith('execution')\n"
        "    or name.startswith('scripts.ops.ghv_')\n"
        ")\n"
        "print('\\n'.join(bad))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == ""
