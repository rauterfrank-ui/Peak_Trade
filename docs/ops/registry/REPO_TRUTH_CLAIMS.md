# REPO_TRUTH_CLAIMS — Zweck

**Status:** Registry — maschinenlesbare, prüfbare Repo-Claims  
**Konfiguration:** `config/ops/repo_truth_claims.yaml`  
**Skript:** `scripts/ops/check_repo_truth_claims.py`

## Zweck

`repo_truth_claims.yaml` fasst **einfache, deterministisch prüfbare** Aussagen über das Repo (z. B. Existenz kanonischer Pfade) zusammen. Erweiterbare `check`-Arten sind in `src/ops/truth/evaluator.py` definiert.

Die gemeinsame Schicht (Modelle, Loader, Evaluatoren) beschreibt `docs/ops/registry/TRUTH_CORE.md`.

Beispiel (NO-LIVE): Claim `cli-run-manifest-run-id-doc-present` stellt sicher, dass `docs/ops/CLI_RUN_MANIFEST_RUN_ID.md` weiterhin existiert — kanonische Beschreibung des deterministischen `run_id`-Fingerprints für CLI-Run-Manifeste (`*_run_manifest.json`).

Claim `truth-branch-protection-registry-present` hält `docs/ops/registry/TRUTH_BRANCH_PROTECTION.md` als Referenz für Required Checks / Branch-Protection-Verifikation (`ensure_truth_branch_protection.py`) fest.

## Claims (`version: 1`)

| `id` | Repo-Pfad |
| --- | --- |
| `governance-overview-present` | `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md` |
| `known-limitations-present` | `docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` |
| `docs-truth-map-registry-present` | `docs/ops/registry/DOCS_TRUTH_MAP.md` |
| `repo-truth-claims-registry-present` | `docs/ops/registry/REPO_TRUTH_CLAIMS.md` (diese Datei) |
| `truth-core-registry-present` | `docs/ops/registry/TRUTH_CORE.md` |
| `truth-branch-protection-registry-present` | `docs/ops/registry/TRUTH_BRANCH_PROTECTION.md` |
| `docs-truth-map-config-present` | `config/ops/docs_truth_map.yaml` |
| `repo-truth-claims-config-present` | `config/ops/repo_truth_claims.yaml` |
| `cli-run-manifest-run-id-doc-present` | `docs/ops/CLI_RUN_MANIFEST_RUN_ID.md` |

## Betrieb

```bash
python3 scripts/ops/check_repo_truth_claims.py
```

## Was das nicht leistet

- Kein inhaltlicher Beweis, dass referenzierte Dateien „richtig“ sind — nur dass definierte Checks **PASS** liefern.
- Keine semantische oder LLM-Prüfung.
