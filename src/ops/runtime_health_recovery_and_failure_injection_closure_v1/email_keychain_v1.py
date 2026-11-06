"""Scoped mail password storage: macOS Keychain prompt, never argv or config.

This is separate from venue credential provisioning and grants no trading access.
The user enters/submits the new GMX app-password directly in their local terminal.
"""

import json
import os
from pathlib import Path
import platform
import smtplib
import ssl
import subprocess
import tempfile

MAIL_KEYCHAIN_SERVICE = "peak_trade.runtime_recovery_email_v1"


def read_mail_keychain_password_v1(account: str) -> str:
    if platform.system() != "Darwin":
        return ""
    try:
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-a",
                account,
                "-s",
                MAIL_KEYCHAIN_SERVICE,
                "-w",
            ],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode:
        return ""
    try:
        return result.stdout.decode("utf-8").rstrip("\r\n")
    except UnicodeError:
        return ""


def _save_private_config_v1(path: Path, config: dict) -> None:
    fd, staged = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
    finally:
        Path(staged).unlink(missing_ok=True)


def provision_mail_keychain_v1(config_path: Path) -> bool:
    """Interactive only. A successful setup authenticates SMTP but sends no mail."""
    if platform.system() != "Darwin":
        raise RuntimeError("MAIL_KEYCHAIN_REQUIRES_MACOS")
    if not os.isatty(0) or not os.isatty(1):
        raise RuntimeError("MAIL_SETUP_REQUIRES_USER_TERMINAL")
    path = Path(config_path)
    config = json.loads(path.read_text(encoding="utf-8"))
    # This owner-specific setup is intentionally scoped to the requested GMX
    # account/provider; arbitrary config destinations cannot receive the password.
    if (
        config.get("smtp_host") != "mail.gmx.net"
        or config.get("smtp_port") != 587
        or config.get("smtp_user") != config.get("from_address")
        or config.get("to_addresses") != [config.get("smtp_user")]
    ):
        raise ValueError("MAIL_SETUP_GMX_BINDING_UNPROVEN")
    account = config["smtp_user"]
    print("PeakTrade – GMX-App-Passwort sicher hinterlegen", flush=True)
    print(f"Konto: {account}", flush=True)
    print("Erstelle zuerst bei GMX ein App-Passwort mit dem Namen PeakTrade.", flush=True)
    print("Verwende hier das GMX-App-Passwort, nicht dein normales Konto-Passwort.", flush=True)
    print("Die anschließende Eingabe bei 'password data' bleibt unsichtbar.", flush=True)
    print(
        "Die Speicherung erfolgt im macOS-Schlüsselbund, nicht in dieser Datei oder im Chat.",
        flush=True,
    )
    existing = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-a", account, "-s", MAIL_KEYCHAIN_SERVICE],
        capture_output=True,
        check=False,
        timeout=15,
    )
    if existing.returncode:
        input("Sobald das GMX-App-Passwort vorliegt: Enter drücken (Abbruch mit Strg+C). ")
        # macOS security explicitly documents -w LAST as its interactive prompt.
        # Inherit the user's terminal. Never obtain the new secret in our argv,
        # environment, script source, chat or captured output. Never use -A/-U.
        result = subprocess.run(
            [
                "/usr/bin/security",
                "add-generic-password",
                "-a",
                account,
                "-s",
                MAIL_KEYCHAIN_SERVICE,
                "-l",
                "PeakTrade GMX Betriebsbenachrichtigungen",
                "-w",
            ],
            check=False,
        )
        if result.returncode:
            print("Speichern abgebrochen. Vorhandene Einstellungen bleiben erhalten.", flush=True)
            return False
    else:
        print("Vorhandener PeakTrade-Mail-Eintrag bleibt erhalten.", flush=True)
    config["password_source"] = "macos_keychain"
    config["keychain_service"] = MAIL_KEYCHAIN_SERVICE
    _save_private_config_v1(path, config)
    password = read_mail_keychain_password_v1(account)
    if not password:
        print("Schlüsselbundzugriff noch nicht bestätigt. Es wurde nichts versendet.", flush=True)
        return False
    try:
        with smtplib.SMTP("mail.gmx.net", 587, timeout=20) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(account, password)
    except (OSError, smtplib.SMTPException):
        print(
            "Gespeichert. Die GMX-Anmeldung konnte noch nicht bestätigt werden. Bitte App-Passwort und GMX-Einstellungen prüfen.",
            flush=True,
        )
        return False
    finally:
        password = ""
    print("Gespeichert. Die SMTP-Anmeldung bei GMX war erfolgreich.", flush=True)
    print("Es wurde keine Test-E-Mail gesendet. Du kannst dieses Fenster schließen.", flush=True)
    return True


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Lokale verdeckte Eingabe des GMX-App-Passworts.")
    parser.add_argument("--config-path", type=Path, required=True)
    args = parser.parse_args()
    return 0 if provision_mail_keychain_v1(args.config_path) else 1


if __name__ == "__main__":
    raise SystemExit(main())
