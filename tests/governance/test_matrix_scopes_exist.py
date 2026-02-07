import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

REQUIRED_SCOPES = [
    "config/capability_scopes/L0_ops_docs.toml",
    "config/capability_scopes/L1_deep_research.toml",
    "config/capability_scopes/L2_market_outlook.toml",
    "config/capability_scopes/L3_trade_plan_advisory.toml",
    "config/capability_scopes/L4_governance_critic.toml",
]

def test_required_capability_scopes_exist():
    missing = [p for p in REQUIRED_SCOPES if not (ROOT / p).is_file()]
    assert not missing, f"Missing capability scopes: {missing}"
