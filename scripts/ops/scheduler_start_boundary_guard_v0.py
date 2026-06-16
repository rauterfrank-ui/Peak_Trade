#!/usr/bin/env python3
"""Shared scheduler start boundary guard (preflight hard-block, non-authorizing)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

SCHEDULER_START_BLOCKED_EXIT = 2
TEST_PREFLIGHT_OVERRIDE_ENV = "PEAK_TRADE_SCHEDULER_BOUNDARY_TEST_PREFLIGHT_JSON"
SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV = "PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_OUTROOT"
SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV = "PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_RUN_ID"


def _load_preflight_status(*, repo_root: Path | None) -> Mapping[str, Any]:
    override = os.environ.get(TEST_PREFLIGHT_OVERRIDE_ENV)
    if override:
        payload = json.loads(override)
        if isinstance(payload, dict):
            return payload

    from scripts.ops.report_paper_shadow_247_preflight_status import (
        build_paper_shadow_247_preflight_status,
    )

    root = repo_root or Path(__file__).resolve().parents[2]
    return build_paper_shadow_247_preflight_status(repo_root=root)


def _emit_scheduler_start_block(
    message: str,
    *,
    hold_no_paper_run_active: bool = False,
    scheduler_execution_authorized: bool = False,
) -> None:
    print("SCHEDULER_START_BLOCKED_BY_PREFLIGHT=true")
    print(f"SCHEDULER_EXECUTION_AUTHORIZED={str(scheduler_execution_authorized).lower()}")
    if hold_no_paper_run_active:
        print("HOLD_NO_PAPER_RUN_ACTIVE=true")
    print(f"SCHEDULER_START_BLOCK_REASON={message}")


def _emit_scheduler_hold_runtime_binding_clearance(
    binding: Mapping[str, Any],
) -> None:
    run_id = binding.get("expected_run_id", "")
    print("SCHEDULER_HOLD_RUNTIME_BINDING_CLEARANCE=true")
    print("SCHEDULER_HOLD_RUNTIME_BINDING_VALID=true")
    print(f"SCHEDULER_HOLD_RUNTIME_BINDING_RUN_ID={run_id}")
    print(f"SCHEDULER_HOLD_RUNTIME_BINDING_SCOPE={binding.get('binding_scope', '')}")
    print("SCHEDULER_START_AUTHORIZED_FOR_RUN_ID_SCOPED_BOUNDED_24H=true")


def _resolve_scheduler_hold_runtime_binding_from_env() -> Mapping[str, Any] | None:
    outroot_raw = os.environ.get(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV, "").strip()
    run_id = os.environ.get(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV, "").strip()
    if not outroot_raw and not run_id:
        return None
    if not outroot_raw or not run_id:
        return {
            "valid": False,
            "validation_issues": ["scheduler_hold_runtime_binding:partial_env"],
        }

    from scripts.ops.paper_shadow_247_scheduler_hold_runtime_binding_v0 import (
        build_scheduler_hold_runtime_binding_v0,
    )

    return build_scheduler_hold_runtime_binding_v0(
        Path(outroot_raw),
        expected_run_id=run_id,
    )


def assert_scheduler_start_authorized(
    preflight_status: Mapping[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> None:
    """Fail closed before non-dry-run scheduler-like execution."""
    if preflight_status is None:
        binding = _resolve_scheduler_hold_runtime_binding_from_env()
        if binding is not None:
            if binding.get("valid") is True:
                _emit_scheduler_hold_runtime_binding_clearance(binding)
                return
            issues = binding.get("validation_issues")
            detail = (
                ",".join(str(x) for x in issues)
                if isinstance(issues, list)
                else "scheduler_hold_runtime_binding_invalid"
            )
            _emit_scheduler_start_block(
                f"scheduler_hold_runtime_binding_v0:{detail}",
                hold_no_paper_run_active=True,
                scheduler_execution_authorized=False,
            )
            raise SystemExit(SCHEDULER_START_BLOCKED_EXIT)

        preflight_status = _load_preflight_status(repo_root=repo_root)

    hold = preflight_status.get("hold_context_v0")
    hold_state = hold.get("current_state") if isinstance(hold, dict) else None
    if hold_state == "HOLD_NO_PAPER_RUN":
        _emit_scheduler_start_block(
            "hold_context_v0.current_state=HOLD_NO_PAPER_RUN",
            hold_no_paper_run_active=True,
            scheduler_execution_authorized=False,
        )
        raise SystemExit(SCHEDULER_START_BLOCKED_EXIT)

    status = preflight_status.get("status")
    if status == "BLOCKED" or status != "READY":
        _emit_scheduler_start_block(
            f"preflight status={status!r}",
            scheduler_execution_authorized=False,
        )
        raise SystemExit(SCHEDULER_START_BLOCKED_EXIT)

    authorized = preflight_status.get("scheduler_execution_authorized")
    if authorized is not True:
        _emit_scheduler_start_block(
            "scheduler_execution_authorized is not true",
            scheduler_execution_authorized=False,
        )
        raise SystemExit(SCHEDULER_START_BLOCKED_EXIT)
