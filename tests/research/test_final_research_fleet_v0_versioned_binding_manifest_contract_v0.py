from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    AUTHORITY_EFFECT,
    CANONICAL_SERIALIZATION_VERSION,
    ECONOMIC_EVALUATION_REFS,
    EXPECTED_DATASET_DIGEST,
    FLEET_CANDIDATES,
    FLEET_ID,
    OPERATOR_RATIFICATION_REF,
    ORDER_EFFECT,
    REASON_BITCOIN_DIRECTION_BINDING,
    REASON_BINDING_REPAIR_REJECTED,
    REASON_CORRUPT_JSON,
    REASON_DUPLICATE_CANDIDATE,
    REASON_ECONOMIC_POLICY_MISMATCH,
    REASON_ECONOMIC_STATUS_CHANGED,
    REASON_EFFECT_NOT_NONE,
    REASON_EXTRA_CANDIDATE,
    REASON_MISSING_CANDIDATE,
    REASON_MISSING_EVALUATION_REF,
    REASON_MISSING_REQUIRED_FIELD,
    REASON_NOT_RATIFIED,
    REASON_RATIFICATION_REF_MISMATCH,
    REASON_SHARED_BINDING_MISMATCH,
    REASON_SPOT_BINDING,
    REASON_SYNTHETIC_SPOT_BINDING,
    REASON_UNKNOWN_ECONOMIC_STATUS,
    REASON_UNKNOWN_SCHEMA_VERSION,
    REASON_UNKNOWN_STRATEGY,
    REASON_UNKNOWN_DATASET_VERSION,
    REASON_WRONG_CONFIG_DIGEST,
    REASON_WRONG_DATA_DIGEST,
    REASON_WRONG_IMPLEMENTATION_DIGEST,
    REASON_WRONG_MANIFEST_DIGEST,
    REASON_WRONG_PARAMETER_BINDING,
    REASON_WRONG_STRATEGY_VERSION,
    REASON_ZERO_FEE,
    REASON_ZERO_SLIPPAGE,
    RUNTIME_EFFECT,
    SCHEMA_VERSION,
    STEP31F_CONFIG_PATHS,
    ValidationVerdict,
    clone_manifest,
    compute_config_digest_v1,
    compute_implementation_digest_v1,
    compute_manifest_digest_v1,
    compute_raw_file_config_digest_v0,
    load_step31f_evaluation_config_v0,
    materialize_final_research_fleet_v0_versioned_binding_manifest_v0,
    serialize_manifest_canonical_v1,
    validate_final_research_fleet_v0_versioned_binding_manifest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def canonical_manifest() -> dict:
    return materialize_final_research_fleet_v0_versioned_binding_manifest_v0(REPO_ROOT)


def _candidate(manifest: dict, strategy_id: str) -> dict:
    for candidate in manifest["candidates"]:
        if candidate["strategy_id"] == strategy_id:
            return candidate
    raise KeyError(strategy_id)


def _validate(manifest: dict, *, allow_recompute: bool = True):
    return validate_final_research_fleet_v0_versioned_binding_manifest_v0(
        manifest,
        repo_root=REPO_ROOT,
        allow_recompute_digests=allow_recompute,
    )


def test_materialize_accepts_exactly_three_fleet_candidates(canonical_manifest: dict) -> None:
    assert len(canonical_manifest["candidates"]) == 3
    ids = {candidate["strategy_id"] for candidate in canonical_manifest["candidates"]}
    assert ids == {sid for sid, _ in FLEET_CANDIDATES}


def test_deterministic_manifest_generation(canonical_manifest: dict) -> None:
    second = materialize_final_research_fleet_v0_versioned_binding_manifest_v0(REPO_ROOT)
    assert serialize_manifest_canonical_v1(canonical_manifest) == serialize_manifest_canonical_v1(
        second
    )
    assert canonical_manifest["manifest_digest"] == second["manifest_digest"]


