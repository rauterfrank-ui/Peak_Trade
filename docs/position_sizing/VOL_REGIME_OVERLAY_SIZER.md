# Vol Regime Overlay Position Sizer

## ⚠️ EMPFOHLENE USAGE: Overlay-Pipeline (NEU)

**Nutze die neue Overlay-Pipeline statt dem monolithischen Sizer:**

```toml
[position_sizing]
key = "fixed_size"
units = 10
overlays = ["vol_regime_overlay"]

[position_sizing.overlay.vol_regime_overlay]
day_vol_budget = 0.02
vol_window_bars = 20
regime_lookback_bars = 100
# ... (siehe Overlay-Pipeline-Doku)

[research]
allow_r_and_d_overlays = true

[environment]
mode = "offline_backtest"
```

**Siehe vollständige Doku:** [`docs/position_sizing/OVERLAY_PIPELINE.md`](./OVERLAY_PIPELINE.md)

---

## Überblick

Der **VolRegimeOverlaySizer** ist ein fortgeschrittener Position-Sizing-Wrapper, der die Position-Größe dynamisch basierend auf:

1. **Realized Volatility** (Vol-Targeting)
2. **Volatility Regime** (Quantil-basierte Klassifizierung)
3. **Optional: Drawdown-Throttle** (progressives Drosseln bei hohen Drawdowns)

anpasst.

**WICHTIG:** Dieser Sizer ist **NUR für Research und Backtests** geeignet. Er ist **NICHT für Live-Trading zugelassen** (siehe Safety Gates weiter unten).

---

## Warum als Position-Sizer (nicht als Strategie)?

Der Vol-Regime-Overlay ist als **Wrapper um einen Base-Sizer** implementiert, nicht als separate Strategie. Das hat mehrere Vorteile:

1. **Separation of Concerns:**
   - Strategie: Generiert Trading-Signale (wann kaufen/verkaufen)
   - Position-Sizer: Bestimmt WIE VIEL gekauft/verkauft wird
   - Vol-Regime-Overlay: Skaliert die Position basierend auf Marktbedingungen

2. **Wiederverwendbarkeit:**
   - Kann mit **jeder** Strategie kombiniert werden
   - Kann mit **jedem** Base-Sizer kombiniert werden (FixedSizeSizer, FixedFractionSizer, etc.)

3. **Modulare Architektur:**
   - Einfach ein-/ausschaltbar ohne Strategie zu ändern
   - Kann mit anderen Risk-Managern (z.B. MaxDrawdownRiskManager) kombiniert werden

---

## Wie es funktioniert

### 1. Vol-Targeting

Der Sizer versucht, eine **konstante Ziel-Volatilität** zu erreichen, indem er die Position-Größe invers zur realisierten Volatilität skaliert:

```
scale_vol = target_vol / realized_vol
```

**Beispiel:**
- Ziel-Tagesvol: 2% (`day_vol_budget = 0.02`)
- Realized Vol (20-Tage-Fenster): 1% → scale_vol = 2.0 → Position **verdoppeln**
- Realized Vol (20-Tage-Fenster): 4% → scale_vol = 0.5 → Position **halbieren**

**Intuition:** In ruhigen Märkten (low vol) können wir größere Positionen eingehen. In volatilen Märkten (high vol) reduzieren wir die Position, um das Risiko konstant zu halten.

### 2. Regime-Dämpfung

Zusätzlich klassifiziert der Sizer den aktuellen Markt in drei Volatilitäts-Regime:

- **Low Vol:** Realized vol <= 25. Perzentil → `regime_factor = 1.0` (keine Dämpfung)
- **Mid Vol:** Realized vol zwischen 25. und 75. Perzentil → `regime_factor = 0.75` (leichte Dämpfung)
- **High Vol:** Realized vol >= 75. Perzentil → `regime_factor = 0.5` (starke Dämpfung)

**Intuition:** In extremen High-Vol-Phasen reduzieren wir die Position zusätzlich, um uns vor unerwarteten Schocks zu schützen.

### 3. Drawdown-Throttle (Optional)

Wenn aktiviert, drosselt der Sizer die Position progressiv basierend auf dem laufenden Drawdown:

- **DD <= 10%** (`dd_soft_start`): `dd_factor = 1.0` (keine Drosselung)
- **DD >= 25%** (`max_drawdown`): `dd_factor = 0.0` (Trading gestoppt)
- **Dazwischen:** Linear interpoliert

