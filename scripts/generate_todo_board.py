#!/usr/bin/env python3
"""
Peak Trade TODO-Board Generator

Generiert das TODO-Board aus config/todo_board.yaml in verschiedenen Formaten:
- Markdown (docs/ops/todo/PEAK_TRADE_TODO_BOARD.md)
- HTML (docs/ops/todo/todo_board.html)

Alle sichtbaren Texte sind in Deutsch.
Technische Status-Werte (DONE, NEXT, etc.) bleiben im YAML Englisch,
werden aber in der Ausgabe deutsch dargestellt.

Usage:
    python scripts/generate_todo_board.py [--format markdown|html|both]
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict


# Mapping: Technische Status → Deutsche Anzeige
STATUS_DISPLAY = {
    "DONE": {"icon": "✅", "text": "Erledigt", "emoji": "✅"},
    "IN_PROGRESS": {"icon": "🟡", "text": "In Arbeit", "emoji": "🟡"},
    "NEXT": {"icon": "⏭️", "text": "Als Nächstes", "emoji": "⏭️"},
    "BLOCKED": {"icon": "⛔", "text": "Blockiert", "emoji": "⛔"},
    "TECH_DEBT": {"icon": "🧊", "text": "Tech-Schulden", "emoji": "🧊"},
    "FUTURE": {"icon": "🩶", "text": "Zukunft", "emoji": "🩶"},
}

PRIORITY_DISPLAY = {
    "HIGH": {"icon": "🔴", "text": "Hoch"},
    "MEDIUM": {"icon": "🟡", "text": "Mittel"},
    "LOW": {"icon": "🟢", "text": "Niedrig"},
}

STREAM_COLORS = {
    "research": "🔵 Blue",
    "live": "🟢 Green",
    "infra": "🟣 Purple",
    "governance": "🟠 Orange",
}


def load_config(config_path: Path) -> Dict[str, Any]:
    """Lädt die TODO-Board-Konfiguration aus YAML."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_markdown(config: Dict[str, Any], output_path: Path) -> None:
    """Generiert Markdown-Board."""

    todos = config.get('todos', [])
    streams = {s['id']: s for s in config.get('streams', [])}

    # Gruppiere Tasks nach Status
    by_status = defaultdict(list)
    for todo in todos:
        by_status[todo['status']].append(todo)

    # Beginne Markdown
    md = []
    md.append("# Peak Trade TODO-Board\n")
    md.append(f"**Stand:** {datetime.now().strftime('%Y-%m-%d')}")
    md.append("**Quelle:** `config/todo_board.yaml`\n")
    md.append("---\n")

    # Status-Legende
    md.append("## Status-Legende\n")
    md.append("| Status | Bedeutung | Icon |")
    md.append("|--------|-----------|------|")
    for status, display in STATUS_DISPLAY.items():
        md.append(f"| {display['emoji']} {display['text']} | {_get_status_description(status)} | {display['emoji']} {status} |")
    md.append("")

    # Prioritäts-Legende
    md.append("## Prioritäts-Legende\n")
    md.append("| Priorität | Beschreibung |")
    md.append("|-----------|--------------|")
    md.append("| 🔴 HIGH | Kritisch, hohe Priorität |")
    md.append("| 🟡 MEDIUM | Mittlere Priorität |")
    md.append("| 🟢 LOW | Niedrige Priorität, Nice-to-have |")
    md.append("\n---\n")

    # Aktive Tasks (IN_PROGRESS & NEXT)
    md.append("## Aktive Tasks (In Arbeit & Als Nächstes)\n")

    if by_status.get('IN_PROGRESS'):
        md.append("### 🟡 In Arbeit\n")
        md.append("| ID | Titel | Priorität | Stream | Tags |")
        md.append("|----|-------|-----------|--------|------|")
        for todo in by_status['IN_PROGRESS']:
            stream_name = streams.get(todo['stream'], {}).get('name', todo['stream'])
            priority = PRIORITY_DISPLAY[todo['priority']]['icon'] + " " + todo['priority']
            tags = ", ".join(todo.get('tags', []))
            md.append(f"| {todo['id']} | {todo['title']} | {priority} | {stream_name} | {tags} |")
        md.append("")

        # Details zu IN_PROGRESS Tasks
        for todo in by_status['IN_PROGRESS']:
            md.append(f"**{todo['id']}: {todo['title']}**")
            md.append(f"- **Beschreibung:** {todo['description']}")
            md.append(f"- **Status:** {STATUS_DISPLAY['IN_PROGRESS']['emoji']} {STATUS_DISPLAY['IN_PROGRESS']['text']}")
            if todo.get('notes'):
                md.append(f"- **Hinweise:** {todo['notes']}")
            md.append("")
        md.append("---\n")

    if by_status.get('NEXT'):
        md.append("### ⏭️ Als Nächstes\n")
        md.append("| ID | Titel | Priorität | Stream | Tags |")
        md.append("|----|-------|-----------|--------|------|")
        for todo in by_status['NEXT']:
            stream_name = streams.get(todo['stream'], {}).get('name', todo['stream'])
            priority = PRIORITY_DISPLAY[todo['priority']]['icon'] + " " + todo['priority']
            tags = ", ".join(todo.get('tags', []))
            md.append(f"| {todo['id']} | {todo['title']} | {priority} | {stream_name} | {tags} |")
        md.append("")

        # Details zu NEXT Tasks
        for todo in by_status['NEXT']:
            md.append(f"**{todo['id']}: {todo['title']}**")
            md.append(f"- **Beschreibung:** {todo['description']}")
            md.append(f"- **Status:** {STATUS_DISPLAY['NEXT']['emoji']} {STATUS_DISPLAY['NEXT']['text']}")
            md.append(f"- **Priorität:** {PRIORITY_DISPLAY[todo['priority']]['icon']} {PRIORITY_DISPLAY[todo['priority']]['text']}")
            if todo.get('notes'):
                md.append(f"- **Hinweise:** {todo['notes']}")
            md.append("")
        md.append("---\n")

    # Abgeschlossene Tasks
    if by_status.get('DONE'):
        md.append("## Abgeschlossene Tasks\n")
        md.append("| ID | Titel | Stream | Letzte Änderung |")
        md.append("|----|-------|--------|-----------------|")
        for todo in by_status['DONE']:
            stream_name = streams.get(todo['stream'], {}).get('name', todo['stream'])
            md.append(f"| {todo['id']} | {todo['title']} | {stream_name} | {todo['last_updated']} |")
        md.append("")

        md.append("**Details zu abgeschlossenen Tasks:**\n")
        for todo in by_status['DONE']:
            if todo.get('notes'):
                md.append(f"- **{todo['id']} ({todo['title']}):** {todo['notes']}")
        md.append("\n---\n")

    # Grey-Track (FUTURE Tasks)
    if by_status.get('FUTURE'):
        md.append("## 🩶 Zukünftige Tasks (Grey-Track)\n")
        md.append('<div style="opacity: 0.6; color: #666;">\n')

        # Gruppiere FUTURE nach Priorität/Timeframe
        md.append("### Mittelfristig (48 Sessions)\n")
        md.append("| ID | Titel | Priorität | Dependencies |")
        md.append("|----|-------|-----------|--------------|")

        for todo in by_status['FUTURE']:
            if todo['id'] in ['R7', 'R8', 'R9', 'R10', 'R11', 'R12']:
                priority = PRIORITY_DISPLAY[todo['priority']]['icon'] + " " + todo['priority']
                deps = ", ".join(todo.get('dependencies', [])) or "-"
                md.append(f"| {todo['id']} | {todo['title']} | {priority} | {deps} |")
        md.append("")

        md.append("### Langfristig (Phase 50+)\n")
        md.append("| ID | Titel | Priorität | Dependencies |")
        md.append("|----|-------|-----------|--------------|")

        for todo in by_status['FUTURE']:
            if todo['id'] not in ['R7', 'R8', 'R9', 'R10', 'R11', 'R12']:
                priority = PRIORITY_DISPLAY[todo['priority']]['icon'] + " " + todo['priority']
                deps = ", ".join(todo.get('dependencies', [])) or "-"
                md.append(f"| {todo['id']} | {todo['title']} | {priority} | {deps} |")
        md.append("")

        md.append("</div>\n")
        md.append("---\n")

    # Stream-Übersicht
    md.append("## Stream-Übersicht\n")
    for stream_id, stream_info in streams.items():
        color = STREAM_COLORS.get(stream_id, "⚪ White")
        md.append(f"### {stream_info['name']} ({color})")
        md.append(_get_stream_description(stream_id) + "\n")

        # Zähle Tasks pro Status für diesen Stream
        stream_tasks = [t for t in todos if t['stream'] == stream_id]
        active = [t['id'] for t in stream_tasks if t['status'] == 'NEXT']
        in_progress = [t['id'] for t in stream_tasks if t['status'] == 'IN_PROGRESS']
        done = [t['id'] for t in stream_tasks if t['status'] == 'DONE']
        future = [t['id'] for t in stream_tasks if t['status'] == 'FUTURE']

        if in_progress:
            md.append(f"**In Arbeit:** {', '.join(in_progress)}")
        if active:
            md.append(f"**Aktive:** {', '.join(active)}")
        if done:
            md.append(f"**Abgeschlossen:** {', '.join(done)}")
        if future:
            md.append(f"**Zukünftig:** {', '.join(future)}")
        md.append("")

    md.append("---\n")

    # Dependency-Graph
    md.append("## Dependency-Graph (Wichtigste Abhängigkeiten)\n")
    md.append("```")
    deps_shown = set()
    for todo in todos:
        if todo.get('dependencies'):
            for dep in todo['dependencies']:
                dep_line = f"{dep} → {todo['id']} ({todo['title']})"
                if dep_line not in deps_shown:
                    md.append(dep_line)
                    deps_shown.add(dep_line)
    md.append("```\n")
    md.append("---\n")

    # Board-Regeln
    md.append("## Regeln für Board-Updates\n")
    md.append("1. **Status-Änderungen:** Nur über `config/todo_board.yaml` → dann `generate_todo_board.py` ausführen")
    md.append("2. **Neue Tasks:** In YAML hinzufügen mit eindeutiger ID (R/L/I/G + Nummer)")
    md.append("3. **Last Updated:** Datum bei Statusänderungen aktualisieren")
    md.append("4. **Dependencies:** In YAML pflegen, werden automatisch in Graph übertragen")
    md.append("5. **Grey-Track:** Tasks mit Status `FUTURE` werden visuell abgesetzt dargestellt\n")
    md.append("---\n")

    md.append(f"**Generiert von:** `scripts/generate_todo_board.py`")
    md.append(f"**Letzte Aktualisierung:** {datetime.now().strftime('%Y-%m-%d')}")

    # Schreibe Markdown-Datei
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f"✅ Markdown-Board generiert: {output_path}")


