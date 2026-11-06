# Strategy Profile - RSI_REVERSION

## 1. Meta

- **Strategy ID:** `rsi_reversion`
- **Version:** v1
- **Erstellt:** 2025-12-07T22:28:31.390668
- **Daten:** 2024-01-01..2024-01-09
- **Universe:** BTC/EUR
- **Timeframe:** 1h

---

## 2. Performance (Baseline)

| Metrik | Wert |
|--------|------|
| Sharpe | -0.38 |
| CAGR | -12.62% |
| Max Drawdown | -27.99% |
| Volatilität | 174.27% |
| Total Return | -10.23% |
| Winrate | 50.50% |
| Avg. Trade | -0.03% |
| Trades | 200 |

---

## 3. Robustness

### Monte-Carlo-Analyse

- **Runs:** 20
- **Return p5/p50/p95:** -39.56% / -22.01% / 3.58%
- **Sharpe p5/p95:** 0.00 / 0.00

### Stress-Tests

- **Szenarien:** 2
- **Min/Avg/Max Return:** -26.13% / -18.60% / -11.07%

---

## 4. Regime-Profil

| Regime | Contribution% | Time% | Effizienz (C/T) | Trades | Avg Return |
|--------|---------------|-------|-----------------|--------|------------|
| low_vol | -4.36% | 3.50% | -1.25 | 7 | -0.62% |
| neutral | 0.56% | 84.50% | 0.01 | 169 | 0.00% |
| high_vol | 0.57% | 2.50% | 0.23 | 5 | 0.11% |

**Dominantes Regime:** high_vol
**Schwächstes Regime:** low_vol

---

## 5. Tiering & Empfehlung

- **Tier:** **Core**
- **Empfohlene Config:** `rsi_reversion_v1_core`
- **Live-Trading:** Nicht freigegeben
- **Kommentar:** Robust über mehrere Vol-Regime, gute Sharpe/MaxDD-Balance. Empfohlen als Mean-Reversion-Komponente.

---

## 6. Fazit & Next Steps

- Schwache risikoadjustierte Performance (Sharpe < 1.0)
- Hoher Max-Drawdown (> 20%)
- Monte-Carlo zeigt Risiko negativer Returns im Tail
- Als Core-Strategie klassifiziert - geeignet für Hauptportfolio

---

*Generiert am 2025-12-07T22:28:31.390668 - Peak_Trade Strategy Profiling*
