"""Local read-only operator offline-bundle binding (consumer-only).

Discovers the same durable offline bundle root used by
``scripts/ops/start_market_dashboard_visual_operator_readonly_v1.sh`` and, when
safe, exports the existing fail-closed gate env vars so a normal uvicorn start
resolves canonical OHLCV/ranking/F5 without test-fixture injection.

Rules:
- Never invents market data.
- Never enables request-time venue/network producers.
- Never overrides explicitly set env (tests remain explicit).
- Never auto-binds under pytest (``pytest`` already imported).
- Never binds ``fixture:*`` / ``tests/fixtures`` paths as operator truth.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .contracts import ENV_EVIDENCE_ROOT, ENV_LINEAR_DIAGNOSTICS_ROOT

# Reuse the same durable locations as the canonical start script (no new producer).
_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
_DURABLE_BUNDLE_ROOT = _ARCHIVE_ROOT / "research" / "_market_visual_operator_offline_bundles_v1"
_TMP_BUNDLE_ROOT = Path("/tmp/peak_trade_market_visual_operator_bundles_v1")
_LINEAR_DIAGNOSTICS_DIR = (
    _ARCHIVE_ROOT
    / "research"
    / "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0_20260715T004424Z"
)

_ENV_DISABLE = "PEAK_TRADE_DISABLE_OPERATOR_LOCAL_BIND"
_ENV_BUNDLE_ROOT_OVERRIDE = "MARKET_VISUAL_OPERATOR_BUNDLE_ROOT"

_OHLCV_ENABLED = "PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED"
_OHLCV_ROOT = "PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT"
_RANKING_ENABLED = "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED"
_RANKING_ROOT = "PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT"
_F5_ENABLED = "PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED"
_F5_ROOT = "PEAK_TRADE_F5_MARKET_DASHBOARD_BUNDLE_ROOT"
_DEPTH_ENABLED = "PEAK_TRADE_MARKET_DEPTH_ENABLED"

_APPLIED_FLAG = "_PEAK_TRADE_OPERATOR_LOCAL_BIND_APPLIED"


def _under_pytest() -> bool:
    return "pytest" in sys.modules or os.environ.get("PEAK_TRADE_WEB_TEST_MODE") == "1"


def _env_blank(name: str) -> bool:
    return name not in os.environ or not str(os.environ.get(name, "")).strip()


def _set_if_blank(name: str, value: str) -> None:
    if _env_blank(name):
        os.environ[name] = value


def discover_canonical_operator_bundle_root() -> Path | None:
    """Return the first existing materialized offline bundle root, or None."""
    candidates: list[Path] = []
    override = (os.environ.get(_ENV_BUNDLE_ROOT_OVERRIDE) or "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend([_DURABLE_BUNDLE_ROOT, _TMP_BUNDLE_ROOT])

    for root in candidates:
        try:
            root = root.resolve(strict=True)
        except OSError:
            continue
        ohlcv = root / "futures_ohlcv" / "futures_ohlcv.json"
        if not ohlcv.is_file():
            continue
        if not _bundle_is_canonical_operator_source(ohlcv):
            continue
        return root
    return None


def _bundle_is_canonical_operator_source(ohlcv_json: Path) -> bool:
    """Reject test fixtures / unlabeled synthetic sources for operator binding."""
    try:
        payload = json.loads(ohlcv_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    source = str(payload.get("source") or "").strip().lower()
    if not source:
        return False
    if source.startswith("fixture:") or "complete_minimal" in source:
        return False
    if "test_fixture" in source or source == "synthetic":
        return False
    # Canonical materialize owner stamps historical_panel_offline:<sha>
    if source.startswith("historical_panel_offline:"):
        return True
    # Allow other non-fixture offline identifiers that are explicitly non-authorizing.
    if payload.get("non_authorizing") is True and "fixture" not in source:
        return True
    return False


def describe_binding_state() -> dict[str, Any]:
    root = discover_canonical_operator_bundle_root()
    return {
        "under_pytest": _under_pytest(),
        "disable_env": os.environ.get(_ENV_DISABLE),
        "bundle_root": str(root) if root else None,
        "applied": os.environ.get(_APPLIED_FLAG) == "1",
        "ohlcv_enabled": os.environ.get(_OHLCV_ENABLED),
        "ohlcv_root": os.environ.get(_OHLCV_ROOT),
    }


def maybe_apply_local_operator_offline_binding() -> dict[str, Any]:
    """Apply canonical offline gate env when safe; no-op otherwise.

    Returns a small diagnostic dict (never secrets).
    """
    state: dict[str, Any] = {
        "applied": False,
        "reason": "",
        "bundle_root": None,
        "source_class": "NONE",
    }
    if os.environ.get(_ENV_DISABLE, "").strip() == "1":
        state["reason"] = "disabled_by_env"
        return state
    if _under_pytest():
        state["reason"] = "pytest_isolation"
        return state
    if os.environ.get(_APPLIED_FLAG) == "1":
        state["applied"] = True
        state["reason"] = "already_applied"
        state["bundle_root"] = os.environ.get(_OHLCV_ROOT)
        return state

    # If operator already bound OHLCV explicitly (including fixture tests outside pytest),
    # do not silently replace it.
    if not _env_blank(_OHLCV_ENABLED) or not _env_blank(_OHLCV_ROOT):
        state["reason"] = "explicit_ohlcv_env_present"
        return state

    root = discover_canonical_operator_bundle_root()
    if root is None:
        state["reason"] = "canonical_bundle_missing"
        return state

    ohlcv_root = root / "futures_ohlcv"
    ranking_root = root / "ranking_funnel"
    f5_root = root / "f5_dashboard"

    _set_if_blank(_OHLCV_ENABLED, "1")
    _set_if_blank(_OHLCV_ROOT, str(ohlcv_root))
    if ranking_root.is_dir():
        _set_if_blank(_RANKING_ENABLED, "1")
        _set_if_blank(_RANKING_ROOT, str(ranking_root))
    if f5_root.is_dir():
        _set_if_blank(_F5_ENABLED, "1")
        _set_if_blank(_F5_ROOT, str(f5_root))
    _set_if_blank(ENV_EVIDENCE_ROOT, str(root))
    if _LINEAR_DIAGNOSTICS_DIR.is_dir():
        _set_if_blank(ENV_LINEAR_DIAGNOSTICS_ROOT, str(_LINEAR_DIAGNOSTICS_DIR))
    _set_if_blank(_DEPTH_ENABLED, "0")

    # Never pin future FIXED_GENERATED_AT for operator binding.
    os.environ[_APPLIED_FLAG] = "1"
    state.update(
        {
            "applied": True,
            "reason": "canonical_offline_bundle_bound",
            "bundle_root": str(root),
            "source_class": "CANONICAL_LOCAL_READ_ONLY_BUNDLE",
        }
    )
    return state


__all__ = [
    "describe_binding_state",
    "discover_canonical_operator_bundle_root",
    "maybe_apply_local_operator_offline_binding",
]