def generate_html(config: Dict[str, Any], output_path: Path) -> None:
    """Generiert HTML-Board mit interaktiven Features."""

    todos = config.get('todos', [])
    streams = {s['id']: s for s in config.get('streams', [])}

    # Gruppiere Tasks nach Status
    by_status = defaultdict(list)
    for todo in todos:
        by_status[todo['status']].append(todo)

    html = ['<!DOCTYPE html>', '<html lang="de">', '<head>']
    html.append('<meta charset="UTF-8">')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html.append('<title>Peak Trade TODO-Board</title>')
    html.append('<style>')
    html.append("""
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }
        h3 {
            color: #7f8c8d;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .priority-high { color: #e74c3c; font-weight: bold; }
        .priority-medium { color: #f39c12; }
        .priority-low { color: #27ae60; }
        .grey-track {
            opacity: 0.6;
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .task-card {
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .task-card h4 { margin: 0 0 10px 0; color: #2c3e50; }
        .task-meta { font-size: 0.9em; color: #7f8c8d; }
        .tags { margin-top: 8px; }
        .tag {
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-right: 5px;
        }
        .legend {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .dep-graph {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }
    """)
    html.append('</style>')
    html.append('</head><body><div class="container">')

    # Header
    html.append(f'<h1>🎯 Peak Trade TODO-Board</h1>')
    html.append(f'<p><strong>Stand:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>')
    html.append(f'<p><strong>Quelle:</strong> <code>config/todo_board.yaml</code></p>')

    # Status-Legende
    html.append('<div class="legend">')
    html.append('<h2>📊 Status-Legende</h2>')
    html.append('<table><thead><tr><th>Status</th><th>Bedeutung</th><th>Icon</th></tr></thead><tbody>')
    for status, display in STATUS_DISPLAY.items():
        html.append(f"<tr><td>{display['emoji']} {display['text']}</td>")
        html.append(f"<td>{_get_status_description(status)}</td>")
        html.append(f"<td>{display['emoji']} {status}</td></tr>")
    html.append('</tbody></table></div>')

    # Prioritäts-Legende
    html.append('<div class="legend">')
    html.append('<h2>⚡ Prioritäts-Legende</h2>')
    html.append('<table><thead><tr><th>Priorität</th><th>Beschreibung</th></tr></thead><tbody>')
    html.append('<tr><td class="priority-high">🔴 HIGH</td><td>Kritisch, hohe Priorität</td></tr>')
    html.append('<tr><td class="priority-medium">🟡 MEDIUM</td><td>Mittlere Priorität</td></tr>')
    html.append('<tr><td class="priority-low">🟢 LOW</td><td>Niedrige Priorität, Nice-to-have</td></tr>')
    html.append('</tbody></table></div>')

    # Aktive Tasks
    html.append('<h2>🔥 Aktive Tasks</h2>')

    if by_status.get('IN_PROGRESS'):
        html.append('<h3>🟡 In Arbeit</h3>')
        for todo in by_status['IN_PROGRESS']:
            html.append(_render_task_card(todo, streams))

    if by_status.get('NEXT'):
        html.append('<h3>⏭️ Als Nächstes</h3>')
        for todo in by_status['NEXT']:
            html.append(_render_task_card(todo, streams))

    # Abgeschlossene Tasks
    if by_status.get('DONE'):
        html.append('<h2>✅ Abgeschlossene Tasks</h2>')
        html.append('<table><thead><tr><th>ID</th><th>Titel</th><th>Stream</th><th>Letzte Änderung</th></tr></thead><tbody>')
        for todo in by_status['DONE']:
            stream_name = streams.get(todo['stream'], {}).get('name', todo['stream'])
            html.append(f"<tr><td><strong>{todo['id']}</strong></td>")
            html.append(f"<td>{todo['title']}</td>")
            html.append(f"<td>{stream_name}</td>")
            html.append(f"<td>{todo['last_updated']}</td></tr>")
        html.append('</tbody></table>')

    # Grey-Track
    if by_status.get('FUTURE'):
        html.append('<h2>🩶 Zukünftige Tasks (Grey-Track)</h2>')
        html.append('<div class="grey-track">')
        html.append('<table><thead><tr><th>ID</th><th>Titel</th><th>Priorität</th><th>Stream</th><th>Dependencies</th></tr></thead><tbody>')
        for todo in by_status['FUTURE']:
            stream_name = streams.get(todo['stream'], {}).get('name', todo['stream'])
            priority_class = f"priority-{todo['priority'].lower()}"
            priority = PRIORITY_DISPLAY[todo['priority']]['icon'] + " " + todo['priority']
            deps = ", ".join(todo.get('dependencies', [])) or "-"
            html.append(f"<tr><td><strong>{todo['id']}</strong></td>")
            html.append(f"<td>{todo['title']}</td>")
            html.append(f"<td class='{priority_class}'>{priority}</td>")
            html.append(f"<td>{stream_name}</td>")
            html.append(f"<td>{deps}</td></tr>")
        html.append('</tbody></table></div>')

    # Dependency-Graph
    html.append('<h2>🔗 Dependency-Graph</h2>')
    html.append('<div class="dep-graph"><pre>')
    for todo in todos:
        if todo.get('dependencies'):
            for dep in todo['dependencies']:
                html.append(f"{dep} → {todo['id']} ({todo['title']})")
    html.append('</pre></div>')

    # Footer
    html.append('<hr>')
    html.append(f"<p><em>Generiert von: <code>scripts/generate_todo_board.py</code></em></p>")
    html.append(f"<p><em>Letzte Aktualisierung: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</em></p>")

    html.append('</div></body></html>')

    # Schreibe HTML-Datei
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))

    print(f"✅ HTML-Board generiert: {output_path}")


