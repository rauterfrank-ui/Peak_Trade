# Peak_Trade Visual Operator Dashboard Product Runbook v1.3

> **Canonical dashboard master runbook (Composition + Landmark + Discovery):**
> [Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md](Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md)
>
> This file is a **compatibility / contract surface** for path-bound tests and historical references.
> It does **not** define a second product norm and must not diverge from the Master Runbook.

## Role

```text
CANONICAL_DASHBOARD_MASTER_RUNBOOK=docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md
PRODUCT_RUNBOOK_ROLE=COMPATIBILITY_CONTRACT_SURFACE
BUSINESS_SSOT=MASTER_V2_AND_DOUBLE_PLAY
DASHBOARD_ROLE=READ_ONLY_CONSUMER_DISPLAY_LAYER
DASHBOARD_CREATES_SECOND_TRUTH=false
PART_I_NORMATIVE_OWNER=MASTER_RUNBOOK
PART_II_DISCOVERY_SNAPSHOT_OWNER=MASTER_RUNBOOK
VERSION=v1.3
```

- Fachliche Business-SSOT bleibt ausschließlich **Master V2 und Double Play**.
- Das Dashboard bleibt **Consumer-/Display-only**.
- Normative Composition-/Landmark-Vorgaben und der technische Discovery-Snapshot leben im Master Runbook (PART I / PART II).
- Diese Datei behält die maschinenlesbare Browser-Verification-Policy für bestehende Repo-Contracts.

# 6A. Browser Verification Policy

Diese Policy ist für alle visuellen Dashboard-Slices verbindlich.

``` text
PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_BROWSER_AUTOMATION=PLAYWRIGHT
PRIMARY_PLAYWRIGHT_CHANNEL=chrome
PRIMARY_BROWSER_SCREENSHOTS=CHROME
PRIMARY_DOM_ASSERTIONS=CHROME
PRIMARY_CONSOLE_ASSERTIONS=CHROME
PRIMARY_NETWORK_ASSERTIONS=CHROME
PRIMARY_INTERACTION_ASSERTIONS=CHROME

CHROMIUM_FALLBACK_ALLOWED=true
CHROMIUM_FALLBACK_MUST_BE_REPORTED=true
PLAYWRIGHT_CHROMIUM_IS_NOT_REAL_CHROME=true

WEBKIT_VERIFICATION=SECONDARY
WEBKIT_IS_NOT_REAL_SAFARI=true

REAL_SAFARI_VERIFICATION=SECONDARY
SAFARI_REQUIRED_FOR_NORMAL_SLICE_MERGE=false
SAFARI_FAILURE_BLOCKS_NORMAL_SLICE=false

POST_SLICE_INTERACTIVE_OPEN=REAL_CHROME
```

Verbindliche Regeln:

1.  Google Chrome über Playwright ist der primäre Browser für
    Entwicklung, visuelle Abnahme, Screenshots, DOM-, Console-, Network-
    und Interaktionsprüfungen.
2.  Playwright verwendet nach Möglichkeit den lokal installierten
    Google-Chrome-Channel `chrome`.
3.  Falls echter Google Chrome technisch nicht verfügbar ist, darf
    Playwright Chromium als Fallback verwendet werden.
4.  Ein Chromium-Fallback muss ausdrücklich berichtet werden und darf
    niemals als echter Google-Chrome-Nachweis bezeichnet werden.
5.  WebKit ist ausschließlich ein sekundärer
    Engine-Kompatibilitätscheck.
6.  WebKit darf nicht als echter Safari-Nachweis bezeichnet werden.
7.  Echter Safari ist ein optionaler sekundärer Kompatibilitätscheck.
8.  Safari oder WebKit sind für normale Dashboard-Slices keine
    allgemeinen Merge-Blocker.
9.  Safari wird nur dann zum Blocker, wenn ein konkreter späterer
    Release-Gate dies ausdrücklich verlangt.
10. Nach erfolgreichem Slice soll das Dashboard für die Operator-Prüfung
    sichtbar in realem Google Chrome geöffnet werden.
11. Browser-Evidence muss den tatsächlich verwendeten Browser eindeutig
    ausweisen.
12. Die bestehende Self-only-Netzwerk- und Read-only-Policy bleibt
    unverändert.

------------------------------------------------------------------------