**Intuition:** Bei hohen Drawdowns reduzieren wir das Risiko, um die Verluste nicht zu eskalieren.

### Kombinierter Scale-Faktor

```python
final_scale = scale_vol * regime_factor * dd_factor
final_scale = clamp(final_scale, min_scale, max_scale)  # z.B. [0.0, 3.0]

final_units = base_units * final_scale
```

---

## No-Lookahead Garantien

Der Sizer ist **strikt lookahead-free** konstruiert:

1. **Price History:** Nur Preise bis Bar `t-1` werden für Vol-Berechnung genutzt
   - Der **aktuelle** Preis (Bar `t`) wird **NICHT** für vol/regime-Berechnung verwendet
   - Implementiert via `price_history[:-1]` (exklusive letzter Bar)

2. **Returns:** Werden aus vergangenen Preisen berechnet
   - `returns[i] = (price[i] - price[i-1]) / price[i-1]`
   - Nur returns bis Bar `t-1` fließen in realized vol ein

3. **Quantile:** Werden auf **vergangenen** realized vols berechnet
   - Lookback-Window exkludiert die aktuelle realized vol
   - `lookback_vols[-regime_lookback:-1]` (exklusive current)

4. **Drawdown:** Basiert auf **bekannter** Equity
   - Equity bis Bar `t` ist bekannt (wird von Engine übergeben)
   - Peak-Equity wird laufend getrackt

**Testbar:** Siehe `test_no_lookahead_shift` in den Unit-Tests.

---

## Konfiguration

### Minimale Config (mit Safety Gates)

```toml
[position_sizing]
type = "vol_regime_overlay"

[position_sizing.vol_regime_overlay]
base_sizer_key = "fixed_size"
base_units = 0.01
day_vol_budget = 0.02
vol_window_bars = 20
regime_lookback_bars = 100

[research]
allow_r_and_d_overlays = true  # MUSS aktiviert werden!

[environment]
mode = "offline_backtest"  # oder "research" (NICHT "live"!)
```

### Vollständige Config (alle Parameter)

```toml
[position_sizing]
type = "vol_regime_overlay"

[position_sizing.vol_regime_overlay]
# Base-Sizer Config
base_sizer_key = "fixed_size"        # oder "fixed_fraction", "noop"
base_units = 0.01                    # nur für fixed_size
base_fraction = 0.1                  # nur für fixed_fraction

# Vol-Targeting
day_vol_budget = 0.02                # Ziel-Tagesvol (2%)
vol_window_bars = 20                 # Rolling window für realized vol
vol_target_scaling = true            # Aktiviert vol-targeting

# Regime-Klassifizierung
regime_lookback_bars = 100           # Lookback für Quantile
low_vol_threshold = 0.25             # 25. Perzentil = low vol
high_vol_threshold = 0.75            # 75. Perzentil = high vol
regime_scale_low = 1.0               # Multiplikator bei low vol
regime_scale_mid = 0.75              # Multiplikator bei mid vol
regime_scale_high = 0.5              # Multiplikator bei high vol

# Scale Clipping
max_scale = 3.0                      # Max. Leverage
min_scale = 0.0                      # Min. Scale (0 = kein Trading)

# Drawdown-Throttle (Optional)
enable_dd_throttle = false           # Aktiviert DD-Drosselung
dd_soft_start = 0.10                 # Ab 10% DD beginnt Drosselung
max_drawdown = 0.25                  # Bei 25% DD: Trading gestoppt

# Annualisierung
bars_per_day = 1                     # 1 = Daily bars, 24 = Hourly bars
trading_days_per_year = 252          # Trading-Tage pro Jahr

# Numerische Stabilität
eps = 1e-12                          # Epsilon für Division

[research]
allow_r_and_d_overlays = true

[environment]
mode = "offline_backtest"
```

---

## Safety Gates

Der Sizer implementiert **zwei Safety Gates** um versehentliches Live-Trading zu verhindern:

### Gate 1: Environment-Check

```python
if env_mode == "live":
    raise ValueError("VolRegimeOverlaySizer ist NICHT für Live-Trading zugelassen")
```

**Erlaubte Modi:**
- `offline_backtest` ✅
- `research` ✅
- `shadow` ✅ (sofern implementiert)
- `live` ❌ **VERBOTEN**

**Grund:** Der Sizer ist **stateful** und tracked Price/Equity-History bar-by-bar. Dies ist für Backtests geeignet, aber für Live-Trading müsste:
1. State persistent gespeichert werden
2. Rolling-Windows robust bei Market-Gaps funktionieren
3. Latenz-Handling implementiert werden

