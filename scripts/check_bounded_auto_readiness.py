#!/usr/bin/env python3
"""
bounded_auto Readiness Checker

Dieses Tool prüft automatisch die Go/No-Go-Kriterien für bounded_auto
und gibt eine klare Text-Zusammenfassung aus.

Exit-Codes:
  0 - READY (GO): Alle kritischen Checks erfolgreich
  1 - NOT READY (NO-GO): Mindestens ein kritischer Check fehlgeschlagen

Usage:
  python scripts/check_bounded_auto_readiness.py
  python scripts/check_bounded_auto_readiness.py --verbose
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class CheckResult:
    """Result of a single readiness check."""

    name: str
    status: str  # "OK", "WARN", "ERR"
    message: str
    details: Optional[List[str]] = None


class ReadinessChecker:
    """
    Checker for bounded_auto readiness criteria.
    
    Performs automated checks based on the Go/No-Go checklist from
    docs/learning_promotion/BOUNDED_AUTO_SAFETY_PLAYBOOK.md
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[CheckResult] = []
        self.config_path = PROJECT_ROOT / "config" / "promotion_loop_config.toml"

    def run_all_checks(self) -> bool:
        """
        Run all readiness checks.
        
        Returns:
            True if all checks pass (READY), False otherwise (NOT READY)
        """
        print("[bounded_auto readiness]\n")

        # Run checks
        self._check_config_loadable()
        self._check_p0_blacklist_config()
        self._check_p0_bounds_config()
        self._check_p0_guardrails_config()
        self._check_p1_promotion_lock_config()
        self._check_p1_audit_log_config()

        # Print results
        self._print_results()

        # Determine overall status
        has_errors = any(r.status == "ERR" for r in self.results)
        return not has_errors

    def _check_config_loadable(self) -> None:
        """Check if promotion_loop_config.toml can be loaded."""
        try:
            import toml

            if not self.config_path.exists():
                self.results.append(
                    CheckResult(
                        name="Config-Datei existiert",
                        status="ERR",
                        message=f"Config-Datei nicht gefunden: {self.config_path}",
                    )
                )
                return

            data = toml.load(self.config_path)

            if "promotion_loop" not in data:
                self.results.append(
                    CheckResult(
                        name="Config-Struktur",
                        status="ERR",
                        message="Sektion [promotion_loop] nicht gefunden in Config",
                    )
                )
                return

            self.config_data = data
            self.results.append(
                CheckResult(
                    name="Config-Datei laden",
                    status="OK",
                    message=f"Config erfolgreich geladen: {self.config_path}",
                )
            )

        except Exception as e:
            self.results.append(
                CheckResult(
                    name="Config-Datei laden",
                    status="ERR",
                    message=f"Fehler beim Laden der Config: {e}",
                )
            )

    def _check_p0_blacklist_config(self) -> None:
        """Check P0: Promotion blacklist configuration."""
        if not hasattr(self, "config_data"):
            return  # Skip if config not loaded

        safety_section = self.config_data.get("promotion_loop", {}).get("safety", {})

        blacklist_targets = safety_section.get("auto_apply_blacklist", [])
        blacklist_tags = safety_section.get("blacklist_tags", [])

        details = []
        if blacklist_targets:
            details.append(f"  • Blacklisted targets: {len(blacklist_targets)}")
            if self.verbose:
                for target in blacklist_targets[:5]:
                    details.append(f"    - {target}")
                if len(blacklist_targets) > 5:
                    details.append(f"    ... und {len(blacklist_targets) - 5} weitere")

        if blacklist_tags:
            details.append(f"  • Blacklisted tags: {len(blacklist_tags)}")
            if self.verbose:
                for tag in blacklist_tags:
                    details.append(f"    - {tag}")

        if not blacklist_targets and not blacklist_tags:
            self.results.append(
                CheckResult(
                    name="P0: Promotion-Blacklist",
                    status="WARN",
                    message="Keine Blacklist konfiguriert (weder Targets noch Tags)",
                    details=["  ⚠️  Empfehlung: Mindestens kritische Targets blacklisten"],
                )
            )
        else:
            self.results.append(
                CheckResult(
                    name="P0: Promotion-Blacklist",
                    status="OK",
                    message="Blacklist-Konfiguration vorhanden",
                    details=details if details else None,
                )
            )

    def _check_p0_bounds_config(self) -> None:
        """Check P0: Bounds configuration."""
        if not hasattr(self, "config_data"):
            return

        bounds_section = self.config_data.get("promotion_loop", {}).get("bounds", {})

        # Check for expected bounds parameters
        expected_bounds = [
            ("leverage_min", "leverage_max", "leverage_max_step"),
            ("trigger_delay_min", "trigger_delay_max", "trigger_delay_max_step"),
            ("macro_weight_min", "macro_weight_max", "macro_weight_max_step"),
        ]

        found_bounds = []
        missing_bounds = []

        for min_key, max_key, step_key in expected_bounds:
            if all(k in bounds_section for k in [min_key, max_key, step_key]):
                param_name = min_key.replace("_min", "").replace("_", " ").title()
                found_bounds.append(
                    f"  • {param_name}: [{bounds_section[min_key]}, {bounds_section[max_key]}], step≤{bounds_section[step_key]}"
                )
            else:
                param_name = min_key.replace("_min", "").replace("_", " ").title()
                missing_bounds.append(param_name)

        if not found_bounds:
            self.results.append(
                CheckResult(
                    name="P0: Bounds-Konfiguration",
                    status="ERR",
                    message="Keine Bounds konfiguriert",
                    details=["  ❌ Bounds für Leverage, Trigger-Delay und Macro-Weight fehlen"],
                )
            )
        elif missing_bounds:
            self.results.append(
                CheckResult(
                    name="P0: Bounds-Konfiguration",
                    status="WARN",
                    message="Bounds teilweise konfiguriert",
                    details=(
                        found_bounds
                        + [f"  ⚠️  Fehlend: {', '.join(missing_bounds)}"]
                    ),
                )
            )
        else:
            self.results.append(
                CheckResult(
                    name="P0: Bounds-Konfiguration",
                    status="OK",
                    message="Alle Bounds konfiguriert",
                    details=found_bounds if self.verbose else None,
                )
            )

    def _check_p0_guardrails_config(self) -> None:
        """Check P0: bounded_auto guardrails configuration."""
        if not hasattr(self, "config_data"):
            return

        promo_section = self.config_data.get("promotion_loop", {})
        safety_section = promo_section.get("safety", {})

        details = []

        # Check mode is configured
        mode = promo_section.get("mode")
        if mode:
            details.append(f"  • Aktueller Modus: {mode}")
        else:
            self.results.append(
                CheckResult(
                    name="P0: bounded_auto Guardrails",
                    status="ERR",
                    message="Promotion-Modus nicht konfiguriert",
                )
            )
            return

        # Check min_confidence_for_auto_apply
        min_conf = safety_section.get("min_confidence_for_auto_apply")
        if min_conf is not None:
            details.append(f"  • Min. Confidence für Auto-Apply: {min_conf}")
        else:
            details.append("  ⚠️  min_confidence_for_auto_apply nicht gesetzt (Default wird verwendet)")

        # Check for auto_apply_whitelist (optional but good to have)
        whitelist = safety_section.get("auto_apply_whitelist", [])
        if whitelist:
            details.append(f"  • Auto-Apply Whitelist: {len(whitelist)} Targets")
            if self.verbose:
                for target in whitelist:
                    details.append(f"    - {target}")

        self.results.append(
            CheckResult(
                name="P0: bounded_auto Guardrails",
                status="OK",
                message="Guardrails im Code konfiguriert",
                details=details if details else None,
            )
        )

    def _check_p1_promotion_lock_config(self) -> None:
        """Check P1: Global promotion lock configuration."""
        if not hasattr(self, "config_data"):
            return

        governance_section = (
            self.config_data.get("promotion_loop", {}).get("governance", {})
        )

        lock_value = governance_section.get("global_promotion_lock")

        if lock_value is None:
            self.results.append(
                CheckResult(
                    name="P1: Globaler Promotion-Lock",
                    status="ERR",
                    message="global_promotion_lock nicht konfiguriert",
                )
            )
            return

        details = [f"  • Lock-Status: {'🔒 LOCKED' if lock_value else '🔓 UNLOCKED'}"]

        if lock_value:
            details.append("  ℹ️  bounded_auto ist derzeit durch Lock deaktiviert")

        self.results.append(
            CheckResult(
                name="P1: Globaler Promotion-Lock",
                status="OK",
                message="Promotion-Lock konfiguriert",
                details=details if self.verbose else None,
            )
        )

    def _check_p1_audit_log_config(self) -> None:
        """Check P1: Audit log configuration."""
        if not hasattr(self, "config_data"):
            return

        governance_section = (
            self.config_data.get("promotion_loop", {}).get("governance", {})
        )

        audit_log_path = governance_section.get("audit_log_path")

        if not audit_log_path:
            self.results.append(
                CheckResult(
                    name="P1: Audit-Log Settings",
                    status="WARN",
                    message="audit_log_path nicht konfiguriert (Default wird verwendet)",
                )
            )
            return

        details = [f"  • Audit-Log-Pfad: {audit_log_path}"]

        # Check if parent directory exists
        full_path = PROJECT_ROOT / audit_log_path
        if full_path.parent.exists():
            details.append("  • Verzeichnis existiert: ✓")
        else:
            details.append("  ⚠️  Verzeichnis existiert noch nicht (wird bei Bedarf erstellt)")

        self.results.append(
            CheckResult(
                name="P1: Audit-Log Settings",
                status="OK",
                message="Audit-Log-Konfiguration vorhanden",
                details=details if self.verbose else None,
            )
        )

    def _print_results(self) -> None:
        """Print check results in human-readable format."""
        print("Checks:")
        print()

        for result in self.results:
            # Status symbol
            if result.status == "OK":
                symbol = "✓"
                color_code = "\033[32m"  # Green
            elif result.status == "WARN":
                symbol = "⚠"
                color_code = "\033[33m"  # Yellow
            else:  # ERR
                symbol = "✗"
                color_code = "\033[31m"  # Red

            reset_code = "\033[0m"

            # Print main line
            print(f"  {color_code}[{result.status}]{reset_code} {result.name}")
            if self.verbose or result.status in ["WARN", "ERR"]:
                print(f"      → {result.message}")

            # Print details if verbose or if there are warnings/errors
            if result.details and (self.verbose or result.status in ["WARN", "ERR"]):
                for detail in result.details:
                    print(f"      {detail}")

            print()

        # Overall status
        has_errors = any(r.status == "ERR" for r in self.results)
        has_warnings = any(r.status == "WARN" for r in self.results)

        print("─" * 60)
        print()

        if has_errors:
            print("\033[31mStatus: NOT READY (NO-GO)\033[0m")
            print()
            print("Probleme gefunden:")
            for result in self.results:
                if result.status == "ERR":
                    print(f"  ✗ {result.name}: {result.message}")
            print()
            print("Empfehlung:")
            print("  Siehe docs/learning_promotion/BOUNDED_AUTO_SAFETY_PLAYBOOK.md")
            print("  und ergänze die fehlenden Konfigurationen, bevor bounded_auto aktiviert wird.")
        else:
            print("\033[32mStatus: READY (GO)\033[0m")
            print()
            if has_warnings:
                print("Hinweise:")
                for result in self.results:
                    if result.status == "WARN":
                        print(f"  ⚠  {result.name}: {result.message}")
                print()
            print("✓ bounded_auto kann im Dry-Run-Modus gestartet werden.")
            print("  Siehe docs/learning_promotion/BOUNDED_AUTO_SAFETY_PLAYBOOK.md für Operator-Details.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check bounded_auto readiness (Go/No-Go criteria)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0 - READY (GO): All critical checks passed
  1 - NOT READY (NO-GO): At least one critical check failed

Examples:
  python scripts/check_bounded_auto_readiness.py
  python scripts/check_bounded_auto_readiness.py --verbose
        """,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information for all checks",
    )

    args = parser.parse_args()

    checker = ReadinessChecker(verbose=args.verbose)
    is_ready = checker.run_all_checks()

    sys.exit(0 if is_ready else 1)


if __name__ == "__main__":
    main()


