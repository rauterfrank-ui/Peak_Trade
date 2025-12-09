# Strategy Profile - EHLERS_CYCLE_FILTER

## 1. Meta

- **Strategy ID:** `ehlers_cycle_filter`
- **Version:** v1
- **Erstellt:** 2025-12-08T23:13:55.402769
- **Daten:** 2024-01-01..2024-01-05
- **Universe:** BTC/EUR
- **Timeframe:** 1h

---

## 2. Performance (Baseline)

| Metrik | Wert |
|--------|------|
| Sharpe | -1.78 |
| CAGR | -46.23% |
| Max Drawdown | -27.15% |
| Volatilität | 170.00% |
| Total Return | -16.86% |
| Winrate | 47.00% |
| Avg. Trade | -0.16% |
| Trades | 100 |

---

## 3. Robustness

---

## 5. Tiering & Empfehlung

- **Tier:** 🔬 **R&D/Research**
- **Empfohlene Config:** `ehlers_cycle_filter_v0_research`
- **Live-Trading:** Nicht freigegeben
- **Kommentar:** Ehlers DSP Cycle Filter (Research-Only).
Basiert auf John Ehlers' Digital Signal Processing Techniken:
- Super Smoother Filter (weniger Lag als EMA)
- Bandpass-Filter für Cycle-Isolation
- Hilbert Transform für Phase-Messung
Ziel: Verbesserte Intraday-Signalqualität.
⚠️ NICHT FÜR LIVE-TRADING - Nur für Research/Backtests.
Deployment erst nach Phase-X-Freigabe möglich.


---

## 6. Fazit & Next Steps

- Schwache risikoadjustierte Performance (Sharpe < 1.0)
- Hoher Max-Drawdown (> 20%)

---

*Generiert am 2025-12-08T23:13:55.402769 - Peak_Trade Strategy Profiling*