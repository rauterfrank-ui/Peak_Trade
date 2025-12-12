# Case Study: Regime-Analyse – Regime-Aware Portfolio (BTCUSDT)

## 1. Setup & Kontext

**Strategie:**  
BTCUSDT – Regime-Aware Portfolio  
- Zusammensetzung: Breakout 60 % / RSI-Reversion 40 %  
- Timeframe: Daily Bars  
- Regime-Modell: Volatilitäts-/Regime-Filter mit 3 Zuständen:
  - Risk-Off
  - Neutral
  - Risk-On

**Zeitraum:**  
2021-01-01 bis 2024-12-31

**Regime-Scales (Backtest-Konfiguration):**
- `risk_off_scale = 0.10`
- `neutral_scale = 0.60`
- `risk_on_scale = 1.00`

**Gesamt-Performance (Portfolio-Ebene):**
- Total Return ≈ **+45 %**
- Sharpe ≈ **1.40**
- Max Drawdown ≈ **-19 %**

---

## 2. Regime-Analyse – Ergebnis-Tabelle

| Regime   | Bars [%] | Return | Return Contribution [%] | Sharpe | Max Drawdown |
|----------|----------|--------|-------------------------|--------|--------------|
| Risk-Off | 24.8%    | -0.12  | -26.7%                  | -0.45  | -0.18        |
| Neutral  | 45.3%    | 0.22   | 48.9%                   | 1.05   | -0.14        |
| Risk-On  | 29.9%    | 0.35   | 77.8%                   | 1.85   | -0.21        |

Interpretation der Spalten:
- **Bars [%]** – Zeitanteil des jeweiligen Regimes
- **Return** – kumulierter Return im jeweiligen Regime (z.B. 0.35 = +35 %)
- **Return Contribution [%]** – Beitrag dieses Regimes zur Gesamt-Performance (Summe ≈ 100 %, inkl. negativer Beiträge)
- **Sharpe / Max Drawdown** – Kennzahlen pro Regime

---

## 3. Quant-Lead Analyse

### 3.1 Kurz-Fazit

Die Strategie zeigt ein klares **Regime-Alpha**:

- **Risk-On** liefert mit nur ~30 % der Zeit fast **78 % der Gesamt-Performance** bei exzellentem Sharpe (**1.85**).  
- **Risk-Off** ist ein **Performance-Killer** – trotz niedrigem Scale (0.10) verbrennt dieses Regime rund **27 % der Gewinne**.  
- Die aktuelle Konfiguration ist solide, aber das **Neutral-Regime** ist mit 45 % Zeitanteil und ~49 % Contribution nur leicht über „fair" und damit **unteroptimiert**.

### 3.2 Regime-Profil im Detail

#### Risk-On – ✅ Exzellent

- **Zeitanteil:** 29.9 %  
- **Return Contribution:** 77.8 % → Effizienz ≈ 2.6x (Contribution% / Bars%)  
- **Sharpe:** 1.85 → sehr starke, konsistente Alpha-Generierung  
- **Max Drawdown:** -21 % → für Crypto absolut akzeptabel im Kontext der Performance  

**Bewertung:**  
Risk-On ist klar das **Haupt-Value-Regime**. Die Strategie monetarisiert Risk-On-Phasen sehr effektiv.  
`risk_on_scale = 1.00` ist angemessen und muss **nicht reduziert** werden.

---

#### Neutral – ⚠️ Unterperformant, aber positiv

- **Zeitanteil:** 45.3 %  
- **Return Contribution:** 48.9 % → Effizienz ≈ 1.1x  
- **Sharpe:** 1.05 → „okay", aber kein Überflieger  
- **Max Drawdown:** -14 % → moderat und gut kontrollierbar  

**Bewertung:**  
Neutral trägt etwa proportional zu seinem Zeitanteil bei – leicht positiv, aber kein Alpha-Monster.  
Bei fast der **Hälfte aller Bars** könnte man erwarten, dass hier mehr Return generiert wird.  
`neutral_scale = 0.60` wirkt eher konservativ; angesichts Sharpe 1.05 ist **Luft nach oben**.

---

#### Risk-Off – ❌ Klar problematisch

- **Zeitanteil:** 24.8 %  
- **Return:** -0.12 (≈ -12 %)  
- **Return Contribution:** -26.7 % → direkt negativer Value-Beitrag  
- **Sharpe:** -0.45 → systematischer Value-Destruction  
- **Max Drawdown:** -18 %  

**Bewertung:**  
Risk-Off ist ein **Value-Destruction-Regime**:

- Trotz bereits reduziertem `risk_off_scale = 0.10` entstehen **signifikante Verluste**.
- Negativer Sharpe und negative Contribution zeigen:  
  **Jeder Trade in Risk-Off kostet im Erwartungswert Geld.**

---

### 3.3 Handlungsempfehlungen

#### Empfohlene Parameter-Anpassungen

