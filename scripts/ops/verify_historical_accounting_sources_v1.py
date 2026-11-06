"""Offline replay of historical accounting and source links; never today's equity.

Run with scripts/pt -m scripts.ops.verify_historical_accounting_sources_v1.
Prints a derived report. Does not write historical packs or exercise old GOs.
"""

from hashlib import sha256
import json
from pathlib import Path

from src.ops.okx_eea_private_account_state_runtime_v1.bills_observation_v1 import (
    audit_bill_pages_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_execute_v1 import (
    bind_accounting_evidence_from_persisted_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_adjudication_v1 import (
    adjudicate_live_accounting_reconstructed_v1,
)


def verify_historical_sources_v1(repo_root):
    root = Path(repo_root)
    sources = {}

    def read(relative):
        data = (root / relative).read_bytes()
        sources[relative] = sha256(data).hexdigest()
        return json.loads(data)

    evidence = bind_accounting_evidence_from_persisted_path_v1(repo_root=root)
    for key in ("fill_source_path", "position_source_path"):
        artifact = read(evidence[key])
        body = artifact["BODY_UTF8_EXACT"]
        if sha256(body.encode()).hexdigest() != artifact["BODY_SHA256"]:
            raise ValueError("HISTORICAL_RAW_BODY_DIGEST_MISMATCH")
        if str(artifact["HTTP_STATUS"]) != "200" or str(json.loads(body)["code"]) != "0":
            raise ValueError("HISTORICAL_RAW_RESPONSE_INVALID")
    trade = adjudicate_live_accounting_reconstructed_v1(accounting_evidence=evidence)
    if trade["LIVE_ACCOUNTING_RECONSTRUCTED"] is not True:
        raise ValueError("HISTORICAL_TRADE_PROOF_NOT_REPRODUCED")

    prefix = "evidence/ops/"
    candidate = read(
        prefix
        + "full_core_live_equity_stock_today_declaration_governed_binding_contract_wp1/2026-09-14T174507Z/system_bound_today_initial_stock_candidate_v1.json"
    )
    ratification = read(
        prefix
        + "full_core_live_equity_stock_today_initial_stock_ratification_wp1/2026-09-14T182100Z/today_initial_stock_owner_ratification_v1.json"
    )
    anchor = read(
        prefix
        + "full_core_live_equity_stock_today_initial_stock_anchor_wp1/2026-09-14T205500Z/today_initial_stock_anchor_v1.json"
    )
    membership = read(
        prefix
        + "full_core_live_equity_stock_today_initial_stock_kind_set_membership_wp1/2026-09-14T212500Z/today_initial_stock_kind_set_membership_v1.json"
    )
    for doc in (ratification, anchor, membership):
        for field in ("declaration_id", "equity_value", "as_of_time", "settlement_currency"):
            if doc[field] != candidate[field]:
                raise ValueError("HISTORICAL_ANCHOR_LINK_MISMATCH:" + field)
        if doc["candidate_digest"] != candidate["provenance_digest"]:
            raise ValueError("HISTORICAL_CANDIDATE_DIGEST_LINK_MISMATCH")
        if doc["ratification_status"] != "RATIFIED":
            raise ValueError("HISTORICAL_RATIFICATION_ABSENT")
    if any(
        doc["ratification_digest"] != ratification["ratification_digest"]
        for doc in (anchor, membership)
    ):
        raise ValueError("HISTORICAL_RATIFICATION_LINK_MISMATCH")
    if (
        membership["anchor_digest"] != anchor["anchor_digest"]
        or membership["anchor_id"] != anchor["anchor_id"]
    ):
        raise ValueError("HISTORICAL_ANCHOR_LINK_MISMATCH")
    if (
        anchor["initial_stock_anchor_status"] != "PRESENT"
        or membership["membership_status"] != "PRESENT"
    ):
        raise ValueError("HISTORICAL_ANCHOR_OR_MEMBERSHIP_ABSENT")

    pages = []
    base = prefix + "full_core_d6_path_b_package_1_observation_execution_v1/2026-09-13T182521Z/"
    for name in (
        "s4_account_bills_observation_v1.json",
        "s4_account_bills_archive_observation_v1.json",
    ):
        doc = read(base + name)
        if doc["http_status"] != "200" or doc["venue_code"] != "0":
            raise ValueError("HISTORICAL_BILL_RESPONSE_INVALID")
        pages.append(
            dict(
                account_binding_digest=doc["d4_identity_digest"],
                endpoint_path=doc["request_surface"].removeprefix("GET_"),
                rows=doc["rows"],
            )
        )
    bills = audit_bill_pages_v1(pages, account_binding_digest=pages[0]["account_binding_digest"])
    return {
        "schema": "peaktrade.historical_accounting_sources_replay.v1",
        "historical_trade_reproduced": trade["LIVE_ACCOUNTING_RECONSTRUCTED"],
        "historical_trade_result": trade["ACCOUNTING_RESULT"],
        "historical_restart_proven": trade["LIVE_RESTART_RECONSTRUCTED"],
        "historical_anchor_cross_artifact_links_match": True,
        "historical_anchor_as_of": candidate["as_of_time"],
        "historical_links_are_not_new_ratification": True,
        "historical_bills_audit": bills,
        "sources_sha256": sources,
        "today_equity_reconstructed": False,
        "historical_anchor_adopted_as_current": False,
        "account_identity_continuity_to_today_proven": False,
        "complete_stream_between_anchor_and_today_proven": False,
        "authority_effect": "NONE",
        "network_requests": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify_historical_sources_v1(Path(__file__).resolve().parents[2]), indent=2))
