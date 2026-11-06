"""Before/after witness for the B2 capital-guard config coercion defect (offline)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    parse_full_core_capital_guard_config_v1,
)

repo = Path(sys.argv[1])
label = sys.argv[2]
base = json.loads((repo / "config/ops/current_full_core_capital_guard_v1.json").read_text())
cases = {
    "owner_caps_ratified_string_false": {"owner_caps_ratified": "false", "full_core_guard_join_enabled": "false"},
    "max_single_order_notional_infinity": {"max_single_order_notional": "Infinity"},
}
out = {"label": label, "cases": {}}
for name, patch in cases.items():
    try:
        cfg = parse_full_core_capital_guard_config_v1({**base, **patch}, config_digest="d" * 64)
        out["cases"][name] = {
            "raised": False,
            "owner_caps_ratified": cfg.owner_caps_ratified,
            "full_core_guard_join_enabled": cfg.full_core_guard_join_enabled,
            "max_single_order_notional": None
            if cfg.max_single_order_notional is None
            else str(cfg.max_single_order_notional),
        }
    except Exception as exc:  # noqa: BLE001
        out["cases"][name] = {"raised": True, "error": f"{type(exc).__name__}:{exc}"}
print(json.dumps(out, sort_keys=True))
