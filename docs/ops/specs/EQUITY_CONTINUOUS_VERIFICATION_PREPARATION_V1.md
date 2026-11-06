---
docs_token: DOCS_TOKEN_EQUITY_CONTINUOUS_VERIFICATION_PREPARATION_V1
status: working
scope: Internal comparison rule and offline verification; continuous operation remains blocked
---

# Equity: interne Abgleichsregel und vorbereitete Betriebsprüfungen

Die interne Regel ist eine dokumentierte technische Entscheidung für die lokale Verifikation. Sie ist kein Vertrag mit OKX und setzt keinen nachgewiesenen allgemeinen Binär64-Vertrag der Börse voraus. Der ursprüngliche native Dezimalbestand und sämtliche historischen Befunde bleiben unverändert. Eine lokale erfolgreiche Prüfung erzeugt weder Kapital- noch Betriebsberechtigung.

## Interner Abgleich

Konfiguration: [lokale Verifikationsregel](../../../config/ops/equity_verification_policy_v1.json). Die primäre Wahrheit für die vorhandene Bewegungsrechnung bleibt das native Journal. Die Publikationsdarstellung ist ein getrenntes Vergleichsziel. Exakte Dezimalgleichheit besteht unverändert als eigener Befund.

Eine unterschiedliche Darstellung darf lokal akzeptiert werden, wenn der beobachtete Dezimalstring genau der definierten kürzesten Binär64-Darstellung entspricht und der verbleibende Betrag höchstens ein Billionstel der jeweiligen nativen Währungseinheit beträgt. Dies ist die ausdrücklich gewählte lokale Obergrenze für USDC, EUR und BTC, keine von der Börse behauptete Genauigkeit. Unbekannte Währungen erlauben ausschließlich exakte Gleichheit. Die Obergrenze allein reicht nicht: Ein beliebiger nahe gelegener Wert wird weiterhin abgewiesen. Große Verluste durch eine grobe Binär64-Darstellung werden ebenfalls abgewiesen.

Funding-Residuen müssen zusätzlich durch die erhaltenen Gegenbuchungsunterschiede vollständig erklärt sein. Eine kleine, aber nicht zugeordnete Buchungslücke wird nicht als Darstellung akzeptiert. Keine Journalbuchung wird gerundet, ersetzt oder angepasst. Die ursprüngliche strengere Rekonstruktion bleibt als unverändertes Teilobjekt im neuen Bericht erhalten.

Die Policy lässt keine Aktivierung, Kapitalfreigabe oder Journalanpassung zu. Entsprechende geänderte Freigabeflags werden vom Loader abgewiesen. Tatsächliche kontinuierliche Beobachtung bleibt ausdrücklich erforderlich. Der lokale Status lautet `LOCAL_VERIFICATION_PASS_RUNTIME_BLOCKED` oder `LOCAL_VERIFICATION_BLOCKED`.

## Vorbereitete Prüfungen und behobene Binding-Fehler

Der bestehende lineare Futures-Kern wird weiterverwendet. Es entsteht kein zweites PnL-Modell. Die mathematischen Primitive im kanonischen Kernel bleiben unverändert; korrigiert wird die Zusammensetzung im bestehenden Accounting-Binding:

- Brutto-realisiertes PnL und Gebühren sind getrennt. Eine Schließungsgebühr wird genau einmal abgezogen; Teilpositionen behalten die Gebühreninformation.
- Slippage steckt bereits im Ausführungspreis. Ihre Attribution bleibt sichtbar, wird aber nicht nochmals vom Bestand abgezogen.
- Beobachtetes Funding wird signiert, währungs- und instrumentgebunden sowie idempotent erfasst. Die kumulierte Wirkung bleibt nach Schließung und Neustart erhalten. Die analytische Portfolio-Shell verwendet ihren bestehenden Ausgaben-Vorzeichenvertrag und denselben Cash-Bestand.
- Ein gewichteter Einstand wird nicht auf einen handelbaren Preistick gerundet. Die Equity erhält keinen pauschalen Acht-Nachkommastellen-Abschlag.
- Identische Fill-/Funding-IDs mit identischem Inhalt sind Wiederholungen; widersprüchlicher Inhalt wird abgewiesen. Ein Replay setzt einen neueren Mark nicht zurück. Explizit verspätete Fill-Zeitpunkte und falsche Instrumente werden abgewiesen.
- Fehlgeschlagene Fill-/Mark-Berechnungen übernehmen keinen teilweise veränderten Zustand. Die Zuordnung der Fill-Anzahl im zurückgegebenen Zustand enthält die gerade verarbeitete Ausführung.

