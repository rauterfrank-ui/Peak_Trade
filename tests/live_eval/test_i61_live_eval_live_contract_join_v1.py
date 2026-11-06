"""U-I82-R15 tests for dormant I61 live-contract join registration."""

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
from src.ingress.capsules.i56_ingress_live_contract_join_v1 import (
    I56_LIVE_CONTRACT_REGISTERED,
    is_i56_live_contract_registered,
)
from src.levelup.i52_levelup_live_contract_join_v1 import (
    I52_LIVE_CONTRACT_REGISTERED,
    is_i52_live_contract_registered,
)
from src.live_eval.i61_live_eval_join_attachment_v1 import CONTRACT_ID as R8_CONTRACT_ID
from src.live_eval.i61_live_eval_live_contract_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I61_LIVE_CONTRACT_REGISTERED,
    I61LiveEvalLiveContractJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i61_live_contract_registered,
    register_i61_live_contract_join_v1,
)
from src.live_eval.live_session_eval import Fill, compute_metrics
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_live_contract_join_v1 import (
    I17_LIVE_CONTRACT_REGISTERED,
    is_i17_live_contract_registered,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_PATH = REPO_ROOT / "src" / "live_eval" / "i61_live_eval_live_contract_join_v1.py"
ATTACHMENT_PATH = REPO_ROOT / "src" / "live_eval" / "i61_live_eval_join_attachment_v1.py"
EVAL_PATH = REPO_ROOT / "src" / "live_eval" / "live_session_eval.py"
IO_PATH = REPO_ROOT / "src" / "live_eval" / "live_session_io.py"
INIT_PATH = REPO_ROOT / "src" / "live_eval" / "__init__.py"
CLI_PATH = REPO_ROOT / "scripts" / "evaluate_live_session.py"
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
_LIVE_CONTRACT_FILES = (EVAL_PATH, IO_PATH, INIT_PATH, ATTACHMENT_PATH, CLI_PATH)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r15-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r15-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r15-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_SESSION_ID = "live_eval_fixture_session_non_auth_v1"
_SESSION_DIR = "evidence/fixtures/live_eval/session_dir"


def _metrics() -> dict[str, object]:
    return compute_metrics([])


def _session() -> dict[str, object]:
    return {"session_dir": _SESSION_DIR}


def _envelope(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "metrics": _metrics(),
    }
    payload.update(overrides)
    return payload


def test_live_contract_registration_flag_is_reachable() -> None:
    assert CONTRACT_ID == "i61_live_eval_live_contract_join_v1"
    assert R8_CONTRACT_ID == "live_session_eval_identity_envelope_v1"
    assert I61_LIVE_CONTRACT_REGISTERED is True
    assert is_i61_live_contract_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("metrics", "session")
    assert I17_LIVE_CONTRACT_REGISTERED is True
    assert is_i17_live_contract_registered() is True
    assert I52_LIVE_CONTRACT_REGISTERED is True
    assert is_i52_live_contract_registered() is True
    assert I56_LIVE_CONTRACT_REGISTERED is True
    assert is_i56_live_contract_registered() is True


def test_canonical_package_n_sha256_present_join_from_metrics() -> None:
    record = register_i61_live_contract_join_v1(_envelope(session_id=_SESSION_ID))
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True
    assert record.session_id == _SESSION_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _SESSION_ID


def test_declared_absence_for_alias_run_campaign_evidence_content_hash() -> None:
    record = register_i61_live_contract_join_v1(_envelope())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.run_id is None
    assert record.campaign_id is None
    assert record.session_id is None
    assert record.content_sha256 is None


def test_session_dir_surface_does_not_populate_session_plane() -> None:
    record = register_i61_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "session": _session(),
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.session_id is None
    assert record.experiment_identity_id != _SESSION_DIR


def test_explicit_content_sha256_is_content_hash_not_identity() -> None:
    record = register_i61_live_contract_join_v1(_envelope(content_sha256=_CONTENT_SHA256))
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _CONTENT_SHA256
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_prior_i61_metrics_still_compute_from_fills() -> None:
    fill = Fill(
        ts=datetime(2026, 1, 1, tzinfo=timezone.utc),
        symbol="ETH-USD",
        side="buy",
        qty=1.0,
        fill_price=100.0,
    )
    metrics = compute_metrics([fill])
    assert metrics["total_fills"] == 1
    record = register_i61_live_contract_join_v1(
        {"experiment_identity_id": _PACKAGE_N_SHA256, "metrics": metrics}
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="implicit absence rejected"):
        register_i61_live_contract_join_v1({"metrics": _metrics()})


def test_implicit_absence_of_live_surface_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="implicit absence rejected"):
        register_i61_live_contract_join_v1({"experiment_identity_id": _PACKAGE_N_SHA256})


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="noncanonical ID substitution"):
        register_i61_live_contract_join_v1(_envelope(experiment_identity_id=_RUN_ID))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="noncanonical ID substitution"):
        register_i61_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_12))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="noncanonical ID substitution"):
        register_i61_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_32))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="noncanonical ID substitution"):
        register_i61_live_contract_join_v1(_envelope(experiment_identity_id=_SESSION_DIR))


