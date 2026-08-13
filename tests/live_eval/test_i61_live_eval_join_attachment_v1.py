"""U-I82-R8 tests for dormant I61 live-eval identity envelope."""

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
from src.live_eval.i61_live_eval_join_attachment_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I61LiveEvalJoinAttachmentError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    attach_i61_live_eval_join_v1,
)
from src.live_eval.live_session_eval import Fill, compute_metrics
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACHMENT_PATH = REPO_ROOT / "src" / "live_eval" / "i61_live_eval_join_attachment_v1.py"
FILL_PATH = REPO_ROOT / "src" / "live_eval" / "live_session_eval.py"
CLI_PATH = REPO_ROOT / "scripts" / "evaluate_live_session.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r8-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r8-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r8-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_SESSION_ID = "live_eval_fixture_session_non_auth_v1"
_SESSION_DIR = "evidence/fixtures/live_eval/session_dir"


def _i61_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "session_id": _SESSION_ID,
    }
    payload.update(overrides)
    return payload


def test_canonical_package_n_sha256_happy_path() -> None:
    record = attach_i61_live_eval_join_v1(_i61_payload())
    assert CONTRACT_ID == "live_session_eval_identity_envelope_v1"
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.session_id == _SESSION_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _SESSION_ID
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True


def test_alias_run_campaign_absent_declared_by_default() -> None:
    record = attach_i61_live_eval_join_v1(_i61_payload())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.run_id is None
    assert record.campaign_id is None


def test_session_dir_hint_does_not_populate_session_plane() -> None:
    payload = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "session_dir": _SESSION_DIR,
    }
    record = attach_i61_live_eval_join_v1(payload)
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.session_id is None
    assert record.experiment_identity_id != _SESSION_DIR


def test_explicit_content_sha256_is_content_hash_not_identity() -> None:
    record = attach_i61_live_eval_join_v1(_i61_payload(content_sha256=_CONTENT_SHA256))
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _CONTENT_SHA256
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="IDENTITY missing"):
        attach_i61_live_eval_join_v1({"session_id": _SESSION_ID, "session_dir": _SESSION_DIR})


def test_session_dir_path_as_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="session-dir path is not identity"):
        attach_i61_live_eval_join_v1(
            _i61_payload(experiment_identity_id=_SESSION_DIR, session_dir=_SESSION_DIR)
        )


def test_session_dir_path_as_session_id_rejected() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="session-dir path is not session_id"):
        attach_i61_live_eval_join_v1(
            _i61_payload(session_id=_SESSION_DIR, session_dir=_SESSION_DIR)
        )


def test_uuid_run_id_as_identity_rejected() -> None:
    assert is_package_n_sha256_canonical_id(_RUN_ID) is False
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="Package-N SHA256"):
        attach_i61_live_eval_join_v1(_i61_payload(experiment_identity_id=_RUN_ID, run_id=_RUN_ID))


def test_legacy_experiment_id_as_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="forbidden I61 join field"):
        attach_i61_live_eval_join_v1(_i61_payload(experiment_id=_RUN_ID))


def test_md5_as_identity_rejected() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="Package-N SHA256"):
        attach_i61_live_eval_join_v1(_i61_payload(experiment_identity_id=_MD5_12))
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="Package-N SHA256"):
        attach_i61_live_eval_join_v1(_i61_payload(experiment_identity_id=_MD5_32))


def test_session_id_must_not_substitute_identity() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="must not substitute"):
        attach_i61_live_eval_join_v1(_i61_payload(session_id=_PACKAGE_N_SHA256))


def test_run_id_must_not_substitute_identity() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="must not substitute"):
        attach_i61_live_eval_join_v1(_i61_payload(run_id=_PACKAGE_N_SHA256))


def test_fill_fields_rejected_from_envelope() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="forbidden I61 join field"):
        attach_i61_live_eval_join_v1(_i61_payload(fill_price=50000.0))
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="forbidden I61 join field"):
        attach_i61_live_eval_join_v1(_i61_payload(fills=[]))


def test_conflicting_identity_values_rejected() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="forbidden I61 join field"):
        attach_i61_live_eval_join_v1(_i61_payload(ref_id=_OTHER_SHA256))
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="conflicting identities"):
        attach_i61_live_eval_join_v1(
            _i61_payload(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )


def test_malformed_and_ambiguous_join_rejected() -> None:
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="must be an object"):
        attach_i61_live_eval_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="unknown I61 join field"):
        attach_i61_live_eval_join_v1(_i61_payload(authorization_id="not-in-i61-envelope"))
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="empty or whitespace-padded"):
        attach_i61_live_eval_join_v1(_i61_payload(experiment_identity_id="   "))
    with pytest.raises(I61LiveEvalJoinAttachmentError, match="must be a string when present"):
        attach_i61_live_eval_join_v1(_i61_payload(session_id=123))


def test_join_is_deterministic() -> None:
    payload = _i61_payload(content_sha256=_CONTENT_SHA256, run_id=_RUN_ID)
    first = attach_i61_live_eval_join_v1(payload).to_canonical_mapping()
    second = attach_i61_live_eval_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_attachment_does_not_mutate_inputs() -> None:
    payload = _i61_payload(
        historical_provenance={"legacy_session_id": _SESSION_ID, "session_dir": _SESSION_DIR}
    )
    snapshot = copy.deepcopy(payload)
    record = attach_i61_live_eval_join_v1(payload)
    payload["session_id"] = "MUTATED"
    payload["historical_provenance"]["legacy_session_id"] = "MUTATED"  # type: ignore[index]
    assert dict(record.historical_provenance)["legacy_session_id"] == _SESSION_ID
    assert dict(record.historical_provenance)["session_dir"] == _SESSION_DIR
    assert payload != snapshot


def test_historical_provenance_non_authoritative() -> None:
    payload = _i61_payload(
        historical_provenance={"legacy_session_id": _SESSION_ID, "session_dir": _SESSION_DIR}
    )
    record = attach_i61_live_eval_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _SESSION_ID
    assert record.experiment_identity_id != _SESSION_DIR
    assert dict(record.historical_provenance)["session_dir"] == _SESSION_DIR


def test_fill_only_eval_remains_non_join_and_metrics_still_compute() -> None:
    fill = Fill(
        ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        symbol="BTC/USD",
        side="buy",
        qty=0.1,
        fill_price=50000.0,
    )
    metrics = compute_metrics([fill])
    assert metrics["total_fills"] == 1
    assert "experiment_identity_id" not in metrics
    assert set(fill.__dataclass_fields__) == {"ts", "symbol", "side", "qty", "fill_price"}
    source = FILL_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in source


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


def test_no_runtime_registration_or_forbidden_imports() -> None:
    modules = _imported_modules(ATTACHMENT_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.live_eval.live_session_eval" not in modules
    assert "src.live_eval.live_session_io" not in modules
    assert "src.experiments.base" not in modules
    assert not any("evaluate_live_session" in mod for mod in modules)
    source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "compute_metrics" not in source
    assert "read_fills_csv" not in source
    cli_source = CLI_PATH.read_text(encoding="utf-8")
    assert "attach_i61_live_eval_join_v1" not in cli_source
    assert "experiment_identity_id" not in cli_source
