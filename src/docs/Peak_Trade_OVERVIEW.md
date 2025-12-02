# Peak_Trade – Projektüberblick

Dieses Dokument fasst den aktuellen Stand des **Peak_Trade**-Projekts zusammen, damit du in neuen Chats oder auf einem anderen Rechner schnell weiterarbeiten kannst.

---

## 1. Ziel des Projekts

Peak_Trade ist ein modularer Trading-Framework-Prototyp mit Fokus auf:

- **Krypto-Backtesting** (aktuell: Kraken-Spotmarkt, OHLCV-Daten)
- **Einfache Strategien** als Einstieg (z. B. Moving-Average-Crossover)
- **Realistische Annahmen** (Fees, Slippage, Mindestordergrößen – teils bereits vorbereitet)
- Saubere Trennung von:
  - Datenbeschaffung & Caching
  - Strategielogik
  - Backtest-Engine
  - Auswertung/Statistiken
  - Skripte/Runner

Das Projekt ist so aufgebaut, dass du später:

- Weitere Börsen anbinden kannst,
- zusätzliche Strategien plug&play hinzufügen kannst,
- und langfristig einen Weg zu einem Live-Trading-Bot hast (nicht Teil des aktuellen MVP).

---

## 2. Projektstruktur (vereinfacht)

```text
Peak_Trade/
├─ src/
│  ├─ data/
│  │  └─ kraken.py          # OHLCV-Fetch + Caching
│  ├─ strategies/
│  │  └─ ma_crossover.py    # Beispielstrategie: Moving-Average-Crossover
│  ├─ backtest/
│  │  ├─ engine.py          # Backtest-Engine (Trades, PnL, Equitykurve)
│  │  └─ stats.py           # Kennzahlen & Auswertung
│  └─ __init__.py
├─ scripts/
│  └─ run_ma_realistic.py   # Runner-Skript für MA-Crossover-Backtest
└─ requirements.txt / pyproject.toml (abhängig von deiner Umgebung)
```

Die exakten Dateinamen können leicht abweichen – wichtig ist das **Konzept**: klare Module je Verantwortung.

---

## 3. Module im Detail

### 3.1 `src/data/kraken.py`

Aufgaben:

- Verbindung zur **Kraken-API** (meistens REST über `requests` oder `ccxt`)
- Laden von **OHLCV-Daten** für ein Symbol (z. B. `BTC/EUR`) und Timeframe (z. B. `1h`)
- Optionales **Caching** der Daten (z. B. lokal als CSV oder Parquet), um:
  - API-Limits zu schonen
  - Backtests schneller zu machen

Typische Funktionen (vereinfacht):

- `fetch_ohlcv(pair: str, timeframe: str, since: datetime, until: datetime) -> pd.DataFrame`
- `load_or_download_ohlcv(..., cache_path: Path) -> pd.DataFrame`

Wichtige Punkte:

- Spaltenstruktur: `timestamp`, `open`, `high`, `low`, `close`, `volume`
- Sicherstellen, dass der Index ein sortierter `DatetimeIndex` ist
- Umgang mit Lücken (fehlende Kerzen) definieren

---

### 3.2 `src/strategies/ma_crossover.py`

Beispielstrategie: **Moving Average Crossover**

Idee:

- Berechne zwei Gleitende Durchschnitte (z. B. `fast = 50`, `slow = 200`)
- **Kaufsignal**, wenn `MA_fast` von unten nach oben durch `MA_slow` kreuzt
- **Verkaufssignal**, wenn `MA_fast` von oben nach unten durch `MA_slow` kreuzt

Struktur:

- Eine Klassenstruktur wie z. B. `MACrossoverStrategy`, die eine generische Basisstrategie-Schnittstelle implementiert:
  - `on_bar(bar)` oder
  - `generate_signals(dataframe) -> signal_series`
- Parameter:
  - `fast_window: int`
  - `slow_window: int`
  - optional: `use_close_only`, `position_size` usw.

Ziel:

- Strategie ist **zustandslos** bzw. minimal zustandsbehaftet, damit der Backtester die Kontrolle über Positionsgrößen, Fees etc. hat.

---

### 3.3 `src/backtest/engine.py`

Herzstück für die Simulation.

Typische Verantwortlichkeiten:

- Schleife über alle Bars (Kerzen)
- Weitergabe der Daten/Signale an die Strategie (oder Auswertung einer Signalserie)
- Führen eines **Portfolios**:
  - Cash-Bestand
  - Offene Positionen (Entry-Preis, Größe, PnL, Fees)
