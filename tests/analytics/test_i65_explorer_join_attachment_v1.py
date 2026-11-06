"""U-I82-R9 tests for dormant I65 explorer join attachment."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest

from src.analytics.explorer import ExperimentSummary
from src.analytics.i65_explorer_join_attachment_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I65ExplorerJoinAttachmentError,
    LEGACY_EXPERIMENT_ID_CLASSIFICATION,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    attach_i65_explorer_join_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACHMENT_PATH = REPO_ROOT / "src" / "analytics" / "i65_explorer_join_attachment_v1.py"
EXPLORER_PATH = REPO_ROOT / "src" / "analytics" / "explorer.py"
EXPERIMENTS_PATH = REPO_ROOT / "src" / "core" / "experiments.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r9-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r9-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r9-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())


def _i65_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "run_id": _RUN_ID,
    }
    payload.update(overrides)
    return payload


def test_canonical_package_n_sha256_happy_path() -> None:
    record = attach_i65_explorer_join_v1(_i65_payload())
    assert CONTRACT_ID == "i65_explorer_join_attachment_v1"
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.run_id == _RUN_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _RUN_ID
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True


def test_alias_campaign_session_absent_declared_by_default() -> None:
    record = attach_i65_explorer_join_v1(_i65_payload())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.campaign_id is None
    assert record.session_id is None


def test_declared_absent_without_run_id() -> None:
    record = attach_i65_explorer_join_v1({"experiment_identity_id": _PACKAGE_N_SHA256})
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.run_id is None
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value


def test_legacy_experiment_id_is_run_provenance_alias_not_identity() -> None:
    record = attach_i65_explorer_join_v1(_i65_payload(experiment_id=_RUN_ID))
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.run_id == _RUN_ID
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert (
        dict(record.historical_provenance)["legacy_experiment_id_classification"]
        == LEGACY_EXPERIMENT_ID_CLASSIFICATION
    )
    assert record.experiment_identity_id != _RUN_ID


def test_explicit_content_sha256_is_content_hash_not_identity() -> None:
    record = attach_i65_explorer_join_v1(_i65_payload(content_sha256=_CONTENT_SHA256))
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _CONTENT_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I65ExplorerJoinAttachmentError, match="IDENTITY missing"):
        attach_i65_explorer_join_v1({"run_id": _RUN_ID, "experiment_id": _RUN_ID})


def test_uuid_run_id_as_identity_rejected() -> None:
    assert is_package_n_sha256_canonical_id(_RUN_ID) is False
    with pytest.raises(I65ExplorerJoinAttachmentError, match="Package-N SHA256"):
        attach_i65_explorer_join_v1(_i65_payload(experiment_identity_id=_RUN_ID))


def test_legacy_experiment_id_as_identity_rejected() -> None:
    with pytest.raises(I65ExplorerJoinAttachmentError, match="Package-N SHA256"):
        attach_i65_explorer_join_v1(
            _i65_payload(experiment_identity_id=_RUN_ID, experiment_id=_RUN_ID)
        )


def test_md5_as_identity_rejected() -> None:
    with pytest.raises(I65ExplorerJoinAttachmentError, match="Package-N SHA256"):
        attach_i65_explorer_join_v1(_i65_payload(experiment_identity_id=_MD5_12))
    with pytest.raises(I65ExplorerJoinAttachmentError, match="Package-N SHA256"):
        attach_i65_explorer_join_v1(_i65_payload(experiment_identity_id=_MD5_32))


def test_run_id_must_not_substitute_identity() -> None:
    with pytest.raises(
        I65ExplorerJoinAttachmentError,
        match="must not substitute|equals run_id|field separation rejected",
    ):
        attach_i65_explorer_join_v1(_i65_payload(run_id=_PACKAGE_N_SHA256))


def test_legacy_experiment_id_must_not_substitute_identity() -> None:
    with pytest.raises(I65ExplorerJoinAttachmentError, match="field separation rejected"):
        attach_i65_explorer_join_v1(_i65_payload(experiment_id=_PACKAGE_N_SHA256))


def test_registry_and_mlflow_ids_cannot_replace_identity() -> None:
    with pytest.raises(I65ExplorerJoinAttachmentError, match="forbidden I65 join field"):
        attach_i65_explorer_join_v1(_i65_payload(registry_run_id=_RUN_ID))
    with pytest.raises(I65ExplorerJoinAttachmentError, match="forbidden I65 join field"):
        attach_i65_explorer_join_v1(_i65_payload(mlflow_run_id=_RUN_ID))
    with pytest.raises(I65ExplorerJoinAttachmentError, match="forbidden I65 join field"):
        attach_i65_explorer_join_v1(_i65_payload(git_sha="abc123"))


def test_conflicting_identity_values_rejected() -> None:
    with pytest.raises(I65ExplorerJoinAttachmentError, match="forbidden I65 join field"):
        attach_i65_explorer_join_v1(_i65_payload(ref_id=_OTHER_SHA256))
    with pytest.raises(I65ExplorerJoinAttachmentError, match="conflicting identities"):
        attach_i65_explorer_join_v1(
            _i65_payload(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )


def test_legacy_experiment_id_run_id_conflation_rejected() -> None:
    other_uuid = str(uuid.uuid4())
    with pytest.raises(I65ExplorerJoinAttachmentError, match="field separation rejected"):
        attach_i65_explorer_join_v1(_i65_payload(experiment_id=other_uuid, run_id=_RUN_ID))


def test_malformed_and_ambiguous_join_rejected() -> None:
    with pytest.raises(I65ExplorerJoinAttachmentError, match="must be an object"):
        attach_i65_explorer_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I65ExplorerJoinAttachmentError, match="unknown I65 join field"):
        attach_i65_explorer_join_v1(_i65_payload(authorization_id="not-in-i65-join"))
    with pytest.raises(I65ExplorerJoinAttachmentError, match="empty or whitespace-padded"):
        attach_i65_explorer_join_v1(_i65_payload(experiment_identity_id="   "))
    with pytest.raises(I65ExplorerJoinAttachmentError, match="must be a string when present"):
        attach_i65_explorer_join_v1(_i65_payload(run_id=123))


def test_join_is_deterministic() -> None:
    payload = _i65_payload(experiment_id=_RUN_ID, content_sha256=_CONTENT_SHA256)
    first = attach_i65_explorer_join_v1(payload).to_canonical_mapping()
    second = attach_i65_explorer_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_attachment_does_not_mutate_inputs() -> None:
    payload = _i65_payload(
        experiment_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID},
    )
    snapshot = copy.deepcopy(payload)
    record = attach_i65_explorer_join_v1(payload)
    payload["run_id"] = "MUTATED"
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert record.run_id == _RUN_ID
    assert payload != snapshot


def test_historical_provenance_non_authoritative() -> None:
    payload = _i65_payload(
        experiment_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID},
    )
    record = attach_i65_explorer_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert (
        dict(record.historical_provenance)["legacy_experiment_id_classification"]
        == LEGACY_EXPERIMENT_ID_CLASSIFICATION
    )


def test_live_explorer_contract_unregistered() -> None:
    summary = ExperimentSummary(
        experiment_id=_RUN_ID,
        run_type="backtest",
        run_name="hist",
    )
    assert summary.experiment_id == _RUN_ID
    assert not hasattr(summary, "experiment_identity_id")
    source = EXPLORER_PATH.read_text(encoding="utf-8")
    assert 'experiment_id=str(row.get("run_id", ""))' in source
    assert "uuid.uuid4()" in EXPERIMENTS_PATH.read_text(encoding="utf-8")


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
    assert "src.analytics.explorer" not in modules
    assert "src.core.experiments" not in modules
    assert "src.analytics.legacy_identity_row_interpretation_v1" in modules
    source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "_row_to_summary" not in source
    assert "get_experiment_details" not in source
    assert "uuid.uuid4()" not in source
    explorer_source = EXPLORER_PATH.read_text(encoding="utf-8")
    assert "attach_i65_explorer_join_v1" not in explorer_source
