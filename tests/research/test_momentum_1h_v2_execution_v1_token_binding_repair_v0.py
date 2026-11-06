"""Contract tests for momentum_1h/v2 execution V1 token binding repair."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.run_momentum_1h_v2_offline_economic_evaluation_execution_v0 import (
    EXECUTION_GO as CLI_EXECUTION_GO,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession_v1 import (
    CONFIG_REL_PATH as SUPERSESSION_CONFIG_REL_PATH,
    EXECUTION_GO_TOKEN,
    FAILED_V0_EXECUTION_BUNDLE,
    SUPERSEDED_EXECUTION_GO_TOKEN,
    SupersessionValidationVerdict,
    execution_token_contract_parity_v1,
    load_execution_authorization_supersession_v1,
    materialize_execution_authorization_supersession_v1,
    scan_prior_productive_v1_execution_bundles_v1,
    validate_execution_authorization_supersession_v1,
    verify_execution_go_token_replay_guard_v1,
    verify_v0_execution_consumed_v1,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0 import (
    EXECUTION_GO_TOKEN as HARNESS_EXECUTION_GO_TOKEN,
    REASON_SUPERSEDED_EXECUTION_GO_TOKEN_REJECTED,
    REASON_V0_REUSE_FORBIDDEN,
    run_full_offline_economic_evaluation_v0,
    validate_entry_point_go_token_v0,
    validate_execution_go_token_v0,
    verify_execution_start_state_v0,
)
from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERSESSION_CONFIG = REPO_ROOT / SUPERSESSION_CONFIG_REL_PATH


@pytest.fixture(name="versioned_binding")
def fixture_versioned_binding() -> dict:
    return materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification(versioned_binding: dict) -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=versioned_binding,
    )


@pytest.fixture(name="supersession")
def fixture_supersession(versioned_binding: dict) -> dict:
    return materialize_execution_authorization_supersession_v1(
        repo_root=REPO_ROOT,
        versioned_binding=versioned_binding,
    )


class TestPositiveTokenBindingContract:
    def test_harness_binds_exact_v1(self) -> None:
        assert HARNESS_EXECUTION_GO_TOKEN == EXECUTION_GO_TOKEN

    def test_cli_requires_exact_v1(self) -> None:
        assert CLI_EXECUTION_GO == EXECUTION_GO_TOKEN

    def test_supersession_binds_next_operator_go_v1(self, supersession: dict) -> None:
        assert supersession["next_operator_go"] == EXECUTION_GO_TOKEN

    def test_authorization_cli_harness_token_parity(self) -> None:
        parity = execution_token_contract_parity_v1(repo_root=REPO_ROOT)
        assert parity["token_contract_parity_pass"] is True

    def test_v1_passes_token_precheck(self) -> None:
        ok, reasons = validate_execution_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok, reasons

    def test_v1_entry_point_branch(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok and branch == "EXECUTION_V1"

    def test_supersession_config_valid(self, supersession: dict) -> None:
        verdict, reasons = validate_execution_authorization_supersession_v1(supersession)
        assert verdict == SupersessionValidationVerdict.ACCEPTED_COMPLETE
        assert reasons == ()

    def test_v0_consumed_detected(self) -> None:
        consumed, ref = verify_v0_execution_consumed_v1()
        assert consumed is True
        assert FAILED_V0_EXECUTION_BUNDLE in ref

    def test_v0_consumed_does_not_block_v1_token_validation(self) -> None:
        replay = verify_execution_go_token_replay_guard_v1(go_token=EXECUTION_GO_TOKEN)
        assert replay.v0_consumed is True
        assert replay.allowed is True

    def test_prior_productive_v1_not_present_by_default(self) -> None:
        bundles = scan_prior_productive_v1_execution_bundles_v1()
        assert bundles == ()

    def test_start_state_includes_supersession(
        self,
        authorization_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        result = verify_execution_start_state_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=versioned_binding,
        )
        assert result.valid is True

    def test_productive_owner_not_called_on_token_validation_only(
        self,
    ) -> None:
        with (
            patch(
                "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
                "run_baseline_offline_economic_evaluation_v0",
            ) as baseline_spy,
            patch(
                "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
                "run_offline_economic_evaluation_execution_dispatch_v0",
            ) as dispatch_spy,
        ):
            ok, _ = validate_execution_go_token_v0(EXECUTION_GO_TOKEN)
            replay = verify_execution_go_token_replay_guard_v1(go_token=EXECUTION_GO_TOKEN)
        dispatch_spy.assert_not_called()
        baseline_spy.assert_not_called()
        assert ok is True
        assert replay.allowed is True


class TestNegativeTokenBindingContract:
    @pytest.mark.parametrize(
        "token",
        [
            SUPERSEDED_EXECUTION_GO_TOKEN,
            "",
            " ",
            "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2",
            "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V1 ",
            " GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V1",
            "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V1_SUFFIX",
            "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION",
            "GO_UNKNOWN",
            None,
        ],
    )
    def test_invalid_tokens_rejected(self, token: str | None) -> None:
        ok, reasons = validate_execution_go_token_v0(token)
        assert ok is False
        assert reasons

    def test_v0_rejected_with_superseded_reason(self) -> None:
        ok, reasons = validate_execution_go_token_v0(SUPERSEDED_EXECUTION_GO_TOKEN)
        assert ok is False
        assert REASON_SUPERSEDED_EXECUTION_GO_TOKEN_REJECTED in reasons
        assert REASON_V0_REUSE_FORBIDDEN in reasons

    def test_authorization_v0_harness_v1_drift_detected(self, supersession: dict) -> None:
        drift = dict(supersession)
        drift["next_operator_go"] = SUPERSEDED_EXECUTION_GO_TOKEN
        verdict, reasons = validate_execution_authorization_supersession_v1(drift)
        assert verdict == SupersessionValidationVerdict.REJECTED_INCOMPLETE
        assert "NEXT_OPERATOR_GO_MISMATCH" in reasons

    def test_missing_supersession_fail_closed(
        self,
        authorization_ratification: dict,
        versioned_binding: dict,
        tmp_path: Path,
    ) -> None:
        missing_root = tmp_path / "repo"
        missing_root.mkdir()
        (missing_root / "config/ops").mkdir(parents=True)
        (missing_root / "config/research").mkdir(parents=True)
        binding_path = (
            missing_root / "config/research/momentum_1h_v2_versioned_research_binding_v0.json"
        )
        binding_path.write_text(json.dumps(versioned_binding), encoding="utf-8")
        ops_src = REPO_ROOT / "config/ops/momentum_1h_v2_economic_evaluation_v1.json"
        (missing_root / "config/ops/momentum_1h_v2_economic_evaluation_v1.json").write_text(
            ops_src.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        auth_src = (
            REPO_ROOT
            / "config/research/momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0.json"
        )
        if auth_src.is_file():
            (missing_root / auth_src.relative_to(REPO_ROOT)).write_text(
                auth_src.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        result = verify_execution_start_state_v0(
            repo_root=missing_root,
            authorization_ratification=authorization_ratification,
            versioned_binding=versioned_binding,
        )
        assert result.valid is False
        assert "EXECUTION_AUTHORIZATION_SUPERSESSION_MISSING" in result.fail_reasons

    def test_prior_productive_v1_blocks_start(self, tmp_path: Path) -> None:
        archive = tmp_path / "archive"
        bundle = (
            archive / "research/momentum_1h_v2_offline_economic_evaluation_execution_v1_test123Z"
        )
        bundle.mkdir(parents=True)
        (bundle / "execution_result.json").write_text(
            json.dumps({"productive_economic_evaluation_executed": True}),
            encoding="utf-8",
        )
        replay = verify_execution_go_token_replay_guard_v1(
            go_token=EXECUTION_GO_TOKEN,
            archive_root=archive,
        )
        assert replay.allowed is False
        assert replay.prior_productive_v1_execution_exists is True

    def test_failed_v1_start_does_not_block(self, tmp_path: Path) -> None:
        archive = tmp_path / "archive"
        bundle = (
            archive
            / "research/momentum_1h_v2_offline_economic_evaluation_execution_v1_failedstartZ"
        )
        bundle.mkdir(parents=True)
        (bundle / "execution_result.json").write_text(
            json.dumps(
                {
                    "productive_economic_evaluation_executed": False,
                    "cli_accepted_go_token": False,
                }
            ),
            encoding="utf-8",
        )
        replay = verify_execution_go_token_replay_guard_v1(
            go_token=EXECUTION_GO_TOKEN,
            archive_root=archive,
        )
        assert replay.prior_productive_v1_execution_exists is False
        assert replay.allowed is True


class TestConfigSurface:
    def test_supersession_config_present(self) -> None:
        assert SUPERSESSION_CONFIG.is_file()

    def test_loaded_supersession_matches_materializer(self, supersession: dict) -> None:
        loaded = load_execution_authorization_supersession_v1(REPO_ROOT)
        assert loaded == supersession