def test_legacy_experiment_id_on_envelope_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="noncanonical ID substitution"):
        register_i61_live_contract_join_v1(_envelope(experiment_id=_RUN_ID))


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="conflicting"):
        register_i61_live_contract_join_v1(
            _envelope(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="conflicting"):
        register_i61_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "session": _session(),
                "session_dir": "evidence/fixtures/live_eval/other_session",
            }
        )


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="ambiguous join rejected"):
        register_i61_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "metrics": _metrics(),
                "session": _session(),
            }
        )
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="ambiguous join rejected"):
        register_i61_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "metrics": [_metrics(), copy.deepcopy(_metrics())],
            }
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="malformed plane data"):
        register_i61_live_contract_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="malformed plane data"):
        register_i61_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "metrics": "bad"}
        )
    mutated = _metrics()
    mutated.pop("total_fills")
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="malformed plane data"):
        register_i61_live_contract_join_v1(_envelope(metrics=mutated))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="malformed plane data"):
        register_i61_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "session": {"session_dir": "nopath"}}
        )


def test_cross_plane_substitution_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="cross-plane substitution"):
        register_i61_live_contract_join_v1(_envelope(plane_presence={"IDENTITY": "PRESENT"}))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="cross-plane substitution"):
        register_i61_live_contract_join_v1(_envelope(fill_price=50000.0))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="cross-plane substitution"):
        register_i61_live_contract_join_v1(_envelope(fills=[]))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="cross-plane substitution"):
        register_i61_live_contract_join_v1(_envelope(session_id=_PACKAGE_N_SHA256))
    live = _metrics()
    live["fill_price"] = 50000.0
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="cross-plane substitution"):
        register_i61_live_contract_join_v1(_envelope(metrics=live))


def test_cross_lane_substitution_rejected() -> None:
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="cross-lane substitution"):
        register_i61_live_contract_join_v1(_envelope(I65={"experiment_id": _RUN_ID}))
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="malformed plane data"):
        register_i61_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "metrics": {
                    "capsule_id": "default.capsule",
                    "run_id": "default",
                    "ts_ms": 1000,
                },
            }
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _metrics()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I61LiveEvalLiveContractJoinError, match="noncanonical ID substitution"):
        register_i61_live_contract_join_v1(_envelope(metrics=live))


def test_join_is_deterministic() -> None:
    payload = _envelope(content_sha256=_CONTENT_SHA256, session_id=_SESSION_ID)
    first = register_i61_live_contract_join_v1(payload).to_canonical_mapping()
    second = register_i61_live_contract_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_registration_does_not_mutate_inputs() -> None:
    payload = _envelope(historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID})
    snapshot = copy.deepcopy(payload)
    record = register_i61_live_contract_join_v1(payload)
    payload["experiment_identity_id"] = "MUTATED"
    payload["metrics"]["total_fills"] = 99  # type: ignore[index]
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert record.experiment_identity_id == snapshot["experiment_identity_id"]
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    payload = _envelope(
        run_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    record = register_i61_live_contract_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert record.run_id == _RUN_ID
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID


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


def test_no_cap72_execution_hook_or_persistence() -> None:
    modules = _imported_modules(REGISTRATION_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.experiments.base" not in modules
    assert "src.live_eval.live_session_io" not in modules
    assert "src.live_eval.live_session_eval" not in modules
    assert "src.analytics.explorer" not in modules
    assert "src.live_eval.i61_live_eval_join_attachment_v1" in modules
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_text" not in source
    assert "Path(" not in source
    assert "compute_metrics" not in source
    assert "read_fills_csv" not in source
    assert "class Fill" not in source


def test_live_contracts_and_prior_registrations_remain_unhooked() -> None:
    for path in _LIVE_CONTRACT_FILES:
        source = path.read_text(encoding="utf-8")
        assert "register_i61_live_contract_join_v1" not in source
        assert "i61_live_eval_live_contract_join_v1" not in source
    eval_src = EVAL_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in eval_src
    assert "class Fill:" in eval_src
    for prior in (I17_REGISTRATION_PATH, I52_REGISTRATION_PATH, I56_REGISTRATION_PATH):
        source = prior.read_text(encoding="utf-8")
        assert "i61_live_eval_live_contract_join_v1" not in source
        assert "I61_LIVE_CONTRACT_REGISTERED = True" not in source
