# Live-Demo-Script – Web-Dashboard v1.1

> **Dauer:** ca. 2 Minuten  
> **Zielgruppe:** Operatoren, Quant-Leads, Stakeholder  
> **Modus:** Shadow / Testnet (Live ist gesperrt)

---

## Vorbereitung

- Dashboard läuft unter `http://127.0.0.1:8000/`
- 1–2 Shadow-/Testnet-Sessions wurden vorab gestartet (für sichtbare Beispiele)
- Browser-Tab bereit

---

## Script

### 1. Einstieg – Was sehen wir hier?

> „Hier seht ihr das Peak_Trade Web-Dashboard in Version **v1.1**.
> Das ist unsere zentrale Operator-Ansicht für den **Live-Track-Stack** – allerdings aktuell bewusst nur für **Shadow- und Testnet-Sessions** freigegeben."

---

### 2. Header zeigen – System-Health & Live-Lock

*(Zeige oben den Header.)*

> „Oben im Header seht ihr zwei Dinge:
>
> * Zum einen die **Version `v1.1`**, damit klar ist, auf welchem Stand wir sind.
> * Und ganz wichtig: das Badge **‚🟢 System OK'** – damit sieht ein Operator sofort, ob das Setup gesund ist.
>
> Direkt daneben seht ihr **‚🔒 LIVE LOCKED'**.
> Das bedeutet: **Live-Execution ist in dieser Version komplett gesperrt**. Wir können alles beobachten, aber nichts im echten Markt auslösen."

---

### 3. Stats-Kacheln – kurzer Überblick

*(Zeige die kleinen Stats-Kacheln.)*

> „Hier in den **Stats-Kacheln** bekommt ihr einen kompakten Überblick:
>
> * wie viele Sessions es insgesamt gibt,
> * wie viele davon im **Shadow-Mode** laufen,
> * wie viele im **Testnet**,
> * und wie viele bereits abgeschlossen sind.
>
> Gerade in Demos oder im Onboarding ist das super hilfreich, weil man sofort sieht:
> *‚Da läuft wirklich etwas, das System ist aktiv.'*"

---

### 4. Session-Tabelle – Operator-Perspektive

*(Scrolle zur Session-Tabelle, ggf. auf eine frische Shadow/Testnet-Session zeigen.)*

> „Darunter seht ihr die **Session-Tabelle**.
> Die ist bewusst operator-freundlich gebaut:
>
> * klare Spalten-Header,
> * **Zebra-Stripes** für bessere Lesbarkeit,
> * und `tabular-nums`, damit Zahlen sauber ausgerichtet sind.
>
> Jede Zeile ist klickbar – der Operator kann also in eine Session reingehen und sich Details anschauen, ohne irgendetwas im System zu verändern."

---

### 5. Safety-Botschaft – Read-Only & Gates

> „Wichtig ist:
> Dieses Dashboard ist **strictly read-only**.
> Es gibt **keine Endpoints**, um Orders auszulösen, und **Live bleibt über die bestehenden Safety-Gates blockiert**.
>
> Wir nutzen das Dashboard aktuell nur für:
>
> * **Shadow-Sessions**,
> * **Testnet-Sessions**,
> * und für **Demos / interne Showcases**."

---

### 6. Abschluss – Brücke zur CLI

> „Damit ist die Rollenverteilung klar:
>
> * Über die **CLI** starten wir Sessions, registrieren sie und erzeugen Reports.
> * Über das **Web-Dashboard v1.1** erzählen wir die Story: System-Health, laufende Sessions, Shadow/Testnet-Aktivität.
>
> Für Operatoren ist das die ideale Einstiegssicht, um in den Live-Track-Stack reinzukommen, ohne irgendein Risiko im echten Markt zu haben."

---

## Cheat-Sheet für den Moderator

| Punkt | Kernaussage | UI-Element |
|-------|-------------|------------|
| 1 | Dashboard v1.1, Shadow/Testnet only | – |
| 2 | System OK + LIVE LOCKED | Header-Badges |
| 3 | Überblick: Total, Shadow, Testnet, Completed | Stats-Kacheln |
| 4 | Operator-freundliche Tabelle, klickbar | Session-Tabelle |
| 5 | Read-only, keine Order-Endpoints | – |
| 6 | CLI startet, Dashboard zeigt | – |

---

## Referenzen

- **Demo-Walkthrough:** [`docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)
- **Web-Dashboard v1.1 (Code):** `src/webui/app.py`
- **Live-Track Service (Code):** `src/webui/live_track.py`

---

*Peak_Trade – Web-Dashboard v1.1 Demo-Script · Stand: Dezember 2024*
