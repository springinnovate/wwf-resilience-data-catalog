"""Reader views for the study workbook; the reviewed matching data stay separate."""
import collections
import json
import math
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

DISPLAY_STATUS = {
    'Matched': 'Found', 'Partial match': 'Partly found',
    'Related inputs/code only': 'Supporting files only',
    'Different product': 'Different data', 'No local match': 'Not found locally',
    'Unresolved': 'Unclear',
}
STATUS_COLOR = {'Found': 'E2EEDC', 'Partly found': 'FFF0CF',
                'Supporting files only': 'ECEFF1', 'Different data': 'F5DDD6',
                'Not found locally': 'F3E6E3', 'Unclear': 'EAE5F0'}
INK, MUTED, BLUE, LINE = '25343B', '53666E', '1D6084', 'D5DFE3'


def read_presentation(inputs, matches, papers, unmatched):
    records = []
    for name in ['review_rows_001_041.json', 'review_rows_042_078.json']:
        records.extend(json.loads((inputs/'presentation'/name).read_text(encoding='utf-8')))
    by_row = {r['row_id']: r for r in records}
    if len(by_row) != len(records) or set(by_row) != {m['row_id'] for m in matches}:
        raise ValueError('Presentation notes must cover each description exactly once.')
    review = []
    for m in matches:
        r = by_row[m['row_id']]
        for key, limit in [('dataset_label',65), ('found',180), ('attention',190)]:
            if not isinstance(r[key], str) or not r[key].strip() or len(r[key]) > limit:
                raise ValueError(f"Invalid presentation {key}: {m['row_id']}")
        review.append(dict(row_id=m['row_id'], dataset=r['dataset_label'],
            match_result=DISPLAY_STATUS[m['match_status']], what_we_found=r['found'],
            needs_checking=r['attention'], paper=f"{m['paper']} ({m['verified_year']})",
            publisher_link=m['publisher_link']))
    notes = json.loads((inputs/'presentation/other_data_notes.json').read_text(encoding='utf-8'))
    by_paper = {n['paper_id']: n['summary'] for n in notes}
    groups = collections.defaultdict(list)
    for item in unmatched:
        groups[item['paper_id']].append(item)
    if len(notes) != len(by_paper) or set(groups) != set(by_paper):
        raise ValueError('Other-data notes must cover each paper group exactly once.')
    registry = {p['paper_id']: p for p in papers}
    other = []
    for pid, items in sorted(groups.items()):
        p = registry[pid]
        note = by_paper[pid]
        if not isinstance(note, str) or not note.strip() or len(note) > 240:
            raise ValueError(f'Invalid other-data note: {pid}')
        nfiles = sum(x['asset_level']=='standalone_file' for x in items)
        other.append(dict(paper_id=pid, paper=f"{p['verified_title']} ({p['verified_year']})",
            publisher_link=p['publisher_url'], additional_data=note,
            files=nfiles, archive_entries=len(items)-nfiles))
    return review, other


def literal(cell, value):
    cell.value = value
    if isinstance(value, str):
        cell.data_type = 's'
    return cell


def internal(cell, sheet, address='A1'):
    cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"'{sheet}'!{address}")
    cell.font = Font(name='Calibri',size=11,color=BLUE,underline='single')


def external(cell, url):
    cell.hyperlink = url
    cell.font = Font(name='Calibri',size=11,color=BLUE,underline='single')


def wrapped_lines(value, width):
    """Conservative wrap estimate in Excel's Calibri-11 character-width units."""
    def size(s):
        return sum(0.45 if c in ' ilI.,:;!\'|' else 1.5 if c in 'MWmw@%' else
                   1.05 if c.isupper() else 0.82 for c in s)
    capacity = max(8, width-2)
    total = 0
    for paragraph in str(value or '').split('\n'):
        current, lines = 0, 1
        for word in paragraph.split():
            amount = size(word)
            if current and current + 0.45 + amount > capacity:
                lines += 1; current = 0
            if amount > capacity:
                pieces = math.ceil(amount/capacity)
                lines += pieces-1; current = amount-(pieces-1)*capacity
            else:
                current += (0.45 if current else 0)+amount
        total += lines
    return total


def base_sheet(wb, name, widths, *, reference=False):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 90
    ws.sheet_properties.tabColor = 'AFBCC2' if reference else BLUE
    for i, width in enumerate(widths,1):
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.print_options.horizontalCentered = True
    ws.oddFooter.center.text = 'Study data review | Page &P of &N'
    ws.oddFooter.center.size = 9
    return ws


