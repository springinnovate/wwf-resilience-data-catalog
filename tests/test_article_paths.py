"""Check that article reports stay portable without exposing machine paths."""
import copy
import csv
import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_article_report as report
from openpyxl import load_workbook


class ArticlePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'original'
        self.root.mkdir()
        snapshot = json.loads((ROOT / 'data/articles/article_search.json').read_text(encoding='utf-8'))
        record = copy.deepcopy(next(r for r in snapshot['records'] if r['status'] == 'Downloaded'))
        record['filename'] = record['paper_id'] + '_fixture #1.pdf'
        body = b'%PDF-1.4\nArticle link test fixture\n'
        record.update(size_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        snapshot['records'] = [record]
        self.snapshot = snapshot
        (self.root / snapshot['local_directory']).mkdir(parents=True)
        (self.root / snapshot['local_directory'] / record['filename']).write_bytes(body)
        (self.root / 'search.json').write_text(json.dumps(snapshot), encoding='utf-8')
        (self.root / 'outputs').mkdir()
        with (ROOT / 'outputs/papers.csv').open(encoding='utf-8-sig', newline='') as handle:
            paper = next(r for r in csv.DictReader(handle) if r['paper_id'] == record['paper_id'])
        with (self.root / 'outputs/papers.csv').open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(paper))
            writer.writeheader()
            writer.writerow(paper)

    def build(self, root):
        with patch.object(report, 'REPO', root):
            snapshot, papers = report.load_records(root / 'search.json', verify_local=True)
            rows = report.export_records(snapshot, papers)
            folder = root / 'reports'
            folder.mkdir(exist_ok=True)
            path = folder / 'article_downloads.xlsx'
            report.save_workbook(path, rows, snapshot)
        return rows, path

    def test_moving_checkout_preserves_reports_and_verification(self):
        rows_before, workbook_before = self.build(self.root)
        content_before = workbook_before.read_bytes()
        relocated = self.root.with_name('relocated')
        shutil.move(str(self.root), str(relocated))
        rows_after, workbook_after = self.build(relocated)
        self.assertEqual(rows_before, rows_after)
        self.assertEqual(content_before, workbook_after.read_bytes())
        self.assertFalse(PureWindowsPath(rows_after[0]['local_file']).anchor)
        self.assertTrue((relocated / rows_after[0]['local_file']).is_file())

    def test_workbook_links_open_the_recorded_file(self):
        rows, path = self.build(self.root)
        workbook = load_workbook(path)
        try:
            target = workbook['Articles']['E6'].hyperlink.target
        finally:
            workbook.close()
        self.assertFalse(urlsplit(target).scheme)
        self.assertIn('%23', target)
        expected = (self.root / rows[0]['local_file']).resolve()
        self.assertEqual((path.parent / unquote(target)).resolve(), expected)
        # The convenience workbook beside PDFs uses the same sibling-folder link.
        self.assertEqual((expected.parent / unquote(target)).resolve(), expected)

    def test_machine_specific_or_outside_directory_is_rejected(self):
        for directory in ['C:/private/articles', r'C:\private\articles', r'\\server\share',
                          '/private/articles', '../articles', 'file:///private/articles']:
            with self.subTest(directory=directory):
                snapshot = dict(self.snapshot, local_directory=directory)
                path = self.root / 'search.json'
                path.write_text(json.dumps(snapshot), encoding='utf-8')
                with patch.object(report, 'REPO', self.root):
                    with self.assertRaisesRegex(ValueError, 'repository-relative'):
                        report.load_records(path, verify_local=False)


if __name__ == '__main__':
    unittest.main()