def _render_task_card(todo: Dict[str, Any], streams: Dict[str, Any]) -> str:
    """Rendert eine Task-Card für HTML."""
    stream_name = streams.get(todo['stream'], {}).get('name', todo['stream'])
    priority = PRIORITY_DISPLAY[todo['priority']]['icon'] + " " + todo['priority']
    status = STATUS_DISPLAY[todo['status']]['emoji'] + " " + STATUS_DISPLAY[todo['status']]['text']

    card = '<div class="task-card">'
    card += f"<h4>{todo['id']}: {todo['title']}</h4>"
    card += f"<p>{todo['description']}</p>"
    card += f'<div class="task-meta">'
    card += f"<strong>Status:</strong> {status} | "
    card += f"<strong>Priorität:</strong> {priority} | "
    card += f"<strong>Stream:</strong> {stream_name}"
    card += '</div>'

    if todo.get('tags'):
        card += '<div class="tags">'
        for tag in todo['tags']:
            card += f'<span class="tag">{tag}</span>'
        card += '</div>'

    if todo.get('notes'):
        card += f"<p><em><strong>Hinweise:</strong> {todo['notes']}</em></p>"

    card += '</div>'
    return card


def _get_status_description(status: str) -> str:
    """Gibt deutsche Beschreibung für Status zurück."""
    descriptions = {
        "DONE": "Abgeschlossen",
        "IN_PROGRESS": "Aktiv in Bearbeitung",
        "NEXT": "Geplant für nächste Iteration",
        "BLOCKED": "Wartet auf Dependencies/Entscheidungen",
        "TECH_DEBT": "Technische Schulden, Refactoring",
        "FUTURE": "Noch nicht gestartet, langfristige Planung",
    }
    return descriptions.get(status, status)


