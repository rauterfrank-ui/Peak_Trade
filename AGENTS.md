# Peak_Trade Agent Entrypoint

```text
CANONICAL_MAP_OF_TRUTH_PATH=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
READ_BEFORE_MUTATION=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
NO_PARALLEL_SEMANTIC_MODEL=true
CANONICAL_PYTHON_LAUNCHER=scripts/pt
CANONICAL_PYTHON_INTERPRETER=.venv/bin/python
REQUIRES_PYTHON=>=3.10
```

- Vor jeder Mutation: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` vollständig lesen.
- Navigations-Einstieg ohne eigene Semantik: `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`.
- Runtime-Wahrheit stammt aus Code, Config, Persistenz und Evidence — nicht aus dem Runbook allein.
- Bei Drift zwischen Runbook und Runtime-Wahrheit: fail-closed stoppen.
- Kein Live-, Testnet-, Order-, Credential- oder Real-Capital-Recht aus Dokumentation ableiten.
- Git nur im echten lokalen Repository über das lokale Terminal; Cursor-Sandbox-Git ist verboten.
- Untracked Evidence unverändert erhalten.
- Lokale CI-Dedup&#47;Reuse-Orchestrierung (Master Runbook §15.3): `docs&#47;ops&#47;specs&#47;GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md` — kein redundantes Suite-Re-Run nur für Evidence&#47;Verifier&#47;Pre-PR bei identischem gebundenem PASS.
- Python-Ausführung: nur `scripts/pt` bzw. `make` targets, die darauf delegieren. Nie PATH `python`/`python3`, nie `source .venv/bin/activate` als Korrektheitsmechanismus, nie `PYTHONPATH` als Runtime-Workaround. Vertrag: `docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md`. Bei Validation-Fail: HARD STOP.
