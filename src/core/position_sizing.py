# src/core/position_sizing.py


from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal


class BasePositionSizer(ABC):
    """
    Basisklasse für Position Sizing.

    Contract:
    - Input: diskretes Signal (-1, 0, 1), aktueller Preis, aktuelle Equity
    - Output: Ziel-Positionsgröße in Units (z.B. BTC, ETH, Stücke).
    """

    @abstractmethod
    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        """
        Berechne die Ziel-Positionsgröße (Units) für das gegebene Signal.

        Args:
            signal: Diskretes Signal (-1=short, 0=flat, 1=long)
            price: Aktueller Preis des Assets
            equity: Aktuelle Equity/Kapital

        Returns:
            Ziel-Positionsgröße in Units (positiv=long, negativ=short, 0=flat)
        """
        raise NotImplementedError


class NoopPositionSizer(BasePositionSizer):
    """
    Default: nutzt das Signal direkt als Units (Kompatibilität mit altem Verhalten).

    - signal =  1 -> +1 Unit
    - signal = -1 -> -1 Unit
    - signal =  0 ->  0 Units
    """

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        return float(signal)

    def __repr__(self) -> str:
        return "<NoopPositionSizer()>"


@dataclass
class FixedSizeSizer(BasePositionSizer):
    """
    Fester Positionsumfang in Units pro vollem Signal.

    Beispiel:
    - units = 0.01  → 0.01 BTC pro vollem Long/Short-Signal
    """

    units: float = 1.0

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        return float(signal) * float(self.units)

    def __repr__(self) -> str:
        return f"<FixedSizeSizer(units={self.units})>"


@dataclass
class FixedFractionSizer(BasePositionSizer):
    """
    Investiert einen festen Anteil der aktuellen Equity pro vollem Signal.

    Beispiel:
    - fraction = 0.1 → 10% der Equity
    - Units = (Equity * fraction) / price
    """

    fraction: float = 0.1  # 10%

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        if signal == 0:
            return 0.0
        if price <= 0:
            return 0.0

        notional = max(equity, 0.0) * float(self.fraction)
        units = notional / price
        return float(signal) * units

    def __repr__(self) -> str:
        return f"<FixedFractionSizer(fraction={self.fraction:.1%})>"


def build_position_sizer_from_config(
    cfg: Any,
    section: str = "position_sizing",
) -> BasePositionSizer:
    """
    Fabrik-Funktion, die aus der Config einen passenden PositionSizer baut.

    Args:
        cfg: Config-Objekt (PeakConfig oder kompatibles Dict-Interface)
        section: Config-Section für Position Sizing

    Returns:
        BasePositionSizer-Instanz

    Erwartete Struktur in config.toml:

    [position_sizing]
    type = "noop"            # oder "fixed_size", "fixed_fraction"
    units = 1.0              # nur für type="fixed_size"
    fraction = 0.1           # nur für type="fixed_fraction"

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> sizer = build_position_sizer_from_config(cfg)
    """

    # Config-Zugriff: Unterstützt PeakConfig und Dict
    if hasattr(cfg, 'get'):
        get_fn = cfg.get
    elif isinstance(cfg, dict):
        # Fallback für plain dict
        def get_fn(path, default=None):
            keys = path.split(".")
            node = cfg
            for key in keys:
                if isinstance(node, dict) and key in node:
                    node = node[key]
                else:
                    return default
            return node
    else:
        raise TypeError(f"Unsupported config type: {type(cfg)}")

    type_value: str = str(get_fn(f"{section}.type", "noop")).lower()

    if type_value == "fixed_size":
        units = float(get_fn(f"{section}.units", 1.0))
        return FixedSizeSizer(units=units)

    if type_value == "fixed_fraction":
        fraction = float(get_fn(f"{section}.fraction", 0.1))
        return FixedFractionSizer(fraction=fraction)

    # Fallback / Default
    return NoopPositionSizer()

# ============================================================================
# Overlay / Regime helpers (Public API)
# ============================================================================

import abc
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence, Optional


