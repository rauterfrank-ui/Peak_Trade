# Truth Branch Protection — `main`

**Zweck:** Sicherstellen, dass die stabilen Job-Namen aus `.github/workflows/truth_gates_pr.yml` in der **klassischen** Branch Protection von `main` als **Required status checks** eingetragen sind:

- `docs-drift-guard`
- `repo-truth-claims`

**Skript:** `scripts/ops/ensure_truth_branch_protection.py`

| Modus | Verhalten |
| --- | --- |
| `--check` | Nur lesen (`gh api` GET). Exit `0`, wenn beide Kontexte vorhanden sind; sonst `1`. |
| `--apply` | Fehlende Kontexte in `required_status_checks.contexts` mergen und per PUT setzen (Schreibrechte / Admin nötig). |

**Voraussetzungen:** `gh` installiert und authentifiziert; Token mit Leserecht auf Branch Protection, für `--apply` zusätzlich Schreibrecht.

**Standard-Repo:** Owner `rauterfrank-ui`, Repo `Peak_Trade`, Branch `main` (über CLI-Flags überschreibbar).

Siehe auch `docs/ops/registry/TRUTH_CORE.md` für die Truth-Schicht der Checks selbst.
