"""U-I82-R16 tests for dormant I65 live-contract join registration."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest

from src.analytics.explorer import ExperimentSummary
from src.analytics.i65_explorer_join_attachment_v1 import CONTRACT_ID as R9_CONTRACT_ID
from src.analytics.i65_explorer_live_contract_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I65_LIVE_CONTRACT_REGISTERED,
    I65ExplorerLiveContractJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i65_live_contract_registered,
    register_i65_live_contract_join_v1,
)
from src.analytics.legacy_identity_row_interpretation_v1 import (
    LEGACY_EXPERIMENT_ID_CLASSIFICATION,
    interpret_legacy_identity_row_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.ingress.capsules.i56_ingress_live_contract_join_v1 import (
    I56_LIVE_CONTRACT_REGISTERED,
    is_i56_live_contract_registered,
)
from src.levelup.i52_levelup_live_contract_join_v1 import (
    I52_LIVE_CONTRACT_REGISTERED,
    is_i52_live_contract_registered,
)
from src.live_eval.i61_live_eval_live_contract_join_v1 import (
    I61_LIVE_CONTRACT_REGISTERED,
    is_i61_live_contract_registered,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_live_contract_join_v1 import (
    I17_LIVE_CONTRACT_REGISTERED,
    is_i17_live_contract_registered,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_PATH = REPO_ROOT / "src" / "analytics" / "i65_explorer_live_contract_join_v1.py"
ATTACHMENT_PATH = REPO_ROOT / "src" / "analytics" / "i65_explorer_join_attachment_v1.py"
READER_PATH = REPO_ROOT / "src" / "analytics" / "legacy_identity_row_interpretation_v1.py"
EXPLORER_PATH = REPO_ROOT / "src" / "analytics" / "explorer.py"
INIT_PATH = REPO_ROOT / "src" / "analytics" / "__init__.py"
EXPERIMENTS_PATH = REPO_ROOT / "src" / "core" / "experiments.py"
I17_REGISTRATION_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_live_contract_join_v1.py"
)
I52_REGISTRATION_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_live_contract_join_v1.py"
I56_REGISTRATION_PATH = (
    REPO_ROOT / "src" / "ingress" / "capsules" / "i56_ingress_live_contract_join_v1.py"
)
I61_REGISTRATION_PATH = REPO_ROOT / "src" / "live_eval" / "i61_live_eval_live_contract_join_v1.py"
_LIVE_CONTRACT_FILES = (EXPLORER_PATH, INIT_PATH, ATTACHMENT_PATH, READER_PATH, EXPERIMENTS_PATH)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r16-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r16-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r16-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())


def _summary(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_id": _RUN_ID,
        "run_type": "backtest",
        "run_name": "backtest_ma_crossover_r16",
    }
    payload.update(overrides)
    return payload


def _row(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "run_id": _RUN_ID,
        "run_type": "backtest",
        "run_name": "backtest_ma_crossover_hist",
        "strategy_key": "ma_crossover",
        "symbol": "BTC/EUR",
        "sharpe": 1.5,
    }
    payload.update(overrides)
    return payload


def _envelope(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "summary": _summary(),
    }
    payload.update(overrides)
    return payload


def test_live_contract_registration_flag_is_reachable() -> None:
    assert CONTRACT_ID == "i65_explorer_live_contract_join_v1"
    assert R9_CONTRACT_ID == "i65_explorer_join_attachment_v1"
    assert I65_LIVE_CONTRACT_REGISTERED is True
    assert is_i65_live_contract_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("summary", "row")
    assert I17_LIVE_CONTRACT_REGISTERED is True
    assert is_i17_live_contract_registered() is True
    assert I52_LIVE_CONTRACT_REGISTERED is True
    assert is_i52_live_contract_registered() is True
    assert I56_LIVE_CONTRACT_REGISTERED is True
    assert is_i56_live_contract_registered() is True
    assert I61_LIVE_CONTRACT_REGISTERED is True
    assert is_i61_live_contract_registered() is True


def test_canonical_package_n_sha256_present_join_from_summary() -> None:
    record = register_i65_live_contract_join_v1(_envelope())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True
    assert record.run_id == _RUN_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _RUN_ID


def test_declared_absence_for_alias_campaign_session_evidence_content_hash() -> None:
    record = register_i65_live_contract_join_v1(_envelope())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.campaign_id is None
    assert record.session_id is None
    assert record.content_sha256 is None


def test_row_surface_joins_without_rewriting_historical_record() -> None:
    historical = _row(experiment_id=_RUN_ID)
    snapshot = copy.deepcopy(historical)
    record = register_i65_live_contract_join_v1(
        {"experiment_identity_id": _PACKAGE_N_SHA256, "row": historical}
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.run_id == _RUN_ID
    assert historical == snapshot
    parsed = interpret_legacy_identity_row_v1(historical)
    assert parsed.run_id == _RUN_ID
    assert parsed.legacy_experiment_id == _RUN_ID
    assert parsed.experiment_identity_id is None
    assert parsed.identity_canonical is False


def test_explicit_content_sha256_is_content_hash_not_identity() -> None:
    record = register_i65_live_contract_join_v1(_envelope(content_sha256=_CONTENT_SHA256))
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _CONTENT_SHA256
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_live_experiment_summary_remains_identity_free() -> None:
    summary = ExperimentSummary(
        experiment_id=_RUN_ID,
        run_type="backtest",
        run_name="hist",
    )
    assert summary.experiment_id == _RUN_ID
    assert not hasattr(summary, "experiment_identity_id")
    record = register_i65_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "summary": {
                "experiment_id": summary.experiment_id,
                "run_type": summary.run_type,
                "run_name": summary.run_name,
            },
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert summary.experiment_id == _RUN_ID


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="implicit absence rejected"):
        register_i65_live_contract_join_v1({"summary": _summary()})


def test_implicit_absence_of_live_surface_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="implicit absence rejected"):
        register_i65_live_contract_join_v1({"experiment_identity_id": _PACKAGE_N_SHA256})
    with pytest.raises(I65ExplorerLiveContractJoinError, match="implicit absence rejected"):
        register_i65_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "row": {"run_type": "backtest"}}
        )


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="noncanonical ID substitution"):
        register_i65_live_contract_join_v1(_envelope(experiment_identity_id=_RUN_ID))
    with pytest.raises(I65ExplorerLiveContractJoinError, match="noncanonical ID substitution"):
        register_i65_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_12))
    with pytest.raises(I65ExplorerLiveContractJoinError, match="noncanonical ID substitution"):
        register_i65_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_32))
    with pytest.raises(I65ExplorerLiveContractJoinError, match="noncanonical ID substitution"):
        register_i65_live_contract_join_v1(
            _envelope(summary=_summary(experiment_id=_PACKAGE_N_SHA256))
        )


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="conflicting"):
        register_i65_live_contract_join_v1(
            _envelope(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )
    with pytest.raises(I65ExplorerLiveContractJoinError, match="conflicting"):
        register_i65_live_contract_join_v1(_envelope(run_id=str(uuid.uuid4())))
    with pytest.raises(I65ExplorerLiveContractJoinError, match="conflicting"):
        register_i65_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "row": _row(experiment_id=str(uuid.uuid4())),
            }
        )


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="ambiguous join rejected"):
        register_i65_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "summary": _summary(),
                "row": _row(),
            }
        )
    with pytest.raises(I65ExplorerLiveContractJoinError, match="ambiguous join rejected"):
        register_i65_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "summary": [_summary(), copy.deepcopy(_summary())],
            }
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="malformed plane data"):
        register_i65_live_contract_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I65ExplorerLiveContractJoinError, match="malformed plane data"):
        register_i65_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "summary": "bad"}
        )
    mutated = _summary()
    mutated.pop("run_name")
    with pytest.raises(I65ExplorerLiveContractJoinError, match="malformed plane data"):
        register_i65_live_contract_join_v1(_envelope(summary=mutated))


def test_cross_plane_substitution_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="cross-plane substitution"):
        register_i65_live_contract_join_v1(_envelope(plane_presence={"IDENTITY": "PRESENT"}))
    with pytest.raises(I65ExplorerLiveContractJoinError, match="cross-plane substitution"):
        register_i65_live_contract_join_v1(_envelope(fill_price=50000.0))
    live = _summary()
    live["total_fills"] = 1
    with pytest.raises(I65ExplorerLiveContractJoinError, match="cross-plane substitution"):
        register_i65_live_contract_join_v1(_envelope(summary=live))
    with pytest.raises(I65ExplorerLiveContractJoinError, match="cross-plane substitution"):
        register_i65_live_contract_join_v1(_envelope(session_id=_PACKAGE_N_SHA256))


def test_cross_lane_substitution_rejected() -> None:
    with pytest.raises(I65ExplorerLiveContractJoinError, match="cross-lane substitution"):
        register_i65_live_contract_join_v1(_envelope(I61={"metrics": {}}))
    with pytest.raises(I65ExplorerLiveContractJoinError, match="malformed plane data"):
        register_i65_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "summary": {
                    "run_id": "default",
                    "ts_ms": 1000,
                },
            }
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _summary()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I65ExplorerLiveContractJoinError, match="noncanonical ID substitution"):
        register_i65_live_contract_join_v1(_envelope(summary=live))


def test_join_is_deterministic() -> None:
    payload = _envelope(content_sha256=_CONTENT_SHA256)
    first = register_i65_live_contract_join_v1(payload).to_canonical_mapping()
    second = register_i65_live_contract_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_registration_does_not_mutate_inputs() -> None:
    payload = _envelope(historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID})
    snapshot = copy.deepcopy(payload)
    record = register_i65_live_contract_join_v1(payload)
    payload["experiment_identity_id"] = "MUTATED"
    payload["summary"]["experiment_id"] = "MUTATED"  # type: ignore[index]
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert record.experiment_identity_id == snapshot["experiment_identity_id"]
    assert record.run_id == _RUN_ID
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    payload = _envelope()
    record = register_i65_live_contract_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert record.run_id == _RUN_ID
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert (
        dict(record.historical_provenance)["legacy_experiment_id_classification"]
        == LEGACY_EXPERIMENT_ID_CLASSIFICATION
    )
    assert is_package_n_sha256_canonical_id(record.run_id) is False


def test_no_synthetic_package_n_identity() -> None:
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "hashlib" not in source
    assert "uuid.uuid4" not in source
    assert "sha256(" not in source


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_no_cap72_execution_explorer_or_persistence_hook() -> None:
    modules = _imported_modules(REGISTRATION_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.analytics.explorer" not in modules
    assert "src.core.experiments" not in modules
    assert "src.analytics.i65_explorer_join_attachment_v1" in modules
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_text" not in source
    assert "Path(" not in source
    assert "_row_to_summary" not in source
    assert "get_experiment_details" not in source
    assert "append_experiment_record" not in source


def test_live_contracts_and_prior_registrations_remain_unhooked() -> None:
    for path in _LIVE_CONTRACT_FILES:
        source = path.read_text(encoding="utf-8")
        assert "register_i65_live_contract_join_v1" not in source
        assert "i65_explorer_live_contract_join_v1" not in source
    explorer_src = EXPLORER_PATH.read_text(encoding="utf-8")
    assert 'experiment_id=str(row.get("run_id", ""))' in explorer_src
    assert "uuid.uuid4()" in EXPERIMENTS_PATH.read_text(encoding="utf-8")
    for prior in (
        I17_REGISTRATION_PATH,
        I52_REGISTRATION_PATH,
        I56_REGISTRATION_PATH,
        I61_REGISTRATION_PATH,
    ):
        source = prior.read_text(encoding="utf-8")
        assert "i65_explorer_live_contract_join_v1" not in source
        assert "I65_LIVE_CONTRACT_REGISTERED = True" not in source
