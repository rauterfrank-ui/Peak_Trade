# Kupiec POF Test – Theoretischer Hintergrund


## Authority and epoch note

This guide preserves historical and component-level Kupiec POF theory context. Statistical terms such as H0 acceptance, exception-rate fit, Basel traffic-light interpretation, green / yellow / red zones, valid VaR model, or theory-backed validation are not, by themselves, current Master V2 approval, Doubleplay authority, First-Live readiness, operator authorization, model certification, regulatory approval, or permission to route orders into any live capital path.

Kupiec POF theory can support VaR / risk review and model-quality discussions, but it is not a standalone promotion gate. Any live or first-live promotion remains governed by current gate, evidence, and signoff artifacts, Scope / Capital Envelope boundaries, Risk / Exposure Caps, Safety / Kill-Switches, and staged Execution Enablement. This note is docs-only and changes no runtime behavior.

**Autor:** Peak_Trade Risk Team  
**Datum:** 2024-12-27  
**Zweck:** Theoretische Grundlagen für VaR Backtesting

---

## 📐 Mathematische Grundlagen

### VaR Definition

**Value-at-Risk (VaR)** ist ein Risikomaß, das den maximalen erwarteten Verlust über einen Zeitraum bei gegebenem Konfidenzniveau quantifiziert.

**Formale Definition:**

Für Portfolio-Returns \( R_t \) und Konfidenzniveau \( \alpha \):

$$
\text{VaR}_\alpha = -\inf\{x : P(R_t \leq x) \geq 1 - \alpha\}
$$

**Beispiel (99% VaR):**
- \( \alpha = 0.99 \)
- VaR₉₉% = -2% bedeutet: "Mit 99% Wahrscheinlichkeit verlieren wir nicht mehr als 2%"
- Oder umgekehrt: "In 1% der Fälle verlieren wir mehr als 2%"

### VaR-Violation

Eine **Violation** (Überschreitung) tritt auf, wenn der tatsächliche Verlust größer ist als die VaR-Schätzung:

$$
\text{Violation}_t = \mathbb{1}\{R_t < -\text{VaR}_t\}
$$

**Wichtig:** In Peak_Trade Convention:
- Returns sind **dezimal**: -0.02 = -2%
- VaR ist **negativ**: -0.02 = 2% VaR
- Violation wenn: \( R_t < \text{VaR}_t \) (beide negativ!)

**Beispiel:**
- Return = -0.03 (-3%)
- VaR = -0.02 (-2%)
- Violation? JA, weil -0.03 < -0.02

---

## 🧪 Kupiec POF Test (1995)

### Intuition

Der Kupiec Test prüft: **"Stimmt die Häufigkeit der Violations mit der Erwartung überein?"**

**Gedanke:**
- Wenn VaR korrekt kalibriert ist, sollten Violations mit Rate \( p^* = 1 - \alpha \) auftreten
- Für 99% VaR: \( p^* = 0.01 \) → erwarten 1% Violations
- Test prüft: Ist die beobachtete Rate signifikant unterschiedlich?

### Formale Hypothesen

$$
H_0: p = p^* \quad \text{(Modell korrekt kalibriert)}
$$

$$
H_1: p \neq p^* \quad \text{(Modell fehlkalibriert)}
$$

Wobei:
- \( p \) = wahre Violation Rate (unbekannt)
- \( p^* = 1 - \alpha \) = erwartete Violation Rate
- \( \alpha \) = Konfidenzniveau (z.B. 0.99)

### Likelihood Ratio Statistik

**Idee:** Vergleiche Likelihood unter \( H_0 \) vs. \( H_1 \)

Gegeben:
- \( T \) = Anzahl Beobachtungen
- \( N \) = Anzahl Violations
- \( \hat{p} = N/T \) = beobachtete Violation Rate

**Log-Likelihood unter \( H_0 \):**

$$
\log L_0 = (T - N) \log(1 - p^*) + N \log(p^*)
$$

**Log-Likelihood unter \( H_1 \) (mit MLE \( \hat{p} \)):**

$$
\log L_1 = (T - N) \log(1 - \hat{p}) + N \log(\hat{p})
$$

**Likelihood Ratio Statistik:**

$$
\text{LR}_{\text{POF}} = -2(\log L_0 - \log L_1)
$$

### Verteilung

Unter \( H_0 \) gilt asymptotisch:

$$
\text{LR}_{\text{POF}} \sim \chi^2(1)
$$

(Chi-Quadrat-Verteilung mit 1 Freiheitsgrad)

