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
- Deep-Links zu GitHub (tree/blob) mit Zeilen-Support
- Cursor URL-Scheme Links mit Zeilen-Sprung + Prompt-Copy
- Claude Code Terminal-Kommando Generator
- Dark Theme UI

## Syntax in der Source-TODO-Datei

```markdown
## Meine Section

- [ ] [PT-123] Aufgabe mit ID hint_path: "docs/ops/" #ops #urgent
- [ ] Task mit Zeilen-Ref hint_ref: "scripts/foo.py:120" #feature
- [ ] Task mit separatem Line hint_path: "src/core.py" hint_line: 42 #bug
- [ ] Task ohne ID (wird T0001) #feature
- [x] Erledigte Aufgabe
- [ ] DOING: Läuft gerade (Status-Override)
```

## Location Hints (Priorität)

1. **`hint_ref: "file.py:120"`** - Kombiniert Pfad + Zeile (bevorzugt)
   - Cursor springt direkt zu Zeile 120
   - GitHub öffnet Datei bei `#L120`

2. **`hint_path: "file.py"` + `hint_line: 42`** - Getrennte Angaben
   - Cursor springt zu Zeile 42
   - GitHub öffnet Datei bei `#L42`

3. **`hint_path: "src/dir/"`** - Nur Pfad
   - Cursor/GitHub öffnen Datei/Verzeichnis ohne Zeilen-Sprung

## Button-Funktionen

- **🌐 GitHub**: Öffnet Datei/Verzeichnis auf GitHub (mit `#L...` bei Zeilen-Angabe)
- **🧠 Cursor**: Kopiert Task-Prompt + öffnet Pfad (springt zu Zeile bei Angabe)
- **🤖 Claude Code**: Kopiert `cd ... && claude "..."` Kommando für Terminal

## Quell-Datei

Standard: `docs/Peak_Trade_Research_Strategy_TODO_2025-12-07.md`
Fallback: Erste `*TODO*.md` in `docs/`.

Override mit `--source-md`.

---

**Generated:** 2025-12-12 20:26:31
**Output:** `docs/00_overview/PEAK_TRADE_TODO_BOARD.html`
