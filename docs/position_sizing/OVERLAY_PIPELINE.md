# Position Sizing Overlay Pipeline

## Konzept

Die **Overlay-Pipeline** ermöglicht es, Position Sizing in zwei unabhängige Komponenten zu trennen:

1. **Base-Sizer**: Bestimmt die Basis-Positionsgröße (z.B. `FixedSizeSizer`, `FixedFractionSizer`)
2. **Overlays**: Kleine Module, die die Units bar-by-bar skalieren/clippen

```
signal → Base-Sizer → raw_units → Overlay₁ → Overlay₂ → ... → final_units
```

### Vorteile

- **Modularität**: Base-Sizer und Overlays sind unabhängig kombinierbar
- **Wiederverwendbarkeit**: Overlays können mit verschiedenen Base-Sizern genutzt werden
- **Keine Strategie-Verschmutzung**: Risk-Management bleibt außerhalb der Trading-Strategie
- **Testbarkeit**: Jedes Modul kann isoliert getestet werden

## Warum Overlays?

Overlays lösen ein wichtiges Problem: **Volatilitäts-Management gehört nicht in die Trading-Strategie.**

### Anti-Pattern (NICHT machen)

```python
# FALSCH: Vol-Regime-Logic in Strategie
def ma_crossover_with_vol_regime(df, params):
    # Trading-Logic
    signals = generate_ma_signals(df, params)

    # Vol-Regime-Logic (GEHÖRT HIER NICHT HIN!)
    vol = df['close'].pct_change().rolling(20).std()
    regime = pd.cut(vol, bins=[0, 0.25, 0.75, 1.0])
    signals = signals * regime_scale_factor  # Strategie-Verschmutzung!

    return signals
```

**Probleme:**
- Strategie und Risk-Management vermischt
- Schwer zu testen
- Nicht wiederverwendbar
- Lookahead-Risiko

### Korrektes Pattern (mit Overlays)

```python
# RICHTIG: Strategie bleibt clean
def ma_crossover(df, params):
    # NUR Trading-Logic
    return generate_ma_signals(df, params)

# Risk-Management via Overlay (außerhalb der Strategie)
```

**Config:**
```toml
[position_sizing]
key = "fixed_size"
units = 10
overlays = ["vol_regime_overlay"]

[position_sizing.overlay.vol_regime_overlay]
day_vol_budget = 0.02
vol_window_bars = 20
```

## Verfügbare Overlays

### VolRegimeOverlay

Skaliert Position Sizing basierend auf:
1. **Vol-Targeting**: Ziel-Volatilität pro Tag
2. **Regime-Dämpfung**: Reduziert Exposure in High-Vol-Phasen
3. **DD-Throttle** (optional): Stoppt Trading bei großem Drawdown

**Status:**
- TIER: `r_and_d` (experimentell)
- IS_LIVE_READY: `False`
- ALLOWED_ENVIRONMENTS: `{offline_backtest, research}`

**Config-Beispiel:**

```toml
[position_sizing]
key = "fixed_size"
units = 10
overlays = ["vol_regime_overlay"]

[position_sizing.overlay.vol_regime_overlay]
# Vol-Targeting
day_vol_budget = 0.02          # 2% Tagesvol als Ziel
vol_window_bars = 20           # Rolling window für realized vol
vol_target_scaling = true      # Vol-Targeting aktivieren

# Regime-Dämpfung
regime_lookback_bars = 100     # Lookback für Quantil-Berechnung
low_vol_threshold = 0.25       # 25. Quantil = low vol
high_vol_threshold = 0.75      # 75. Quantil = high vol
regime_scale_low = 1.0         # Kein Scaling bei low vol
regime_scale_mid = 0.75        # 25% Reduktion bei mid vol
regime_scale_high = 0.5        # 50% Reduktion bei high vol

# Clipping
min_scale = 0.0                # Min. Scale-Faktor
max_scale = 3.0                # Max. Scale-Faktor

# DD-Throttle (optional)
enable_dd_throttle = false     # Aktiviert DD-based Throttle
max_drawdown = 0.25            # Stop bei 25% DD
dd_soft_start = 0.10           # Ab 10% DD linear drosseln

# Annualisierung
bars_per_day = 1               # Für Daily-Daten
trading_days_per_year = 252    # Trading-Tage pro Jahr

[research]
allow_r_and_d_overlays = true  # MUSS true sein!

[environment]
mode = "offline_backtest"      # NICHT "live"!
```