def merged_text(ws, row, text, *, start=1, end=7, size=11, bold=False,
                color=INK, fill=None, height=None):
    ws.merge_cells(start_row=row,start_column=start,end_row=row,end_column=end)
    cell = literal(ws.cell(row,start),text)
    cell.font = Font(name='Calibri',size=size,bold=bold,color=color)
    cell.alignment = Alignment(wrap_text=True,vertical='top')
    if fill:
        for cells in ws.iter_rows(min_row=row,max_row=row,min_col=start,max_col=end):
            for c in cells: c.fill = PatternFill('solid',fgColor=fill)
    width = sum(ws.column_dimensions[get_column_letter(c)].width for c in range(start,end+1))
    ws.row_dimensions[row].height = height or max(23,wrapped_lines(text,width)*(size+4)+8)
    return cell


def heading(ws, title, subtitle, *, end=7):
    merged_text(ws,1,title,end=end,size=20,bold=True,height=34)
    merged_text(ws,2,subtitle,end=end,color=MUTED,height=32)


def table(ws, name, headers, records, widths, *, start=5, statuses=None, minimum=64):
    for i, h in enumerate(headers,1):
        c=literal(ws.cell(start,i),h)
        c.font=Font(name='Calibri',size=11,bold=True,color='FFFFFF')
        c.fill=PatternFill('solid',fgColor=INK)
        c.alignment=Alignment(wrap_text=True,vertical='center')
    ws.row_dimensions[start].height=32
    for offset,values in enumerate(records,1):
        row=start+offset
        maxlines=1
        for col,(value,width) in enumerate(zip(values,widths),1):
            c=literal(ws.cell(row,col),value)
            c.font=Font(name='Calibri',size=11,color=INK)
            c.alignment=Alignment(wrap_text=True,vertical='top')
            c.border=Border(bottom=Side(style='hair',color=LINE))
            if offset%2==0:c.fill=PatternFill('solid',fgColor='F3F6F7')
            maxlines=max(maxlines,wrapped_lines(value,width))
        ws.row_dimensions[row].height=min(390,max(minimum,maxlines*15+12))
        if statuses is not None:
            c=ws.cell(row,3);c.fill=PatternFill('solid',fgColor=STATUS_COLOR[statuses[offset-1]])
            c.font=Font(name='Calibri',size=11,bold=True,color=INK)
    if records:
        t=Table(displayName=name,ref=f'A{start}:{get_column_letter(len(headers))}{start+len(records)}')
        t.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=False)
        ws.add_table(t)
    ws.print_title_rows=f'1:{start}'
    ws.print_area=ws.dimensions


def reference_sheet(wb,name,records,cols=None):
    cols=cols or list(dict.fromkeys(k for r in records for k in r))
    widths=[]
    for key in cols:
        if key in {'description','evidence','limitations','reason','notes'}:width=70
        elif key in {'paper','verified_title','title_as_supplied'}:width=50
        elif key in {'local_files','local_path','relative_path','member_path','outer_path','asset_selectors','selector'}:width=65
        elif 'link' in key or 'url' in key:width=42
        else:width=23
        widths.append(width)
    ws=base_sheet(wb,name,widths,reference=True)
    values=[]
    for record in records:
        line=[]
        for key in cols:
            value=record.get(key,'')
            if value is None:value=''
            if isinstance(value,(list,dict)):value=json.dumps(value,ensure_ascii=False)
            if isinstance(value,str) and len(value)>32000:
                raise ValueError(f'Workbook cell exceeds display limit: {name} / {key}; split the record before publishing.')
            line.append(value)
        values.append(line)
    table(ws,'Ref'+name.replace(' ',''),cols,values,widths,start=1,minimum=48)
    ws.freeze_panes='B2'
    # These keys are available for joins but do not need to lead a reading view.
    hide={'asset_id','parent_file_id','link_id','paper_id','source_line_start','source_line_end',
          'sha256','metadata_status','modified_utc'}
    if name=='Match records':hide|={'local_files','asset_selectors','title_as_supplied','year_as_supplied','primary_asset_link_count','all_asset_link_count','review_needed','paper_verification_notes'}
    for col,key in enumerate(cols,1):
        if key in hide and name!='Source sheet':
            ws.column_dimensions[get_column_letter(col)].hidden=True
        for row in range(2,len(records)+2):
            c=ws.cell(row,col)
            if key in {'publisher_link','publisher_url'} and c.value:external(c,c.value)
    visible=[i for i,k in enumerate(cols) if k not in hide or name=='Source sheet']
    for index,line in enumerate(values,2):
        lines=max((wrapped_lines(line[i],widths[i]) for i in visible),default=1)
        ws.row_dimensions[index].height=min(260,max(48,lines*15+12))
    return ws


