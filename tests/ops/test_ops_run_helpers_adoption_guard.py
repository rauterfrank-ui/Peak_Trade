from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "scripts" / "ops"

TARGETS = [
    OPS / "pr_inventory_full.sh",
    OPS / "label_merge_log_prs.sh",
]


def test_ops_scripts_reference_run_helpers():
    missing = []
    for p in TARGETS:
        if not p.exists():
            missing.append(f"missing file: {p}")
            continue
        txt = p.read_text(encoding="utf-8")
        if "run_helpers.sh" not in txt:
            missing.append(f"missing run_helpers reference: {p}")
    assert not missing, "Adoption guard failed:\n" + "\n".join(missing)
