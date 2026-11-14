"""Build the auditable sheet-to-local-data reconciliation (no source changes).

Usage: python scripts/build_reconciliation.py [--input-dir data] [--output-dir build/reconciliation]
Requires openpyxl. Inputs are the preserved sheet, inventory and reviewed decisions.
This exports reconciliation evidence, not STAC or a scientific validation result.
"""
import argparse, collections, csv, hashlib, html, json, zipfile
from pathlib import Path
from datetime import datetime, timezone
import os
os.environ['OPENPYXL_LXML']='False'
from openpyxl import load_workbook
from workbook_presentation import read_presentation, build_workbook

parser=argparse.ArgumentParser(description=__doc__)
repo=Path(__file__).resolve().parents[1]
parser.add_argument('--input-dir',type=Path,default=repo/'data')
parser.add_argument('--output-dir',type=Path,default=repo/'build/reconciliation')
args=parser.parse_args()
inputs=args.input_dir.resolve(); out=args.output_dir.resolve()
if out==inputs or out in inputs.parents or inputs in out.parents:
    parser.error('Input and output directories must not overlap.')
out.mkdir(parents=True,exist_ok=True)
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
snapshot=read(inputs/'snapshot.json')
source=read(inputs/'source/parsed_sheet.json')
papers=read(inputs/'decisions/papers_verified.json'); paper_by={x['paper_id']:x for x in papers}
inv=read(inputs/'source/file_manifest.json')
if hashlib.sha256((inputs/'source/source_sheet.tsv').read_bytes()).hexdigest()!=source['source']['source_sha256']:
    raise ValueError('The source paste differs from the recorded source-sheet SHA256.')
substantive={x['relative_path']:x for x in inv['files'] if x['role_guess']!='os_artifact'}
decisions=[read(inputs/'decisions'/n) for n in ['matching_tables.json','matching_spatial.json','matching_hydropower.json','matching_root.json']]
rows_dec=[r for d in decisions for r in d['rows']]
files_dec=[f for d in decisions for f in d['files']]
assert len(files_dec)==len(substantive)==snapshot['substantive_files']
assert len({f['relative_path'] for f in files_dec})==len(files_dec), 'duplicate file decisions'
assert set(f['relative_path'] for f in files_dec)==set(substantive), 'missing/extra file decisions'
assert len({int(r['row_id']) for r in rows_dec})==len(rows_dec)==len(snapshot['assessed_row_ids'])
assert sorted(int(r['row_id']) for r in rows_dec)==snapshot['assessed_row_ids']
assert len(source['rows'])==snapshot['source_records']
assert len(paper_by)==len(papers)==snapshot['paper_count']
assert len(inv['files'])==snapshot['total_files']
assert set(snapshot['assessed_row_ids']).isdisjoint(snapshot['no_local_match_row_ids'])
assert set(snapshot['assessed_row_ids'])|set(snapshot['no_local_match_row_ids'])==set(range(1,len(source['rows'])+1))
by_row={int(r['row_id']):r for r in rows_dec}
by_file={f['relative_path']:f for f in files_dec}
folder_paper={r['candidate_folder']:r['paper_id'] for r in source['rows'] if r.get('candidate_folder')}
assert len(folder_paper)==snapshot['study_folders']

def text(v):
    if v is None: return ''
    if isinstance(v,(list,dict)): return json.dumps(v,ensure_ascii=False)
    return v
def join(v):
    if isinstance(v,list): return '\n'.join(str(x) for x in v)
    return str(v or '')
def rid(n): return f'row-{int(n):03d}'
def aid(path,selector=''): return 'asset-'+hashlib.sha256((path+'|'+selector).encode()).hexdigest()[:14]
status_names={'matched':'Matched','partial':'Partial match','not_located':'Related inputs/code only',
              'related_only':'Related inputs/code only','unresolved':'Unresolved','different_product':'Different product',
              'no_local_match':'No local match'}
