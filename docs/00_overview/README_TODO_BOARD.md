# Peak_Trade – TODO Board

Dieses TODO Board wird automatisch aus einer Markdown-TODO-Datei generiert.

## Generieren

```bash
python3 scripts/build_todo_board_html.py
```

## Öffnen

```bash
open docs/00_overview/PEAK_TRADE_TODO_BOARD.html
```

## Features

- **3-Spalten Kanban**: TODO / DOING / DONE
- **Auto-IDs**: Wenn keine explizite `[ID]` in der Zeile → automatische T0001, T0002, …
- **GitHub-Links**: Bei `hint_path: "..."` wird ein Button zu GitHub generiert
- **Tags**: `#ops`, `#docs`, etc. werden erkannt und angezeigt
- **Suche**: Echtzeit-Filter über Text, ID, Tags, Sections, Pfade
- **Dark Theme**: Modern und responsive

## Syntax-Beispiele

```markdown
## Phase 1: Strategie-Forschung

- [ ] Armstrong-Strategie finalisieren [PT-001] hint_path: "src/strategies/armstrong/" #research #prio
- [ ] Backtesting durchführen (doing) hint_path: "tests/backtest/" #testing
- [x] Initial Prototype hint_path: "docs/prototypes/"
```

Status-Keywords:
- `(doing)`, `(wip)`, `(in arbeit)` → Status DOING
- `[x]` → Status DONE
- Sonst → Status TODO

Generiert: 2025-12-12 19:17:10
