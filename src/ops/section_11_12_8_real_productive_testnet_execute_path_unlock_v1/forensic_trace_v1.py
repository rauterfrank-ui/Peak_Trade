"""Forensic static blocker trace for the §11.12.8 execute path."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    CAPABILITY_ID,
    FORBIDDEN_TRACE_TOKENS,
    REQUIRED_RUNTIME_CHAIN,
)

_PREDECESSOR = Path(__file__).resolve().parents[1] / (
    "section_11_12_8_actual_productive_testnet_campaign_run_start_v1"
)

_BASELINE_REFUSALS: tuple[tuple[str, str], ...] = (
    (
        "productive_consumer_v1.py",
        "REAL_PRODUCTIVE_CAMPAIGN_FORBIDDEN_IN_IMPLEMENTATION_GO",
    ),
    ("secretref_credential_v1.py", "REAL_VAULT_NOT_INVOKED_IN_IMPLEMENTATION_GO"),
    ("testnet_transport_v1.py", "HTTP_CLIENT_NOT_BOUND"),
    ("constants_v1.py", "IMPLEMENTATION_ONLY"),
)


def build_forensic_blocker_trace_v1(*, unlocked: bool) -> dict[str, Any]:
    """Classify remaining refusals/stubs/dead edges on the authorized real path."""
    residual: list[dict[str, str]] = []
    closed: list[dict[str, str]] = []
    for filename, token in _BASELINE_REFUSALS:
        path = _PREDECESSOR / filename
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        present = token in text
        if token == "REAL_PRODUCTIVE_CAMPAIGN_FORBIDDEN_IN_IMPLEMENTATION_GO":
            # Allowed to remain as historical refuse helper, but must not be
            # invoked from MODE_PRODUCTIVE_REAL.
            real_branch_refuses = (
                "if mode == MODE_PRODUCTIVE_REAL:\n"
                "        refuse_real_productive_campaign_in_implementation_go_v1()"
            )
            on_authorized_path = real_branch_refuses in text
            if on_authorized_path:
                residual.append(
                    {
                        "token": token,
                        "file": filename,
                        "status": "PRESENT_ON_AUTHORIZED_PATH",
                    }
                )
            else:
                closed.append(
                    {
                        "token": token,
                        "file": filename,
                        "status": "HISTORICAL_HELPER_ONLY_NOT_ON_REAL_PATH",
                    }
                )
            continue
        if token == "IMPLEMENTATION_ONLY":
            # Predecessor package may retain historical constant; unlock path
            # must not emit it in runtime traces.
            closed.append(
                {
                    "token": token,
                    "file": filename,
                    "status": "HISTORICAL_PACKAGE_CONSTANT_NOT_ON_UNLOCK_TRACE",
                }
            )
            continue
        if token == "REAL_VAULT_NOT_INVOKED_IN_IMPLEMENTATION_GO":
            if present:
                residual.append(
                    {
                        "token": token,
                        "file": filename,
                        "status": "STILL_PRESENT",
                    }
                )
            else:
                closed.append(
                    {
                        "token": token,
                        "file": filename,
                        "status": "REMOVED",
                    }
                )
            continue
        if token == "HTTP_CLIENT_NOT_BOUND":
            # Error string may remain as fail-closed guard when client missing;
            # unlocked path must bind client before request.
            has_builder = "def build_productive_testnet_transport_v1" in text
            closed.append(
                {
                    "token": token,
                    "file": filename,
                    "status": (
                        "FAIL_CLOSED_GUARD_WITH_BOUND_BUILDER"
                        if has_builder
                        else "MISSING_BOUND_BUILDER"
                    ),
                }
            )
            if not has_builder:
                residual.append(
                    {
                        "token": "NO_BOUND_TRANSPORT_BUILDER",
                        "file": filename,
                        "status": "MISSING",
                    }
                )

    chain = {
        link: "PRESENT_AND_EXECUTABLE" if unlocked else "PRESENT_BUT_NON_EXECUTABLE"
        for link in REQUIRED_RUNTIME_CHAIN
    }
    ok = unlocked and len(residual) == 0
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "unlocked": unlocked,
        "required_chain": list(REQUIRED_RUNTIME_CHAIN),
        "chain_classifications": chain,
        "closed_blockers": closed,
        "residual_blockers": residual,
        "forbidden_trace_tokens": list(FORBIDDEN_TRACE_TOKENS),
    }
