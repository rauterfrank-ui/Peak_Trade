# Macro Briefing Template

> **Zweck:** Strukturierte Vorlage für Global Macro & GeoRisk Analysen.  
> **Update-Rhythmus:** Wöchentlich oder bei signifikanten Events.  
> **Maschinenlesbare Version:** `config/macro_regimes/current.toml`

---

## 🚦 SIGNAL-AMPEL

<!-- Eine Zeile: Aktuelles Gesamtbild -->

| Status | Regime | Bias |
|--------|--------|------|
| 🟡 GELB | `[regime_tag]` | Risk-Neutral / Risk-On / Risk-Off |

**Kurzfassung (1 Satz):**  
_[Zusammenfassung der aktuellen Lage in einem Satz]_

---

## 📊 TOP-3 TREIBER

<!-- Maximal 3 Punkte, die gerade die Märkte bewegen -->

| # | Treiber | Fakt (harte Daten) | Marktimpact |
|---|---------|-------------------|-------------|
| 1 | **[Treiber 1]** | [Konkrete Zahl/Event] | [Auswirkung] |
| 2 | **[Treiber 2]** | [Konkrete Zahl/Event] | [Auswirkung] |
| 3 | **[Treiber 3]** | [Konkrete Zahl/Event] | [Auswirkung] |

---

## 🎯 SZENARIEN

| | Szenario | Trigger | Wahrsch. |
|-|----------|---------|----------|
| ⚖️ | **Base:** [Beschreibung] | [Auslöser] | ~X% |
| 🟢 | **Bull:** [Beschreibung] | [Auslöser] | ~Y% |
| 🔴 | **Bear:** [Beschreibung] | [Auslöser] | ~Z% |

### Regime-Wechsel-Trigger

Beobachte diese Indikatoren für potentielle Regime-Shifts:

- **→ Risk-Off:** [Trigger, z.B. VIX >25 sustained]
- **→ Risk-On:** [Trigger, z.B. Fed-Pivot]
- **→ Crisis:** [Trigger, z.B. Geopolitische Eskalation]

---

## ⚙️ PEAK_TRADE ACTIONS

```toml
# Direkt kopierbar nach config/macro_regimes/current.toml

[regime]
primary = "[regime_tag]"           # z.B. "fed_pause", "risk_off", "liquidity_crunch"
secondary = "[optional_tag]"       # z.B. "tariff_uncertainty"
signal = "yellow"                  # green / yellow / red
bias = "neutral"                   # risk_on / neutral / risk_off

[sizing]
max_allocation = 0.70              # Prozent des Max-Kapitals (0.0 - 1.0)
rationale = "[Begründung]"

[watchlist]
primary = ["BTC", "ETH", "GOLD"]   # Hauptfokus
secondary = ["EUR/USD", "VIX"]     # Sekundär beobachten
avoid = []                         # Aktuell meiden

[strategy_tilt]
prefer = "mean_reversion"          # mean_reversion / trend_following / balanced
rationale = "[Begründung]"
```

---

## 📅 Kontext & Quellen

**Briefing-Datum:** YYYY-MM-DD  
**Nächstes Update:** [Datum oder "bei Event"]  
**Analyst:** [Name/Rolle]

### Datenquellen (für Nachvollziehbarkeit)

- Fed: [Link/Statement]
- EZB: [Link/Statement]
- Geopolitik: [Quellen]

### Unsicherheits-Disclaimer

| Kategorie | Sicherheit |
|-----------|------------|
| Zinssätze, Inflationsdaten | ✅ Harte Daten |
| Szenario-Wahrscheinlichkeiten | ⚠️ Schätzung |
| Geopolitik-Timing | ❌ Nicht vorhersagbar |

---

## Changelog

| Datum | Änderung |
|-------|----------|
| YYYY-MM-DD | Initial |
