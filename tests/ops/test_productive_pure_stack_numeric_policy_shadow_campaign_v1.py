"""Fail-closed tests for Stage-2 numeric policy shadow campaign runner v1."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.campaign_runner_v1 import (
    empty_scaffold_manifest,
    run_shadow_campaign_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    MECHANICAL_COUPLING_TOKEN,
    RELATIVE_OUTPUT_ROOT,
    SOLE_TRADING_AUTHORITY,
    STAGE1_MANIFEST_REL,
    STAGE2_TOKENS,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.evidence_emitter_v1 import (
    ShadowCampaignEmitError,
    build_evidence_pack,
    decide_campaign_state,
    resolve_and_validate_output_dir,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    CampaignStateV1,
    EmptyCapableManifestV1,
    FinalizedBarV1,
    ReproducibilityRecordV1,
    ShadowCampaignRequestV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    compute_config_digest,
    sha256_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_VALIDATOR = (
    REPO_ROOT / "scripts/ops/validate_productive_pure_stack_numeric_policy_evidence_pack_v1.py"
)
CAMPAIGN_SCAFFOLD = (
    REPO_ROOT
    / "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json"
)
RUNNER_SRC = (
    REPO_ROOT
    / "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/campaign_runner_v1.py"
)
EMITTER_SRC = (
    REPO_ROOT
    / "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/evidence_emitter_v1.py"
)


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_productive_pure_stack_numeric_policy_evidence_pack_v1",
        CLI_VALIDATOR,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _bars(
    n: int, *, finalized: bool = True, start: int = 1_700_000_000
) -> tuple[FinalizedBarV1, ...]:
    out: list[FinalizedBarV1] = []
    price = 100.0
    for i in range(n):
        price = 100.0 + (0.01 * i)
        out.append(
            FinalizedBarV1(
                instrument_id="TEST-INST",
                event_time_epoch_s=start + i * 60,
                open=price,
                high=price + 0.1,
                low=price - 0.1,
                close=price,
                mark_price=price,
                volume=1.0,
                finalized=finalized,
                dataset_id="hermetic_dataset_v1",
                source_id="hermetic_source_v1",
            )
        )
    return tuple(out)


def _hermetic_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    if not repo.exists():
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "docs").symlink_to(REPO_ROOT / "docs")
        (repo / RELATIVE_OUTPUT_ROOT).mkdir(parents=True)
        (repo / ".git").mkdir()
        (repo / ".git" / "HEAD").write_text("0" * 40 + "\n", encoding="utf-8")
    return repo


def _request(tmp_path: Path, *, campaign_id: str, **kwargs) -> ShadowCampaignRequestV1:
    repo = _hermetic_repo(tmp_path)
    out_root = repo / RELATIVE_OUTPUT_ROOT
    stage1 = sha256_file(repo / STAGE1_MANIFEST_REL)
    protocol = sha256_file(repo / CALIBRATION_PROTOCOL_REL)
    seed = int(kwargs.pop("seed", 7))
    scenario_id = str(kwargs.pop("scenario_id", "hermetic_scenario_v1"))
    defaults = dict(
        campaign_id=campaign_id,
        origin_main_sha="4416d55621b2f85b05c8e2fa9624282e4e6acf05",
        repo_root=str(repo),
        output_root=str(out_root),
        reproducibility=ReproducibilityRecordV1(
            git_sha="0" * 40,
            config_digest=compute_config_digest(
                seed=seed, scenario_id=scenario_id, campaign_id=campaign_id
            ),
            stage1_manifest_digest=stage1,
            calibration_protocol_digest=protocol,
            dataset_id="hermetic_dataset_v1",
            instrument_id="TEST-INST",
            scenario_id=scenario_id,
            seed=seed,
            event_time_epoch_s=1_700_000_000 + 60 * 70,
            wall_time_utc="2026-08-05T00:00:00Z",
            sole_trading_authority=SOLE_TRADING_AUTHORITY,
        ),
        observation_bars=_bars(70),
        recent_abs_log_return=0.002,
        fee_bps=2.0,
        slippage_bps=1.0,
        path_above_barrier=(True, True, False, True),
        sequence_metric_inputs={
            "path_survival_ratio": 0.75,
            "early_loss_toxicity": 0.1,
            "margin_buffer_at_risk_99": 0.2,
            "sequence_fragility_index": 0.1,
            "liquidation_near_miss_rate": 0.01,
            "governance_breach_frequency": 0.0,
            "chop_switch_survival_score": 0.8,
        },
        layer_metric_inputs={
            "max_effective_leverage": 5.0,
            "min_liquidation_buffer": 0.2,
            "fee_breakeven_bps": 3.0,
            "expected_adverse_fill_loss": 0.01,
            "funding_cost_profile": "flat",
            "is_perpetual": True,
        },
        dataset_manifest=empty_scaffold_manifest("test"),
        train_calibration_validation_partition_manifest=empty_scaffold_manifest("test"),
        walk_forward_manifest=empty_scaffold_manifest("test"),
        bootstrap_monte_carlo_manifest=empty_scaffold_manifest("test"),
        stress_pack_manifest=empty_scaffold_manifest("test"),
    )
    defaults.update(kwargs)
    return ShadowCampaignRequestV1(**defaults)


def test_exactly_18_tokens_and_null_values(tmp_path: Path) -> None:
    result = run_shadow_campaign_v1(_request(tmp_path, campaign_id="camp_18_tokens"))
    pack = json.loads(Path(result.evidence_pack_path).read_text(encoding="utf-8"))
    tokens = [row["token"] for row in pack["per_token_evidence"]]
    assert len(tokens) == 18
    assert set(tokens) == set(STAGE2_TOKENS)
    assert MECHANICAL_COUPLING_TOKEN not in tokens
    assert pack["productive_numeric_values_set"] == 0
    assert pack["input_authority"] is False
    assert pack["runtime_implemented"] is False
    assert pack["owner_ratified"] is False
    for row in pack["per_token_evidence"]:
        assert row["productive_numeric_value"] is None
        assert row["input_authority"] is False
        assert row["runtime_implemented"] is False


def test_validator_accepts_in_progress_shadow_pack(tmp_path: Path) -> None:
    result = run_shadow_campaign_v1(_request(tmp_path, campaign_id="camp_validator_ok"))
    pack = json.loads(Path(result.evidence_pack_path).read_text(encoding="utf-8"))
    cli = _load_validator()
    outcome = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert outcome["ok"] is True, outcome["errors"]
    assert pack["campaign_status"] == "IN_PROGRESS"
    assert pack["evidence_complete"] is False


def test_validator_rejects_unlawful_pack(tmp_path: Path) -> None:
    result = run_shadow_campaign_v1(_request(tmp_path, campaign_id="camp_validator_bad"))
    pack = json.loads(Path(result.evidence_pack_path).read_text(encoding="utf-8"))
    bad = deepcopy(pack)
    bad["per_token_evidence"][0]["productive_numeric_value"] = 1.23
    bad["input_authority"] = True
    bad["owner_ratified"] = True
    cli = _load_validator()
    outcome = cli.validate_pack(bad, repo_root=REPO_ROOT)
    assert outcome["ok"] is False
    assert any("productive_numeric_value_must_be_null" in e for e in outcome["errors"])


def test_reinvest_cannot_be_independent_token() -> None:
    scaffold = json.loads(CAMPAIGN_SCAFFOLD.read_text(encoding="utf-8"))
    rows = list(scaffold["per_token_evidence"])
    rows.append(
        {
            "token": MECHANICAL_COUPLING_TOKEN,
            "semantic_role": "bad",
            "required_producer": "x",
            "required_observations": [],
            "required_stratification": [],
            "required_stress_families": [],
            "primary_safety_metrics": [],
            "secondary_metrics": [],
            "mandatory_rejection_criteria": [],
            "dependency_tokens": [],
            "allowed_calibration_output_type": "THRESHOLD_FRACTION_UNIT_INTERVAL",
            "productive_numeric_value": None,
            "input_authority": False,
            "runtime_implemented": False,
            "owner_ratification_status": "NOT_RATIFIED",
            "authority_source": None,
            "derivation_source": None,
            "acceptance_gate_results": [],
            "rejection_reasons": [],
        }
    )
    with pytest.raises(ShadowCampaignEmitError, match="independent_reinvest"):
        build_evidence_pack(
            campaign_id="x",
            campaign_state=CampaignStateV1.IN_PROGRESS,
            origin_main_sha="a" * 40,
            stage1_manifest_digest="b" * 64,
            calibration_protocol_digest="c" * 64,
            scaffold_rows=rows[:18] + [rows[-1]],
            manifests={
                "dataset_manifest": empty_scaffold_manifest("t"),
                "train_calibration_validation_partition_manifest": empty_scaffold_manifest("t"),
                "walk_forward_manifest": empty_scaffold_manifest("t"),
                "bootstrap_monte_carlo_manifest": empty_scaffold_manifest("t"),
                "stress_pack_manifest": empty_scaffold_manifest("t"),
            },
            rejection_reasons=(),
        )


def test_forbidden_authority_source_rejected() -> None:
    scaffold = json.loads(CAMPAIGN_SCAFFOLD.read_text(encoding="utf-8"))
    rows = [dict(r) for r in scaffold["per_token_evidence"]]
    rows[0]["authority_source"] = "webui hardcoded limit"
    with pytest.raises(ShadowCampaignEmitError, match="forbidden_authority_source"):
        build_evidence_pack(
            campaign_id="x",
            campaign_state=CampaignStateV1.IN_PROGRESS,
            origin_main_sha="a" * 40,
            stage1_manifest_digest="b" * 64,
            calibration_protocol_digest="c" * 64,
            scaffold_rows=rows,
            manifests={
                "dataset_manifest": empty_scaffold_manifest("t"),
                "train_calibration_validation_partition_manifest": empty_scaffold_manifest("t"),
                "walk_forward_manifest": empty_scaffold_manifest("t"),
                "bootstrap_monte_carlo_manifest": empty_scaffold_manifest("t"),
                "stress_pack_manifest": empty_scaffold_manifest("t"),
            },
            rejection_reasons=(),
        )


def test_dashboard_runtime_workflow_archive_output_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "evidence" / "ops" / "market_dashboard_archive").mkdir(parents=True)
    with pytest.raises(
        ShadowCampaignEmitError, match="forbidden_output_archive_path|output_root_must"
    ):
        resolve_and_validate_output_dir(
            repo_root=repo,
            output_root=repo / "evidence" / "ops" / "market_dashboard_archive",
            campaign_id="c1",
        )


def test_path_traversal_and_symlink_escape_rejected(tmp_path: Path) -> None:
    with pytest.raises(ShadowCampaignEmitError, match="campaign_id_path_traversal"):
        resolve_and_validate_output_dir(
            repo_root=REPO_ROOT,
            output_root=REPO_ROOT / RELATIVE_OUTPUT_ROOT,
            campaign_id="../escape",
        )
    out = tmp_path / "out"
    out.mkdir()
    link = tmp_path / "link_out"
    link.symlink_to(out)
    with pytest.raises(ShadowCampaignEmitError, match="symlink|output_root_must"):
        resolve_and_validate_output_dir(
            repo_root=REPO_ROOT,
            output_root=link,
            campaign_id="c1",
        )


def test_no_overwrite_existing_campaign(tmp_path: Path) -> None:
    req = _request(tmp_path, campaign_id="camp_once")
    run_shadow_campaign_v1(req)
    with pytest.raises(ShadowCampaignEmitError, match="campaign_output_already_exists"):
        run_shadow_campaign_v1(req)


def test_digest_mismatch_rejected(tmp_path: Path) -> None:
    req = _request(tmp_path, campaign_id="camp_digest_bad")
    bad_repro = ReproducibilityRecordV1(
        **{
            **req.reproducibility.__dict__,
            "stage1_manifest_digest": "0" * 64,
        }
    )
    bad = ShadowCampaignRequestV1(**{**req.__dict__, "reproducibility": bad_repro})
    result = run_shadow_campaign_v1(bad)
    assert result.campaign_state is CampaignStateV1.REJECTED
    assert "stage1_manifest_digest_mismatch" in result.rejection_reasons


def test_incomplete_manifests_cannot_be_complete() -> None:
    manifests = {
        "dataset_manifest": empty_scaffold_manifest("t"),
        "train_calibration_validation_partition_manifest": empty_scaffold_manifest("t"),
        "walk_forward_manifest": empty_scaffold_manifest("t"),
        "bootstrap_monte_carlo_manifest": empty_scaffold_manifest("t"),
        "stress_pack_manifest": empty_scaffold_manifest("t"),
    }
    state = decide_campaign_state(
        rejection_reasons=(),
        manifests=manifests,
        evidence_requirements_met=True,
    )
    assert state is not CampaignStateV1.COMPLETE


def test_owner_ratified_remains_false(tmp_path: Path) -> None:
    result = run_shadow_campaign_v1(_request(tmp_path, campaign_id="camp_owner_false"))
    pack = json.loads(Path(result.evidence_pack_path).read_text(encoding="utf-8"))
    assert result.owner_ratified is False
    assert pack["owner_ratified"] is False
    assert pack["owner_ratification_status"] == "NOT_RATIFIED"


def test_non_finalized_bars_unavailable(tmp_path: Path) -> None:
    result = run_shadow_campaign_v1(
        _request(
            tmp_path,
            campaign_id="camp_non_final",
            observation_bars=_bars(70, finalized=False),
        )
    )
    rv = result.shadow_observations["realized_volatility"]
    assert rv["status"] == "REJECTED"
    assert rv["value"] is None


def test_lookahead_rejected_by_freshness_contract(tmp_path: Path) -> None:
    bars = _bars(70)
    result = run_shadow_campaign_v1(
        _request(
            tmp_path,
            campaign_id="camp_lookahead",
            observation_bars=bars,
            reproducibility=ReproducibilityRecordV1(
                **{
                    **_request(tmp_path, campaign_id="camp_lookahead").reproducibility.__dict__,
                    "event_time_epoch_s": bars[0].event_time_epoch_s - 10,
                }
            ),
        )
    )
    age = result.shadow_observations["freshness_age"]
    assert age["status"] == "REJECTED"
    assert age["age_seconds"] is None


def test_missing_inputs_typed_unavailable_not_defaults(tmp_path: Path) -> None:
    result = run_shadow_campaign_v1(
        _request(
            tmp_path,
            campaign_id="camp_missing",
            observation_bars=(),
            recent_abs_log_return=None,
            fee_bps=None,
            slippage_bps=None,
            path_above_barrier=None,
            sequence_metric_inputs=None,
            layer_metric_inputs=None,
        )
    )
    assert result.shadow_observations["opportunity_score"]["status"] == "UNAVAILABLE"
    assert result.shadow_observations["opportunity_score"]["value"] is None
    assert result.shadow_observations["path_survival_ratio"]["status"] == "UNAVAILABLE"


def test_deterministic_repeat_same_digest(tmp_path: Path) -> None:
    a = run_shadow_campaign_v1(_request(tmp_path / "a", campaign_id="camp_det", seed=11))
    b = run_shadow_campaign_v1(_request(tmp_path / "b", campaign_id="camp_det", seed=11))
    assert a.pack_digest == b.pack_digest
    assert (
        a.shadow_observations["realized_volatility"]["value"]
        == b.shadow_observations["realized_volatility"]["value"]
    )
    assert (
        a.shadow_observations["realized_volatility"]["input_digest"]
        == b.shadow_observations["realized_volatility"]["input_digest"]
    )


def test_different_inputs_change_digest(tmp_path: Path) -> None:
    a = run_shadow_campaign_v1(_request(tmp_path, campaign_id="camp_diff_a", seed=1))
    b = run_shadow_campaign_v1(
        _request(
            tmp_path,
            campaign_id="camp_diff_b",
            seed=1,
            path_above_barrier=(False, False),
        )
    )
    assert (
        a.shadow_observations["path_survival_ratio"]["input_digest"]
        != b.shadow_observations["path_survival_ratio"]["input_digest"]
    )


def test_no_order_testnet_live_imports() -> None:
    for path in (RUNNER_SRC, EMITTER_SRC):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        assert "from src.execution" not in text
        assert "import src.execution" not in text
        assert "market_dashboard" not in text
        assert "submit_order(" not in text
        assert "enable_live_trading=" not in text
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert "market_dashboard" not in mod
                assert not mod.startswith("src.execution")


def test_sole_trading_authority_constant() -> None:
    assert SOLE_TRADING_AUTHORITY == "run_integrated_offline_trading_logic_replay_v1"


def test_complete_requires_manifests() -> None:
    with pytest.raises(ShadowCampaignEmitError, match="complete_requires_all_manifests"):
        build_evidence_pack(
            campaign_id="x",
            campaign_state=CampaignStateV1.COMPLETE,
            origin_main_sha="a" * 40,
            stage1_manifest_digest="b" * 64,
            calibration_protocol_digest="c" * 64,
            scaffold_rows=json.loads(CAMPAIGN_SCAFFOLD.read_text(encoding="utf-8"))[
                "per_token_evidence"
            ],
            manifests={
                "dataset_manifest": empty_scaffold_manifest("t"),
                "train_calibration_validation_partition_manifest": empty_scaffold_manifest("t"),
                "walk_forward_manifest": empty_scaffold_manifest("t"),
                "bootstrap_monte_carlo_manifest": empty_scaffold_manifest("t"),
                "stress_pack_manifest": empty_scaffold_manifest("t"),
            },
            rejection_reasons=(),
        )
