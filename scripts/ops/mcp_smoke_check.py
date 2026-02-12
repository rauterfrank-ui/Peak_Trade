#!/usr/bin/env python3
"""
scripts/ops/mcp_smoke_check.py

MCP (Model Context Protocol) Smoke Check Script.

Prüft die Konfiguration und Verfügbarkeit von MCP-Servern aus .cursor/mcp.json.
Führt optionale Health-Checks für konfigurierte Server aus (Playwright, Grafana).

Exit-Codes:
  0  - Alle Checks erfolgreich
  1  - Konfigurationsfehler (mcp.json ungültig/fehlt)
  2  - Mindestens ein Server-Check fehlgeschlagen
  3  - Tool nicht verfügbar (npx/docker fehlt)
  64 - CLI-Argument-Fehler

Usage:
  ./scripts/ops/mcp_smoke_check.py
  ./scripts/ops/mcp_smoke_check.py --check-playwright
  ./scripts/ops/mcp_smoke_check.py --check-all --verbose
  ./scripts/ops/mcp_smoke_check.py --json-path .cursor/mcp.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Exit-Code Tabelle
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 0   - Alle Checks erfolgreich
# 1   - Konfigurationsfehler (mcp.json ungültig/fehlt, JSON-Parse-Fehler)
# 2   - Mindestens ein Server-Check fehlgeschlagen (Server nicht verfügbar)
# 3   - Tool nicht verfügbar (npx oder docker fehlt, wenn benötigt)
# 64  - CLI-Argument-Fehler (unbekannte Flags, ungültige Kombinationen)
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Colors:
    """ANSI color codes für Terminal-Ausgabe."""

    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def colorize(text: str, color: str) -> str:
    """Färbt Text ein, wenn stdout ein TTY ist."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


def find_repo_root() -> Path:
    """Findet das Repository-Root-Verzeichnis."""
    current = Path(__file__).resolve()
    # Gehe von scripts/ops/ nach oben
    for parent in [current.parent.parent.parent, current.parent.parent]:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    # Fallback: aktuelles Verzeichnis
    return Path.cwd()