definitions=[
 ('Matched','The described product was identified using file contents, metadata or explicit generating-code provenance. Does not certify completeness, scientific accuracy or STAC readiness.'),
 ('Partial match','Some requested content is present, or a processed/filtered/alternate-format version is present; coverage or metric differences are stated.'),
 ('Related inputs/code only','Same-study inputs, code or documentation were found; the requested output itself was not located.'),
 ('Different product','A plausible local candidate was inspected but represents a different measured quantity/product.'),
 ('Unresolved','Local candidate exists but available evidence is insufficient to establish the requested identity.'),
 ('No local match','No local study package/product was identified in this inventory; does not imply that it is unavailable online.'),
 ('Unmatched local data','Scientific files/layers not assigned to any supplied dataset description. Their paper may still be known. Inputs, code, figures, metadata and sidecars are classified separately.'),
 ('File versus dataset','Counts refer to physical files or separately indexed archived members/layers, not unique independent datasets. Copies and shapefile components are retained; archive payloads are not added to filesystem byte totals.'),
 ('Archive locator','The outer path is a real local file. ! separates archive members/nested archives. A selector identifies a workbook sheet, variable or geodatabase layer; it is not a filesystem path.'),
 ('Row identifiers','row-001 etc are parsed data-record numbers in the supplied paste, excluding banner/header. They are not original Excel row numbers or folder-name suffixes.'),
]

archives=[]
raw_archives=[a for d in decisions for a in d.get('archived_assets',[])]+read(inputs/'decisions/archive_assets_root.json')
for a in raw_archives:
    path=a.get('archive_path',a.get('outer_path')); member=a.get('member_path',a.get('member'))
    assert path in substantive,(path,'missing archive')
    selector=a.get('selector',''); locator=path+'!'+member
    p=paper_by[folder_paper[path.split('/')[0]]]
    archives.append(dict(asset_id=aid(locator,selector),paper_id=p['paper_id'],paper=p['verified_title'],publisher_link=p['publisher_url'],
        outer_path=path,member_path=member,selector=selector,asset_level=a.get('asset_level','archive_member'),
        disposition=a['disposition'],row_ids='; '.join(rid(n) for n in a.get('row_ids',[])),
        reason=a.get('reason',''),size_bytes=a.get('size_bytes',a.get('uncompressed_bytes','')),
        inspection=a.get('inspection','Inspected inventory, headers, metadata or relevant source code; see decision JSON.'),
        code_provenance=join(a.get('code_provenance',[]))))
assert len({(a['outer_path'],a['member_path'],a['selector']) for a in archives})==len(archives),'duplicate archive records'

# Every non-directory ZIP member must be represented. RAR physical components and
# logical layers are additionally present. Hash-identical test.rar uses DATAnull's inventory.
with (inputs/'source/archive_members.csv').open(encoding='utf-8-sig',newline='') as f:
    zip_expected={(a['archive_path'],a['member_path']) for a in csv.DictReader(f) if a['is_directory']!='True'}
archive_keys={(a['outer_path'],a['member_path']) for a in archives}
assert zip_expected <= archive_keys, ('unclassified ZIP members',zip_expected-archive_keys)

links=[]; seen=set(); links_by_key={}
relationship_from={'matched_data':'described_asset','partial_data':'partial_or_processed',
 'related_input':'related_input','code':'code','documentation':'documentation','figure':'figure','sidecar':'sidecar',
 'archive_container':'archive_container','unmatched_data':'different_product','unresolved_data':'unresolved'}
def link(n,path,selector,relationship,reason,origin,indexed_asset_id=None):
    key=(n,path,selector,relationship)
    if key in seen:
        # A reviewed row can already name an exact archive selector. Upgrade
        # that relationship to the indexed member when its inventory arrives.
        if indexed_asset_id:
            existing=links_by_key[key]
            existing['asset_id']=indexed_asset_id
            if origin not in existing['decision_source']:
                existing['decision_source']+=' + '+origin
        return
    seen.add(key)
    s=source['rows'][n-1]; p=paper_by[s['paper_id']]
    links.append(dict(row_id=rid(n),paper_id=s['paper_id'],asset_id=indexed_asset_id or aid(path),
        parent_file_id=aid(path),link_id='link-'+hashlib.sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest()[:14],
        local_path=path,selector=selector,relationship=relationship,evidence=reason,decision_source=origin,
        publisher_link=p['publisher_url']))
    links_by_key[key]=links[-1]

for n,d in by_row.items():
    for a in d.get('assets',[]):
        path=a['relative_path']; assert path in substantive,('row asset missing',n,path)
        link(n,path,a.get('selector',''),a.get('relationship','partial_or_processed'),join(a.get('evidence',d.get('evidence',''))),'row decision')
