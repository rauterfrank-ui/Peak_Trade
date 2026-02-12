# RUNBOOK — CME Futures Enablement (NQ/MNQ) Finish (Offline-First, NO-LIVE)

Status: DRAFT → READY wenn **Phase 0** abgeschlossen  
Owner: Operator  
Repo: Peak_Trade  
Scope: CME Equity Index Futures (NQ/MNQ) Enablement als „first-class market“ — Offline-First, deterministisch, NO-LIVE hard

---

## 0. Intent

Peak_Trade so erweitern, dass NQ/MNQ Futures in folgenden Modi konsistent laufen:

- **Backtest/Replay (Offline)** mit Continuous-Contract-Building und Session-Awareness
- **Paper/Shadow Execution** über Broker-Adapter-Hülle (initial IBKR als Interface-Referenz, aber NO-LIVE)
- **Risk-Gates** mit futures-typischen Parametern (max contracts, daily loss, fees, slippage)
- **Observability**: Roll Events, Session Gaps, Execution + Risk Blocks

**Non-Goals**
- Kein echtes Live-Trading (NO-LIVE hard)
- Kein „vollständiger“ DOM/Level2-Simulator im MVP (optional später)
- Kein Vendor-Lock (Rithmic/CQG/TT nur als Capability-Targets dokumentieren)

---

## 1. Source of Truth / Facts (Operator-Verify Pflicht)

### Contract Specs
- NQ: multiplier = 20 USD pro Indexpunkt, min tick = 0.25 Indexpunkte
- MNQ: multiplier = 2 USD pro Indexpunkt, min tick = 0.25 Indexpunkte

Derived:
- NQ tick value = 0.25 * 20 = 5.00 USD
- MNQ tick value = 0.25 * 2  = 0.50 USD

### Roll Rule (Default Policy)
- Equity index roll date = **Monday prior to the third Friday** of expiration month.
- Nach Roll Date gilt üblicherweise der „second nearest“ als lead month.

### Trading Hours / Holidays
- Trading hours + holiday schedule sind **änderbar** → Kalender nie „hard-code-blind“.
- Dieses Runbook erzwingt einen Verify-Step pro Release.

---

## 2. Definitions

- **Front Month**: nächster aktiv gehandelter Kontrakt (vor Roll Date).
- **Lead Month**: nach Roll Date üblicherweise „second nearest“.
- **Continuous Contract**: Zeitreihe, die Kontrakte über Roll Events „stitcht“ oder adjusted.
- **Adjustment**: NONE (stitch), BACK_ADJUST (klassisch), RATIO_ADJUST (optional, später).

---

## 3. Acceptance Criteria (DoD)

### Functional DoD
- [x] Contract Specs als Code-Source verfügbar (NQ/MNQ), inkl. month-codes mapping.
- [x] Roll Policy implementiert + getestet (Default = CME roll date).
- [x] Continuous builder produziert deterministische Outputs (sha256 helper + Tests).
- [x] Dataset validation (session-aware basics) + CLI Scripts vorhanden.
- [ ] Risk config kann futures-spezifische Limits erzwingen.
- [ ] Observability metrics existieren (mindestens Roll + Risk blocks).
- [x] Docs: Market Spec + Roll Policy + dieses Runbook (MVP).

### Governance DoD (NO-LIVE)
- [ ] Broker-Adapter läuft als stub/dry-run/paper; keine echten Orders.
- [ ] Tests/CI gates PASS.
- [ ] Evidence Pack mit manifest + sha256sums vorhanden.

---

## 4. Repo Targets (MVP Paths)

- `src/markets/cme/contracts.py`
- `src/markets/cme/symbols.py`
- `src/markets/cme/calendar.py`
- `src/data/continuous/continuous_contract.py`
- `scripts/markets/build_continuous_contract.py`
- `scripts/markets/validate_futures_dataset.py`
- `docs/markets/cme/NQ_MNQ_SPEC.md`
- `docs/markets/cme/ROLL_POLICY.md`
- `docs/ops/runbooks/RUNBOOK_FUTURES_CME_NQ_MNQ_ENABLEMENT_FINISH.md`
- `tests/markets/cme/test_contract_specs.py`
- `tests/data/continuous/test_continuous_contract.py`

---

## 5. Operator Pre-Flight (immer vor jedem Phase-Block)

Wenn du in einer Continuation-Prompt hängen solltest (`>`, `dquote>`, `heredoc>`): **Ctrl-C**.

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || true
pwd
git rev-parse --show-toplevel
git status -sb
```

---

## Phase 0 — Offline-First Enablement (READY Gate)

### Ziele
- Contract Specs (NQ/MNQ) als Code Source-of-Truth
- Roll-Date Policy als Code + Tests
- Continuous Contract Builder + deterministischer Hash
- Dataset Validator Script
- Docs aktualisiert

### Operator Steps

1) **Verify Facts (manuell)**
- CME NQ/MNQ Specs (multiplier, tick)
- Roll-Policy Definition (Montag vor 3. Freitag)
- (optional) Vendor/Broker Konventionen (für späteres Mapping)

2) **Run Tests**

```bash
pytest -q tests/markets/cme/test_contract_specs.py tests/data/continuous/test_continuous_contract.py
```

3) **Smoke the CLIs (optional)**

```bash
python -m scripts.markets.validate_futures_dataset --help
python -m scripts.markets.build_continuous_contract --help
```

### Exit Criteria (Phase 0 READY)
- Tests grün
- Docs vorhanden (Spec + Roll Policy + Runbook)
- Kein Codepfad führt zu Live-Order-Ausführung

---

## Phase 1+ (nicht Teil des MVP)

Als nächstes (separates Paket) kommen:
- Risk-Limits: max contracts, daily loss, fees, slippage (futures-aware)
- Observability: Roll Events, Session Gaps, Risk Blocks
- Broker Adapter Stub (IBKR Interface-Referenz) **NO-LIVE**