def test_double_execution_produces_identical_bytes(canonical_manifest: dict) -> None:
    first_bytes = serialize_manifest_canonical_v1(canonical_manifest).encode("utf-8")
    second_bytes = serialize_manifest_canonical_v1(
        materialize_final_research_fleet_v0_versioned_binding_manifest_v0(REPO_ROOT)
    ).encode("utf-8")
    assert first_bytes == second_bytes


def test_double_execution_produces_identical_manifest_digest(canonical_manifest: dict) -> None:
    digest_a = canonical_manifest["manifest_digest"]
    digest_b = materialize_final_research_fleet_v0_versioned_binding_manifest_v0(REPO_ROOT)[
        "manifest_digest"
    ]
    assert digest_a == digest_b


def test_candidate_order_is_canonical_sorted(canonical_manifest: dict) -> None:
    strategy_ids = [candidate["strategy_id"] for candidate in canonical_manifest["candidates"]]
    assert strategy_ids == sorted(strategy_ids)
    rematerialized = materialize_final_research_fleet_v0_versioned_binding_manifest_v0(REPO_ROOT)
    assert [candidate["strategy_id"] for candidate in rematerialized["candidates"]] == strategy_ids


def test_step31f_configs_bound_read_only(canonical_manifest: dict) -> None:
    for strategy_id, _ in FLEET_CANDIDATES:
        cfg = load_step31f_evaluation_config_v0(REPO_ROOT, strategy_id)
        candidate = _candidate(canonical_manifest, strategy_id)
        assert candidate["config_digest"] == compute_config_digest_v1(cfg)
        assert candidate["source_config_ref"] == STEP31F_CONFIG_PATHS[strategy_id]


def test_effects_remain_none(canonical_manifest: dict) -> None:
    assert canonical_manifest["authority_effect"] == AUTHORITY_EFFECT == "NONE"
    assert canonical_manifest["runtime_effect"] == RUNTIME_EFFECT == "NONE"
    assert canonical_manifest["order_effect"] == ORDER_EFFECT == "NONE"


def test_existing_fail_statuses_preserved(canonical_manifest: dict) -> None:
    for strategy_id, _ in FLEET_CANDIDATES:
        candidate = _candidate(canonical_manifest, strategy_id)
        assert candidate["economic_evaluation_status"] == "FAIL"
        assert candidate["economic_evaluation_ref"] == ECONOMIC_EVALUATION_REFS[strategy_id]


def test_validator_accepts_canonical_manifest(canonical_manifest: dict) -> None:
    result = _validate(canonical_manifest)
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED
    assert result.fail_reasons == ()


def test_config_digest_semantics_classification() -> None:
    strategy_id = "trend_following"
    path = REPO_ROOT / STEP31F_CONFIG_PATHS[strategy_id]
    cfg = load_step31f_evaluation_config_v0(REPO_ROOT, strategy_id)
    raw_digest = compute_raw_file_config_digest_v0(path.read_bytes())
    canonical_digest = compute_config_digest_v1(cfg)
    assert raw_digest == "913055ac06973219412aa1440bef4f680f2c62a55237469f0aa52c06403d9986"
    assert canonical_digest == "136edb238aef61e8303b8d2d5b4a013dbf3ce6484c3f2aa966a4a1bbf2f1af20"
    assert raw_digest != canonical_digest


def test_implementation_digest_matches_registry(canonical_manifest: dict) -> None:
    expected = {
        "trend_following": "8bc31d6d5c8bce8fbcf9eb1ff5f9e679695e4538af46f542db91aedcccc8588b",
        "bollinger_bands": "2bc0f51f29587670878d7bfae66c3aac1e8c8ae48865f083c3d98611aa0dcb38",
        "momentum_1h": "a31f196354e1fac7f7d5f56e1d02c5b2d466c7dde935b0d8fb26985f40cd4c38",
    }
    for strategy_id, digest in expected.items():
        candidate = _candidate(canonical_manifest, strategy_id)
        assert candidate["implementation_digest"] == digest
        assert candidate["implementation_digest"] == compute_implementation_digest_v1(
            "src.strategies."
            + {
                "trend_following": "trend_following.TrendFollowingStrategy",
                "bollinger_bands": "bollinger.BollingerBandsStrategy",
                "momentum_1h": "momentum.MomentumStrategy",
            }[strategy_id]
        )


