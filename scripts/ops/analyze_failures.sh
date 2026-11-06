#!/usr/bin/env bash
# Recommendation: gezielt die 8 Failures analysieren (schnell, deterministisch),
# dann eine "sandbox-safe" Standard-Suite definieren (Marker/Skip) + optional "network suite" separat.
# Keine timeouts – volle Laufzeit für pytest-Suiten.
# Ohne set -e, damit alle Schritte durchlaufen auch bei Failures.
set -uo pipefail
cd /Users/frnkhrz/Peak_Trade

# 0) Repro: nur die 8 Failures nochmal mit maximaler Signalqualität
python3 -m pytest -q --lf -vv --maxfail=1 || true
python3 -m pytest -q --lf -vv || true

# 1) Failures sammeln (kurz + voll) in Artefakte
mkdir -p out/ops/portable_verify_failures
python3 -m pytest -q --lf --tb=short -rA | tee out/ops/portable_verify_failures/lf_short.txt || true
python3 -m pytest -q --lf --tb=long  -rA | tee out/ops/portable_verify_failures/lf_long.txt  || true

# 2) Gruppieren nach Ursache (governance import / network bind / README assertion)
rg -n "ModuleNotFoundError: No module named 'governance'" -S out/ops/portable_verify_failures/lf_long.txt || true
rg -n "PermissionError: \[Errno 1\]|Operation not permitted|bind\(" -S out/ops/portable_verify_failures/lf_long.txt || true
rg -n "test_ops_readme_exists|PR Inventory|pr_inventory" -S out/ops/portable_verify_failures/lf_long.txt || true

# 3) Governance-Import-Fix: wo liegt das Modul wirklich? (häufig: src/governance oder scripts/governance)
rg -n --hidden --glob '!.git/' '^package_name\s*=\s*"governance"|^name\s*=\s*"governance"' pyproject.toml setup.cfg setup.py || true
find . -maxdepth 3 -type d -name governance -print
python3 - <<'PY'
import sys, os
print("cwd:", os.getcwd())
print("sys.path[0:6]:", sys.path[:6])
PY

# Check ob tests/ingress cli ein falsches import target hat
rg -n --hidden --glob '!.git/' "import governance|from governance" src tests scripts || true
rg -n --hidden --glob '!.git/' "ingress.*cli|cli.*ingress" tests/ingress -S || true

# 4) Network/Sandbox: existierende Marker ansehen und sandbox-safe suite laufen lassen
# (Du hattest bereits Marker wie network/external_tools; wir re-use'n das.)
python3 -m pytest -q -ra -m "not network and not external_tools" | tee out/ops/portable_verify_failures/sandbox_safe.txt || true

# 5) Wenn du "außerhalb der Sandbox" (mit Netzwerk) laufen lassen willst:
#    (lokal auf deiner Maschine normal, nicht in eingeschränkter Sandbox)
#    => explizit nur network marker:
# python3 -m pytest -q -ra -m "network" | tee out/ops/portable_verify_failures/network_only.txt

# 6) README-Test: genau die Assertion anschauen
python3 -m pytest -q -vv tests/test_ops_pr_inventory_scripts_syntax.py::test_ops_readme_exists --tb=long || true
rg -n "PR Inventory|pr_inventory" -S README.md docs/ops/README.md docs/ops/**.md || true

# 7) Quick decision helpers:
# - Nur Governance-Fails isolieren:
python3 -m pytest -q -vv tests/ingress -k "cli" --tb=short || true
# - Nur obs/prom fails isolieren:
python3 -m pytest -q -vv tests/obs -k "prom|server|bind|socket" --tb=short || true
