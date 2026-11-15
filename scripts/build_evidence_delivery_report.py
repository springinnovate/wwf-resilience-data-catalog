"""Write concise delivery and description-coverage tables from reviewed evidence plans."""
import argparse
import csv
from pathlib import Path
from evidence_sources import load_records, load_pilot_plan, reconciliation_tables

REPO=Path(__file__).resolve().parents[1]


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def build(output_dir):
    records=[dict(r,delivery_prefix='matched') for r in load_records(REPO/'evidence/matched/recipes')]
    pilot=load_pilot_plan(REPO/'evidence/pilot/recipes')['records']
    for record in pilot:
        records.append(dict(record,delivery_prefix='pilot',row_ids=record.get('row_ids') or record['descriptor']['metadata']['annotations']['row_ids']))
    delivery=[]
    other_data={}
    for record in records:
        descriptor=record['descriptor']
        metadata=descriptor['metadata'];kind=record['kind']
        availability='Download only: CRS confirmation needed' if 'CRS confirmation needed' in metadata.get('statuses',[]) else ('Map ready' if kind!='nonspatial' else 'Table/workbook ready')
        # Plans additionally mark catalog-only grids, independent of presentation-label spelling.
        if record.get('readiness','').startswith('Download only'):availability='Download only: CRS confirmation needed'
        folder=record['delivery_prefix']+'/'+record['directory']+'/'
        annotations=metadata.get('annotations',{})
        questions=list(annotations.get('limitations',[]))
        if annotations.get('license_note'):questions.append(annotations['license_note'])
        other_data[record['id']]=[
            (asset.get('metadata',{}).get('title',asset['path']),folder+asset['path'])
            for asset_key,asset in descriptor['assets'].items()
            if asset_key!=descriptor['primary_asset'] and asset['location']=='local'
            and 'data' in asset.get('roles',[])]
        delivery.append(dict(dataset_id=record['id'],dataset=metadata['title'],description_ids='; '.join(record['row_ids']),
            availability=availability,file=folder+record['output_file'],sidecar=folder+record['output_file']+'.eolab.yaml',
            summary=metadata['description'],evidence_type=annotations.get('evidence_type',''),
            dataset_role=annotations.get('dataset_role',''),evidence_summary=folder+'evidence-summary.md',
            full_evidence=folder+'review-context.json',paper_doi='; '.join(p['doi'] for p in metadata['publications']),
            dataset_doi=metadata.get('doi',''),license=metadata.get('license','Needs clarification'),
            remaining_questions=' '.join(questions)))
    delivery.sort(key=lambda r:r['dataset_id'])
    write_csv(output_dir/'datasets.csv',delivery)
    studies={}
    for record in records:
        publications=record['descriptor']['metadata']['publications']
        key=tuple(sorted(publication['doi'] for publication in publications))
        if key not in studies:
            studies[key]=dict(publications=publications,dataset_ids=set())
        studies[key]['dataset_ids'].add(record['id'])
    lines=['# Study findings and available data', '',
           f'{len(delivery)} catalog entries, grouped by the publications they support. '
           'Each description explains the finding and what the supplied file can be used for.', '',
           'File paths are relative to `processed-evidence-data/`; they are not download links. '
           'Open the corresponding EOLab entry to download a file, or find it in the prepared folder. '
           'The adjacent `evidence-summary.md` has Findings, Using these data, Limits and Sources. '
           'Other data lists supporting data files within the same entry. '
           '`datasets.csv` lists primary data files and review records; `study_coverage.csv` checks coverage '
           'of the original sheet descriptions.', '']
    for study in sorted(studies.values(),key=lambda group:group['publications'][0]['title'].casefold()):
        publications=study['publications']
        lines.extend(['## '+'; '.join(publication['title'] for publication in publications), '',
                      'Article: '+', '.join('[doi:'+publication['doi']+'](https://doi.org/'+publication['doi']+')'
                                           for publication in publications)+'.', ''])
        entries=sorted((entry for entry in delivery if entry['dataset_id'] in study['dataset_ids']),
                       key=lambda entry:entry['dataset'].casefold())
        for entry in entries:
            lines.extend(['### '+entry['dataset'], '', entry['summary'], '',
                          entry['availability']+'. Primary data: `'+entry['file']+'`.', '',
                          'Findings and limits: `'+entry['evidence_summary']+'`.', ''])
            if other_data[entry['dataset_id']]:
                lines.extend(['**Other data:**', ''])
                lines.extend('- '+title+': `'+path+'`.'
                             for title,path in other_data[entry['dataset_id']])
                lines.append('')
    (output_dir/'catalog-summaries.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    tables=reconciliation_tables()
    names={r['row_id']:r['dataset'] for r in tables['review_summary']}
    coverage=[]
    for row in tables['matches']:
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
    parser.add_argument('--output-dir',type=Path,default=REPO/'build/evidence/delivery')
    delivery,coverage=build(parser.parse_args().output_dir)
    print(f'{len(delivery)} catalog datasets account for {len(coverage)} matched descriptions and the supporting pilot layer.')
