# Armstrong × El Karoui Combo – Cross-Run Findings v1

> **Status:** R&D-Only | **Erstellt:** 2025-12-09 | **Version:** v1.2

---

## 1. Kontext

Auf Basis mehrerer Runs des **Armstrong × El Karoui Combo Experiments v1** wurden die Kombi-States
(Armstrong-Event-Status × El-Karoui-Vol-Regime) hinsichtlich 3d- und 7d-Forward-Returns analysiert.

Beispielhafte Runs:

* EVENT-Phase: BTC/EUR, 1h, 2024-06-01 – 2024-06-30
  → Run-ID: `rnd_combi_20251209_090521_d9dfb356`
* NONE-Phase: BTC/EUR, 1h, 2024-01-01 – 2024-01-10
  → Run-ID: `…10b4f7c9` (mehrfach wiederholt, identischer Hash)

Die zugrunde liegenden Reports liegen unter:

`reports&#47;r_and_d&#47;armstrong_elkaroui_combi&#47;*_report.md`

---

## 2. Run-Übersicht

| Run-ID     | Symbol  | TF | Zeitraum                | Bars | Armstrong-State   | Top-2 States (3d)                           | Bottom-2 States (3d)                            |
| ---------- | ------- | -- | ----------------------- | ---: | ----------------- | ------------------------------------------- | ----------------------------------------------- |
| `d9dfb356` | BTC/EUR | 1h | 2024-06-01 → 2024-06-30 |  696 | EVENT aktiv       | EVENT_LOW (+0.56%), POST_EVENT_LOW (+0.10%) | EVENT_HIGH (-0.34%), POST_EVENT_MEDIUM (-0.39%) |
| `10b4f7c9` | BTC/EUR | 1h | 2024-01-01 → 2024-01-10 |  200 | NONE (kein Event) | NONE_LOW (+0.42%), NONE_HIGH (-0.14%)       | NONE_HIGH (-0.14%), NONE_MEDIUM (-0.45%)        |

---

## 3. Detaillierte State-Rankings

### 3.1 Run d9dfb356 (EVENT-Phase, Juni 2024)

| Rank | Kombi-State        | Count | Ø 3d Return | Ø 7d Return | Std 3d |
|:----:|------------------- |------:|------------:|------------:|-------:|
| 1 🏆 | EVENT_LOW          |   142 |   **+0.56%**|   **+1.23%**|  2.49% |
| 2    | POST_EVENT_LOW     |    36 |      +0.10% |      +0.53% |  2.63% |
| 3    | POST_EVENT_HIGH    |    44 |      +0.07% |      +0.06% |  1.84% |
| 4    | EVENT_MEDIUM       |   221 |      -0.01% |      -0.02% |  2.69% |
| 5    | EVENT_HIGH         |   189 |      -0.34% |      -0.72% |  2.48% |
| 6 ❌ | POST_EVENT_MEDIUM  |    64 |   **-0.39%**|   **-1.34%**|  2.39% |

### 3.2 Run 10b4f7c9 (NONE-Phase, Januar 2024)

| Rank | Kombi-State | Count | Ø 3d Return | Ø 7d Return | Std 3d |
|:----:|-------------|------:|------------:|------------:|-------:|
| 1 🏆 | NONE_LOW    |    52 |   **+0.42%**|   **+0.73%**|  2.68% |
| 2    | NONE_HIGH   |    49 |      -0.14% |      -0.59% |  1.84% |
| 3 ❌ | NONE_MEDIUM |    99 |   **-0.45%**|   **-0.90%**|  2.28% |

---

## 4. Zentrale Beobachtungen

### 4.1 Vol-Regime-Effekt (El Karoui)

* **LOW-Vol-Regime ist durchgängig Top-Performer**
  * EVENT_LOW: Ø +0.56 % (3d), +1.23 % (7d)
  * NONE_LOW: Ø +0.42 % (3d), +0.73 % (7d)
  * **In 100% der Runs (2/2) ist LOW-Vol #1**

* **HIGH-Vol-Regime ist konsistent schwach bis negativ**
  * EVENT_HIGH: Ø -0.34 % (3d), -0.72 % (7d)
  * NONE_HIGH: Ø -0.14 % (3d), -0.59 % (7d)

* **MEDIUM-Regime ist überwiegend leicht negativ**, ohne klare Struktur.

### 4.2 Armstrong-Event-Effekt

* In LOW-Vol-Regimen verstärken Armstrong-Events den positiven Effekt:
  * EVENT_LOW > NONE_LOW

* In HIGH-Vol-Regimen verstärken Armstrong-Events den negativen Effekt:
  * EVENT_HIGH < NONE_HIGH

**Interpretation:**
Armstrong-Events wirken wie ein **„Volatilitäts-Multiplikator"**:

* In ruhigen Phasen (LOW) verbessern sie das Chance-Risiko-Profil,
* in hektischen Phasen (HIGH) verschlechtern sie es.

### 4.3 Return-Skalierung über Zeit

| State       | 1d → 3d → 7d Trend                          |
|-------------|---------------------------------------------|
| EVENT_LOW   | +0.23% → +0.56% → +1.23% ✅ Skaliert gut    |
| EVENT_HIGH  | -0.06% → -0.34% → -0.72% ❌ Negativ verstärkend |
| NONE_LOW    | +0.12% → +0.42% → +0.73% ✅ Konsistent positiv |

---

## 5. Limitierungen & Overfitting-Risiken

| Risiko              | Schwere | Beschreibung                                    |
|---------------------|:-------:|-------------------------------------------------|
| **Zeitraum-Bias**   |   🔴    | Nur 2024 getestet, keine älteren Daten          |
| **Single-Asset**    |   🔴    | Nur BTC/EUR, keine Diversifikation              |
| **Single-Timeframe**|   🟡    | Nur 1h, könnte TF-spezifisch sein               |
| **Kleine N**        |   🟡    | POST_EVENT States haben <50 Bars                |
| **Keine Walk-Forward** | 🔴   | In-Sample = Out-of-Sample                       |
| **Parameter-Tuning**|   🟡    | Vol-Thresholds (0.3/0.7) könnten overfit sein   |

**Fazit:**
Die Ergebnisse sind **vielversprechend**, aber klar als **R&D-Signal** zu behandeln – nicht als Produktions-Edge.

---

## 6. Ableitbare Hypothesen (R&D only)

1. **H1 – Vol-Regime-Filter:**
   Trades sollten in HIGH-Vol-Regimen gemieden oder stark reduziert werden.

2. **H2 – Event × Vol-Kombi:**
   Armstrong-Events sind hauptsächlich in LOW-Vol-Regimen attraktiv (EVENT_LOW).

3. **H3 – Medium-Regime ist optional:**
   EVENT_MEDIUM / NONE_MEDIUM liefern keinen stabilen Edge und können ggf. als „neutral / skip" behandelt werden.

---

## 7. Nächste Schritte (R&D-Roadmap)

### Priorität 1: Robustheits-Checks (kritisch)

1. **Längerer Zeitraum testen** (2022–2024)
   ```bash
   python scripts/research_cli.py armstrong-elkaroui-combi \
     --from 2022-01-01 --to 2024-12-01 --generate-report -v
   ```

2. **Walk-Forward Validation**
   - Train: 2022–2023, Test: 2024
   - Prüfen ob LOW-Vol-Edge out-of-sample hält

3. **Cross-Asset-Check**
   ```bash
   python scripts/research_cli.py armstrong-elkaroui-combi \
     --symbol ETH/EUR --from 2023-01-01 --to 2024-06-30 --generate-report
   ```

### Priorität 2: Statistische Validierung

4. **Signifikanz-Tests hinzufügen**
   - T-Test: EVENT_LOW vs. EVENT_HIGH Returns
   - Bootstrap-Konfidenzintervalle für Ø Returns

5. **Monte-Carlo-Robustness**
   - Shuffled Labels → Nullhypothese prüfen
   - Block-Bootstrap für Return-Verteilungen

### Priorität 3: Parameter-Sensitivität

6. **Vol-Threshold-Sweep**
   - Teste verschiedene Threshold-Kombinationen: (0.25/0.75), (0.33/0.67), (0.4/0.6)
   - Prüfen ob Effekt stabil bleibt

7. **Timeframe-Variation**
   ```bash
   python scripts/research_cli.py armstrong-elkaroui-combi \
     --timeframe 4h --from 2023-01-01 --to 2024-06-30 --generate-report
   ```

---

## 8. Dummy-Langzeit-Run (Framework-Sanity-Check)

**Wichtiger Hinweis:**
Die folgenden Ergebnisse stammen aus einem **Dummy-Daten-Run** und dienen ausschließlich der **Validierung des Frameworks**, nicht als inhaltliche Markt-Analyse.

### 8.1 Setup

* **Run-ID:** `rnd_combi_20251209_092138_04096e5a`
* **Symbol:** BTC/EUR
* **Timeframe:** 1h
* **Zeitraum:** 2022-01-01 bis 2024-12-01
* **Bars:** 10.000
* **Datenquelle:** Dummy-Daten (kein Kraken-API-Zugriff, kein gefüllter Cache)
* **Armstrong-State:** `NONE` (keine Events in den Dummy-Daten)

### 8.2 Kombi-States (3d Forward Return, Dummy-Daten)

