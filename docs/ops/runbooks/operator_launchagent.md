# Operator LaunchAgent (macOS)

Ziel
- `operator_all.sh` täglich automatisch ausführen (auch wenn du den Laptop zuklappst — beim nächsten Wake/Login läuft es wieder).
- Logs und Evidence bleiben lokal unter `out/ops/`.

Install (empfohlen)
- `START_HOUR=7 START_MINUTE=15 STRICT_ALERTS=true scripts/ops/install_operator_all_launchagent.sh`

Defaults
- Uhrzeit: 07:15 (lokale Zeit)
- `RUN_E2E=true`
- `RUN_ONE_SHOT=true`
- `RUN_REGISTRY=true`
- `STRICT_ALERTS=true`
- `RunAtLoad=true` (läuft zusätzlich beim Login/Load)

Logs
- `out/ops/launchd/operator_all.stdout.log`
- `out/ops/launchd/operator_all.stderr.log`

Status
- `launchctl list | rg -n "com\.peaktrade\.operator_all" -S`

Uninstall
- `scripts/ops/uninstall_operator_all_launchagent.sh`

Hinweis
- Diese Runbooks/Plists sind **nur lokal relevant**. `out/` bleibt untracked.
