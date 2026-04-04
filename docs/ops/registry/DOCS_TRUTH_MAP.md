# DOCS_TRUTH_MAP — Zweck (Slice A)

**Status:** Slice A — maschinenlesbares Mapping + lokaler Drift-Check  
**Konfiguration:** `config/ops/docs_truth_map.yaml`  
**Skript:** `scripts/ops/check_docs_drift_guard.py`

## Zweck

Einige **sensible Code- und Dokumentationspfade** (Execution, Orders, Environment, zentrale Governance-/Limitations-Docs) sollen nicht **still** von den **kanonischen Beschreibungen** im Repo abdriften.

Dieses Mapping verknüpft **Bereiche** (Triggers) mit **Canonical-Docs** (mindestens eine Datei aus der Liste muss bei einer Änderung im Bereich mitgeändert werden — im selben Diff gegenüber dem gewählten Basis-Ref, z. B. `origin&#47;main`).

## Wie das Mapping funktioniert

1. Regeln stehen in `config/ops/docs_truth_map.yaml` (`rules[]`).
2. Jede Regel hat `sensitive` (Pfade) und `required_docs` (Pfadliste).
3. Das Skript ermittelt geänderte Dateien via `git diff <base>...HEAD` und prüft pro Regel:  
   **Wenn** mindestens ein `sensitive`-Pfad geändert wurde **und** **keine** der `required_docs` geändert wurde → **Fehler** (Exit 1).

Pfad-Matching:

- Endet ein Eintrag in `sensitive` mit `/`, gelten alle Repo-relativen Pfade **unter** diesem Präfix.
- Sonst exakter Pfad.

## Was das nicht leistet

- **Kein** Beweis, dass die Doku inhaltlich korrekt ist — nur dass **bewusst** mindestens eine referenzierte Canonical-Datei mitaktualisiert wurde.
- **Keine** semantische Prüfung, kein LLM.
- **Kein** Ersatz für Review, Governance oder Operator-Urteil.

## Betrieb

```bash
python3 scripts/ops/check_docs_drift_guard.py --base origin/main
```

Vor dem ersten Lauf: `git fetch origin` sinnvoll, damit `origin&#47;main` existiert.

## Operator: `orders-layer` und Canonical-Doku (Lesson PR #2242)

Kurzablauf, wenn **`src/orders/`** (Prefix-Regel) geändert wird:

1. **Regel `orders-layer`:** Im **selben Diff** wie der Code mindestens **eine** der drei Canonical-Dateien anfassen:  
   `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`, `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`, `docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md` (siehe `config/ops/docs_truth_map.yaml`).
2. **Kaskade:** Wird **`docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`** geändert, greift zusätzlich **`known-limitations-canonical`** → **`docs/ops/registry/DOCS_TRUTH_MAP.md`** (diese Datei) muss im **selben Diff** einen kurzen Nachweis bekommen (z. B. eine Zeile unter „Änderungsnachweis“).
3. **Vor Push lokal:** `python3 scripts/ops/check_docs_drift_guard.py --base origin/main`; bei Docs-Änderungen sinnvoll: `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`.

**Referenzfall (PR #2242, `src/orders/exchange.py`):** Als kleinster **orders-layer**-Nachzug reichte **eine** ergänzende Referenzzeile in `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` (die anderen beiden Canonical-Docs wären alternativ möglich gewesen).

**Hinweis:** Der Check vergleicht `git diff <base>...HEAD` — Stub-Änderungen nur an Code ohne Canonical-Doc lösen den Gate in CI ab.

## Änderungsnachweis (Slice A)

- 2026-04-04 — `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`: Referenz auf `LiveOrderExecutor`-Stub in `src/orders/exchange.py` ergänzt (Abgleich orders-layer / known-limitations-canonical).
- 2026-04-04 — Abschnitt „Operator: orders-layer … (PR #2242)“ ergänzt (Playbook für Drift-Guard); Referenzfall PEAK_TRADE als minimaler Nachzug präzisiert.
