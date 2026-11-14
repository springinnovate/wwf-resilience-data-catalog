"""Check the expanded delivery with EOLab's real discovery and source readers."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator
from pyproj import CRS
from rasterio.warp import transform_bounds
from shapely.geometry import shape
import yaml

from prepare_evidence_pilot import require,relative_file,sha256,write_json
from prepare_matched_evidence import load_records,evidence_context,read_dicts
from evidence_notes import render_evidence_summary, pilot_evidence_context

REPO=Path(__file__).resolve().parents[1]


def validate(data_root: Path,eolab_source: Path,plan_dir: Path,include_pilot=False) -> tuple[dict,list]:
    require(sys.version_info >= (3,12),'EOLab requires Python 3.12 or newer.')
    data_root=data_root.resolve(strict=True);eolab_source=eolab_source.resolve(strict=True)
    sys.path.insert(0,str(eolab_source/'src'))
    from eolab_app.catalog.descriptor_contract import CatalogDescriptor,descriptor_json_schema
    from eolab_app.catalog.descriptors import publish_descriptor_assets
    from eolab_app.catalog.discovery import FilesystemDatasetDiscovery
    from eolab_app.catalog.handlers import create_default_dataset_handler_registry
    from eolab_app.catalog.public_metadata import copy_public_catalog_metadata
    schema=json.loads((REPO/'evidence/pilot/eolab-item-v1.schema.json').read_text(encoding='utf-8'))
    require(descriptor_json_schema()==schema,'EOLab schema changed; review the new contract.')
    entries={}
    records=load_records(plan_dir)
    matched_root=data_root/'matched' if include_pilot else data_root
    preparation=json.loads((matched_root/'preparation-report.json').read_text(encoding='utf-8'))
    results={r['id']:r for r in preparation['datasets']}
    require(set(results)=={r['id'] for r in records},'Prepared dataset set differs from plans.')
    for record in records:
        context=evidence_context(record);context['preparation_checks']=results[record['id']]['checks']
        entries[record['id']]=(record,matched_root/record['directory'],context,results[record['id']])
    if include_pilot:
        pilot=json.loads((REPO/'evidence/pilot/records.json').read_text(encoding='utf-8'))
        delivered=json.loads((data_root/'pilot/preparation-report.json').read_text(encoding='utf-8'))
        old={r['id']:r for r in delivered['datasets']}
        for record in pilot['records']:
            record['row_ids']=record.get('row_ids') or record['descriptor']['metadata']['annotations']['row_ids']
            entries[record['id']]=(record,data_root/'pilot'/record['directory'],pilot_evidence_context(record),old[record['id']])
    for identifier,(record,folder,context,result) in entries.items():
        declaration=record['descriptor']
        require((folder/'evidence-summary.md').read_text(encoding='utf-8')==render_evidence_summary(record),
                'Linked scientific summary differs from the reviewed plan: '+identifier)
        Draft202012Validator(schema).validate(declaration)
        require(yaml.safe_load((folder/result['sidecar']).read_text(encoding='utf-8'))==declaration,
                'Delivered YAML differs from its plan: '+identifier)
        require(json.loads((folder/'review-context.json').read_text(encoding='utf-8'))==context,
                'Linked full evidence differs from the plan: '+identifier)
        for name,details in result['files'].items():
            path=relative_file(folder,name)
            require(path.stat().st_size==details['bytes'] and sha256(path)==details['sha256'],
                    'Delivered file checksum differs: '+identifier+'/'+name)
    registry=create_default_dataset_handler_registry()
    discovery=FilesystemDatasetDiscovery(data_root,(data_root,),registry)
    def scan():
        candidates,errors=discovery.discover()
        require(not errors,'Discovery failed: '+str(errors))
        require(len(candidates)==len(entries),f'Expected {len(entries)} datasets, found {len(candidates)}.')
        items=[]
        for candidate in candidates:
            items.extend(copy_public_catalog_metadata(publish_descriptor_assets(item))
                         for item in registry.build_items(data_root,candidate))
        require(len(items)==len(entries),'Duplicate or missing STAC Items.')
        return sorted(items,key=lambda item:item['properties']['eolab:descriptor_id'])
    items=scan();require(items==scan(),'Repeat discovery changed metadata or identities.')
    require({i['properties']['eolab:descriptor_id'] for i in items}==set(entries),'Unexpected descriptor IDs.')
    summaries=[]
    for item in items:
        props=item['properties'];identifier=props['eolab:descriptor_id']
        record,folder,context,result=entries[identifier]
        declaration=CatalogDescriptor.model_validate(record['descriptor'])
        require(props['eolab:metadata']==declaration.metadata.model_dump(mode='json'), 'Curated metadata changed.')
        for key,asset in declaration.assets.items():
            public=item['assets'][key]
            require(public['eolab:metadata']==asset.metadata.model_dump(mode='json'),'Asset metadata changed.')
            if asset.location=='local':
                require(public['href'].startswith('/api/catalog/asset?'),'Local asset is not served through catalog identity.')
                require(relative_file(folder,asset.path).is_file(),'Linked asset does not exist.')
            else: require(public['href']==str(asset.href),'External source reference changed.')
        if record['kind']=='nonspatial':
            require(item['geometry'] is None and 'bbox' not in item,'Geometry was invented for a catalog-only item.')
        else:
            require(item['geometry'] is not None,'Spatial item has no footprint.')
            expected=CRS.from_user_input(result['checks']['crs']).to_epsg()
            require(props.get('proj:epsg')==expected,'Native CRS was not retained.')
            expected_bounds=transform_bounds(result['checks']['crs'],'EPSG:4326',*result['checks']['bounds'])
            require(all(abs(a-b)<=1e-7 for a,b in zip(item['bbox'],expected_bounds)), 'Public extent is not the expected WGS84 footprint.')
            require(all(abs(a-b)<=1e-7 for a,b in zip(shape(item['geometry']).bounds,expected_bounds)), 'Public geometry and extent differ.')
        temporal=record['descriptor']['temporal']
        if temporal['mode']=='modified': require(props.get('eolab:time_basis')=='source-modified','Modification date not disclosed.')
        elif temporal['mode']=='interval':
            require(props['datetime'] is None and props['start_datetime']==temporal['start_datetime']
                    and props['end_datetime']==temporal['end_datetime'],'Scientific coverage interval changed.')
        summaries.append(dict(id=identifier,kind=record['kind'],row_ids=record['row_ids'],
                              collection=item['collection'],item_id=item['id'],assets=len(item['assets']),
                              full_evidence_preserved=True,temporal_mode=temporal['mode']))
    encoded=json.dumps(items,ensure_ascii=False)
    require('file://' not in encoded and str(data_root) not in encoded and data_root.as_posix() not in encoded,
            'Public metadata exposes a private source root.')
    matched=read_dicts(REPO/'outputs/matches.csv')
    expected_rows={r['row_id'] for r in matched if r['match_status']=='Matched'}
    represented={row for record,_,_,_ in entries.values() for row in record['row_ids']}
    if include_pilot:require(expected_rows <= represented,'A matched sheet description is unaccounted for.')
    report=dict(eolab_source_revision=subprocess.check_output(['git','-C',str(eolab_source),'rev-parse','HEAD'],text=True).strip(),
                schema_matches=True,discovery_errors=0,repeated_discovery_identical=True,
                all_linked_assets_exist=True,all_delivered_checksums_match=True,full_evidence_preserved=True,
                includes_existing_pilot=include_pilot,matched_descriptions_covered=len(expected_rows & represented),
                database_published=False,datasets=summaries)
    return report,items


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--eolab-source',type=Path,required=True)
    parser.add_argument('--plans',type=Path,default=REPO/'evidence/matched/plans')
    parser.add_argument('--include-pilot',action='store_true')
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--items',type=Path,required=True)
    args=parser.parse_args()
    report,items=validate(args.data_root,args.eolab_source,args.plans,args.include_pilot)
    write_json(args.report,report);write_json(args.items,items)
    print(f"EOLab admitted {len(items)} Items with full linked evidence; repeated discovery is stable.")


if __name__=='__main__':main()
