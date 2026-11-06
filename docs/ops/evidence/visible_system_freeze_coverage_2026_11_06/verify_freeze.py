"""Bounded freeze recovery proof. No full-drive or historical-worktree audit.

Invoke using scripts/pt after the v2 tag and its external delta exist.
The original checkout and backup are not modified. Temporary Git objects are
unpacked separately, borrowing prerequisite objects from the external copy.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[3]


def run(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, stderr=subprocess.PIPE)


def git(gitdir, *args):
    return run("git", "--no-optional-locks", "--git-dir=" + str(gitdir), *args)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_objects(gitdir, objects, scratch):
    request = scratch / "object-requests.txt"
    request.write_text("".join(oid + "\n" for oid in sorted(objects)))
    count, payload_bytes = 0, 0
    with request.open("rb") as source:
        process = subprocess.Popen(
            ["git", "--git-dir=" + str(gitdir), "cat-file", "--batch"],
            stdin=source,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        for expected in sorted(objects):
            fields = process.stdout.readline().split()
            assert len(fields) == 3, ("OBJECT_UNAVAILABLE", expected, fields)
            oid, kind, size = fields
            size = int(size)
            assert oid.decode() == expected
            digest = hashlib.sha1(kind + b" " + str(size).encode() + b"\0")
            remaining = size
            while remaining:
                block = process.stdout.read(min(4 * 1024 * 1024, remaining))
                assert block, ("TRUNCATED_OBJECT", expected)
                digest.update(block)
                remaining -= len(block)
            assert process.stdout.read(1) == b"\n"
            assert digest.hexdigest() == expected, ("OBJECT_CONTENT_MISMATCH", expected)
            count += 1
            payload_bytes += size
        assert process.wait() == 0
    return count, payload_bytes


def verify():
    record = json.loads((PACKAGE / "freeze.json").read_bytes())
    archive = Path(record["archive_destination"])
    bundle = archive / record["required_external_delta"]
    backup_git = archive / "repo-complete/Peak_Trade/.git"
    source_git = REPO / ".git"
    tag = record["checkpoint_tag"]
    commit = git(source_git, "rev-parse", tag + "^{commit}").decode().strip()
    assert (
        git(source_git, "rev-parse", record["previous_freeze_tag"] + "^{commit}").decode().strip()
        == record["previous_freeze_commit"]
    )
    assert git(source_git, "status", "--porcelain", "--untracked-files=all").strip() == b""
    assert git(source_git, "rev-parse", "HEAD").decode().strip() == commit
    run(
        "git",
        "--no-optional-locks",
        "-C",
        str(archive / "repo-complete/Peak_Trade"),
        "bundle",
        "verify",
        str(bundle),
    )
    manifest = json.loads((archive / "manifest-before.json").read_bytes())
    originals = {r["source"]: r for r in manifest["files"] if r["kind"] == "file"}
    with tempfile.TemporaryDirectory(prefix=".freeze-recovery-proof-", dir=archive) as name:
        scratch = Path(name)
        bare = scratch / "proof.git"
        run("git", "init", "--bare", "--quiet", str(bare))
        (bare / "objects/info/alternates").write_text(str(backup_git / "objects") + "\n")
        git(bare, "bundle", "unbundle", str(bundle))
        assert git(bare, "cat-file", "-t", commit).strip() == b"commit"
        entries = git(bare, "ls-tree", "-r", "-t", "-z", "--full-tree", commit).split(b"\0")
        objects = {commit, git(source_git, "rev-parse", tag).decode().strip()}
        paths = {}
        for entry in entries:
            if not entry:
                continue
            meta, path = entry.split(b"\t", 1)
            mode, kind, oid = meta.split()
            assert mode not in {b"120000", b"160000"}, ("EXTERNAL_TREE_REFERENCE", path)
            objects.add(oid.decode())
            if kind == b"blob":
                paths[path.decode()] = oid.decode()
        checked_objects, checked_bytes = check_objects(bare, objects, scratch)
        package_relative = str(PACKAGE.relative_to(REPO))
        restored_record = git(bare, "show", commit + ":" + package_relative + "/freeze.json")
        assert json.loads(restored_record) == record
        for row in record["admitted_existing_sources"]:
            restored = git(bare, "show", commit + ":" + row["path"])
            assert sha(restored) == row["sha256"]
            assert (REPO / row["path"]).read_bytes() == restored
            assert (archive / "repo-complete/Peak_Trade" / row["path"]).read_bytes() == restored
        basis = record["obsidian_basis_package"]
        first = json.loads(git(bare, "show", commit + ":" + basis + "/freeze.json"))
        packed = git(bare, "show", commit + ":" + basis + "/" + first["obsidian_inventory"])
        assert sha(packed) == record["obsidian_inventory_sha256"]
        inventory = json.loads(gzip.decompress(packed))
        saved = {r["path"]: r for r in first["changed_view_markers"]}
        restored_vault, archived_count, delta_count = {}, 0, 0
        for row in inventory["files"]:
            relative = row["path"]
            if relative in saved:
                contents = gzip.decompress(
                    git(bare, "show", commit + ":" + basis + "/" + saved[relative]["saved"])
                )
                delta_count += 1
            else:
                locator = originals[str(Path(first["obsidian_vault"]) / relative)]
                contents = (archive / locator["archived"]).read_bytes()
                archived_count += 1
            assert sha(contents) == row["sha256"], ("OBSIDIAN_CONTENT_MISMATCH", relative)
            restored_vault[relative] = row["sha256"]
        assert len(restored_vault) == record["obsidian_bound_files"] == 4954
        cases = ET.fromstring(
            git(bare, "show", commit + ":" + package_relative + "/mail-adapter-tests.xml")
        ).findall(".//testcase")
        assert len(cases) == 7
        assert not any(
            c.find(t) is not None for c in cases for t in ["failure", "error", "skipped"]
        )
    return {
        "result": "PASS",
        "verified_at": datetime.now(ZoneInfo("Europe/Berlin")).isoformat(),
        "tag": tag,
        "commit": commit,
        "versioned_files_recoverable": len(paths),
        "current_tree_git_objects_content_verified": checked_objects,
        "current_tree_git_object_bytes": checked_bytes,
        "obsidian_files_recovered_byte_exactly": len(restored_vault),
        "obsidian_from_prior_copy": archived_count,
        "obsidian_from_committed_updates": delta_count,
        "previously_ignored_source_and_test_included": 2,
        "existing_mocked_tests_passed": len(cases),
        "delta_bundle": str(bundle),
        "delta_bundle_bytes": bundle.stat().st_size,
        "delta_bundle_sha256": sha(bundle.read_bytes()),
        "prior_tag_preserved": True,
        "source_checkout_clean": True,
        "live_vault_present_at_final_check": Path(record["obsidian_vault"]).is_dir(),
        "historical_worktrees_or_full_drive_checked": False,
        "whole_system_runtime_or_disaster_recovery_proven": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
