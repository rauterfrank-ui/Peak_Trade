---
docs_token: DOCS_TOKEN_BTC_OCCUPIED_RECONCILIATION_AND_MONETARY_SCOPE_V1
authority: NONE
runtime_authorization_effect: NONE
---

# BTC: aktuelle Positionswahrheit und monetäre Grenzen

Prüfbasis: `64556dd803c482a8e477c92988bf604b903fa4cf` (PR #7382),
22. November 2026. Diese lokale Fortschreibung prüft die verbliebenen
USD-/USDC- und autonomen Demo-Grenzen nach dem
[Core-/Cursor-/G17-Anschluss](BTC_OFFLINE_CORE_CURSOR_G17_CLOSURE_V1.md).
Keine Betriebs-, Capture-, Demo-, Paper-, Shadow-, Trainings- oder
Researchsitzung wird gestartet oder terminiert.

## Reproduzierter Fehler am Positionsconsumer

Der [BTC-Offlinehost](../../../src/ops/btc_demo_offline_trading_host_v1.py)
verwendete zur weiteren Positionsentscheidung einen gespeicherten positiven
Fill-Abgleich ohne Prüfung seiner aktuellen Frische. Der Gegenfall an der
Prüfbasis akzeptierte einen neuen Mark zehn Sekunden nach diesem Abgleich.
Das ist außerhalb des bestehenden Fünfsekundenvertrags für die betreffende
Kontobeobachtung. Ein frischer Mark macht die Kontobeobachtung nicht frisch.

Vor jedem weiteren Occupied-Core-Aufruf muss der Caller jetzt den aktuellen
originalen Ausführungsabgleich ausdrücklich übergeben. Der
[ursprüngliche Budget-/Reconciliationanschluss](../../../src/ops/btc_demo_budget_reconciliation_host_v1.py)
prüft dessen ursprüngliche V2-Identität, Episode, unverändert abgeglichenen
Zustand und aktuellen Journal-Head. Er rekonstruiert denselben Antwortbatch
mit dem bestehenden Reader und prüft alle einzelnen Empfangszeiten gegen den
vorhandenen Fünfsekundenvertrag. Ein Future-Zeitbezug, veraltete frühere Reads,
offene Pending-Orders oder eine nicht mehr passende bestätigte Position
stoppen vor Core-/Cursor-/Episodenschreiben. Es gibt keinen zusätzlichen GET.

Der ursprüngliche Exchange-Snapshot bindet die Konto-/Config-Empfangszeit
nicht mit. Deshalb bleibt zusätzlich der vollständige geparste Antwortbatch
als unveränderlicher lokaler Beobachtungsbeleg mit Originalrevision erhalten.
Der Consumer liest diesen Inhalt zurück und vergleicht ihn exakt. Neue
Empfangszeiten ergeben einen neuen Beleg, keine umdatierte alte Quelle.
Eine neue Config-Beobachtung kann einen eigenen Beleg besitzen, auch wenn der
ursprüngliche Exchange-Snapshot und seine Budgetrevision unverändert bleiben.
Die Ablage liegt unter der bestehenden isolierten Demowurzel im Unterordner
`execution-observations`. Sie ist Beobachtungsspeicher, kein zweiter
Kapitalledger und kein Berechtigungsbeleg.

Die gespeicherten Antworten, Queries und Empfangszeiten belegen lokale
Konsistenz. Sie beglaubigen weder Venueherkunft noch ursprüngliche HTTP-Bytes
oder die Wahrheit einer vom Betrieb gelieferten Uhr. Fehlende oder beschädigte
lokale Quellen sowie Symlink-Ersetzungen werden abgewiesen. Ein Legacybericht
ohne vollständigen Beleg kann nicht für neue Occupied-Entscheidungen verwendet
werden; ein aktueller Originalabgleich ist erforderlich. Der bisherige native
Erstfill-Readback bleibt mit seinem bisherigen expliziten Bericht lesbar.

Nach Prüfung des Antwortbatches hält der Anschluss die vorhandene Sperre des
Originalbudgetowners und prüft dessen Head nochmals, bevor der Core schreibt.
Damit kann ein weiterer Thread desselben Owners die Budgetrevision während
dieses Core-Aufrufs nicht verändern. Der Core behält seinen eigenen Writer.
Dies ist keine verteilte Transaktion über Budget-, Cursor- und Exit-Stores.
Geschützter Owner, Store, Ledgerformat und Schutzregeln bleiben unverändert.

## Tatsächlicher Richtungswechsel und Wiederanlauf

Die synthetischen positiven Long-/Short-Ketten erreichen weiterhin den echten
ursprünglichen Core und Positionsconsumer. Ein frischer Originalabgleich
ermöglicht den nächsten Mark; er gibt weder Budget noch Orders frei.
Ein kalter Originalbudget-Readback erhält Openingbeleg und Verpflichtung.
Vor weiterer Positionsentscheidung ist wieder eine aktuelle Quelle nötig.
Scheitert das Schreiben des Beobachtungsbelegs nach dem originalen
Budgetcommit, bleibt der Hold bestehen. Die passende Wiederholung kann den
Beleg vervollständigen, ohne eine zweite identische Budgetrevision zu buchen.

Der originale volle Dynamic Scope erzeugt bei der geprüften Gegenbewegung
einen ausstehenden L10-Richtungswechsel für dieselbe Episode. Der tatsächliche
Originalconsumer sperrt weitere Scope-Marks mit
`OCCUPIED_SCOPE_REVERSAL_ALREADY_PLANNED`. Weder eine lokale Flat-Markierung
noch ein Sidewechsel ersetzt bestätigten Fill, Nettobuchung und Folgeepisode.
Die Anfangsposition und der Originalhold bleiben bis zu diesen Nachweisen
erhalten. Die getrennten Mark-/C1-Uhren aus PR #7382 gelten weiter.

## USD, USDC und die ursprünglichen finanziellen Consumer

Der ursprüngliche
[Normalizer](../../../src/ops/governed_productive_monetary_normalization_v1/normalize_v1.py)
besitzt weiterhin USDC-Identität und beobachtete USDT-/USDC-Konvertierung.
Native USD-Operanden scheitern an `NORMALIZATION_UNAVAILABLE_FOR_USD`.
Seine [Konstanten](../../../src/ops/governed_productive_monetary_normalization_v1/constants_v1.py)
setzen USDC als kanonischen Risiko-Numeraire und verlangen dafür allein keinen
physischen USDC-Besitz. Das ist keine Aussage über verfügbare Kontomittel,
ausführbare Konvertierung oder Settlement dieses BTC-Kontrakts.

Der BTC-Bericht gibt jetzt diese Rollen separat zurück: native USD-Preiseinheit,
aus der gelieferten Instrumentzeile gelesene Quote-/Settlementwährung und
Metadatendigest, öffentliche Indexbewertung des deklarierten Budgets sowie
kanonischer Risiko-Numeraire. Der bestehende
[monetäre Identitätsparser](../../../src/ops/governed_productive_monetary_normalization_v1/instrument_monetary_identity_v1.py)
verwendet bei leerer Quote die Settlementangabe. Seine daraus gelesene USDC-
Einheit ist kein Operator für den ausdrücklich in USD gelieferten Core-Preis.
Auch ein Indexwert von exakt eins schließt diese Bedeutungslücke nicht.
Der Bericht bleibt `BLOCKED`, `authority=NONE`, ohne kanonische Sizingoperanden,
mit unbelegtem USD-/USDC-Operator und unbelegtem Accountsettlement.

Der vorhandene separate
[private USDC-Kostenpfad](../../../src/ops/portfolio_capital_reservation_budget_v1/entry_execution_cost_v1.py)
verlangt seine eigenen Konto-/Instrumentquellen und führt eine ursprüngliche
lineare Rechnung in deren Settlementeinheit aus. Er liefert keine allgemeine
USD-/USDC-Brücke für den BTC-Preis dieses Hosts. Die bestehenden finanziellen
Owner und ihre Rechenverfahren werden nicht durch neue Paritätsannahmen,
Schutzpreise oder ersatzweise rohe USD-Zahlen ergänzt.

## Noch offene autonome Demo-Verbindung

Die tatsächliche
[Netto-Gegenwechselbewertung](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_double_play_reversal_v1.py)
fordert einen ursprünglichen Host in LIVE oder intern simulierter Ausführung.
Die [ursprüngliche Buchungs-Recovery](../../../src/ops/portfolio_capital_reservation_budget_v1/live_net_reversal_booking_v1.py)
verlangt ausdrücklich eine LIVE-Ausführungsidentität und die passende monetäre
Quelle. Der [N1-Folgehost](../../../src/ops/n1_occupied_net_reversal_host_v2.py)
setzt auf der ursprünglichen send-/buchungsgebundenen N1-Spur fort. Diese
konkreten Owner dürfen nicht durch Umbenennen von TESTNET oder durch einen
simulierten Fill mit Demoetikett umgangen werden. Sie gehören zum geschützten
gekoppelten Pfad beziehungsweise dessen ursprünglichen Buchungsownern.

Damit bleiben zulässige ursprüngliche numerische USD-/USDC-Quellen,
kontogebundene Demo-Kapital-/Margin-/Kostenzulassung, der ursprüngliche
Demo-Submit-/Reconciliation-/Nettobuchungsanschluss und die dadurch berechtigte
Folgeepisode offen. Ein durchgängiger autonomer Demohandel ist nicht belegt.
Die gezielte Korrektur schließt die beschriebene veraltete Positionsaufnahme
und vervollständigt ihren lokalen Quellenreadback; sie erteilt keine neue
Handels-, Kapital-, Credential- oder Startfreigabe. Hostcrash, Stromausfall
und echter Betriebswiederanlauf benötigen weiterhin eigene Nachweise.
