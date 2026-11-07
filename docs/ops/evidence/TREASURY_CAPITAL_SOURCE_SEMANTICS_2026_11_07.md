---
docs_token: DOCS_TOKEN_TREASURY_CAPITAL_SOURCE_SEMANTICS_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Treasury: Fundingquelle und freie Margin beim richtigen Consumer

Basis: d2615064e7bf757999b6ea0884a51526d5114b6b nach PR 7187.
Der [JSON-Beleg](TREASURY_CAPITAL_SOURCE_SEMANTICS_2026_11_07.json) bindet
Originalquellen, Gegenprobe, Testauswahl und die verbleibenden Grenzen.
Dies setzt die [Kapitalaufnahmeprüfung](CAPITAL_DECISION_ACQUISITION_FRESHNESS_2026_11_07.md)
fort. Der eingefrorene Quellenbestand bleibt erhalten.

## Fachlicher Ursprung und tatsächlicher Rechenweg

Der ursprüngliche 29P-Margin-Producer aus
[PR 6494](https://github.com/rauterfrank-ui/Peak_Trade/pull/6494), Commit
62ac12d8167757aeaa145af03d0e972772385195, verwendet die USDC-Detailzeile des
Account-Balance-Reads. Sein Vertrag behandelt freie Margin als bereits um
Venuebelegung einschließlich offener Orders vermindert. Er zieht U04 deshalb
nicht erneut ab; P01 bleibt eine getrennte bedingte Reduktion.

Der spätere Treasury-/C08-BASE-Join aus
[PR 6676](https://github.com/rauterfrank-ui/Peak_Trade/pull/6676), Commit
90c1ffbcfe04482f1ed9c7ac424918dfea76e5c0, verarbeitet dagegen die Fundingquelle
mit dem bestehenden CT-Producer BASE − U04 − bedingtes P01.
[PR 6827](https://github.com/rauterfrank-ui/Peak_Trade/pull/6827), Commit
9647cb7bbab8137d1db1f47cf053ab6fcb7057a9, delegiert einen einzelnen Marginread
durch diesen Treasury-Pfad und danach wieder an den ursprünglichen 29P-Producer.
Der numerische CT-Ausgang war dort eine Voraussetzung, aber nicht der finale
Kapitalbetrag. Diese Quellen und Rollen sind unterschiedliche historische Varianten.

Die aktuelle [OKX-Felddokumentation](https://www.okx.com/docs-v5/en/)
unterscheidet Account-/Währungs-Equity, verfügbare Equity der Währung und
für Orders gebundene Margin. Das ist kein Nachweis, welche lokalen PeakTrade-Holds
bereits in einem konkreten Venuewert enthalten sind. Dafür fehlen hier die
gebundenen Reservierungs-/Orderidentitäten; die Repo-Owner bleiben maßgeblich.

Die Originalgegenprobe an der Basisrevision zeigt: Der Accountadapter hatte
kein Herkunftsfeld. Der gemeinsame BASE-Wrapper meldete funding_availBal_usdc
und bereits-netto-U04=false auch für diesen Marginread. Mit 1.000 USDC Margin
und einem nichtleeren U04-Witness von 15 USDC waren CT und der finale 29P-Pfad
erfolgreich; final kamen weiterhin 1.000 USDC an. Daraus folgt weder ein
belegter Verlust noch eine bewiesene Liveüberbelegung. Belegt sind die falsche
Quellenbezeichnung und die fehlende Wirkung dieses nichtleeren Witness am
finalen Consumer.

## Umsetzung und Wirkung

Beide Venueadapter setzen jetzt explizit eine unterschiedliche Treasuryquelle.
Der alte Treasury-DTO-Default bleibt zur Kompatibilität der historischen
Fundingaufrufer Funding; neue Marginbeobachtungen werden ausdrücklich markiert.
Der generische CT-BASE-Wrapper lehnt Margin- und unbekannte Quellen ab.
Auch der bestehende reine Funding-Beobachtungsreport weist fremde Quellen
vor Zugriff auf einen nicht anwendbaren CT-BASE ausdrücklich zurück.

Nach den unverändert erforderlichen Treasury-/E4-/C08-Prüfungen leitet der
produktive Host die Original-Marginbeobachtung an den bestehenden 29P-Producer.
Wert, Account, Akquisitionszeit, Fingerprint, Entscheidungsidentität, Alter und
TTL müssen zum Treasurytransport passen. Es entsteht kein CT-BASE und kein
zweiter numerischer Producer. Die vorhandenen P01-/U01-Owner liefern ihre
Facts mit dem ursprünglichen Entscheidungs- und Beobachtungsbezug.

Der Marginpfad prüft den expliziten U04-Witness weiter. Ist er nichtleer, bleibt
der Übergang mit U04_COVERAGE_UNRESOLVED_FOR_FREE_MARGIN gesperrt. Ohne
Coveragebeleg wird der Betrag weder ignoriert noch nochmals abgezogen.
Der Fundingpfad behält seinen CT-Abzug; die Testrechnung 100 − 15 liefert 85 USDC.
Margin mit gültigem leerem Witness liefert im Beispiel 1.000 USDC und durchläuft
danach die ursprünglichen CapitalAdmission-/Step-29P-Owner genau einmal.
Diagnostik meldet dafür free_margin_inputs_bound=true, CT=false und BASE-Zähler 0.

Der bisherige Prozessspeicher für Replay-/Fingerprintprüfung wird von beiden
Quellen getrennt nach Quelle und Account benutzt. Ein älterer Stand oder ein
veränderter Betrag unter demselben Fingerprint bleibt gesperrt. Alter und
Beobachtungszeit werden aus aktuellen validierten Inputs gebunden. Treasury
cached nur vollständig identische Inputs: gleiche Antwortbytes dürfen neue
Stale-/Transfer-Signale nicht verdecken. Der ursprüngliche Margin-Producer
weist nicht endliche Alters-/TTL-Werte nun ohne Decimal-Ausnahme zurück.

## Prüfung und offene Abnahme

158 ausgewählte Owner-/Integrationsfälle bestehen, darunter 32 neue gezielte
Fälle. Sie prüfen beide Quellen, tatsächliche Produceraufrufe, Step-29P-Wirkung,
fremde Inputs, falsche Nettingflags, ungültige Zeitangaben, Replay und die
bestehenden ENTER-/Portfolio-Budget-Pfade. Es werden ausschließlich lokale
synthetische Inputs und vorhandene Testdoubles verwendet.

Vier vorhandene Fälle wurden gesondert an der ursprünglichen Revision als
fehlerhaft reproduziert und bleiben offen. Drei erwarten den entfernten
Atlas-YAML-Katalog; ein weiterer behauptet die längst nicht mehr zutreffende
Abwesenheit von Treasury im Full-Core-Aufrufgraphen. Der volle erste
Ownerlauf hatte 90 PASS und drei FAIL; der ergänzte Lauf 157 PASS, einen FAIL
und drei abgewählte bekannte Fälle. Erst die explizit abgegrenzte Auswahl mit
vier abgewählten Fällen hat EXIT=0. Keine Tests oder fachlichen Gates wurden
zur Anpassung dieser alten Behauptungen abgeschwächt.

Die [bisherigen breiten 24 Fehler-/Setupfälle](CAPITAL_DECISION_ACQUISITION_FRESHNESS_2026_11_07.md)
werden hier nicht zu einer Gesamtfreigabe umgedeutet.
Insbesondere bleiben offen:

- Zuordnung lokaler RESERVED-/COMMITTED-Holds zu tatsächlicher Venuebelegung
  und deren jeweilige Kapitaldomäne. Der bestehende Portfolio-Budget-Owner
  zieht seine aktiven lokalen Holds weiterhin separat ab.
- Der feste leere U04-Default des bisherigen Full-Core-Helfers ist kein
  allgemeiner Beleg eines leeren Kontos oder fehlender lokaler Holds.
- Der Accountadapter setzt prior/cached aus derselben Momentaufnahme.
  RECONCILED ist hier deshalb keine unabhängige historische Einzahlungs-,
  Kapital- oder Buchhaltungsrekonstruktion.
- Dauerhafte Recovery dieses Prozessspeichers, vollständiger Hostrestore,
  echte Venue-/Serviceaufnahme, natürliche Dauerläufe und fünf aktive Slots.

Keine Order, kein echter Venue-GET, keine Credentialnutzung oder Betriebsaktivierung
wurde durchgeführt. Dies ist ein begrenzter Quell-/Consumer-Fix; U04-Gesamtsemantik,
physischer Wiederanlauf und Außenring-Gesamtabnahme bleiben eigenständige Arbeit.
