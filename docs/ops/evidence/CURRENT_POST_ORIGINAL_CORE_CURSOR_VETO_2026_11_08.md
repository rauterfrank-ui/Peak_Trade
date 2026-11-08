---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_CORE_CURSOR_VETO_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Originaler Core-Cursor erreicht den späteren Versandconsumer

Basis 59bbf23613f213c44ece06cc52a5eb439b684542, derselbe Arbeitsbranch
fix/current-entry-policy-plan-revalidation. [Semantik](../specs/CURRENT_POST_ORIGINAL_CORE_CURSOR_VETO_V1.md)
und [JSON-Beleg](CURRENT_POST_ORIGINAL_CORE_CURSOR_VETO_2026_11_08.json) binden
Originalquellen, ursprünglichen Producer, aktuelle Consumer und Prüfstand.

Zwei Gegenproben durch den tatsächlichen N1-/Supervisorpfad erreichen am
unveränderten Basisstand echte gespeicherte Long-/Short-Pläne, aber keinen
gespeicherten Core-Cursorbezug. Beide scheitern am fehlenden Feld. Das ist
ein reproduzierter Quellenübergabefehler, kein ausgeführter Venuekontakt.

Der tatsächliche N1-Producer übergibt nun seinen wirklichen Decisionparent und
seinen tatsächlichen Lane-Cursorroot an denselben Originalbudgetwriter. Die
explizite neue Originversion v2 bindet diesen Bezug neben unverändertem Intent
und Venueplan in denselben Origindigest. Bestehendes Plancontext-Receipt und
ursprüngliche V2-Budgetrevisionen tragen die Bindung weiter. Alte Originversion
v1 bleibt lesbar und erhält keine erfundene aktuelle Quelle.

Der spätere Originalconsumer liest genau diese Quelle erneut. Die ursprüngliche
typisierte SideState.KILL_ALL-Sperre und fehlende/beschädigte/fremde Cursorquellen
stoppen den Entry. Ein neuer Cursor-Payloaddigest oder logischer Epochenfortschritt
allein erzeugt keine pauschale Ablaufregel und keine neue positive Coreadmission.
Der vorhandene POST_BUDGET-Pfad erhält den konkreten Core-Fehler und kann nur
denselben ursprünglichen PRE_SOCKET-Claim negativ schließen. Nach möglicher
Socketwirkung bleiben Ungewissheit, Permitverbrauch und Hold bestehen.

Die erste Producerprüfung besteht mit zwei Fällen; die Erweiterung mit 44.
Die 15 weiteren Herkunfts-/Cold-/Ausfallfälle bestehen ebenfalls. Der endgültige
gemeinsame Lauf endet mit **1243 PASS, Exit 0, ohne Deselektion**: bisherige
1184 Fälle und 59 neue. 1900 Pythonquellen, darunter 1834 tatsächlich geladene
Repomodule, sind vor und nach dem Lauf hashgebunden. Kommando, Runner, Wrapper,
Inventar und Loghash stehen im JSON. Derselbe abgeschlossene PASS wird beim
Commit wiederverwendet.

Der ursprüngliche Core, Cursorwriter und SideState-Parser bleiben bytegleich;
der neue Anschluss liegt an Producerübergabe, Originalpersistenz und späterem
Consumer. Reconciliation und kaltes Storage-Lesen erhalten keine neue mutable
Cursoradmission: Hold und Quellenbezug bleiben auch bei KILL_ALL oder fehlender
Cursordatei erhalten. Der kalte Owner verlangt weiterhin originale Recovery.

**Offen bleiben:** vollständige spätere Richtung-/Scope-/Regime-/Confirmation-
und numerische Risikozulassung, aktuelle unabhängige Markt-/Finanzinputs,
produktive Riskpolicy, eigenständige Sendemandate, globale Root-/Ownerherkunft,
signierte Recovery, vollständige Custody und autonomer Host. Die alte Offline-
Riskpolicy wird nicht produktiv umbenannt. Sieben ältere Collector-/Account-
Verträge und breitere Abnahme bleiben offen. Kein operativer Safetyzustand,
Credential, Venuezugriff, Kapitalfluss oder Aktivierungszustand wurde verändert.