## Gating (Safety-Mechanismus)

Overlays haben ein **dreistufiges Gating-System**:

### Gate A: Research Flag

R&D-Overlays (TIER=`r_and_d`) erfordern explizite Aktivierung:

```toml
[research]
allow_r_and_d_overlays = true
```

**Fehler ohne Flag:**
```
ValueError: Overlay 'vol_regime_overlay' (TIER=r_and_d) ist deaktiviert.
Setze research.allow_r_and_d_overlays=true in config.toml.
```

### Gate B: Live-Block

Overlays mit `IS_LIVE_READY = False` sind für Live-Trading gesperrt:

```toml
[environment]
mode = "live"  # ❌ Fehler!
```

**Fehler:**
```
ValueError: Overlay 'vol_regime_overlay' ist NICHT für Live-Trading zugelassen.
Setze environment.mode='offline_backtest' oder 'research'.
```

### Gate C: Environment-Whitelist

Overlays können erlaubte Environments definieren (`ALLOWED_ENVIRONMENTS`):

```python
ALLOWED_ENVIRONMENTS = {"offline_backtest", "research"}
```

## Usage

### Variante 1: overlays List (empfohlen)

```toml
[position_sizing]
key = "fixed_size"
units = 10
overlays = ["vol_regime_overlay"]

[position_sizing.overlay.vol_regime_overlay]
day_vol_budget = 0.02
vol_window_bars = 20
# ...
```

### Variante 2: Backward-Compat (alt)

```toml
[position_sizing]
key = "vol_regime_overlay"  # Alter Weg

[position_sizing.vol_regime_overlay]
base_sizer_key = "fixed_size"
day_vol_budget = 0.02
# ...
```

**Empfehlung:** Nutze Variante 1 (overlays list) für neue Configs.

## No-Lookahead Garantie

Alle Overlays garantieren **No-Lookahead**:

- `price_history[:-1]` exkludiert current bar für vol-calc
- Returns basieren nur auf vergangenen Preisen
- `shift(1)` bereits in Logik eingebaut

**Beispiel (VolRegimeOverlay):**
```python
# Price History bis t-1 (exklusive current bar!)
past_prices = list(self.price_history)[:-1]

# Returns berechnen (nur Vergangenheit)
returns = [
    (past_prices[i] - past_prices[i-1]) / past_prices[i-1]
    for i in range(1, len(past_prices))
]
```

## Warmup-Verhalten

Overlays haben eine **Warmup-Phase** während der ersten Bars:

- `VolRegimeOverlay`: Benötigt `vol_window_bars + 1` Bars
- Während Warmup: `scale = 1.0` (kein Effekt)
- Base-Sizer-Verhalten bleibt unverändert

**Dokumentiert:**
```python
if len(self.price_history) < min_bars_needed:
    # Warmup-Phase: scale=1 (kein Effekt, dokumentiert)
    return units
```

## Mehrere Overlays kombinieren

Overlays werden **sequenziell** angewendet:

```toml
[position_sizing]
key = "fixed_size"
units = 10
overlays = ["vol_regime_overlay", "session_liquidity_throttle"]
```

**Pipeline:**
```
raw_units = base_sizer(signal=1, ...)  # 10 units
units = vol_regime_overlay.apply(units=10, ...)  # 7.5 units (scaled down)
units = session_liquidity_throttle.apply(units=7.5, ...)  # 5.0 units (throttled)
final_units = 5.0
```

