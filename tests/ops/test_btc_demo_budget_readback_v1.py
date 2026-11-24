"""Read actual original budget rows without modifying the sealed writer or seal."""

import hashlib
import json
from pathlib import Path
from runpy import run_path
import sqlite3
import subprocess

import pytest

from src.ops.btc_demo_budget_reconciliation_host_v1 import BtcDemoBudgetReconciliationHostV1
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    DurableBudgetStoreError,
    digest,
)
from tests.ops.test_btc_demo_budget_reconciliation_host_v1 import ACCOUNT, BOUND, owner_host

ROOT = Path(__file__).resolve().parents[2]
BASE = "f52d52a6e0cd47cbec048adba9e9ff8283f9f693"


def test_consumer_reads_original_committed_row_without_a_writer_transition(tmp_path):
    host, _ = owner_host(tmp_path)
    try:
        before = host.owner.risk_snapshot_v1()
        database = host.root / "testnet-state/budget-owner/owner/reservations.sqlite3"
        checksum = hashlib.sha256(database.read_bytes()).hexdigest()
        sequence, head = host.budget_revision_ref_v1()
        assert head == before["durable_head"]
        original = host.owner._store.read_revision_v1(sequence, head)
        assert original["sequence"] == sequence and original["digest"] == head
        assert host.budget_revision_ref_v1() == (sequence, head)
        assert host.owner.risk_snapshot_v1() == before
        assert hashlib.sha256(database.read_bytes()).hexdigest() == checksum
    finally:
        host.owner.close()


def test_sealed_budget_store_policy_and_enforcement_remain_original():
    for path in (
        "src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py",
        "src/ops/portfolio_capital_reservation_budget_v1/durable_store_v1.py",
        "docs/system_atlas/policy_projection.py",
        "docs/ops/specs/N1_DOUBLE_PLAY_RUNTIME_SEAL_V1.json",
        "scripts/ops/check_n1_double_play_runtime_seal_v1.py",
        ".github/workflows/map_currency_gate_v1.yml",
    ):
        # Slot 4 updated the separate rotation projection on main in 597b3b0e0.
        revision = (
            "597b3b0e0cf27d73e3b0eb704557fa7d41f57b43"
            if path == "docs/system_atlas/policy_projection.py"
            else BASE
        )
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", revision + ":" + path], cwd=ROOT
        )


def test_original_policy_bundle_accepts_the_unchanged_original_budget_source():
    policy = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
    law = json.loads((ROOT / policy["LAW"]).read_bytes())
    assert policy["validate_policy_inventory"](ROOT, law)["runtime_effect_inferred"] is False


@pytest.mark.parametrize("fault", ["payload", "digest", "account_metadata", "new_disk_head"])
def test_original_reader_refuses_corrupt_or_foreign_actual_journal(tmp_path, fault):
    host, _ = owner_host(tmp_path)
    try:
        sequence, head = host.budget_revision_ref_v1()
        database = host.root / "testnet-state/budget-owner/owner/reservations.sqlite3"
        with sqlite3.connect(database) as db:
            if fault == "payload":
                db.execute("UPDATE states SET payload = '{}' WHERE seq = ?", (sequence,))
            elif fault == "digest":
                db.execute("UPDATE states SET digest = ? WHERE seq = ?", ("0" * 64, sequence))
            elif fault == "account_metadata":
                db.execute("UPDATE metadata SET account = ?", ("foreign-account",))
            else:
                payload = json.loads(
                    db.execute("SELECT payload FROM states WHERE seq = ?", (sequence,)).fetchone()[
                        0
                    ]
                )
                checksum = digest({"seq": sequence + 1, "previous": head, "state": payload})
                db.execute(
                    "INSERT INTO states(seq, previous, digest, payload) VALUES (?, ?, ?, ?)",
                    (sequence + 1, head, checksum, json.dumps(payload)),
                )
        before = hashlib.sha256(database.read_bytes()).hexdigest()
        with pytest.raises(DurableBudgetStoreError):
            host.budget_revision_ref_v1()
        assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    finally:
        host.owner.close()


def test_memory_only_owner_cannot_supply_the_durable_demo_scope(tmp_path):
    host, _ = owner_host(tmp_path)
    memory = Owner()
    try:
        with pytest.raises(ValueError, match="DURABLE_BUDGET_SCOPE_REQUIRED"):
            BtcDemoBudgetReconciliationHostV1(
                owner=memory, bound=BOUND, account=ACCOUNT, testnet_root=host.root
            )
    finally:
        memory.close()
        host.owner.close()
