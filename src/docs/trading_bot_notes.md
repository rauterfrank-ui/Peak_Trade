# Peak Trade – KI-Trading-Bot Notizen

## 1. Ziele des Projekts

- Teil‑automatisiertes Trading unterstützen, nicht „blinde“ Vollautomatik.  
- LLMs nutzen für:
  - Research (Ideen, Zusammenfassungen, Regime‑Analyse)
  - Generierung / Erklärung von Regeln
  - Code‑Snippets für Backtests und Strategien
- Harte Regeln für:
  - Order‑Ausführung
  - Risiko- und Moneymanagement
  - Positionsgrößen und Limits

**Leitprinzip:** Mensch definiert Ziele & Grenzen, Maschine übernimmt Fleißarbeit und Routine‑Entscheidungen innerhalb enger Leitplanken.

---

## 2. Grobe Systemarchitektur

```text
Datenquellen  →  Research & Feature-Engine  →  Strategie / Signale  →  Risk Layer  →  Broker/Exchange
                    ↑                               |
                  LLM-Assist (Analyse, Code, Regime-Erkennung)
```

### 2.1. Komponenten

1. **Datenlayer**
   - Historische Preisdaten (Kline/Candles, OHLCV)
   - ggf. Orderbuch-/Tickdaten (später)
   - News/Makro/Krypto‑Onchain (optional, später)

2. **Research- & Feature-Layer**
   - Indikatoren (TA): gleitende Durchschnitte, RSI, Volatilität, ATR, Trendfilter etc.
   - Features: Regime‑Labels, Volatilitäts‑Cluster, ECM‑Fenster, Sentiment (später)

3. **Strategie-Layer**
   - Regelbasierte Strategien (z. B. Trendfolge, Mean Reversion, Breakouts)
   - LLM-unterstützte Generierung: „Formuliere mir eine Strategie mit folgenden Constraints…“

4. **Risk- & Portfolio-Layer**
   - Max. Risiko pro Trade (z. B. 0,5–1 % vom Account)
   - Max. parallele Trades, Korrelationsbegrenzung
   - Hard‑Stops & Trailing‑Stops

5. **Execution-Layer**
   - Anbindung an Broker/Exchange (z. B. über CCXT/REST)
   - Order‑Typen (Market, Limit, Stop, TP/SL)
   - Throttling, Retry‑Logik, Schutz vor Fehl‑Orders

6. **Monitoring & Logging**
   - Logs für Signale, Orders, PnL, Metriken
   - Alerts (z. B. Telegram/Discord), wenn etwas „komisch“ aussieht

---

## 3. Geplante Technologien & Tools (erste Version)

### 3.1. Programmiersprache & Umgebung

- **Python 3.x**
- Virtuelle Umgebung: `venv` oder `poetry`
- Ordnerstruktur (Beispiel):

```text
Peak_Trade/
├─ src/
│  ├─ data/
│  ├─ strategies/
│  ├─ backtests/
│  ├─ execution/
│  └─ utils/
├─ docs/
│  ├─ armstrong_notes.md
│  └─ trading_bot_notes.md
└─ notebooks/
```

### 3.2. Wichtige Libraries (Ideensammlung)

- **Daten & Analyse:** `pandas`, `numpy`  
- **Plotting:** `matplotlib`, `plotly` (für interaktive Charts)  
- **Backtesting:** z. B. `backtesting.py` oder `backtrader`  
- **Börsen‑Anbindung:** `ccxt` (für Krypto) oder spezifische Broker‑SDKs  
- **ML/LLM-Anbindung:** `openai` (oder alternative LLM‑Clients), ggf. Embedding‑DB (z. B. Chroma)  
- **Konfiguration / Struktur:** `pydantic` für Settings, `yaml`/`.env` für Secrets (nicht ins Repo).

---

## 4. Trading-Workflow (Zielbild)

1. **Universe-Definition**
   - Welche Märkte/Paare? (z. B. BTC/ETH + 5–10 Liquiditäts‑Top‑Coins oder Index‑Futures/ETFs)  

2. **Regime-Erkennung (optional, mittlere Phase)**
   - Trend vs. Range vs. High‑Vol‑Regime.  
   - LLM‑Assist, der Makro‑Narrative zusammenfasst, aber die Entscheidung bleibt regelbasiert.

