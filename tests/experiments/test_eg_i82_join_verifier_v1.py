"""U-I82-R11 tests for dormant EG-I82 cross-lane join verifier."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest

from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.cross_lane_identity_join_record_v1 import (
    build_cross_lane_identity_join_record_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    CONTRACT_VERSION,
    JOIN_PLANES,
    PlanePresence,
    is_package_n_sha256_canonical_id,
    validate_cross_lane_identity_join_v1,
)
from src.experiments.eg_i82_join_verifier_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    EG_I82_CROSS_LANE_VERIFIER_REGISTERED,
    EgI82JoinVerifierError,
    LANE_DORMANT_CONTRACT_IDS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NAMED_JOIN_LANES,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_eg_i82_cross_lane_verifier_registered,
    verify_eg_i82_cross_lane_join_v1,
)
from src.experiments.experiment_identity_manifest_v1 import build_manifest
from src.experiments.i16_package_n_join_emission_v1 import (
    emit_i16_package_n_join_from_producer_v1,
    emit_i16_package_n_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER_PATH = REPO_ROOT / "src" / "experiments" / "eg_i82_join_verifier_v1.py"
I16_EMISSION_PATH = REPO_ROOT / "src" / "experiments" / "i16_package_n_join_emission_v1.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r11-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r11-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r11-content").hexdigest()
_MD5_12 = "abcdef012345"
_RUN_ID = str(uuid.uuid4())
_LIVE_CONTRACT_MODULES = (
    "src.ingress.capsules.evidence_capsule",
    "src.levelup.v0_models",
    "src.live_eval.live_session_eval",
    "src.analytics.explorer",
    "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1",
    "src.core.experiments",
)
_DORMANT_ATTACHMENT_MODULES = (
    "src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1",
    "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_join_attachment_v1",
    "src.levelup.i52_levelup_join_attachment_v1",
    "src.ingress.capsules.i56_ingress_join_attachment_v1",
    "src.live_eval.i61_live_eval_join_attachment_v1",
    "src.analytics.i65_explorer_join_attachment_v1",
    "src.experiments.i16_package_n_join_emission_v1",
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


def _absent(plane: str) -> dict[str, str]:
    return {"plane": plane, "presence": PlanePresence.ABSENT_DECLARED.value}


def _present(plane: str, value: str, join_key: str = _PACKAGE_N_SHA256) -> dict[str, str]:
    return {
        "plane": plane,
        "presence": PlanePresence.PRESENT.value,
        "join_key": join_key,
        "value": value,
    }


def _complete(*overrides: dict[str, str]) -> list[dict[str, str]]:
    by_plane = {plane: _absent(plane) for plane in JOIN_PLANES}
    for item in overrides:
        by_plane[item["plane"]] = item
    return [by_plane[plane] for plane in JOIN_PLANES]


def _absent_record():
    return build_cross_lane_identity_join_record_v1(_complete())


def _identity_record(
    identity: str = _PACKAGE_N_SHA256,
    *,
    run_id: str | None = None,
    content_sha256: str | None = None,
    session_id: str | None = None,
    historical_provenance: dict[str, str] | None = None,
):
    overrides = [_present("IDENTITY", identity, join_key=identity)]
    if run_id is not None:
        overrides.append(_present("RUN", run_id, join_key=identity))
    if content_sha256 is not None:
        overrides.append(_present("CONTENT_HASH", content_sha256, join_key=identity))
    if session_id is not None:
        overrides.append(_present("SESSION", session_id, join_key=identity))
    return build_cross_lane_identity_join_record_v1(
        _complete(*overrides),
        package_n_identity_id=identity,
        historical_provenance=historical_provenance,
    )


def _lanes(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {lane: _absent_record() for lane in NAMED_JOIN_LANES}
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


def test_verifier_is_registered_and_reachable() -> None:
    assert CONTRACT_ID == "eg_i82_join_verifier_v1"
    assert EG_I82_CROSS_LANE_VERIFIER_REGISTERED is True
    assert is_eg_i82_cross_lane_verifier_registered() is True
    assert NAMED_JOIN_LANES == ("I16", "I17", "I52", "I56", "I61", "I65")
    assert LANE_DORMANT_CONTRACT_IDS["I16"] == "i16_package_n_join_emission_v1"
    result = verify_eg_i82_cross_lane_join_v1(_lanes())
    assert result.verifier_registered is True
    assert result.contract_id == CONTRACT_ID


def test_i16_producer_emission_reaches_join_path() -> None:
    config = _sample_config()
    emitted = emit_i16_package_n_join_from_producer_v1(config)
    result = verify_eg_i82_cross_lane_join_v1(_lanes(I16=emitted))
    assert result.package_n_sha256 == emitted.experiment_identity_id
    assert is_package_n_sha256_canonical_id(result.package_n_sha256) is True
    assert result.lane_identity_presence["I16"] == PlanePresence.PRESENT.value
    again = emit_i16_package_n_join_v1(build_manifest(config))
    assert again.experiment_identity_id == result.package_n_sha256


def test_identical_canonical_identities_across_lanes_accepted() -> None:
    result = verify_eg_i82_cross_lane_join_v1(
        _lanes(
            I16=_identity_record(),
            I17=_identity_record(),
            I52=_identity_record(),
        )
    )
    assert result.package_n_sha256 == _PACKAGE_N_SHA256
    assert result.lane_identity_presence["I16"] == PlanePresence.PRESENT.value
    assert result.lane_identity_presence["I17"] == PlanePresence.PRESENT.value
    assert result.lane_identity_presence["I65"] == PlanePresence.ABSENT_DECLARED.value


def test_declared_absence_supported() -> None:
    result = verify_eg_i82_cross_lane_join_v1(_lanes())
    assert result.package_n_sha256 is None
    for lane in NAMED_JOIN_LANES:
        assert result.lane_identity_presence[lane] == PlanePresence.ABSENT_DECLARED.value


def test_present_versus_declared_absent_follows_join_semantics() -> None:
    result = verify_eg_i82_cross_lane_join_v1(_lanes(I16=_identity_record()))
    assert result.package_n_sha256 == _PACKAGE_N_SHA256
    assert result.lane_identity_presence["I16"] == PlanePresence.PRESENT.value
    for lane in ("I17", "I52", "I56", "I61", "I65"):
        assert result.lane_identity_presence[lane] == PlanePresence.ABSENT_DECLARED.value


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(EgI82JoinVerifierError, match="conflicting identity rejected"):
        verify_eg_i82_cross_lane_join_v1(
            _lanes(
                I16=_identity_record(_PACKAGE_N_SHA256),
                I17=_identity_record(_OTHER_SHA256),
            )
        )


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(EgI82JoinVerifierError, match="ambiguous join rejected"):
        verify_eg_i82_cross_lane_join_v1(
            _lanes(
                I16=[_identity_record(_PACKAGE_N_SHA256), _identity_record(_OTHER_SHA256)],
            )
        )


def test_implicit_absence_rejected() -> None:
    lanes = _lanes()
    del lanes["I17"]
    with pytest.raises(EgI82JoinVerifierError, match="implicit absence rejected"):
        verify_eg_i82_cross_lane_join_v1(lanes)
    with pytest.raises(EgI82JoinVerifierError, match="implicit absence rejected"):
        verify_eg_i82_cross_lane_join_v1(_lanes(I52=None))
    payload = _identity_record().to_canonical_mapping()
    del payload["experiment_identity_id"]
    with pytest.raises(EgI82JoinVerifierError, match="implicit absence rejected"):
        verify_eg_i82_cross_lane_join_v1(_lanes(I16=payload))


def test_malformed_lane_data_rejected() -> None:
    with pytest.raises(EgI82JoinVerifierError, match="malformed plane data rejected"):
        verify_eg_i82_cross_lane_join_v1(_lanes(I16="not-an-object"))
    with pytest.raises(EgI82JoinVerifierError, match="malformed plane data rejected"):
        verify_eg_i82_cross_lane_join_v1("not-lanes")  # type: ignore[arg-type]
    payload = _identity_record().to_canonical_mapping()
    payload["plane_presence"] = {**payload["plane_presence"], "ORDERS": "PRESENT"}
    with pytest.raises(EgI82JoinVerifierError, match="malformed plane data rejected"):
        verify_eg_i82_cross_lane_join_v1(_lanes(I16=payload))


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(EgI82JoinVerifierError, match="noncanonical ID substitution rejected"):
        verify_eg_i82_cross_lane_join_v1(_lanes(I16={"run_id": _RUN_ID}))
    payload = _identity_record().to_canonical_mapping()
    payload["experiment_identity_id"] = _RUN_ID
    with pytest.raises(EgI82JoinVerifierError, match="noncanonical ID substitution rejected"):
        verify_eg_i82_cross_lane_join_v1(_lanes(I16=payload))


def test_cross_lane_substitution_rejected() -> None:
    with pytest.raises(EgI82JoinVerifierError, match="cross-lane substitution rejected"):
        verify_eg_i82_cross_lane_join_v1(
            _lanes(
                I16=_identity_record(_PACKAGE_N_SHA256, content_sha256=_CONTENT_SHA256),
                I17=_identity_record(_CONTENT_SHA256),
            )
        )


def test_cross_plane_substitution_rejected() -> None:
    with pytest.raises(EgI82JoinVerifierError, match="cross-plane substitution rejected"):
        verify_eg_i82_cross_lane_join_v1(
            _lanes(I16=_identity_record(_PACKAGE_N_SHA256, content_sha256=_PACKAGE_N_SHA256))
        )


def test_legacy_experiment_id_is_not_authoritative() -> None:
    provenance = {"legacy_experiment_id": "legacy-source-alias", "experiment_id": _RUN_ID}
    result = verify_eg_i82_cross_lane_join_v1(
        _lanes(I16=_identity_record(historical_provenance=provenance))
    )
    assert result.package_n_sha256 == _PACKAGE_N_SHA256
    assert result.package_n_sha256 != provenance["legacy_experiment_id"]
    assert result.package_n_sha256 != provenance["experiment_id"]
    absent = verify_eg_i82_cross_lane_join_v1(
        _lanes(
            I65=build_cross_lane_identity_join_record_v1(
                _complete(),
                historical_provenance=provenance,
            )
        )
    )
    assert absent.package_n_sha256 is None


def test_run_id_is_not_authoritative() -> None:
    result = verify_eg_i82_cross_lane_join_v1(_lanes(I16=_identity_record(run_id=_RUN_ID)))
    assert result.package_n_sha256 == _PACKAGE_N_SHA256
    assert result.package_n_sha256 != _RUN_ID
    with pytest.raises(EgI82JoinVerifierError, match="noncanonical ID substitution rejected"):
        verify_eg_i82_cross_lane_join_v1(_lanes(I16={"run_id": _RUN_ID, "experiment_id": _RUN_ID}))


def test_verifier_behavior_is_deterministic() -> None:
    raw = _lanes(I16=_identity_record(), I61=_identity_record())
    lanes = {lane: value.to_canonical_mapping() for lane, value in raw.items()}
    first = verify_eg_i82_cross_lane_join_v1(lanes).to_canonical_mapping()
    second = verify_eg_i82_cross_lane_join_v1(copy.deepcopy(lanes)).to_canonical_mapping()
    assert first == second
    assert first["package_n_sha256"] == _PACKAGE_N_SHA256
    assert first["schema_version"] == CONTRACT_VERSION


def test_inputs_are_not_mutated() -> None:
    original = _identity_record().to_canonical_mapping()
    snapshot = copy.deepcopy(original)
    lanes = _lanes(I16=original)
    result = verify_eg_i82_cross_lane_join_v1(lanes)
    original["experiment_identity_id"] = "MUTATED"
    lanes["I17"] = "MUTATED"
    assert result.package_n_sha256 == snapshot["experiment_identity_id"]
    assert original["experiment_identity_id"] == "MUTATED"


def test_no_persistence_migration_backfill_or_runtime_effects() -> None:
    source = VERIFIER_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_text" not in source
    assert "Path(" not in source
    assert "socket" not in source
    assert "urllib" not in source
    assert "requests" not in source
    assert "submit_order" not in source
    assert "place_order" not in source
    modules = _imported_modules(VERIFIER_PATH)
    assert "src.experiments.cross_lane_identity_join_v1" in modules
    assert "src.experiments.cross_lane_identity_join_record_v1" not in modules
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    for forbidden in (*_LIVE_CONTRACT_MODULES, *_DORMANT_ATTACHMENT_MODULES):
        assert forbidden not in modules
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def test_i16_emission_and_live_contracts_remain_unregistered() -> None:
    emission_source = I16_EMISSION_PATH.read_text(encoding="utf-8")
    assert "eg_i82_join_verifier_v1" not in emission_source
    assert "verify_eg_i82_cross_lane_join_v1" not in emission_source
    live_paths = (
        REPO_ROOT / "src" / "ingress" / "capsules" / "evidence_capsule.py",
        REPO_ROOT / "src" / "levelup" / "v0_models.py",
        REPO_ROOT / "src" / "live_eval" / "live_session_eval.py",
        REPO_ROOT / "src" / "analytics" / "explorer.py",
        REPO_ROOT
        / "src"
        / "ops"
        / "paper_shadow_observation_operator_go_session_preregistration_v1"
        / "preregistration_contract_v1.py",
    )
    for path in live_paths:
        text = path.read_text(encoding="utf-8")
        assert "eg_i82_join_verifier_v1" not in text
        assert "verify_eg_i82_cross_lane_join_v1" not in text


def test_r1_record_round_trip_still_validates() -> None:
    record = _identity_record()
    validated = validate_cross_lane_identity_join_v1(record.to_canonical_mapping())
    result = verify_eg_i82_cross_lane_join_v1(_lanes(I56=validated))
    assert result.package_n_sha256 == _PACKAGE_N_SHA256
