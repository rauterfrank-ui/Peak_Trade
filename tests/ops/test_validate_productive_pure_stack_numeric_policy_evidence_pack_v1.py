"""Fail-closed tests for Stage-2 numeric policy Evidence pack scaffolding v1.

Docs/validator-only. Non-authorizing. No runtime, dashboard, archive, or config mutation.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts/ops/validate_productive_pure_stack_numeric_policy_evidence_pack_v1.py"
CAMPAIGN = (
    REPO_ROOT
    / "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json"
)
SCHEMA = (
    REPO_ROOT / "docs/ops/schemas/productive_pure_stack_numeric_policy_evidence_pack_v1.schema.json"
)
REQUIREMENTS = (
    REPO_ROOT / "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_EVIDENCE_REQUIREMENTS_V1.md"
)
SCAFFOLDING = (
    REPO_ROOT / "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_EVIDENCE_PACK_SCAFFOLDING_V1.md"
)
STAGE1 = REPO_ROOT / "docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json"
PROTOCOL = REPO_ROOT / "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md"

STAGE2_TOKENS: tuple[str, ...] = (
    "OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS",
    "OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT",
    "OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE",
    "OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE",
    "OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE",
)

FORBIDDEN_IMPORT_MARKERS = (
    "market_dashboard",
    "from src.execution",
    "import execution",
    "src.archive",
    "durable_closeout",
    "run_integrated_offline_trading_logic_replay_v1",
)


def _load_cli():
    spec = importlib.util.spec_from_file_location(
        "validate_productive_pure_stack_numeric_policy_evidence_pack_v1",
        CLI,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_campaign() -> dict:
    return json.loads(CAMPAIGN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cli():
    return _load_cli()


def test_artifacts_exist_v1() -> None:
    assert CLI.is_file()
    assert CAMPAIGN.is_file()
    assert SCHEMA.is_file()
    assert REQUIREMENTS.is_file()
    assert SCAFFOLDING.is_file()
    assert STAGE1.is_file()
    assert PROTOCOL.is_file()


def test_valid_empty_not_started_manifest_v1(cli) -> None:
    pack = _load_campaign()
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is True, result["errors"]
    assert pack["campaign_status"] == "NOT_STARTED"
    assert pack["evidence_complete"] is False
    assert pack["owner_ratified"] is False
    assert pack["productive_numeric_values_set"] == 0
    assert pack["input_authority"] is False
    assert pack["runtime_implemented"] is False


def test_exactly_18_stage2_tokens_v1(cli) -> None:
    pack = _load_campaign()
    tokens = [row["token"] for row in pack["per_token_evidence"]]
    assert len(tokens) == 18
    assert set(tokens) == set(STAGE2_TOKENS)
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["token_count"] == 18
    assert result["ok"] is True


def test_productive_numeric_values_remain_null_v1() -> None:
    pack = _load_campaign()
    assert pack["productive_numeric_values_set"] == 0
    for row in pack["per_token_evidence"]:
        assert row["productive_numeric_value"] is None
        assert row["input_authority"] is False
        assert row["runtime_implemented"] is False


def test_reject_unknown_or_missing_tokens_v1(cli) -> None:
    pack = _load_campaign()
    bad = deepcopy(pack)
    bad["per_token_evidence"] = bad["per_token_evidence"][:-1]
    result = cli.validate_pack(bad, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert any(
        e.startswith("missing_tokens:") or "token_count_must_be_18" in e for e in result["errors"]
    )

    bad2 = deepcopy(pack)
    bad2["per_token_evidence"][0]["token"] = "OWNER_VALUE_NOT_A_STAGE2_TOKEN"
    result2 = cli.validate_pack(bad2, repo_root=REPO_ROOT)
    assert result2["ok"] is False
    assert any(e.startswith("unknown_tokens:") for e in result2["errors"])


def test_reject_productive_numeric_value_not_null_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["per_token_evidence"][0]["productive_numeric_value"] = 42
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert any(e.startswith("productive_numeric_value_must_be_null:") for e in result["errors"])


def test_reject_input_authority_not_false_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["input_authority"] = True
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert "input_authority_must_be_false" in result["errors"]


def test_reject_runtime_implemented_not_false_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["runtime_implemented"] = True
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert "runtime_implemented_must_be_false" in result["errors"]


def test_reject_missing_stage1_or_protocol_digests_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["stage1_manifest_digest"] = ""
    pack["calibration_protocol_digest"] = "deadbeef"
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert "missing_or_invalid_stage1_manifest_digest" in result["errors"]
    assert "missing_or_invalid_calibration_protocol_digest" in result["errors"]

    pack2 = deepcopy(_load_campaign())
    pack2["stage1_manifest_digest"] = "0" * 64
    pack2["calibration_protocol_digest"] = "1" * 64
    result2 = cli.validate_pack(pack2, repo_root=REPO_ROOT)
    assert result2["ok"] is False
    assert "stage1_manifest_digest_mismatch" in result2["errors"]
    assert "calibration_protocol_digest_mismatch" in result2["errors"]


def test_reject_fixture_webui_cmc_dashboard_authority_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["per_token_evidence"][0]["authority_source"] = "webui_hardcoded_limit"
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert any("forbidden_fixture_webui_cmc_dashboard_authority:" in e for e in result["errors"])


def test_reject_cmc_volatility_estimate_as_realized_volatility_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    for row in pack["per_token_evidence"]:
        if row["token"] == "OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY":
            row["authority_source"] = "CMC.volatility_estimate as realized_volatility"
            break
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert any("cmc_volatility_estimate_as_realized_volatility:" in e for e in result["errors"])


def test_reject_survival_or_suitability_result_v1_authority_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["per_token_evidence"][1]["authority_source"] = "SurvivalResultV1"
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert any("survival_result_v1_as_numeric_authority:" in e for e in result["errors"])

    pack2 = deepcopy(_load_campaign())
    pack2["per_token_evidence"][1]["authority_source"] = "SuitabilityResultV1"
    result2 = cli.validate_pack(pack2, repo_root=REPO_ROOT)
    assert result2["ok"] is False
    assert any("suitability_result_v1_as_numeric_authority:" in e for e in result2["errors"])


def test_reject_incomplete_stress_oos_partition_manifests_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["campaign_status"] = "IN_PROGRESS"
    pack["evidence_complete"] = True
    pack["stress_pack_manifest"] = {
        "status": "DECLARED",
        "populated": True,
        "entries": [],
        "digest": None,
        "notes": "incomplete",
    }
    pack["train_calibration_validation_partition_manifest"] = {
        "status": "EMPTY_SCAFFOLD",
        "populated": False,
        "entries": [],
        "digest": None,
        "notes": None,
    }
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert any(e.startswith("incomplete_manifest:") for e in result["errors"])


def test_reject_independent_reinvest_fraction_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    pack["forbidden_authority_declarations"]["reinvest_fraction_independent_numeric"] = True
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert "independent_reinvest_fraction_value" in result["errors"]

    pack2 = deepcopy(_load_campaign())
    extra = deepcopy(pack2["per_token_evidence"][0])
    extra["token"] = "OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION"
    pack2["per_token_evidence"].append(extra)
    result2 = cli.validate_pack(pack2, repo_root=REPO_ROOT)
    assert result2["ok"] is False
    assert "independent_reinvest_fraction_token_forbidden" in result2["errors"]


def test_reject_wallclock_seconds_for_time_quantum_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    for row in pack["per_token_evidence"]:
        if row["token"] == "OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP":
            row["derivation_source"] = "wallclock_seconds"
            row["allowed_calibration_output_type"] = "THRESHOLD_SECONDS"
            break
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert "capital_slot_time_quantum_wallclock_seconds" in result["errors"]


def test_reject_account_equity_derivation_for_initial_slot_base_v1(cli) -> None:
    pack = deepcopy(_load_campaign())
    for row in pack["per_token_evidence"]:
        if row["token"] == "OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE":
            row["derivation_source"] = "account_equity"
            break
    result = cli.validate_pack(pack, repo_root=REPO_ROOT)
    assert result["ok"] is False
    assert "initial_slot_base_from_account_equity" in result["errors"]


def test_validator_does_not_import_or_mutate_runtime_dashboard_archive_v1() -> None:
    source = CLI.read_text(encoding="utf-8")
    for marker in FORBIDDEN_IMPORT_MARKERS:
        # Symbol name may appear as a string constant (authority pin), but not as import.
        if marker.startswith("from ") or marker.startswith("import ") or marker.startswith("src."):
            assert marker not in source
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    joined = " ".join(imported)
    assert "market_dashboard" not in joined
    assert "execution" not in joined
    assert "archive" not in joined
    assert "src." not in joined
    # No Path.write / open write side effects in validator module body beyond CLI stdout.
    assert "write_text" not in source
    assert "Path.open" not in source or "read" in source


def test_requirements_doc_covers_all_18_tokens_v1() -> None:
    text = REQUIREMENTS.read_text(encoding="utf-8")
    for token in STAGE2_TOKENS:
        assert token in text
    assert "productive_numeric_value=null" in text or "productive_numeric_value | `null`" in text
    assert "TOKEN_COUNT=18" in text
    assert "CALIBRATION_EXECUTED=false" in text


def test_scaffolding_governance_assertions_v1() -> None:
    text = SCAFFOLDING.read_text(encoding="utf-8")
    assert "INFRASTRUCTURE_ONLY_NO_CALIBRATION_NO_NUMBERS" in text
    assert "CALIBRATION_EXECUTED=false" in text
    assert "NO_TOKEN_MAY_BE_GROUP_AUTO_RATIFIED=true" in text
    assert "EACH_PRODUCTIVE_VALUE_REQUIRES_SEPARATE_OWNER_RATIFICATION=true" in text
    assert "PRIMARY=SAFETY_METRICS" in text
    assert "separate" in text.lower()