for f in files_dec:
    for n in f.get('row_ids',[]):
        # Keep precise selectors rather than adding duplicate whole-file matches.
        if any(k[0]==n and k[1]==f['relative_path'] for k in seen): continue
        link(n,f['relative_path'],'',relationship_from[f['disposition']],f.get('reason',''),'file disposition')
for a in archives:
    for r in a['row_ids'].split('; '):
        if not r:continue
        n=int(r[4:]);path=a['outer_path'];sel=a['member_path']+(' / '+a['selector'] if a['selector'] else '')
        link(n,path,sel,relationship_from[a['disposition']],a['reason'],'archive member/layer disposition',a['asset_id'])
links.sort(key=lambda l:(l['row_id'],l['local_path'],l['selector'],l['relationship']))
links_by=collections.defaultdict(list)
for l in links:links_by[l['row_id']].append(l)

matches=[]
for s in source['rows']:
    n=s['parsed_row_number'];p=paper_by[s['paper_id']]
    d=by_row.get(n,dict(status='no_local_match',evidence='No corresponding local study package or dataset was identified in the indexed folders.',
        limitations='The sheet-provided repository/download references are preserved in SourceSheet for subsequent retrieval; no new datasets were downloaded.'))
    status=status_names[d['status']]
    ls=links_by[s['row_id']]
    primary=[l for l in ls if l['relationship'] in ['described_asset','partial_or_processed','different_product','unresolved']]
    shown=primary or [l for l in ls if l['relationship'] in ['related_input','code','documentation','archive_container']]
    local=sorted(set(l['local_path'] for l in shown))
    selector_lines=sorted(set(l['local_path']+' :: '+l['selector'] for l in primary if l['selector']))
    matches.append(dict(row_id=s['row_id'],description=s['dataset_description'],paper=p['verified_title'],
        publisher_link=p['publisher_url'],local_files='\n'.join(local),match_status=status,
        asset_selectors='\n'.join(selector_lines),evidence=join(d.get('evidence','')),limitations=join(d.get('limitations','')),
        paper_id=s['paper_id'],article_doi=p['article_doi'],verified_year=p['verified_year'],
        title_as_supplied=s['title'],year_as_supplied=s['year'],candidate_folder=s.get('candidate_folder',''),
        primary_asset_link_count=len(primary),all_asset_link_count=len(ls),review_needed=status!='Matched',
        paper_verification_notes=join(p.get('notes',[])),source_line_start=s['source_line_start'],source_line_end=s['source_line_end']))

allfiles=[]
for path,m in sorted(substantive.items()):
    f=by_file[path]; pid=folder_paper[m['study_folder']]; p=paper_by[pid]
    allfiles.append(dict(asset_id=aid(path),relative_path=path,study_folder=m['study_folder'],paper_id=pid,paper=p['verified_title'],
        publisher_link=p['publisher_url'],disposition=f['disposition'],row_ids='; '.join(rid(n) for n in f.get('row_ids',[])),
        reason=f.get('reason',''),size_bytes=m['size_bytes'],extension=m['extension'],modified_utc=m['modified_utc'],
        metadata_status=m.get('metadata_status',''),sha256=m.get('sha256','')))
unmatched=[]
for f in allfiles:
    if f['disposition'] in ['unmatched_data','unresolved_data']:
        unmatched.append(dict(asset_id=f['asset_id'],description=f['reason'],paper=f['paper'],publisher_link=f['publisher_link'],
            local_path=f['relative_path'],selector='',match_status='Unmatched local data' if f['disposition']=='unmatched_data' else 'Unresolved local data',
            paper_id=f['paper_id'],asset_level='standalone_file',disposition=f['disposition'],row_ids=f['row_ids'],size_bytes=f['size_bytes']))
for a in archives:
    if a['disposition'] in ['unmatched_data','unresolved_data']:
        unmatched.append(dict(asset_id=a['asset_id'],description=a['reason'],paper=a['paper'],publisher_link=a['publisher_link'],
            local_path=a['outer_path']+'!'+a['member_path'],selector=a['selector'],match_status='Unmatched local data' if a['disposition']=='unmatched_data' else 'Unresolved local data',
            paper_id=a['paper_id'],asset_level=a['asset_level'],disposition=a['disposition'],row_ids=a['row_ids'],size_bytes=a['size_bytes']))