### Gate 2: Research-Flag

```python
if not cfg.get("research.allow_r_and_d_overlays", False):
    raise ValueError("VolRegimeOverlaySizer ist deaktiviert")
```

**Zweck:** Bewusste Aktivierung erforderlich. Der User muss explizit `allow_r_and_d_overlays=true` setzen.

**Hinweis:** "R&D Overlays" = Research & Development Overlays (experimentelle Features).

---

## Parameter-Tuning

### Vol-Budget

`day_vol_budget` sollte basierend auf **Asset-Klasse** gewählt werden:

- **BTC/Crypto:** 0.02 - 0.04 (2-4% Tagesvol)
- **Stocks:** 0.01 - 0.02 (1-2% Tagesvol)
- **Forex:** 0.005 - 0.01 (0.5-1% Tagesvol)

**Faustregel:** Höheres `day_vol_budget` → Aggressiver (größere Positionen in low-vol)

### Vol-Window

`vol_window_bars` bestimmt die **Reaktionsgeschwindigkeit**:

- **Kurze Windows (10-20 Bars):** Schnelle Anpassung, aber noisier
- **Lange Windows (30-60 Bars):** Glattere Anpassung, aber träger

**Empfehlung:** 20 Bars für Daily, 60 Bars für Hourly

### Regime-Lookback

`regime_lookback_bars` sollte **lang genug** sein, um verschiedene Vol-Regime zu erfassen:

- **Minimum:** 60 Bars
- **Empfohlen:** 100-200 Bars
- **Maximum:** 500 Bars (bei längeren Zeiträumen diminishing returns)

### Regime-Scales

Die drei Multiplikatoren (`regime_scale_low/mid/high`) kontrollieren die **Aggressivität**:

**Konservativ:**
```toml
regime_scale_low = 0.8
regime_scale_mid = 0.6
regime_scale_high = 0.3
```

**Moderat (Default):**
```toml
regime_scale_low = 1.0
regime_scale_mid = 0.75
regime_scale_high = 0.5
```

**Aggressiv:**
```toml
regime_scale_low = 1.2
regime_scale_mid = 1.0
regime_scale_high = 0.7
```

---

## Interaktion mit anderen Komponenten

### 1. Mit Base-Sizer

Der Overlay **wrappet** einen Base-Sizer:

```python
base_sizer = FixedSizeSizer(units=0.01)
overlay = VolRegimeOverlaySizer(base_sizer=base_sizer, config=cfg)

# Bar-by-bar:
raw_units = base_sizer.get_target_position(signal=1, price=50000, equity=10000)
# -> raw_units = 0.01

final_units = overlay.get_target_position(signal=1, price=50000, equity=10000)
# -> final_units = raw_units * scale (z.B. 0.01 * 2.0 = 0.02)
```

### 2. Mit RiskManager

Der **RiskManager** läuft **NACH** dem PositionSizer in der Engine:

```
Signal → PositionSizer (inkl. Overlay) → Units → RiskManager → Adjusted Units
```

**Beispiel:**
1. VolRegimeOverlaySizer: `units = 0.02`
2. MaxDrawdownRiskManager: Bei DD > 25% → `adjusted_units = 0.0`

**Hinweis:** DD-Throttle im Overlay und MaxDrawdownRiskManager sind **komplementär**:
- Overlay: **Progressives** Drosseln (linear)
- RiskManager: **Harte** Grenze (on/off)

**Empfehlung:** Nutze **entweder** DD-Throttle im Overlay **oder** MaxDrawdownRiskManager, nicht beides (sonst doppelte Drosselung).

### 3. Mit Strategien

Der Overlay ist **strategie-agnostisch**. Er funktioniert mit **jeder** Strategie, die Signale erzeugt:

```toml
# Beispiel: MA-Crossover mit Vol-Overlay
[strategy]
name = "ma_crossover"
fast_period = 10
slow_period = 30

[position_sizing]
type = "vol_regime_overlay"
# ... (Overlay-Config)
```

---

## Warmup-Phase

Der Sizer benötigt eine **Warmup-Phase**, um genug Daten zu sammeln:

```
min_bars_needed = vol_window_bars + 1  # +1 für pct_change
```

**Während Warmup:**
- `scale = 1.0` (Overlay inaktiv)
- Base-Sizer-Units werden unverändert durchgereicht