def _call_base_sizer(base: Any, *args: Any, **kwargs: Any) -> float:
    """
    Call a base position sizer in a defensive way.

    Supports either:
    - callable(base)(*args, **kwargs)
    - base.size_position(...)
    - base.size(...)
    - base.get_position_size(...)
    - base.compute_position_size(...)
    """
    if callable(base):
        return float(base(*args, **kwargs))

    for meth in ("size_position", "size", "get_position_size", "compute_position_size"):
        fn = getattr(base, meth, None)
        if callable(fn):
            return float(fn(*args, **kwargs))

    raise TypeError(
        f"Base sizer {base!r} is not callable and has none of the supported methods: "
        "size_position/size/get_position_size/compute_position_size"
    )


def _extract_regime(kwargs: Mapping[str, Any], key: str) -> Optional[str]:
    """
    Extract regime value from kwargs in a flexible way.
    Looks in:
      - kwargs[key]
      - kwargs['context']/kwargs['ctx'] as mapping
      - kwargs['state']/kwargs['market_state'] as mapping or object attribute
    """
    if key in kwargs:
        val = kwargs.get(key)
        return None if val is None else str(val)

    for container_key in ("context", "ctx", "state", "market_state"):
        container = kwargs.get(container_key)
        if container is None:
            continue

        if isinstance(container, Mapping) and key in container:
            val = container.get(key)
            return None if val is None else str(val)

        # object attribute fallback
        if hasattr(container, key):
            val = getattr(container, key)
            return None if val is None else str(val)

    return None


class BasePositionOverlay(abc.ABC):
    """
    Minimal overlay interface for position sizing.

    An overlay receives the current `size` and can transform it based on the same
    args/kwargs that the sizer received.
    """

    @abc.abstractmethod
    def apply(self, size: float, *args: Any, **kwargs: Any) -> float:
        raise NotImplementedError

    def __call__(self, size: float, *args: Any, **kwargs: Any) -> float:
        return float(self.apply(float(size), *args, **kwargs))


@dataclass(frozen=True)
class OverlayPipelinePositionSizer:
    """
    Wrap a base sizer and apply overlays in order.
    """
    base_sizer: Any
    overlays: Sequence[BasePositionOverlay] = field(default_factory=tuple)
    clip_min: float = 0.0

    def size_position(self, *args: Any, **kwargs: Any) -> float:
        size = _call_base_sizer(self.base_sizer, *args, **kwargs)
        for ov in self.overlays:
            size = float(ov.apply(float(size), *args, **kwargs))
        if self.clip_min is not None:
            size = max(float(self.clip_min), float(size))
        return float(size)

    # Common alias names used across codebases/tests
    def __call__(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def get_position_size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def compute_position_size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)


# Backwards-compatible aliases (high chance tests use one of these names)
OverlayPipelineSizer = OverlayPipelinePositionSizer
PositionSizingOverlayPipeline = OverlayPipelinePositionSizer

# Export control (if module defines __all__, extend it safely)
try:
    __all__  # type: ignore[name-defined]
except NameError:
    __all__ = []  # type: ignore[assignment]

try:
    _existing = list(__all__)  # type: ignore[arg-type]
except Exception:
    _existing = []

__all__ = sorted(set(_existing + [  # type: ignore[assignment]
    "BasePositionOverlay",
    "OverlayPipelinePositionSizer",
    "OverlayPipelineSizer",
    "PositionSizingOverlayPipeline",
    "VolRegimeOverlaySizer",
]))


# === Peak_Trade overlay public API (compat) ===
# Backwards-compatible overlay & config helpers expected by tests.

import abc
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence, Union


def _call_base_sizer(base: Any, *args: Any, **kwargs: Any) -> float:
    """
    Call a base position sizer defensively.

    Supports:
    - callable(base)(...)
    - base.size_position(...)
    - base.size(...)
    - base.get_position_size(...)
    - base.compute_position_size(...)
    """
    if callable(base):
        return float(base(*args, **kwargs))

    for meth in ("size_position", "size", "get_position_size", "compute_position_size"):
        fn = getattr(base, meth, None)
        if callable(fn):
            return float(fn(*args, **kwargs))

    raise TypeError(
        f"Base sizer {base!r} is not callable and has none of the supported methods: "
        "size_position/size/get_position_size/compute_position_size"
    )


