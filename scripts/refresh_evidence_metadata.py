"""Refresh reviewed evidence descriptions without replacing scientific files.

Preflight verifies both collections before any writes. Metadata replacements are
atomic per file and rolled back on caught failures; a machine crash is not a
transaction. Never run a catalog scan concurrently with publication.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from jsonschema import Draft202012Validator
import yaml

from evidence_notes import render_evidence_summary, pilot_evidence_context
from prepare_evidence_pilot import require, relative_file, sha256, write_json
from evidence_sources import evidence_context, load_records, load_pilot_plan, input_fingerprints, inputs_sha256

REPO = Path(__file__).resolve().parents[1]


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def state(path):
    return sha256(path), path.stat().st_mtime_ns


def check_descriptor_change(old, new):
    for key in ['schema', 'id', 'kind', 'primary_asset', 'source', 'temporal']:
        require(old.get(key) == new.get(key), 'Metadata refresh cannot change ' + key)
    # Existing assets may gain clearer metadata, but their identity, locations,
    # roles and media types must remain unchanged.
    without_metadata = lambda asset: {k:v for k,v in asset.items() if k != 'metadata'}
    for key, asset in old['assets'].items():
        require(key in new['assets'] and without_metadata(asset) == without_metadata(new['assets'][key]),
                'Metadata refresh cannot change an existing asset: ' + key)
    added = set(new['assets']) - set(old['assets'])
    require(added <= {'evidence_summary'}, 'Only the scientific evidence note may be added.')
    brief = new['assets'].get('evidence_summary', {})
    require(without_metadata(brief) == dict(location='local', path='evidence-summary.md',
            media_type='text/markdown', roles=['metadata']), 'Invalid scientific evidence note asset.')


def preserve_provenance(previous, current):
    """Keep changed delivery contexts once, outside the versioned authoring inputs."""
    prior = {k:v for k,v in previous.items() if k != 'provenance_history'}
    history = deepcopy(previous.get('provenance_history', []))
    if prior != current and prior not in history:
        history.append(prior)
    return dict(current, provenance_history=history) if history else dict(current)


def plan_collection(root, records, contexts, fingerprints, schema):
    """Construct metadata replacements only after validating the previous delivery."""
    root = root.resolve(strict=True)
    report_path = root / 'preparation-report.json'
    previous = json.loads(report_path.read_text(encoding='utf-8'))
    report = deepcopy(previous)
    delivered = {d['id']: d for d in report['datasets']}
    require(len(delivered) == len(records) and set(delivered) == {r['id'] for r in records},
            'Dataset set differs from the previous delivery.')
    before = {report_path: state(report_path)}
    payloads, replacements = {}, {}
    validator = Draft202012Validator(schema)
    for record in records:
        identifier = record['id']; result = delivered[identifier]
        for key, expected in [('kind',record['kind']),('directory',record['directory']),
                              ('primary',record['output_file']),('source_files',record['source_files']),
                              ('sidecar',record['output_file'] + '.eolab.yaml')]:
            require(result[key] == expected, 'Preparation identity or source changed: ' + identifier + '/' + key)
        folder = relative_file(root, result['directory'])
        sidecar = relative_file(folder, result['sidecar'])
        context_path = folder / 'review-context.json'
        brief_path = folder / 'evidence-summary.md'
        allowed_metadata = {sidecar, context_path, brief_path}
        for name, details in result['files'].items():
            path = relative_file(folder, name)
            before[path] = state(path)
            require(before[path][0] == details['sha256'] and path.stat().st_size == details['bytes'],
                    'Delivered checksum differs: ' + identifier + '/' + name)
            if path not in allowed_metadata:
                payloads[path] = before[path]
        old_context = json.loads(context_path.read_text(encoding='utf-8'))
        new_context = contexts[identifier]
        if 'scientific_note_text' in record:
            # Preserve old delivered evidence as generated history when the source
            # layout changes, without keeping duplicate snapshots in Git.
            new_context = preserve_provenance(old_context, new_context)
        else:
            for key, value in old_context.items():
                if key not in {'evidence_summary', 'metadata_history'}:
                    require(new_context.get(key) == value, 'Historical evidence changed: ' + identifier + '/' + key)
            if old_context.get('metadata_history'):
                require(new_context.get('metadata_history', [])[:len(old_context['metadata_history'])]
                        == old_context['metadata_history'], 'Historical metadata was removed.')
        new = record['descriptor']
        validator.validate(new)
        require(new['id'] == identifier and new['kind'] == record['kind'], 'Descriptor identity differs.')
        require(new['assets'][new['primary_asset']]['path'] == result['primary'], 'Primary file differs.')
        check_descriptor_change(yaml.safe_load(sidecar.read_text(encoding='utf-8')), new)
        for asset in new['assets'].values():
            if asset['location'] == 'local' and asset['path'] != 'evidence-summary.md':
                require(relative_file(folder, asset['path']).is_file(), 'A linked asset is missing.')
        generated = {
            sidecar: yaml.safe_dump(new,allow_unicode=True,sort_keys=False,width=100).encode('utf-8'),
            context_path: json_bytes(new_context),
            brief_path: render_evidence_summary(record).encode('utf-8')}
        for path, content in generated.items():
            if path not in before:
                require(not path.exists(), 'Unrecorded metadata already exists.')
            replacements[path] = content
            result['files'][path.relative_to(folder).as_posix()] = dict(
                sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
    require({p.resolve() for p in root.rglob('*') if p.is_file()} == set(before),
            'Unrecorded files exist in the prepared collection.')
    previous_fingerprints = {k:previous.get(k) for k in fingerprints}
    report.update(fingerprints)
    if previous.get('metadata_refresh'):
        report.setdefault('metadata_refresh_history', []).append(previous['metadata_refresh'])
    report['metadata_refresh'] = dict(
        method='Scientific summaries and linked evidence notes; original payloads and preparation checks retained.',
        previous_plan_fingerprints=previous_fingerprints, delivered_checksums_verified=True,
        payload_files_verified=len(payloads), payload_bytes_and_mtimes_preserved=True,
        data_transformations_rerun=False,
        updated_files=[p.relative_to(root).as_posix() for p in replacements] + ['preparation-report.json'])
    replacements[report_path] = json_bytes(report)
    return report, replacements, before, payloads


def publish(root, replacements, before, payloads):
    """Publish verified metadata with rollback, leaving data bytes and mtimes intact."""
    root = root.resolve(strict=True)
    require(all(p.resolve().is_relative_to(root) for p in replacements), 'Publication escapes the delivery root.')
    staging = Path(tempfile.mkdtemp(prefix='.evidence-refresh-', dir=root.parent)).resolve()
    require(staging.is_relative_to(root.parent) and staging != root, 'Invalid staging location.')
    keep = False
    try:
        pending, backups = {}, {}
        for index, (path, content) in enumerate(replacements.items()):
            pending[path] = staging / f'{index}.pending'
            pending[path].write_bytes(content)
            if path.exists():
                require(path in before, 'An unrecorded destination appeared.')
                backups[path] = staging / f'{index}.previous'
                shutil.copy2(path, backups[path])
        for path, expected in before.items():
            require(state(path) == expected, 'Delivered file changed during preflight.')
        for path in set(replacements) - set(before):
            require(not path.exists(), 'New metadata destination appeared during preflight.')
        replaced = []
        try:
            for path, source in pending.items():
                os.replace(source, path)
                replaced.append(path)
            for path, expected in payloads.items():
                require(state(path) == expected, 'Scientific payload changed during refresh.')
            for path, content in replacements.items():
                require(path.read_bytes() == content, 'Published metadata differs from staged content.')
        except BaseException:
            failures = []
            for path in reversed(replaced):
                try:
                    if path in backups:
                        os.replace(backups[path], path)
                    else:
                        path.unlink()
                except OSError:
                    failures.append(path.relative_to(root).as_posix())
            if failures:
                keep = True
                raise RuntimeError('Metadata rollback failed for ' + ', '.join(failures)
                                   + '; recovery copies retained in ' + staging.name)
            raise
    finally:
        if not keep:
            shutil.rmtree(staging)


def reviewed_records():
    return dict(matched=load_records(REPO/'evidence/matched/recipes'),
                pilot=load_pilot_plan(REPO/'evidence/pilot/recipes')['records'])


def export_review_files(collections):
    """Render disposable previews; committed YAML and notes remain the inputs."""
    for collection, records in collections.items():
        base=REPO/'build/evidence'/collection
        (base/'briefs').mkdir(parents=True, exist_ok=True)
        for record in records:
            (base/'briefs'/(record['id']+'.md')).write_text(
                render_evidence_summary(record),encoding='utf-8',newline='\n')


def refresh(data_root):
    data_root=data_root.resolve(strict=True)
    collections=reviewed_records()
    schema=json.loads((REPO/'evidence/pilot/eolab-item-v1.schema.json').read_text(encoding='utf-8'))
    reports, replacements, before, payloads = {}, {}, {}, {}
    for collection, records in collections.items():
        root=data_root/collection
        previous=json.loads((root/'preparation-report.json').read_text(encoding='utf-8'))
        checks={d['id']:d['checks'] for d in previous['datasets']}
        if collection=='matched':
            contexts={r['id']:dict(evidence_context(r),preparation_checks=checks[r['id']]) for r in records}
            fingerprints={'plans':input_fingerprints(REPO/'evidence/matched/recipes')}
        else:
            contexts={r['id']:pilot_evidence_context(r) for r in records}
            fingerprints={'records_sha256':inputs_sha256(REPO/'evidence/pilot/recipes')}
        report, updates, old, data=plan_collection(root,records,contexts,fingerprints,schema)
        reports[collection]=report
        replacements.update(updates);before.update(old);payloads.update(data)
    audit=dict(datasets_updated=sum(len(r) for r in collections.values()),
               payload_files_verified=len(payloads),payload_bytes_and_mtimes_preserved=True,
               data_transformations_rerun=False,prior_provenance_retained=True,
               linked_scientific_notes=sum(len(r) for r in collections.values()),
               catalog_rescan_performed=False)
    publish(data_root,replacements,before,payloads)
    try:
        for collection, report in reports.items():
            name='preparation.json' if collection=='matched' else 'evidence_pilot.json'
            write_json(REPO/'build/evidence'/collection/name,report)
        export_review_files(collections)
        write_json(REPO/'build/evidence/metadata-refresh.json',audit)
    except Exception as error:
        raise RuntimeError('Processed metadata was published and verified, but local report/preview '
                           'export failed. The delivery is updated; copy its preparation reports and '
                           'rerun --export-only after resolving the export error.') from error
    return audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path)
    parser.add_argument('--export-only',action='store_true')
    args=parser.parse_args()
    if args.export_only:
        export_review_files(reviewed_records())
        print('Rendered evidence note previews in build/evidence.')
    else:
        require(args.data_root is not None,'Specify --data-root or --export-only.')
        print(json.dumps(refresh(args.data_root),indent=2))


if __name__=='__main__':main()
