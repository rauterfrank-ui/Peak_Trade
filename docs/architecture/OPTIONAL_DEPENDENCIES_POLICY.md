# Optional Dependencies Policy (Hard Rules)

## Problem
Optionale Dependencies (z.B. `ccxt`) dürfen **nicht** den Import-Graph zerstören.
Sonst bricht ein „Core“-Install (ohne Extras) bereits beim `import src...` – und damit CI, Tools, Docs-Gates.

## Regeln (NON-NEGOTIABLE)
- **Allowlist**: Optionale Dependencies wie `ccxt` dürfen **nur** in `src/data/providers/**` importiert werden.
  - Erlaubt: `import ccxt` / `from ccxt ...` in `src/data/providers/**`
  - Verboten: `import ccxt` überall sonst (z.B. `src/data/**`, `src/exchange/**`, `src/data/backend.py`, usw.)
- **Core muss importierbar bleiben** (ohne Extras):
  - `import src.data`
  - `import src.data.backend`
  - `import src.exchange` (inkl. Shims)
- **Lazy Loading ist Pflicht** für Provider-Features:
  - `__getattr__` (PEP 562) in `__init__.py` **oder**
  - `factory()`/Registry mit `importlib.import_module` **oder**
  - `_load_impl()` in Shim-Modulen
- **Fehlermeldungen**:
  - Fehler wegen fehlender optionaler Dependency **dürfen nur on-demand** passieren (z.B. bei Instanziierung oder bei tatsächlichem Call wie `fetch_ohlcv`).
  - Fehlermeldung muss **hilfreich** sein: enthält mindestens „`ccxt`“ + Install-Hinweis (`pip install ccxt` / `pip install -e ".[kraken]"`).

## Enforcement (Gates)
- **Leak-Scan (harte Policy)**: `scripts/ops/check_optional_deps_leaks.sh`
  - CI-fail wenn `ccxt` außerhalb `src/data/providers/**` importiert wird.
- **Importability Gate (Packaging, E2E)**: `scripts/ops/check_optional_deps_importability.sh`
  - erstellt 2 venvs:
    - core: `pip install -e .`
    - extras: `pip install -e ".[kraken]"`
  - führt nur Imports/Init aus (kein Netzwerk).
- **Unit Tests (Importgraph)**:
  - `tests/data/test_optional_deps_imports.py`
  - `tests/exchange/test_ccxt_shims_importability.py`
- **Dev-only Typechecks (nicht required)**:
  - `.github/workflows/typecheck-pyright.yml`
  - `.github/workflows/typecheck-mypy.yml`

## How to add a new optional dependency (3 Steps)
1) **Provider kapseln**
   - Lege neue Implementierung unter `src/data/providers/<provider>.py` an und importiere dort das SDK.
2) **Shim/Lazy Entry hinzufügen**
   - Exponiere den Provider über `__getattr__`/Factory/`_load_impl()` – aber **ohne** SDK-Import beim Modulimport.
3) **Gates erweitern**
   - Leak-Scan Allowlist bleibt `providers/**` (bei Bedarf: neue allowlist-Pfade explizit diskutieren).
   - Ergänze/aktualisiere Importability-Checks + einen kleinen Unit-Test, der „Import ohne SDK“ beweist.

## Quick Commands (Local)
- Leak-Scan:

```bash
bash scripts/ops/check_optional_deps_leaks.sh
```

- Packaging Importability Gate:

```bash
bash scripts/ops/check_optional_deps_importability.sh
```
