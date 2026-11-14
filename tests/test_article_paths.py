"""Check portable article reports using an independent, minimal input fixture."""
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
        body = b'%PDF-1.4\nArticle link test fixture\n'
        record = dict(paper_id='paper-001', status='Downloaded',
                      source_name='Author repository', reader_note='Author manuscript.',
                      found_url='https://example.org/article', download_url='https://example.org/article.pdf',
                      human_url='https://example.org/article', attempts=[{'url': 'https://example.org/article.pdf'}],
                      filename='paper-001_fixture #1.pdf', pages=2, size_bytes=len(body),
                      sha256=hashlib.sha256(body).hexdigest(), copy_version='Author manuscript')
        self.snapshot = dict(local_directory='articles', search_date='2026-11-14',
                             report_timestamp_utc='2026-11-14T00:00:00Z', records=[record])
        (self.root / 'articles').mkdir()
        (self.root / 'articles' / record['filename']).write_bytes(body)
        (self.root / 'search.json').write_text(json.dumps(self.snapshot), encoding='utf-8')
        decisions = self.root / 'data/decisions'
        decisions.mkdir(parents=True)
        paper = dict(paper_id='paper-001', verified_title='Fixture study', verified_year=2020,
                     article_doi='10.1234/example', publisher_url='https://doi.org/10.1234/example')
        (decisions / 'papers_verified.json').write_text(json.dumps([paper]), encoding='utf-8')

    def build(self, root, relative_output='build/articles'):
        with patch.object(report, 'REPO', root):
            snapshot, papers = report.load_records(root / 'search.json', verify_local=True)
            rows = report.export_records(snapshot, papers)
            folder = root / relative_output
            folder.mkdir(parents=True, exist_ok=True)
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
        self.assertEqual(rows_after[0]['year'], '2020')

    def test_workbook_links_open_the_recorded_file_at_each_output_depth(self):
        for output in ['build/articles', 'build/nested/articles', 'articles']:
            with self.subTest(output=output):
                rows, path = self.build(self.root, output)
                workbook = load_workbook(path)
                try:
                    target = workbook['Articles']['E6'].hyperlink.target
                finally:
                    workbook.close()
                self.assertFalse(urlsplit(target).scheme)
                self.assertIn('%23', target)
                expected = (self.root / rows[0]['local_file']).resolve()
                self.assertEqual((path.parent / unquote(target)).resolve(), expected)

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
