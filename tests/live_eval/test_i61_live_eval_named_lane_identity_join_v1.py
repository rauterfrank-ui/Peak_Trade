"""U-I82-R22 tests for I61 named-lane IDENTITY join on live session eval."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.live_eval.i61_live_eval_join_attachment_v1 import CONTRACT_ID as R8_CONTRACT_ID
from src.live_eval.i61_live_eval_named_lane_identity_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I61_NAMED_LANE_IDENTITY_JOIN_REGISTERED,
    I61LiveEvalNamedLaneIdentityJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i61_named_lane_identity_join_registered,
    join_i61_named_lane_identity_v1,
)
from src.live_eval.live_session_eval import (
    Fill,
    compute_metrics,
    parse_live_session_dir_with_identity_join_v1,
    parse_live_session_metrics_with_identity_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_PATH = REPO_ROOT / "src" / "live_eval" / "i61_live_eval_named_lane_identity_join_v1.py"
ATTACHMENT_PATH = REPO_ROOT / "src" / "live_eval" / "i61_live_eval_join_attachment_v1.py"
EVAL_PATH = REPO_ROOT / "src" / "live_eval" / "live_session_eval.py"
IO_PATH = REPO_ROOT / "src" / "live_eval" / "live_session_io.py"
INIT_PATH = REPO_ROOT / "src" / "live_eval" / "__init__.py"
CLI_PATH = REPO_ROOT / "scripts" / "evaluate_live_session.py"
R15_PATH = REPO_ROOT / "src" / "live_eval" / "i61_live_eval_live_contract_join_v1.py"
_JOIN_MODULE = "src.live_eval.i61_live_eval_named_lane_identity_join_v1"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r22-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r22-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r22-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_CAMPAIGN_ID = "campaign-i61-r22"
_SESSION_ID = "live_eval_fixture_session_non_auth_v1"
_SESSION_DIR = "evidence/fixtures/live_eval/session_dir"
_EVIDENCE_REF = "eval-evidence-i61-r22"


def _metrics() -> dict[str, object]:
    return compute_metrics([])


def _session() -> dict[str, object]:
    return {"session_dir": _SESSION_DIR}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_named_lane_identity_join_is_registered_and_reachable() -> None:
    assert CONTRACT_ID == "i61_live_eval_named_lane_identity_join_v1"
    assert R8_CONTRACT_ID == "live_session_eval_identity_envelope_v1"
    assert I61_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True
    assert is_i61_named_lane_identity_join_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("metrics", "session")


def test_named_metrics_producer_attaches_identity() -> None:
    result = parse_live_session_metrics_with_identity_join_v1(
        _metrics(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(result.join.experiment_identity_id) is True
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.contract["total_fills"] == 0
    assert "experiment_identity_id" not in result.contract
    assert result.join.experiment_identity_id != _SESSION_DIR


def test_declared_absence_for_alias_run_campaign_session_evidence_content_hash() -> None:
    result = parse_live_session_metrics_with_identity_join_v1(
        _metrics(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.legacy_alias_md5_12 is None
    assert result.join.run_id is None
    assert result.join.campaign_id is None
    assert result.join.session_id is None
    assert result.join.content_sha256 is None


def test_present_sidecars_are_joined_and_not_identity() -> None:
    result = parse_live_session_metrics_with_identity_join_v1(
        _metrics(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
        campaign_id=_CAMPAIGN_ID,
        session_id=_SESSION_ID,
        legacy_alias_md5_12=_MD5_12,
        content_sha256=_CONTENT_SHA256,
        evidence_ref=_EVIDENCE_REF,
    )
    assert result.join.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["ALIAS"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert result.join.run_id == _RUN_ID
    assert result.join.campaign_id == _CAMPAIGN_ID
    assert result.join.session_id == _SESSION_ID
    assert result.join.legacy_alias_md5_12 == _MD5_12
    assert result.join.content_sha256 == _CONTENT_SHA256
    assert result.join.evidence_ref == _EVIDENCE_REF
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.join.experiment_identity_id != _CAMPAIGN_ID
    assert result.join.experiment_identity_id != _SESSION_ID
    assert result.join.experiment_identity_id != _MD5_12
    assert result.join.experiment_identity_id != _CONTENT_SHA256
    assert result.join.experiment_identity_id != _EVIDENCE_REF


def test_session_dir_named_lane_does_not_populate_session_plane() -> None:
    result = parse_live_session_dir_with_identity_join_v1(
        _session(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.session_id is None
    assert result.contract["session_dir"] == _SESSION_DIR
    assert result.join.experiment_identity_id != _SESSION_DIR


def test_session_dir_with_explicit_session_id_keeps_planes_distinct() -> None:
    result = parse_live_session_dir_with_identity_join_v1(
        _session(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        session_id=_SESSION_ID,
    )
    assert result.join.session_id == _SESSION_ID
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.experiment_identity_id != _SESSION_ID
    assert result.join.experiment_identity_id != _SESSION_DIR
    assert result.contract["session_dir"] == _SESSION_DIR


def test_fill_metrics_still_compute_without_identity() -> None:
    fill = Fill(
        ts=datetime(2026, 1, 1, tzinfo=timezone.utc),
        symbol="ETH-USD",
        side="buy",
        qty=1.0,
        fill_price=100.0,
    )
    metrics = compute_metrics([fill])
    assert metrics["total_fills"] == 1
    assert "experiment_identity_id" not in metrics
    assert set(fill.__dataclass_fields__) == {"ts", "symbol", "side", "qty", "fill_price"}
    result = parse_live_session_metrics_with_identity_join_v1(
        metrics,
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.contract["total_fills"] == 1
    assert "experiment_identity_id" not in result.contract


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="implicit absence rejected"):
        parse_live_session_metrics_with_identity_join_v1(_metrics())


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_RUN_ID,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_MD5_12,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_MD5_32,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_SESSION_DIR,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_SESSION_ID,
        )


def test_session_dir_and_session_id_must_not_substitute_identity() -> None:
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="cross-plane substitution"):
        parse_live_session_dir_with_identity_join_v1(
            _session(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            session_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="cross-plane substitution"):
        parse_live_session_dir_with_identity_join_v1(
            _session(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            session_id=_SESSION_DIR,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="cross-plane substitution"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            run_id=_PACKAGE_N_SHA256,
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _metrics()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        join_i61_named_lane_identity_v1(
            live,
            surface="metrics",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="conflicting"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            historical_provenance={"experiment_identity_id": _OTHER_SHA256},
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="conflicting"):
        parse_live_session_dir_with_identity_join_v1(
            _session(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            session_dir="evidence/fixtures/live_eval/other_session",
        )


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="ambiguous join rejected"):
        join_i61_named_lane_identity_v1(
            [_metrics(), copy.deepcopy(_metrics())],
            surface="metrics",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="malformed plane data"):
        join_i61_named_lane_identity_v1(
            "not-an-object",  # type: ignore[arg-type]
            surface="metrics",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_live_session_metrics_with_identity_join_v1(
            _metrics(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            session_id="   ",
        )
    mutated = _metrics()
    mutated.pop("total_fills")
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_live_session_metrics_with_identity_join_v1(
            mutated,
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_live_session_dir_with_identity_join_v1(
            {"session_dir": "nopath"},
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_cross_lane_substitution_rejected() -> None:
    live = _metrics()
    live["I56"] = {"capsule_id": "default.capsule"}
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="cross-lane substitution"):
        join_i61_named_lane_identity_v1(
            live,
            surface="metrics",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_cross_plane_substitution_rejected() -> None:
    live = _metrics()
    live["plane_presence"] = {"IDENTITY": "PRESENT"}
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i61_named_lane_identity_v1(
            live,
            surface="metrics",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    live_fill = _metrics()
    live_fill["fill_price"] = 50000.0
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i61_named_lane_identity_v1(
            live_fill,
            surface="metrics",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    live_fills = _metrics()
    live_fills["fills"] = []
    with pytest.raises(I61LiveEvalNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i61_named_lane_identity_v1(
            live_fills,
            surface="metrics",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_join_is_deterministic() -> None:
    first = parse_live_session_metrics_with_identity_join_v1(
        _metrics(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        session_id=_SESSION_ID,
        content_sha256=_CONTENT_SHA256,
    ).join.to_canonical_mapping()
    second = parse_live_session_metrics_with_identity_join_v1(
        _metrics(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        session_id=_SESSION_ID,
        content_sha256=_CONTENT_SHA256,
    ).join.to_canonical_mapping()
    assert first == second


def test_named_lane_does_not_mutate_inputs() -> None:
    raw = _metrics()
    snapshot = copy.deepcopy(raw)
    result = parse_live_session_metrics_with_identity_join_v1(
        raw,
        experiment_identity_id=_PACKAGE_N_SHA256,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    raw["total_fills"] = 99
    assert result.contract["total_fills"] == snapshot["total_fills"]
    assert dict(raw) != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    result = parse_live_session_metrics_with_identity_join_v1(
        _metrics(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.join.run_id == _RUN_ID
    assert dict(result.join.historical_provenance)["legacy_experiment_id"] == _RUN_ID


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def test_named_lane_producer_is_hooked_and_forbidden_surfaces_are_not() -> None:
    join_modules = _imported_modules(JOIN_PATH)
    assert "src.live_eval.i61_live_eval_join_attachment_v1" in join_modules
    assert "src.live_eval.live_session_eval" not in join_modules
    assert "src.live_eval.live_session_io" not in join_modules
    eval_modules = _imported_modules(EVAL_PATH)
    assert _JOIN_MODULE in eval_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in eval_modules
    )
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in eval_modules
    )
    assert "src.analytics.explorer" not in eval_modules
    assert "src.ingress.capsules.evidence_capsule" not in eval_modules
    assert "src.experiments.base" not in eval_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in join_modules
    )
    join_source = JOIN_PATH.read_text(encoding="utf-8")
    assert "write_text" not in join_source
    assert "open(" not in join_source
    assert "Path(" not in join_source
    assert "compute_metrics" not in join_source
    assert "read_fills_csv" not in join_source
    assert "class Fill" not in join_source
    eval_source = EVAL_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in eval_source
    assert "i61_live_eval_live_contract_join_v1" not in eval_source
    assert "class Fill:" in eval_source
    init_source = INIT_PATH.read_text(encoding="utf-8")
    io_source = IO_PATH.read_text(encoding="utf-8")
    cli_source = CLI_PATH.read_text(encoding="utf-8")
    attachment_source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    r15_source = R15_PATH.read_text(encoding="utf-8")
    assert "i61_live_eval_named_lane_identity_join_v1" not in init_source
    assert "i61_live_eval_named_lane_identity_join_v1" not in io_source
    assert "i61_live_eval_named_lane_identity_join_v1" not in cli_source
    assert "i61_live_eval_named_lane_identity_join_v1" not in attachment_source
    assert "i61_live_eval_named_lane_identity_join_v1" not in r15_source
    assert _PACKAGE_N_SHA256 not in eval_source
    assert "experiment_identity_id" not in cli_source
