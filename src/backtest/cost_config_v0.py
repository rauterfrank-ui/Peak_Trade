"""
Canonical default backtest cost binding (RUNBOOK STEP 29J).

Single source of truth for versioned, reproducible backtest cost parameters.
Fail-closed: missing/invalid config must not silently default to zero cost.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from ..core.errors import BacktestError

COST_MODEL_VERSION = "backtest_cost_v0"
FEE_MODEL_VERSION = "backtest_fee_taker_symmetric_v0"
SLIPPAGE_MODEL_VERSION = "backtest_slippage_symmetric_v0"
FUNDING_MODEL_VERSION = "NOT_BOUND"
SPREAD_MODEL_VERSION = "NOT_APPLICABLE"
EXECUTION_MODEL_VERSION = "paper_market_context_v0"

REASON_EXPLICIT_ZERO_COST = "EXPLICIT_ZERO_COST_NON_ECONOMIC_MODE"
REASON_CONFIG_BOUND = "CANONICAL_VERSIONED_DEFAULT_CONFIG"
REASON_CLI_OVERRIDE = "EXPLICIT_CLI_OVERRIDE"
REASON_RUN_CONFIG_OVERRIDE = "EXPLICIT_RUN_CONFIG_OVERRIDE"
REASON_FUNDING_NOT_BOUND = "FUNDING_NOT_BOUND_DEFERRED"

_OVERRIDE_PRIORITY = (
    "explicit_cli_override",
    "explicit_run_config",
    "canonical_versioned_default_config",
)


class BacktestCostConfigError(BacktestError):
    """Raised when backtest cost configuration cannot be resolved fail-closed."""


@dataclass(frozen=True)
class CostOverrideProvenanceV0:
    field_name: str
    config_value: Optional[float]
    override_value: float
    override_source: str
    effective_value: float
    reason_code: str


@dataclass(frozen=True)
class EffectiveBacktestCostConfigV0:
    cost_model_version: str
    fee_model_version: str
    slippage_model_version: str
    funding_model_version: str
    spread_model_version: str
    execution_model_version: str
    maker_fee_bps: float
    taker_fee_bps: float
    entry_slippage_bps: float
    exit_slippage_bps: float
    funding_rate_source: str
    funding_application_policy: str
    spread_application_policy: str
    latency_assumption: str
    partial_fill_assumption: str
    config_source: str
    config_digest: str
    override_source: Optional[str]
    override_digest: Optional[str]
    economic_interpretation_allowed: bool
    zero_cost_explicitly_requested: bool
    reason_codes: List[str] = field(default_factory=list)
    override_provenance: List[CostOverrideProvenanceV0] = field(default_factory=list)

    @property
    def fee_bps(self) -> float:
        return self.taker_fee_bps

    @property
    def slippage_bps(self) -> float:
        return self.entry_slippage_bps

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["override_provenance"] = [asdict(p) for p in self.override_provenance]
        return d


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def compute_cost_config_digest(fields: Mapping[str, Any]) -> str:
    digest_input = {
        k: fields[k] for k in sorted(fields) if k not in {"config_digest", "override_digest"}
    }
    return hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()


def _validate_bps_value(name: str, value: Any) -> float:
    if value is None:
        raise BacktestCostConfigError(f"Missing required backtest cost field: {name}")
    if isinstance(value, str) and not value.strip():
        raise BacktestCostConfigError(f"Empty backtest cost field: {name}")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise BacktestCostConfigError(f"Invalid backtest cost field {name}: {value!r}") from exc
    if not math.isfinite(numeric):
        raise BacktestCostConfigError(f"Non-finite backtest cost field {name}: {value!r}")
    if numeric < 0:
        raise BacktestCostConfigError(f"Negative backtest cost field {name}: {numeric}")
    return numeric


def _extract_backtest_cost_section(cfg: Mapping[str, Any]) -> Dict[str, Any]:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, dict):
        raise BacktestCostConfigError(
            "Missing [backtest] section in config — cannot bind default backtest costs"
        )
    return dict(backtest)


def resolve_effective_backtest_cost_config(
    cfg: Mapping[str, Any],
    *,
    cli_fee_bps: Optional[float] = None,
    cli_slippage_bps: Optional[float] = None,
    run_config_fee_bps: Optional[float] = None,
    run_config_slippage_bps: Optional[float] = None,
    explicit_zero_cost_non_economic: bool = False,
    config_source: str = "canonical_versioned_default_config",
) -> EffectiveBacktestCostConfigV0:
    """
    Resolve effective backtest cost configuration.

    Priority: explicit_cli_override > explicit_run_config > canonical_versioned_default_config > fail_closed
    """
    if explicit_zero_cost_non_economic:
        base_fields = {
            "cost_model_version": COST_MODEL_VERSION,
            "fee_model_version": FEE_MODEL_VERSION,
            "slippage_model_version": SLIPPAGE_MODEL_VERSION,
            "funding_model_version": FUNDING_MODEL_VERSION,
            "spread_model_version": SPREAD_MODEL_VERSION,
            "execution_model_version": EXECUTION_MODEL_VERSION,
            "maker_fee_bps": 0.0,
            "taker_fee_bps": 0.0,
            "entry_slippage_bps": 0.0,
            "exit_slippage_bps": 0.0,
            "funding_rate_source": "NOT_BOUND",
            "funding_application_policy": "DEFERRED_TO_LATER_STEP",
            "spread_application_policy": "NOT_APPLICABLE",
            "latency_assumption": "NOT_BOUND",
            "partial_fill_assumption": "NOT_BOUND",
            "config_source": "explicit_zero_cost_non_economic",
        }
        digest = compute_cost_config_digest(base_fields)
        return EffectiveBacktestCostConfigV0(
            **base_fields,
            config_digest=digest,
            override_source=None,
            override_digest=None,
            economic_interpretation_allowed=False,
            zero_cost_explicitly_requested=True,
            reason_codes=[REASON_EXPLICIT_ZERO_COST, REASON_FUNDING_NOT_BOUND],
        )

    section = _extract_backtest_cost_section(cfg)
    config_fee = _validate_bps_value("backtest.fee_bps", section.get("fee_bps"))
    config_slippage = _validate_bps_value("backtest.slippage_bps", section.get("slippage_bps"))

    if config_fee == 0.0 and cli_fee_bps is None and run_config_fee_bps is None:
        raise BacktestCostConfigError(
            "Implicit zero-cost backtest fee is forbidden; set explicit_zero_cost_non_economic=True "
            "for non-economic test mode"
        )
    if config_slippage == 0.0 and cli_slippage_bps is None and run_config_slippage_bps is None:
        raise BacktestCostConfigError(
            "Implicit zero-cost backtest slippage is forbidden; set explicit_zero_cost_non_economic=True "
            "for non-economic test mode"
        )

    effective_fee = config_fee
    effective_slippage = config_slippage
    provenance: List[CostOverrideProvenanceV0] = []
    override_source: Optional[str] = None
    reason_codes = [REASON_CONFIG_BOUND, REASON_FUNDING_NOT_BOUND]

    if run_config_fee_bps is not None:
        run_fee = _validate_bps_value("run_config.fee_bps", run_config_fee_bps)
        provenance.append(
            CostOverrideProvenanceV0(
                field_name="fee_bps",
                config_value=config_fee,
                override_value=run_fee,
                override_source="explicit_run_config",
                effective_value=run_fee,
                reason_code=REASON_RUN_CONFIG_OVERRIDE,
            )
        )
        effective_fee = run_fee
        override_source = "explicit_run_config"
        reason_codes.append(REASON_RUN_CONFIG_OVERRIDE)

    if run_config_slippage_bps is not None:
        run_slip = _validate_bps_value("run_config.slippage_bps", run_config_slippage_bps)
        provenance.append(
            CostOverrideProvenanceV0(
                field_name="slippage_bps",
                config_value=config_slippage,
                override_value=run_slip,
                override_source="explicit_run_config",
                effective_value=run_slip,
                reason_code=REASON_RUN_CONFIG_OVERRIDE,
            )
        )
        effective_slippage = run_slip
        override_source = "explicit_run_config"
        if REASON_RUN_CONFIG_OVERRIDE not in reason_codes:
            reason_codes.append(REASON_RUN_CONFIG_OVERRIDE)

    if cli_fee_bps is not None:
        cli_fee = _validate_bps_value("cli.fee_bps", cli_fee_bps)
        provenance.append(
            CostOverrideProvenanceV0(
                field_name="fee_bps",
                config_value=config_fee,
                override_value=cli_fee,
                override_source="explicit_cli_override",
                effective_value=cli_fee,
                reason_code=REASON_CLI_OVERRIDE,
            )
        )
        effective_fee = cli_fee
        override_source = "explicit_cli_override"
        if REASON_CLI_OVERRIDE not in reason_codes:
            reason_codes.append(REASON_CLI_OVERRIDE)

    if cli_slippage_bps is not None:
        cli_slip = _validate_bps_value("cli.slippage_bps", cli_slippage_bps)
        provenance.append(
            CostOverrideProvenanceV0(
                field_name="slippage_bps",
                config_value=config_slippage,
                override_value=cli_slip,
                override_source="explicit_cli_override",
                effective_value=cli_slip,
                reason_code=REASON_CLI_OVERRIDE,
            )
        )
        effective_slippage = cli_slip
        override_source = "explicit_cli_override"
        if REASON_CLI_OVERRIDE not in reason_codes:
            reason_codes.append(REASON_CLI_OVERRIDE)

    if effective_fee == 0.0 and effective_slippage == 0.0:
        raise BacktestCostConfigError(
            "Zero-cost economic backtest is forbidden without explicit_zero_cost_non_economic=True"
        )

    base_fields = {
        "cost_model_version": str(section.get("cost_model_version", COST_MODEL_VERSION)),
        "fee_model_version": str(section.get("fee_model_version", FEE_MODEL_VERSION)),
        "slippage_model_version": str(
            section.get("slippage_model_version", SLIPPAGE_MODEL_VERSION)
        ),
        "funding_model_version": FUNDING_MODEL_VERSION,
        "spread_model_version": SPREAD_MODEL_VERSION,
        "execution_model_version": EXECUTION_MODEL_VERSION,
        "maker_fee_bps": effective_fee,
        "taker_fee_bps": effective_fee,
        "entry_slippage_bps": effective_slippage,
        "exit_slippage_bps": effective_slippage,
        "funding_rate_source": "NOT_BOUND",
        "funding_application_policy": "DEFERRED_TO_LATER_STEP",
        "spread_application_policy": "NOT_APPLICABLE",
        "latency_assumption": "NOT_BOUND",
        "partial_fill_assumption": "NOT_BOUND",
        "config_source": config_source,
    }
    config_digest = compute_cost_config_digest(base_fields)
    override_digest = None
    if provenance:
        override_digest = hashlib.sha256(
            _canonical_json([asdict(p) for p in provenance]).encode("utf-8")
        ).hexdigest()

    # Futures-only path: funding not yet bound — no economic validity claim (STEP 29J boundary).
    economic_allowed = False

    return EffectiveBacktestCostConfigV0(
        **base_fields,
        config_digest=config_digest,
        override_source=override_source,
        override_digest=override_digest,
        economic_interpretation_allowed=economic_allowed,
        zero_cost_explicitly_requested=False,
        reason_codes=reason_codes,
        override_provenance=provenance,
    )


def append_cost_accounting_fields(
    stats: Dict[str, Any],
    *,
    initial_equity: float,
    effective_cost: EffectiveBacktestCostConfigV0,
    total_fees: float = 0.0,
    total_notional: float = 0.0,
) -> Dict[str, Any]:
    """Augment stats with gross/net cost breakdown fields."""
    net_return = float(stats.get("total_return", 0.0))
    fee_drag = (total_fees / initial_equity) if initial_equity > 0 else 0.0
    slippage_impact = (
        (total_notional * effective_cost.entry_slippage_bps / 10000.0) / initial_equity
        if initial_equity > 0
        else 0.0
    )
    gross_return = net_return + fee_drag + slippage_impact
    stats = dict(stats)
    stats.update(
        {
            "gross_return": gross_return,
            "net_return": net_return,
            "fee_drag": fee_drag,
            "slippage_impact": slippage_impact,
            "funding_drag_or_status": FUNDING_MODEL_VERSION,
            "economic_interpretation_allowed": effective_cost.economic_interpretation_allowed,
        }
    )
    return stats


def build_cost_result_metadata(
    effective_cost: EffectiveBacktestCostConfigV0,
    *,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta = {
        "effective_cost_config": effective_cost.to_dict(),
        "cost_model_version": effective_cost.cost_model_version,
        "config_digest": effective_cost.config_digest,
        "override_digest": effective_cost.override_digest,
        "fee_bps": effective_cost.taker_fee_bps,
        "slippage_bps": effective_cost.entry_slippage_bps,
        "economic_interpretation_allowed": effective_cost.economic_interpretation_allowed,
        "reason_codes": list(effective_cost.reason_codes),
        "funding_binding_status": FUNDING_MODEL_VERSION,
    }
    if extra:
        meta.update(extra)
    return meta
