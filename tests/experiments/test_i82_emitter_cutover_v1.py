"""I82 MU6 producer/emitter cutover tests.

Offline only. No exchange, credentials, orders, runtime authority,
backfill, Z2 mutation, or historical-evidence rewrite.
"""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

import pytest

from src.experiments.base import ExperimentConfig, ExperimentRunner, ParamSweep
from src.experiments.cross_lane_identity_join_v1 import is_package_n_sha256_canonical_id
from src.experiments.experiment_identity_manifest_v1 import (
    build_identity_config,
    build_manifest,
    compute_experiment_identity_id,
    compute_legacy_experiment_id_md5_12,
)
from src.ops.i82_emitter_cutover_preparation_contract_v1 import (
    BACKFILL_EXECUTED,
    CUTOVER_OWNER_GO,
    EMITTER_CUTOVER_EXECUTED,
    GET_EXPERIMENT_ID_PRE_CUTOVER_SOURCE_SHA256,
    GET_EXPERIMENT_ID_SOURCE_SHA256,
    I82EmitterCutoverPreparationError,
    I82_FULL_MIGRATION_PROVEN,
    LEGACY_MD5_REMOVED,
    LEGACY_SCHEME_MD5_12,
    MG_I82_EMITTER_CUTOVER_STATUS,
    PRESERVATION_FIXTURE_CANONICAL_SHA256,
    PRESERVATION_FIXTURE_LEGACY_MD5_12,
    RUNTIME_AUTHORITY_IMPACT,
    assert_preservation_fixture_v1,
    build_i82_identity_sidecar_from_package_n_manifest_v1,
    build_i82_identity_sidecar_v1,
    canonical_join_from_legacy_alias_alone_v1,
    require_canonical_identity_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EMITTER_PATH = REPO_ROOT / "src" / "experiments" / "base.py"
ARMSTRONG_PATH = REPO_ROOT / "src" / "experiments" / "armstrong_elkaroui_combi_experiment.py"
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
PREP_EVIDENCE = (
    REPO_ROOT / "docs" / "evidence" / "i82_emitter_cutover_preparation_v1" / "ATTESTATION.env"
)
OLD_MD5_12_OUTPUT = PRESERVATION_FIXTURE_LEGACY_MD5_12
NEW_SHA256_OUTPUT = PRESERVATION_FIXTURE_CANONICAL_SHA256


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


def test_cutover_status_flags() -> None:
    assert CUTOVER_OWNER_GO == "OWNER_GO_I82_EMITTER_CUTOVER"
    assert EMITTER_CUTOVER_EXECUTED is True
    assert MG_I82_EMITTER_CUTOVER_STATUS == "EMITTER_CUTOVER_COMPLETE"
    assert LEGACY_MD5_REMOVED is False
    assert BACKFILL_EXECUTED is False
    assert I82_FULL_MIGRATION_PROVEN is False
    assert RUNTIME_AUTHORITY_IMPACT == "NONE"


def test_forensic_md5_12_to_sha256_identifier_only() -> None:
    config = _sample_config()
    new_id = config.get_experiment_id()
    legacy = compute_legacy_experiment_id_md5_12(config)
    assert OLD_MD5_12_OUTPUT == "9b586cf2f92a"
    assert NEW_SHA256_OUTPUT == ("ef57df63bd82c65dc83258060424653d41180bd0d90c2ebd7f167531449ed36e")
    assert legacy == OLD_MD5_12_OUTPUT
    assert new_id == NEW_SHA256_OUTPUT
    assert new_id != OLD_MD5_12_OUTPUT
    assert len(OLD_MD5_12_OUTPUT) == 12
    assert len(new_id) == 64
    payload = config.to_dict()
    assert payload["name"] == "MA Optimization"
    assert payload["strategy_name"] == "ma_crossover"
    assert payload["symbols"] == ["ETH/EUR", "BTC/EUR"]
    assert payload["timeframe"] == "1h"
    assert payload["start_date"] == "2024-01-01"
    assert payload["end_date"] == "2024-06-01"
    assert payload["initial_capital"] == 10000.0
    assert payload["base_params"] == {"window": 3}


def test_productive_emitter_is_deterministic_sha256() -> None:
    config = _sample_config()
    first = config.get_experiment_id()
    second = config.get_experiment_id()
    third = _sample_config().get_experiment_id()
    canonical = compute_experiment_identity_id(build_identity_config(config))
    assert first == second == third == canonical == NEW_SHA256_OUTPUT
    assert is_package_n_sha256_canonical_id(first)
    source = inspect.getsource(ExperimentConfig.get_experiment_id)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    assert digest == GET_EXPERIMENT_ID_SOURCE_SHA256
    assert digest != GET_EXPERIMENT_ID_PRE_CUTOVER_SOURCE_SHA256


def test_name_change_changes_identity_and_keeps_sha256_width() -> None:
    left = _sample_config()
    right = ExperimentConfig(
        name="MA Optimization other",
        strategy_name="ma_crossover",
        param_sweeps=left.param_sweeps,
        symbols=left.symbols,
        timeframe=left.timeframe,
        start_date=left.start_date,
        end_date=left.end_date,
        initial_capital=left.initial_capital,
        base_params=left.base_params,
    )
    left_id = left.get_experiment_id()
    right_id = right.get_experiment_id()
    assert left_id != right_id
    assert is_package_n_sha256_canonical_id(left_id)
    assert is_package_n_sha256_canonical_id(right_id)
    assert compute_legacy_experiment_id_md5_12(left) != compute_legacy_experiment_id_md5_12(right)


def test_consumers_do_not_assume_md5_12_from_emitter() -> None:
    config = _sample_config()
    manifest = build_manifest(config)
    sidecar = build_i82_identity_sidecar_from_package_n_manifest_v1(manifest)
    emitted = config.get_experiment_id()
    assert sidecar.canonical_identity_id == emitted
    assert sidecar.legacy_experiment_id == OLD_MD5_12_OUTPUT
    assert sidecar.legacy_scheme == LEGACY_SCHEME_MD5_12
    joined = require_canonical_identity_v1(
        canonical_identity_id=emitted,
        legacy_experiment_id=sidecar.legacy_experiment_id,
    )
    assert joined == emitted
    with pytest.raises(I82EmitterCutoverPreparationError, match="legacy alias alone"):
        canonical_join_from_legacy_alias_alone_v1(OLD_MD5_12_OUTPUT)
    with pytest.raises(I82EmitterCutoverPreparationError, match="must not substitute"):
        require_canonical_identity_v1(
            canonical_identity_id=None,
            legacy_experiment_id=OLD_MD5_12_OUTPUT,
        )
    with pytest.raises(I82EmitterCutoverPreparationError, match="Package-N SHA256"):
        build_i82_identity_sidecar_v1(
            canonical_identity_id=OLD_MD5_12_OUTPUT,
            legacy_experiment_id=OLD_MD5_12_OUTPUT,
            legacy_scheme=LEGACY_SCHEME_MD5_12,
        )


def test_run_id_follows_emitter_without_independent_hash_rewrite() -> None:
    source = EMITTER_PATH.read_text(encoding="utf-8")
    assert 'run_id = f"{experiment_id}_{run_index:04d}"' in source
    runner = ExperimentRunner(quiet=True)
    result = runner.run(_sample_config(), dry_run=True)
    assert result.experiment_id == NEW_SHA256_OUTPUT
    assert is_package_n_sha256_canonical_id(result.experiment_id)


def test_armstrong_run_id_emitter_not_rewritten() -> None:
    text = ARMSTRONG_PATH.read_text(encoding="utf-8")
    assert "hashlib.md5(str(config.to_dict()).encode()).hexdigest()[:8]" in text


def test_negative_invalid_legacy_inputs_still_fail_closed() -> None:
    with pytest.raises(I82EmitterCutoverPreparationError, match="12 lowercase hex"):
        build_i82_identity_sidecar_v1(
            canonical_identity_id=NEW_SHA256_OUTPUT,
            legacy_experiment_id="not-an-md5",
            legacy_scheme=LEGACY_SCHEME_MD5_12,
        )
    with pytest.raises(I82EmitterCutoverPreparationError, match="JSON null"):
        build_i82_identity_sidecar_v1(
            canonical_identity_id=NEW_SHA256_OUTPUT,
            legacy_experiment_id="NONE",
            legacy_scheme=None,
        )


def test_historical_preparation_evidence_not_mutated() -> None:
    text = PREP_EVIDENCE.read_text(encoding="utf-8")
    assert "EMITTER_CUTOVER_EXECUTED=false" in text
    assert "MG_I82_EMITTER_CUTOVER=PREPARATION_COMPLETE" in text
    assert "BACKFILL_EXECUTED=false" in text


def test_z2_live_and_fee_semantics_unchanged() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    assert (
        "CURRENT_PHASE=SECTION_11_13_5_Z2_EDGE_I_EVENT_B_APPLICABILITY_UNPROVEN_SEARCH_SURFACES_EXHAUSTED"
        in text
    )
    assert "EDGE_I_STATUS=UNPROVEN" in text
    assert "OPERATIVE_EXPIRY_FEE_RATE=NONE" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "CANARY_EXECUTED=false" in text
    assert "SUCCESSOR_PHASE_AUTHORIZED=false" in text
    assert "Z2_CANONICAL_POINTER_REPLACED=false" in text
    assert "## 5.11 MG-I82-EMITTER-CUTOVER MU6 producer" in text
    assert "MG_I82_EMITTER_CUTOVER=EMITTER_CUTOVER_COMPLETE" in text
    assert "NEW_EMITTER_ALGORITHM=SHA256" in text


def test_cutover_fixture_contract() -> None:
    assert_preservation_fixture_v1()
