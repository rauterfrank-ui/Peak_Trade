"""Tests for CAPABILITY_O8 activation metadata (presentation entry retired fail-closed)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.canonical_runtime_operations_activation_v1.constants_v1 import (
    ACTIVATION_CONTRACT_RELATIVE_PATH,
    CANONICAL_OPERATOR_ENTRYPOINT,
    CANONICAL_SUBCOMMANDS,
    CAPABILITY_ID as O8_CAPABILITY_ID,
)
from src.ops.canonical_runtime_operations_activation_v1.contract_v1 import (
    ActivationContractError,
    default_activation_contract_path,
    load_activation_contract_v1,
    validate_activation_contract_v1,
)


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_activation_contract_valid_in_repository(repo_root: Path) -> None:
    path = default_activation_contract_path(repo_root)
    assert path.is_file()
    contract = validate_activation_contract_v1(load_activation_contract_v1(path))
    assert contract["capability_id"] == O8_CAPABILITY_ID
    assert contract["canonical_operator_entrypoint"] == CANONICAL_OPERATOR_ENTRYPOINT
    assert contract["presentation_operator_entry_retired"] is True
    assert contract["presentation_operator_entry_fail_closed"] is True
    assert contract["o2_dashboard_supervisor_retired"] is True
    assert contract["canonical_supervisor"] == "RETIRED_PRESENTATION_SUPERVISOR_V1"
    assert contract["canonical_dashboard_path"] == "RETIRED_PRESENTATION_DASHBOARD_V1"
    assert contract["core_logic_changed"] is False
    assert contract["dashboard_trading_authority"] is False
    assert contract["read_model_authority_effect"] == "NONE"
    assert contract["master_runbook_is_only_ssot"] is True
    assert contract["second_ssot_allowed"] is False
    for cmd in CANONICAL_SUBCOMMANDS:
        assert cmd in contract["canonical_subcommands"]
    assert contract["o6_productive_recovery_o2_supervisor_coupling"] == "DETACHED_V1"
    assert contract["canonical_operator_entry_productive_full_core_dependency"] is False


def test_activation_contract_rejects_authority_and_second_ssot(
    tmp_path: Path, repo_root: Path
) -> None:
    good = load_activation_contract_v1(default_activation_contract_path(repo_root))
    bad = dict(good)
    bad["live_trading_authorized"] = True
    with pytest.raises(ActivationContractError) as exc:
        validate_activation_contract_v1(bad)
    assert exc.value.code == "ACTIVATION_CONTRACT_FORBIDDEN_AUTHORITY"

    bad2 = dict(good)
    bad2["second_ssot_allowed"] = True
    with pytest.raises(ActivationContractError) as exc2:
        validate_activation_contract_v1(bad2)
    assert exc2.value.code == "ACTIVATION_CONTRACT_SECOND_SSOT_RISK"


def test_operator_entrypoint_fail_closed(repo_root: Path) -> None:
    entry = repo_root / CANONICAL_OPERATOR_ENTRYPOINT
    assert entry.is_file()
    proc = subprocess.run(
        [sys.executable, str(entry)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["presentation_http_host_retired"] is True
    assert payload["o2_dashboard_supervisor_retired"] is True


def test_single_operator_entrypoint_docs_and_contract_align(repo_root: Path) -> None:
    docs = repo_root / "docs/ops/CANONICAL_RUNTIME_OPERATOR_ENTRYPOINT_O8_V1.md"
    assert docs.is_file()
    docs_text = docs.read_text(encoding="utf-8")
    assert CANONICAL_OPERATOR_ENTRYPOINT in docs_text
    assert ACTIVATION_CONTRACT_RELATIVE_PATH in docs_text
    contract = load_activation_contract_v1(default_activation_contract_path(repo_root))
    assert contract["canonical_operator_entrypoint"] == CANONICAL_OPERATOR_ENTRYPOINT


def test_unknown_dependency_deauthorization_fail_closed(repo_root: Path) -> None:
    contract = load_activation_contract_v1(default_activation_contract_path(repo_root))
    legacy = contract["legacy_path_policy"]
    assert legacy["unknown_dependency_fail_closed"] is True
    assert legacy["deletion_allowed"] is False
    assert legacy["functional_change_allowed"] is False
    mutated = dict(contract)
    mutated_legacy = dict(legacy)
    mutated_legacy["unknown_dependency_fail_closed"] = False
    mutated["legacy_path_policy"] = mutated_legacy
    with pytest.raises(ActivationContractError) as exc:
        validate_activation_contract_v1(mutated)
    assert exc.value.code == "ACTIVATION_CONTRACT_UNKNOWN_DEPENDENCY_NOT_FAIL_CLOSED"


def test_rollback_boundary_and_authority_separation(repo_root: Path) -> None:
    contract = validate_activation_contract_v1(
        load_activation_contract_v1(default_activation_contract_path(repo_root))
    )
    rollback = contract["rollback_policy"]
    assert rollback["preserves_o1_o7_code"] is True
    assert rollback["preserves_o7_evidence"] is True
    assert rollback["preserves_legacy_callability"] is True
    assert contract["dashboard_trading_authority"] is False
    assert contract["read_model_authority_effect"] == "NONE"
    assert contract["live_trading_authorized"] is False
    assert contract["credentials_authorized"] is False


def test_o2_supervisor_package_absent(repo_root: Path) -> None:
    o2 = repo_root / "src/ops/canonical_local_launcher_and_process_supervision_v1"
    assert not o2.exists()