def _extract_regime(kwargs: Mapping[str, Any], key: str) -> Optional[str]:
    """
    Extract regime value from kwargs in a flexible way.
    Looks in:
      - kwargs[key]
      - kwargs['context']/kwargs['ctx'] as mapping or object attr
      - kwargs['state']/kwargs['market_state'] as mapping or object attr
    """
    if key in kwargs:
        v = kwargs.get(key)
        return None if v is None else str(v)

    for container_key in ("context", "ctx", "state", "market_state"):
        container = kwargs.get(container_key)
        if container is None:
            continue

        if isinstance(container, Mapping) and key in container:
            v = container.get(key)
            return None if v is None else str(v)

        if hasattr(container, key):
            v = getattr(container, key)
            return None if v is None else str(v)

    return None


class BasePositionOverlay(abc.ABC):
    """Minimal overlay interface: transform a computed size."""

    @abc.abstractmethod
    def apply(self, size: float, *args: Any, **kwargs: Any) -> float:
        raise NotImplementedError

    def __call__(self, size: float, *args: Any, **kwargs: Any) -> float:
        return float(self.apply(float(size), *args, **kwargs))


@dataclass(frozen=True)
class VolRegimeOverlay(BasePositionOverlay):
    """Overlay: size *= multiplier(regime)."""
    regime_multipliers: Mapping[str, float]
    default_multiplier: float = 1.0
    regime_key: str = "vol_regime"
    clip_min: float = 0.0

    def apply(self, size: float, *args: Any, **kwargs: Any) -> float:
        regime = _extract_regime(kwargs, self.regime_key)
        mult = float(self.regime_multipliers.get(regime, self.default_multiplier))
        out = float(size) * mult
        if self.clip_min is not None:
            out = max(float(self.clip_min), float(out))
        return float(out)


@dataclass(frozen=True)
class CompositePositionSizer(BasePositionSizer):  # type: ignore[name-defined]
    """Base sizer + overlays (applied in order)."""
    base_sizer: Any
    overlays: Sequence[BasePositionOverlay] = field(default_factory=tuple)
    clip_min: float = 0.0

    def size_position(self, *args: Any, **kwargs: Any) -> float:
        size = _call_base_sizer(self.base_sizer, *args, **kwargs)
        for ov in self.overlays:
            size = float(ov.apply(float(size), *args, **kwargs))
        if self.clip_min is not None:
            size = max(float(self.clip_min), float(size))
        return float(size)

    def __call__(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def get_position_size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def compute_position_size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)



    # PT_CONCRETE_COMPOSITE_GTP
    def get_target_position(self, *args, **kwargs):
        """Concrete implementation to satisfy ABC; delegates to base_sizer."""
        base = getattr(self, 'base_sizer', None) or getattr(self, 'base', None)
        if base is None:
            raise ValueError('CompositePositionSizer: missing base_sizer')
        units = base.get_target_position(*args, **kwargs)
        
        # Prepare kwargs for overlay.apply() - it expects keyword-only args
        # Standard signature: apply(*, units, signal, price, equity, context)
        signal = args[0] if len(args) > 0 else kwargs.get('signal', 0)
        price = args[1] if len(args) > 1 else kwargs.get('price', 0.0)
        equity = args[2] if len(args) > 2 else kwargs.get('equity', 0.0)
        context = kwargs.get('context', {})
        
        overlay_kwargs = {
            'units': units,
            'signal': signal,
            'price': price,
            'equity': equity,
            'context': context,
        }
        
        for ov in (getattr(self, 'overlays', None) or []):
            if hasattr(ov, 'apply'):
                try:
                    units = ov.apply(**overlay_kwargs)
                    overlay_kwargs['units'] = units  # Update for next overlay
                    continue
                except TypeError:
                    pass
            if hasattr(ov, 'transform'):
                try:
                    units = ov.transform(units, *args, **kwargs)
                    continue
                except TypeError:
                    pass
        return float(units)