3. **Signal-Generierung**
   - Start mit einfachen, klaren Regeln:
     - z. B. MA‑Crossovers, Donchian‑Breakouts, RSI‑Reversion.  
   - LLM darf Vorschläge machen, aber **jede Strategie → Backtest + Out‑of‑Sample‑Test**.

4. **Position Sizing & Risiko**
   - z. B. feste Prozent‑Risiko‑Regel: 0,5–1 % pro Trade.  
   - Stop‑Loss aus ATR / Volatilität ableiten.  
   - Max. Gesamt‑Exposure und Tages‑Verlustlimit definieren.

5. **Order-Ausführung**
   - Erst **Paper Trading / Sandbox**.  
   - Dann kleine Live‑Positionen.  
   - LLM darf keine Live‑Orders ausführen, nur Code/Signale generieren, die du reviewst.

6. **Review & Iteration**
   - Regelmäßige Auswertung: Equity‑Curve, Drawdown, Winrate, Expectancy.  
   - Strategien, die nicht mehr funktionieren, werden deaktiviert oder angepasst.

---

## 5. Sicherheits- und Risiko‑Leitplanken

- **Kein Auto-Size über gesamten Account ohne Limit.**  
- Secrets / API‑Keys in `.env` oder Keychain, niemals im Repo.  
- Kill‑Switch: Möglichkeit, alle Orders und Strategien schnell zu stoppen.  
- Max. Drawdown‑Limit (z. B. 10–15 %) definieren, bei dem alles auf Pause geht.

---

## 6. Rolle von LLMs im Peak-Trade-System

### 6.1. Was LLMs tun dürfen

- Strategien in **natürlicher Sprache** beschreiben und in Code übersetzen.  
- Bestehende Strategien erklären („Warum sind wir hier long?“ – aus der Logik, nicht aus der Zukunft).  
- Research‑Zusammenfassungen (Makro, Sektoren, Narratives).  
- Generierung von Test‑Cases für Backtests („Edge Cases“, Ausnahmesituationen).

### 6.2. Was LLMs *nicht* tun sollten

- Ohne Backtest Live‑Signale handeln.  
- Kapitalallokation selbstständig verändern.  
- „Bauchgefühls‑Trades“ vorschlagen ohne klare Regelbasis.

**Faustregel:** LLM = Co‑Pilot, nicht Autopilot.

---

## 7. Roadmap (grob)

1. **Phase 0 – Setup**
   - Repo & Ordnerstruktur erstellen
   - Basic‑Datenpipeline + erste Charts

2. **Phase 1 – Backtesting‑Framework**
   - Einfache Strategien implementieren (MA‑Crossover etc.)  
   - Backtests laufen lassen, Report‑Struktur etablieren

3. **Phase 2 – Regelbasierte Grundstrategien**
   - 1–2 saubere Strategien mit klarer Logik + Risk‑Layer  
   - Paper‑Trading

4. **Phase 3 – LLM-Assist**
   - LLM zur Strategie‑Iteration, Code‑Refactoring, Research einsetzen  
   - Evtl. ECM-/Makro‑Overlay als Feature

5. **Phase 4 – Semi‑Automatik**
   - Signale automatisch generieren, du bestätigst Orders manuell.  

6. **Phase 5 – Teilweise Automatik (optional)**
   - Nur wenn sich System und Leitplanken bewährt haben.

---

## 8. Offene TODOs

- [ ] Konkrete Broker-/Exchange‑Auswahl finalisieren.  
- [ ] Entscheidung für ein Backtesting‑Framework (z. B. `backtesting.py` vs. `backtrader`).  
- [ ] Erste Beispiel‑Strategie als Referenz implementieren.  
- [ ] Logging‑Standard (Struktur, Format, Speicherort) festlegen.  
- [ ] Interface definieren: Wie interagiert der Mensch am Ende mit dem System? CLI, Web‑UI, Notebooks?

---

*Arbeitsstatus:* Diese Notizen sind das **Gerüst** für den Peak‑Trade‑Trading‑Bot. Details und konkrete Implementierungsschritte werden in weiteren Dateien/Notebooks ausgearbeitet.
