# R&D-Strategie-Welle v2 – Research-Presets

**Status:** 🔜 Vorbereitung (Scope & Presets definiert)
**Abhängigkeit:** R&D-Strategie-Welle v1 abgeschlossen (siehe `PEAK_TRADE_STATUS_OVERVIEW.md`)

---

## 1. Ziel & Scope

R&D-Strategie-Welle v2 baut auf den implementierten R&D-Modulen aus Welle v1 auf und definiert **konkrete Research-Presets** für systematische Backtests, Parameter-Sweeps und Regime-Analysen.

**Fokus:**
- „High-Concept"-Ansätze von Armstrong, Ehlers, López de Prado (+ optional El Karoui)
- Strukturierte Research-Experimente mit definierten Hypothesen
- Vergleichbarkeit der Ergebnisse über standardisierte Metriken

> **⚠️ WICHTIG:** Alle Presets sind ausschließlich für **Offline-Research** gedacht.
> Kein Live-/Shadow-/Testnet-Trading. Keine Integration in Phase 80/81 (Live-Track).

---

## 2. Kandidaten & Research-Fokus

### 2.1 Martin Armstrong – Zyklen & Timing

**Modul:** `src/strategies/armstrong/armstrong_cycle_strategy.py`

**Forschungsfokus:**
- Economic Confidence Model (ECM) – 8.6-Jahre-Zyklus (π × 1000 Tage)
- Langfrist-Macro-Zyklen und deren Übertragbarkeit auf Crypto-Märkte
- Cycle-Peak/Trough-Timing für Entry/Exit

**Hypothesen:**
1. ECM-Zyklen korrelieren mit BTC-Halving-Zyklen
2. Cycle-Timing verbessert Sharpe vs. Buy-and-Hold
3. Multi-Cycle-Overlay (kurz + lang) reduziert Drawdown

**Offene Fragen:**
- Wie robust sind die Zyklen bei Regime-Wechseln (2020 COVID, 2022 Crash)?
- Welche Adaptions-Mechanismen sind nötig für kürzere Timeframes (1h, 4h)?

### 2.2 John Ehlers – Signal-Processing & Filter

**Modul:** `src/strategies/ehlers/ehlers_cycle_filter_strategy.py`

**Forschungsfokus:**
- Digital Signal Processing (DSP) Techniken
- Super Smoother Filter (weniger Lag als EMA)
- Bandpass-Filter für Cycle-Isolation
- Hilbert Transform für Phase-Messung
- MESA (Maximum Entropy Spectral Analysis)

**Hypothesen:**
1. Super Smoother reduziert Whipsaw-Trades vs. Standard-MA
2. Bandpass-Filter isoliert dominante Zyklen zuverlässiger als FFT
3. Phase-basierte Entries verbessern Timing in Trending-Märkten

**Offene Fragen:**
- Optimale Cutoff-Frequenzen für verschiedene Timeframes?
- Kombination mit Vol-Regime-Filter (Ehlers + Gatheral/Cont)?

### 2.3 Marcos López de Prado – ML & Feature-Engineering

**Modul:** `src/strategies/lopez_de_prado/meta_labeling_strategy.py`

**Forschungsfokus:**
- Meta-Labeling (Primär-Signal + Meta-Classifier)
- Triple-Barrier-Methode für Label-Generierung
- Fractional Differencing für Stationarität (konzeptionell)
- Feature-Importance und Modell-Interpretierbarkeit

**Hypothesen:**
1. Meta-Labeling verbessert Precision ohne Recall-Verlust
2. Triple-Barrier-Labels sind robuster als feste Horizonte
3. Fractional Differencing erhält mehr Information als Standard-Differencing

**Offene Fragen:**
- Welche Primär-Signale (RSI, MA, Breakout) profitieren am meisten von Meta-Labeling?
- Wie verhält sich das Modell bei Out-of-Sample-Daten?

### 2.4 (Optional) Nicole El Karoui – Stochastische Volatilität

**Modul:** `src/strategies/el_karoui/el_karoui_vol_model_strategy.py`

**Forschungsfokus:**
- Stochastische Volatilitätsmodelle
- Lokale Volatilität und Smile-Dynamik
- Vol-Regime-Klassifikation

**Hypothesen:**
1. Stoch-Vol-Modelle verbessern Vol-Forecasts vs. GARCH
2. Vol-Smile-Dynamik enthält prädiktive Information
3. El-Karoui-Modell + Gatheral-Overlay = robustere Vol-Signale

**Status:** Niedrigere Priorität – erst nach Armstrong/Ehlers/Lopez-Presets

---

## 3. R&D-Strategy-Presets (v2)

### 3.1 Armstrong-Presets

| Preset-ID | Beschreibung | Märkte | Timeframes | Fokus-Metriken |
|-----------|--------------|--------|------------|----------------|
| `armstrong_ecm_btc_longterm_v1` | ECM-Zyklus auf BTC (Langfrist) | BTC/USDT | 1d, 1w | Sharpe, MaxDD, Cycle-Hit-Rate |
| `armstrong_multi_cycle_scan_v1` | Multi-Cycle-Overlay (kurz + lang) | BTC, ETH | 4h, 1d | Drawdown-Reduktion, Win-Rate |

**Parameter-Skizze:**
```toml
[preset.armstrong_ecm_btc_longterm_v1]
strategy = "armstrong_cycle"
tier = "r_and_d"
enabled = false
experimental = true
markets = ["BTC/USDT"]
timeframes = ["1d", "1w"]
parameters = { cycle_period_days = 3141, phase_offset = 0.0, entry_threshold = 0.8 }
```

### 3.2 Ehlers-Presets

