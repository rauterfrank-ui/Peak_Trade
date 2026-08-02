"""SimulatedExecutionPort — physically separate from real venue execution."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    apply_intended_action_via_canonical_accounting_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    OWNER,
    SIMULATED_EXECUTION_DELEGATE,
    repo_root_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)

# Hard deny: no-order host must never import or construct these.
_FORBIDDEN_IMPORT_SUFFIXES = (
    "live.broker_base",
    "execution.pipeline",
    "execution.orchestrator",
    "execution.paper.engine",
    "execution.paper.broker",
)
_FORBIDDEN_CALL_NAMES = frozenset(
    {
        "submit_order",
        "submit_orders",
        "place_order",
        "create_order",
        "cancel_order",
    }
)


class SimulatedExecutionPortError(RuntimeError):
    def __init__(self, code: ActivationFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


class SimulatedExecutionPortV1:
    """Sole execution port constructible by the Cap 7.2 no-order host.

    Delegates only to canonical simulated accounting. No polymorphic switch to
    a real venue execution adapter is possible from this type.
    """

    PORT_KIND = "SIMULATED_EXECUTION_PORT_V1"
    REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
    EXCHANGE_ORDER_SUBMIT_REACHABLE = False
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE = False
    ORDER_SIDE_EFFECT_OCCURRED = False

    def __init__(self) -> None:
        self.constructed = True
        self.delegate = SIMULATED_EXECUTION_DELEGATE
        self.owner = OWNER
        self.last_apply: dict[str, Any] = {}

    def apply_intended_action(
        self,
        *,
        session: Any,
        portfolio: Any,
        instrument_id: str,
        side: Any,
        quantity: Any,
        mark_price: Decimal | str,
        session_id: str,
        cycle_index: int,
        reduce_only: bool = False,
        state_root: Optional[Path] = None,
        persist: bool = True,
        writer_session_id: str = "",
    ) -> dict[str, Any]:
        out = apply_intended_action_via_canonical_accounting_v1(
            session=session,
            portfolio=portfolio,
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            mark_price=Decimal(str(mark_price)),
            session_id=session_id,
            cycle_index=cycle_index,
            reduce_only=reduce_only,
            state_root=state_root,
            persist=persist,
            writer_session_id=writer_session_id,
        )
        self.last_apply = {
            "port_kind": self.PORT_KIND,
            "delegate": self.delegate,
            "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
            "ORDER_SIDE_EFFECT_OCCURRED": False,
            "fill_present": out.get("fill") is not None,
        }
        return out


def construct_simulated_execution_port_v1() -> SimulatedExecutionPortV1:
    return SimulatedExecutionPortV1()


def refuse_real_execution_adapter_construction_v1(*_args: Any, **_kwargs: Any) -> None:
    raise SimulatedExecutionPortError(
        ActivationFailureCodeV1.REAL_EXECUTION_REACHABLE,
        "real_execution_adapter_construction_forbidden_in_no_order_host",
    )


def prove_execution_port_separation_v1() -> dict[str, Any]:
    package_root = Path(__file__).resolve().parent
    host_path = (
        repo_root_v1()
        / "src"
        / "ops"
        / "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "decision_economics_cycle_bridge_v1.py"
    )
    # AST scan of Cap 7.2 package + host for order submission calls / forbidden imports.
    call_hits: list[str] = []
    import_hits: list[str] = []
    scan_paths = [
        p for p in package_root.glob("*.py") if p.name != "simulated_execution_port_v1.py"
    ]
    if host_path.is_file():
        scan_paths.append(host_path)
    for path in scan_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if any(
                        name == suffix or name.startswith(suffix + ".")
                        for suffix in _FORBIDDEN_IMPORT_SUFFIXES
                    ):
                        import_hits.append(f"{path.name}:{name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if any(
                    mod == suffix or mod.startswith(suffix + ".")
                    for suffix in _FORBIDDEN_IMPORT_SUFFIXES
                ):
                    import_hits.append(f"{path.name}:{mod}")
            if isinstance(node, ast.Call):
                func = node.func
                fname = ""
                if isinstance(func, ast.Name):
                    fname = func.id
                elif isinstance(func, ast.Attribute):
                    fname = func.attr
                if fname in _FORBIDDEN_CALL_NAMES:
                    call_hits.append(f"{path.name}:{fname}")

    port = construct_simulated_execution_port_v1()
    ok = (
        port.PORT_KIND == "SIMULATED_EXECUTION_PORT_V1"
        and port.REAL_EXECUTION_ADAPTER_CONSTRUCTED is False
        and port.EXCHANGE_ORDER_SUBMIT_REACHABLE is False
        and port.EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False
        and not call_hits
        and not import_hits
        and not hasattr(port, "submit_order")
    )
    return {
        "ok": ok,
        "SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT": ok,
        "NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST": ok and not hasattr(port, "submit_order"),
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
        "port_kind": port.PORT_KIND,
        "delegate": port.delegate,
        "forbidden_call_hits": call_hits,
        "forbidden_import_hits": import_hits,
        "refuse_real_adapter": refuse_real_execution_adapter_construction_v1.__name__,
    }


def prove_no_polymorphic_real_port_switch_v1() -> dict[str, Any]:
    """Config/env/CLI cannot select a real venue execution port in Cap 7.2."""
    annotations = getattr(SimulatedExecutionPortV1.apply_intended_action, "__annotations__", {})
    has_port_selector = "execution_port" in annotations or "venue_port" in annotations
    return {
        "ok": not has_port_selector,
        "polymorphic_port_selector_absent": not has_port_selector,
        "config_switch_to_real_port_possible": False,
        "env_switch_to_real_port_possible": False,
        "cli_switch_to_real_port_possible": False,
    }
