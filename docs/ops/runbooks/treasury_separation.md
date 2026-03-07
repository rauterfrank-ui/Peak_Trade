# Treasury Separation

## Ziel
Trennung zwischen normalem Bot-Betrieb und Treasury-Operationen. Der Default bleibt **bot**. Treasury-only Aktionen dürfen im Bot-Kontext nicht ausführbar sein.

## Deliverables
- `config&#47;security&#47;keys.toml`
- `src&#47;ops&#47;treasury_separation_gate.py`
- `tests&#47;ops&#47;test_treasury_separation_gate.py`

## Rollen

### bot
Trading-only Runtime-Rolle.

Verboten:
- Withdrawals
- Deposit-Address-Requests
- Internal Transfers

### treasury
Separate Betriebsrolle für Treasury-Aktionen außerhalb des normalen Bot-Runtimes.

## Environment
Default:

```bash
PT_KEY_ROLE=bot
```

Für Treasury-Operationen (manuell, außerhalb Bot-Runtime):

```bash
PT_KEY_ROLE=treasury
```

## Exchange Permission Checklist
- **Bot-Key:** Nur Trading (Spot/Futures), keine Withdrawals, keine Deposit-Address-Requests, keine Internal Transfers.
- **Treasury-Key:** Withdrawals/Transfers erlaubt, kein Trading. Nur manuell nutzen.

## Secret Storage
Secrets niemals im Repo speichern. Keys nur via GitHub Actions Secrets, lokale Keychain oder externe Secret-Manager. `config&#47;security&#47;keys.toml` enthält nur Rollen-Namen und Policy, keine echten Keys.

## Pre-Pilot Operational Checks
- [ ] Bot-Key an Exchange mit minimalen Rechten erstellt
- [ ] Treasury-Key separat, nur für manuelle Treasury-Ops
- [ ] `PT_KEY_ROLE` im Bot-Runtime nicht auf `treasury` gesetzt
- [ ] Gate-Tests grün: `pytest tests&#47;ops&#47;test_treasury_separation_gate.py`

## Truth-first reference
- Canonical AI layer truth: `docs&#47;governance&#47;ai&#47;AI_LAYER_CANONICAL_SPEC_V1.md`
- Latest truth model artifacts: `out&#47;ops&#47;peak_trade_truth_model_*`
- Latest AI layer matrix artifacts: `out&#47;ops&#47;ai_layer_model_matrix_v1_*`
