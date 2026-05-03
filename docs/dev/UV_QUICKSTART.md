# UV Quickstart

[uv](https://github.com/astral-sh/uv) ist ein extrem schneller Python-Paketmanager, geschrieben in Rust.

Für den **Peak Trade–Kanon** (englischer Überblick) siehe [Development Tooling](tooling.md) — dieser Text ist eine **kurze deutschsprachige** Einstiegshilfe und folgt dort demselben **`uv sync`‑first**‑Setup.

## Installation

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Oder via Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Projekt-Setup ( empfohlener Pfad )

Das Repository enthält bereits **`pyproject.toml`** und ein **`uv.lock`** (von git versioniert). Arbeite im geklonten Repo-Root:

```bash
# Abhängigkeiten aus Lockfile/projektbezug installieren (legt bei Bedarf .venv an)
uv sync

# Mit Dev-/Tooling‑Gruppe (dependency groups / dev extras wie in pyproject.toml)
uv sync --dev

# Aktivieren
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

So bleiben Peak Trade und die englischen **Development Tooling**‑Doku konsistent (**`tooling.md`**: `uv sync`, `uv sync --dev`, `uv add`, `uv add --dev`).

### Legacy / Alternative (ohne Primärstellung)

Ältere Anleitungen nutzen häufig `uv pip`‑ oder klassische‑pip‑Pfade — die sind **nachrangig**, wenn ihr mit **`uv.lock`** arbeiten wollt:

```bash
# Nachrangig (manuellen venv anlegen — sync legt ihn i. d. R. selbst an)
uv venv
source .venv/bin/activate

# Nachrangig: editable install ohne sync-first Narrativ des Repos
uv pip install -e ".[dev]"
# Nur requirements.txt ohne Lockfile-Fokus
uv pip install -r requirements.txt
```

Bevorzuge **immer** Kombination **`uv sync`** plus bei Bedarf **`uv sync --dev`**, wenn keine spezielle Legacy‑Notwendigkeit vorliegt.

## Tägliche Nutzung

```bash
# Virtualenv aktivieren
source .venv/bin/activate  # Linux/macOS

# Tests ausführen
python3 -m pytest tests/ -v

# Einzelnen Test
python3 -m pytest tests/test_basics.py -v

# Mit Coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Linting
ruff check src tests scripts

# Formatting prüfen
ruff format --check src tests scripts

# Formatting anwenden
ruff format src tests scripts
```

## Paket hinzufügen

Wie **`tooling.md`**: Abhängigkeiten ins Projekt über **`uv add`** aufnehmen (nicht `uv pip install` für den Routine-Umgang):

```bash
# Runtime-Abhängigkeit
uv add <package-name>

# Dev-/Gruppenbezug (--dev entspricht dem üblichen Dev-Workflow hier)
uv add --dev <package-name>
```

## Parallel zu klassischem pip

`uv pip` und `pip` sind weiterhin möglich, verlassen aber den **Sync‑ und Lockfile‑Kanon** mit `uv.lock`. Nutze sie nach Bedarf bei Integration in externe Umgebungen, nicht für den Standard‑Onboardingspfad dieses Repos.

```bash
# Beispiele (Alternative, nicht Hauptpfad)
pip install -r requirements.txt
uv pip install -r requirements.txt
```

## Performance-Vergleich

| Operation          | pip      | uv       |
|--------------------|----------|----------|
| Clean install      | ~45s     | ~3s      |
| Cached install     | ~12s     | <1s      |

## Troubleshooting

### Cache leeren
```bash
uv cache clean
```

### Virtualenv neu erstellen
```bash
rm -rf .venv
uv sync --dev
```