unmatched_sheet=[m for m in matches if m['match_status'] not in ['Matched','Partial match']]
review=[m for m in matches if m['review_needed']]
registry_ids={a['asset_id'] for a in allfiles+archives}
file_ids={a['asset_id'] for a in allfiles}
assert len(registry_ids)==len(allfiles)+len(archives),'asset ID collision'
assert all(l['asset_id'] in registry_ids and l['parent_file_id'] in file_ids for l in links),'dangling asset link'
assert len({l['link_id'] for l in links})==len(links),'link ID collision'
summary=dict(generated_utc=snapshot['report_timestamp_utc'],source_sha256=source['source']['source_sha256'],
    sheet_rows=len(matches),papers=len(papers),publisher_links_verified=len(papers),study_folders=len(folder_paper),
    standalone_files=len(allfiles),os_artifacts_excluded=len(inv['files'])-len(allfiles),
    status_counts=dict(collections.Counter(m['match_status'] for m in matches)),
    file_disposition_counts=dict(collections.Counter(f['disposition'] for f in allfiles)),
    archived_assets=len(archives),zip_members_classified=len(zip_expected),asset_links=len(links),
    unmatched_sheet_entries=len(unmatched_sheet),review_gap_entries=len(review),
    unmatched_local_entries=len(unmatched),unmatched_local_by_level=dict(collections.Counter(u['asset_level'] for u in unmatched)),
    scope='All supplied sheet rows and substantive local files classified. Scientific matching is evidence-based and conservative, not a complete scientific validation or STAC catalog. Article identifiers are distinct from download/repository identifiers.')

def writecsv(name,records,cols=None):
    cols=cols or list(dict.fromkeys(k for r in records for k in r))
    with (out/name).open('w',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=cols,extrasaction='ignore');w.writeheader()
        for r in records:w.writerow({k:text(r.get(k,'')) for k in cols})
for name,records in [('matches',matches),('asset_links',links),('papers',papers),('all_local_files',allfiles),
                     ('archive_assets',archives),('unmatched_sheet_entries',unmatched_sheet),('review_gaps',review),('unmatched_local_data',unmatched)]:
    writecsv(name+'.csv',records)
