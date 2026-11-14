"""Prepare the remaining matched evidence with concise EOLab metadata.

Plans describe source selection; linked review contexts preserve original matching
records and all preparation checks. Inputs are never modified. New deliveries
are built in a fresh directory and admitted separately before publication.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import csv
from datetime import date, datetime
from decimal import Decimal
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

import fiona
from jsonschema import Draft202012Validator
import numpy as np
from openpyxl import load_workbook
from pyproj import CRS
import rasterio
from rasterio.shutil import copy as raster_copy
from rasterio.windows import Window
from shapely import get_num_coordinates, is_valid_reason, make_valid, to_wkb
from shapely.geometry import MultiPolygon, mapping, shape
import yaml

from prepare_evidence_pilot import require, relative_file, sha256, write_json
from evidence_notes import write_evidence_summary

REPO = Path(__file__).resolve().parents[1]
SCHEMA = REPO / 'evidence/pilot/eolab-item-v1.schema.json'


def load_records(plan_dir: Path) -> list[dict]:
    records = []
    for path in sorted(plan_dir.glob('*.json')):
        plan = json.loads(path.read_text(encoding='utf-8'))
        records.extend(plan if isinstance(plan, list) else plan['records'])
    require(bool(records), 'No evidence plans found.')
    require(len({r['id'] for r in records}) == len(records), 'Duplicate dataset ID.')
    require(len({r['directory'] for r in records}) == len(records), 'Duplicate dataset directory.')
    return records


def read_csv(path: Path, encoding='utf-8-sig', delimiter=',') -> list[list[str]]:
    with path.open(encoding=encoding, newline='') as handle:
        return list(csv.reader(handle, delimiter=delimiter))


def read_dicts(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def literal(value) -> str:
    if value is None:
        return ''
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def table_rows(source_root: Path, operation: dict) -> tuple[list[str], list[list[str]], dict]:
    """Select table cells explicitly, retaining strings unless a decimal conversion is declared."""
    kind = operation['type']
    if kind == 'xlsx_table':
        path = relative_file(source_root, operation['source'])
        book = load_workbook(path, data_only=False, read_only=True)
        rows = []
        iterator = None
        try:
            sheet = book[operation['sheet']]
            iterator = sheet.iter_rows(min_row=operation.get('header_row', 1))
            for cells in iterator:
                require(not any(cell.data_type == 'f' for cell in cells),
                        'Formula cells need an explicit cached-value policy or a byte-preserved workbook.')
                rows.append([literal(cell.value) for cell in cells])
        finally:
            if iterator is not None and hasattr(iterator, 'close'):
                iterator.close()
            book.close()
        while rows and not any(rows[-1]):
            rows.pop()
        headers, values = rows[0], rows[1:]
        details = dict(source_sheet=operation['sheet'], header_row=operation.get('header_row', 1))
    elif kind == 'csv_concat':
        headers = None
        values = []
        counts = {}
        for entry in operation['sources']:
            rows = read_csv(relative_file(source_root, entry['path']),
                            operation.get('encoding', 'utf-8-sig'), operation.get('delimiter', ','))
            require(headers is None or rows[0] == headers, 'Concatenated source headers differ.')
            headers = rows[0]
            selected = rows[1:]
            if operation.get('filter'):
                selector = operation['filter']
                require(headers.count(selector['column']) == 1, 'Filter column name is ambiguous.')
                index = headers.index(selector['column'])
                selected = [row for row in selected if row[index].endswith(selector['endswith'])]
            require('land_management' not in headers, 'New scenario column would overwrite a source column.')
            counts[entry['path']] = len(selected)
            values.extend([row + [entry['land_management']] for row in selected])
        headers = headers + ['land_management']
        details = dict(source_row_counts=counts, selection=operation.get('filter'),
                       added_column='land_management from the source filename')
    else:
        rows = read_csv(relative_file(source_root, operation['source']),
                        operation.get('encoding', 'utf-8-sig'), operation.get('delimiter', ','))
        header_row = operation.get('header_row', 1)
        headers, values = rows[header_row - 1], rows[header_row:]
        details = dict(source_encoding=operation.get('encoding', 'utf-8-sig'),
                       source_delimiter=operation.get('delimiter', ','))
    require(headers and all(len(row) == len(headers) for row in values), 'Table contains ragged rows.')
    if operation.get('columns'):
        require(all(headers.count(name) == 1 for name in operation['columns']), 'Selected source column name is ambiguous.')
        indices = [headers.index(name) for name in operation['columns']]
        headers = [headers[i] for i in indices]
        values = [[row[i] for i in indices] for row in values]
        details['selected_columns'] = headers
    if operation.get('column_indices') is not None:
        indices = operation['column_indices']
        headers = [headers[i] for i in indices]
        values = [[row[i] for i in indices] for row in values]
        details['source_column_indices_zero_based'] = indices
    if operation.get('output_headers'):
        require(len(headers) == len(operation['output_headers']), 'Output header count differs.')
        details['source_headers'] = headers
        headers = operation['output_headers']
    require(len(headers) == len(set(headers)), 'Duplicate headers need explicit position-based names.')
    for column in operation.get('decimal_columns', []):
        index = headers.index(column)
        for row in values:
            if row[index].strip():
                original = row[index]
                converted = original.replace(',', '.')
                require(Decimal(converted).is_finite(), 'Non-finite decimal in selected column.')
                row[index] = converted
        details.setdefault('decimal_comma_normalized_columns', []).append(column)
    return headers, values, details


def prepare_table(source_root: Path, target: Path, record: dict) -> dict:
    headers, rows, details = table_rows(source_root, record['operation'])
    if 'expected_rows' in record:
        require(len(rows) == record['expected_rows'], 'Table row count differs from the reviewed selection.')
    with target.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(headers)
        writer.writerows(rows)
    require(read_csv(target, encoding='utf-8') == [headers, *rows], 'Table cells changed during encoding.')
    return dict(rows=len(rows), columns=headers, selected_cells_preserved=True, encoding='UTF-8', **details)


@contextmanager
def raster_source(source_root: Path, operation: dict):
    source = relative_file(source_root, operation['source'])
    member = operation.get('member') or operation.get('archive_member')
    if not member:
        yield source
    else:
        with tempfile.TemporaryDirectory(prefix='evidence-raster-') as temporary:
            target = Path(temporary) / 'source.tif'
            with zipfile.ZipFile(source) as archive, archive.open(member) as handle, target.open('wb') as out:
                shutil.copyfileobj(handle, out)
            yield target


def prepare_raster(source_root: Path, target: Path, record: dict) -> dict:
    """Encode a native grid as a COG and check every source value and mask in blocks."""
    with raster_source(source_root, record['operation']) as source:
        with rasterio.open(source) as original:
            require(original.crs is not None, 'Raster CRS is unverified; do not assign a guessed CRS.')
        raster_copy(str(source), str(target), driver='COG', compress='DEFLATE',
                    blocksize=512, overview_resampling='NEAREST')
        counts = []
        ranges = []
        with rasterio.open(source) as original, rasterio.open(target) as output:
            for key in ['crs','transform','width','height','count','dtypes','scales','offsets','descriptions','units']:
                require(getattr(original,key) == getattr(output,key), f'Raster {key} changed.')
            require(original.nodata == output.nodata or (original.nodata is not None and output.nodata is not None
                    and np.isnan(original.nodata) and np.isnan(output.nodata)), 'Raster nodata changed.')
            require(output.tags(ns='IMAGE_STRUCTURE').get('LAYOUT') == 'COG', 'Output is not a COG.')
            for band in range(1, original.count + 1):
                count, minimum, maximum = 0, None, None
                for y in range(0,original.height,512):
                    for x in range(0,original.width,512):
                        window=Window(x,y,min(512,original.width-x),min(512,original.height-y))
                        a,b=original.read(band,window=window),output.read(band,window=window)
                        mask=original.read_masks(band,window=window)
                        require(np.array_equal(a,b,equal_nan=True), 'Raster values changed.')
                        require(np.array_equal(mask,output.read_masks(band,window=window)), 'Raster masks changed.')
                        valid=a[mask != 0]; count+=int(valid.size)
                        if valid.size:
                            low,high=float(valid.min()),float(valid.max())
                            minimum=low if minimum is None else min(minimum,low)
                            maximum=high if maximum is None else max(maximum,high)
                counts.append(count);ranges.append([minimum,maximum])
            return dict(crs=output.crs.to_string(), width=output.width,height=output.height,bands=output.count,
                        dtypes=list(output.dtypes), nodata=output.nodata, bounds=list(output.bounds),
                        valid_pixels=counts,value_ranges=ranges,base_values_identical=True,masks_identical=True,
                        overviews=output.overviews(1),transformation='Lossless COG; native grid and CRS retained.')


def prepare_vector(source_root: Path, target: Path, record: dict) -> dict:
    """Export a selected geodatabase layer, recording conservative validity repair per feature."""
    operation=record['operation']
    archive=relative_file(source_root,operation['source'])
    executable=shutil.which('7z')
    if not executable and os.environ.get('ProgramFiles'):
        executable=str(Path(os.environ['ProgramFiles'])/'7-Zip'/'7z.exe')
    require(executable and Path(executable).is_file(), 'Install 7-Zip to read the source RAR archive.')
    with tempfile.TemporaryDirectory(prefix='evidence-vector-') as temporary:
        extraction=Path(temporary)
        listing=subprocess.check_output([executable,'l','-slt',str(archive)],text=True)
        names=[line[7:] for line in listing.split('----------',1)[1].splitlines() if line.startswith('Path = ')]
        for name in names:
            relative_file(extraction,name.replace('\\','/'))
        subprocess.run([executable,'x','-y','-o'+str(extraction),str(archive)],check=True,stdout=subprocess.DEVNULL)
        source=relative_file(extraction,operation['geodatabase'])
        expected=[];changes=[]
        with fiona.open(source,layer=operation['layer'],encoding='UTF-8') as original:
            require(bool(original.crs), 'Vector source CRS is missing.')
            schema=dict(original.schema);schema['geometry']='MultiPolygon'
            source_crs=CRS(original.crs)
            with fiona.open(target,'w',driver='GPKG',layer=operation['output_layer'],schema=schema,
                            crs_wkt=original.crs_wkt,encoding='UTF-8') as output:
                for feature in original:
                    require(feature.geometry is not None, 'Missing source geometry.')
                    geometry=shape(feature.geometry)
                    require(not geometry.is_empty, 'Empty source geometry.')
                    valid=geometry.is_valid
                    result=geometry if valid else make_valid(geometry,method='structure',keep_collapsed=False)
                    require(result.geom_type in ['Polygon','MultiPolygon'] and result.is_valid and not result.is_empty,
                            'Geometry repair did not produce a valid polygon.')
                    if result.geom_type=='Polygon': result=MultiPolygon([result])
                    require(geometry.area > 0, 'Zero-area source polygon needs manual review.')
                    area_change=abs(result.area-geometry.area)/abs(geometry.area)
                    bounds_change=max(abs(a-b) for a,b in zip(geometry.bounds,result.bounds))
                    require(area_change <= 1e-8 and bounds_change <= 1e-8,
                            'Geometry repair changed area or extent materially; manual review required.')
                    if valid:
                        comparable=MultiPolygon([geometry]) if geometry.geom_type=='Polygon' else geometry
                        require(result.equals_exact(comparable,0), 'Valid source geometry changed.')
                    properties=dict(feature.properties)
                    output.write({'geometry':mapping(result),'properties':properties})
                    expected.append((properties,to_wkb(result)))
                    if not valid:
                        changes.append(dict(source_id=feature['id'],reason=is_valid_reason(geometry),
                                            original_vertices=int(get_num_coordinates(geometry)),
                                            prepared_vertices=int(get_num_coordinates(result)),
                                            relative_area_change=area_change,max_bounds_change_degrees=bounds_change))
        with fiona.open(target,layer=operation['output_layer']) as output:
            require(len(output)==len(expected)==record['expected_features'], 'Vector feature count changed.')
            require(CRS(output.crs)==source_crs,'Vector CRS changed.')
            for feature,(properties,wkb) in zip(output,expected,strict=True):
                require(dict(feature.properties)==properties, 'Vector attribute values changed.')
                geometry=shape(feature.geometry)
                require(to_wkb(geometry)==wkb and geometry.is_valid,'Export changed repaired geometry.')
            return dict(features=len(output),fields=list(output.schema['properties']),crs=source_crs.to_string(),
                        bounds=list(output.bounds),attributes_identical=True,invalid_output_geometries=0,
                        repaired_features=len(changes),repair_method='Shapely make_valid structure; keep_collapsed=False',
                        repair_details=changes,source_reader=f'Fiona {fiona.__version__}; GDAL {fiona.__gdal_version__}')


def evidence_context(record: dict) -> dict:
    """Retain all frozen source rows and crosswalks alongside new evidence and checks."""
    row_ids=set(record['row_ids'])
    rows=json.loads((REPO/'data/source/parsed_sheet.json').read_text(encoding='utf-8'))['rows']
    matches=read_dicts(REPO/'outputs/matches.csv')
    links=read_dicts(REPO/'outputs/asset_links.csv')
    papers=read_dicts(REPO/'outputs/papers.csv')
    selected=[r for r in rows if r['row_id'] in row_ids]
    require({r['row_id'] for r in selected}==row_ids,'Unknown sheet row.')
    paper_ids={r['paper_id'] for r in selected}
    return dict(note='Original sheet and matching records are historical evidence. The curated evidence and adjacent YAML describe this prepared product.',
                source_base='evidence_data',source_sheet_rows=selected,
                reconciliation_snapshot=[r for r in matches if r['row_id'] in row_ids],
                paper_references=[r for r in papers if r['paper_id'] in paper_ids],
                asset_links=[r for r in links if r['row_id'] in row_ids],
                curated_evidence=record.get('review_context',{}),source_files=record['source_files'],
                operation=record['operation'], evidence_summary=record.get('evidence_summary',{}),
                metadata_history=record.get('metadata_history',[]))


def prepare(source_root: Path,output_root: Path,plan_dir: Path,sidecar_dir: Path|None=None) -> dict:
    source_root=source_root.resolve(strict=True);output_root=output_root.resolve()
    require(not output_root.exists(),'Output already exists; choose a fresh directory.')
    require(not output_root.is_relative_to(source_root),'Output must be outside the source collection.')
    require(not output_root.is_relative_to(REPO) or output_root.is_relative_to(REPO/'build'),
            'Only ignored build storage may hold scientific outputs inside the repository.')
    records=load_records(plan_dir)
    validator=Draft202012Validator(json.loads(SCHEMA.read_text(encoding='utf-8')))
    for record in records:
        validator.validate(record['descriptor'])
        require(record['descriptor']['id']==record['id'],'Descriptor ID differs.')
        require(record['descriptor']['kind']==record['kind'],'Descriptor kind differs.')
        require(record['descriptor']['assets'][record['descriptor']['primary_asset']]['path']==record['output_file'],
                'Primary asset does not match output filename.')
        operation=record['operation']
        operation_sources={operation['source']} if operation.get('source') else {s['path'] for s in operation['sources']}
        bundle_sources={f['source'] for b in record.get('bundles',[]) for f in b['files']}
        required_sources=operation_sources | {a['source'] for a in record.get('attachments',[])} | bundle_sources
        for bundle in record.get('bundles',[]):
            relative_file(output_root,bundle['path'])
            names=[f['path'] for f in bundle['files']]
            require(len(names)==len(set(names)), 'Archive member names must be unique.')
            for name in names:
                relative_file(output_root,name)
        require(required_sources <= set(record['source_files']), 'Every operation and attachment source must have a checksum.')
        for name,checksum in record['source_files'].items():
            require(sha256(relative_file(source_root,name))==checksum,f'Source checksum changed: {name}')
    output_root.parent.mkdir(parents=True,exist_ok=True)
    report=dict(plans={p.name:sha256(p) for p in sorted(plan_dir.glob('*.json'))},
                runtime={name:version(name) for name in ['numpy','rasterio','fiona','shapely','pyproj','openpyxl','PyYAML','jsonschema']},
                datasets=[])
    with tempfile.TemporaryDirectory(prefix='.matched-evidence-',dir=output_root.parent) as temporary:
        staged=Path(temporary)/'ready';staged.mkdir()
        for record in records:
            folder=relative_file(staged,record['directory']);folder.mkdir(parents=True)
            target=relative_file(folder,record['output_file']);target.parent.mkdir(parents=True,exist_ok=True)
            operation=record['operation'];kind=operation['type']
            if kind=='copy':
                shutil.copy2(relative_file(source_root,operation['source']),target)
                require(sha256(target)==record['source_files'][operation['source']], 'Source copy changed.')
                checks=dict(source_bytes_identical=True)
            elif kind=='raster': checks=prepare_raster(source_root,target,record)
            elif kind=='vector_gdb_archive': checks=prepare_vector(source_root,target,record)
            else:
                require(kind in ['xlsx_table','csv_table','csv_concat'],'Unknown preparation operation.')
                checks=prepare_table(source_root,target,record)
            timestamp_source=operation.get('source') or operation['sources'][0]['path']
            shutil.copystat(relative_file(source_root,timestamp_source),target)
            for attachment in record.get('attachments',[]):
                destination=relative_file(folder,attachment['path']);destination.parent.mkdir(parents=True,exist_ok=True)
                require(destination != target, 'Attachment collides with prepared data.')
                shutil.copy2(relative_file(source_root,attachment['source']),destination)
                require(sha256(destination)==record['source_files'][attachment['source']],'Attachment changed.')
            for bundle in record.get('bundles',[]):
                destination=relative_file(folder,bundle['path']);destination.parent.mkdir(parents=True,exist_ok=True)
                require(not destination.exists(), 'Archive collides with a prepared file.')
                members={}
                with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                    for entry in bundle['files']:
                        content=relative_file(source_root,entry['source']).read_bytes()
                        expected=record['source_files'][entry['source']]
                        require(hashlib.sha256(content).hexdigest()==expected,'Archive source changed.')
                        info=zipfile.ZipInfo(entry['path'],date_time=(1980,1,1,0,0,0))
                        info.compress_type=zipfile.ZIP_DEFLATED
                        archive.writestr(info,content)
                        members[entry['path']]=dict(source=entry['source'],sha256=expected,bytes=len(content))
                with zipfile.ZipFile(destination) as archive:
                    require(set(archive.namelist())==set(members),'Archive member set changed.')
                    for name,details in members.items():
                        require(hashlib.sha256(archive.read(name)).hexdigest()==details['sha256'],'Archive member bytes changed.')
                checks.setdefault('supporting_archives',{})[bundle['path']]=members
            context=evidence_context(record);context['preparation_checks']=checks
            write_json(folder/'review-context.json',context)
            write_evidence_summary(folder,record)
            sidecar=folder/(record['output_file']+'.eolab.yaml')
            sidecar.write_text(yaml.safe_dump(record['descriptor'],sort_keys=False,allow_unicode=True,width=100),encoding='utf-8',newline='\n')
            for asset in record['descriptor']['assets'].values():
                if asset['location']=='local':
                    require(relative_file(folder,asset['path']).is_file(),'Declared asset missing.')
            files={p.relative_to(folder).as_posix():dict(sha256=sha256(p),bytes=p.stat().st_size)
                   for p in sorted(folder.rglob('*')) if p.is_file()}
            report['datasets'].append(dict(id=record['id'],directory=record['directory'],kind=record['kind'],
                row_ids=record['row_ids'],readiness=record.get('readiness','map-ready' if record['kind']!='nonspatial' else 'table-ready'),
                primary=record['output_file'],sidecar=sidecar.name,source_files=record['source_files'],checks=checks,files=files))
            print('Prepared '+record['id'],flush=True)
        write_json(staged/'preparation-report.json',report)
        staged.rename(output_root)
    if sidecar_dir:
        sidecar_dir.mkdir(parents=True,exist_ok=True)
        for result in report['datasets']:
            shutil.copyfile(output_root/result['directory']/result['sidecar'],sidecar_dir/result['sidecar'])
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    parser.add_argument('--plans',type=Path,default=REPO/'evidence/matched/plans')
    parser.add_argument('--report',type=Path)
    parser.add_argument('--sidecar-dir',type=Path)
    args=parser.parse_args()
    report=prepare(args.source_root,args.output_root,args.plans,args.sidecar_dir)
    if args.report:write_json(args.report,report)


if __name__=='__main__':main()
