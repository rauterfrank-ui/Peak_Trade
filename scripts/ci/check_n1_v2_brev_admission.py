#!/usr/bin/env python3
"""Check the BREV V2 source admission using immutable Git objects only."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys


CHECKER = "scripts/ci/check_n1_v2_brev_admission.py"
WORKFLOW = ".github/workflows/n1-v2-brev-admission.yml"
POLICY = "docs/ops/specs/N1_V2_BREV_SOURCE_ADMISSION.json"
EVIDENCE = "docs/ops/evidence/N1_V2_BREV_OFFLINE_RECOVERY.json"
SPEC = "docs/ops/specs/N1_V2_BREV_SOURCE_ADMISSION.md"
TEST = "tests/governance/test_n1_v2_brev_source_admission.py"
CONTROL_PATHS = {CHECKER, WORKFLOW, POLICY, EVIDENCE, SPEC, TEST}
ATLAS = "docs/system_atlas/source/development-binding-v1.json"
IMPACT = "config/governance/current_law_impact_map_v1/impact_adjudication_v1.json"
REGISTRATION_RECORDS = {
    "config/ci/required_status_checks.json",
    "docs/ops/specs/branch_ruleset_enforcement_api_evidence_after_v1.json",
    "docs/system_atlas/current_atlas.py",
}
V1_MANIFEST = "docs/ops/specs/N1_DOUBLE_PLAY_RUNTIME_SEAL_V1.json"
V2_ROOT = "src/ops/n1_occupied_scope_recovery_v2"
V2_PATHS = {f"{V2_ROOT}/{name}" for name in ("cap24.py", "checkpoint.py", "runtime.py")}
CONTEXT = "n1-v2-brev-admission"


class AdmissionError(ValueError):
    """The reviewed source or its proof is not bound to this candidate."""


def _require(condition, reason):
    if not condition:
        raise AdmissionError(reason)


def _git(root, *args):
    return subprocess.check_output(["git", "--literal-pathspecs", *args], cwd=root)


def _tree(root, rev, *paths):
    entries = {}
    for entry in _git(root, "ls-tree", "-rz", "--full-tree", rev, "--", *paths).split(b"\0"):
        if entry:
            meta, path = entry.split(b"\t", 1)
            entries[path.decode()] = tuple(meta.decode().split())
    return entries


def _blob(root, rev, path):
    entry = _tree(root, rev, path).get(path)
    _require(entry is not None and entry[:2] == ("100644", "blob"), f"REGULAR_FILE_REQUIRED:{path}")
    return _git(root, "cat-file", "blob", entry[2])


def _diff(root, base, candidate):
    raw = _git(root, "diff", "--name-only", "--no-renames", "-z", base, candidate, "--")
    return set(raw.decode().split("\0")) - {""}


def _sha(value):
    return sha256(value).hexdigest()


def _load_policy(root, trusted):
    policy = json.loads(_blob(root, trusted, POLICY))
    _require(
        policy["schema"] == "peaktrade.n1_v2_brev_source_admission.v1"
        and policy["required_context"] == CONTEXT
        and policy["runtime_authorization_effect"] == "NONE"
        and set(policy["source_sha256"]) == V2_PATHS
        and all(re.fullmatch(r"[0-9a-f]{64}", value) for value in policy["source_sha256"].values())
        and re.fullmatch(r"[0-9a-f]{40}", policy["reviewed_base"]),
        "POLICY_BINDING_INVALID",
    )
    raw = _blob(root, trusted, EVIDENCE)
    _require(_sha(raw) == policy["evidence_sha256"], "OFFLINE_EVIDENCE_DIGEST_MISMATCH")
    proof = json.loads(raw)
    _require(
        proof["schema"] == "peaktrade.n1_v2_brev_offline_recovery.v1"
        and re.fullmatch(r"[0-9a-f]{64}", proof["original_report_sha256"])
        and proof["source_sha256"] == policy["source_sha256"]
        and proof["repository_base"] == policy["reviewed_base"]
        and proof["instrument"] == "BREV-USDT-SWAP"
        and proof["lane"] == "LANE_1"
        and proof["process_exit"] == "SIGKILL"
        and proof["system_reboot_performed"] is False
        and type(proof["real_gets"]) is int
        and proof["real_gets"] == 0
        and type(proof["real_posts"]) is int
        and proof["real_posts"] == 0
        and proof["start_authorized"] is False
        and proof["v1_seal"] == {"content": "PASS", "base_policy": "PASS"},
        "OFFLINE_EVIDENCE_BINDING_INVALID",
    )
    cases = proof["cases"]
    positive = {"same-boot", "managed-other-boot"}
    negative = {
        "attempt-present",
        "changed-cursor",
        "changed-hold-proof",
        "changed-scope",
        "missing-v2-checkpoint",
        "plain-other-boot",
        "replaced-store",
        "truncated-checkpoint",
    }
    _require(set(cases) == positive | negative, "OFFLINE_EVIDENCE_CASE_SET_INVALID")
    for name, case in cases.items():
        _require(case["new_process"] is True, f"NEW_PROCESS_UNPROVEN:{name}")
        if name in positive:
            _require(
                case["result"] == "RESTARTED_AT_OCCUPIED_WAIT"
                and case["native_resume_state"] == "WAITING_FOR_NEXT_C1"
                and case["same_budget_db_and_history"] is True
                and case["same_reservation"] is True
                and case["byte_identical_cursor"] is True
                and case["independent_managed_checkpoint"] is (name == "managed-other-boot")
                and case["boot_identity_changed_in_simulation"] is (name == "managed-other-boot"),
                f"ORIGINAL_WAIT_UNPROVEN:{name}",
            )
        else:
            _require(case["result"] == "BLOCKED_BEFORE_PORT_OPEN", f"FAULT_NOT_FENCED:{name}")
    return policy


def _check_atlas(root, base, candidate, hashes):
    approved = json.loads(_blob(root, base, ATLAS))
    new = json.loads(_blob(root, candidate, ATLAS))
    rows = new.pop("files")
    old_rows = approved.pop("files")
    expected = [
        *old_rows,
        *(
            {"path": path, "before_sha256": None, "sha256": digest}
            for path, digest in hashes.items()
        ),
    ]
    _require(
        new == approved
        and sorted(rows, key=lambda row: row["path"])
        == sorted(expected, key=lambda row: row["path"]),
        "UNREVIEWED_ATLAS_DELTA",
    )
    before = json.loads(_blob(root, base, IMPACT))
    after = json.loads(_blob(root, candidate, IMPACT))
    expected_paths = sorted(set(before["changed_paths"]) | V2_PATHS)
    before["changed_paths"] = expected_paths
    before["changed_paths_sha256"] = _sha("\n".join(expected_paths).encode())
    _require(after == before, "UNREVIEWED_LAW_IMPACT_DELTA")


def verify(root, base, candidate, *, bootstrap=False):
    base, candidate = (
        _git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
        for ref in (base, candidate)
    )
    _git(root, "merge-base", "--is-ancestor", base, candidate)
    base_controls = _tree(root, base, *sorted(CONTROL_PATHS))
    candidate_controls = _tree(root, candidate, *sorted(CONTROL_PATHS))
    changes = _diff(root, base, candidate)
    if bootstrap:
        _require(not base_controls, "ALREADY_BOOTSTRAPPED")
        _require(changes == CONTROL_PATHS | {ATLAS, IMPACT}, "UNREVIEWED_BOOTSTRAP_DIFF")
    else:
        _require(candidate_controls == base_controls, "TRUSTED_GOVERNANCE_FILES_CHANGED")
    _require(set(candidate_controls) == CONTROL_PATHS, "GOVERNANCE_FILES_MISSING")
    for path in CONTROL_PATHS:
        _require(candidate_controls[path][:2] == ("100644", "blob"), f"INVALID_CONTROL_MODE:{path}")
    policy = _load_policy(root, candidate if bootstrap else base)
    reviewed = policy["reviewed_base"]
    _require(
        _sha(_blob(root, candidate, V1_MANIFEST)) == policy["v1_manifest_sha256"],
        "V1_MANIFEST_CHANGED",
    )
    candidate_entries = _tree(root, candidate, V2_ROOT)
    if bootstrap:
        _require(base == reviewed and not candidate_entries, "BOOTSTRAP_BASE_OR_V2_TREE_CHANGED")
        return "GOVERNANCE_BOOTSTRAP"
    base_entries = _tree(root, base, V2_ROOT)
    if not base_entries and not candidate_entries:
        # Unrelated PRs can run normally. Only the actual V2 admission is bound to the reviewed base.
        return "V2_ABSENT"
    _require(set(candidate_entries) == V2_PATHS, "V2_PATH_SET_CHANGED")
    for path, expected in policy["source_sha256"].items():
        _require(
            _sha(_blob(root, candidate, path)) == expected, f"V2_SOURCE_DIGEST_MISMATCH:{path}"
        )
    if base_entries:
        _require(base_entries == candidate_entries, "SEALED_V2_TREE_CHANGED")
        return "V2_SOURCE_PRESERVED"
    _git(root, "merge-base", "--is-ancestor", reviewed, base)
    _require(
        _diff(root, reviewed, base) <= CONTROL_PATHS | {ATLAS, IMPACT} | REGISTRATION_RECORDS,
        "REVIEWED_BASE_CHANGED",
    )
    _require(changes == V2_PATHS | {ATLAS, IMPACT}, "UNREVIEWED_IMPLEMENTATION_DIFF")
    _check_atlas(root, base, candidate, policy["source_sha256"])
    return "V2_SOURCE_ADMITTED"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", default="HEAD")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.root, args.base, args.candidate, bootstrap=args.bootstrap)
    except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"N1_V2_BREV_ADMISSION=FAIL {exc}", file=sys.stderr)
        return 1
    print(f"N1_V2_BREV_ADMISSION=PASS {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
