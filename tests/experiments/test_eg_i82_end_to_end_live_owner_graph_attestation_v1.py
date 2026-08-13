"""U-I82-R24 tests for durable end-to-end live-owner graph attestation."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pandas as pd
import pytest

from src.analytics.explorer import ExperimentSummary, _row_to_summary
from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.cross_lane_identity_join_v1 import (
    JOIN_PLANES,
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.experiments.eg_i82_end_to_end_live_owner_graph_attestation_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    EG_I82_END_TO_END_LIVE_OWNER_GRAPH_ATTESTATION_REGISTERED,
    EXPECTED_EDGE_COUNT,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    REAL_LIVE_OWNER_PATHS,
    REQUIRED_GRAPH_EDGE_IDS,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    EgI82EndToEndLiveOwnerGraphAttestationError,
    attest_eg_i82_end_to_end_live_owner_graph_v1,
    is_eg_i82_end_to_end_live_owner_graph_attestation_registered,
    require_eg_i82_complete_live_edge_matrix_v1,
)
from src.experiments.eg_i82_join_verifier_v1 import NAMED_JOIN_LANES
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    build_manifest,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRef,
    LineageRefType,
    LineageRelation,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    EXPERIMENT_OWNER_DOMAIN,
)
from src.levelup.v0_models import EvidenceBundleRefV0, LevelUpManifestV0, SliceContractV0
from src.live_eval.live_session_eval import compute_metrics
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTESTATION_PATH = (
    REPO_ROOT / "src" / "experiments" / "eg_i82_end_to_end_live_owner_graph_attestation_v1.py"
)
VERIFIER_PATH = REPO_ROOT / "src" / "experiments" / "eg_i82_join_verifier_v1.py"
MASTER_RUNBOOK_PATH = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH_PATH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
I52_MODELS_PATH = REPO_ROOT / "src" / "levelup" / "v0_models.py"
I61_EVAL_PATH = REPO_ROOT / "src" / "live_eval" / "live_session_eval.py"
I65_EXPLORER_PATH = REPO_ROOT / "src" / "analytics" / "explorer.py"
PREREG_FIX = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "preregistration_valid_non_authoritative.json"
)

_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r24-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r24-content").hexdigest()
_MD5_12 = "abcdef012345"
_RUN_ID = str(uuid.uuid4())
_CAMPAIGN_ID = "campaign-i82-r24"
_SESSION_ID = "session-i82-r24"
_CAPSULE_ID = "capsule-i82-r24"
_LIVE_OWNER_FILES = (
    REPO_ROOT / "src" / "governance" / "promotion_loop" / "experiment_lineage_ref_producer_v1.py",
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "preregistration_contract_v1.py",
    I52_MODELS_PATH,
    REPO_ROOT / "src" / "ingress" / "capsules" / "evidence_capsule.py",
    I61_EVAL_PATH,
    I65_EXPLORER_PATH,
)


def _sample_config() -> ExperimentConfig:
    return ExperimentConfig(
        name="MA Optimization",
        strategy_name="ma_crossover",
        param_sweeps=[
            ParamSweep("slow", [50, 100], description="ignored in identity"),
            ParamSweep("fast", [5, 10]),
        ],
        symbols=["ETH/EUR", "BTC/EUR"],
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-06-01",
        initial_capital=10000.0,
        base_params={"window": 3},
    )


def _i52_live() -> dict[str, object]:
    evidence = EvidenceBundleRefV0(relative_dir="out/ops/slice_demo_001/")
    slice_model = SliceContractV0(
        slice_id="S1-R3",
        title="Live execution gated",
        contract_summary="Without enabled+armed+token → no order.",
        evidence=evidence,
    )
    return LevelUpManifestV0(title="Test", slices=(slice_model,)).model_dump(mode="python")


def _i56_live() -> dict[str, object]:
    return {
        "capsule_id": _CAPSULE_ID,
        "run_id": "default",
        "ts_ms": 1000,
        "artifacts": [],
        "labels": {},
        "facts": {},
    }


def _i65_live() -> dict[str, object]:
    return {
        "experiment_id": _RUN_ID,
        "run_type": "backtest",
        "run_name": "hist-run",
    }


def _canonical_owners(*, identity: str | None = None) -> dict[str, dict[str, object]]:
    manifest = build_manifest(_sample_config())
    package_n = str(manifest["experiment_identity_id"])
    if identity is None:
        identity = package_n
    assert is_package_n_sha256_canonical_id(package_n)
    return {
        "I16": {
            "manifest": manifest,
            "artifact_path": ARTIFACT_FILENAME,
            "run_id": "run-i16-r24",
            "campaign_id": _CAMPAIGN_ID,
            "session_id": _SESSION_ID,
        },
        "I17": {
            "live": load_preregistration_contract_dict_v1(PREREG_FIX),
            "experiment_identity_id": identity,
            "run_id": "run-i17-r24",
            "legacy_alias_md5_12": _MD5_12,
        },
        "I52": {
            "live": _i52_live(),
            "experiment_identity_id": identity,
            "run_id": "run-i52-r24",
            "campaign_id": _CAMPAIGN_ID,
            "session_id": "session-i52-r24",
            "legacy_alias_md5_12": _MD5_12,
            "content_sha256": _CONTENT_SHA256,
        },
        "I56": {
            "live": _i56_live(),
            "experiment_identity_id": identity,
            "campaign_id": _CAMPAIGN_ID,
            "session_id": "session-i56-r24",
            "legacy_alias_md5_12": _MD5_12,
        },
        "I61": {
            "live": compute_metrics([]),
            "experiment_identity_id": identity,
            "run_id": "run-i61-r24",
            "campaign_id": _CAMPAIGN_ID,
            "session_id": "session-i61-r24",
            "legacy_alias_md5_12": _MD5_12,
            "content_sha256": _CONTENT_SHA256,
            "evidence_ref": "evidence/i61-r24",
        },
        "I65": {
            "live": _i65_live(),
            "experiment_identity_id": identity,
            "campaign_id": _CAMPAIGN_ID,
            "session_id": "session-i65-r24",
            "legacy_alias_md5_12": _MD5_12,
            "content_sha256": _CONTENT_SHA256,
            "evidence_ref": "evidence/i65-r24",
        },
    }


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_attestation_is_registered_and_requires_exactly_42_edges() -> None:
    assert CONTRACT_ID == "eg_i82_end_to_end_live_owner_graph_attestation_v1"
    assert EG_I82_END_TO_END_LIVE_OWNER_GRAPH_ATTESTATION_REGISTERED is True
    assert is_eg_i82_end_to_end_live_owner_graph_attestation_registered() is True
    assert EXPECTED_EDGE_COUNT == 42
    assert len(REQUIRED_GRAPH_EDGE_IDS) == 42
    assert len(NAMED_JOIN_LANES) == 6
    assert len(JOIN_PLANES) == 7
    assert set(REAL_LIVE_OWNER_PATHS) == set(NAMED_JOIN_LANES)


def test_canonical_full_live_owner_graph_passes() -> None:
    owners = _canonical_owners()
    snapshot = copy.deepcopy(owners)
    first = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    second = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    assert owners == snapshot
    assert first.to_canonical_mapping() == second.to_canonical_mapping()
    assert first.package_n_sha256 == snapshot["I16"]["manifest"]["experiment_identity_id"]
    assert is_package_n_sha256_canonical_id(first.package_n_sha256)
    assert first.expected_edge_count == 42
    assert first.edges_evaluated == 42
    assert first.edges_proven == 42
    assert first.edges_disproven == 0
    assert first.edges_not_proven == 0
    assert first.edges_not_applicable == 0
    assert first.all_required_edges_proven is True
    assert first.static_flag_aggregation_only is False
    assert first.full_graph_traversal is True
    assert first.end_to_end_join_graph_proven is True
    assert first.eg_i82_join_closure_proven is True
    assert first.eg_i82_join_status == "CLOSED_PROVEN"
    assert tuple(edge.edge_id for edge in first.edges) == REQUIRED_GRAPH_EDGE_IDS
    assert all(edge.canonical_join_key == first.package_n_sha256 for edge in first.edges)
    assert all(edge.proven for edge in first.edges)
    assert set(first.live_owner_paths.values()) == set(REAL_LIVE_OWNER_PATHS.values())
    assert all(
        first.lane_identity_presence[lane] == PlanePresence.PRESENT.value
        for lane in NAMED_JOIN_LANES
    )
    campaign_edges = [edge for edge in first.edges if edge.plane == "CAMPAIGN"]
    assert any(edge.presence == PlanePresence.PRESENT.value for edge in campaign_edges)
    assert any(edge.presence == PlanePresence.ABSENT_DECLARED.value for edge in campaign_edges)


def test_declared_absence_is_deterministic_and_proven() -> None:
    owners = _canonical_owners()
    for lane in ("I16", "I52", "I56", "I61", "I65"):
        owners[lane].pop("campaign_id", None)
    result = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    campaign = {edge.lane: edge for edge in result.edges if edge.plane == "CAMPAIGN"}
    assert campaign["I17"].presence == PlanePresence.ABSENT_DECLARED.value
    assert campaign["I16"].presence == PlanePresence.ABSENT_DECLARED.value
    assert campaign["I17"].proven is True
    assert result.edges_proven == 42
    assert result.eg_i82_join_status == "CLOSED_PROVEN"


def test_exactly_one_missing_required_edge_fail_closed() -> None:
    owners = _canonical_owners()
    result = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    edges = [edge.to_canonical_mapping() for edge in result.edges]
    removed = edges.pop(
        edges.index(next(item for item in edges if item["edge_id"] == "I65xEVIDENCE"))
    )
    assert removed["edge_id"] == "I65xEVIDENCE"
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="missing required edge rejected: I65xEVIDENCE",
    ):
        require_eg_i82_complete_live_edge_matrix_v1(
            edges,
            package_n_sha256=result.package_n_sha256,
        )


def test_wrong_join_key_on_one_edge_fail_closed() -> None:
    owners = _canonical_owners()
    owners["I65"]["experiment_identity_id"] = str(uuid.uuid4())
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="noncanonical ID substitution rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_conflicting_package_n_within_owner_fail_closed() -> None:
    owners = _canonical_owners()
    manifest = owners["I16"]["manifest"]
    owners["I16"]["ref"] = LineageRef(
        ref_type=LineageRefType.EXPERIMENT,
        ref_id=_OTHER_SHA256,
        relation=LineageRelation.SOURCES,
        owner_domain=EXPERIMENT_OWNER_DOMAIN,
        required=False,
        digest=str(manifest["integrity"]["content_sha256"]),
        artifact_path=ARTIFACT_FILENAME,
    )
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="conflicting identity rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_conflicting_package_n_across_owners_fail_closed() -> None:
    owners = _canonical_owners()
    owners["I65"]["experiment_identity_id"] = _OTHER_SHA256
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="conflicting identity rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_run_as_identity_fail_closed() -> None:
    owners = _canonical_owners()
    owners["I65"]["experiment_identity_id"] = str(owners["I65"]["live"]["experiment_id"])
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="noncanonical ID substitution rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_alias_as_identity_fail_closed() -> None:
    owners = _canonical_owners()
    owners["I52"]["experiment_identity_id"] = _MD5_12
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="noncanonical ID substitution rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_synthetic_package_n_identity_fail_closed() -> None:
    source = ATTESTATION_PATH.read_text(encoding="utf-8")
    assert "hashlib" not in source
    owners = _canonical_owners()
    owners["I56"].pop("experiment_identity_id")
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="implicit absence rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_implicit_absence_of_owner_fail_closed() -> None:
    owners = _canonical_owners()
    owners.pop("I61")
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="implicit absence rejected: named lane I61 is missing",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_cross_lane_substitution_fail_closed() -> None:
    owners = _canonical_owners()
    owners["I52"]["I16"] = {"manifest": owners["I16"]["manifest"]}
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="cross-lane substitution rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    live = dict(owners["I61"]["live"])
    live["I16"] = "not-allowed"
    owners["I61"]["live"] = live
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="cross-lane substitution rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_cross_plane_substitution_fail_closed() -> None:
    owners = _canonical_owners()
    live = dict(owners["I61"]["live"])
    live["plane_presence"] = {"IDENTITY": "PRESENT"}
    owners["I61"]["live"] = live
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="cross-plane substitution rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_malformed_owner_payload_fail_closed() -> None:
    owners = _canonical_owners()
    owners["I52"]["live"] = "not-an-object"
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="malformed plane data rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_ambiguous_join_fail_closed() -> None:
    owners = _canonical_owners()
    owners["I56"]["live"] = [_i56_live(), _i56_live()]
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="ambiguous join rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners)


def test_duplicate_and_unexpected_edge_fail_closed() -> None:
    owners = _canonical_owners()
    result = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    edges = [edge.to_canonical_mapping() for edge in result.edges]
    duplicated = edges + [edges[0]]
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="duplicate/conflicting edge registration rejected",
    ):
        require_eg_i82_complete_live_edge_matrix_v1(
            duplicated,
            package_n_sha256=result.package_n_sha256,
        )
    extra = edges + [
        {
            "edge_id": "I99xIDENTITY",
            "lane": "I99",
            "plane": "IDENTITY",
            "presence": PlanePresence.PRESENT.value,
            "canonical_join_key": result.package_n_sha256,
        }
    ]
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="unexpected extra edge rejected",
    ):
        require_eg_i82_complete_live_edge_matrix_v1(
            extra,
            package_n_sha256=result.package_n_sha256,
        )
    owners_extra = dict(owners)
    owners_extra["I99"] = {"live": {}, "experiment_identity_id": result.package_n_sha256}
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="unexpected extra edge rejected",
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(owners_extra)


def test_static_join_records_are_not_accepted_as_live_owners() -> None:
    owners = _canonical_owners()
    result = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    static = {
        lane: {
            "plane_presence": {plane: PlanePresence.PRESENT.value for plane in JOIN_PLANES},
            "experiment_identity_id": result.package_n_sha256,
            "contract_id": "static",
        }
        for lane in NAMED_JOIN_LANES
    }
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match=(
            "static join record rejected|malformed plane data rejected|"
            "cross-plane substitution rejected"
        ),
    ):
        attest_eg_i82_end_to_end_live_owner_graph_v1(static)


def test_wrong_join_key_on_matrix_edge_fail_closed() -> None:
    owners = _canonical_owners()
    result = attest_eg_i82_end_to_end_live_owner_graph_v1(owners)
    edges = [edge.to_canonical_mapping() for edge in result.edges]
    for item in edges:
        if item["edge_id"] == "I17xRUN":
            item["canonical_join_key"] = _OTHER_SHA256
    with pytest.raises(
        EgI82EndToEndLiveOwnerGraphAttestationError,
        match="conflicting identity rejected: I17xRUN join key disagrees",
    ):
        require_eg_i82_complete_live_edge_matrix_v1(
            edges,
            package_n_sha256=result.package_n_sha256,
        )


def test_historical_readability_paths_remain() -> None:
    explorer_source = I65_EXPLORER_PATH.read_text(encoding="utf-8")
    assert 'experiment_id=str(row.get("run_id", ""))' in explorer_source
    row = pd.Series(
        {
            "run_id": _RUN_ID,
            "run_type": "backtest",
            "run_name": "hist-run",
            "strategy_key": "ma_crossover",
            "sweep_name": None,
            "scan_name": None,
            "portfolio_name": None,
            "symbol": "BTC-USDT",
            "metadata_json": "{}",
            "timestamp": "2026-01-01T00:00:00",
            "params_json": "{}",
            "sharpe": 1.2,
            "total_return": 0.1,
            "max_drawdown": -0.05,
            "cagr": 0.08,
            "stats_json": "{}",
        }
    )
    summary = _row_to_summary(row)
    assert isinstance(summary, ExperimentSummary)
    assert summary.experiment_id == _RUN_ID
    assert not hasattr(summary, "experiment_identity_id")
    models_source = I52_MODELS_PATH.read_text(encoding="utf-8")
    assert 'extra="forbid"' in models_source
    eval_source = I61_EVAL_PATH.read_text(encoding="utf-8")
    assert "class Fill:" in eval_source
    assert "def compute_metrics(" in eval_source


def test_runtime_and_import_invariants() -> None:
    modules = _imported_modules(ATTESTATION_PATH)
    assert "src.analytics.explorer" in modules
    assert "src.levelup.v0_models" in modules
    assert "src.ingress.capsules.evidence_capsule" in modules
    assert "src.live_eval.live_session_eval" in modules
    assert (
        "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1"
        ".preregistration_contract_v1" in modules
    )
    assert "src.governance.promotion_loop.experiment_lineage_ref_producer_v1" in modules
    assert "src.experiments.eg_i82_join_verifier_v1" in modules
    assert "hashlib" not in modules
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    source = ATTESTATION_PATH.read_text(encoding="utf-8")
    assert "place_order" not in source
    verifier_source = VERIFIER_PATH.read_text(encoding="utf-8")
    assert "eg_i82_end_to_end_live_owner_graph_attestation_v1" not in verifier_source
    for path in _LIVE_OWNER_FILES:
        text = path.read_text(encoding="utf-8")
        assert "eg_i82_end_to_end_live_owner_graph_attestation_v1" not in text
        assert "attest_eg_i82_end_to_end_live_owner_graph_v1" not in text
    master = MASTER_RUNBOOK_PATH.read_text(encoding="utf-8")
    assert "## 5.8 EG-I82-JOIN Package-N live-owner identity-join closeout" in master
    assert "EG_I82_JOIN_STATUS=CLOSED_PROVEN" in master
    assert "SUCCESSOR_PHASE_AUTHORIZED=false" in master
    assert "RUNTIME_AUTHORIZATION_EFFECT=NONE" in master
    assert "ORDER_EFFECT=NONE" in master
    map_of_truth = MAP_OF_TRUTH_PATH.read_text(encoding="utf-8")
    assert "## 8.2 EG-I82-JOIN closeout (navigation only)" in map_of_truth
    assert "THIS_SECTION_DEFINES_NO_SEMANTICS=true" in map_of_truth
    assert "EG_I82_JOIN_STATUS=CLOSED_PROVEN" not in map_of_truth
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1
