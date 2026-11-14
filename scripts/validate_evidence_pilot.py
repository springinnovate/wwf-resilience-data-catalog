"""Validate prepared evidence through EOLab's real discovery and metadata readers.

This check builds public STAC previews without writing to a running catalog.
It deliberately does not substitute fake source readers or parse nonspatial
payloads on EOLab's behalf; data-value checks belong to the preparation script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from evidence_notes import pilot_evidence_context
from evidence_sources import load_pilot_plan
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[1]


def current_context(context: dict) -> dict:
    """Compare current authored evidence without historical delivery snapshots."""
    return {key: value for key, value in context.items() if key != 'provenance_history'}


def require(condition: bool, message: str) -> None:
    """Stop admission validation when an expected contract is not satisfied."""
    if not condition:
        raise ValueError(message)


def write_json(path: Path, value: Any) -> None:
    """Write a public report using relative identifiers and portable metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def validate(data_root: Path, eolab_source: Path, records_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Discover the three real datasets and check their public metadata and identity."""
    require(sys.version_info >= (3, 12), 'EOLab admission requires Python 3.12 or newer.')
    data_root, eolab_source = data_root.resolve(strict=True), eolab_source.resolve(strict=True)
    sys.path.insert(0, str(eolab_source / 'src'))
    from eolab_app.catalog.descriptor_contract import CatalogDescriptor, descriptor_json_schema
    from eolab_app.catalog.descriptors import publish_descriptor_assets
    from eolab_app.catalog.discovery import FilesystemDatasetDiscovery
    from eolab_app.catalog.handlers import create_default_dataset_handler_registry
    from eolab_app.catalog.public_metadata import copy_public_catalog_metadata

    expected_schema = json.loads((REPO / 'evidence/pilot/eolab-item-v1.schema.json').read_text(encoding='utf-8'))
    require(descriptor_json_schema() == expected_schema, 'EOLab descriptor schema differs from the reviewed schema.')
    plan = load_pilot_plan(records_path)
    records = {record['id']: record for record in plan['records']}
    registry = create_default_dataset_handler_registry()
    discovery = FilesystemDatasetDiscovery(data_root, (data_root,), registry)

    def scan() -> list[dict[str, Any]]:
        """Run unchanged EOLab discovery, source readers and public metadata projection."""
        candidates, errors = discovery.discover()
        require(not errors, f'EOLab discovery errors: {errors}')
        require(len(candidates) == 3, f'Expected three datasets, found {len(candidates)}.')
        public = []
        for candidate in candidates:
            for item in registry.build_items(data_root, candidate):
                public.append(copy_public_catalog_metadata(publish_descriptor_assets(item)))
        require(len(public) == 3, 'Expected exactly three STAC Items.')
        return sorted(public, key=lambda item: item['properties']['eolab:descriptor_id'])

    items = scan()
    require(items == scan(), 'Repeated discovery changed identities or metadata.')
    summaries = []
    for item in items:
        props = item['properties']
        identifier = props['eolab:descriptor_id']
        require(identifier in records, 'Unexpected descriptor identity.')
        record = records[identifier]
        declaration = record['descriptor']
        require(props['title'] == declaration['metadata']['title'], 'Dataset title was not retained.')
        expected_metadata = CatalogDescriptor.model_validate(declaration).metadata.model_dump(mode='json')
        require(props['eolab:metadata'] == expected_metadata,
                'Curated metadata or publication references changed during admission.')
        context_path = data_root / record['directory'] / declaration['assets']['review_context']['path']
        require(current_context(json.loads(context_path.read_text(encoding='utf-8')))
                == current_context(pilot_evidence_context(record)),
                'Linked supporting evidence differs from the reviewed record.')
        for key, asset in declaration['assets'].items():
            admitted = item['assets'][key]
            if asset['location'] == 'local':
                require(admitted['href'].startswith('/api/catalog/asset?'), 'Local asset lacks a catalog identity URL.')
            else:
                require(admitted['href'] == asset['href'], 'External reference changed.')
        temporal = declaration['temporal']
        if temporal['mode'] == 'interval':
            require(props['datetime'] is None and props['start_datetime'] == temporal['start_datetime']
                    and props['end_datetime'] == temporal['end_datetime'], 'Observation interval changed.')
        else:
            require(props['eolab:time_basis'] == 'source-modified', 'Modified time is not disclosed.')
        if record['kind'] == 'nonspatial':
            require(item['geometry'] is None and 'bbox' not in item, 'Nonspatial geometry was invented.')
        else:
            require(item['geometry'] is not None and props['proj:epsg'] == 4326, 'Spatial metadata differs.')
        summaries.append(dict(id=identifier, kind=record['kind'], collection=item['collection'],
                              item_id=item['id'], assets=len(item['assets']), annotations_preserved=True,
                              supporting_evidence_preserved=True,
                              temporal_mode=temporal['mode']))
    text = json.dumps(items, ensure_ascii=False)
    require('file://' not in text and str(data_root) not in text and data_root.as_posix() not in text,
            'Public Item metadata contains a private path.')
    revision = subprocess.check_output(['git', '-C', str(eolab_source), 'rev-parse', 'HEAD'], text=True).strip()
    module = eolab_source / 'src/eolab_app/catalog/descriptor_contract.py'
    report = dict(eolab_source_revision=revision, eolab_merged_revision=plan['eolab_contract']['merged_revision'],
                  descriptor_module_sha256=hashlib.sha256(module.read_bytes()).hexdigest(),
                  schema_matches=True, discovery_errors=0, repeated_discovery_identical=True,
                  provenance_history_excluded_from_context_comparison=True,
                  public_paths_are_catalog_identities=True, database_published=False,
                  scope='Real filesystem discovery, native raster/vector readers, sidecar admission and public metadata projection. No running HTTP/pgSTAC service was exercised.',
                  datasets=summaries)
    return report, items


def main() -> None:
    """Validate a prepared directory without changing EOLab or its running catalog."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--eolab-source', type=Path, required=True)
    parser.add_argument('--recipes', '--records', dest='recipes', type=Path, default=REPO/'evidence/pilot/recipes')
    parser.add_argument('--report', type=Path, default=REPO/'build/evidence/pilot/admission.json')
    parser.add_argument('--items', type=Path, default=REPO/'build/evidence/pilot/stac-preview.json')
    args = parser.parse_args()
    report, items = validate(args.data_root, args.eolab_source, args.recipes)
    write_json(args.report, report)
    write_json(args.items, items)
    print('EOLab admitted exactly three datasets; metadata, relative source links and repeat-scan identity checks passed.')


if __name__ == '__main__':
    main()
