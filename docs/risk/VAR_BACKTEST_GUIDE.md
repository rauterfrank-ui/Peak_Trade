# VaR Backtest Guide – Operator Manual


## Authority and epoch note

This guide preserves historical and component-level VaR backtest operator context. Phrases such as `production-ready`, deployment, live-gate, or operational readiness are not, by themselves, current Master V2 approval, Doubleplay authority, First-Live readiness, operator authorization, or permission to route orders into any live capital path.

VaR backtesting can support risk review, diagnostics, and promotion discussions, but it is not a standalone promotion gate. Any live or first-live promotion remains governed by current gate, evidence, and signoff artifacts, Scope / Capital Envelope boundaries, Risk / Exposure Caps, Safety / Kill-Switches, and staged Execution Enablement. This note is docs-only and changes no runtime behavior.

**Module:** `src/risk_layer/var_backtest/`  
**Purpose:** Research & Backtesting Only  
**Status:** ✅ Production Ready (Backtest/Research)

---

## 🎯 Überblick

Dieses Modul implementiert statistische Backtests für VaR-Modelle, insbesondere den **Kupiec Proportion of Failures (POF) Test**. Es dient ausschließlich der **historischen Validierung** von VaR-Schätzungen und ist **NICHT** für Live-Trading-Validierung konzipiert.

### Wann sollten Sie dieses Tool verwenden?

✅ **JA - Verwenden Sie VaR Backtest für:**
- Validierung neuer VaR-Modelle vor Deployment
- Periodische Modell-Reviews (z.B. monatlich/quartalsweise)
- Forschung und Entwicklung neuer VaR-Methoden
- Regulatorische Berichterstattung (Basel III Compliance)
- A/B Testing verschiedener VaR-Ansätze

❌ **NEIN - Verwenden Sie NICHT VaR Backtest für:**
- Echtzeit-Risikobewertung im Live-Trading
- Order-Validierung vor Execution
- Dynamische Positionsgrößenänderungen
- Automatisierte Trading-Entscheidungen

> **Für Live-Trading:** Siehe `src/live/live_gates.py` und risk enforcement modules

---

## 📋 Schnellstart

### Installation / Setup

Das Modul ist Teil von Peak_Trade und erfordert keine zusätzlichen Dependencies:

```bash
# Stelle sicher, dass du im Peak_Trade venv bist
cd /Users/frnkhrz/Peak_Trade
source venv/bin/activate  # oder entsprechender Pfad

# Teste Installation
python3 -m pytest tests/risk_layer/var_backtest/ -v
```

### Einfacher Test (Kommandozeile)

```bash
# Einzelnes Symbol backtesten
python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --confidence 0.99 \
  --output reports/var_backtest/btc_2024.json

# Ausgabe anschauen
cat reports/var_backtest/btc_2024.json | jq .summary
```

### Programmatic Usage (Python)

```python
from src.risk_layer.var_backtest import VaRBacktestRunner
import pandas as pd

# Lade deine Daten (Returns & VaR-Schätzungen)
returns = pd.Series([...])  # Deine täglichen Returns
var_estimates = pd.Series([...])  # Deine VaR-Schätzungen (negativ!)

# Initialisiere Runner
runner = VaRBacktestRunner(
    confidence_level=0.99,  # 99% VaR
    significance_level=0.05,  # 5% Test-Signifikanz
    min_observations=250,  # Basel Minimum
)

# Führe Backtest durch
result = runner.run(
    returns=returns,
    var_estimates=var_estimates,
    symbol="BTC-EUR"
)

# Ergebnisse prüfen
print(result.summary())
print(f"Model Valid: {result.is_valid}")
```

---

## 🔬 Kupiec POF Test - Praktische Interpretation

### Was testet der Kupiec POF?

Der Kupiec Test prüft, ob die **Häufigkeit von VaR-Überschreitungen** mit der erwarteten Häufigkeit übereinstimmt.

