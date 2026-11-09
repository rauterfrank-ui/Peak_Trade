---
docs_token: DOCS_TOKEN_CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Bestehende Risiko- und Mengenconsumer im aktuellen N1

Ausgangspunkt ist Main `f7f6ad36e91016c93935d2f90ce9d9a125fa6000` mit der
[Quellenklärung zum fortgesetzten Handelskreis](CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_V1.md).
Dieser Schritt verändert keine Handelsformel, finanzielle Policy oder Freigabe.

Der [tatsächliche N1-Consumer](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
übergibt den ursprünglichen Coreentscheid an den
[29P-Join](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py).
Dieser trennt ENTER von HOLD und Positionsmanagement. ENTER benötigt den
gemeinsamen Reservierungsowner und gebundenen Slot. Die vorhandene
Kapitaladmission prüft den ursprünglichen, accountgebundenen Produceroutput;
ein beliebiges Venuefeld oder die Offline-Defaultequity ist kein Ersatz.

## Kapital, Währungen und endgültige Menge

Der [29P-Kapitalproducer](../../../src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_risk_capital_model_v1.py)
verwendet USDC-Free-Margin und den bedingten P01-Abzug. U04 wird nicht nochmals
abgezogen; die separate eq-Reconciliation ist kein alternativer Sizingwert.
Account-, Instrument-, Zeit- und Provenienzbindungen gehören zur Admission.
Der 29P-Join bindet außerdem den originalen MV2-Mark, die adverse Exitdistanz
des materialisierten Scopes und die daraus abgeleitete seitengerechte Stopbasis.
Das ist eine Sizingannahme über einen Exitabstand, keine garantierte Fillausführung.

Die [monetäre Normalisierung](../../../src/ops/governed_productive_monetary_normalization_v1/normalize_v1.py)
verbindet USDC-Kapital, native Preis-/Settlementwährung, FX-Quellen und
Kontraktmetadaten. Der [kanonische Sizer](../../../src/governance/capital_risk_sizing_v1.py)
begrenzt die Menge über Verlustbudget je Einheit, Kapital, Exposure und
Mengenbedingungen. Er rundet auf die Lotgröße ab und prüft das Ergebnis erneut.
Referenzpreis mal Kontraktmultiplikator mal Kontraktmenge ergibt das gebundene
Notional; Exitdistanz mal Multiplikator mal Menge ergibt den modellierten
Stopverlust in der normalisierten Kapitalrechnung.

Die [bestehende äußere Entrypolicy](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_entry_budget_policy_v1.py)
begrenzt die Sizingdecken nach der Coreentscheidung. Die aktuelle
[Policydatei](../../../config/ops/current_productive_entry_budget_policy_v1.json)
enthält 25 USDC je Entry und insgesamt reserviertes Notional, keine automatische
Erhöhung. Diese Grenze ist kein tägliches Verlustlimit und keine Erlaubnis,
die Coreentscheidung oder Account-Equity zu überschreiben.

Nutzerpräzisierung: Die 25 USDC dienen der anfänglichen Testphase am ersten Slot;
die spätere Dimensionierung soll vom tatsächlich verfügbaren Gesamtkapital
abhängen. Das ist kein dauerhaft gewünschtes 25-USDC-System. Die vorhandene
Kapitalrechnung ist bereits variabel: 29P produziert den aktuellen verfügbaren
Kapitalwert, der ursprüngliche Contextbuilder leitet seine Decken davon ab und
der Budgetowner zieht bestehende Verpflichtungen in die Mengenrechnung ein.
Die kleine äußere Policy begrenzt dieses Ergebnis zusätzlich. Mehr Kontokapital
hebt diese Startgrenze daher heute nicht automatisch an.

Ein späterer kapitalabhängiger Betrieb nutzt weiterhin diese ursprünglichen
Kapital-/Mengenowner. Frank entscheidet ausdrücklich, wann die Testphase endet
und dieser Übergang stattfinden soll. Ein automatischer Wechsel ist weder
definiert noch gewünscht und wird nicht als fehlende Automatisierung behandelt.
Das entspricht dem bestehenden Verbot automatischer Erhöhung und der Gültigkeit
bis zur ausdrücklichen Policyänderung. Diese Freigabeentscheidung bleibt von der
danach automatisch berechneten Menge getrennt.

Eine konkrete produktive prozentuale Slot-/Risikoallokation wird durch diese
Bindung noch nicht belegt. Dieser Prüfschritt aktiviert keinen Übergang und
ersetzt keine fehlende Allokationsregel durch eine frei gewählte Prozentzahl
oder durch Einsatz des gesamten Guthabens. Die spätere Freigabe braucht eine
konkrete prüfbare Policy; sie ist heute nicht erteilt.

Der [originale Budgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
serialisiert Sizingentscheidung, Anfragebindung und Reservation gemeinsam.
Replay verwendet die bereits gebundene Menge; ein geänderter Preis-/Policykontext
darf einen bestehenden Hold nicht heimlich neu dimensionieren. Der
[Ausführungslink](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py)
bindet diese Menge an den nativen Envelope und die Ausführungsidentität.
Unknown oder lokales Flat begründet keine Freigabe von Kapital.

Der [Venue-Mengenconsumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_n1_venue_quantity_limit_admission_v1.py)
prüft die endgültige native Kontraktmenge gegen die ursprünglichen öffentlichen
und privaten Quellen, seitengerecht und nach Orderart. Er schreibt keine
größere Ersatzmenge. Die späteren POST-Consumer lesen aktuelle Mengenquellen,
die geltende Entrypolicy und den ursprünglichen Budgetowner erneut.

## Was diese Risikoprüfung belegt und was offen bleibt

Die [produktive Kapitalcontext-Bindung](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_mv2_capital_context_rebind_v1.py)
setzt ihre Risiko-/Tagesbudgetdimensionen zunächst aus derselben typisierten
29P-Kapitalgröße. Die äußere Policy reduziert Kapital-/Notionaldecken. Daraus
folgt weder eine empirisch kalibrierte Verlustwahrscheinlichkeit noch ein aus
realisierten Tagesverlusten fortgeschriebener Drawdownvertrag. Der Contextbuilder
nutzt weiterhin Defaultzustände für nicht ausdrücklich übergebene Felder;
separate Owner-/Recoveryprüfungen dürfen deshalb nicht als diese Messung gelten.

Die [VaR-/Stress-/Liquiditätsadapter](../../../src/risk/decision_bound_model_adapters_v1.py)
verlangen ausdrücklich `EXPLICIT_OFFLINE_TEST_POLICY` und
`INTERNAL_SIMULATED_EXECUTION`. Ihre eigene Schnittstelle bindet unter anderem
Returnperiode, Horizont, Kenntniszeit, Preis-/FX-Herkunft, Orderbuch, ADV,
Portfolio und ursprüngliche Holds. Der aktuelle N1 übergibt dem 29P-Join kein
`restrictive_risk`-Objekt. Die Offlineprüfung belegt Modellrechnung und Veto am
simulierten Pfad; sie wird nicht zur produktiven Risikodefinition umbenannt.

Bestehende Kapital-, Stop-, Mengen-, Reservation- und Venueprüfungen sind somit
tatsächlich angeschlossen. Produktive statistische Verlust-/Survivaldefinition,
deren etwaige Notwendigkeit und Kalibrierung sowie unbegrenzter autonomer Betrieb
bleiben eigene offene Fragen. Die Rankingfristen werden nicht zu einem
Risikohorizont erklärt. Es werden keine zusätzlichen pauschalen Gates eingeführt.

Die [gemeinsame Prüfung](../evidence/CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_2026_11_09.md)
enthält eine zusätzliche Beobachtung am tatsächlichen N1 für LONG und SHORT:
originaler Entscheid, Risikomengenrechnung, gespeicherte Reservation und finaler
Envelope stimmen überein. Alle verwendeten Markt-/Accountports sind synthetisch;
Netzwerkverbindungen sind in dieser Gegenprobe gesperrt. Es entstehen keine
Orders oder produktiven Rechte.
