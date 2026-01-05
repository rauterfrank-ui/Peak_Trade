# Pre-commit Setup

Pre-commit-Hooks laufen automatisch vor jedem Commit und stellen Code-Qualität sicher.

## Installation

```bash
# Pre-commit installieren
pip install pre-commit
# oder
uv pip install pre-commit

# Hooks aktivieren (einmalig pro Clone)
pre-commit install
```

## Konfigurierte Hooks

| Hook | Beschreibung |
|------|--------------|
| `ruff` | Python Linter (mit auto-fix) |
| `ruff-format` | Python Formatter |
| `trailing-whitespace` | Entfernt trailing whitespace |
| `end-of-file-fixer` | Stellt newline am Dateiende sicher |
| `check-yaml` | Validiert YAML-Syntax |
| `check-added-large-files` | Warnt bei Dateien >1MB |
| `check-merge-conflict` | Erkennt ungelöste Merge-Konflikte |

## Nutzung

```bash
# Hooks laufen automatisch bei git commit
git commit -m "feat: my change"

# Manuell alle Dateien prüfen
pre-commit run --all-files

# Einzelnen Hook ausführen
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files

# Hooks aktualisieren
pre-commit autoupdate
```

## Bypass (nur wenn nötig)

```bash
# Hooks überspringen (nur in Ausnahmefällen!)
git commit --no-verify -m "wip: emergency fix"
```

## Troubleshooting

### Hooks schlagen fehl
```bash
# Meist reicht ein erneuter Commit nach Auto-Fixes
git add -u
git commit -m "fix: apply linter fixes"
```

### Hooks neu installieren
```bash
pre-commit uninstall
pre-commit install
```