**Beispiel (99% VaR):**
- Erwartung: 1% der Tage sollten VaR-Überschreitungen (Violations) sein
- Bei 250 Handelstagen: ~2.5 Violations erwartet
- Test prüft: Sind tatsächlich ~2-3 Violations aufgetreten?

### Ergebnis-Interpretation

| Ergebnis | Bedeutung | Handlungsempfehlung |
|----------|-----------|---------------------|
| **ACCEPT** | Modell korrekt kalibriert | ✅ Modell kann verwendet werden |
| **REJECT** | Zu viele/wenige Violations | ⚠️ Modell rekalibrieren/anpassen |
| **INCONCLUSIVE** | Zu wenig Daten | 📊 Mehr Daten sammeln (min. 250 Tage) |

### Häufige Szenarien

#### Szenario 1: Zu viele Violations (Underestimation)

```
VaR Backtest: BTC-EUR (2024)
Observations:   250
Violations:     15  (6.0%)
Expected:       2.5 (1.0%)
Result:         REJECT
```

**Problem:** VaR unterschätzt das Risiko (zu optimistisch)  
**Lösung:**
- Erhöhe VaR-Schätzung (z.B. höhere Volatilitäts-Scaling)
- Wechsel zu konservativerer Methode (Historical → Parametric)
- Prüfe ob extreme Events besser modelliert werden müssen

#### Szenario 2: Zu wenige Violations (Overestimation)

```
VaR Backtest: ETH-EUR (2024)
Observations:   500
Violations:     0   (0.0%)
Expected:       5.0 (1.0%)
Result:         REJECT
```

**Problem:** VaR überschätzt das Risiko (zu konservativ)  
**Lösung:**
- Senke VaR-Schätzung (Capital ineffizient)
- Prüfe ob Volatilität overestimated wird
- Wechsel zu weniger konservativer Methode

#### Szenario 3: Perfekte Kalibrierung

```
VaR Backtest: BTC-EUR (2024)
Observations:   365
Violations:     4   (1.1%)
Expected:       3.6 (1.0%)
Result:         ACCEPT
```

**Interpretation:** Modell gut kalibriert ✅  
**Nächste Schritte:** Weiter monitoren, periodisch revalidieren

---

## ⚙️ CLI Reference

### Basis-Kommando

```bash
python3 scripts/risk/run_var_backtest.py \
  --symbol SYMBOL \
  [OPTIONS]
```

### Optionen

| Option | Typ | Default | Beschreibung |
|--------|-----|---------|--------------|
| `--symbol` | str | **required** | Symbol (z.B. BTC-EUR) |
| `--start` | date | all | Start-Datum (YYYY-MM-DD) |
| `--end` | date | all | End-Datum (YYYY-MM-DD) |
| `--confidence` | float | 0.99 | VaR-Konfidenzniveau |
| `--significance` | float | 0.05 | Test-Signifikanzniveau |
| `--min-observations` | int | 250 | Minimum Beobachtungen |
| `--output` | path | - | Output-Datei (JSON) |
| `--ci-mode` | flag | - | CI-freundlicher Output |
| `--fail-on-reject` | flag | - | Exit Code 1 bei REJECT |
| `--fail-on-inconclusive` | flag | - | Exit Code 2 bei INCONCLUSIVE |

### Exit Codes

| Code | Bedeutung | Verwendung |
|------|-----------|------------|
| 0 | ACCEPT | Modell OK |
| 1 | REJECT | Modell fehlkalibriert |
| 2 | INCONCLUSIVE | Zu wenig Daten |
| 3 | ERROR | Ausführungsfehler |

### Beispiele

#### Standard-Backtest

```bash
python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output reports/var_backtest/btc_eur_2024.json
```

#### CI Integration

```bash
# Exit Code basiert auf Ergebnis
python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --ci-mode \
  --fail-on-reject \
  --fail-on-inconclusive

# In CI-Pipeline
if [ $? -ne 0 ]; then
  echo "VaR Model validation failed!"
  exit 1
fi
```

#### Batch Processing

