---
docs_token: DOCS_TOKEN_CAPITAL_DECISION_ACQUISITION_FRESHNESS_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Kapital: Entscheidungsbindung und tatsächliche Aufnahmefrische

Basis ist 74714c81b539743b65c384118cbb6b1dd278559f nach PR 7185. Der
[JSON-Beleg](CAPITAL_DECISION_ACQUISITION_FRESHNESS_2026_11_07.json) bindet
Originalrevision, Quelldateien, Testauswahl und verbleibende Fehler.
Dies ist ein begrenzter Entwicklungsschritt aus Paket B/C des Außenringplans.

## Ursprung und Ursache

Die [normative 29P-Festlegung](../../../config/governance/od_29p_normative_pack_v1.json)
verlangt gemeinsame Entscheidungsidentität; DL-SEAL-02 trennt diese ausdrücklich
von Beobachtungs- und Frischeuhren. Die beabsichtigte Treasurydelegation derselben
ursprünglichen USDC-Margin wurde anhand der Original-PRs 6494, 6676 und 6827
rekonstruiert; siehe den [vorherigen Consumerbeleg](WP03_CURRENT_CONSUMER_PROOF_2026_11_07.md).

Im ursprünglichen Treasury-/E4-Join geht die Entscheidungsepoche verloren;
BASE, P01 und Eligibility übernehmen stattdessen die Aufnahmezeit. Der
CT-Validator verlangt zusätzlich Aufnahmezeit gleich Entscheidungsepoche.
Sechs der neun ersten gezielten Gegenfälle scheiterten vor der Änderung.

Der ursprüngliche produktive GET-Transport cached nach Endpoint. Common-Epoch
liest eine veränderliche Pfadmappe und setzt Aufnahme und Auswertung auf seinen
eigenen Paketzeitpunkt: Alter null. Die Carrierbildung kann danach weitere
Cacheobjekte oder GETs statt des bereits geprüften Snapshots verwenden.

## Änderung und Consumerwirkung

- Decision wird durch Treasury/E4 bis BASE weitergegeben. BASE, U04 und P01
  vergleichen gemeinsame Entscheidungsidentität und gemeinsamen Aufnahmebezug
  getrennt. Tatsächliches Alter und bestehende TTL werden durchgereicht.
- DECISION_BOUND_SNAPSHOT bindet Endpoint, Authentifizierungsanforderung und
  Entscheidung. Im S5-Host gehört die vorhandene Originalzyklus-ID zur Bindung;
  zwei verschiedene Zyklen derselben Uhrsekunde teilen keinen Cacheeintrag.
  Der ursprüngliche Enter-Consumer verlangt dieselbe Portfoliozyklus-ID.
  Die gemeinsame Entscheidungsepoche bleibt unverändert; die kollisionsfreie
  Kodierung vorhandener IDs ist kein neuer Zeit- oder 29P-Packowner.
  Allgemeiner Snapshotcache und dynamischer Marktcache behalten
  ihre bisherigen Zwecke. Der Transport ergänzt tatsächliche UTC-Aufnahmezeit
  und angeforderte Entscheidungskennung.
- Pretrade teilt doppelte Items derselben Fetchgruppe und prüft nach dem letzten
  GET sämtliche Aufnahmebelege. Fehlende, naive, fehlerhafte, zukünftige oder
  fremd gebundene Belege sperren. Bruchteile werden konservativ aufgerundet;
  die bestehende numerische TTL wird nicht erweitert.
- Common-Epoch und Carrier verwenden eigene Payloadkopien der gesammelten
  Originalresultate und denselben Quelltransport. Keine spätere Pfadmappe und
  kein zusätzlicher GET ersetzt einen bereits geprüften Snapshot. Decision,
  tatsächliche Aufnahme und Venue-uTime bleiben verschiedene Bezüge.
- Carrier und ursprünglicher Enter-Consumer prüfen das verstrichene Alter erneut.
  Ein Frischeablauf während der Carrierbildung liefert den vorgesehenen
  sperrenden Ownerfehler statt eines unerwarteten Hostfehlers.
  Eine Wiederholung derselben Aufnahme altert weiter. Gleiche Antwortbytes einer
  echten neuen Aufnahme dürfen denselben Kapitalbetrag liefern. Der BASE-Owner
  erhält aktuelle validierte Zeit-/Peerbezüge ohne zusätzlichen Kapitalbetrag;
  gleicher Fingerprint mit anderem Betrag und ältere Aufnahmen bleiben gesperrt.

Die endgültige Margin-minus-anwendbarem-P01-Formel, CT-Zahlenformel, vorgelagerte
Originalzulassungen sowie Sizing-, Budget-, Permit- und POST-Owner bleiben
zuständig. Keine Kapitalfreigabe und keine neue Mengenentscheidung.

## Prüfung und Grenzen

Die gezielte Auswahl aus zwölf Modulen besteht mit **151 PASS**: ursprünglicher
Transportcode mit vollständig lokalen Netzwerk-/Signierstubs, Common-Epoch,
Carrier, Treasury-/E4-/BASE-/P01-Consumer, Ownerprüfungen, monetäre Normalisierung,
GET-Budget und WP03-/WP04-Supervisorintegration. Daten sind synthetisch; kein
Venue- oder Credentialzugriff. WP03/WP04 halten nur ihren synthetischen
Entscheidungsstart fest; Aufnahme- und Auswertungsuhren laufen jetzt weiter.

Die Probe beobachtet neun Stub-GETs bei der ersten und weitere neun bei einer
neuen Entscheidung, auch bei gleichen Bytes. Wiederholung derselben Entscheidung
erhält Aufnahmezeit und Alter ohne neuen Request. Ein Gesamtdeckel von 16 sperrt
beim zweiten Snapshot exakt nach Versuch 16, ohne Reset.

Die breitere Abnahme bleibt insgesamt fehlgeschlagen. Alte Dokument-, Core-/
Cursor-, Identitäts- und Cap24-Probleme werden gegen aus der Basisrevision
geladene Originalmodule abgeglichen und im JSON einzeln ausgewiesen. Der
Originalvergleich ist ein isolierter Testprozess, kein vollständiger separater
Checkout. Der begrenzte PASS ersetzt diese offenen Verträge nicht.

**Ressourcenfolge:** Jede neue Pretradeentscheidung benötigt neun neue GETs.
Bestehende Gesamtrequest-, Retry-, Zeit- und Capabilitygrenzen bleiben bestehen;
der Gesamtdeckel kann früher sperren. Ein späterer natürlicher Dauerlauf benötigt
ein passend begründetes Ressourcenbudget. Dieser Patch erhöht es nicht.

Die Funding-/Margin-Herkunfts- und Nettingbeschreibung des generischen
Treasuryzwischenvertrags bleibt separate offene Facharbeit. Vollständiger
Prozesshost-Restore, alle Runtimeowner, autonomer Dauerbetrieb, N5 und bestätigte
Venueausführung sind nicht abgenommen. Freeze, geschützte Corequellen und
Aktivierung bleiben unverändert. Keine Gesamtfertigstellung des Außenrings.
