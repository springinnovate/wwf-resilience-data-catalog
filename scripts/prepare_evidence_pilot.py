"""Prepare three reviewed evidence datasets without changing the source collection.

The records file defines exact inputs, transformations and EOLab metadata. Outputs
are published together only after source, content and sidecar checks pass.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
from importlib.metadata import version
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Any

import fiona
from jsonschema import Draft202012Validator
import numpy as np
from pyproj import CRS
import rasterio
from rasterio.shutil import copy as raster_copy
from shapely.geometry import shape
import yaml

REPO = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    """Reject an input or output that violates the reviewed preparation plan."""
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    """Return a file checksum without loading the entire file into memory."""
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def relative_file(root: Path, name: str) -> Path:
    """Resolve a portable record path within its declared filesystem root."""
    relative = PurePosixPath(name)
    require(bool(name) and not relative.is_absolute() and '..' not in relative.parts
            and ':' not in name and '\\' not in name, 'Expected a confined relative path.')
    result = (root / name).resolve()
    require(result.is_relative_to(root.resolve()), 'File escapes its declared root.')
    return result


def write_json(path: Path, value: Any) -> None:
    """Write readable UTF-8 metadata with stable key order and no non-JSON numbers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def prepare_raster(source: Path, target: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Create a lossless COG and verify every base-resolution value and mask."""
    raster_copy(str(source), str(target), driver='COG', compress='DEFLATE',
                predictor='FLOATING_POINT', blocksize=512, overview_resampling='NEAREST')
    shutil.copystat(source, target)
    with rasterio.open(source) as original, rasterio.open(target) as result:
        require(original.crs is not None, 'Raster source CRS is missing.')
        for name in ['crs', 'transform', 'width', 'height', 'count', 'dtypes',
                     'nodatavals', 'scales', 'offsets']:
            require(getattr(original, name) == getattr(result, name), f'Raster {name} changed.')
        require(np.array_equal(original.read(), result.read(), equal_nan=True),
                'Raster base-resolution values changed.')
        require(np.array_equal(original.read_masks(), result.read_masks()), 'Raster mask changed.')
        require(result.tags(ns='IMAGE_STRUCTURE').get('LAYOUT') == 'COG', 'Output is not a COG.')
        values = result.read(1, masked=True)
        require(int(values.count()) == record['expected_valid_pixels'], 'Raster valid-cell count differs.')
        return dict(crs=result.crs.to_string(), width=result.width, height=result.height,
                    bands=result.count, dtype=result.dtypes[0], nodata=result.nodata,
                    valid_pixels=int(values.count()), minimum=float(values.min()),
                    maximum=float(values.max()), bounds=list(result.bounds),
                    overviews=result.overviews(1), base_values_identical=True, masks_identical=True,
                    transformation='Lossless COG encoding; nearest-neighbour display overviews; no reprojection.')


def prepare_vector(source: Path, target: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Export the selected point source to GeoPackage with exact attributes and geometry."""
    with fiona.open(source) as original:
        require(bool(original.crs), 'Vector source CRS is missing.')
        schema = dict(original.schema)
        require(len(original) == record['expected_features'], 'Vector source feature count differs.')
        with fiona.open(target, 'w', driver='GPKG', layer=record['output_layer'],
                        schema=schema, crs_wkt=original.crs_wkt, encoding='UTF-8') as result:
            for feature in original:
                require(feature.geometry is not None and shape(feature.geometry).is_valid,
                        'Vector source has missing or invalid geometry.')
                result.write(feature)
    shutil.copystat(source, target)
    with fiona.open(source) as original, fiona.open(target, layer=record['output_layer']) as result:
        require(len(original) == len(result), 'Vector feature count changed.')
        require(CRS(original.crs) == CRS(result.crs), 'Vector CRS changed.')
        require(list(original.schema['properties']) == list(result.schema['properties']),
                'Vector attribute names or order changed.')
        for left, right in zip(original, result, strict=True):
            require(dict(left.properties) == dict(right.properties), 'Vector attributes changed.')
            require(shape(left.geometry).equals_exact(shape(right.geometry), 0),
                    'Vector coordinates changed.')
            require(shape(right.geometry).is_valid, 'Output vector has invalid geometry.')
        return dict(features=len(result), fields=len(result.schema['properties']),
                    crs=CRS(result.crs).to_string(), geometry=result.schema['geometry'],
                    bounds=list(result.bounds), source_schema=schema, output_schema=dict(result.schema),
                    attributes_identical=True, coordinates_identical=True, invalid_geometries=0,
                    transformation='Shapefile to GeoPackage; no reprojection, geometry repair or field renaming.')


def prepare_table(source: Path, target: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Select the twelve 2023 monthly flux records without rounding their values."""
    with source.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == record['expected_source_rows'], 'Source table row count differs.')
    selected = [row for row in rows if row['Year'] == str(record['year'])]
    require(len(selected) == 12 and [int(row['Month']) for row in selected] == list(range(1, 13)),
            'Selected year must contain each month exactly once in calendar order.')
    fields = record['columns']
    for row in selected:
        month = int(row['Month'])
        require(row['Time'] == f"{record['year']}-{month:02d}-{calendar.monthrange(record['year'], month)[1]}",
                'Unexpected monthly time label.')
        require(all(row[field] != '' for field in fields), 'Selected table value is missing.')
    with target.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        writer.writerows(selected)
    with target.open(encoding='utf-8', newline='') as handle:
        actual = list(csv.DictReader(handle))
    require(actual == [{key: row[key] for key in fields} for row in selected], 'Table values changed.')
    require(sha256(target) == record['expected_output_sha256'], 'Table encoding/content differs from reviewed output.')
    return dict(source_rows=len(rows), rows=len(actual), columns=fields, year=record['year'],
                selected_strings_identical=True, geometry=None,
                transformation='Select Year=2023 and six named columns; preserve original numeric strings.')


def prepare(source_root: Path, output_root: Path, records_path: Path,
            schema_path: Path) -> dict[str, Any]:
    """Publish a new pilot directory after checking all three reviewed products.

    Existing destinations are never overwritten. Temporary files are confined to
    a fresh sibling staging directory, so a failed check cannot replace data.
    """
    source_root = source_root.resolve(strict=True)
    output_root = output_root.resolve()
    require(not output_root.exists(), 'Output directory already exists; choose a new destination.')
    require(not output_root.is_relative_to(source_root), 'Output must be outside the original data collection.')
    require(not output_root.is_relative_to(REPO), 'Scientific outputs must remain outside the Git repository.')
    plan = json.loads(records_path.read_text(encoding='utf-8'))
    validator = Draft202012Validator(json.loads(schema_path.read_text(encoding='utf-8')))
    records = plan['records']
    require(sorted(r['kind'] for r in records) == ['nonspatial', 'raster', 'vector'], 'Pilot needs exactly three kinds.')
    require(len({r['id'] for r in records}) == 3, 'Pilot identifiers are not unique.')
    for record in records:
        validator.validate(record['descriptor'])
        for name, checksum in record['source_files'].items():
            require(sha256(relative_file(source_root, name)) == checksum,
                    f"Source checksum differs for {record['id']}: {name}")
    report = dict(eolab_contract=plan['eolab_contract'], records_sha256=sha256(records_path),
                  runtime={name: version(name) for name in ['numpy', 'rasterio', 'fiona', 'pyproj', 'shapely', 'PyYAML', 'jsonschema']},
                  gdal_version=rasterio.__gdal_version__, datasets=[])
    output_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.evidence-pilot-', dir=output_root.parent) as temporary:
        staging_root = Path(temporary).resolve()
        require(staging_root.is_relative_to(output_root.parent), 'Unexpected staging location.')
        staged = staging_root / 'ready'
        staged.mkdir()
        for record in records:
            folder = relative_file(staged, record['directory'])
            folder.mkdir()
            source = relative_file(source_root, record['primary_source'])
            target = relative_file(folder, record['output_file'])
            builder = {'raster': prepare_raster, 'vector': prepare_vector, 'nonspatial': prepare_table}[record['kind']]
            checks = builder(source, target, record)
            for attachment in record['attachments']:
                destination = relative_file(folder, attachment['path'])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(relative_file(source_root, attachment['source']), destination)
                require(sha256(destination) == record['source_files'][attachment['source']], 'Attachment copy changed.')
            write_json(folder / 'review-context.json', record['review_context'])
            sidecar = folder / (record['output_file'] + '.eolab.yaml')
            sidecar.write_text(yaml.safe_dump(record['descriptor'], allow_unicode=True, sort_keys=False,
                                               width=100), encoding='utf-8', newline='\n')
            validator.validate(yaml.safe_load(sidecar.read_text(encoding='utf-8')))
            files = {p.relative_to(folder).as_posix(): dict(sha256=sha256(p), bytes=p.stat().st_size)
                     for p in sorted(folder.rglob('*')) if p.is_file()}
            report['datasets'].append(dict(id=record['id'], kind=record['kind'], directory=record['directory'],
                                           primary=record['output_file'], sidecar=sidecar.name,
                                           source_files=record['source_files'], files=files, checks=checks))
        write_json(staged / 'preparation-report.json', report)
        staged.rename(output_root)
    return report


def write_summary(path: Path, report: dict[str, Any], records_path: Path) -> None:
    """Write the three-row review table with paths relative to the pilot output."""
    records = {record['id']: record for record in json.loads(records_path.read_text(encoding='utf-8'))['records']}
    rows = []
    for result in report['datasets']:
        record = records[result['id']]
        metadata = record['descriptor']['metadata']
        checks = result['checks']
        rows.append(dict(dataset=metadata['title'], kind=result['kind'],
                         file=result['directory'] + '/' + result['primary'],
                         sidecar=result['directory'] + '/' + result['sidecar'],
                         paper_doi=metadata['publications'][0]['doi'], dataset_doi=metadata['doi'],
                         crs=checks.get('crs', 'Not spatial'),
                         coverage=checks.get('valid_pixels', checks.get('features', checks.get('rows'))),
                         coverage_unit={'raster': 'valid pixels', 'vector': 'points', 'nonspatial': 'monthly rows'}[result['kind']],
                         checks='Source-preservation checks passed; see separate EOLab admission report',
                         temporal_mode=record['descriptor']['temporal']['mode'],
                         limitation=metadata['annotations']['limitations'][0]))
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Read private filesystem roots from CLI arguments, never from committed metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--output-root', required=True, type=Path)
    parser.add_argument('--records', type=Path, default=REPO/'evidence/pilot/records.json')
    parser.add_argument('--schema', type=Path, default=REPO/'evidence/pilot/eolab-item-v1.schema.json')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--sidecar-dir', type=Path)
    args = parser.parse_args()
    report = prepare(args.source_root, args.output_root, args.records, args.schema)
    if args.report:
        write_json(args.report, report)
        write_summary(args.report.with_suffix('.csv'), report, args.records)
    if args.sidecar_dir:
        args.sidecar_dir.mkdir(parents=True, exist_ok=True)
        for dataset in report['datasets']:
            shutil.copyfile(args.output_root/dataset['directory']/dataset['sidecar'],
                            args.sidecar_dir/dataset['sidecar'])
    for dataset in report['datasets']:
        print(f"Prepared {dataset['kind']}: {dataset['id']}")


if __name__ == '__main__':
    main()