def _get_stream_description(stream_id: str) -> str:
    """Gibt deutsche Beschreibung für Stream zurück."""
    descriptions = {
        "research": "Strategieentwicklung, Parameter-Sweeps, Metriken, Analysen",
        "live": "Paper-Trading, Risk-Management, Live-Execution",
        "infra": "Tooling, CI/CD, Deployment",
        "governance": "Policies, Compliance, Safety-Checks",
    }
    return descriptions.get(stream_id, "")


def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(description='Peak Trade TODO-Board Generator')
    parser.add_argument(
        '--format',
        choices=['markdown', 'html', 'both'],
        default='both',
        help='Ausgabeformat (default: both)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path(__file__).parent.parent / 'config' / 'todo_board.yaml',
        help='Pfad zur YAML-Konfiguration'
    )

    args = parser.parse_args()

    # Lade Konfiguration
    if not args.config.exists():
        print(f"❌ Konfigurationsdatei nicht gefunden: {args.config}")
        return 1

    config = load_config(args.config)

    # Output-Pfade
    base_dir = Path(__file__).parent.parent / 'docs' / 'ops' / 'todo'
    md_output = base_dir / 'PEAK_TRADE_TODO_BOARD.md'
    html_output = base_dir / 'todo_board.html'

    # Generiere Boards
    if args.format in ['markdown', 'both']:
        generate_markdown(config, md_output)

    if args.format in ['html', 'both']:
        generate_html(config, html_output)

    print("\n✨ TODO-Board erfolgreich generiert!")
    return 0


if __name__ == '__main__':
    exit(main())
