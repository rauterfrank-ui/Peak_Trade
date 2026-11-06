# CME Equity Index Futures — Roll Policy (Default)

Status: MVP / Offline-First  
NO-LIVE: Nur Backtest/Replay/Validation, keine Live-Orders.

---

## Default Roll Rule (MVP)

Für Equity Index Futures (z. B. NQ/MNQ) verwenden wir als Default:

- **Roll Date** = **Monday prior to the third Friday** of the expiration month.

Implementiert in:
- `src/markets/cme/calendar.py` (`cme_equity_index_roll_date`)

### Beispiel

- Expiration Month: **Mar 2026**
- Third Friday: **2026-03-20**
- Roll Date: **2026-03-16** (Monday)

---

## Begriffe

- **Front Month**: nächster aktiv gehandelter Kontrakt **vor** dem Roll Date.
- **Lead Month**: **nach** Roll Date i.d.R. der „second nearest“ Kontrakt.
- **Continuous Contract**: Zeitreihe, die Kontrakte über Roll Events „stitcht“ oder adjusted.

---

## Adjustment Methods (Continuous Building)

MVP unterstützt:
- **NONE** (stitch): keine Preis-Anpassung, nur Segment-Stitching
- **BACK_ADJUST**: historische Segmente werden per Offset angepasst, um am Rollpunkt zu matchen

Implementiert in:
- `src/data/continuous/continuous_contract.py`

---

## Operator-Verify Hinweis

Roll-Regeln können je nach Vendor/Institution variieren (z. B. Volumen/Open Interest basierte Rolls).
Dieses Dokument ist ein Default für deterministische Offline-Replays und muss pro Release verifiziert werden.