(out/'reconciliation.json').write_text(json.dumps(dict(summary=summary,matches=matches,papers=papers,asset_links=links,
    files=allfiles,archive_assets=archives,unmatched_local_data=unmatched),ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

review_rows, other_rows = read_presentation(inputs, matches, papers, unmatched)
writecsv('review_summary.csv', review_rows)
writecsv('other_data_summary.csv', other_rows)
wb = build_workbook(matches, papers, links, allfiles, archives, source, unmatched, summary, review_rows, other_rows, snapshot)
truncated=[]
wb.properties.title='WWF resilience data: study, paper and local-asset reconciliation'
wb.properties.creator='richpsharp'
wb.properties.description='All supplied descriptions and local files accounted for, with evidence and unresolved gaps.'
stamp=datetime.fromisoformat(snapshot['report_timestamp_utc']).astimezone(timezone.utc).replace(tzinfo=None)
wb.properties.created=stamp;wb.properties.modified=stamp
target=out/'study_data_matches.xlsx';wb.save(target)
with zipfile.ZipFile(target) as archive_in:
    package={name:archive_in.read(name) for name in archive_in.namelist()}
# et_xmlfile writes worksheet temporary files in text mode: Windows inserts
# CRLF into embedded text where Linux writes LF. XML readers normalize literal
# line endings to LF anyway. Preserve character references (e.g. &#13;) and
# normalize only literal CRLF so the package is reproducible across platforms.
package={name:payload.replace(b'\r\n',b'\n') if name.endswith(('.xml','.rels')) else payload
         for name,payload in package.items()}
import re
fixed_time=stamp.isoformat(timespec='seconds')+'Z'
package['docProps/core.xml']=re.sub(rb'(<dcterms:modified[^>]*>).*?(</dcterms:modified>)',lambda m:m[1]+fixed_time.encode()+m[2],package['docProps/core.xml'])
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive_out:
    for name,payload in sorted(package.items()):
        entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
        archive_out.writestr(entry,payload)

check=load_workbook(target,read_only=False,data_only=False)
assert check['Match records'].max_row==len(matches)+1 and check['Paper references'].max_row==len(papers)+1
assert check['File inventory'].max_row==len(allfiles)+1
assert all(check['Match records'].cell(i+2,2).value==m['description'] for i,m in enumerate(matches))
assert all(check['Match records'].cell(i+2,4).hyperlink.target==m['publisher_link'] for i,m in enumerate(matches))
assert not any(c.data_type=='f' for ws in check for row in ws for c in row), 'unexpected formula'
check.close()
qa=dict(sheet_rows_unique=len({m['row_id'] for m in matches})==snapshot['source_records'],papers_unique=len(paper_by)==snapshot['paper_count'],
    all_files_accounted=True,all_zip_members_accounted=True,workbook_reopened=True,
    all_asset_foreign_keys_resolve=True,all_parent_file_foreign_keys_resolve=True,unique_link_ids=True,
    descriptions_preserved=True,publisher_hyperlinks_checked=True,source_text_not_executed_as_formulas=True,
    shortened_workbook_cells=truncated)
(out/'validation.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

esc=lambda s:html.escape(str(s or ''))
trs=[]
for m in matches:
    pathlist='<br>'.join(esc(x) for x in m['local_files'].splitlines()) or 'None identified'
    trs.append('<tr>'+''.join(['<td>'+esc(m['row_id'])+'</td>','<td>'+esc(m['description'])+'</td>',
       '<td><a href="'+esc(m['publisher_link'])+'">'+esc(m['paper'])+'</a></td>',
       '<td>'+esc(m['match_status'])+'</td>','<td>'+pathlist+'</td>',
       '<td>'+esc(m['evidence'])+'<p><strong>Limitations:</strong> '+esc(m['limitations'])+'</p></td>'])+'</tr>')
stats='; '.join(f'{k}: {v}' for k,v in summary['status_counts'].items())
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Study-data reconciliation</title>
<style>body{font:15px/1.5 system-ui,sans-serif;color:#173838;margin:30px;background:#f7faf9}h1{font-size:29px}a{color:#056b78}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;border:1px solid #cddcda;vertical-align:top;overflow-wrap:anywhere}th{background:#183d3d;color:white;position:sticky;top:0}td:nth-child(2){min-width:270px}td:nth-child(3){min-width:190px}td:nth-child(5){min-width:260px}td:nth-child(6){min-width:350px}input{padding:10px;width:50%;margin:15px 0}nav a{margin-right:20px}.scroll{overflow:auto;max-height:78vh}</style>
<h1>Study descriptions, papers and local data</h1>'''
page+=f'<p>{len(matches)} descriptions · {len(papers)} verified papers · {len(allfiles):,} substantive files.</p><p>{esc(stats)}</p>'
page+='<nav><a href="study_data_matches.xlsx">Excel workbook</a><a href="matches.csv">Matches CSV</a><a href="unmatched_sheet_entries.csv">Unmatched sheet entries</a><a href="unmatched_local_data.csv">Unmatched local data</a><a href="asset_links.csv">Full asset links and selectors</a></nav>'
page+='<p>Every source row and substantive file is accounted for. Partial and unmatched results preserve gaps; a matching paper or folder alone does not establish a dataset match. Archive members and exact selectors are expanded in the workbook. This is not yet a STAC catalog.</p>'
page+='<label>Filter rows <input id="search" placeholder="Paper, description, status or filename"></label><span id="count">78 rows</span><div class="scroll"><table><thead><tr><th>Row</th><th>Description</th><th>Paper / publisher</th><th>Status</th><th>Local files</th><th>Evidence and limitations</th></tr></thead><tbody>'+''.join(trs)+'</tbody></table></div>'
page+='''<script>const q=document.getElementById('search'),rs=[...document.querySelectorAll('tbody tr')];q.addEventListener('input',()=>{let n=0;for(const r of rs){const show=r.textContent.toLowerCase().includes(q.value.toLowerCase());r.hidden=!show;if(show)n++;}document.getElementById('count').textContent=n+' rows';});</script></html>'''
(out/'matching_summary.html').write_text(page,encoding='utf-8',newline='\n')
print(f"Built {target}: {len(matches)} descriptions, {len(papers)} papers, {len(allfiles)} files; all embedded checks passed.")
