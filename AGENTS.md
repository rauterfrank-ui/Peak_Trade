# Peak_Trade Agent Entrypoint

```text
CANONICAL_MAP_OF_TRUTH_PATH=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
READ_BEFORE_MUTATION=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
NO_PARALLEL_SEMANTIC_MODEL=true
```

- Vor jeder Mutation: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` vollständig lesen.
- Navigations-Einstieg ohne eigene Semantik: `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`.
- Runtime-Wahrheit stammt aus Code, Config, Persistenz und Evidence — nicht aus dem Runbook allein.
- Bei Drift zwischen Runbook und Runtime-Wahrheit: fail-closed stoppen.
- Kein Live-, Testnet-, Order-, Credential- oder Real-Capital-Recht aus Dokumentation ableiten.
- Git nur im echten lokalen Repository über das lokale Terminal; Cursor-Sandbox-Git ist verboten.
- Untracked Evidence unverändert erhalten.