| Kombi-State   | Count | Ø 3d Return |
| ------------- | ----: | ----------: |
| `NONE_LOW`    | 3.065 |     +0,05 % |
| `NONE_HIGH`   | 2.993 |     +0,03 % |
| `NONE_MEDIUM` | 3.942 |     -0,00 % |

**Interpretation:**

* Alle States liegen nahe 0 %, wie bei einem **Random Walk** zu erwarten.
* Es existieren keine `EVENT_*` States, da in den Dummy-Daten keine echten Armstrong-Events definiert sind.
* Der Run bestätigt:
  * das Experiment skaliert technisch auf längere Zeiträume / größere Bar-Mengen,
  * die Kombi-State-Logik funktioniert syntaktisch auch ohne Events,
  * es gibt **keine** zusätzlichen Erkenntnisse über EVENT vs. NONE Phasen.

### 8.3 Implikation für die Findings

* Die **inhaltlichen Hypothesen (H1–H3)** und die **Konfidenz-Matrix** basieren weiterhin **nur** auf den kürzeren BTC/EUR-Runs mit (simulierten) EVENT-Phasen.
* Der Dummy-Langzeit-Run wird als **Framework-Sanity-Check** verbucht und fließt **nicht** in die Bewertung eines handelbaren Edges ein.

### 8.4 TODO – Echte Markt-Robustheit (wenn API/Caches verfügbar)

Für eine echte Robustheits-Analyse über 2022–2024 werden benötigt:

1. **Historische Marktdaten im Cache**, z.B. über ein separates Data-Loading-Script (Kraken o.ä.).
2. Mindestens ein Run mit:
   * echten `EVENT_*` und `NONE_*` Phasen,
   * ausreichend langen Zeitreihen und realer Marktdynamik.
3. Danach:
   * erneute Cross-Run-Analyse (v2),
   * Update der Hypothesen / Konfidenzen,
   * ggf. erste Walk-Forward-Setups.

Bis dahin bleibt dieser Abschnitt explizit als **technischer Validierungs-Check** gekennzeichnet.

---

## 9. Konfidenz-Matrix (vorläufig)

| Hypothese                                    | Status      | Konfidenz |
|----------------------------------------------|:-----------:|:---------:|
| LOW-Vol zeigt bessere Forward-Returns        | ✅ Bestätigt |    60%    |
| Armstrong-Events verstärken Vol-Effekte      | ⚠️ Hinweise  |    40%    |
| Effekt ist handelbarer Edge                  | ❓ Unklar    |    20%    |

---

## 10. TODO – Real-Data Robustness (R&D)

**Status:** ⏳ Vorbereitet, wartet auf echte Marktdaten (Kraken-API / Data-Cache).

**Ziel:**
Die bisherigen R&D-Findings (EVENT_LOW vs. EVENT_HIGH, NONE_LOW vs. NONE_HIGH) mit **echten Marktdaten** über längere Zeiträume (2022–2024), mehrere Assets und Timeframes zu validieren.

### Voraussetzungen

* Historische Daten im Data-Cache verfügbar (z.B. BTC/EUR, ETH/EUR, weitere Assets).
* Kombi-Experiment `armstrong-elkaroui-combi` lauffähig gegen Real-Daten.

### Geplante Schritte (wenn Daten da sind)

| # | Schritt | Befehl / Details |
|---|---------|------------------|
| 1 | BTC/EUR, 1h, 2022–2024 | `--from 2022-01-01 --to 2024-12-01` (ohne Dummy-Fallback) |
| 2 | Cross-Asset-Runs | ETH/EUR, ggf. FX-/Index-Asset |
| 3 | Timeframe-Variation | 15m, 4h, 1d |
| 4 | Findings-Update | `ARMSTRONG_ELKAROUI_CROSS_RUN_FINDINGS_V1.md` → v2 |
| 5 | Walk-Forward-Setup | Train: 2022–2023, Test: 2024 |

### Nach Abschluss

* Neue Run-IDs dokumentieren
* Hypothesen & Konfidenz-Matrix aktualisieren
* Ggf. erste Walk-Forward-Ergebnisse einpflegen

**Hinweis:**
Bis diese Schritte mit echten Daten gelaufen sind, bleiben alle Armstrong × El Karoui Hypothesen klar als **R&D-only** markiert (kein produktiver Strategy-Layer-Einsatz).

---

## Changelog

| Version | Datum      | Änderungen                                    |
|---------|------------|-----------------------------------------------|
| v1.0    | 2025-12-09 | Initial Findings aus 2 Runs (d9dfb356, 10b4f7c9) |
| v1.1    | 2025-12-09 | Add Dummy-Langzeit-Run (Framework-Sanity-Check) |
| v1.2    | 2025-12-09 | Add TODO section for Real-Data Robustness |