### Entscheidungsregel

Wähle Signifikanzniveau \( \beta \) (typisch: 0.05).

Kritischer Wert: \( c = \chi^2_{1, 1-\beta} \) (z.B. 3.84 für \( \beta = 0.05 \))

**Entscheidung:**
- Wenn \( \text{LR}_{\text{POF}} > c \): **REJECT** \( H_0 \) (Modell fehlkalibriert)
- Wenn \( \text{LR}_{\text{POF}} \leq c \): **ACCEPT** \( H_0 \) (Modell OK)

**P-Wert:**

$$
p\text{-value} = P(\chi^2(1) > \text{LR}_{\text{POF}})
$$

Interpretation:
- Kleiner p-value (< 0.05): starke Evidenz gegen \( H_0 \)
- Großer p-value (> 0.05): keine Evidenz gegen \( H_0 \)

---

## 🔢 Beispielrechnung

### Szenario

- **T** = 250 Handelstage
- **N** = 5 Violations
- **α** = 0.99 (99% VaR)
- **p\*** = 0.01 (erwartete Rate)
- **β** = 0.05 (Signifikanzniveau)

### Schritt 1: Beobachtete Rate

$$
\hat{p} = \frac{N}{T} = \frac{5}{250} = 0.02 = 2\%
$$

→ Doppelt so viele Violations wie erwartet!

### Schritt 2: Log-Likelihoods

**Unter \( H_0 \) (\( p = p^* = 0.01 \)):**

$$
\log L_0 = (250 - 5) \log(0.99) + 5 \log(0.01)
$$

$$
= 245 \cdot (-0.01005) + 5 \cdot (-4.605)
$$

$$
= -2.462 - 23.026 = -25.488
$$

**Unter \( H_1 \) (\( p = \hat{p} = 0.02 \)):**

$$
\log L_1 = 245 \log(0.98) + 5 \log(0.02)
$$

$$
= 245 \cdot (-0.02020) + 5 \cdot (-3.912)
$$

$$
= -4.950 - 19.560 = -24.510
$$

### Schritt 3: LR Statistik

$$
\text{LR}_{\text{POF}} = -2(-25.488 - (-24.510)) = -2 \cdot (-0.978) = 1.956
$$

### Schritt 4: Kritischer Wert

Für \( \beta = 0.05 \), \( \text{df} = 1 \):

$$
c = \chi^2_{1, 0.95} = 3.841
$$

### Schritt 5: Entscheidung

$$
\text{LR}_{\text{POF}} = 1.956 < 3.841 = c
$$

→ **ACCEPT** \( H_0 \): Modell OK! ✅

**P-Wert:**

$$
p = P(\chi^2(1) > 1.956) \approx 0.162
$$

→ Keine signifikante Abweichung (p > 0.05)

---

## 📊 Chi-Quadrat Verteilung (df=1)

### Eigenschaften

Die Chi-Quadrat-Verteilung mit 1 Freiheitsgrad hat besondere Eigenschaften:

**Beziehung zur Normalverteilung:**

Wenn \( Z \sim N(0, 1) \), dann \( Z^2 \sim \chi^2(1) \)

**CDF via Error Function:**

$$
F_{\chi^2(1)}(x) = \text{erf}\left(\sqrt{\frac{x}{2}}\right)
$$

Wobei:

$$
\text{erf}(z) = \frac{2}{\sqrt{\pi}} \int_0^z e^{-t^2} dt
$$

**Wichtige Perzentile:**

| Percentil | Wert | Interpretation |
|-----------|------|----------------|
| 50% | 0.455 | Median |
| 90% | 2.706 | 90th Percentile |
| 95% | 3.841 | Kritisch für α=0.05 |
| 99% | 6.635 | Kritisch für α=0.01 |

### Stdlib Implementation (Python)

Peak_Trade implementiert Chi-Quadrat (df=1) **ohne scipy**:

```python
import math

def chi2_df1_cdf(x):
    """CDF für Chi²(1)"""
    if x <= 0:
        return 0.0
    return math.erf(math.sqrt(x / 2))

def chi2_df1_sf(x):
    """Survival Function (1 - CDF)"""
    if x <= 0:
        return 1.0
    return math.erfc(math.sqrt(x / 2))

def chi2_df1_ppf(p):
    """Inverse CDF via Binary Search"""
    # Siehe kupiec_pof.py für vollständige Implementierung
    ...
```

**Warum kein scipy?**
- Reduziert Dependencies
- Volle Kontrolle über numerische Stabilität
- Ausreichend für df=1 (einfacher Spezialfall)

