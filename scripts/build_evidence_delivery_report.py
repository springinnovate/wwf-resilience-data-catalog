"""Write concise delivery and description-coverage tables from reviewed evidence plans."""
import argparse
import csv
from pathlib import Path
import json

REPO=Path(__file__).resolve().parents[1]


def read_dicts(path):
    with path.open(encoding='utf-8-sig',newline='') as handle:
        return list(csv.DictReader(handle))


def load_records(plan_dir):
    return [record for path in sorted(plan_dir.glob('*.json'))
            for record in json.loads(path.read_text(encoding='utf-8'))['records']]


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def build(output_dir):
    records=[dict(r,delivery_prefix='matched') for r in load_records(REPO/'evidence/matched/plans')]
    pilot=json.loads((REPO/'evidence/pilot/records.json').read_text(encoding='utf-8'))['records']
    for record in pilot:
        records.append(dict(record,delivery_prefix='pilot',row_ids=record.get('row_ids') or record['descriptor']['metadata']['annotations']['row_ids']))
    delivery=[]
    for record in records:
        metadata=record['descriptor']['metadata'];kind=record['kind']
        availability='Download only: CRS confirmation needed' if 'CRS confirmation needed' in metadata.get('statuses',[]) else ('Map ready' if kind!='nonspatial' else 'Table/workbook ready')
        # Plans additionally mark catalog-only grids, independent of presentation-label spelling.
        if record.get('readiness','').startswith('Download only'):availability='Download only: CRS confirmation needed'
        folder=record['delivery_prefix']+'/'+record['directory']+'/'
        annotations=metadata.get('annotations',{})
        questions=list(annotations.get('limitations',[]))
        if annotations.get('license_note'):questions.append(annotations['license_note'])
        delivery.append(dict(dataset_id=record['id'],dataset=metadata['title'],description_ids='; '.join(record['row_ids']),
            availability=availability,file=folder+record['output_file'],sidecar=folder+record['output_file']+'.eolab.yaml',
            summary=metadata['description'],evidence_type=annotations.get('evidence_type',''),
            dataset_role=annotations.get('dataset_role',''),evidence_summary=folder+'evidence-summary.md',
            full_evidence=folder+'review-context.json',paper_doi='; '.join(p['doi'] for p in metadata['publications']),
            dataset_doi=metadata.get('doi',''),license=metadata.get('license','Needs clarification'),
            remaining_questions=' '.join(questions)))
    delivery.sort(key=lambda r:r['dataset_id'])
    write_csv(output_dir/'datasets.csv',delivery)
    lines=['# Catalog summaries', '',
           'Public descriptions for the prepared collection. Paper findings and the role of each supplied file are distinguished below.', '']
    for entry in delivery:
        lines.extend(['## '+entry['dataset'], '', '**Evidence:** '+entry['evidence_type']+'. '
                      +'**Dataset role:** '+entry['dataset_role']+'.', '', entry['summary'], '',
                      'Availability: '+entry['availability']+'.', '',
                      'Paper: '+', '.join('[doi:'+doi+'](https://doi.org/'+doi+')' for doi in entry['paper_doi'].split('; '))+'.', ''])
    (output_dir/'catalog-summaries.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    names={r['row_id']:r['dataset'] for r in read_dicts(REPO/'outputs/review_summary.csv')}
    coverage=[]
    for row in read_dicts(REPO/'outputs/matches.csv'):
        if row['match_status']!='Matched':continue
        linked=[d for d in delivery if row['row_id'] in d['description_ids'].split('; ')]
        if not linked:raise ValueError('Unrepresented matched description: '+row['row_id'])
        coverage.append(dict(description_id=row['row_id'],description=names[row['row_id']],
            availability='; '.join(dict.fromkeys(d['availability'] for d in linked)),
            prepared_files='; '.join(d['file'] for d in linked),
            paper=row['paper'],publisher_link=row['publisher_link'],
            remaining_questions=' '.join(dict.fromkeys(d['remaining_questions'] for d in linked))))
    write_csv(output_dir/'study_coverage.csv',coverage)
    return delivery,coverage


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=REPO/'evidence/matched/reports')
    delivery,coverage=build(parser.parse_args().output_dir)
    print(f'{len(delivery)} catalog datasets account for {len(coverage)} matched descriptions and the supporting pilot layer.')
