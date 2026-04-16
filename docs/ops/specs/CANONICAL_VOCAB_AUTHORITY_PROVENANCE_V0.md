# Canonical Vocabulary / Authority / Provenance v0

## 1) Ziel und Geltungsbereich

Dieses Dokument normiert den gemeinsamen Begriffsraum sowie Authority- und Provenance-Grenzen fuer Peak_Trade v0, damit Architektur-, Governance- und Ops-Aussagen konsistent bleiben.  
Es definiert Begriffe und Abgrenzungen normativ, ersetzt jedoch keine subsystem-spezifischen Detail-Spezifikationen.

## 2) Canonical Vocabulary

- **Universe Selection**: Auswahl des analysierten Marktuniversums.
- **Scan / Ranking / Top-N Promotion**: Pipeline zur Bewertung und Auswahl in eine priorisierte Top-N-Menge.
- **Doubleplay Core**: Kernlogik fuer Doubleplay-Signalerzeugung und -Bewertung.
- **Bull Specialist**: Strategiebaustein fuer bullische Marktlagen.
- **Bear Specialist**: Strategiebaustein fuer baerische Marktlagen.
- **Switch-Gate**: Gate-Mechanismus fuer Freigabe oder Blockade von Strategiewechseln.
- **Regime Detection**: Erkennung des Marktregimes.
- **Strategy Switching**: Entscheidung und Umschaltung zwischen Strategiezustaenden.
- **Strategy Embedding**: Einbettung einer Strategie in ein uebergeordnetes Systemkonzept.
- **Scope / Capital Envelope**: Kapital- und Einsatzrahmen auf Portfolio- oder Mandatsebene.
- **Risk / Exposure Caps**: Harte Risiko- und Expositionsobergrenzen.
- **Safety / Kill-Switches**: Sicherheitsmechanismen inklusive Not-Aus-Semantik.
- **Governance / Live Mode Gate**: Governance-Freigabelogik fuer Live-Betrieb.
- **Execution Pipeline**: Technische Ausfuehrungskette bis zur Order- bzw. Aktionsuebermittlung.
- **Business Decision Core**: Fachliche Entscheidungsinstanz fuer Handels- oder Allokationsentscheidungen.
- **AI Orchestrator**: Orchestrierung von Analyse-, Entscheidungs- und Kontrollschritten durch KI-Komponenten.
- **Replay / Provenance**: Reproduzierbarkeit, Herkunftsnachweis und Nachvollziehbarkeit von Daten und Entscheidungen.

## 3) Forbidden Equalities

Die folgenden Gleichsetzungen sind unzulaessig und duerfen in Specs, Runbooks und Reviews nicht als austauschbar behauptet werden:

- Regime Detection != Doubleplay
- Strategy Switching != Strategy Embedding
- Switch-Gate != finale Trade-Autoritaet
- Scope / Capital Envelope != Risk Limits
- Governance != Safety != Kill Switch
- Execution Pipeline != Business Decision Core
- AI Orchestration != Execution Authority
- lokale Replay-Faehigkeit != E2E-Provenance
- im Repo vorhanden != kanonisch integriert

## 4) Authority / Veto Precedence

- **Governance / Live Mode Gate** hat Veto-Prioritaet gegenueber Betriebsfreigaben.
- **Safety / Kill-Switches** haben Veto-Prioritaet gegenueber Ausfuehrungspfaden.
- **Risk / Exposure Caps** begrenzen zulaessige Entscheidungs- und Ausfuehrungsraeume.
- **Switch-Gate** wirkt als Umschalt-Gate, aber nicht als finale Trade-Autoritaet.
- **Business Decision Core** ist nicht identisch mit der **Execution Pipeline**; Entscheidung und Ausfuehrung bleiben getrennte Autoritaetsdomaenen.
- **AI Orchestrator** ist koordinierend, aber keine eigenstaendige Execution Authority.

## 5) Provenance Boundary Notes

- **nachweisbar**: Es existieren lokale Artefakte fuer Replay-/Provenance-Bausteine, die Teilaspekte der Nachvollziehbarkeit dokumentieren.
- **teilweise nachweisbar**: Mehrere Begriffe und Kontrollgrenzen sind in unterschiedlichen Dokumenten beschrieben, aber nicht durchgaengig als einheitlicher End-to-End-Strang belegt.
- **unklar**: Einzelne Authority-Uebergaenge zwischen Decision-, Gate- und Execution-Ebenen sind dokumentarisch nicht in jeder Richtung explizit verknuepft.
- **nicht als kanonischer End-to-End-Pfad nachgewiesen**: Eine vollstaendig kanonisch integrierte E2E-Kette aus Vocabulary, Authority und Provenance wird hier nicht behauptet.

## 6) Offene Luecken / nicht nachgewiesene Punkte

- Vollstaendige E2E-Provenance ueber alle Subsystem-Grenzen ist nicht als kanonisch abgeschlossen nachgewiesen.
- Die verbindliche Kopplung zwischen Strategy Switching, Switch-Gate und finaler Ausfuehrungsautoritaet ist als Boundary definiert, aber nicht als einheitlicher kanonischer Pfad belegt.
- Die Trennung von Governance, Safety und Kill-Switch ist normativ festgelegt; die durchgaengige Evidenzkette bleibt teilweise nachzuweisen.
- Vorhandene Repo-Artefakte werden nicht automatisch als kanonische Integration interpretiert.

## 7) Guardrails before runtime work

- Keine Runtime-Ableitung aus diesem Dokument ohne subsystem-spezifische Spezifikation.
- Keine Gleichsetzung der in Abschnitt 3 verbotenen Paare in Design-, Implementierungs- oder Review-Claims.
- Claims sind ausschliesslich in den Klassen **nachweisbar**, **teilweise nachweisbar**, **unklar** oder **nicht als kanonischer End-to-End-Pfad nachgewiesen** zu formulieren.
- Jede spaetere Runtime-Arbeit muss die Authority-Veto-Hierarchie sowie die Provenance-Boundaries explizit referenzieren.

## Verifizierte Cross-Links (knapp)

- [AI_AUTONOMY_GO_NO_GO_OVERVIEW](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)
- [GATES_UND_DATENFLUSS_UEBERSICHT](../GATES_UND_DATENFLUSS_UEBERSICHT.md)
- [PHASE_42_TOPN_PROMOTION](../../PHASE_42_TOPN_PROMOTION.md)
- [REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28](../../REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28.md)
- [double_play runbook](../runbooks/double_play.md)
- [DETERMINISTIC_REPLAY_PACK](../../execution/DETERMINISTIC_REPLAY_PACK.md)
- [AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2](../../governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md)
