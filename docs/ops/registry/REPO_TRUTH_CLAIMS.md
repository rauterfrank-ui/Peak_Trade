# REPO_TRUTH_CLAIMS — Zweck

**Status:** Registry — maschinenlesbare, prüfbare Repo-Claims  
**Konfiguration:** `config/ops/repo_truth_claims.yaml`  
**Skript:** `scripts/ops/check_repo_truth_claims.py`

## Zweck

`repo_truth_claims.yaml` fasst **einfache, deterministisch prüfbare** Aussagen über das Repo (z. B. Existenz kanonischer Pfade) zusammen. Erweiterbare `check`-Arten sind in `src/ops/truth/evaluator.py` definiert.

Die gemeinsame Schicht (Modelle, Loader, Evaluatoren) beschreibt `docs/ops/registry/TRUTH_CORE.md`.

Beispiel (NO-LIVE): Claim `cli-run-manifest-run-id-doc-present` stellt sicher, dass `docs/ops/CLI_RUN_MANIFEST_RUN_ID.md` weiterhin existiert — kanonische Beschreibung des deterministischen `run_id`-Fingerprints für CLI-Run-Manifeste (`*_run_manifest.json`).

## Betrieb

```bash
python3 scripts/ops/check_repo_truth_claims.py
```

## Was das nicht leistet

- Kein inhaltlicher Beweis, dass referenzierte Dateien „richtig“ sind — nur dass definierte Checks **PASS** liefern.
- Keine semantische oder LLM-Prüfung.
