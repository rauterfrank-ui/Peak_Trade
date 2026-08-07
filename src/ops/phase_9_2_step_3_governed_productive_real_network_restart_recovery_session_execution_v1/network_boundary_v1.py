"""Public-MD GET-only network boundary for Step-3 surface."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1 as prove_step3_entrypoint_network_boundary_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    repo_root_v1,
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "exchange_credential",
    "live_order",
    "testnet_order",
    "paper_exchange",
    "order_submit",
    "real_execution_adapter",
    "okx_private",
    "private_rest_order",
)


def prove_public_md_get_only_boundary_v1(
    *,
    environ: Mapping[str, str] | None = None,
    package_root: Path | None = None,
) -> dict[str, Any]:
    base = prove_step3_entrypoint_network_boundary_v1(environ=environ or {})
    blockers = list(base.get("blockers") or [])
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ALLOW_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PRODUCTIVE_NETWORK_MUST_REMAIN_UNAUTHORIZED")
    if NETWORK_ALLOWLIST != "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY":
        blockers.append("PUBLIC_MD_ALLOWLIST_DRIFT")
    if HTTP_METHOD_ALLOWLIST != "GET_ONLY":
        blockers.append("HTTP_METHOD_ALLOWLIST_DRIFT")

    root = (
        Path(package_root)
        if package_root is not None
        else (
            repo_root_v1() / "src/ops/phase_9_2_step_3_governed_productive_real_network_"
            "restart_recovery_session_execution_v1"
        )
    )
    import_hits: list[str] = []
    if root.is_dir():
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.lower()
                        for bad in FORBIDDEN_IMPORT_SUBSTRINGS:
                            if bad in name:
                                import_hits.append(f"{path.name}:{alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    mod = str(node.module or "").lower()
                    for bad in FORBIDDEN_IMPORT_SUBSTRINGS:
                        if bad in mod:
                            import_hits.append(f"{path.name}:{mod}")
    if import_hits:
        blockers.append("FORBIDDEN_ORDER_OR_CREDENTIAL_IMPORT:" + ",".join(import_hits))

    ok = not blockers and bool(base.get("ok"))
    return {
        "ok": ok,
        "blockers": blockers,
        "PUBLIC_MD_GET_ONLY": True,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_PATH_REACHABLE": False,
        "ORDER_SUBMIT_PATH_REACHABLE": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
        "NETWORK_ALLOWLIST": NETWORK_ALLOWLIST,
        "HTTP_METHOD_ALLOWLIST": HTTP_METHOD_ALLOWLIST,
        "entrypoint_boundary": base,
        "notes": [
            "REUSES_STEP3_ENTRYPOINT_NETWORK_BOUNDARY=true",
            "NO_PARALLEL_TRANSPORT_AUTHORITY=true",
        ],
    }
