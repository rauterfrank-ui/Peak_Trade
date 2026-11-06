"""Contract digest bindings for Step-3 executor (surface + session + binding)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1 as load_surface_contract_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    BINDING_CAPABILITY_ID,
    BINDING_CONFIG_RELATIVE_PATH,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CONFIG_RELATIVE_PATH,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_MODE,
    PLANNED_RESTART_TEST_CONTRACT_SECONDS,
    SESSION_CONTRACT_RELATIVE_PATH,
    SURFACE_CAPABILITY_ID,
    SURFACE_CONFIG_RELATIVE_PATH,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
    sha256_file_bytes_v1,
)


class Step3ExecutorContractError(RuntimeError):
    """Fail-closed executor contract binding error."""


def load_execution_contract_bundle_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    executor_cfg_path = root / CONFIG_RELATIVE_PATH
    surface_cfg_path = root / SURFACE_CONFIG_RELATIVE_PATH
    session_contract_path = root / SESSION_CONTRACT_RELATIVE_PATH
    binding_cfg_path = root / BINDING_CONFIG_RELATIVE_PATH
    for path, label in (
        (executor_cfg_path, "EXECUTOR_CONFIG_MISSING"),
        (surface_cfg_path, "SURFACE_CONFIG_MISSING"),
        (session_contract_path, "SESSION_CONTRACT_MISSING"),
        (binding_cfg_path, "BINDING_CONFIG_MISSING"),
    ):
        if not path.is_file():
            raise Step3ExecutorContractError(label)

    executor_cfg = read_json_v1(executor_cfg_path)
    surface_cfg = read_json_v1(surface_cfg_path)
    session_contract = read_json_v1(session_contract_path)
    binding_cfg = read_json_v1(binding_cfg_path)

    if str(executor_cfg.get("capability_id") or "") != CAPABILITY_ID:
        raise Step3ExecutorContractError("EXECUTOR_CONFIG_CAPABILITY_ID_MISMATCH")
    if str(surface_cfg.get("capability_id") or "") != SURFACE_CAPABILITY_ID:
        raise Step3ExecutorContractError("SURFACE_CONFIG_CAPABILITY_ID_MISMATCH")
    if str(binding_cfg.get("capability_id") or "") != BINDING_CAPABILITY_ID:
        raise Step3ExecutorContractError("BINDING_CAPABILITY_ID_MISMATCH")
    if str(session_contract.get("session_id") or "") != TARGET_SESSION_ID:
        raise Step3ExecutorContractError("SESSION_ID_MISMATCH")
    if str(session_contract.get("canonical_instrument_id") or "") != CANONICAL_INSTRUMENT_ID:
        raise Step3ExecutorContractError("INSTRUMENT_SCOPE_MISMATCH")

    # Consume surface contract digests via surface loader (no duplication of digest math).
    surface_bundle = load_surface_contract_bundle_v1(repo_root=root)

    return {
        "executor_config": executor_cfg,
        "surface_config": surface_cfg,
        "session_contract": session_contract,
        "binding_config": binding_cfg,
        "executor_config_digest": sha256_file_bytes_v1(executor_cfg_path),
        "surface_config_digest": surface_bundle["surface_config_digest"],
        "session_contract_digest": surface_bundle["session_contract_digest"],
        "binding_config_digest": surface_bundle["binding_config_digest"],
        "network_mode": NETWORK_MODE,
        "network_allowlist": NETWORK_ALLOWLIST,
        "http_method_allowlist": HTTP_METHOD_ALLOWLIST,
        "target_session_id": TARGET_SESSION_ID,
        "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
        "planned_restart_test_contract_seconds": PLANNED_RESTART_TEST_CONTRACT_SECONDS,
        "required_reconciliation_before_alpha": bool(
            session_contract.get("required_reconciliation_before_alpha")
        ),
        "minimum_pre_restart_distinct_observations": int(
            session_contract.get("minimum_pre_restart_distinct_observations") or 0
        ),
        "surface_bundle": surface_bundle,
    }


def validate_digest_bindings_v1(
    *,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
    expected_surface_config_digest: str | None = None,
    expected_executor_config_digest: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    blockers: list[str] = []
    if expected_session_contract_digest != bundle["session_contract_digest"]:
        blockers.append("SESSION_CONTRACT_DIGEST_MISMATCH")
    if expected_binding_config_digest != bundle["binding_config_digest"]:
        blockers.append("BINDING_CONFIG_DIGEST_MISMATCH")
    if (
        expected_surface_config_digest is not None
        and expected_surface_config_digest != bundle["surface_config_digest"]
    ):
        blockers.append("SURFACE_CONFIG_DIGEST_MISMATCH")
    if (
        expected_executor_config_digest is not None
        and expected_executor_config_digest != bundle["executor_config_digest"]
    ):
        blockers.append("EXECUTOR_CONFIG_DIGEST_MISMATCH")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "bundle": bundle,
        "validation_digest": sha256_canonical_v1(
            {
                "session_contract_digest": bundle["session_contract_digest"],
                "binding_config_digest": bundle["binding_config_digest"],
                "surface_config_digest": bundle["surface_config_digest"],
                "executor_config_digest": bundle["executor_config_digest"],
            }
        ),
    }
