"""Read the frozen documentation checkpoint without importing product modules."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(package: Path) -> dict:
    manifest = json.loads((package / 'manifest.json').read_text())
    repo = Path(subprocess.check_output(
        ['git', '-C', str(package), 'rev-parse', '--show-toplevel'], text=True
    ).strip())
    errors = []

    def require(ok, message):
        if not ok:
            errors.append(message)

    for record in manifest['package_files']:
        path = package / record['path']
        require(path.is_file() and sha(path.read_bytes()) == record['sha256'],
                'package bytes: ' + record['path'])
    listed = {x['path'] for x in manifest['package_files']} | {'manifest.json'}
    actual = {str(p.relative_to(package)) for p in package.rglob('*') if p.is_file()}
    require(actual == listed, 'unexpected or missing checkpoint files')

    note_links = 0
    for note in [package / 'README.md', *sorted((package / 'notes').glob('*.md'))]:
        for raw in re.findall(r'\]\(([^\n]+?)\)', note.read_text()):
            target = unquote(raw.strip('<>')).split('#', 1)[0]
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target):
                continue
            target = re.sub(r':\d+$', '', target)
            path = Path(target) if target.startswith('/') else note.parent / target
            require(path.exists(), 'readable note link: ' + str(note.name) + ' ' + target)
            note_links += 1

    artifacts = {}
    for record in manifest['original_artifacts']:
        data = json.loads((package / record['archive']).read_text())
        payload = data['original_utf8'].encode('utf-8')
        require(sha(payload) == record['sha256'] == data['sha256'],
                'original text: ' + record['archive'])
        artifacts[record['origin']] = payload
    for record in manifest['pdf_originals']:
        require(sha((package / record['archive']).read_bytes()) == record['sha256'],
                'original PDF: ' + record['archive'])

    rows = []
    for name in manifest['repository_baseline']['file_parts']:
        rows.extend(json.loads((package / name).read_text()))
    baseline = {}
    for key in manifest['repository_baseline']['key_order']:
        baseline[key] = rows if key == 'files' else manifest['repository_baseline']['metadata'][key]
    reconstructed = (json.dumps(baseline, ensure_ascii=False, indent=2) + '\n').encode()
    require(sha(reconstructed) == manifest['repository_baseline']['original_sha256'],
            'complete original repository baseline reconstruction')

    source_bytes = {}
    for rel, record in manifest['reviewed_sources'].items():
        if record['materialization'] == 'INERT_WORKING_TREE_SNAPSHOT':
            payload = artifacts[record['origin']]
        else:
            result = subprocess.run(
                ['git', '-C', str(repo), 'show', manifest['source_head'] + ':' + rel],
                capture_output=True, check=False,
            )
            require(result.returncode == 0, 'bound Git object: ' + rel)
            payload = result.stdout
        require(sha(payload) == record['sha256'], 'review source: ' + rel)
        source_bytes[rel] = payload

    def symbols(tree):
        found = {}

        def walk(nodes, prefix=''):
            for n in nodes:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    found[prefix + n.name] = (n.lineno, n.end_lineno)
                    if isinstance(n, ast.ClassDef):
                        walk(n.body, prefix + n.name + '.')
        walk(tree.body)
        return found

    for key, anchor in manifest['review_anchors'].items():
        found = symbols(ast.parse(source_bytes[anchor['path']].decode()))
        require(found.get(anchor['symbol']) == (anchor['line'], anchor['end_line']),
                'exact review anchor: ' + key)

    historical = json.loads(artifacts[manifest['historical_report_origin']])
    require(historical['result'] == 'PASS', 'historical document verification result')
    require(not historical['complete_semantic_understanding_claimed'],
            'historical report is not semantic completion')
    require(manifest['product_changes_in_this_checkpoint'] == 0,
            'checkpoint product mutation claim')
    require(manifest['runtime_authorization_effect'] == 'NONE',
            'checkpoint runtime authorization')

    return {
        'schema': 'peaktrade.iu_sl_opt.frozen_checkpoint_readback.v1',
        'result': 'PASS' if not errors else 'FAIL',
        'errors': errors,
        'source_head': manifest['source_head'],
        'package_files': len(manifest['package_files']),
        'original_text_artifacts': len(artifacts),
        'original_pdfs': len(manifest['pdf_originals']),
        'bound_review_sources': len(source_bytes),
        'bound_review_anchors': len(manifest['review_anchors']),
        'pre_review_repository_files': len(rows),
        'readable_note_local_links_checked': note_links,
        'product_modules_imported': False,
        'product_tests_executed': False,
        'whole_system_semantic_completion_claimed': False,
    }


if __name__ == '__main__':
    result = verify(Path(__file__).resolve().parent)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['result'] == 'PASS' else 1)
