# UV Quickstart

[uv](https://github.com/astral-sh/uv) ist ein extrem schneller Python-Paketmanager, geschrieben in Rust.

## Installation

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Oder via Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Projekt-Setup

```bash
# Virtual Environment erstellen
uv venv

# Aktivieren
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Dependencies aus pyproject.toml installieren
uv pip install -e ".[dev]"

# Oder nur requirements.txt
uv pip install -r requirements.txt
```

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

```bash
# Neues Paket installieren
uv pip install <package-name>

# Dev-Dependency
uv pip install --extra dev <package-name>
```

## Parallel zu pip/poetry

uv arbeitet mit Standard-`pyproject.toml` und `requirements.txt`. Du kannst jederzeit zwischen uv und pip wechseln:

```bash
# Mit pip (klassisch)
pip install -r requirements.txt

# Mit uv (schneller)
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
uv venv
uv pip install -e ".[dev]"
```
