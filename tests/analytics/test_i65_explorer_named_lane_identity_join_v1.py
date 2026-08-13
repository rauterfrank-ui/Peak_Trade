"""U-I82-R23 tests for I65 named-lane IDENTITY join on explorer."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pandas as pd
import pytest

from src.analytics.explorer import (
    ExperimentSummary,
    _row_to_summary,
    parse_experiment_row_with_identity_join_v1,
    parse_experiment_summary_with_identity_join_v1,
)
from src.analytics.i65_explorer_join_attachment_v1 import CONTRACT_ID as R9_CONTRACT_ID
from src.analytics.i65_explorer_named_lane_identity_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I65_NAMED_LANE_IDENTITY_JOIN_REGISTERED,
    I65ExplorerNamedLaneIdentityJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i65_named_lane_identity_join_registered,
    join_i65_named_lane_identity_v1,
)
from src.analytics.legacy_identity_row_interpretation_v1 import (
    LEGACY_EXPERIMENT_ID_CLASSIFICATION,
    IdentityRequestMode,
    interpret_legacy_identity_row_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_PATH = REPO_ROOT / "src" / "analytics" / "i65_explorer_named_lane_identity_join_v1.py"
ATTACHMENT_PATH = REPO_ROOT / "src" / "analytics" / "i65_explorer_join_attachment_v1.py"
READER_PATH = REPO_ROOT / "src" / "analytics" / "legacy_identity_row_interpretation_v1.py"
EXPLORER_PATH = REPO_ROOT / "src" / "analytics" / "explorer.py"
INIT_PATH = REPO_ROOT / "src" / "analytics" / "__init__.py"
R16_PATH = REPO_ROOT / "src" / "analytics" / "i65_explorer_live_contract_join_v1.py"
EXPERIMENTS_PATH = REPO_ROOT / "src" / "core" / "experiments.py"
_JOIN_MODULE = "src.analytics.i65_explorer_named_lane_identity_join_v1"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r23-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r23-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r23-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_CAMPAIGN_ID = "campaign-i65-r23"
_SESSION_ID = "session-i65-r23"
_EVIDENCE_REF = "explorer-evidence-i65-r23"


def _summary(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_id": _RUN_ID,
        "run_type": "backtest",
        "run_name": "hist-run",
    }
    payload.update(overrides)
    return payload


def _row(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "run_id": _RUN_ID,
        "run_type": "backtest",
        "run_name": "hist-run",
    }
    payload.update(overrides)
    return payload


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
    assert CONTRACT_ID == "i65_explorer_named_lane_identity_join_v1"
    assert R9_CONTRACT_ID == "i65_explorer_join_attachment_v1"
    assert I65_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True
    assert is_i65_named_lane_identity_join_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("summary", "row")


def test_named_summary_producer_attaches_package_n_identity() -> None:
    result = parse_experiment_summary_with_identity_join_v1(
        _summary(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(result.join.experiment_identity_id) is True
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert result.join.run_id == _RUN_ID
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.contract.experiment_id == _RUN_ID
    assert not hasattr(result.contract, "experiment_identity_id")


def test_declared_absence_for_alias_campaign_session_evidence_content_hash() -> None:
    result = parse_experiment_summary_with_identity_join_v1(
        _summary(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.legacy_alias_md5_12 is None
    assert result.join.campaign_id is None
    assert result.join.session_id is None
    assert result.join.content_sha256 is None


def test_present_sidecars_are_joined_and_not_identity() -> None:
    result = parse_experiment_summary_with_identity_join_v1(
        _summary(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        campaign_id=_CAMPAIGN_ID,
        session_id=_SESSION_ID,
        legacy_alias_md5_12=_MD5_12,
        content_sha256=_CONTENT_SHA256,
        evidence_ref=_EVIDENCE_REF,
    )
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["ALIAS"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert result.join.campaign_id == _CAMPAIGN_ID
    assert result.join.session_id == _SESSION_ID
    assert result.join.legacy_alias_md5_12 == _MD5_12
    assert result.join.content_sha256 == _CONTENT_SHA256
    assert result.join.evidence_ref == _EVIDENCE_REF
    assert result.join.experiment_identity_id != _CAMPAIGN_ID
    assert result.join.experiment_identity_id != _SESSION_ID
    assert result.join.experiment_identity_id != _MD5_12
    assert result.join.experiment_identity_id != _CONTENT_SHA256
    assert result.join.experiment_identity_id != _EVIDENCE_REF
    assert result.join.run_id == _RUN_ID


def test_named_row_producer_attaches_identity_and_keeps_run_plane() -> None:
    result = parse_experiment_row_with_identity_join_v1(
        _row(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert result.join.run_id == _RUN_ID
    assert result.join.experiment_identity_id != result.contract["run_id"]
    assert result.contract["run_id"] == _RUN_ID


def test_legacy_experiment_id_is_run_provenance_not_identity() -> None:
    result = parse_experiment_row_with_identity_join_v1(
        _row(experiment_id=_RUN_ID),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.run_id == _RUN_ID
    assert dict(result.join.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert (
        dict(result.join.historical_provenance)["legacy_experiment_id_classification"]
        == LEGACY_EXPERIMENT_ID_CLASSIFICATION
    )
    assert result.join.experiment_identity_id != _RUN_ID


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="implicit absence rejected"):
        parse_experiment_summary_with_identity_join_v1(_summary())


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_RUN_ID,
        )
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_MD5_12,
        )
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_MD5_32,
        )


def test_synthetic_package_n_identity_from_run_id_forbidden() -> None:
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="implicit absence rejected"):
        parse_experiment_row_with_identity_join_v1(_row())
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_RUN_ID,
        )
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(experiment_id=_PACKAGE_N_SHA256),
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_run_id_sidecar_cannot_fill_identity() -> None:
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            run_id=_RUN_ID,
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _summary()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        join_i65_named_lane_identity_v1(
            live,
            surface="summary",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="conflicting"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            historical_provenance={"experiment_identity_id": _OTHER_SHA256},
        )
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="conflicting"):
        parse_experiment_row_with_identity_join_v1(
            _row(experiment_id=str(uuid.uuid4())),
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="ambiguous join rejected"):
        join_i65_named_lane_identity_v1(
            [_summary(), _summary(run_name="other")],
            surface="summary",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="malformed plane data"):
        join_i65_named_lane_identity_v1(
            "not-an-object",  # type: ignore[arg-type]
            surface="summary",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            session_id="   ",
        )
    mutated = _summary()
    mutated.pop("run_type")
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_experiment_summary_with_identity_join_v1(
            mutated,
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_cross_lane_substitution_rejected() -> None:
    live = _summary()
    live["I61"] = {"session_dir": "/tmp/eval"}
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="cross-lane substitution"):
        join_i65_named_lane_identity_v1(
            live,
            surface="summary",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_cross_plane_substitution_rejected() -> None:
    live = _summary()
    live["plane_presence"] = {"IDENTITY": "PRESENT"}
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i65_named_lane_identity_v1(
            live,
            surface="summary",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    live_fill = _summary()
    live_fill["session_dir"] = "evidence/fixtures/live_eval/session_dir"
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i65_named_lane_identity_v1(
            live_fill,
            surface="summary",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I65ExplorerNamedLaneIdentityJoinError, match="cross-plane substitution"):
        parse_experiment_summary_with_identity_join_v1(
            _summary(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            session_id=_PACKAGE_N_SHA256,
        )


def test_join_is_deterministic() -> None:
    first = parse_experiment_summary_with_identity_join_v1(
        _summary(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        content_sha256=_CONTENT_SHA256,
    ).join.to_canonical_mapping()
    second = parse_experiment_summary_with_identity_join_v1(
        _summary(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        content_sha256=_CONTENT_SHA256,
    ).join.to_canonical_mapping()
    assert first == second


def test_named_lane_does_not_mutate_inputs() -> None:
    raw = _summary()
    snapshot = copy.deepcopy(raw)
    result = parse_experiment_summary_with_identity_join_v1(
        raw,
        experiment_identity_id=_PACKAGE_N_SHA256,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    raw["experiment_id"] = "MUTATED"
    assert result.contract.experiment_id == snapshot["experiment_id"]
    assert dict(raw) != snapshot


def test_historical_i65_row_readability_preserved() -> None:
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
    assert summary.experiment_id == _RUN_ID
    assert not hasattr(summary, "experiment_identity_id")
    interpreted = interpret_legacy_identity_row_v1(
        {"run_id": _RUN_ID, "experiment_id": _RUN_ID},
        identity_request=IdentityRequestMode.PROVENANCE,
    )
    assert interpreted.identity_canonical is False
    assert interpreted.identity_status == PlanePresence.ABSENT_DECLARED.value
    assert interpreted.run_id == _RUN_ID
    assert interpreted.legacy_experiment_id_classification == LEGACY_EXPERIMENT_ID_CLASSIFICATION
    source = EXPLORER_PATH.read_text(encoding="utf-8")
    assert 'experiment_id=str(row.get("run_id", ""))' in source
    constructed = ExperimentSummary(
        experiment_id=_RUN_ID,
        run_type="backtest",
        run_name="hist-run",
    )
    assert constructed.experiment_id == _RUN_ID


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def test_named_lane_producer_is_hooked_and_forbidden_surfaces_are_not() -> None:
    join_modules = _imported_modules(JOIN_PATH)
    assert "src.analytics.i65_explorer_join_attachment_v1" in join_modules
    assert "src.analytics.explorer" not in join_modules
    assert "src.core.experiments" not in join_modules
    explorer_modules = _imported_modules(EXPLORER_PATH)
    assert _JOIN_MODULE in explorer_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in explorer_modules
    )
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in explorer_modules
    )
    assert "src.ingress.capsules.evidence_capsule" not in explorer_modules
    assert "src.live_eval.live_session_eval" not in explorer_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in join_modules
    )
    join_source = JOIN_PATH.read_text(encoding="utf-8")
    assert "write_text" not in join_source
    assert "open(" not in join_source
    assert "Path(" not in join_source
    assert "_row_to_summary" not in join_source
    assert "get_experiment_details" not in join_source
    assert "append_experiment_record" not in join_source
    explorer_source = EXPLORER_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in explorer_source
    assert "i65_explorer_live_contract_join_v1" not in explorer_source
    assert 'experiment_id=str(row.get("run_id", ""))' in explorer_source
    init_source = INIT_PATH.read_text(encoding="utf-8")
    attachment_source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    reader_source = READER_PATH.read_text(encoding="utf-8")
    r16_source = R16_PATH.read_text(encoding="utf-8")
    experiments_source = EXPERIMENTS_PATH.read_text(encoding="utf-8")
    assert "i65_explorer_named_lane_identity_join_v1" not in init_source
    assert "i65_explorer_named_lane_identity_join_v1" not in attachment_source
    assert "i65_explorer_named_lane_identity_join_v1" not in reader_source
    assert "i65_explorer_named_lane_identity_join_v1" not in r16_source
    assert "i65_explorer_named_lane_identity_join_v1" not in experiments_source
    assert "uuid.uuid4()" in experiments_source
    assert _PACKAGE_N_SHA256 not in explorer_source
