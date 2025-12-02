# Peak_Trade – Data-Layer & Demo-Pipeline

Stand: Session-Abbruch nach erfolgreicher Einrichtung von Data-Layer-Struktur und Umgebungsvorbereitung.

---

## 1. Überblick

In dieser Session haben wir den **Data-Layer** für dein Projekt `Peak_Trade` konzipiert und (größtenteils) implementiert. Ziel:

- Rohdaten (z. B. aus Kraken-Exports oder anderen CSVs) einlesen,
- in ein **standardisiertes OHLCV-Format** bringen,
- optional auf andere Timeframes resamplen,
- die normalisierten Daten als **Parquet** cachen,
- und sie direkt an deine **BacktestEngine** und Strategien übergeben.

Du hast jetzt:

- einen neuen `src/data/`‑Namespace mit Loader, Normalizer und Cache,
- ein Demoprogramm `demo_data_pipeline.py` im Projekt-Root,
- eine funktionierende `.venv` mit `pandas`, `numpy`, `pyarrow`.

---

## 2. Projektstruktur (relevante Teile)

```text
Peak_Trade/
├─ .venv/                      # Virtuelle Umgebung
├─ demo_data_pipeline.py       # Demo-Script für die komplette Data-Pipeline
├─ src/
│  ├─ backtest/
│  │  └─ ...                   # Deine BacktestEngine etc.
│  └─ data/
│     ├─ __init__.py           # Zentrale Exports + REQUIRED_OHLCV_COLUMNS
│     ├─ loader.py             # CsvLoader, KrakenCsvLoader
│     ├─ normalizer.py         # DataNormalizer, resample_ohlcv
│     ├─ cache.py              # ParquetCache
│     └─ kraken.py             # (bereits vorher vorhanden, Kraken-spezifisch)
└─ ...
```

Optional (falls noch nicht angelegt, aber geplant):

- `src/data/examples.py` – reine Doku-Beispiele (NotImplementedError).

---

## 3. `src/data/__init__.py` – Zentrale Exports & Konstante

Wichtige Punkte:

- **Konstante zuerst definieren**, dann Module importieren, um Reihenfolge-/Init-Probleme zu vermeiden.
- Eine einzige `__all__`‑Liste, die alles Wichtige exportiert.

Kerninhalt sinngemäß:

```python
"""
Peak_Trade Data Module
======================
Datenbeschaffung, Normalisierung, Caching und Preprocessing.
"""

# Wichtig: Konstante VOR den Modul-Imports definieren
REQUIRED_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

from .kraken import get_kraken_client, fetch_ohlcv_df, clear_cache
from .loader import CsvLoader, KrakenCsvLoader
from .normalizer import DataNormalizer, resample_ohlcv
from .cache import ParquetCache

__all__ = [
    "REQUIRED_OHLCV_COLUMNS",
    "get_kraken_client",
    "fetch_ohlcv_df",
    "clear_cache",
    "CsvLoader",
    "KrakenCsvLoader",
    "DataNormalizer",
    "resample_ohlcv",
    "ParquetCache",
]
```

Wichtig: In `normalizer.py` und `cache.py` wird `REQUIRED_OHLCV_COLUMNS` mit

```python
from . import REQUIRED_OHLCV_COLUMNS
```

importiert – deshalb muss die Konstante beim Import des Pakets bereits existieren.

---

## 4. `loader.py` – CsvLoader & KrakenCsvLoader

Zweck: Rohdaten laden, **ohne** sich um Normalisierung zu kümmern.

### 4.1 `CsvLoader`

- Lädt generische CSV-Dateien mit `pandas.read_csv`.
- Parameter:
  - `delimiter=","`
  - `decimal="."`
  - `parse_dates=True` → erste Spalte wird als Datum geparst und als Index gesetzt (`index_col=0`).
- Fehlerhandling:
  - `FileNotFoundError`, wenn Pfad nicht existiert,
  - `ValueError`, wenn `pandas.read_csv` fehlschlägt.

