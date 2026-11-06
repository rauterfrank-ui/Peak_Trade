"""Explicit flat SWAP account for offline host lifecycle tests only."""

from tests.ops.test_okx_eea_private_account_state_runtime_v1 import _fixture_rest


def host_private_rest_fixture_v1(path, params):
    payload = _fixture_rest(path, params)
    if path.endswith("/config"):
        payload["data"][0]["uid"] = "host-offline-account"
    if path.endswith(("/positions", "/orders-pending", "/orders-history", "/fills")):
        payload["data"] = []
    return payload


def initialize_synthetic_host_budget_v1(private_store_root, bound, account="host-offline-account"):
    """Explicit first-bootstrap of empty metadata in a temporary test scope only."""
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )

    root = private_store_root / "portfolio_budget_host_v1"
    if not root.exists():
        owner = PortfolioCapitalReservationBudgetOwnerV1(
            durable_root=root / "owner",
            durable_account_identity=account,
            durable_mode="create",
            durable_lane_bindings={"LANE_1": bound},
        )
        owner.close()