@pytest.mark.parametrize(
    ("strategy_id", "mutator", "reason_prefix"),
    [
        ("trend_following", lambda m: m["candidates"].pop(0), REASON_MISSING_CANDIDATE),
        (
            "trend_following",
            lambda m: m["candidates"].append(copy.deepcopy(m["candidates"][0])),
            REASON_DUPLICATE_CANDIDATE,
        ),
        (
            "trend_following",
            lambda m: m["candidates"].append(
                {
                    **_candidate(m, "bollinger_bands"),
                    "strategy_id": "macd",
                    "strategy_version": "v1",
                    "economic_evaluation_ref": "bogus",
                }
            ),
            REASON_UNKNOWN_STRATEGY,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update({"strategy_version": "v2"}),
            REASON_WRONG_STRATEGY_VERSION,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").pop("parameter_binding", None),
            REASON_MISSING_REQUIRED_FIELD,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update(
                {"parameter_binding": {"adx_period": 99}}
            ),
            REASON_WRONG_PARAMETER_BINDING,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following")["dataset_binding"].update(
                {"expected_dataset_digest": "f" * 64}
            ),
            REASON_UNKNOWN_DATASET_VERSION,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following")["period_binding"].update(
                {"training_period": "1970-01-01..1970-01-02"}
            ),
            REASON_SHARED_BINDING_MISMATCH,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following")["instrument_binding"].update(
                {"spot_allowed": True}
            ),
            REASON_SPOT_BINDING,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following")["instrument_binding"].update(
                {"synthetic_spot_allowed": True}
            ),
            REASON_SYNTHETIC_SPOT_BINDING,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following")["instrument_binding"].update(
                {"canonical_instrument_id": "inst-btc-usdt-perp"}
            ),
            REASON_BITCOIN_DIRECTION_BINDING,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following")["fee_model_binding"].update({"fee_bps": 0}),
            REASON_ZERO_FEE,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following")["slippage_model_binding"].update(
                {"slippage_bps": 0}
            ),
            REASON_ZERO_SLIPPAGE,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "bollinger_bands")["economic_policy_binding"].update(
                {"policy_version": "other_policy_v9"}
            ),
            REASON_ECONOMIC_POLICY_MISMATCH,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update({"ratified": False}),
            REASON_NOT_RATIFIED,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update(
                {"operator_ratification_ref": "wrong_ref"}
            ),
            REASON_RATIFICATION_REF_MISMATCH,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update(
                {"economic_evaluation_status": "PASS"}
            ),
            REASON_ECONOMIC_STATUS_CHANGED,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update(
                {"economic_evaluation_status": "UNKNOWN"}
            ),
            REASON_ECONOMIC_STATUS_CHANGED,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update({"economic_evaluation_ref": ""}),
            REASON_MISSING_EVALUATION_REF,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update({"implementation_digest": "0" * 64}),
            REASON_WRONG_IMPLEMENTATION_DIGEST,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update({"config_digest": "0" * 64}),
            REASON_WRONG_CONFIG_DIGEST,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update({"data_digest": "0" * 64}),
            REASON_WRONG_DATA_DIGEST,
        ),
        (
            "trend_following",
            lambda m: m.update({"schema_version": "unknown.v9"}),
            REASON_UNKNOWN_SCHEMA_VERSION,
        ),
        (
            "trend_following",
            lambda m: m.update({"authority_effect": "LIVE"}),
            REASON_EFFECT_NOT_NONE,
        ),
        (
            "trend_following",
            lambda m: m.update({"manifest_digest": "0" * 64}),
            REASON_WRONG_MANIFEST_DIGEST,
        ),
        (
            "trend_following",
            lambda m: _candidate(m, "trend_following").update({"fallback": True}),
            REASON_BINDING_REPAIR_REJECTED,
        ),
    ],
)
def test_negative_validation_cases(
    canonical_manifest: dict,
    strategy_id: str,
    mutator,
    reason_prefix: str,
) -> None:
    mutated = clone_manifest(canonical_manifest)
    mutator(mutated)
    if mutated.get("manifest_digest") == canonical_manifest["manifest_digest"]:
        mutated["manifest_digest"] = compute_manifest_digest_v1(mutated)
    result = _validate(mutated)
    assert result.valid is False
    assert result.verdict == ValidationVerdict.REJECTED
    assert any(reason.startswith(reason_prefix) for reason in result.fail_reasons)


