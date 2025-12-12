# Global Macro & GeoRisk Module

> Strukturiertes Framework für makroökonomische Analyse und deren Übersetzung in handelbare Regime für Peak_Trade.

## Überblick

```
┌─────────────────────────────────────────────────────────────────┐
│                    MACRO REGIME SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   docs/macro/                    config/macro_regimes/          │
│   ├── README.md (dieses File)    ├── schema.toml (Definition)  │
│   └── MACRO_BRIEFING_TEMPLATE.md └── current.toml (Aktuell)    │
│                                                                 │
│   Manuelles Briefing ──────────► Maschinenlesbare Config       │
│   (Analyse & Kontext)            (für Peak_Trade System)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Dateien

| Datei | Zweck |
|-------|-------|
| `docs/macro/MACRO_BRIEFING_TEMPLATE.md` | Template für strukturierte Makro-Analysen |
| `config/macro_regimes/schema.toml` | Schema-Definition mit allen gültigen Werten |
| `config/macro_regimes/current.toml` | Aktuelles Makro-Regime (maschinenlesbar) |

## Regime-Hierarchie

Das Macro-Regime-System arbeitet auf einer höheren Abstraktionsebene als die technischen Regimes:

```
┌─────────────────────────────────────────┐
│ MACRO REGIME (dieses Modul)             │  ← Geldpolitik, Geopolitik, Liquidität
│ z.B. fed_pause + tariff_uncertainty     │
├─────────────────────────────────────────┤
│ TECHNICAL REGIME (config/regimes.toml)  │  ← Preis-basiert: Volatilität, Trend
│ z.B. mid_vol + sideways                 │
├─────────────────────────────────────────┤
│ STRATEGY SELECTION                       │  ← Kombiniert beide Layer
│ z.B. mean_reversion mit konserv. Sizing │
└─────────────────────────────────────────┘
```

## Gültige Regime-Tags

### Primäre Regimes (`regime.primary`)

| Tag | Beschreibung |
|-----|--------------|
| `fed_easing` | Fed senkt aktiv Zinsen |
| `fed_pause` | Fed in Wartehaltung |
| `fed_tightening` | Fed erhöht Zinsen |
| `risk_on` | Breiter Risikoappetit |
| `risk_off` | Flight to Safety |
| `risk_neutral` | Keine klare Richtung |
| `liquidity_crunch` | Liquiditätsengpass |
| `credit_stress` | Credit-Spreads weiten |
| `crisis_mode` | Akute Krise |
| `inflation_scare` | Inflationssorgen dominieren |
| `deflation_risk` | Deflationsrisiko |
| `goldilocks` | Ideales Umfeld |

### Sekundäre Regimes (`regime.secondary`)

| Tag | Beschreibung |
|-----|--------------|
| `tariff_uncertainty` | Handels-/Zoll-Unsicherheit |
| `geopolitical_elevated` | Erhöhtes geopolitisches Risiko |
| `election_risk` | Wahlbezogene Unsicherheit |
| `ai_bubble_watch` | Tech/AI-Bewertungsrisiko |
| `china_stress` | China-spezifischer Stress |
| `energy_shock` | Energiepreis-Schock |
| `banking_stress` | Bankensektor-Stress |

## Workflow

### 1. Analyse erstellen

```bash
# Template kopieren und ausfüllen
cp docs/macro/MACRO_BRIEFING_TEMPLATE.md docs/macro/briefings/2025-12-11.md
```

### 2. Config aktualisieren

Nach der Analyse die maschinenlesbare Version updaten:

```bash
# current.toml mit neuen Werten aktualisieren
vim config/macro_regimes/current.toml
```

### 3. Im System nutzen

```python
import tomllib
from pathlib import Path

def load_macro_regime():
    """Lädt aktuelles Makro-Regime."""
    config_path = Path("config/macro_regimes/current.toml")
    with open(config_path, "rb") as f:
        return tomllib.load(f)

regime = load_macro_regime()
print(f"Aktuelles Regime: {regime['regime']['primary']}")
print(f"Max Allocation: {regime['sizing']['max_allocation']:.0%}")
print(f"Strategy Tilt: {regime['strategy_tilt']['prefer']}")
```

## Update-Rhythmus

| Event | Aktion |
|-------|--------|
| Wöchentlich (Sonntag) | Routine-Update falls keine Events |
| Zentralbank-Meeting | Update nach Statement |
| Signifikantes Geopolitik-Event | Sofort-Update |
| Markt-Crash (>5% Daily) | Sofort-Update |

## Integration mit Peak_Trade

Das Macro-Regime kann in der Strategie-Auswahl und beim Position-Sizing berücksichtigt werden:

```python
# Beispiel: Sizing basierend auf Macro-Regime
macro = load_macro_regime()

if macro['regime']['signal'] == 'red':
    position_size *= 0.5  # Halbieren bei roter Ampel
elif macro['regime']['bias'] == 'risk_off':
    position_size *= macro['sizing']['max_allocation']
```

## Quellen-Richtlinien

Für Macro-Briefings nur vertrauenswürdige Quellen nutzen:

- **Zentralbanken:** Fed, EZB, BoJ, BoE Statements
- **Harte Daten:** BLS, Eurostat, offizielle Statistikämter
- **Marktdaten:** Bloomberg, Reuters, CME
- **Nachrichten:** Reuters, FT, WSJ (für Geopolitik)

**Keine** Social-Media-Posts, Crypto-Twitter, oder unverifizierten Quellen.

## Disclaimer

- Alle Szenarien sind Schätzungen, keine Vorhersagen
- Wahrscheinlichkeiten basieren auf qualitativer Einschätzung
- Geopolitik-Timing ist grundsätzlich nicht vorhersagbar
- Dieses System ersetzt keine eigenständige Due Diligence
