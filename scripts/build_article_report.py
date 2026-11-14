"""Rebuild the article-download table from the recorded search; no network requests."""
import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import posixpath
import re
from urllib.parse import quote, urlsplit
import zipfile

os.environ['OPENPYXL_LXML'] = 'False'
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from workbook_presentation import base_sheet, merged_text, table, external

REPO = Path(__file__).resolve().parents[1]
COLORS = {'Downloaded': 'E2EEDC', 'Download blocked': 'FFF0CF', 'No open copy found': 'F3E6E3'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_records(input_path, verify_local):
    snapshot = json.loads(input_path.read_text(encoding='utf-8'))
    directory = snapshot['local_directory']
    require(directory and not urlsplit(directory).scheme and not PureWindowsPath(directory).anchor
            and not PurePosixPath(directory).is_absolute() and '\\' not in directory
            and '..' not in PurePosixPath(directory).parts,
            'Article directory must be a repository-relative path with forward slashes.')
    with (REPO / 'outputs/papers.csv').open(encoding='utf-8-sig', newline='') as handle:
        papers = {r['paper_id']: r for r in csv.DictReader(handle)}
    records = snapshot['records']
    require(len(records) == len(papers) and {r['paper_id'] for r in records} == set(papers),
            'Article search must account for each paper exactly once.')
    for record in records:
        pid = record['paper_id']
        require(record['status'] in COLORS, f'Unknown article status: {pid}')
        require(record['source_name'] and record['reader_note'] and len(record['reader_note']) <= 250,
                f'Missing or overlong reader note: {pid}')
        require(record['attempts'], f'No search evidence: {pid}')
        for url in [record['found_url'], record['download_url'], record['human_url']] + [a['url'] for a in record['attempts']]:
            if url:
                require(urlsplit(url).scheme in {'https', 'http'}, f'Invalid source URL: {pid}')
                require('cookies_not_supported' not in url and 'validate.perfdrive.com' not in url,
                        f'Transient access-challenge URL: {pid}')
        if record['status'] == 'Downloaded':
            filename = record['filename']
            require(filename.startswith(pid + '_') and PureWindowsPath(filename).name == filename
                    and filename.lower().endswith('.pdf'), f'Invalid local article filename: {pid}')
            require(re.fullmatch('[0-9a-f]{64}', record['sha256']) and record['pages'] >= 2
                    and record['size_bytes'] > 0 and record['download_url'], f'Incomplete download evidence: {pid}')
            if verify_local:
                path = REPO / snapshot['local_directory'] / filename
                body = path.read_bytes()
                require(body.startswith(b'%PDF-') and len(body) == record['size_bytes']
                        and hashlib.sha256(body).hexdigest() == record['sha256'], f'Local PDF changed: {filename}')
        else:
            require(not record['filename'] and not record['sha256'] and record['human_url'],
                    f'Blocked/missing paper needs a human follow-up link and no saved-file claim: {pid}')
    return snapshot, papers


def export_records(snapshot, papers):
    rows = []
    for record in sorted(snapshot['records'], key=lambda r: r['paper_id']):
        paper = papers[record['paper_id']]
        local = str(PurePosixPath(snapshot['local_directory']) / record['filename']) if record['filename'] else ''
        rows.append(dict(paper_id=record['paper_id'], paper=paper['verified_title'], year=paper['verified_year'],
                         status=record['status'], where_found=record['source_name'], source_url=record['found_url'],
                         local_file=local, human_download_link=record['human_url'], copy_version=record['copy_version'],
                         notes=record['reader_note'], doi=paper['article_doi'], publisher_url=paper['publisher_url']))
    return rows


def workbook_file_link(local_file):
    # Exports retain the canonical reports/ layout, including comparison builds.
    return quote(posixpath.relpath(local_file, start='reports'), safe='/')


def save_workbook(path, rows, snapshot):
    workbook = Workbook()
    workbook.remove(workbook.active)
    widths = [5, 39, 18, 22, 28, 21, 37]
    sheet = base_sheet(workbook, 'Articles', widths)
    counts = Counter(r['status'] for r in rows)
    checked = datetime.fromisoformat(snapshot['search_date'])
    merged_text(sheet, 1, 'Article downloads', size=20, bold=True, height=34)
    merged_text(sheet, 2, f'{counts["Downloaded"]} downloaded | {counts["Download blocked"]} download blocked | '
                f'{counts["No open copy found"]} no open copy found | Checked {checked.day} {checked:%B %Y}', height=25)
    merged_text(sheet, 3, 'Article folder (relative to repository): ' + snapshot['local_directory'], height=25)
    merged_text(sheet, 4, 'Paper titles link to publishers. PDF links are relative to reports/. CSV file paths are relative to the repository. Try download may require manual access.', height=30)
    headers = ['No.', 'Paper', 'Result', 'Where found', 'Local file', 'If not downloaded', 'Notes about this copy / next step']
    values = []
    for record in rows:
        values.append([int(record['paper_id'][-3:]), record['paper'] + ' (' + record['year'] + ')', record['status'],
                       record['where_found'], 'Open PDF' if record['local_file'] else 'Not downloaded',
                       '' if record['local_file'] else 'Try publisher access' if record['status'] == 'No open copy found' else 'Try download',
                       record['notes']])
    table(sheet, 'ArticleDownloads', headers, values, widths)
    sheet.row_dimensions[5].height = 42
    sheet.freeze_panes = 'C6'
    for number, record in enumerate(rows, 6):
        external(sheet.cell(number, 2), record['publisher_url'])
        external(sheet.cell(number, 4), record['source_url'])
        if record['local_file']:
            external(sheet.cell(number, 5), workbook_file_link(record['local_file']))
        else:
            external(sheet.cell(number, 6), record['human_download_link'])
        cell = sheet.cell(number, 3)
        cell.fill = PatternFill('solid', fgColor=COLORS[record['status']])
        cell.font = Font(name='Calibri', size=11, bold=True, color='25343B')
    timestamp = datetime.fromisoformat(snapshot['report_timestamp_utc']).replace(tzinfo=None)
    workbook.properties.creator = 'richpsharp'
    workbook.properties.title = 'Article downloads for the WWF resilience study review'
    workbook.properties.created = timestamp
    workbook.properties.modified = timestamp
    buffer = io.BytesIO()
    workbook.save(buffer)
    workbook.close()
    # Fixed package metadata and normalized XML make Windows/Linux rebuilds agree.
    with zipfile.ZipFile(buffer) as original, zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
        for name in sorted(original.namelist()):
            payload = original.read(name)
            if name.endswith(('.xml', '.rels')):
                payload = payload.replace(b'\r\n', b'\n')
            if name == 'docProps/core.xml':
                fixed = timestamp.isoformat(timespec='seconds').encode() + b'Z'
                payload = re.sub(rb'(<dcterms:modified[^>]*>).*?(</dcterms:modified>)',
                                 lambda match: match[1] + fixed + match[2], payload)
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(entry, payload)
    check = load_workbook(path)
    try:
        actual = check['Articles']
        require(actual.max_row == len(rows) + 5, 'Article workbook row count differs.')
        for number, values_row in enumerate(values, 6):
            require([actual.cell(number, col).value or '' for col in range(1, 8)] == values_row,
                    f'Article workbook row {number} differs.')
            record = rows[number-6]
            expected_links = {2: record['publisher_url'], 4: record['source_url']}
            expected_links[5 if record['local_file'] else 6] = (workbook_file_link(record['local_file'])
                if record['local_file'] else record['human_download_link'])
            for col, url in expected_links.items():
                require(actual.cell(number, col).hyperlink.target == url, f'Article workbook link differs at row {number}.')
        require(not any(c.data_type == 'f' for row in actual for c in row), 'Unexpected article workbook formula.')
    finally:
        check.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=REPO/'data/articles/article_search.json')
    parser.add_argument('--output-dir', type=Path, default=REPO/'reports')
    parser.add_argument('--verify-local', action='store_true', help='Also verify the recorded local PDF sizes and SHA256 hashes.')
    args = parser.parse_args()
    try:
        snapshot, papers = load_records(args.input.resolve(), args.verify_local)
        rows = export_records(snapshot, papers)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with (args.output_dir/'article_downloads.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        save_workbook(args.output_dir/'article_downloads.xlsx', rows, snapshot)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Article report failed: {error}\n')
    print(f'Article table: {len(rows)} papers; ' + ', '.join(f'{n} {status.lower()}' for status, n in Counter(r['status'] for r in rows).items()) + '.')
    if args.verify_local:
        print('All recorded local PDF sizes and SHA256 hashes match.')


if __name__ == '__main__':
    main()
