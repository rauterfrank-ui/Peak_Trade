# Peak_Trade Visual Operator Dashboard Product Runbook v1.3

> **Supersession (Architecture Reset / Rebuild scope):** Compatibility-/Contract-Surface bleibt als Evidence erhalten. Für den neuen Architecture-Reset-/Rebuild-Scope gilt ausschließlich [Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md](Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md). Keine automatische Implementierungsfreigabe.
>
> **Historical dashboard master runbook (Composition + Landmark + Discovery):**
> [Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md](Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md)
>
> This file is a **compatibility / contract surface** for path-bound tests and historical references.
> It does **not** define a second product norm and must not diverge from the historical Master Runbook.

## Role

```text
HISTORICAL_PRODUCT_REFERENCE=docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md
COMPATIBILITY_REFERENCE=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
PRODUCT_RUNBOOK_ROLE=COMPATIBILITY_CONTRACT_SURFACE
STATUS=HISTORICAL_PRE_RESET
SUPERSEDED_FOR_ARCHITECTURE_RESET_REBUILD=true
ACTIVE_FOR_ARCHITECTURE_RESET_REBUILD_SCOPE=false
BUSINESS_SSOT=MASTER_V2_AND_DOUBLE_PLAY
DASHBOARD_ROLE=READ_ONLY_CONSUMER_DISPLAY_LAYER
DASHBOARD_CREATES_SECOND_TRUTH=false
PART_I_NORMATIVE_OWNER=HISTORICAL_MASTER_RUNBOOK_PRE_RESET
PART_II_DISCOVERY_SNAPSHOT_OWNER=HISTORICAL_MASTER_RUNBOOK_PRE_RESET
ARCHITECTURE_RESET_REBUILD_GOVERNED_BY=docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md
VERSION=v1.3
```

- Für den **Architecture-Reset-/Rebuild-Scope** gilt ausschließlich [Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md](Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md).
- Fachliche Business-SSOT bleibt ausschließlich **Master V2 und Double Play**.
- Das Dashboard bleibt **Consumer-/Display-only**.
- Historische Composition-/Landmark-Vorgaben und der technische Discovery-Snapshot leben im historischen Master Runbook (PART I / PART II; pre-reset only).
- Diese Datei behält die maschinenlesbare Browser-Verification-Policy für bestehende Repo-Contracts (Chrome/Playwright primary).

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
