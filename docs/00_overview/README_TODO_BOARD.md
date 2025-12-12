# Peak_Trade – TODO Board

Dieses TODO Board wird automatisch aus einer Markdown-TODO-Datei generiert.

## Generieren

```bash
python3 scripts/build_todo_board_html.py
```

Öffne dann `docs/00_overview/PEAK_TRADE_TODO_BOARD.html` in deinem Browser.

## Features

- 3-spaltige Kanban-Ansicht (TODO, DOING, DONE)
- Echtzeit-Suche über Text, IDs, Tags, Sections, Pfade
- Deep-Links zu GitHub (tree/blob)
- Cursor URL-Scheme Links mit Prompt-Copy
- Claude Code Terminal-Kommando Generator
- Dark Theme UI

## Syntax in der Source-TODO-Datei

```markdown
## Meine Section

- [ ] [PT-123] Aufgabe mit ID hint_path: "docs/ops/" #ops #urgent
- [ ] Task ohne ID (wird T0001) #feature
- [x] Erledigte Aufgabe
- [ ] DOING: Läuft gerade (Status-Override)
```

## Button-Funktionen

- **🌐 GitHub**: Öffnet Datei/Verzeichnis auf GitHub (nur aktiv bei `hint_path`)
- **🧠 Cursor**: Kopiert Task-Prompt + öffnet Pfad in Cursor
- **🤖 Claude Code**: Kopiert `cd ... && claude "..."` Kommando für Terminal

## Quell-Datei

Standard: `docs/Peak_Trade_Research_Strategy_TODO_2025-12-07.md`
Fallback: Erste `*TODO*.md` in `docs/`.

Override mit `--source-md`.

---

**Generated:** 2025-12-12 20:07:46
**Output:** `docs/00_overview/PEAK_TRADE_TODO_BOARD.html`