---

## 🎓 Basel III Kontext

### Regulatorische Anforderungen

Das **Basel Committee on Banking Supervision** schreibt VaR-Backtesting vor:

**Minimum Standards:**
- Mindestens **250 Handelstage** Backtesting-Periode
- **Tägliche** Überwachung der Violations
- **Dokumentation** von Exceedances
- **Action Plan** bei zu vielen Violations

### Traffic Light Approach

Basel verwendet ein "Ampel-System":

| Zone | Violations (99% VaR, 250 Tage) | Bedeutung | Action |
|------|-------------------------------|-----------|--------|
| 🟢 Grün | 0-4 | Modell OK | Keine |
| 🟡 Gelb | 5-9 | Grenzwertig | Review |
| 🔴 Rot | ≥10 | Inakzeptabel | Modell ändern |

**Kupiec Test vs. Traffic Light:**
- Kupiec: Statistischer Test (p-value basiert)
- Traffic Light: Deterministischer Schwellwert
- Beide ergänzen sich!

---

## 🔍 Limitationen des Kupiec Tests

### 1. Keine Clustering-Erkennung

**Problem:** Test zählt nur Violations, nicht deren Verteilung

**Beispiel:**
- Szenario A: 5 Violations gleichmäßig über Jahr verteilt
- Szenario B: 5 Violations alle in derselben Woche

→ Kupiec sagt: beide ACCEPT, aber B zeigt Clustering!

**Lösung:** Christoffersen Independence Test (nicht in Phase 1)

### 2. Geringe Power bei kleinen Samples

**Problem:** Bei wenigen Beobachtungen schwer, Fehlkalibrierung zu erkennen

**Beispiel:**
- T = 100, erwartete 1 Violation, beobachtet 3
- Technisch 3x mehr, aber statistisch nicht signifikant

**Lösung:** Mindestens 250 Tage (Basel Standard)

### 3. Keine Magnitude-Bewertung

**Problem:** Test unterscheidet nicht zwischen leichten und schweren Violations

**Beispiel:**
- Violation A: -2.1% (VaR = -2%)
- Violation B: -10% (VaR = -2%)

→ Beide zählen gleich, aber B ist viel kritischer!

**Lösung:** Expected Shortfall Backtest (zukünftige Erweiterung)

### 4. Asymptotische Verteilung

**Problem:** \( \chi^2 \)-Approximation gilt nur asymptotisch

**Praxis:** Bei T ≥ 250 ausreichend genau

---

## 📚 Referenzen

### Primärliteratur

**Kupiec, P. H. (1995)**  
*"Techniques for Verifying the Accuracy of Risk Measurement Models"*  
Journal of Derivatives, Vol. 3, No. 2, pp. 73-84

### Regulatorische Dokumente

**Basel Committee on Banking Supervision (1996)**  
*"Supervisory Framework for the Use of 'Backtesting' in Conjunction with the Internal Models Approach to Market Risk Capital Requirements"*

**Basel Committee (2019)**  
*"Minimum Capital Requirements for Market Risk"*  
(Revised Framework)

### Weiterführende Tests

**Christoffersen, P. F. (1998)**  
*"Evaluating Interval Forecasts"*  
International Economic Review, Vol. 39, No. 4, pp. 841-862  
→ Conditional Coverage Test (Independence + Unconditional Coverage)

**Berkowitz, J., Christoffersen, P., Pelletier, D. (2011)**  
*"Evaluating Value-at-Risk Models with Desk-Level Data"*  
Management Science, Vol. 57, No. 12  
→ Duration-based Tests

---

## 🧩 Zusammenfassung

### Kernpunkte

1. **Kupiec POF** testet, ob Violation-Häufigkeit mit Erwartung übereinstimmt
2. Verwendet **Likelihood Ratio Test** mit \( \chi^2(1) \)-Verteilung
3. **Basel-konform**: Mindestens 250 Tage Beobachtungsperiode
4. **Limitiert**: Erkennt weder Clustering noch Magnitude
5. **Best Practice**: Kombiniere mit weiteren Tests (Christoffersen, Traffic Light)

### Nächste Schritte

Nach erfolgreicher Kupiec POF Implementation (Phase 1+2):

- **Phase 3:** Christoffersen Independence Test
- **Phase 4:** Traffic Light System Integration
- **Phase 5:** Expected Shortfall Backtesting

---

**Für praktische Anwendung siehe:** [VAR_BACKTEST_GUIDE.md](./VAR_BACKTEST_GUIDE.md)
