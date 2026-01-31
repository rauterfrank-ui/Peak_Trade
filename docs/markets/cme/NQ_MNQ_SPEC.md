# CME Equity Index Futures — NQ / MNQ (MVP Spec)

Status: MVP / Offline-First  
Scope: Contract Specs + Roll Policy Inputs für Backtest/Replay  
NO-LIVE: Dieses Paket beinhaltet **keine** Broker-Anbindung und keine Live-Order-Ausführung.

---

## Source of Truth (Operator-Verify Pflicht)

Diese Werte müssen pro Release gegen CME Rulebook / Broker-Spezifikationen verifiziert werden.

### NQ (E-mini Nasdaq-100)
- **Symbol Root**: `NQ`
- **Multiplier**: 20 USD pro Indexpunkt
- **Min Tick**: 0.25 Indexpunkte
- **Tick Value**: \(0.25 \times 20 = 5.00\) USD
- **Currency**: USD

### MNQ (Micro E-mini Nasdaq-100)
- **Symbol Root**: `MNQ`
- **Multiplier**: 2 USD pro Indexpunkt
- **Min Tick**: 0.25 Indexpunkte
- **Tick Value**: \(0.25 \times 2 = 0.50\) USD
- **Currency**: USD

---

## Code Source (Peak_Trade)

- Specs als Code: `src/markets/cme/contracts.py`
- Month Codes & Symbol Format: `src/markets/cme/symbols.py`

### Kanonisches Symbolformat (MVP)

Peak_Trade nutzt intern ein deterministisches Format:

- `{ROOT}{MONTH_CODE}{YEAR4}` (Beispiel: `NQH2026`)

Hinweis: Viele Vendoren/Broker nutzen andere Varianten (z. B. `NQH6`, `NQ 03-26`, etc.).
Diese werden später bei Bedarf über Mapper/Adapter normalisiert.

---

## Session / Kalender

MVP enthält einen vereinfachten Session-Spec (konfigurierbar), primär für Offline-Validierung:

- `src/markets/cme/calendar.py`

Holiday Schedules sind im MVP **nicht** vollständig modelliert.