| Preset-ID | Beschreibung | Märkte | Timeframes | Fokus-Metriken |
|-----------|--------------|--------|------------|----------------|
| `ehlers_super_smoother_v1` | Super Smoother vs. EMA Vergleich | BTC, ETH | 1h, 4h | Lag, Whipsaw-Rate, Sharpe |
| `ehlers_bandpass_cycle_v1` | Bandpass-Filter Cycle-Isolation | BTC/USDT | 4h, 1d | Cycle-Purity, Signal-Noise |
| `ehlers_hilbert_phase_v1` | Hilbert Transform Phase-Timing | BTC, ETH | 1h, 4h | Entry-Timing, Phase-Accuracy |

**Parameter-Skizze:**
```toml
[preset.ehlers_super_smoother_v1]
strategy = "ehlers_cycle_filter"
tier = "r_and_d"
enabled = false
experimental = true
markets = ["BTC/USDT", "ETH/USDT"]
timeframes = ["1h", "4h"]
parameters = { filter_type = "super_smoother", period = 20, cutoff_period = 10 }
```

### 3.3 Lopez de Prado-Presets

| Preset-ID | Beschreibung | Märkte | Timeframes | Fokus-Metriken |
|-----------|--------------|--------|------------|----------------|
| `lopez_meta_labeling_rsi_v1` | Meta-Labeling mit RSI als Primär-Signal | BTC/USDT | 1h, 4h | Precision, Recall, F1 |
| `lopez_triple_barrier_scan_v1` | Triple-Barrier Label-Analyse | BTC, ETH | 4h, 1d | Label-Distribution, Barrier-Hits |
| `lopez_feature_importance_v1` | Feature-Importance-Analyse | BTC/USDT | 4h | Top-Features, SHAP-Values |

**Parameter-Skizze:**
```toml
[preset.lopez_meta_labeling_rsi_v1]
strategy = "meta_labeling"
tier = "r_and_d"
enabled = false
experimental = true
markets = ["BTC/USDT"]
timeframes = ["1h", "4h"]
parameters = { primary_signal = "rsi_reversion", meta_model = "random_forest", barrier_width = 0.02 }
```

### 3.4 El Karoui-Presets (Optional)

| Preset-ID | Beschreibung | Märkte | Timeframes | Fokus-Metriken |
|-----------|--------------|--------|------------|----------------|
| `el_karoui_stoch_vol_v1` | Stoch-Vol-Modell Baseline | BTC/USDT | 4h, 1d | Vol-Forecast-Error, MAE |

---

## 4. Abgrenzung & Safety

### 4.1 Nutzungsregeln

| Erlaubt | Nicht erlaubt |
|---------|---------------|
| ✅ Offline-Backtests | ❌ Shadow-Mode |
| ✅ Research-Pipeline (Sweeps, MC) | ❌ Testnet-Trading |
| ✅ Paper-Mode (nur Analyse) | ❌ Live-Trading |
| ✅ Akademische Analysen | ❌ Phase-80/81-Integration |

### 4.2 Technische Absicherung

- **Strategy-Tiering:** Alle Presets haben `tier = "r_and_d"` und `allow_live = false`
- **Feature-Flags:** `enabled = false` und `experimental = true` in Preset-Config
- **Registry:** R&D-Strategien werden nur mit explizitem Flag geladen
- **Dashboard:** Nur mit `?include_research=true` sichtbar
- **CI/Tests:** R&D-Presets werden in separaten Test-Dateien getestet, nicht in Standard-CI

### 4.3 Code-Isolation

```
src/strategies/
├── armstrong/          # R&D – Welle v1
├── ehlers/             # R&D – Welle v1
├── el_karoui/          # R&D – Welle v1
├── bouchaud/           # R&D – Welle v1
├── gatheral_cont/      # R&D – Welle v1
├── lopez_de_prado/     # R&D – Welle v1
└── (core/aux/legacy Strategien)

config/
├── strategy_tiering.toml           # Tiering-Definitionen
└── r_and_d_presets.toml            # R&D-Presets (Welle v2) ← NEU
```

---

## 5. Nächste Schritte / Einstiegskriterien

### 5.1 Wann ist ein R&D-Preset „reif"?

| Kriterium | Beschreibung |
|-----------|--------------|
| **Backtest-Coverage** | Min. 2 Jahre Daten, mehrere Regime (Bull/Bear/Sideways) |
| **Robustheit** | Walk-Forward + Monte-Carlo mit akzeptablen Ergebnissen |
| **Dokumentation** | Hypothese, Methodik, Ergebnisse dokumentiert |
| **Review** | Code-Review durch zweite Person |

### 5.2 Übergang zu Strategy-Library (Post-R&D)

1. **Phase 40+ Integration:** R&D-Preset wird in `core` oder `aux` Tier überführt
2. **Strategy-Tiering Update:** `tier = "aux"` oder `tier = "core"` nach Review
3. **Demo-/Showcase-Integration:** Optional in Live-Track-Demos (nur Shadow-Mode)

### 5.3 Verweis auf Einstiegskriterien

Siehe `docs/PEAK_TRADE_STATUS_OVERVIEW.md` → Abschnitt „Einstiegskriterien für R&D-Strategie-Welle v2":

- Abgeschlossene R&D-Experimente mit Welle v1
- Konkrete Gaps/Hypothesen aus Welle-v1-Ergebnissen
- Klar umrissener Scope für neue Baustein-Kategorien
- Welle v1 stabil (keine offenen Blocker)

---

## 6. Änderungshistorie

| Datum | Änderung |
|-------|----------|
| 2025-12-08 | Initiale Version – Scope & Presets für Armstrong/Ehlers/Lopez definiert |

---

**Built for Research – Not for Live Trading**
