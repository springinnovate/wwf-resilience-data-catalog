"""Load reviewed evidence inputs and regenerate matching provenance from source records.

YAML is authoritative for catalog metadata; recipes only describe preparation.
This module deliberately has no GIS dependencies or stored-report dependencies.
"""
from __future__ import annotations
import csv
from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

import yaml

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / 'evidence'


def reference(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or '..' in relative.parts or ':' in name or '\\' in name:
        raise ValueError('Expected a confined relative evidence path.')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Evidence reference escapes its root.')
    return path


def load_records(recipe_dir: Path) -> list[dict]:
    records = []
    for path in sorted(recipe_dir.glob('*.json')):
        recipe = json.loads(path.read_text(encoding='utf-8'))
        # Small inline plans remain useful for isolated transformation tests.
        if isinstance(recipe, list) or 'records' in recipe:
            records.extend(recipe if isinstance(recipe, list) else recipe['records'])
            continue
        root = recipe_dir.resolve().parents[1]
        sidecar = reference(root, recipe['sidecar'])
        descriptor = yaml.safe_load(sidecar.read_text(encoding='utf-8'))
        identifier = descriptor['id']
        if path.stem != identifier:
            raise ValueError('Recipe filename must match its sidecar ID.')
        primary = descriptor['assets'][descriptor['primary_asset']]
        if primary['location'] != 'local':
            raise ValueError('A preparation recipe requires a local primary asset.')
        note = reference(root, recipe['scientific_note'])
        curation = json.loads(reference(root, recipe['curation']).read_text(encoding='utf-8'))
        if note.stem != identifier or curation.get('dataset_id') != identifier:
            raise ValueError('Scientific note and curation must identify the same dataset as the sidecar.')
        records.append(dict(recipe, id=identifier, kind=descriptor['kind'],
            output_file=primary['path'], descriptor=descriptor,
            scientific_note_text=note.read_text(encoding='utf-8'),
            review_context=curation))
    if not records:
        raise ValueError('No evidence recipes found.')
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('Duplicate dataset ID.')
    if len({r['directory'] for r in records}) != len(records):
        raise ValueError('Duplicate dataset directory.')
    return records


def load_pilot_plan(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding='utf-8'))
    return dict(eolab_contract=json.loads((path.parent/'contract.json').read_text(encoding='utf-8')),
                records=load_records(path))


def input_fingerprints(path: Path) -> dict[str, str]:
    """Hash recipes and every authored input they reference, using portable names."""
    if path.is_file():
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}
    root = path.resolve().parents[1]
    inputs = set(path.glob('*.json'))
    for recipe_path in list(inputs):
        recipe = json.loads(recipe_path.read_text(encoding='utf-8'))
        if isinstance(recipe, dict) and 'sidecar' in recipe:
            inputs.update(reference(root, recipe[key]) for key in ['sidecar','scientific_note','curation'])
    inputs.update(p for p in [root/'pilot/eolab-item-v1.schema.json',path.parent/'contract.json'] if p.is_file())
    return {p.resolve().relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(inputs)}


def inputs_sha256(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(input_fingerprints(path),sort_keys=True).encode('utf-8')).hexdigest()


@lru_cache(maxsize=1)
def reconciliation_tables() -> dict[str, list[dict]]:
    """Build current crosswalks once per process, with no committed outputs or stale cache."""
    with tempfile.TemporaryDirectory(prefix='evidence-reconciliation-') as temporary:
        subprocess.run([sys.executable,str(REPO/'scripts/build_reconciliation.py'),
                        '--output-dir',temporary],cwd=REPO,check=True,stdout=subprocess.DEVNULL)
        result = {}
        for name in ['matches','papers','asset_links','review_summary']:
            with (Path(temporary)/(name+'.csv')).open(encoding='utf-8-sig',newline='') as handle:
                result[name] = list(csv.DictReader(handle))
        return result


def evidence_context(record: dict) -> dict:
    """Join authored interpretation to original rows and freshly rebuilt matching records."""
    row_ids = set(record['row_ids'])
    rows = json.loads((REPO/'data/source/parsed_sheet.json').read_text(encoding='utf-8'))['rows']
    selected = [r for r in rows if r['row_id'] in row_ids]
    if {r['row_id'] for r in selected} != row_ids:
        raise ValueError('Unknown sheet row.')
    tables = reconciliation_tables()
    paper_ids = {r['paper_id'] for r in selected}
    context = dict(
        note='Original sheet and matching records are historical evidence. The curated evidence and adjacent YAML describe this prepared product.',
        source_base='evidence_data',source_sheet_rows=selected,
        reconciliation_snapshot=[r for r in tables['matches'] if r['row_id'] in row_ids],
        paper_references=[r for r in tables['papers'] if r['paper_id'] in paper_ids],
        asset_links=[r for r in tables['asset_links'] if r['row_id'] in row_ids],
        curated_evidence=record.get('review_context',{}),source_files=record['source_files'])
    # Include exact processing choices, without copying metadata or inventories into source recipes.
    context['preparation_recipe'] = {k:v for k,v in record.items() if k not in {
        'descriptor','review_context','scientific_note_text','evidence_summary','metadata_history'}}
    return context
