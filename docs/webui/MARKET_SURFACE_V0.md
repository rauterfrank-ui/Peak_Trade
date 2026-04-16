# Market Surface v0 (read-only)

## Routen

| Methode | Pfad | Beschreibung |
|---------|------|----------------|
| GET | `/market` | HTML: Close-Line-Chart (Chart.js), Parameter per Query |
| GET | `/api/market/ohlcv` | JSON: OHLCV-Bars (`open`/`high`/`low`/`close`/`volume`, Zeit `ts`) |

## Query-Parameter (beide Endpunkte)

- `symbol` — z. B. `BTC&#47;USD`
- `timeframe` — `1m` \| `5m` \| `15m` \| `1h` \| `4h` \| `1d` (Kraken-Pfad; Dummy bleibt synthetisch 1h)
- `limit` — 1 … 720
- `source` — `dummy` (Default, offline) \| `kraken` (öffentliche OHLCV, Netzwerk)

Keine Kopplung an OPS Cockpit (`/ops`). Keine Trading-Aktionen.
