# PR 201 – Merge Log

**Title:** test(web): make web-ui tests optional via extras + importorskip  
**Outcome:** ✅ merged (squash), branch deleted  
**Author:** rauterfrank-ui  
**Date:** 2025-12-21 (Europe/Berlin)

## Scope (What changed)
- Web-UI Tests sind optional via Extras `web`
- Web-spezifische Tests nutzen `importorskip` / Marker-basiertes Skipping statt ImportErrors
- Anpassungen in: `README.md`, `pyproject.toml`, `pytest.ini` + betroffene Web-Testdateien

## Motivation
- Core-Setup soll ohne FastAPI/Starlette/Web-Stack laufen (keine ImportErrors)
- Web-Tests sollen nur laufen, wenn der Web-Stack bewusst installiert wurde

## Breaking Change Policy
- ✅ Additiv & safe: Core bleibt ohne Web-Extras lauffähig
- ✅ Web-only Tests werden sauber **geskippt** statt zu crashen
- ✅ Keine Änderungen an Live-Trading kritischen Pfaden

## CI Results (PR)
- ✅ CI Health Gate (weekly_core)
- ✅ audit
- ✅ lint
- ✅ strategy-smoke
- ✅ tests (3.11)

## Local Verification Snapshot (post-merge)
- ✅ Ruff: pass
- ✅ Pytest: 4208 passed, 19 skipped, 3 xfailed
- ⚠️ 35 failed (matplotlib-related; separater Follow-up)

## Notes / Follow-ups
- Matplotlib-Failures separat behandeln (Optionalisierung/Extras, headless backend, eigener CI-Job)