## Eigene Overlays implementieren

```python
from src.core.position_sizing import BasePositionOverlay
from dataclasses import dataclass

@dataclass
class MyCustomOverlay(BasePositionOverlay):
    KEY: str = "my_custom_overlay"
    TIER: str = "core"  # oder "r_and_d"
    IS_LIVE_READY: bool = True

    # Custom-Parameter
    my_param: float = 1.0

    def apply(
        self,
        *,
        units: float,
        signal: int,
        price: float,
        equity: float,
        context: Dict[str, Any],
    ) -> float:
        # Deine Logik hier
        scale = self.my_param
        return units * scale
```

**In Factory registrieren:**
```python
# In build_position_sizer_from_config():
elif overlay_key_str == "my_custom_overlay":
    overlay_inst = MyCustomOverlay(
        my_param=float(get_fn(f"{section}.overlay.my_custom_overlay.my_param", 1.0))
    )
    overlay_instances.append(overlay_inst)
```

## API-Referenz

### BasePositionOverlay

```python
class BasePositionOverlay(ABC):
    KEY: str = ""
    TIER: str = "core"
    IS_LIVE_READY: bool = True
    ALLOWED_ENVIRONMENTS: Optional[set] = None

    @abstractmethod
    def apply(
        self,
        *,
        units: float,
        signal: int,
        price: float,
        equity: float,
        context: Dict[str, Any],
    ) -> float:
        ...
```

### CompositePositionSizer

```python
@dataclass
class CompositePositionSizer(BasePositionSizer):
    base_sizer: BasePositionSizer
    overlays: List[BasePositionOverlay] = field(default_factory=list)

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        raw_units = self.base_sizer.get_target_position(signal, price, equity)
        for overlay in self.overlays:
            raw_units = overlay.apply(
                units=raw_units,
                signal=signal,
                price=price,
                equity=equity,
                context={},
            )
        return raw_units
```

## Next Steps

### Geplante Overlays

1. **SessionLiquidityThrottle**: Reduziert Exposure außerhalb liquider Sessions
2. **NewsShockBrake**: Stoppt Trading bei News-Events
3. **CorrelationOverlay**: Skaliert basierend auf Asset-Korrelationen

### Equity-Context Integration

Aktuell: `context = {}` (leer)

**TODO:** Equity-Context sauber an Sizer/Overlays übergeben:
```python
context = {
    "equity_curve": [...],
    "peak_equity": 10000.0,
    "current_dd": 0.05,
}
```

Damit wird DD-Throttle echt nutzbar (aktuell nur stateful tracking).

### Live-Track Dashboard

**Nur Anzeige, kein Live-Enable!**

Dashboard-Ansicht für Overlay-Metriken:
- Current Vol-Regime (low/mid/high)
- Active Scale-Factor
- DD-Throttle-Status

## Troubleshooting

### Fehler: "Overlay ist deaktiviert"

**Lösung:**
```toml
[research]
allow_r_and_d_overlays = true
```

### Fehler: "Nicht für Live-Trading zugelassen"

**Lösung:**
```toml
[environment]
mode = "offline_backtest"  # oder "research"
```

### Units bleiben unverändert während Warmup

**Erwartetes Verhalten:** Overlays haben Warmup-Phase (scale=1.0).

**Lösung:** Warten bis `vol_window_bars + 1` Bars vergangen sind.

### Overlays werden nicht angewendet

**Check:**
1. `overlays = [...]` in Config gesetzt?
2. Overlay-Key korrekt geschrieben? (case-insensitive)
3. `CompositePositionSizer aktiviert` im Log?

## Referenzen

- Implementierung: `src/core/position_sizing.py`
- Tests: `tests/test_position_sizing_overlay_pipeline.py`
- VolRegimeOverlay-Spec: `docs/position_sizing/VOL_REGIME_OVERLAY_SIZER.md`
