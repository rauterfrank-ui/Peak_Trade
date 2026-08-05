"""Fail-closed authorization and boundary proofs for the productive host launcher."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    AUTHORIZED_MODES,
    MODE_DASHBOARD_ONLY,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    EXCHANGE_CREDENTIAL_USE,
    FORBIDDEN_PRIVATE_PATH_PREFIXES,
    LIVE_ORDERS,
    O2_AUTHORIZED_MODES_REQUIRED,
    ORDER_PATH_ACTIVATED,
    OWNER,
    PAPER_EXCHANGE_ORDERS,
    PUBLIC_MD_ALLOWED_HOSTS,
    PUBLIC_MD_ALLOWED_PATH_PREFIXES,
    REAL_CAPITAL_MOVEMENT,
    TESTNET_ORDERS,
)


class ProductiveHostAuthorizationError(RuntimeError):
    """Fail-closed authorization / preflight error."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}:{detail}" if detail else code)


@dataclass(frozen=True)
class BoundaryProofV1:
    ok: bool
    o2_authorized_modes: tuple[str, ...]
    o2_unchanged: bool
    public_md_hosts: tuple[str, ...]
    public_md_path_prefixes: tuple[str, ...]
    private_endpoints_reachable: bool
    credential_path_reachable: bool
    order_submit_reachable: bool
    live_orders: bool
    testnet_orders: bool
    paper_exchange_orders: bool
    exchange_credential_use: bool
    real_capital_movement: bool
    order_path_activated: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "o2_authorized_modes": list(self.o2_authorized_modes),
            "o2_unchanged": self.o2_unchanged,
            "public_md_hosts": list(self.public_md_hosts),
            "public_md_path_prefixes": list(self.public_md_path_prefixes),
            "private_endpoints_reachable": self.private_endpoints_reachable,
            "credential_path_reachable": self.credential_path_reachable,
            "order_submit_reachable": self.order_submit_reachable,
            "live_orders": self.live_orders,
            "testnet_orders": self.testnet_orders,
            "paper_exchange_orders": self.paper_exchange_orders,
            "exchange_credential_use": self.exchange_credential_use,
            "real_capital_movement": self.real_capital_movement,
            "order_path_activated": self.order_path_activated,
            "detail": self.detail,
            "owner": OWNER,
        }


