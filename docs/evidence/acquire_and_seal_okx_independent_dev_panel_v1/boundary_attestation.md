# Boundary attestation — sealed holdout non-access

## Opaque exclusion only

- Holdout evidence ID: `offline_economic_reevaluation_sealed_long_panel_v1`
- Development panel ends exclusively at registry holdout start `2023-08-16T05:55:00Z`
- No read/copy/derive of holdout pack contents, bars, metrics, or instrument lists

## Acquisition sources used

- Production lifecycle registry snapshot (external, digest `ddcdec73…`)
- Public OKX endpoints only: `/api/v5/public/instruments`, `/api/v5/market/history-candles`
- Existing scaffold `src/research/longer_chronological_pit_acquisition_v1/`

## Explicit non-use

- No sealed-holdout economic metrics
- No performance-based instrument selection
- No authenticated / private OKX endpoints
