"""Frozen Execution handoff consumed by three guardian tracks. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Any, Final

EXPECTED_BASELINE_SHA: Final = "5b90ede63db49ad0e252b2664c77a926a985656f"
EXPECTED_BASELINE_TREE: Final = "d9be174f6e3ec79f642aa5fea3ddd59425ea11d7"

REGISTRY_ID: Final = "EXECUTION_M15_BOUNDARY_HANDOFF"
COVERAGE: Final = "PARTIAL"
UNIVERSE_MEMBERSHIP: Final = "NOT_RATIFIED"
COMPLETENESS_CLAIMED: Final = False
DOUBLE_PLAY_FULL_OWNER_LOCK: Final = "LEVEL_3"

WORKFLOW_PACKAGE_ID: Final = "GHOSV_BOUNDED_CONTEXT_V1"
GUARDIAN_GHOSV_IDENTITY: Final = "EXECUTION_GHOSV"
WORKFLOW_EQUALS_GUARDIAN: Final = False

POST_ALLOWED: Final = False
EXTERNAL_EFFECT_AUTHORIZED: Final = False

BOUNDARY_CONTRACT_TOKENS: Final = (
    ("COVERAGE", "EXECUTION_OUTER_BOUNDARY_COVERAGE=PARTIAL"),
    ("UNIVERSE_MEMBERSHIP", "EXECUTION_UNIVERSE_MEMBERSHIP=NOT_RATIFIED"),
    ("OWNER_LOCK", "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3"),
    ("POST_ALLOWED", "POST_ALLOWED=false"),
    ("EXTERNAL_EFFECT", "EXTERNAL_EFFECT_AUTHORIZED=false"),
)
FORBIDDEN_CONTRACT_TOKENS: Final = (
    "EXECUTION_OUTER_BOUNDARY_COVERAGE=COMPLETE",
    "EXECUTION_UNIVERSE_MEMBERSHIP=RATIFIED",
    "POST_ALLOWED=true",
    "EXTERNAL_EFFECT_AUTHORIZED=true",
)
REQUIREMENT_IDS: Final = ("EX-COV", "EX-MEM", "EX-LOCK", "EX-POST", "EX-EXT")
STALE_FOREIGN_SNAPSHOT_ID: Final = "58f855c9c9818a78849859613c33148e"
CURRENT_GRAPH_SNAPSHOT_MATERIALIZED: Final = False

TOOL_IDENTITIES: Final = (
    "EXECUTION_GHV",
    "EXECUTION_CURRENT_CAUSAL_GRAPH",
    "EXECUTION_GHOSV",
)

FORBIDDEN_OUTPUT_KEYS: Final = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized"}
)

EDGE_CLASSES: Final = (
    "CONFIRMED",
    "CONFIRMED_EXTERNAL",
    "CONTRACT_ONLY",
    "NOT_CONNECTED_WITHIN_CHECKED_SCOPE",
    "UNRESOLVED",
)
EDGE_CLASS_COUNTS: Final = {
    "CONFIRMED": 4,
    "CONFIRMED_EXTERNAL": 11,
    "CONTRACT_ONLY": 3,
    "NOT_CONNECTED_WITHIN_CHECKED_SCOPE": 3,
    "UNRESOLVED": 2,
}

TRAVERSABLE_CLASSES: Final = frozenset({"CONFIRMED", "CONFIRMED_EXTERNAL"})
INTERNAL_REGISTRY_LABELS: Final = frozenset({"Compose", "Halt", "Translation"})
PROSE_ONLY_INTERNAL_LABEL: Final = "send-capable Port"
INTERNAL_PROSE_ALIAS: Final = {"Translation": "Venue-Translation"}

OPEN_TASKS: Final[tuple[dict[str, str], ...]] = (
    {
        "TASK_ID": "EX-OPEN-01",
        "STATUS": "OPEN",
        "TEXT": (
            "Governed-Cycle-Reachability: ob der Orchestrator-Körper das "
            "bereits bestätigte Wiring aufruft."
        ),
    },
    {
        "TASK_ID": "EX-OPEN-02",
        "STATUS": "OPEN",
        "TEXT": (
            "Accounting und Portfolio: ob eine Übergabe unter einem anderen "
            "Typnamen als CanonicalExecutionEventV1 besteht."
        ),
    },
    {
        "TASK_ID": "EX-OPEN-03",
        "STATUS": "OPEN",
        "TEXT": "Transitive N5-Verbindungen jenseits der zwei bereits gelesenen Dateien.",
    },
    {
        "TASK_ID": "EX-OPEN-04",
        "STATUS": "OPEN",
        "TEXT": (
            "Produktive Aktivierung der Post-Submit-Wiring- und DW-Schnittstellen. "
            "Default DISABLED bleibt der bisherige Beleg."
        ),
    },
    {
        "TASK_ID": "EX-OPEN-05",
        "STATUS": "OPEN",
        "TEXT": (
            "Vollständige interne Execution-Mitgliedschaft. Sie ist nicht ratifiziert "
            "und wird hier nicht ergänzt."
        ),
    },
)

_EDGE_ROWS: Final[tuple[tuple[str, str, str, str, str, str, str, str], ...]] = (
    (
        "EX-01",
        "Master-V2-Replay",
        "Compose",
        "INBOUND",
        "Replay-PASS, decision_outcome",
        "integriertes Replay",
        "CONFIRMED_EXTERNAL",
        "Aufrufer außerhalb des Offline-Pfads nicht neu gelesen",
    ),
    (
        "EX-02",
        "CanonicalOrderIntentV1",
        "Compose",
        "INBOUND",
        "MISSING_29Q",
        "canonical_order_intent_owner_v1",
        "CONFIRMED_EXTERNAL",
        "PLAN_ONLY ist keine POST-Freigabe",
    ),
    (
        "EX-03",
        "Frozen Pretrade",
        "Offline-Pfad",
        "INBOUND",
        "pretrade_valid",
        "VENUE_PRETRADE_GATES",
        "CONFIRMED_EXTERNAL",
        "keine",
    ),
    (
        "EX-04",
        "Capital-Admission",
        "Halt",
        "INBOUND",
        "keine Capital-Authority",
        "capital_risk_admissibility_owner_v1",
        "CONFIRMED_EXTERNAL",
        "tiefere Joins nicht als Writer gelesen",
    ),
    (
        "EX-05",
        "Cap-7.2-Host-Join",
        "Halt",
        "INBOUND",
        "nicht execution-eligible",
        "stateful_no_order_host_join_v1",
        "CONFIRMED_EXTERNAL",
        "keine",
    ),
    (
        "EX-06",
        "path_mode",
        "Admission",
        "INBOUND",
        "Live oder Offline-Proof",
        "CURRENT_PRODUCTIVE_EXECUTION_MODE",
        "CONFIRMED_EXTERNAL",
        "keine Trading-Entscheidung",
    ),
    (
        "EX-07",
        "td_mode",
        "Translation",
        "INBOUND",
        "Token cross",
        "CURRENT_PRODUCTIVE_VENUE_EXECUTION_POLICY",
        "CONFIRMED_EXTERNAL",
        "keine",
    ),
    (
        "EX-08",
        "Kill-Switch-Status",
        "Halt",
        "INBOUND",
        "fremder Safety-Input",
        "Replay-Safety-Kernel",
        "CONFIRMED_EXTERNAL",
        "keine",
    ),
    (
        "EX-09",
        "owner_go",
        "Halt",
        "INBOUND",
        "MISSING_OWNER_GO",
        "Governance",
        "CONFIRMED_EXTERNAL",
        "kein POST-GO",
    ),
    (
        "EX-10",
        "Credential-Handle",
        "Wire",
        "OUTBOUND, verweigert",
        "External Effect nicht autorisiert",
        "Credential-Grenze",
        "CONFIRMED_EXTERNAL",
        "kein Keychain-Read in den gelesenen Zeilen",
    ),
    (
        "EX-11",
        "Halt",
        "Venue",
        "OUTBOUND",
        "HARD_STOP_BEFORE_WIRE",
        "LIVE_EXECUTION_BOUNDARY",
        "CONFIRMED",
        "Reachability nicht belegt",
    ),
    (
        "EX-12",
        "Cycle-Resultat",
        "Post-Submit-Wiring",
        "INBOUND",
        "nur PRE_EXTERNAL_EFFECT",
        "Cycle-Orchestrator",
        "CONFIRMED",
        "Aufruf aus dem Orchestrator-Körper nicht geprüft",
    ),
    (
        "EX-13",
        "injiziertes Join",
        "Reconciliation-Orchestrator",
        "FORWARD",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        "Wiring konsumiert",
        "CONFIRMED",
        "produktiver Aufrufer nicht geprüft",
    ),
    (
        "EX-14",
        "übergebenes Join",
        "DW-Wiring",
        "FORWARD nur wenn nicht DISABLED",
        "Default DISABLED",
        "DW-Wiring",
        "CONFIRMED",
        "produktive Aktivierung nicht belegt",
    ),
    (
        "EX-15",
        "Reconciliation-Entscheidung",
        "G004-Store",
        "OUTBOUND nur bei Flag",
        "G004",
        "Reconciliation-Disposition",
        "CONFIRMED_EXTERNAL",
        "Default false",
    ),
    (
        "EX-16",
        "Cap-11.1-AFTER",
        "Accounting",
        "gezeichnet",
        "nicht aktiviert",
        "canonical_futures_accounting",
        "CONTRACT_ONLY",
        "Körper nicht gelesen",
    ),
    (
        "EX-17",
        "Cap-11.1-AFTER",
        "Portfolio",
        "gezeichnet",
        "nicht aktiviert",
        "canonical_portfolio_authority",
        "CONTRACT_ONLY",
        "Körper nicht gelesen",
    ),
    (
        "EX-18",
        "Cap-11.1-AFTER",
        "Reconciliation/Evidence aus dem Halt",
        "gezeichnet",
        "Nachbereich",
        "keine Execution-Owner-Zeile",
        "CONTRACT_ONLY",
        "verschieden vom Post-Submit-Orchestrator",
    ),
    (
        "EX-19",
        "CanonicalExecutionEventV1",
        "Accounting und Portfolio",
        "keine Übergabe",
        "Schema-Modul",
        "Schema-Owner",
        "NOT_CONNECTED_WITHIN_CHECKED_SCOPE",
        "anderer Typname nicht inventarisiert",
    ),
    (
        "EX-20",
        "Envelope-Seam",
        "Orchestrator",
        "keine Übergabe",
        "Join bleibt im Seam-Resultat",
        "Send-Seam",
        "NOT_CONNECTED_WITHIN_CHECKED_SCOPE",
        "keine",
    ),
    (
        "EX-21",
        "N5-Full-Autonomy",
        "Halt",
        "keine direkte Bindung",
        "JOIN_EXECUTION_AUTHORITY=false",
        "N5-Orchestrator",
        "NOT_CONNECTED_WITHIN_CHECKED_SCOPE",
        "transitive Zyklen offen",
    ),
    (
        "EX-22",
        "Token-FULL_AUTONOMOUS_STACK",
        "Execution",
        "keine Identität",
        "Token fehlt",
        "nicht belegt",
        "UNRESOLVED",
        "nicht aus N5 ableitbar",
    ),
    (
        "EX-23",
        "Cycle-Orchestrator-Körper",
        "Wiring",
        "Aufruf nicht gelesen",
        "Interface bleibt bestätigt",
        "Orchestrator",
        "UNRESOLVED",
        "Reachability-Lücke, keine neue Excavation",
    ),
)


def frozen_edges_v1() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in _EDGE_ROWS:
        rows.append(
            {
                "EDGE_ID": row[0],
                "SOURCE": row[1],
                "TARGET": row[2],
                "DIRECTION": row[3],
                "CONTRACT": row[4],
                "DOMAIN_OWNER": row[5],
                "EDGE_CLASS": row[6],
                "UNCERTAINTY": row[7],
            }
        )
    return rows


def frozen_open_tasks_v1() -> list[dict[str, str]]:
    return [dict(row) for row in OPEN_TASKS]


def frozen_registry_document_v1() -> dict[str, Any]:
    return {
        "REGISTRY_ID": REGISTRY_ID,
        "COVERAGE": COVERAGE,
        "UNIVERSE_MEMBERSHIP": UNIVERSE_MEMBERSHIP,
        "COMPLETENESS_CLAIMED": COMPLETENESS_CLAIMED,
        "EDGES": frozen_edges_v1(),
        "OPEN_TASKS": frozen_open_tasks_v1(),
    }
