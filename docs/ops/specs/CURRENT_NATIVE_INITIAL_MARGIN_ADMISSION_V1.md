---
docs_token: DOCS_TOKEN_CURRENT_NATIVE_INITIAL_MARGIN_ADMISSION_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Native Initialmargin an der ursprünglichen Entrymenge

BWP1-Fortschreibung vom 9. November 2026 auf
`1520d4ee74f2d117c1bf9a303de511e560d2b34c` (PR 7210).
Dies ist ein begrenzter zusätzlicher finanzieller Consumer, kein Abschluss von
[BWP1](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md).

## Ausgangslage und fachliche Herkunft

Der originale [29P-Producer](../../../src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_risk_capital_model_v1.py)
liefert USDC-Free-Margin abzüglich des bedingten P01. Die originale
[Geldnormalisierung](../../../src/ops/governed_productive_monetary_normalization_v1/normalize_v1.py)
unterstützt USDC und USDT mit beobachtetem Wechselkurs. Das beweist weder
USDT-Kollateral aus USDC-Bestand noch vollständige Margin-/Liquidationsdeckung.

Die älteren Canaryverträge und der
[Qty-one-Tierbinder](../../../src/ops/section_11_13_5_live_canary_minimum_exposure_v1/cover_usdc_current_public_tier_mmr_productive_evidence_v1.py)
trennen öffentliche MMR-Beobachtung, accountwirksame Margin und Liquidationspuffer.
Der historische [USD-/USDC-Abrechnungsbefund](../../../src/ops/section_11_13_5_live_canary_minimum_exposure_v1/z2ar_usd_usdc_account_settlement_offline_reproof_v1.py)
bleibt ausdrücklich unbelegt. Weder ein alter Tierwert für Menge eins noch der
OFFLINE_STUB-Wert 0,05 wird auf heutige Slots übertragen. USD-X-Perps erhalten
hier keine neue Umrechnung oder Zulassung.

Die am 9. November erneut gelesenen Obsidian-Notizen sind datierte Wissensquellen:
`00 Systemindex&#47;Semantik&#47;S01.md`, `S11.md`, `S12.md`,
`00 Systemindex&#47;Governance und Risk Sizing&#47;03 Kapital und Limitquellen.md` und
`Gesamtoffenlegung&#47;A Kausalfluss und Verantwortungsgrenzen.md` im Vault
`/Users/frnkhrz/PEAK_TRADE_SYSTEM_AKTUELL`. S01 verlangt Bedeutung, Einheit,
Identität und Informationszeit bis zum Consumer. S11 bindet Originalwriter und
Wiederaufnahme; S12 trennt Finanzadmission, Hold, Wahrheit, Veto und Capability.
Die Kausalnotiz verfolgt 29P → CRS → atomaren Hold → finale Menge → Execution.
Die Notiz über Kapitalquellen trennt den Notionaldeckel von einer Marginanforderung
und untersagt einen nochmaligen U04-Abzug. Ihre datierten Quellkörper ersetzen
keinen heutigen Laufzeitbeleg. Die S-Adressen sind analytische Sichten.