```bash
# Mehrere Symbole testen
for symbol in BTC-EUR ETH-EUR ADA-EUR; do
  python3 scripts/risk/run_var_backtest.py \
    --symbol $symbol \
    --output reports/var_backtest/${symbol}_$(date +%Y%m%d).json
done
```

---

## 📊 Output Format (JSON)

```json
{
  "meta": {
    "generated_at": "2024-12-27T10:30:00Z",
    "test_type": "kupiec_pof"
  },
  "summary": {
    "symbol": "BTC-EUR",
    "period": {
      "start": "2024-01-01T00:00:00",
      "end": "2024-12-31T00:00:00"
    },
    "result": "accept",
    "is_valid": true
  },
  "statistics": {
    "n_observations": 365,
    "n_violations": 4,
    "confidence_level": 0.99,
    "expected_violation_rate": 0.01,
    "observed_violation_rate": 0.0109,
    "violation_ratio": 1.09,
    "lr_statistic": 0.1234,
    "p_value": 0.7253,
    "critical_value": 3.8415,
    "significance_level": 0.05
  },
  "violations": {
    "dates": [
      "2024-03-15T00:00:00",
      "2024-06-22T00:00:00",
      "2024-09-10T00:00:00",
      "2024-11-05T00:00:00"
    ],
    "count": 4
  }
}
```

---

## 🛠️ Troubleshooting

### Problem: "Insufficient Data (INCONCLUSIVE)"

**Ursache:** Weniger als min_observations (default: 250 Tage)

**Lösung:**
- Sammle mehr historische Daten
- Oder: senke `--min-observations` (nicht empfohlen für Produktion)

### Problem: "Zu viele Violations bei ruhigen Märkten"

**Ursache:** VaR-Modell nicht adaptiv genug

**Lösung:**
- Verwende rolling window für Volatilität
- Implementiere Regime-Switching VaR

### Problem: "Konsistent REJECT, aber Modell funktioniert in Live"

**Ursache:** Möglicherweise Lookback-Bias oder Daten-Qualität

**Lösung:**
- Prüfe Daten-Alignment (Returns vs. VaR timestamps)
- Stelle sicher dass VaR-Schätzungen ex-ante sind (nicht ex-post!)
- Überprüfe Sign Conventions (negativ = Verlust)

---

## 📚 Best Practices

### 1. Periodisches Revalidieren

```python
# Empfohlen: Monatliches Revalidieren
# Beispiel: Jeden Monatsanfang letztes Jahr testen

from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=365)

result = runner.run(returns, var_estimates, symbol="BTC-EUR")

if not result.is_valid:
    send_alert(f"VaR Model validation failed for BTC-EUR")
```

### 2. Rolling Window Backtests

```python
# Teste Stabilität über Zeit
for start in pd.date_range("2023-01-01", "2024-01-01", freq="M"):
    end = start + pd.DateOffset(months=12)
    window_result = runner.run(
        returns[start:end],
        var_estimates[start:end]
    )
    print(f"{start.date()}: {window_result.kupiec.result.value}")
```

### 3. Multi-Confidence-Level Testing

```python
# Teste mehrere Konfidenzniveaus
for confidence in [0.95, 0.99, 0.995]:
    runner = VaRBacktestRunner(confidence_level=confidence)
    result = runner.run(returns, var_estimates)
    print(f"{confidence:.1%} VaR: {result.kupiec.result.value}")
```

---

## 🔗 Weiterführende Dokumentation

- **Theorie:** [KUPIEC_POF_THEORY.md](./KUPIEC_POF_THEORY.md)
- **API Docs:** `src/risk_layer/var_backtest/`
- **Tests:** `tests/risk_layer/var_backtest/`

---

## 📝 Changelog

**v1.0.0 (2024-12-27)**
- Initial implementation (Phase 1+2)
- Kupiec POF Test mit stdlib-only chi2
- CLI interface mit CI support
- Comprehensive test suite

---

**Fragen? Probleme?**  
Siehe `docs/risk/roadmaps/KUPIEC_POF_BACKTEST_ROADMAP.md` oder kontaktiere das Risk Team.