def build_workbook(matches,papers,links,allfiles,archives,source,unmatched,summary,review,other,snapshot):
    wb=Workbook();wb.remove(wb.active)
    main_widths=[5,27,18,36,38,33,9]
    unlisted_view=sorted(unmatched,key=lambda r:(r['paper_id'],r['local_path'],r['selector']))
    ws=base_sheet(wb,'Study review',main_widths)
    reviewed=date.fromisoformat(snapshot['snapshot_date'])
    date_label=f'{reviewed.day} {reviewed.strftime("%B")} {reviewed.year}'
    heading(ws,'Study data review',
            f'{len(matches)} descriptions from {len(papers)} papers | Files reviewed {date_label} | Paper titles link to the published articles.')
    counts=collections.Counter(r['match_result'] for r in review)
    merged_text(ws,3,'  |  '.join(f'{label}: {counts[label]}' for label in DISPLAY_STATUS.values() if counts[label]),
                size=11,height=24)
    for start,end,label,target in [(1,2,'How to read this workbook','Guide'),(3,4,'Other available data','Other available data'),(5,7,'Full file list and evidence','File links')]:
        internal(merged_text(ws,4,label,start=start,end=end,height=25),target)
    values=[[int(r['row_id'][4:]),r['dataset'],r['match_result'],r['what_we_found'],r['needs_checking'],r['paper'],'Open'] for r in review]
    table(ws,'StudyReview',['No.','Data described','Match','What we found','What needs checking','Paper','Details'],values,main_widths,statuses=[r['match_result'] for r in review])
    ws.freeze_panes='C6'
    for index,r in enumerate(review):
        row=index+6
        external(ws.cell(row,6),r['publisher_link'])
        internal(ws.cell(row,7),'Details',f'A{4+index*11}')

    ow=[48,67,10,16,10]
    ws=base_sheet(wb,'Other available data',ow)
    heading(ws,'Other available data','These files are present, but are not matched to a description in the supplied sheet. They may still be useful.',end=5)
    merged_text(ws,3,f'{len(other)} papers | {sum(r["files"] for r in other)} files + {sum(r["archive_entries"] for r in other)} archived members/layers. Counts include copies; they are not counts of distinct datasets.',end=5,color=MUTED,height=28)
    internal(merged_text(ws,4,'Back to study review',end=5,height=25),'Study review')
    values=[[r['paper'],r['additional_data'],r['files'],r['archive_entries'],'Open'] for r in other]
    table(ws,'OtherAvailable',['Paper','Additional data','Files','Archive entries','Details'],values,ow)
    ws.freeze_panes='B6'
    for i,r in enumerate(other,6):
        external(ws.cell(i,1),r['publisher_link'])
        first=next(n+2 for n,item in enumerate(unlisted_view) if item['paper_id']==r['paper_id'])
        internal(ws.cell(i,5),'Other data files',f'A{first}')

    ws=base_sheet(wb,'Details',[24,26,18,31,31,25,10])
    heading(ws,'Description and evidence','Original descriptions are preserved below. Use the links to inspect exact files or return to the short review.')
    ws.freeze_panes='B3'
    for i,(m,r) in enumerate(zip(matches,review)):
        start=4+i*11
        c=merged_text(ws,start,f'{i+1:02d}  {r["dataset"]}',size=14,bold=True,fill='E9EFF2',height=32)
        internal(c,'Study review',f'A{i+6}')
        c.font=Font(name='Calibri',size=14,bold=True,color=BLUE,underline='single')
        first_link=next((n+2 for n,l in enumerate(links) if l['row_id']==m['row_id']),None)
        file_label=(f'Open file links for description {i+1} ({m["all_asset_link_count"]} links, including supporting files).' if first_link else 'No local file links identified for this description.')
        fields=[('Paper',r['paper']),('Match',r['match_result']),('Original description',m['description']),
                ('What we found',r['what_we_found']),('Main check',r['needs_checking']),
                ('Evidence',m['evidence']),('Limitations',m['limitations']),('Files',file_label),
                ('Source reference',f'{m["row_id"]} | {m["paper_id"]} | Open the original source-sheet record (paste lines {m["source_line_start"]}-{m["source_line_end"]}).')]
        for j,(label,value) in enumerate(fields,1):
            row=start+j
            c=literal(ws.cell(row,1),label);c.font=Font(name='Calibri',size=11,bold=True,color=MUTED)
            c.alignment=Alignment(wrap_text=True,vertical='top')
            merged_text(ws,row,value,start=2,end=7)
        external(ws.cell(start+1,2),m['publisher_link'])
        ws.cell(start+2,2).fill=PatternFill('solid',fgColor=STATUS_COLOR[r['match_result']])
        if first_link:internal(ws.cell(start+8,2),'File links',f'A{first_link}')
        internal(ws.cell(start+9,2),'Source sheet',f'A{i+2}')
        ws.row_dimensions[start+10].height=14
    ws.print_area=ws.dimensions

    ws=base_sheet(wb,'Guide',[29,31,22,25,23,24,18])
    heading(ws,'How to read this workbook','Start with Study review. It compares the descriptions in the supplied sheet with the files available locally.')
    merged_text(ws,4,'Read a row in this order: data described → match → what we found → what needs checking.',bold=True)
    merged_text(ws,5,'Use the column filters to narrow the list. Click a paper title for the article, or Open for the original description and detailed evidence.')
    merged_text(ws,7,'What the match labels mean',size=14,bold=True)
    meanings=[('Found','The described data were identified. Read “What needs checking” for remaining limits.'),
              ('Partly found','Only some of the requested data, or a processed version, were found.'),
              ('Supporting files only','Inputs, scripts or documentation are present; the requested output was not found.'),
              ('Different data','The candidate file measures something different from the description.'),
              ('Not found locally','No corresponding files were found in this inventory. They may be available elsewhere.'),
              ('Unclear','There is a candidate file, but there is not enough evidence to identify it confidently.')]
    for row,(label,meaning) in enumerate(meanings,8):
        c=literal(ws.cell(row,1),label);c.font=Font(name='Calibri',size=11,bold=True,color=INK)
        c.alignment=Alignment(wrap_text=True,vertical='top');c.fill=PatternFill('solid',fgColor=STATUS_COLOR[label])
        merged_text(ws,row,meaning,start=2,end=7,height=30)
    merged_text(ws,15,'Two different questions',size=14,bold=True)
    merged_text(ws,16,'Study review asks whether we have the data described in the sheet. Other available data lists data we do have that are outside those descriptions, or still need identification.')
    merged_text(ws,18,'Where to check the evidence',size=14,bold=True)
    destinations=[('Details','Original description, full matching evidence and limitations for each numbered entry.'),
                  ('File links','Exact paths, archive members, variables and workbook sheets. Filter row_id to see every link for an entry.'),
                  ('Other data files','All additional/unidentified files and archive entries, grouped by paper. Filter the paper title to narrow the list. Counts include copies.'),
                  ('Paper references','Article DOIs, publisher links, source URLs and publication-year notes.'),
                  ('File inventory','Every indexed local file, including its purpose and size.'),
                  ('Archive contents','Members of ZIP/RAR files and geodatabase layers.'),
                  ('Source sheet','The original pasted columns, unchanged.'),
                  ('Match records','The complete matching table used by the rebuild scripts.')]
    for row,(target,explanation) in enumerate(destinations,19):
        internal(literal(ws.cell(row,1),target),target)
        merged_text(ws,row,explanation,start=2,end=7,height=36)
    merged_text(ws,28,'Useful limits',size=14,bold=True)
    merged_text(ws,29,'A match identifies a data product; it does not certify every measurement or make it ready for STAC. Dates, coordinates, units, source permissions and publishing locations still need review.')
    merged_text(ws,30,'Paths refer to the external study-data folder. A ! separates an archive from a file inside it. These paths are not download links. Counts are file/member entries, including copies and supporting files, rather than distinct datasets.')
    merged_text(ws,31,f'No. follows the order of the {len(matches)} descriptions in the pasted sheet; it is not the row number in the original Excel file. Some descriptions share files or overlap. Link counts do not imply independent datasets.')
    merged_text(ws,32,'To suggest a correction, cite the description number and filename. Review text is shortened for reading; Details and Source sheet preserve the original wording. Corrections should go into the saved inputs before rebuilding.')
    merged_text(ws,33,'The grey reference tabs contain the supporting tables. Internal ID columns are hidden to keep the file information visible; unhide columns if needed, or use the complete CSV exports.')
    ws.freeze_panes='A3';ws.print_area='A1:G33'

    for name,records,cols in [
        ('Paper references',papers,None),('File links',links,None),('Other data files',unlisted_view,None),
        ('File inventory',allfiles,None),('Archive contents',archives,None),
        ('Source sheet',source['rows'],['row_id','paper_id']+source['columns']),('Match records',matches,None)]:
        reference_sheet(wb,name,records,cols)
    # Keep source evidence visible; only technical join-key columns are collapsed.
    wb.active=0
    for sh in wb:
        sh.sheet_view.tabSelected=False
    wb.worksheets[0].sheet_view.tabSelected=True
    return wb