def test_missing_candidate_rejected(canonical_manifest: dict) -> None:
    mutated = clone_manifest(canonical_manifest)
    mutated["candidates"] = [
        candidate
        for candidate in mutated["candidates"]
        if candidate["strategy_id"] != "momentum_1h"
    ]
    mutated["manifest_digest"] = compute_manifest_digest_v1(mutated)
    result = _validate(mutated)
    assert REASON_MISSING_CANDIDATE + ":momentum_1h" in result.fail_reasons


def test_extra_candidate_rejected(canonical_manifest: dict) -> None:
    mutated = clone_manifest(canonical_manifest)
    extra = copy.deepcopy(mutated["candidates"][0])
    extra["strategy_id"] = "rsi_reversion"
    extra["strategy_version"] = "v1"
    extra["economic_evaluation_ref"] = "bogus"
    mutated["candidates"].append(extra)
    mutated["manifest_digest"] = compute_manifest_digest_v1(mutated)
    result = _validate(mutated)
    assert any(reason.startswith(REASON_EXTRA_CANDIDATE) for reason in result.fail_reasons)


def test_corrupt_config_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad_root = tmp_path / "repo"
    bad_root.mkdir()
    config_dir = bad_root / "config/ops"
    config_dir.mkdir(parents=True)
    for rel in STEP31F_CONFIG_PATHS.values():
        source = REPO_ROOT / rel
        target = bad_root / rel
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    broken = bad_root / STEP31F_CONFIG_PATHS["trend_following"]
    broken.write_text("{not-json", encoding="utf-8")
    manifest = materialize_final_research_fleet_v0_versioned_binding_manifest_v0(REPO_ROOT)
    with pytest.raises(json.JSONDecodeError):
        load_step31f_evaluation_config_v0(bad_root, "trend_following")
    result = validate_final_research_fleet_v0_versioned_binding_manifest_v0(
        manifest,
        repo_root=bad_root,
        allow_recompute_digests=True,
    )
    assert result.valid is False
    assert any(REASON_CORRUPT_JSON in reason for reason in result.fail_reasons)


def test_manifest_metadata_fields(canonical_manifest: dict) -> None:
    assert canonical_manifest["schema_version"] == SCHEMA_VERSION
    assert canonical_manifest["fleet_id"] == FLEET_ID
    assert canonical_manifest["canonical_serialization_version"] == CANONICAL_SERIALIZATION_VERSION
    assert canonical_manifest["digest_semantics"]["config_digest"] == (
        "CANONICAL_PARSED_EVALUATION_CONFIG_v1"
    )
    assert canonical_manifest["candidates"][0]["operator_ratification_ref"] == (
        OPERATOR_RATIFICATION_REF
    )
    for candidate in canonical_manifest["candidates"]:
        assert candidate["data_digest"] == EXPECTED_DATASET_DIGEST
