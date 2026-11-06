"""Read-only verification of the bounded Obsidian/repository knowledge checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from urllib.parse import unquote, urlparse

PACK = Path(__file__).resolve().parent
REPO = PACK.parents[3]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(name: str):
    return json.loads((PACK / name).read_text())


def safe_path(root: Path, relative: str) -> Path:
    path = root / relative
    assert not Path(relative).is_absolute() and ".." not in Path(relative).parts, relative
    assert path.resolve().is_relative_to(root.resolve()), relative
    return path


def repo_original(representation: dict) -> bytes:
    path = safe_path(REPO, representation["path"])
    if representation["kind"] == "EXACT_FILE":
        return path.read_bytes()
    assert representation["kind"] == "EXACT_UTF8_IN_JSON", representation
    return json.loads(path.read_text())[representation["key"]].encode()


def original(row: dict) -> bytes:
    storage = row["storage"]
    if storage["kind"] == "REPOSITORY_ORIGINAL":
        raw = repo_original(storage["representation"])
    else:
        with tarfile.open(safe_path(PACK, storage["archive"]), "r:gz") as archive:
            stream = archive.extractfile(storage["member"])
            assert stream is not None
            raw = stream.read()
    assert sha(raw) == row["sha256"] and len(raw) == row["bytes"], row["path"]
    return raw


def introduced_links(root: Path, path: str, text: str, old_text: str) -> tuple[int, int]:
    wiki_pattern = r"\[\[([^\]\n]+)\]\]"
    markdown_pattern = r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)"
    wiki = set(re.findall(wiki_pattern, text)) - set(re.findall(wiki_pattern, old_text))
    markdown = set(re.findall(markdown_pattern, text)) - set(re.findall(markdown_pattern, old_text))
    for target in wiki:
        target = target.split("|", 1)[0].split("#", 1)[0]
        if not target:
            continue
        candidate = root / target
        assert candidate.is_file() or candidate.with_suffix(".md").is_file(), (path, target)
    checked = 0
    for target in markdown:
        target = html.unescape(unquote(target.strip().strip("<>")))
        parsed = urlparse(target)
        if parsed.scheme in {"https", "http", "mailto", "obsidian"} or target.startswith("#"):
            continue
        if parsed.scheme == "file":
            target = parsed.path
        target = target.split("#", 1)[0]
        target = re.sub(r":\d+$", "", target)
        candidate = Path(target) if target.startswith("/") else root / Path(path).parent / target
        assert candidate.is_file(), (path, target)
        checked += 1
    return len(wiki), checked


def verify(vaults: bool) -> dict:
    coverage = load("coverage.json")
    before = load("vaults-before.json")
    rows = {
        (label, row["path"]): row
        for label, vault in coverage["vaults"].items()
        for row in vault["files"]
    }
    assert len(rows) == sum(len(v["files"]) for v in coverage["vaults"].values())
    expected = {}
    verified_hashes = set()
    references = {}
    for row in rows.values():
        storage = row["storage"]
        if storage["kind"] == "ARCHIVE_ORIGINAL":
            key = (storage["archive"], storage["member"])
            value = (row["sha256"], row["bytes"])
            assert key not in expected or expected[key] == value
            expected[key] = value
        else:
            assert storage["kind"] == "REPOSITORY_ORIGINAL"
            key = json.dumps(storage["representation"], sort_keys=True)
            if key not in references:
                raw = repo_original(storage["representation"])
                references[key] = (sha(raw), len(raw))
            assert references[key] == (row["sha256"], row["bytes"]), row["path"]
            verified_hashes.add(row["sha256"])
    seen = set()
    for record in coverage["archives"]:
        path = safe_path(PACK, record["path"])
        assert (
            sha(path.read_bytes()) == record["sha256"] and path.stat().st_size == record["bytes"]
        ), record["path"]
        count = 0
        with tarfile.open(path, "r|gz") as archive:
            for member in archive:
                assert member.isfile() and not member.issym() and not member.islnk(), member.name
                assert not Path(member.name).is_absolute() and ".." not in Path(member.name).parts
                key = (record["path"], member.name)
                assert key in expected and key not in seen, key
                stream = archive.extractfile(member)
                assert stream is not None
                digest = hashlib.sha256()
                size = 0
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
                assert (digest.hexdigest(), size) == expected[key], key
                verified_hashes.add(digest.hexdigest())
                seen.add(key)
                count += 1
        assert count == record["members"]
    assert seen == set(expected)
    for label, vault in before.items():
        for row in vault["files"]:
            assert row["sha256"] in verified_hashes, (label, row["path"], "ORIGINAL_NOT_PRESERVED")

    checkpoint = load("repository-before.json")
    navigation = load("repository-document-change.json")
    unchanged = 0
    for row in checkpoint["files"]:
        path = safe_path(REPO, row["path"])
        if row["path"] == navigation["path"]:
            assert sha(path.read_bytes()) == navigation["after_sha256"]
            assert (
                sha((PACK / navigation["before_file"]).read_bytes())
                == row["sha256"]
                == navigation["before_sha256"]
            )
        elif "symlink" in row:
            assert path.is_symlink() and str(path.readlink()) == row["symlink"]
            unchanged += 1
        else:
            assert sha(path.read_bytes()) == row["sha256"], (row["path"], "PREEXISTING_REPO_DRIFT")
            unchanged += 1
    subprocess.run(
        ["git", "-C", str(REPO), "merge-base", "--is-ancestor", checkpoint["head"], "HEAD"],
        check=True,
    )
    for record in load("current-module-symbols.json"):
        assert sha((REPO / record["path"]).read_bytes()) == record["sha256"]

    for projection in load("readers.json"):
        row = rows[(projection["vault"], projection["source_path"])]
        raw = original(row)
        assert sha(raw) == projection["source_sha256"]
        text = re.sub(
            r"`([^`\n]+)`", lambda m: "`" + m[1].replace("/", "&#47;") + "`", raw.decode()
        )
        footer = f"\n<!-- Vollständige Leserprojektion; Original: {projection['vault']}:{projection['source_path']}; SHA256: {projection['source_sha256']}. Native Wikilinks beziehen sich auf den ursprünglichen Vault. -->\n"
        actual = safe_path(PACK, projection["path"]).read_bytes()
        assert actual == (text + footer).encode() and sha(actual) == projection["sha256"]

    links = [0, 0]
    changes = load("abgleich.json")["changes"]
    if vaults:
        for (label, path), row in rows.items():
            root = Path(coverage["vaults"][label]["root_at_capture"])
            assert sha((root / path).read_bytes()) == row["sha256"], (label, path, "VAULT_DRIFT")
        for change in changes:
            root = Path(coverage["vaults"][change["vault"]]["root_at_capture"])
            path = root / change["path"]
            assert sha(path.read_bytes()) == change["after_sha256"]
            old_text = ""
            if change["before_sha256"]:
                backup = (
                    Path(coverage["vaults"]["system"]["root_at_capture"])
                    / ".belege/Systemindex/repoabgleich-2026-11-06/vorher"
                    / change["vault"]
                    / change["path"]
                )
                assert sha(backup.read_bytes()) == change["before_sha256"]
                old_text = backup.read_text()
            if path.suffix == ".md":
                a, b = introduced_links(root, change["path"], path.read_text(), old_text)
                links[0] += a
                links[1] += b
        for name in ["Systemindexbindung.json", "Systematlasbindung.json", "Ansichtsbindung.json"]:
            root = Path(coverage["vaults"]["system"]["root_at_capture"])
            current = json.loads((root / name).read_text())
            prior = json.loads(
                (
                    root / ".belege/Systemindex/repoabgleich-2026-11-06/vorher/system" / name
                ).read_text()
            )
            for key, value in prior.items():
                if key != "generated_files":
                    assert current[key] == value, (name, key, "HISTORICAL_BINDING_CHANGED")

    if (PACK / "package.json").exists():
        package = load("package.json")
        actual_paths = {
            str(p.relative_to(PACK))
            for p in PACK.rglob("*")
            if p.is_file() and p.name != "package.json" and "__pycache__" not in p.parts
        }
        assert actual_paths == {r["path"] for r in package["files"]}, "PACKAGE_FILE_SET_DRIFT"
        for row in package["files"]:
            assert sha(safe_path(PACK, row["path"]).read_bytes()) == row["sha256"], row["path"]

    return {
        "result": "PASS",
        "scope": "EXACT_CONTENT_PRESERVATION_AND_BOUNDED_DOCUMENT_ALIGNMENT",
        "captured_files": len(rows),
        "before_originals_preserved": sum(len(v["files"]) for v in before.values()),
        "archives_verified": len(coverage["archives"]),
        "unique_archive_members_verified": len(seen),
        "existing_original_references_verified": len(references),
        "reader_projections_verified": len(load("readers.json")),
        "preexisting_repository_files_unchanged": unchanged,
        "repository_navigation_files_changed": 1,
        "vault_content_checked": vaults,
        "introduced_wikilinks_checked": links[0],
        "introduced_markdown_links_checked": links[1],
        "global_semantic_recertified": False,
        "product_code_changed": False,
        "runtime_authorization_effect": "NONE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vaults",
        action="store_true",
        help="Also check captured original vault paths and introduced links.",
    )
    parser.add_argument(
        "--cat",
        nargs=2,
        metavar=("VAULT", "ORIGINAL_PATH"),
        help="Write exact captured original bytes to stdout.",
    )
    args = parser.parse_args()
    if args.cat:
        label, path = args.cat
        rows = load("coverage.json")["vaults"][label]["files"]
        row = next(row for row in rows if row["path"] == path)
        sys.stdout.buffer.write(original(row))
        return
    print(json.dumps(verify(args.vaults), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