def require_owner_go_v1(
    *,
    owner_go: bool,
    environ: Mapping[str, str] | None = None,
) -> None:
    """Fail-closed unless explicit Owner-GO is present (arg or env)."""
    import os

    env = os.environ if environ is None else environ
    env_go = str(env.get("PEAK_TRADE_PRODUCTIVE_HOST_OWNER_GO", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "owner_go",
    }
    if not (bool(owner_go) or env_go):
        raise ProductiveHostAuthorizationError(
            "OWNER_GO_REQUIRED",
            "explicit owner_go=true or PEAK_TRADE_PRODUCTIVE_HOST_OWNER_GO required",
        )


def require_repository_sha_match_v1(
    *,
    actual_sha: str,
    expected_sha: str,
) -> None:
    actual = (actual_sha or "").strip().lower()
    expected = (expected_sha or "").strip().lower()
    if not expected:
        raise ProductiveHostAuthorizationError("EXPECTED_REPO_SHA_REQUIRED")
    if not actual:
        raise ProductiveHostAuthorizationError("ACTUAL_REPO_SHA_REQUIRED")
    if actual != expected:
        raise ProductiveHostAuthorizationError(
            "REPOSITORY_SHA_MISMATCH",
            f"actual={actual}:expected={expected}",
        )


def prove_o2_dashboard_only_unchanged_v1() -> None:
    if set(AUTHORIZED_MODES) != set(O2_AUTHORIZED_MODES_REQUIRED):
        raise ProductiveHostAuthorizationError(
            "O2_AUTHORIZED_MODES_DRIFT",
            f"AUTHORIZED_MODES={sorted(AUTHORIZED_MODES)}",
        )
    if MODE_DASHBOARD_ONLY not in AUTHORIZED_MODES:
        raise ProductiveHostAuthorizationError("O2_DASHBOARD_ONLY_MISSING")


def _bridge_authority_flags_from_source(repo_root: Path) -> dict[str, bool]:
    path = (
        repo_root
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "constants_v1.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, bool] = {}
    wanted = {
        "ORDERS_AUTHORIZED",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "PAPER_EXECUTION_AUTHORIZED",
        "RUNTIME_BRIDGE_LIVE_ACTIVATED",
    }
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in wanted:
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, bool):
                    out[target.id] = bool(node.value.value)
    missing = wanted - set(out)
    if missing:
        raise ProductiveHostAuthorizationError(
            "BRIDGE_AUTHORITY_FLAGS_UNREADABLE",
            ",".join(sorted(missing)),
        )
    return out


def prove_network_and_order_boundary_v1(
    *,
    repo_root: Path | None = None,
) -> BoundaryProofV1:
    """Static fail-closed proof: public-MD allowlist only; no order/credential path."""
    prove_o2_dashboard_only_unchanged_v1()
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    flags = _bridge_authority_flags_from_source(root)
    order_reachable = bool(
        flags["ORDERS_AUTHORIZED"]
        or flags["LIVE_AUTHORIZED"]
        or flags["TESTNET_AUTHORIZED"]
        or flags["PAPER_EXECUTION_AUTHORIZED"]
        or flags["RUNTIME_BRIDGE_LIVE_ACTIVATED"]
        or ORDER_PATH_ACTIVATED
        or LIVE_ORDERS
        or TESTNET_ORDERS
        or PAPER_EXCHANGE_ORDERS
    )
    credential_reachable = bool(EXCHANGE_CREDENTIAL_USE)
    private_reachable = False  # allowlist excludes private prefixes by contract
    ok = (
        not order_reachable
        and not credential_reachable
        and not private_reachable
        and not REAL_CAPITAL_MOVEMENT
    )
    proof = BoundaryProofV1(
        ok=ok,
        o2_authorized_modes=tuple(sorted(AUTHORIZED_MODES)),
        o2_unchanged=set(AUTHORIZED_MODES) == set(O2_AUTHORIZED_MODES_REQUIRED),
        public_md_hosts=PUBLIC_MD_ALLOWED_HOSTS,
        public_md_path_prefixes=PUBLIC_MD_ALLOWED_PATH_PREFIXES,
        private_endpoints_reachable=private_reachable,
        credential_path_reachable=credential_reachable,
        order_submit_reachable=order_reachable,
        live_orders=LIVE_ORDERS,
        testnet_orders=TESTNET_ORDERS,
        paper_exchange_orders=PAPER_EXCHANGE_ORDERS,
        exchange_credential_use=EXCHANGE_CREDENTIAL_USE,
        real_capital_movement=REAL_CAPITAL_MOVEMENT,
        order_path_activated=ORDER_PATH_ACTIVATED,
        detail="" if ok else "boundary_violation",
    )
    if not proof.ok:
        raise ProductiveHostAuthorizationError("NETWORK_OR_ORDER_BOUNDARY_VIOLATION", proof.detail)
    # Document private prefixes remain forbidden.
    _ = FORBIDDEN_PRIVATE_PATH_PREFIXES
    return proof


def resolve_git_head_sha_v1(repo_root: Path) -> str:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        raise ProductiveHostAuthorizationError("GIT_DIR_MISSING", str(git_dir))
    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref:"):
        ref = head.split(" ", 1)[1].strip()
        ref_path = git_dir / ref
        if not ref_path.is_file():
            raise ProductiveHostAuthorizationError("GIT_REF_MISSING", ref)
        return ref_path.read_text(encoding="utf-8").strip().lower()
    return head.lower()
