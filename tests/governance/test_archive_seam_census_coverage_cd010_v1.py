"""CD-010 archive-seam census + GHV graph coverage regression. AUTHORITY=NONE."""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict, deque
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "config/governance/current_system_census_graph_v1/source_v1.json"
VALIDATOR = REPO / "scripts/ops/validate_current_system_census_graph_v1.py"
CROSSWALK_CLI = REPO / "scripts/ops/ghv_forensic_whole_system_crosswalk_v1/cli.py"

SMOKE_HOST = "SO-OPS-PKG:productive_decision_host_active_archive_three_family_binding_v1"
WEBUI = "SO-SRC-PKG:webui"
MATERIALIZER = "SO-OPS-PKG:presentation_projection_operational_materializer_invocation_v1"
OCTET = "SO-OPS-PKG:presentation_projection_octet_orchestrator_v1"

REQUIRED_ARCHIVE_EDGE_IDS = frozenset(
    {
        "archive_selection_binding_to_universe_readmodel_surface",
        "archive_verified_readmodel_to_smoke_host",
        "archive_smoke_host_to_archive_sibling_export_contract",
        "archive_smoke_host_to_canonical_decision_exporter",
        "archive_smoke_host_to_dynamic_scope_exporter",
        "archive_smoke_host_to_double_play_exporter",
        "archive_smoke_host_to_regime_bull_bear_exporter",
        "archive_smoke_host_to_risk_sizing_exporter",
        "archive_smoke_host_to_execution_reconciliation_exporter",
        "archive_smoke_host_to_economic_summary_exporter",
        "archive_smoke_host_to_safety_authority_exporter",
        "archive_smoke_export_to_materializer_invocation",
        "archive_materializer_invocation_to_octet_orchestrator",
        "archive_octet_orchestrator_to_presentation_builder",
    }
)

EXPORTER_TARGETS = frozenset(
    {
        "SO-OPS-PKG:double_play_archive_sibling_exporter_v1",
        "SO-OPS-PKG:regime_bull_bear_switch_archive_sibling_exporter_v1",
        "SO-OPS-PKG:risk_sizing_capital_archive_sibling_exporter_v1",
        "SO-OPS-PKG:execution_reconciliation_archive_sibling_exporter_v1",
        "SO-OPS-PKG:economic_summary_archive_sibling_exporter_v1",
        "SO-OPS-PKG:safety_authority_archive_sibling_exporter_v1",
        "SO-OPS-PKG:canonical_decision_archive_sibling_exporter_v1",
        "SO-OPS-PKG:dynamic_scope_archive_sibling_exporter_v1",
    }
)


def _load_census() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_cd010_webui_retargeted_to_workflow_archive_surface() -> None:
    doc = _load_census()
    webui = next(o for o in doc["census_objects"] if o["object_id"] == WEBUI)
    paths = webui.get("paths") or []
    assert "src/ops/workflow_archive_readmodel_projections_v1/**" in paths
    assert "src/ops/presentation_archive_root_v1/**" in paths
    assert "src/webui/**" not in paths
    assert webui.get("name") == "workflow_archive_readmodel_projections_v1"


def test_cd010_archive_seam_edges_present_and_non_authorizing() -> None:
    doc = _load_census()
    by_id = {e["edge_id"]: e for e in doc["semantic_edges"]}
    assert REQUIRED_ARCHIVE_EDGE_IDS <= set(by_id)
    for eid in REQUIRED_ARCHIVE_EDGE_IDS:
        edge = by_id[eid]
        assert edge.get("authority_effect") == "NONE"
        assert edge.get("flow_type") in {"EVIDENCE_FLOW", "EVIDENCE"}
        assert edge.get("map_relationship") == "CODE_ONLY"
        assert edge.get("productive_reachability") is False


def test_cd010_discrepancy_closed() -> None:
    doc = _load_census()
    cd010 = next(d for d in doc["census_discrepancies"] if d.get("id") == "CD-010")
    assert "CLOSED_PASS" in cd010.get("detail", "")


def test_archive_seam_structural_forward_and_reverse_traversal() -> None:
    doc = _load_census()
    adj: dict[str, set[str]] = defaultdict(set)
    radj: dict[str, set[str]] = defaultdict(set)
    for e in doc["semantic_edges"]:
        if e.get("edge_id") not in REQUIRED_ARCHIVE_EDGE_IDS and not (
            e.get("edge_id", "").startswith("archive_")
        ):
            continue
        s, t = e["source_object"], e["target_object"]
        adj[s].add(t)
        radj[t].add(s)

    def reach(start: str, graph: dict[str, set[str]], depth: int = 12) -> set[str]:
        seen = {start}
        q: deque[tuple[str, int]] = deque([(start, 0)])
        out: set[str] = set()
        while q:
            n, d = q.popleft()
            if d > 0:
                out.add(n)
            if d >= depth:
                continue
            for nb in graph.get(n, ()):
                if nb not in seen:
                    seen.add(nb)
                    q.append((nb, d + 1))
        return out

    forward = reach(SMOKE_HOST, adj)
    assert EXPORTER_TARGETS <= forward
    assert MATERIALIZER in forward
    assert OCTET in forward
    assert WEBUI in forward

    reverse = reach(SMOKE_HOST, radj)
    assert WEBUI in reverse


@pytest.mark.parametrize(
    "exporter_id",
    sorted(EXPORTER_TARGETS),
)
def test_smoke_host_reaches_each_family_exporter(exporter_id: str) -> None:
    doc = _load_census()
    adj: dict[str, set[str]] = defaultdict(set)
    for e in doc["semantic_edges"]:
        if e.get("edge_id", "").startswith("archive_smoke_host_to_"):
            adj[e["source_object"]].add(e["target_object"])
    assert exporter_id in adj.get(SMOKE_HOST, set())


def test_ghv_crosswalk_materializes_archive_seam_edges(tmp_path: Path) -> None:
    if not CROSSWALK_CLI.is_file():
        pytest.skip("ghv crosswalk cli not present")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    out = tmp_path / "ghv_out"
    proc = subprocess.run(
        [
            str(REPO / "scripts/pt"),
            str(CROSSWALK_CLI),
            "--output-dir",
            str(out),
            "--declared-current-sha",
            head,
            "--test-execution-sha",
            head,
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload.get("crosswalk_cli_ok") is True
    coverage = payload.get("coverage") or {}
    assert coverage.get("CURRENT_GRAPH_VERIFIED") is True
    assert coverage.get("SNAPSHOT_BINDING_VERIFIED") is True
    porcelain = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if not porcelain:
        assert payload.get("proof_eligibility") is True
    graph = json.loads((out / "composed_forensic_graph.v1.json").read_text(encoding="utf-8"))
    edge_ids = {e.get("edge_id") for e in graph.get("edges") or []}
    for eid in REQUIRED_ARCHIVE_EDGE_IDS:
        census_key = f"census:{eid}"
        assert census_key in edge_ids, f"missing graph edge {census_key}"