| Parameter        | Aktuell | Empfehlung        | Begründung |
|------------------|---------|-------------------|-----------|
| `risk_off_scale` | 0.10    | **0.00**          | Komplettes Exit in Risk-Off. Selbst 10 % Exposure vernichtet ~27 % der Gesamtgewinne. Sharpe -0.45 → kein Alpha, reiner Drag. |
| `neutral_scale` | 0.60    | **0.70–0.80**     | Neutral ist positiv (Sharpe 1.05, moderater Drawdown). Etwas höheres Exposure ist bei akzeptablem Risiko gerechtfertigt. |
| `risk_on_scale`  | 1.00    | **1.00 beibehalten** | Already „all-in" auf das beste Regime. Sharpe 1.85 und hoher Beitrag – kein unmittelbarer Anpassungsbedarf. |

#### Erwarteter Impact (Heuristik)

Bei `risk_off_scale = 0.00`:

- Eliminierung der **negativen Risk-Off-Contribution** (~-26.7 %)  
- Erwartete Verbesserung der Gesamt-Kennzahlen:
  - Sharpe von ~1.40 → grob in Richtung **1.55–1.65**
  - Max Drawdown-Effekt:
    - Risk-Off MaxDD (-18 %) entfällt → potenziell **Reduktion des Gesamt-DD** in Richtung ~-15 %  
    - (abhängig vom genauen Pfad der Equity, aber sinnvoll als Erwartung)

**Key Insight:**  
Die Strategie verdient Geld primär in **Risk-On**, hält sich in **Neutral** über Wasser und verliert systematisch in **Risk-Off** – selbst bei minimaler Exposure.  
Der klare **Quick-Win** ist: **Risk-Off-Exposure auf 0 setzen.**

---

## 4. Nächste Experimente & Sweeps

### 4.1 Risk-Off Scale Null-Test

**Hypothese:**  
Vollständiges Exit in Risk-Off (statt 10 % Exposure) eliminiert den größten Performance-Drag, ohne signifikante Downside.

**Beispiel-Kommando (an tatsächliche CLI anpassen):**

```bash
python scripts/run_portfolio_backtest.py \
  --risk-off-scale 0.0 \
  --neutral-scale 0.60 \
  --risk-on-scale 1.00 \
  --label "btc_regime_no_riskoff"
```

**Erwartung:**

* Deutlich verbesserter Sharpe
* Geringerer Max Drawdown
* Kaum reduzierter Total Return (eher höher)

---

### 4.2 Neutral-Scale Sensitivity Sweep

Ziel: Finde den Sweet-Spot, an dem Neutral mehr Performance bringt, ohne das Drawdown-Profil zu stark zu verschlechtern.

```toml
# Datei: config/sweeps/neutral_scale_sensitivity.toml

[sweep]
param = "neutral_scale"
values = [0.50, 0.60, 0.70, 0.80, 0.90]
# weitere Parameter wie risk_off_scale=0.0, risk_on_scale=1.0
```

**Hypothese:**

* Bereich **0.70–0.80** liefert besseren Kompromiss aus Sharpe und Drawdown als 0.60.

---

### 4.3 Regime-Threshold Robustness Check

Ziel: Prüfen, ob durch leicht verschobene Thresholds mehr „gute" Phasen als Risk-On klassifiziert werden können, ohne die Risk-Off-Phasen zu kontaminieren.

```bash
python scripts/run_regime_threshold_sweep.py \
  --low-vol-threshold "0.4,0.5,0.6" \
  --high-vol-threshold "1.8,2.0,2.2"
```

---

### 4.4 Risk-Off-Alternative: Hedge statt Exit

Variante untersuchen:

* Long-Strategien sind in Risk-Off flat (kein Exposure),
* zusätzliches Hedge-System (Short-Futures, Perps o.ä.) nur in Risk-Off.

Vergleich:

* Variante A: `risk_off_scale = 0.0` (flat)
* Variante B: `risk_off_scale = 0.0` + Hedge-System

---

### 4.5 Walk-Forward Validation

Ziel: Überprüfen, ob die gewählten Regime-Parameter (insbesondere `risk_off_scale=0.0` und angepasste `neutral_scale`) **zeitlich stabil** sind.

```bash
python scripts/run_walkforward.py \
  --config config/sweeps/regime_aware_portfolio_aggressive.toml \
  --folds 5 \
  --label "btc_regime_wf_validation"
```

---

## 5. Bottom Line

* Die Strategie zeigt ein **klar strukturiertes Regime-Profil**:

  * **Risk-On**: Treiber-Regime mit hohem Alpha
  * **Neutral**: leicht positiv, ausbaufähig
  * **Risk-Off**: systematischer Performance-Drag

* Der **größte Quick-Win** ist:

  * `risk_off_scale = 0.00` → komplettes Exit in Risk-Off

* Weitere Upside liegt in:

  * vorsichtigem Hochziehen von `neutral_scale`
  * Feintuning der Regime-Grenzen
  * optionalem Hedge-System für Risk-Off-Phasen

Diese Case Study dient als Referenz, wie Regime-Analyse in Peak_Trade für **konkrete Portfolio-Entscheidungen** eingesetzt wird.
