Typischer Use-Case im Demo:

- CSV hat eine Spalte `timestamp` als erste Spalte → wird Index.

### 4.2 `KrakenCsvLoader`

- Subklasse von `CsvLoader` mit `parse_dates=False`.
- Erwartet eine Spalte `time` (Unix-Timestamp in Sekunden).
- Verhalten:
  - Timestamp → `pd.to_datetime(..., unit="s", utc=True)`,
  - wird als Index gesetzt,
  - Spalte `time` wird entfernt.
- Ideal für Kraken-OHLC-Exporte: `time, open, high, low, close, vwap, volume, count`.

---

## 5. `normalizer.py` – DataNormalizer & resample_ohlcv

Zweck: DataFrames in das **Peak_Trade-Standardformat** bringen.

### 5.1 `DataNormalizer.normalize(...)`

**Annahmen:**

- Der DataFrame hat bereits einen `DatetimeIndex` (z. B. durch `CsvLoader` oder `KrakenCsvLoader`).
- Der Index kann naive oder tz-aware sein.

**Schritte:**

1. **Index prüfen**
   - Wenn kein `DatetimeIndex` → `ValueError`.
   - Wenn `ensure_utc=True`:
     - naive: `tz_localize("UTC")`,
     - andere TZ: `tz_convert("UTC")`.

2. **Spalten-Mapping**
   - Optionales `column_mapping` (z. B. `"Open" -> "open"`).
   - Alle Spaltennamen werden nach `lower()` konvertiert.

3. **OHLCV-Validierung**
   - Prüft, dass alle `REQUIRED_OHLCV_COLUMNS` vorhanden sind.
   - Wenn nicht → `ValueError` mit Liste der fehlenden Spalten.

4. **Extra-Spalten**
   - Bei `drop_extra_columns=True` werden nur `open, high, low, close, volume` behalten.

5. **Sortierung & Duplikate**
   - Sortierung nach Index (`sort_index()`).
   - Duplikate im Index → letzter Eintrag bleibt.

6. **Datentypen**
   - Alle OHLCV-Spalten → `float`.

### 5.2 `resample_ohlcv(df, freq, ...)`

- Erwartet einen **normalisierten** OHLCV-DataFrame.
- Validiert erneut:
  - `DatetimeIndex`,
  - OHLCV-Spalten vollständig.
- Aggregation:
  - `open`: `first()`,
  - `high`: `max()`,
  - `low`: `min()`,
  - `close`: `last()`,
  - `volume`: `sum()`.
- Entfernt Bars, in denen **alle** OHLC-Werte `NaN` sind.

---

## 6. `cache.py` – ParquetCache

Zweck: Normalisierte OHLCV-Daten schnell speichern und laden.

### 6.1 Konstruktor

```python
cache = ParquetCache(cache_dir="./data_cache")
```

- Legt das Cache-Verzeichnis automatisch an (`os.makedirs(..., exist_ok=True)`).

### 6.2 `save(df, key, compression="snappy")`

- Validiert:
  - `DatetimeIndex`,
  - OHLCV-Spalten vorhanden.
- Leitet Dateipfad aus dem `key` ab:
  - Sanitizing (unerlaubte Zeichen → `_`),
  - Dateiname: `<sanitized_key>.parquet`.
- Schreibt mit `df.to_parquet(path, compression=compression)`.

### 6.3 `load(key)`

- Leitet Pfad analog zu `save` ab.
- Wenn Datei fehlt → `FileNotFoundError`.
- Lädt mit `pd.read_parquet(path)`.

### 6.4 `exists(key)` & `clear(key=None)`

- `exists` prüft, ob die entsprechende Parquet-Datei existiert.
- `clear`:
  - Ohne Argument: löscht alle `*.parquet` im Cache-Verzeichnis.
  - Mit `key`: löscht die eine Datei, falls vorhanden.

---

