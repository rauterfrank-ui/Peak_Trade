#!/usr/bin/env python3
"""
Runner Index Curator (Tier A) - Evidence Chain Readiness + P1 Shortlist

Sammelt automatisch Info über Tier-A Runner:
- --help output (usage, description, args)
- Static scan (run_id, results/, ResultsWriter, mlflow tokens)
- Evidence Chain Readiness (READY/PARTIAL/TODO)
- P1 Priority (basierend auf Docs/CI Referenzen)

Output: results/dev/runner_index_curation.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def extract_tier_a_scripts(index_path: Path) -> List[str]:
    """Extrahiere alle Tier-A Runner aus RUNNER_INDEX.md"""
    if not index_path.exists():
        return []

    content = index_path.read_text()

    # Find Tier A section (actual table section, not definition)
    tier_a_match = re.search(
        r"## Tier A \(Canonical Runner Set\).*?(?=## Tier B|$)", content, re.DOTALL
    )
    if not tier_a_match:
        return []

    tier_a_section = tier_a_match.group(0)

    # Extract all scripts/*.py paths (handle backticks)
    scripts = re.findall(r"scripts/[a-zA-Z0-9_/]+\.py", tier_a_section)
    # Also try without word boundaries for backtick cases
    if not scripts:
        # Remove backticks and try again
        clean_section = tier_a_section.replace("`", "")
        scripts = re.findall(r"scripts/[a-zA-Z0-9_/]+\.py", clean_section)

    # Exclude dev tools (self-referential)
    scripts = [s for s in scripts if not s.startswith("scripts/dev/")]

    return sorted(set(scripts))


def try_help(script_path: Path) -> Optional[str]:
    """Versuche --help auszuführen"""
    try:
        result = subprocess.run(
            ["python3", str(script_path), "--help"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, Exception):
        return None


def extract_docstring(script_path: Path) -> Optional[str]:
    """Extrahiere Modul-Docstring oder ArgumentParser description"""
    if not script_path.exists():
        return None

    try:
        content = script_path.read_text()

        # Try module docstring first
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()

        # Try ArgumentParser description
        parser_match = re.search(
            r'ArgumentParser\(.*?description=["\']([^"\']+)["\']', content, re.DOTALL
        )
        if parser_match:
            return parser_match.group(1).strip()

        return None
    except Exception:
        return None


def static_scan_tokens(script_path: Path) -> Dict[str, bool]:
    """Scanne nach Evidence-Chain relevanten Tokens"""
    if not script_path.exists():
        return {}

    try:
        content = script_path.read_text()

        return {
            "has_results_path": bool(re.search(r"results[/\\]", content)),
            "has_run_id": bool(re.search(r"\brun_id\b", content)),
            "has_results_writer": bool(re.search(r"ResultsWriter", content)),
            "has_mlflow": bool(re.search(r"\bmlflow\b", content)),
            "has_quarto": bool(re.search(r"\bquarto\b", content)),
            "has_config_snapshot": bool(re.search(r"config_snapshot", content)),
            "has_stats_json": bool(re.search(r"stats\.json", content)),
            "has_equity_csv": bool(re.search(r"equity\.csv", content)),
        }
    except Exception:
        return {}


def determine_readiness(tokens: Dict[str, bool]) -> str:
    """Bestimme Evidence Chain Readiness"""
    # READY: run_id + results path
    if tokens.get("has_run_id") and tokens.get("has_results_path"):
        return "READY"

    # PARTIAL: mindestens eines der Signale
    if any(
        [
            tokens.get("has_results_path"),
            tokens.get("has_run_id"),
            tokens.get("has_results_writer"),
            tokens.get("has_mlflow"),
        ]
    ):
        return "PARTIAL"

    return "TODO"


def determine_required_artifacts(tokens: Dict[str, bool]) -> List[str]:
    """Bestimme required artifacts basierend auf Tokens"""
    artifacts = []

    if tokens.get("has_config_snapshot"):
        artifacts.append("config_snapshot.*")
    if tokens.get("has_stats_json"):
        artifacts.append("stats.json")
    if tokens.get("has_equity_csv"):
        artifacts.append("equity.csv")

    # Defaults wenn unklar
    if not artifacts and tokens.get("has_run_id"):
        artifacts = ["config_snapshot.*", "stats.json", "equity.csv"]

    return artifacts


def extract_purpose_from_help(help_text: Optional[str], docstring: Optional[str]) -> str:
    """Extrahiere Zweck (1 Satz, max 120 chars)"""
    # Versuche aus --help
    if help_text:
        # Erste Zeile nach usage
        lines = [l.strip() for l in help_text.split("\n") if l.strip()]
        for line in lines:
            if (
                not line.startswith("usage:")
                and not line.startswith("positional")
                and len(line) > 20
            ):
                purpose = line[:120]
                if not purpose.endswith("."):
                    purpose += "..."
                return purpose

    # Fallback: docstring
    if docstring:
        first_line = docstring.split("\n")[0].strip()
        purpose = first_line[:120]
        if not purpose.endswith("."):
            purpose += "..."
        return purpose

    return "unknown"


def extract_example_command(script_path: str, help_text: Optional[str]) -> str:
    """Extrahiere Beispiel-Command"""
    if help_text:
        # Check ob required args existieren
        if "required" not in help_text.lower() or "--help" in help_text:
            # Einfach --help zeigen
            return f"python {script_path} --help"
        else:
            # Zeige usage line wenn möglich
            usage_match = re.search(r"usage:\s+(.+)", help_text)
            if usage_match:
                return usage_match.group(1).strip()

    return f"python {script_path} --help"


def count_doc_references(script_name: str, repo_root: Path) -> int:
    """Zähle Referenzen in Docs/CI/README"""
    count = 0

    # Search in docs/
    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        for md_file in docs_dir.rglob("*.md"):
            try:
                if script_name in md_file.read_text():
                    count += 1
            except Exception:
                pass

    # Search in .github/
    github_dir = repo_root / ".github"
    if github_dir.exists():
        for yml_file in github_dir.rglob("*.yml"):
            try:
                if script_name in yml_file.read_text():
                    count += 2  # CI refs gewichtet doppelt
            except Exception:
                pass
        for yaml_file in github_dir.rglob("*.yaml"):
            try:
                if script_name in yaml_file.read_text():
                    count += 2
            except Exception:
                pass

    # Search in README
    readme = repo_root / "README.md"
    if readme.exists():
        try:
            if script_name in readme.read_text():
                count += 3  # README refs gewichtet dreifach
        except Exception:
            pass

    return count


def analyze_runner(script_path: str, repo_root: Path) -> Dict:
    """Analysiere einen Runner komplett"""
    full_path = repo_root / script_path
    script_name = Path(script_path).name

    # Sammle Infos
    help_text = try_help(full_path)
    docstring = extract_docstring(full_path)
    tokens = static_scan_tokens(full_path)
    readiness = determine_readiness(tokens)
    artifacts = determine_required_artifacts(tokens)
    purpose = extract_purpose_from_help(help_text, docstring)
    example_cmd = extract_example_command(script_path, help_text)
    doc_refs = count_doc_references(script_name, repo_root)

    return {
        "script_path": script_path,
        "script_name": script_name,
        "purpose": purpose,
        "example_command": example_cmd,
        "readiness": readiness,
        "required_artifacts": artifacts,
        "tokens": tokens,
        "doc_references": doc_refs,
        "has_help": help_text is not None,
        "help_available": bool(help_text),
        "docstring_available": bool(docstring),
    }


def determine_p1_priority(runners: List[Dict]) -> List[Dict]:
    """Bestimme P1 Priorities (Top 3-5)"""
    # Sortiere nach doc_references (höchste zuerst)
    sorted_runners = sorted(runners, key=lambda r: r["doc_references"], reverse=True)

    # Top 3-5 basierend auf Referenzen + Readiness
    for i, runner in enumerate(sorted_runners):
        if i < 3:
            runner["priority"] = "MUST"
        elif i < 5 and runner["readiness"] in ["READY", "PARTIAL"]:
            runner["priority"] = "SHOULD"
        else:
            runner["priority"] = "LATER"

    return sorted_runners


def main():
    parser = argparse.ArgumentParser(description="Curate Runner Index (Tier A)")
    parser.add_argument(
        "--index", default="docs/dev/RUNNER_INDEX.md", help="Path to RUNNER_INDEX.md"
    )
    parser.add_argument(
        "--output", default="results/dev/runner_index_curation.json", help="Output JSON path"
    )
    args = parser.parse_args()

    # Repo root
    repo_root = Path(__file__).parent.parent.parent
    index_path = repo_root / args.index
    output_path = repo_root / args.output

    print(f"Curating Runner Index from: {index_path}")
    print(f"Output will be written to: {output_path}")

    # Extract Tier A scripts
    tier_a_scripts = extract_tier_a_scripts(index_path)
    if not tier_a_scripts:
        print("ERROR: No Tier A scripts found in RUNNER_INDEX.md")
        sys.exit(1)

    print(f"\nFound {len(tier_a_scripts)} Tier A runners:")
    for script in tier_a_scripts:
        print(f"  - {script}")

    # Analyze each runner
    print("\nAnalyzing runners...")
    runners = []
    for script_path in tier_a_scripts:
        print(f"  Analyzing {script_path}...")
        analysis = analyze_runner(script_path, repo_root)
        runners.append(analysis)

    # Determine P1 priorities
    runners = determine_p1_priority(runners)

    # Prepare output
    output_data = {
        "tier_a_count": len(runners),
        "runners": runners,
        "summary": {
            "ready": sum(1 for r in runners if r["readiness"] == "READY"),
            "partial": sum(1 for r in runners if r["readiness"] == "PARTIAL"),
            "todo": sum(1 for r in runners if r["readiness"] == "TODO"),
            "p1_must": [r["script_name"] for r in runners if r["priority"] == "MUST"],
            "p1_should": [r["script_name"] for r in runners if r["priority"] == "SHOULD"],
        },
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, indent=2))

    print(f"\nCuration complete!")
    print(f"  READY: {output_data['summary']['ready']}")
    print(f"  PARTIAL: {output_data['summary']['partial']}")
    print(f"  TODO: {output_data['summary']['todo']}")
    print(f"\nP1 MUST integrate first:")
    for script in output_data["summary"]["p1_must"]:
        print(f"  - {script}")
    print(f"\nP1 SHOULD integrate next:")
    for script in output_data["summary"]["p1_should"]:
        print(f"  - {script}")
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