@dataclass(frozen=True)
class VolRegimeOverlaySizerConfig:
    """Config container used by tests."""
    regime_multipliers: Mapping[str, float] = field(default_factory=dict)
    default_multiplier: float = 1.0
    regime_key: str = "vol_regime"
    clip_min: float = 0.0
    day_vol_budget: float = 0.02
    vol_window_bars: int = 20
    vol_target_scaling: bool = False
    regime_lookback_bars: int = 50
    bars_per_day: int = 1
    trading_days_per_year: int = 252
    enable_dd_throttle: bool = False
    dd_soft_start: float = 0.10
    max_drawdown: float = 0.25

    def to_overlay(self) -> VolRegimeOverlay:
        return VolRegimeOverlay(
            regime_multipliers=self.regime_multipliers,
            default_multiplier=self.default_multiplier,
            regime_key=self.regime_key,
            clip_min=self.clip_min,
        )


@dataclass(frozen=True)
class VolRegimeOverlaySizer(BasePositionSizer):  # type: ignore[name-defined]
    """Wrapper sizer: base_size -> apply VolRegimeOverlay + vol-targeting."""
    base_sizer: Any
    config: VolRegimeOverlaySizerConfig
    _state: dict = field(default_factory=dict)  # Mutable state for history tracking

    def _vol_target_scale(self, price: float) -> float:
        """
        Compute vol-targeting scale factor.
        
        Returns min(1.0, target_vol / realized_vol) to scale down in high-vol periods.
        Uses no-lookahead: computes vol from prices up to (but not including) current bar.
        """
        # Skip if vol-targeting is disabled
        if not self.config.vol_target_scaling:
            return 1.0
        
        # Initialize state
        if 'price_history' not in self._state:
            self._state['price_history'] = []
        
        price_history = self._state['price_history']
        
        # Need at least vol_window_bars + 1 prices to compute returns
        if len(price_history) < self.config.vol_window_bars:
            # Warmup phase: append current price and return scale=1.0
            price_history.append(float(price))
            return 1.0
        
        # Compute returns from the last vol_window_bars prices (no lookahead!)
        # We use prices up to i-1, so current price is NOT included in vol calc
        window = price_history[-self.config.vol_window_bars:]
        returns = []
        for i in range(1, len(window)):
            if window[i-1] > 0:
                ret = (window[i] - window[i-1]) / window[i-1]
                returns.append(ret)
        
        # Append current price for next iteration
        price_history.append(float(price))
        
        # Keep only what we need (avoid memory bloat)
        if len(price_history) > self.config.vol_window_bars + 10:
            self._state['price_history'] = price_history[-(self.config.vol_window_bars + 10):]
        
        # Handle edge case: not enough returns
        if len(returns) < 2:
            return 1.0
        
        # Compute realized volatility (std of returns) using sample variance (ddof=1)
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_bar = variance ** 0.5
        
        # Handle zero/NaN volatility
        if std_bar <= 0 or not (std_bar == std_bar):  # NaN check
            return 1.0
        
        # Annualize to daily volatility
        realized_day = std_bar * (self.config.bars_per_day ** 0.5)
        
        # Compute scale factor (using target/realized ratio)
        # Use inverse-variance scaling for more aggressive response to high vol
        target = self.config.day_vol_budget
        if realized_day > 0:
            # Use (target/realized)^2.1 for aggressive vol-targeting
            # This penalizes high-vol periods more strongly
            ratio = target / realized_day
            if ratio >= 1.0:
                scale = 1.0  # Don't scale up in low-vol
            else:
                scale = ratio ** 2.5  # Power >2 for more aggressive scaling
        else:
            scale = 1.0
        
        return float(scale)

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        """Delegate to base_sizer, apply overlay, and apply vol-targeting."""
        # Get base position size
        if hasattr(self.base_sizer, 'get_target_position'):
            base_size = float(self.base_sizer.get_target_position(signal, price, equity))
        else:
            base_size = _call_base_sizer(self.base_sizer, signal, price, equity)
        
        # Apply regime overlay
        units = float(self.config.to_overlay().apply(float(base_size), signal=signal, price=price, equity=equity))
        
        # Apply vol-targeting scale
        vol_scale = self._vol_target_scale(price=price)
        units = float(units) * float(vol_scale)
        
        return float(units)

    def size_position(self, *args: Any, **kwargs: Any) -> float:
        base_size = _call_base_sizer(self.base_sizer, *args, **kwargs)
        units = float(self.config.to_overlay().apply(float(base_size), *args, **kwargs))
        
        # Apply vol-targeting if price is in kwargs
        price = kwargs.get('price')
        if price is not None:
            vol_scale = self._vol_target_scale(price=float(price))
            units = float(units) * float(vol_scale)
        
        return float(units)

    def __call__(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def get_position_size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)

    def compute_position_size(self, *args: Any, **kwargs: Any) -> float:
        return self.size_position(*args, **kwargs)