Die Tests verwenden bewusst kontrollierte Daten und explizite Anfangsbestände. Long und Short werden für drei unterschiedliche Symbol-/Multiplier-/Preisfälle von Öffnung über Marktbewertung und Funding bis Teilverkauf, vollständiger Schließung und Neustart geprüft. Ein längerer kontrollierter Verlauf enthält 500 Fills, 250 Funding-Ereignisse und zehn gespeicherte Neustarts. Ein zusätzlicher Betriebssystemprozess lädt einen echten temporären Accounting-Checkpoint und wiederholt Fill sowie Funding idempotent bei gesperrtem Netzwerk. Dies ist ein Belastungs-/Konsistenztest, keine 24-Stunden-Beobachtung und kein echter Handel.

Nur lineare Kontrakte sind hier positiv geprüft. Eine explizit inverse Kennzeichnung wird abgewiesen. Die noch vorhandene ältere Default-Metadatenkonstruktion ist kein Beweis für die tatsächliche Kontraktart eines beliebigen Instruments. Frische reale Instrumentbindung und unterstützte Bewertung müssen vor einer späteren realen Nutzung separat belegt sein. Der echte Account-Replay bleibt für reale offene Positionen gesperrt.

## Zustand und Neustart

Neue Checkpoints verwenden Version 2 und enthalten Funding-Ledger, signierte Funding-Summe, Fill-Identitäten, letzten Fill-Zeitpunkt und abgeleitete Zustände. Der Loader überprüft ein vollständiges Manifest mit erlaubten Dateinamen, Hashes und Pflichtdateien; abweichende Owner, unbekannte Aktionen und widersprüchliche Ableitungen werden abgewiesen. Ein fehlender Anfangsbestand wird nicht durch den Simulationsstandard ersetzt; ein expliziter Null-Anfangsbestand bleibt Null.

Ältere Version-1-Checkpoints werden nicht automatisch übernommen, umgerechnet oder überschrieben. Sie benötigen bei späterer Wiederaufnahme eine ausdrücklich nachgewiesene Rekonstruktion aus ihren Eingangsbelegen. Vorhandene Originale wurden in dieser Arbeit nicht verändert. Dieser Schritt behauptet keine abgeschlossene Migration vorhandener Laufzeitbestände.

Die vorhandene Bundle-Publikation ist keine einzelne atomare Transaktion über sämtliche Dateien. Der injizierte Abbruch zwischen den Dateien wird beim Lesen erkannt und blockiert den Neustart. Eine automatische Reparatur oder sichere Fortsetzung eines solchen Zwischenzustands wird nicht behauptet. Writer-Ausschluss und die vorhandene persistente Close-/Custody-Kette bleiben zusätzlich geprüft.

## CLI und erhaltene Betriebsgrenze

Der bestehende Einstieg `scripts.ops.run_real_equity_reconciliation_v1` erhält `--verification-policy`. Ohne diese Option bleiben ursprünglicher Bericht und ursprüngliche strenge Rückgabesemantik erhalten. Mit ihr wird ein neues Ergebnisobjekt aus Originalrekonstruktion und separater interner Bewertung erzeugt. Der Ergebnis-Hash bindet die tatsächlich geschriebene Gesamtausgabe; der ursprüngliche Rekonstruktionshash bleibt getrennt sichtbar. Die Option gilt ausschließlich für Offline-Replay.

Die gespeicherten echten Originale bestehen den lokalen Abgleich ohne neue Börsenabfrage. Der bestehende exakte Gleichheitsbefund wird dadurch nicht nachträglich wahr. Der tatsächliche Dauerbetrieb, echte offene Positionsbewertung und Kapitalfreigabe bleiben blockiert. Es werden weder Dienste noch Orders ausgelöst. U04, P01, bestehender Treasury-Kapital-Owner und Lernbestände bleiben unverändert.

Nachweis: [lokale Vorbereitung und Tests](../evidence/EQUITY_CONTINUOUS_PREPARATION_2026_11_03.md).
