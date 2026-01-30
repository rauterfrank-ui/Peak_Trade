## How-To: Live-Track v1.1 in 3 Minuten nutzen

Ziel: In **3 Minuten** den kompletten Live-Track-Stack im Demo-Mode einmal anfassen – von CLI bis Dashboard.  
Ideal für einen schnellen Funktionstest, Onboarding oder eine Mini-Demo.

---

### 1. Shadow-/Testnet-Session starten (CLI)

Im Projekt-Root:

```bash
cd /path/to/Peak_Trade
source .venv/bin/activate

python3 scripts/run_execution_session.py \
  --mode shadow \
  --config config/live/demo_session.toml
```

* Ergebnis: Eine neue Shadow-/Testnet-Session wird registriert.
* Details zur Registry/CLI findest du im Live-Track-Stack (Phase 80/81).

---

### 2. Live-Readiness / Registry kurz prüfen (optional, aber empfehlenswert)

```bash
python3 scripts/check_live_readiness.py
```

* Erwartung: Alle Checks im grünen Bereich für Shadow-/Testnet.
* Bestätigt, dass Demo-Stack sauber läuft, ohne Live-Orders zu riskieren.

---

### 3. Web-Dashboard starten

```bash
python3 scripts/operator_dashboard.py
```

* Merke dir die ausgegebene URL (typisch `http://127.0.0.1:8000` oder ähnlich).
* Browser öffnen und auf diese Adresse gehen.

---

### 4. 2-Minuten-Demo im Dashboard fahren

Nutze jetzt das vorbereitete Demo-Script, um das Live-Track Web-Dashboard v1.1 zu zeigen:

**Fokus im Dashboard:**

1. **System-Header**

   * Betriebsmodus (Shadow/Testnet), Tiering, **Live-Lock / Safety-Lock** erklären
   * Klar machen: Live-Mode ist weiterhin blockiert, Demo läuft nur in Shadow-/Testnet.

2. **Status-Kacheln**

   * Anzahl Sessions
   * Verteilung Shadow vs. Testnet
   * letzte Runs / Aktivität kurz erläutern

3. **Session-Tabelle**

   * Die soeben gestartete Demo-Session finden und kurz erklären
   * Kontext: Mode, Tier, Startzeit, Status

4. **Brücke CLI ↔ Dashboard**

   * Deutlich machen: Was wir in der CLI gestartet/registriert haben, taucht hier im UI auf.

**Dazu passende Dokumente:**

* Voller Demo-Walkthrough (CLI → Registry → Dashboard):
  `docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`

* 2-Minuten-Moderationsscript inkl. Cheat-Sheet:
  `docs/DEMO_SCRIPT_DASHBOARD_V11.md`

* Kurz-How-To im Playbook (Operator-Fokus):
  `docs/LIVE_DEPLOYMENT_PLAYBOOK.md` → Abschnitt **12.5 Kurz-How-To: Live-Track Dashboard Demo (ca. 2 Minuten)**

---

### 5. Safety-Botschaft klar kommunizieren

* Der komplette Flow läuft **nur in Shadow-/Testnet-Mode**.
* Live-Mode bleibt durch bestehende Safety-Gates blockiert.
* Release v1.1 ist ein **Demo- und Onboarding-Release** für den Live-Track-Stack –
  es ändert **keine** Kern-Execution- oder Risk-Logik, sondern ergänzt:

  * Dashboard-Ansicht
  * Demo-/Onboarding-Dokumentation
  * Operator-How-Tos.

Damit kannst du v1.1 jederzeit in wenigen Minuten zeigen – von der CLI über Readiness-Check bis ins Live-Track Web-Dashboard v1.1.