## 7. `demo_data_pipeline.py` – End-to-End-Demo

Diese Datei liegt im **Projekt-Root** (`Peak_Trade/demo_data_pipeline.py`).  
Sie zeigt die komplette Pipeline von Fake-Daten bis Backtest.

### 7.1 Schritte im Script (High Level)

1. **Künstliche OHLCV-Daten erzeugen**
   - Random-Walk für `close`,
   - konsistente `open/high/low`,
   - zufällige Volumenwerte,
   - 1-Minuten-Timestamps (`freq="1T"`).

2. **CSV schreiben**
   - Output nach `data_temp/test_ohlcv.csv`.

3. **CSV laden**
   - Mit `CsvLoader`,
   - Index wird automatisch als Datum geparst.

4. **Normalisieren**
   - Mit `DataNormalizer.normalize(...)` + `column_mapping`:
     - `"Open" -> "open"`, etc.

5. **Resamplen**
   - `resample_ohlcv(df_norm, freq="1H")` → 1-Stunden-Bars.

6. **Cachen**
   - `ParquetCache.save(df_1h, key="TEST_1H")`,
   - `ParquetCache.load("TEST_1H")` zum Test.

7. **Backtest**
   - Übergibt den gecachten DataFrame an `BacktestEngine.run_realistic(...)`,
   - nutzt z. B. `ma_crossover` als Strategie,
   - gibt `result.stats`, Equity-Curve und ggf. Trades aus.

---

## 8. Umgebung & Installation

### 8.1 Virtuelle Umgebung aktivieren

Im Projekt-Root (`/Users/frnkhrz/Peak_Trade`):

```bash
cd ~/Peak_Trade
source .venv/bin/activate
```

Das Prompt sollte dann mit `(.venv)` beginnen.

### 8.2 Wichtige Pakete installieren

Einmalig in der aktivierten `.venv`:

```bash
pip install --upgrade pip setuptools wheel
pip install pandas numpy pyarrow
```

- `pandas` – DataFrames, CSV, Parquet,
- `numpy` – numerische Grundlagen,
- `pyarrow` – Parquet-Engine.

---

## 9. Demo ausführen

Mit aktivierter `.venv` und im Projekt-Root:

```bash
python demo_data_pipeline.py
```

Erwartetes Verhalten:
- Ausgabe der einzelnen Schritte (SCHRITT 1–6),
- am Ende Backtest-Statistiken und ggf. Trades.

Wenn Python die Datei nicht findet, prüfen:

- `pwd` muss `.../Peak_Trade` sein,
- `demo_data_pipeline.py` muss **direkt** in diesem Ordner liegen, nicht unter `src/` oder `src/data/`.

---

## 10. Nächste sinnvolle Schritte

1. **Stabilität & Tests**
   - Pytest-Tests für:
     - `CsvLoader` / `KrakenCsvLoader`,
     - `DataNormalizer.normalize` mit verschiedenen Mappings,
     - `resample_ohlcv` (Edge-Cases, leere Intervalle),
     - `ParquetCache` (save/load/exists/clear).

2. **Integration mit echten Daten**
   - Kraken-Client (`src/data/kraken.py`) mit dem neuen Data-Layer verheiraten,
   - echte OHLC-Dumps laden und in den gleichen OHLCV-Standard bringen.

3. **Weiterer Ausbau**
   - Data-Layer-Hooks in Backtest-Skripte,
   - später: Quant-Layer (El-Karoui, BSDE, HJB) on top.

---

## 11. Zusammenfassung in einem Satz

Du hast jetzt einen sauberen, modularen **Data-Layer** in `src/data/` plus eine **End-to-End-Demo**, die zeigt, wie Daten von „Roh-CSV“ über Normalisierung, Resampling und Parquet-Cache bis hin zur BacktestEngine durchgereicht werden – alles innerhalb deiner `.venv` lauffähig und erweiterbar für reale Marktdaten und spätere Quant-Modelle.