**Beispiel:**
- `vol_window_bars = 20` → Warmup = 21 Bars
- Erste 21 Bars: `final_units = raw_units`
- Ab Bar 22: `final_units = raw_units * scale`

**Hinweis:** Regime-Klassifizierung braucht zusätzlich `regime_lookback_bars` (z.B. 100), aber defaulted zu `mid-regime` bis genug Daten vorhanden sind.

---

## Beispiel-Szenarien

### Szenario 1: Low-Vol-Phase

```
Realized Vol: 1% (25. Perzentil)
Target Vol: 2%

scale_vol = 2.0 / 1.0 = 2.0
regime_factor = 1.0 (low vol)
dd_factor = 1.0 (kein DD)

final_scale = 2.0 * 1.0 * 1.0 = 2.0

→ Position wird VERDOPPELT
```

### Szenario 2: High-Vol-Phase

```
Realized Vol: 4% (80. Perzentil)
Target Vol: 2%

scale_vol = 2.0 / 4.0 = 0.5
regime_factor = 0.5 (high vol)
dd_factor = 1.0 (kein DD)

final_scale = 0.5 * 0.5 * 1.0 = 0.25

→ Position wird auf 25% REDUZIERT
```

### Szenario 3: Drawdown-Phase

```
Realized Vol: 2% (mid)
Target Vol: 2%
Drawdown: 15% (zwischen dd_soft_start=10% und max_drawdown=25%)

scale_vol = 1.0
regime_factor = 0.75 (mid vol)
dd_factor = 1.0 - (15% - 10%) / (25% - 10%) = 0.67

final_scale = 1.0 * 0.75 * 0.67 = 0.50

→ Position wird auf 50% REDUZIERT
```

---

## Limitationen & Future Work

### Aktuelle Limitationen

1. **Nur Single-Asset:**
   - Berechnet Vol basierend auf einem Preis-Feed
   - Kein Portfolio-Vol-Targeting (Cross-Asset-Korrelationen)

2. **Symmetrisch:**
   - Long und Short werden gleich behandelt
   - Kein asymmetrisches Vol-Targeting (z.B. mehr Risk bei Longs)

3. **Realized Vol Only:**
   - Nutzt nur historische Vol (backward-looking)
   - Kein Implied Vol oder Forward-Looking-Estimatoren

4. **Stateful Bar-by-Bar:**
   - Nicht parallelisierbar
   - Nicht für Vektor-Backtests geeignet

### Mögliche Erweiterungen

1. **Rough Vol Estimator:**
   - Nutze Rough-Volatility-Modelle für bessere Vol-Forecasts
   - Implementierung als separater Estimator (siehe `docs/TECH_DEBT_BACKLOG.md`)

2. **Multi-Asset Vol-Budgeting:**
   - Portfolio-weites Vol-Targeting
   - Cross-Asset-Korrelations-Adjustments

3. **Asymmetrisches Targeting:**
   - Separate Vol-Budgets für Long/Short
   - Skew-Adjustments (Put-Skew bei Equity)

4. **CompositeSizer:**
   - Generalisierung zu `CompositeSizer(base, overlays=[])`
   - Mehrere Overlays kombinierbar (z.B. Vol + Sentiment + Seasonality)

5. **Vectorized Overlay:**
   - Refactor zu vektorisierter Berechnung
   - Schnellere Backtests (aber kompliziertere No-Lookahead-Handling)

---

## Testing

Der Sizer wird durch umfangreiche Unit-Tests abgedeckt:

1. **Safety Gates:**
   - `test_overlay_blocks_without_research_flag`
   - `test_overlay_blocks_in_live_env`

2. **Vol-Targeting:**
   - `test_vol_target_scales_down_in_high_vol`

3. **No-Lookahead:**
   - `test_no_lookahead_shift` (kritischster Test!)

4. **DD-Throttle:**
   - `test_dd_throttle_when_equity_available`

**Run Tests:**
```bash
python -m pytest tests/test_vol_regime_overlay_sizer.py -v
```

---

## Referenzen

- [Overlay Pipeline](OVERLAY_PIPELINE.md)
- BacktestEngine: `src/backtest/engine.py` (wie Sizer aufgerufen wird; lines 424-440)
- BasePositionSizer: `src/core/position_sizing.py` (lines 14-31)

---

## Changelog

- **2025-01-XX:** Initial implementation (Vol-Targeting + Regime + DD-Throttle)
- **Future:** Rough Vol Estimator, Multi-Asset Support

---

**Autor:** Claude Code (generated)
**Letzte Änderung:** 2025-01-XX
