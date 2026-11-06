"""Static contract: OKX public PT1M raw-bytes exclusive-tip proof cybersecurity mirror."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE = (
    REPO_ROOT
    / "docs"
    / "ops"
    / (
        "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
        "OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_CYBERSECURITY_MIRROR_V1.md"
    )
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_NOTE",
    "CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF",
    "DECISION_ID=DEC_RAW_INPUT_PACK_MATERIALIZATION",
    "DECISION_STATUS=RATIFIED",
    "OWNER_GO=OWNER_STA_SURFACE_B_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_V1",
    "OWNER_GO_BASE_SHA=54642d8250bb59ba58d98da7ce7b6ab52558e43b",
    "OWNER_VALUE=AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION",
    "AUTHORIZED_NETWORK_FETCH=true",
    "DOWNLOAD_OR_NETWORK_FETCH=true",
    "PROOF_CONTRACT_READY=true",
    "STA_EXTERNAL_INPUT_FIELDS_READY=true",
    "OWNER_PARTITION_SELECTION_READY=false",
    "NUMERIC_PROOFS_RESOLVED=true",
    "PACK_MATERIALIZATION=false",
    "RAW_INPUT_PACK_CREATED=false",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "ORDERS_TESTNET_LIVE=false",
    "INVENTED_VALUES=false",
    "WALLCLOCK_AS_DATA_AUTHORITY=false",
    "RUNTIME_AUTHORIZATION_EFFECT=NONE",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "PACK_MATERIALIZATION=true",
    "RAW_INPUT_PACK_CREATED=true",
    "CAMPAIGN_START=true",
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "OWNER_PARTITION_SELECTION_READY=true",
    "ORDERS_TESTNET_LIVE=true",
    "WALLCLOCK_AS_DATA_AUTHORITY=true",
)


def test_tip_proof_cybersecurity_mirror_exists_v1() -> None:
    assert NOTE.is_file()


def test_tip_proof_cybersecurity_mirror_markers_v1() -> None:
    text = NOTE.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_security_notes_mirrors_tip_proof_surface_v1() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    assert (
        "STAGE2_SURFACE_B_OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_V1"
    ) in notes
    assert (
        "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
        "OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_V1.md"
    ) in notes
    assert "54642d8250bb59ba58d98da7ce7b6ab52558e43b" in notes
    assert "last_finalized_common_bucket_open_event_time_epoch_s+60" in notes