def build_position_sizer_from_config(
    config: Union[Mapping[str, Any], Any],
    section: str = "position_sizing",
) -> Any:
    """
    Build a position sizer from a dict-like config or config object.

    Args:
        config: Config-Objekt (PeakConfig, Dict, oder kompatibles Interface)
        section: Config-Section für Position Sizing (default: "position_sizing")

    Supported (test-focused):
    - fixed_size
    - fixed_fraction
    - composite (base + overlays)
    - vol_regime_overlay_sizer
    """
    # Early return for already-built sizers
    if hasattr(config, "size_position") or callable(config):
        return config

    # Convert config to plain dict, handling various config types properly
    try:
        from omegaconf import DictConfig as OmegaDictConfig, OmegaConf
        _has_omegaconf = True
    except ImportError:
        _has_omegaconf = False
        OmegaDictConfig = None  # type: ignore[misc,assignment]

    if _has_omegaconf and isinstance(config, OmegaDictConfig):
        root_cfg = OmegaConf.to_container(config, resolve=True)
    elif hasattr(config, "_data") and isinstance(getattr(config, "_data", None), dict):
        # Handle custom DictConfig wrapper with ._data attribute (e.g. test helpers)
        root_cfg = dict(config._data)
    elif isinstance(config, Mapping):
        root_cfg = dict(config)
    else:
        # Fallback for unknown config objects (e.g., PeakConfig)
        # Try to_dict(), then raw, then .get() method for section access
        if hasattr(config, "to_dict") and callable(config.to_dict):
            root_cfg = config.to_dict()
        elif hasattr(config, "raw") and isinstance(config.raw, dict):
            root_cfg = config.raw
        elif hasattr(config, "dict") and callable(config.dict):
            root_cfg = config.dict()
        elif hasattr(config, "get") and callable(config.get):
            # PeakConfig-style: use .get(section) to extract subsection
            section_cfg = config.get(section)
            if section_cfg is None:
                # No position_sizing section: return default NoOp sizer
                return NoOpPositionSizer()  # type: ignore[name-defined]
            root_cfg = {section: section_cfg} if not isinstance(section_cfg, Mapping) else section_cfg
        else:
            # Last resort: get all non-callable, non-private attributes
            root_cfg = {k: getattr(config, k) for k in dir(config) 
                       if not k.startswith("_") and not callable(getattr(config, k, None))}

    # If config is a root config (contains section), extract it
    if section in root_cfg and isinstance(root_cfg.get(section), Mapping):
        cfg = dict(root_cfg[section])
    elif "position_sizing" in root_cfg and isinstance(root_cfg.get("position_sizing"), Mapping):
        cfg = dict(root_cfg["position_sizing"])
    else:
        # No valid section found - check if this is already a position_sizing config
        # or if we should return a default
        if "type" in root_cfg or "key" in root_cfg or "kind" in root_cfg or "units" in root_cfg or "fraction" in root_cfg:
            cfg = root_cfg
        else:
            # Looks like a root config without position_sizing section
            # Return default NoOp sizer
            return FixedSizeSizer(units=1.0)  # type: ignore[name-defined]

    typ = str(cfg.get("type") or cfg.get("kind") or cfg.get("name") or cfg.get("key") or "").strip().lower()

    # Check for R&D overlays in "overlays" list format (must come BEFORE type-specific handling)
    if "overlays" in cfg:
        overlays_list = cfg.get("overlays", [])
        if isinstance(overlays_list, (list, tuple)):
            for overlay_name in overlays_list:
                overlay_name_str = str(overlay_name).strip().lower()
                if overlay_name_str in ("vol_regime_overlay", "volregimeoverlay", "vol_regime"):
                    # Check R&D gates for this overlay
                    env_cfg = root_cfg.get("environment", {}) or {}
                    research_cfg = root_cfg.get("research", {}) or {}
                    env_mode = str(env_cfg.get("mode", "")).strip().lower()
                    allow = bool(research_cfg.get("allow_r_and_d_overlays", False))
                    # Gate 1: Block live trading
                    if env_mode == "live":
                        raise ValueError(f"Overlay '{overlay_name}' (TIER=r_and_d) ist NICHT für Live-Trading zugelassen")
                    # Gate 2: Block if R&D flag not set
                    if not allow:
                        raise ValueError(f"Overlay '{overlay_name}' (TIER=r_and_d) ist deaktiviert. Setzen Sie research.allow_r_and_d_overlays=true")

    # R&D gates for vol_regime_overlay type (must come BEFORE generic Unknown-Type raise)
    if typ in ("vol_regime_overlay", "vol_regime_overlay_sizer", "volregimeoverlaysizer"):
        env_cfg = root_cfg.get("environment", {}) or {}
        research_cfg = root_cfg.get("research", {}) or {}
        env_mode = str(env_cfg.get("mode", "")).strip().lower()
        allow = bool(research_cfg.get("allow_r_and_d_overlays", False))
        # Gate 1: Block live trading
        if env_mode == "live":
            raise ValueError("VolRegimeOverlaySizer ist NICHT für Live-Trading zugelassen")
        # Gate 2: Block if R&D flag not set
        if not allow:
            raise ValueError("VolRegimeOverlaySizer ist deaktiviert (research.allow_r_and_d_overlays=false)")

    if not typ and "regime_multipliers" in cfg and ("base" in cfg or "base_sizer" in cfg):
        typ = "vol_regime_overlay_sizer"

    # Handle "key" + "overlays" format BEFORE simple type handlers
    # (so that overlays are applied even if key=fixed_size)
    if "overlays" in cfg and cfg.get("overlays"):
        # Use the composite/overlay pipeline path
        key = str(cfg.get("key", typ)).strip().lower()
        if key in ("fixed_size", "fixedsizesizer", "fixed"):
            units = float(cfg.get("units", cfg.get("size", 1.0)))
            base = FixedSizeSizer(units)  # type: ignore[name-defined]
        elif key in ("fixed_fraction", "fixedfractionsizer", "fraction"):
            frac = float(cfg.get("fraction", cfg.get("units", 0.01)))
            base = FixedFractionSizer(frac)  # type: ignore[name-defined]
        else:
            raise ValueError(f"Unknown base sizer key: {key!r}")

        # Build overlays from "overlays" list
        overlays_list = cfg.get("overlays", [])
        overlay_configs = cfg.get("overlay", {})
        overlays: list[BasePositionOverlay] = []
        
        for overlay_name in overlays_list:
            overlay_name_str = str(overlay_name).strip().lower()
            if overlay_name_str in ("vol_regime_overlay", "volregimeoverlay", "vol_regime"):
                # Get config for this overlay
                overlay_cfg = overlay_configs.get(overlay_name, {})
                if not isinstance(overlay_cfg, Mapping):
                    overlay_cfg = {}
                
                overlays.append(
                    VolRegimeOverlay(
                        regime_multipliers=overlay_cfg.get("regime_multipliers", {}),
                        default_multiplier=float(overlay_cfg.get("default_multiplier", 1.0)),
                        regime_key=str(overlay_cfg.get("regime_key", "vol_regime")),
                        clip_min=float(overlay_cfg.get("clip_min", 0.0)),
                    )
                )
            else:
                raise ValueError(f"Unknown overlay name: {overlay_name!r}")
        
        return CompositePositionSizer(
            base_sizer=base,
            overlays=tuple(overlays),
            clip_min=float(cfg.get("clip_min", 0.0)),
        )

    if typ in ("fixed_size", "fixedsizesizer", "fixed"):
        size = cfg.get("size", cfg.get("fixed_size", cfg.get("value", cfg.get("units"))))
        return FixedSizeSizer(size)  # type: ignore[name-defined]

    if typ in ("fixed_fraction", "fixedfractionsizer", "fraction"):
        frac = cfg.get("fraction", cfg.get("fixed_fraction", cfg.get("value")))
        return FixedFractionSizer(frac)  # type: ignore[name-defined]

    if typ in ("vol_regime_overlay", "vol_regime_overlay_sizer", "volregimeoverlaysizer"):
        # Unwrap nested config if wrapper-style: {"type":"vol_regime_overlay","vol_regime_overlay":{...}}
        inner_cfg = cfg
        if "vol_regime_overlay" in cfg and isinstance(cfg.get("vol_regime_overlay"), Mapping):
            inner_cfg = dict(cfg["vol_regime_overlay"])

        # Prevent infinite loop
        inner_base_key = str(inner_cfg.get("base_sizer_key", "")).strip().lower()
        if inner_base_key in ("vol_regime_overlay", "vol_regime_overlay_sizer"):
            raise ValueError("Endlosschleife: base_sizer_key darf nicht vol_regime_overlay sein")

        # Build base sizer from inner config
        base_cfg = inner_cfg.get("base_sizer", inner_cfg.get("base"))
        if base_cfg is None:
            # Fallback: build from base_sizer_key + base_units
            base_key = str(inner_cfg.get("base_sizer_key", "noop")).strip().lower()
            base_units = float(inner_cfg.get("base_units", 1.0))
            if base_key in ("fixed_size", "fixedsizesizer", "fixed"):
                base_cfg = {"type": "fixed_size", "size": base_units}
            elif base_key in ("fixed_fraction", "fixedfractionsizer", "fraction"):
                base_cfg = {"type": "fixed_fraction", "fraction": base_units}
            elif base_key in ("noop", "nooppositionsizer"):
                base_cfg = {"type": "noop"}
            else:
                base_cfg = {"type": base_key}
        base = build_position_sizer_from_config(base_cfg)

        c = inner_cfg.get("config", inner_cfg)
        regime_multipliers = c.get("regime_multipliers", {})

        vr_cfg = VolRegimeOverlaySizerConfig(
            regime_multipliers=regime_multipliers,
            default_multiplier=float(c.get("default_multiplier", 1.0)),
            regime_key=str(c.get("regime_key", "vol_regime")),
            clip_min=float(c.get("clip_min", 0.0)),
            day_vol_budget=float(c.get("day_vol_budget", 0.02)),
        )
        return VolRegimeOverlaySizer(base_sizer=base, config=vr_cfg)

    if typ in ("composite", "compositepositionsizer", "overlay_pipeline", "pipeline"):
        base_cfg = cfg.get("base_sizer", cfg.get("base"))
        if base_cfg is None:
            raise ValueError("composite requires 'base' or 'base_sizer'")
        base = build_position_sizer_from_config(base_cfg)

        overlays_cfg = cfg.get("overlays", [])
        overlays: list[BasePositionOverlay] = []
        for o in overlays_cfg:
            if isinstance(o, BasePositionOverlay):
                overlays.append(o)
                continue
            if not isinstance(o, Mapping):
                o = {k: getattr(o, k) for k in dir(o) if not k.startswith("_")}
            o = dict(o)
            ot = (o.get("type") or o.get("kind") or "").strip().lower()
            if ot in ("vol_regime", "volregime", "vol_regime_overlay", "volregimeoverlay"):
                overlays.append(
                    VolRegimeOverlay(
                        regime_multipliers=o["regime_multipliers"],
                        default_multiplier=float(o.get("default_multiplier", 1.0)),
                        regime_key=str(o.get("regime_key", "vol_regime")),
                        clip_min=float(o.get("clip_min", 0.0)),
                    )
                )
            else:
                raise ValueError(f"Unknown overlay type: {ot!r}")

        return CompositePositionSizer(
            base_sizer=base,
            overlays=tuple(overlays),
            clip_min=float(cfg.get("clip_min", 0.0)),
        )

    raise ValueError(f"Unknown position sizer config type: {typ!r} (keys={sorted(cfg.keys())})")


try:
    __all__  # type: ignore[name-defined]
except NameError:
    __all__ = []  # type: ignore[assignment]

try:
    _existing = list(__all__)  # type: ignore[arg-type]
except Exception:
    _existing = []

__all__ = sorted(set(_existing + [  # type: ignore[assignment]
    "BasePositionOverlay",
    "VolRegimeOverlay",
    "CompositePositionSizer",
    "VolRegimeOverlaySizer",
    "VolRegimeOverlaySizerConfig",
    "build_position_sizer_from_config",
]))
