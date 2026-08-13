"""U-I82-R2 tests for dormant historical I65 identity-row interpretation."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest

from src.analytics.legacy_identity_row_interpretation_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    IdentityRequestMode,
    LEGACY_EXPERIMENT_ID_CLASSIFICATION,
    LegacyIdentityRowInterpretationError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
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
READER_PATH = REPO_ROOT / "src" / "analytics" / "legacy_identity_row_interpretation_v1.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r2-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r2-other").hexdigest()
_MD5_12 = "abcdef012345"


def _historical_i65_row(**overrides: object) -> dict[str, object]:
    run_id = str(uuid.uuid4())
    payload: dict[str, object] = {
        "run_id": run_id,
        "run_type": "backtest",
        "run_name": "backtest_ma_crossover_hist",
        "strategy_key": "ma_crossover",
        "symbol": "BTC/EUR",
        "sharpe": 1.5,
    }
    payload.update(overrides)
    return payload


def test_historical_uuid_run_id_remains_readable() -> None:
    row = _historical_i65_row()
    parsed = interpret_legacy_identity_row_v1(row)
    assert parsed.run_id == row["run_id"]
    assert parsed.contract_id == CONTRACT_ID
    assert parsed.join_record.run_id == row["run_id"]


def test_run_id_preserved_as_run_provenance() -> None:
    row = _historical_i65_row()
    parsed = interpret_legacy_identity_row_v1(row)
    assert parsed.join_record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert parsed.run_id == row["run_id"]
    assert parsed.identity_canonical is False


def test_legacy_experiment_id_equal_run_id_is_not_package_n_sha256() -> None:
    run_id = str(uuid.uuid4())
    row = _historical_i65_row(run_id=run_id, experiment_id=run_id)
    parsed = interpret_legacy_identity_row_v1(row)
    assert parsed.legacy_experiment_id == run_id
    assert parsed.legacy_experiment_id_classification == LEGACY_EXPERIMENT_ID_CLASSIFICATION
    assert parsed.experiment_identity_id is None
    assert is_package_n_sha256_canonical_id(parsed.legacy_experiment_id) is False
    assert parsed.join_record.experiment_identity_id is None


def test_missing_package_n_identity_does_not_synthesize() -> None:
    row = _historical_i65_row()
    parsed = interpret_legacy_identity_row_v1(row)
    assert parsed.experiment_identity_id is None
    assert parsed.identity_canonical is False
    assert "experiment_identity_id" not in parsed.to_canonical_mapping()["join_record"]
    with pytest.raises(LegacyIdentityRowInterpretationError, match="IDENTITY_CANONICAL"):
        interpret_legacy_identity_row_v1(
            row, identity_request=IdentityRequestMode.IDENTITY_CANONICAL
        )


def test_absent_declared_semantics_match_r1_contract() -> None:
    row = _historical_i65_row()
    parsed = interpret_legacy_identity_row_v1(row)
    assert parsed.identity_status == PlanePresence.ABSENT_DECLARED.value
    assert parsed.join_record.plane_presence["IDENTITY"] == PlanePresence.ABSENT_DECLARED.value
    assert parsed.join_record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert parsed.join_record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert parsed.join_record.experiment_identity_id is None


def test_present_valid_package_n_sha256_is_recognized() -> None:
    row = _historical_i65_row(experiment_identity_id=_PACKAGE_N_SHA256)
    parsed = interpret_legacy_identity_row_v1(
        row, identity_request=IdentityRequestMode.IDENTITY_CANONICAL
    )
    assert parsed.identity_canonical is True
    assert parsed.experiment_identity_id == _PACKAGE_N_SHA256
    assert parsed.identity_status == PlanePresence.PRESENT.value
    assert parsed.join_record.experiment_identity_id == _PACKAGE_N_SHA256
    assert parsed.run_id == row["run_id"]
    assert parsed.join_record.plane_presence["RUN"] == PlanePresence.PRESENT.value


def test_conflicting_identity_data_fail_closed() -> None:
    run_id = str(uuid.uuid4())
    other = str(uuid.uuid4())
    row = _historical_i65_row(run_id=run_id, experiment_id=other)
    with pytest.raises(LegacyIdentityRowInterpretationError, match="conflicting identities"):
        interpret_legacy_identity_row_v1(row)

    row = _historical_i65_row()
    row["experiment_identity_id"] = row["run_id"]
    with pytest.raises(LegacyIdentityRowInterpretationError, match="not a Package-N SHA256"):
        interpret_legacy_identity_row_v1(row)

    row = {"experiment_id": _OTHER_SHA256}
    with pytest.raises(LegacyIdentityRowInterpretationError, match="must not be treated"):
        interpret_legacy_identity_row_v1(row)


def test_reader_does_not_mutate_historical_record() -> None:
    run_id = str(uuid.uuid4())
    row: dict[str, object] = _historical_i65_row(run_id=run_id, experiment_id=run_id)
    snapshot = copy.deepcopy(row)
    parsed = interpret_legacy_identity_row_v1(row)
    row["run_id"] = "MUTATED"
    row["experiment_id"] = "MUTATED"
    assert parsed.run_id == snapshot["run_id"]
    assert parsed.legacy_experiment_id == snapshot["experiment_id"]
    assert dict(parsed.historical_provenance)["run_id"] == snapshot["run_id"]
    assert row["run_id"] == "MUTATED"
    assert snapshot["run_id"] != "MUTATED"


def test_repeated_read_is_deterministic() -> None:
    run_id = str(uuid.uuid4())
    row = _historical_i65_row(run_id=run_id, experiment_id=run_id)
    first = interpret_legacy_identity_row_v1(row).to_canonical_mapping()
    second = interpret_legacy_identity_row_v1(row).to_canonical_mapping()
    third = interpret_legacy_identity_row_v1(copy.deepcopy(row)).to_canonical_mapping()
    assert first == second == third


def test_uuid_run_id_cannot_bypass_r1_sha256_validator() -> None:
    run_id = str(uuid.uuid4())
    assert is_package_n_sha256_canonical_id(run_id) is False
    row = _historical_i65_row(run_id=run_id, experiment_identity_id=run_id)
    with pytest.raises(LegacyIdentityRowInterpretationError, match="Package-N SHA256"):
        interpret_legacy_identity_row_v1(row)
    row = _historical_i65_row(experiment_identity_id=_MD5_12)
    with pytest.raises(LegacyIdentityRowInterpretationError, match="Package-N SHA256"):
        interpret_legacy_identity_row_v1(row)


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


def test_no_cap72_or_src_execution_or_writer_imports() -> None:
    modules = _imported_modules(READER_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.core.experiments" not in modules
    assert "src.analytics.explorer" not in modules
    assert "src.experiments.base" not in modules
    source = READER_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "to_csv" not in source
    assert "append_experiment_record" not in source
