# Gezielte Auswertung: 8 portable_verify-Failures

Kurzfassung der Analyse (lf_short.txt, lf_long.txt, sandbox_safe.txt). Gruppierung nach Ursache und konkrete Fix-Optionen.

---

## 1) Governance-Import (2 Failures)

**Tests:**
- `tests/ingress/test_ingress_cli_smoke.py::test_cli_empty_input_exits_zero_and_prints_two_paths`
- `tests/ingress/test_ingress_cli_smoke.py::test_cli_with_label_exits_zero`

**Fehler:**  
`ModuleNotFoundError: No module named 'governance'`  
Import-Kette: `ingress_cli` → `ingress_orchestrator` → `l2_to_l3_handoff` → `CapabilityScopeLoader` → `runner` → **`l3_runner`** → `from governance.learning import validate_envelope_learnable_surfaces`.

**Ursache:**  
In `src/ai_orchestration/l3_runner.py` Zeile 17 steht:
```python
from governance.learning import validate_envelope_learnable_surfaces
```
Das Modul liegt unter **`src/governance/learning/`**; der Rest des Repos nutzt `src.governance` (z. B. `src/governance/policy_critic/auto_apply_gate.py`: `from src.governance.learning import ...`).

**Fix (empfohlen):**  
In `src/ai_orchestration/l3_runner.py`:
```python
from src.governance.learning import validate_envelope_learnable_surfaces
```
Damit läuft der Import mit `PYTHONPATH=REPO_ROOT` wie in den Ingress-CLI-Tests.

---

## 2) Network/Bind – Sandbox (5 Failures)

**Tests:**
- `tests/obs/test_ai_live_activity_demo_v1.py::test_ai_live_activity_demo_produces_file_backed_proof`
- `tests/obs/test_ai_live_ops_determinism_v1.py::test_ai_live_ops_verify_script_can_run_against_mock_endpoints`
- `tests/obs/test_prom_query_json_helper.py::test_prom_query_json_helper_retries_and_succeeds`
- `tests/obs/test_prom_query_json_helper.py::test_prom_query_json_helper_supports_positional_alias`
- `tests/obs/test_shadow_mvs_verify_retries.py::test_shadow_mvs_verify_retries_and_warmup_passes`

**Fehler:**  
`PermissionError: [Errno 1] Operation not permitted` bei `s.bind(("127.0.0.1", 0))` bzw. `ThreadingHTTPServer(("127.0.0.1", 0), ...)` → `server_bind()` → `self.socket.bind(self.server_address)`.

**Ursache:**  
Sandbox (z. B. Cursor/CI) erlaubt kein Socket-Bind; die Tests starten lokale HTTP/Prom-Mock-Server.

**Befund sandbox-safe-Suite:**  
`pytest -q -ra -m "not network and not external_tools"` → **6942 selected**, davon **6877 passed**, **3 failed** (die 2 Ingress-CLI + 1 README, keine obs-Bind-Fails). Die 5 obs-Tests werden durch den Marker **nicht** ausgeschlossen (sie haben vermutlich keinen `network`-Marker), schlagen aber in der Sandbox trotzdem fehl.

**Fix-Optionen:**
- **A)** In den 5 Tests (oder zentral in `conftest`) einen Pytest-Marker setzen, z. B. `@pytest.mark.network` oder `@pytest.mark.socket_bind`, und die „sandbox-safe“-Suite mit `-m "not network and not external_tools"` fahren (dann müssen die betroffenen Tests mit diesem Marker versehen werden).
- **B)** Tests in Sandbox überspringen: z. B. `@pytest.mark.skipif(not can_bind_localhost(), reason="sandbox: no socket bind")` mit einer kleinen Hilfsfunktion, die einmal `socket.socket(); s.bind(("127.0.0.1", 0))` probiert.
- **C)** Unverändert lassen; die 5 Tests nur außerhalb der Sandbox (lokal/CI mit Netzwerk) laufen lassen.

---

## 3) README-Assertion (1 Failure)

**Test:**  
`tests/test_ops_pr_inventory_scripts_syntax.py::test_ops_readme_exists`

**Fehler:**  
`assert "PR Inventory" in content or "pr_inventory" in content`  
Der Test liest **`docs/ops/README.md`** aus **git** (`git show HEAD:docs/ops/README.md`). Aktueller Inhalt (laut Failure):  
`# Test README\n<!-- MERGE_LOG_EXAMPLES:START -->\n- PR #281 — ...\n<!-- MERGE_LOG_EXAMPLES:END -->\n\n'`  
→ weder „PR Inventory“ noch „pr_inventory“ kommen vor.

**Ursache:**  
Die echte `docs/ops/README.md` im Repo enthält die erwarteten Begriffe vermutlich; in HEAD ist entweder eine andere Version (z. B. Test-README) oder die Doku wurde nie ergänzt.

**Fix-Optionen:**
- **A)** Inhalt von `docs/ops/README.md` anpassen: mindestens einen der Begriffe „PR Inventory“ oder „pr_inventory“ (und „label“) aufnehmen, damit der Test grün wird.
- **B)** Test anpassen: z. B. andere/weichere Assertion oder andere Datei, falls die Absicht eine andere ist (z. B. nur „label“ prüfen).

---

## Übersicht

| Gruppe              | Anzahl | Ursache                    | Schnellster Fix                          |
|---------------------|--------|----------------------------|------------------------------------------|
| Governance-Import   | 2      | Falscher Import in l3_runner | `governance.learning` → `src.governance.learning` |
| Network/Bind        | 5      | Sandbox verbietet bind()   | Marker/Skip für sandbox-safe Suite       |
| README-Assertion    | 1      | HEAD:docs/ops/README.md ohne Stichworte | README ergänzen oder Assertion lockern   |

**Sandbox-safe-Suite (Stand Analyse):**  
3 failed, 6877 passed (nach `-m "not network and not external_tools"`). Die 3 Failures sind die 2× Governance + 1× README; die 5 obs-Bind-Tests sind in dieser Suite enthalten und schlagen in der Sandbox fehl, bis sie per Marker/Skip ausgeklammert werden.

## Closeout — normalize_validator_report_cli (fixed) + suite green

- Fix commit: 604a53fb — scripts(aiops): run normalize validator report without PYTHONPATH (repo-root sys.path + src imports)
- Root cause: subprocess-run CLI script without PYTHONPATH; sys.path previously pointed at repo_root/src which breaks `import src.*`.
- Fix: scripts/aiops/normalize_validator_report.py now inserts repo-root on sys.path and uses `from src.ai_orchestration.*` imports.
- Verification:
  - pytest -q: 14 passed (Exit 0)
  - pytest -ra: 14 passed (Exit 0)
  - collect-only: 14 tests collected
- Evidence directory:
  - out/ops/portable_verify_failures/fix_normalize_validator_report_cli/