- Ausführen von Trades:
  - Market/Limit (für den Anfang meist Market)
  - Abzug von **Fees** (z. B. prozentual vom Tradevolumen)
  - Optional: **Slippage** (Preisaufschlag/-abschlag)

Wichtige Outputs:

- Zeitreihe der **Equity Curve**
- Liste aller **Trades / Orders**
- Basisdaten für `stats.py` (Returns, Drawdown etc.)

---

### 3.4 `src/backtest/stats.py`

Berechnet Kennzahlen, z. B.:

- Gesamtrendite, annualisierte Rendite
- Volatilität, Sharpe-Ratio
- Maximaler Drawdown, Dauer des Drawdowns
- Winrate, durchschnittlicher Gewinn/Verlust pro Trade
- Profit-Faktor

Außerdem ggf. Helfer:

- Umwandlung der Equitykurve in tägliche/wöchentliche Returns
- Erstellung von Report-Strukturen (z. B. Dictionary, DataFrame)

---

### 3.5 `scripts/run_ma_realistic.py`

Ein Einstiegsskript, um **einen kompletten Backtest mit realistischer Konfiguration** zu starten, z. B.:

1. Laden der OHLCV-Daten über `kraken.py`
2. Erzeugen einer `MACrossoverStrategy` mit Parametern
3. Aufsetzen der Backtest-Engine (Startkapital, Fees, Slippage, Mindestgröße)
4. Ausführen des Backtests
5. Übergabe der Ergebnisse an `stats.py`
6. Ausgabe der wichtigsten Kennzahlen + optional einfache Plots (Equitykurve)

Beispielhafte CLI-Idee (Pseudo-Code):

```bash
python -m scripts.run_ma_realistic \
  --pair BTC/EUR \
  --timeframe 1h \
  --fast 50 \
  --slow 200 \
  --start 2021-01-01 \
  --end 2023-01-01
```

---

## 4. Nächste sinnvolle Schritte

Hier ein Vorschlag, wie du sinnvoll weitermachen kannst:

1. **Environment stabilisieren**
   - Sicherstellen, dass dein virtuelles Environment sauber ist
   - `requirements.txt` oder `pyproject.toml` aufräumen
   - Eventuelle SSL/`urllib3`/`OpenSSL`-Warnungen lösen (ggf. System-Python vs. Homebrew-Python trennen)

2. **Backtest-Engine fertigstellen & testen**
   - Prüfen, ob alle zentralen Methoden implementiert sind (Order-Ausführung, Fee-Handling, Slippage)
   - Mit kleinen, künstlichen Datensätzen Unit-Tests schreiben (z. B. 10 Kerzen mit bekannten Preisen)

3. **MA-Crossover-Strategie „realistisch“ machen**
   - Parameter sauber übergeben (Position Size, Max Risk pro Trade)
   - Vermeiden von Look-Ahead-Bias (Signale nur auf abgeschlossenen Kerzen)

4. **Reporting verbessern**
   - In `stats.py` eine kompakte Summary-Funktion bauen, z. B. `summarize(results)`
   - Optional: einfache Matplotlib-Plots für Equitykurve & Drawdown

5. **Dokumentation erweitern**
   - Dieses Dokument als Einstieg beibehalten
   - Weitere `HOWTO`-Abschnitte ergänzen (z. B. „Wie füge ich eine neue Strategie hinzu?“)

---

## 5. Wie du mich im neuen Chat „anfüttern“ kannst

Wenn du einen neuen Chat startest, kannst du zum schnellen Kontext einfach folgendes schreiben:

> „Das ist für mein **Peak_Trade**-Projekt. Wir haben ein Python-Backtesting-Framework mit Modulen `kraken.py`, `ma_crossover.py`, `backtest/engine.py`, `backtest/stats.py` und einem Runner-Skript `run_ma_realistic.py`. Bitte berücksichtige, dass es um Krypto-Backtests (v. a. Kraken) geht.“

Du kannst außerdem dieses `.md` hochladen oder reinkopieren, dann kann ich exakt auf diesem Stand weitermachen.

---

## 6. Vorschlag für den nächsten konkreten Schritt

Mein Vorschlag für **jetzt direkt**:

- Wir definieren gemeinsam eine minimal saubere **Schnittstelle** für die Backtest-Engine (welche Inputs, welche Outputs) **oder**
- wir bauen ein **kleines Test-Setup**, das mit Dummy-Daten prüft, ob dein MA-Crossover so handelt, wie du es erwartest.

Sag mir einfach kurz, worauf du mehr Lust hast – dann springen wir direkt in Code.