Aktuell abgeglichene Primärquellen:
[OKX API, Balance und Leverage](https://www.okx.com/docs-v5/en/),
[Futures Cross Margin](https://www.okx.com/help/iii-single-currency-margin-cross-margin-trading),
[EEA-X-Perp-Marginassets](https://www.okx.com/en-eu/help/okx-x-perps-eea-margin-assets).
Im Futures-Modus sind Free-Margin und Marginbedarf währungsbezogen. Der
beobachtete Hebel ist kein öffentlicher Maximalhebel. EEA-Multi-Asset-Kollateral
und gewählte Abrechnungswährung sind unterschiedliche Einstellungen; daraus
wird keine pauschale Übertragbarkeit auf den bestehenden acctLv=2-Pfad abgeleitet.

## Quellen, Rechnung und Zuständigkeit

Die neue [explizite Testpolicy](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V9.json)
(Revision 9, Schema v10) verlangt `require_native_initial_margin`. Die älteren
Policies behalten ihre Bytes, Schemata und Bedeutung. Ein bestehender Hold wird
weder beim Replay noch beim Cold-Read automatisch aufgewertet.

Der [neue Quellenbinder](../../../src/ops/portfolio_capital_reservation_budget_v1/native_initial_margin_v1.py)
verwendet die unveränderte finale native CRS-Menge, die bereits zugelassenen
Account-/Instrument-/Bookquellen und den exakten ursprünglichen 29P-Balancebezug.
Ein ausdrücklich übergebener GET-Port kann zusätzlich genau den gebundenen
Leverage-GET sammeln; der originale Balance-GET wird wiederverwendet. Ein
Collectoraufruf ist kein neuer Defaulttransport und erweitert keine Endpointrechte.
Der N1-Injektionsport reicht die Beobachtung an denselben Budgetowner weiter;
eine automatische produktive Collector-/Hostaktivierung wird nicht ergänzt.

Zugelassener Umfang: `acctLv=2`, Cross, Netmode, lineare SWAP/FUTURES mit gleicher
Preis-/Abrechnungswährung USDT oder USDC. Der Kontraktwert muss dabei die
Basiswährung tragen; ein Quote-Kontraktwert wird nicht zusätzlich mit einem
Basispreis multipliziert. Im unfiltrierten, authentifizierten
Balance-GET muss die tatsächlich benötigte `details[ccy].availEq` eindeutig und
nichtnegativ vorliegen. USDC-Basis, Account, Entscheidungsepoche, Cycle,
Aufnahmezeit und Bodyreferenz bleiben an die originale Kapitalbeobachtung gebunden.
`availBal`, `eq`, accountweites `availEq`, leere Felder und Bewertungs-FX sind keine
Ersatzquelle. Der Leverage-GET muss genau Instrument, Cross und Netseite treffen.
Fehlender, unendlicher, nichtpositiver oder veralteter Hebel sperrt den Entry.

Der geplante native Initialmarginbedarf ist native Menge × ctVal × Preis ÷
beobachteter Hebel. Verwendet wird der höhere Wert aus originalem Markbezug und
dem tatsächlich für diese Menge vorhandenen Openingbookwert. Die Quoteanteile
werden aus den bereits validierten Leveln exakt rational gerechnet; ein gerundeter
VWAP und eine periodische Division dürfen eine Unterdeckung nicht verschwinden
lassen. Das ist eine aktuelle Planprüfung, keine Zusicherung des späteren Fills.
Die bestehenden privaten und öffentlichen nativen Mengenlimits bleiben eigene
nachfolgende Zulassungen; öffentliche Tier-IMR/MMR wird hier nicht accountwirksam.

## Tatsächliche Consumer und Wiederaufnahme

Der ursprüngliche
[Budgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
prüft unter seinem vorhandenen Lock den Kandidaten zusammen mit den gespeicherten
Initialmarginverpflichtungen derselben Währung. Einzeln ausreichende Beobachtungen
dürfen nicht denselben begrenzten nativen Betrag mehrfach vergeben. Die
unterschiedlichen Währungen werden nicht addiert oder durch FX ersetzt.

Diese konservative lokale Zulassung gewährt keine Venue-Margin-Gutschrift aus
Fill, COMMITTED oder Unknown. Ein frischer Balancewert kann Venuebelastungen
bereits enthalten; mangels Zuordnungsnachweis werden lokale Verpflichtungen
trotzdem erhalten. Das kann früher sperren. Es ist kein erneuter U04-Abzug in
29P und keine zusätzliche Buchung oder Freigabe von USDC. Notional-, Kosten- und
Testverlustzustand bleiben beim vorhandenen Owner unverändert getrennt.

Originalbeobachtungen und reproduzierter Receipt werden gemeinsam mit dem Hold
als Sizingbinding v7 durch denselben SQLitewriter gespeichert. Cold-Read berechnet
den Receipt aus den Originalquellen erneut; ein neu berechneter äußerer Digest
reicht nicht aus. Offene Holds bleiben gebunden und der kalte Owner benötigt
weiterhin originale Accountrecovery. Replay verlangt exakt den ursprünglichen
Quellenkontext; die späte Entrybudgetprüfung kontrolliert die Aufnahmezeit erneut.
Aus dem Block folgt kein Positionsclose, Holdrelease oder Senderecht.

## Nachweisgrenze

Die verbundenen Prüfungen benutzen ausschließlich injizierte GETs, originale
N1-/Sizer-/Hold-/Envelopeconsumer und angewandte interne simulierte Fills.
LONG/SHORT, einzelne und gemeinsam ungedeckte native Beträge, fünf Holds,
Cold-Read, rehashte Manipulation, Replay und abgelaufene Pläne werden geprüft.
Der [Prüfbeleg](../evidence/CURRENT_NATIVE_INITIAL_MARGIN_ADMISSION_V1_2026-11-09.json)
bindet den endgültigen Quellstand und die erneut gelesenen Wissensquellen.

Die zusätzlich einbezogene alte Normalisierungssuite enthielt einen fehlerhaften
positiven Fixturepfad: ADA-Account-/Metadaten wurden mit einer ETH-Entscheidung
verbunden, obwohl der Test API3 benannte. Der originale Geldquellenbinder sperrt
diesen Identitätsbruch auch mit den vier unveränderten Ausgangsmodulen. Die
positive Probe erzeugt jetzt über den bestehenden Supervisor durchgehend einen
API3-Core und einen dazu passenden Account-/Metadaten-/Mengenpfad. Ein neuer
negativer Fall erhält ausdrücklich den Block der früheren ADA-/ETH-Mischung.
Der fehlgeschlagene erste Gesamtlauf bleibt separat erhalten.

Ein zweiter Gesamtlauf zeigte einmal einen ausbleibenden natürlichen SHORT-Entry
am vorhandenen Treasury-Handoff. Die beiden betroffenen SHORT-Fälle bestanden
isoliert; die Ursache dieses abweichenden Laufs ist damit nicht erklärt. Der
unveränderte Runtimepfad wird nicht abgeschwächt. Der SHORT-Prüfhelfer gibt bei
einem erneuten Ausfall jetzt die tatsächlichen finanziellen Reasoncodes aus.
Dieser Befund bleibt als offene Prüfunsicherheit dokumentiert, auch wenn ein
nachfolgender gemeinsamer Lauf besteht.

Offen bleiben insbesondere tatsächliche aktuelle Venuequellen, native physische
Kostendeckung einschließlich erneuerter Funding-/Closereserven, spätere Änderungen
des Marginbedarfs, accountwirksame Erhaltungsmargin/Liquidationskosten und deren
gemeinsame finanzielle Zulassung, USD-X-Perp-Abrechnung sowie der gesamte vorab
geprüfte Wirtschaftsrahmen. Die bisherige Kosten-/Reservenfortschreibung bleibt
erhalten. Keine Live-/Testnet-, Order- oder Kapitalbewegungsfreigabe; keine
Behauptung produktiver Betriebsbereitschaft oder eines abgeschlossenen BWP1.