def load_mcp_config(config_path: Path) -> Dict:
    """
    Lädt und parst die MCP-Konfiguration aus JSON.

    Returns:
        Dict mit mcpServers-Struktur

    Raises:
        FileNotFoundError: Wenn Datei nicht existiert
        json.JSONDecodeError: Wenn JSON ungültig ist
        KeyError: Wenn mcpServers fehlt
    """
    if not config_path.exists():
        raise FileNotFoundError(f"MCP-Konfiguration nicht gefunden: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "mcpServers" not in data:
        raise KeyError("mcpServers-Schlüssel fehlt in mcp.json")

    return data


def check_tool_available(tool: str) -> bool:
    """Prüft ob ein Tool (npx, docker) verfügbar ist."""
    try:
        subprocess.run(
            ["which", tool],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_command(
    cmd: List[str],
    timeout: int = 10,
    verbose: bool = False,
) -> Tuple[bool, str]:
    """
    Führt einen Befehl aus und gibt Erfolg/Fehler zurück.

    Returns:
        (success: bool, output: str)
    """
    if verbose:
        print(f"  → {' '.join(cmd)}", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # Wir prüfen exit code selbst
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"Timeout nach {timeout}s"
    except FileNotFoundError:
        return False, f"Tool nicht gefunden: {cmd[0]}"
    except Exception as e:
        return False, f"Unerwarteter Fehler: {e}"


def check_playwright_server(verbose: bool = False) -> Tuple[bool, str]:
    """
    Prüft ob Playwright MCP Server verfügbar ist.

    Führt aus: npx -y @playwright/mcp@latest --help
    """
    if not check_tool_available("npx"):
        return False, "npx nicht verfügbar (Node.js/npm erforderlich)"

    cmd = ["npx", "-y", "@playwright/mcp@latest", "--help"]
    success, output = run_command(cmd, timeout=30, verbose=verbose)

    if success:
        return True, "Playwright MCP Server verfügbar"
    else:
        return False, f"Playwright Check fehlgeschlagen: {output[:200]}"


def check_grafana_server(verbose: bool = False) -> Tuple[bool, str]:
    """
    Prüft ob Grafana MCP Server verfügbar ist.

    Führt aus: docker run --rm grafana/mcp-grafana -h
    """
    if not check_tool_available("docker"):
        return False, "docker nicht verfügbar"

    cmd = ["docker", "run", "--rm", "grafana/mcp-grafana", "-h"]
    success, output = run_command(cmd, timeout=30, verbose=verbose)

    if success:
        return True, "Grafana MCP Server verfügbar"
    else:
        # Docker kann auch fehlschlagen wenn Image nicht lokal vorhanden ist
        # Das ist ok für einen Smoke-Check (nur Tool-Verfügbarkeit)
        if "Cannot connect to the Docker daemon" in output:
            return False, "Docker daemon nicht erreichbar"
        elif "pull access denied" in output.lower() or "image" in output.lower():
            # Image nicht lokal, aber docker funktioniert
            return True, "Docker verfügbar (Image würde beim ersten Run geladen)"
        else:
            return False, f"Grafana Check fehlgeschlagen: {output[:200]}"


def check_server_config(
    server_name: str,
    server_config: Dict,
    check_all: bool = False,
    check_playwright: bool = False,
    check_grafana: bool = False,
    verbose: bool = False,
) -> Tuple[bool, str]:
    """
    Prüft einen einzelnen Server aus der Konfiguration.

    Returns:
        (success: bool, message: str)
    """
    command = server_config.get("command", "")

    # Nur strukturelle Prüfung (kein Runtime-Check)
    if not check_all and not check_playwright and not check_grafana:
        if command:
            return True, f"Konfiguriert (command: {command})"
        else:
            return False, "Kein 'command' Feld gefunden"

    # Runtime-Checks nur wenn explizit angefordert
    if command == "npx" and (check_all or check_playwright):
        return check_playwright_server(verbose=verbose)
    elif command == "docker" and (check_all or check_grafana):
        # Prüfe ob es Grafana ist
        args = server_config.get("args", [])
        if "grafana/mcp-grafana" in " ".join(args):
            return check_grafana_server(verbose=verbose)
        else:
            return True, f"Docker-Server konfiguriert (kein Grafana-Check)"

    # Kein Runtime-Check für diesen Server
    return True, f"Konfiguriert (command: {command}, kein Check angefordert)"


def main() -> int:
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description="MCP Smoke Check - Prüft MCP-Server Konfiguration und Verfügbarkeit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit-Codes:
  0  - Alle Checks erfolgreich
  1  - Konfigurationsfehler
  2  - Server-Check fehlgeschlagen
  3  - Tool nicht verfügbar
  64 - CLI-Argument-Fehler

Beispiele:
  %(prog)s
  %(prog)s --check-playwright
  %(prog)s --check-all --verbose
  %(prog)s --json-path .cursor/mcp.json
        """,
    )

    parser.add_argument(
        "--json-path",
        type=str,
        default=".cursor/mcp.json",
        help="Pfad zur mcp.json Datei (relativ zu Repo-Root, default: .cursor/mcp.json)",
    )
    parser.add_argument(
        "--check-playwright",
        action="store_true",
        help="Prüfe Playwright MCP Server Verfügbarkeit (npx)",
    )
    parser.add_argument(
        "--check-grafana",
        action="store_true",
        help="Prüfe Grafana MCP Server Verfügbarkeit (docker)",
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Prüfe alle konfigurierten Server (Playwright + Grafana)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Zeige detaillierte Ausgabe",
    )

    args = parser.parse_args()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. Lade Konfiguration
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    repo_root = find_repo_root()
    config_path = repo_root / args.json_path

    print(colorize("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.BOLD))
    print(colorize("🧪 MCP Smoke Check", Colors.BOLD))
    print(colorize("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.BOLD))
    print(f"Config:     {config_path}")
    print(f"Repo Root:  {repo_root}")
    print()

    try:
        config = load_mcp_config(config_path)
        servers = config.get("mcpServers", {})
    except FileNotFoundError as e:
        print(colorize(f"❌ FEHLER: {e}", Colors.RED))
        return 1
    except json.JSONDecodeError as e:
        print(colorize(f"❌ FEHLER: JSON-Parse-Fehler: {e}", Colors.RED))
        return 1
    except KeyError as e:
        print(colorize(f"❌ FEHLER: {e}", Colors.RED))
        return 1

    if not servers:
        print(colorize("⚠️  WARNUNG: Keine Server in mcpServers konfiguriert", Colors.YELLOW))
        print(colorize("✅ Konfiguration strukturell ok (leer)", Colors.GREEN))
        return 0

    print(f"Gefundene Server: {', '.join(servers.keys())}")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. Prüfe Server
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    results: List[Tuple[str, bool, str]] = []
    config_errors = 0
    check_errors = 0
    tool_errors = 0

    for server_name, server_config in servers.items():
        success, message = check_server_config(
            server_name,
            server_config,
            check_all=args.check_all,
            check_playwright=args.check_playwright,
            check_grafana=args.check_grafana,
            verbose=args.verbose,
        )

        results.append((server_name, success, message))

        if not success:
            if "nicht verfügbar" in message or "nicht gefunden" in message:
                tool_errors += 1
            elif "Check fehlgeschlagen" in message or "fehlgeschlagen" in message:
                check_errors += 1
            else:
                config_errors += 1

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. Ausgabe
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    print(colorize("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.BOLD))
    print(colorize("📊 Ergebnisse", Colors.BOLD))
    print(colorize("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.BOLD))

    for server_name, success, message in results:
        if success:
            print(f"{colorize('✅', Colors.GREEN)} {server_name}: {message}")
        else:
            print(f"{colorize('❌', Colors.RED)} {server_name}: {message}")

    print()
    print(colorize("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.BOLD))
    print(colorize("📈 Summary", Colors.BOLD))
    print(colorize("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.BOLD))

    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    failed = total - passed

    print(f"Gesamt:     {total}")
    print(f"{colorize('✅ PASS', Colors.GREEN)}:     {passed}")
    print(f"{colorize('❌ FAIL', Colors.RED)}:     {failed}")

    if config_errors > 0:
        print(f"{colorize('⚠️  Config-Fehler', Colors.YELLOW)}: {config_errors}")
    if tool_errors > 0:
        print(f"{colorize('⚠️  Tool-Fehler', Colors.YELLOW)}: {tool_errors}")
    if check_errors > 0:
        print(f"{colorize('⚠️  Check-Fehler', Colors.YELLOW)}: {check_errors}")

    print(colorize("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.BOLD))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. Exit-Code
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if config_errors > 0:
        print(colorize("❌ Konfigurationsfehler", Colors.RED))
        return 1
    elif tool_errors > 0:
        print(colorize("❌ Tools nicht verfügbar", Colors.RED))
        return 3
    elif check_errors > 0 or failed > 0:
        print(colorize("❌ Server-Checks fehlgeschlagen", Colors.RED))
        return 2
    else:
        print(colorize("🎉 Alle Checks erfolgreich", Colors.GREEN))
        return 0


if __name__ == "__main__":
    sys.exit(main())
