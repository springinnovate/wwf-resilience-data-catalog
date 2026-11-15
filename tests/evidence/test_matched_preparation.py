"""Boundary checks for matched evidence using small, real scientific files."""
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

import yaml

from jsonschema import Draft202012Validator
import numpy as np
from openpyxl import Workbook
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_matched_evidence as prepare
import build_evidence_delivery_report as delivery_report
from evidence_sources import load_pilot_plan, reconciliation_tables


class MatchedPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()

    def write_csv(self, name, rows, *, encoding='utf-8', delimiter=','):
        path = self.source / name
        with path.open('w', encoding=encoding, newline='') as handle:
            csv.writer(handle, delimiter=delimiter).writerows(rows)
        return path

    def table(self, operation, **extra):
        return prepare.prepare_table(self.source, self.root / 'output.csv',
                                     {'operation': operation, **extra})

    def test_archived_byte_raster_retains_native_crs_grid_values_and_explicit_mask(self):
        # Cross both 512-cell block boundaries; a masked valid value is distinct
        # from nodata, and zero must remain valid rather than becoming background.
        source = self.source / 'native.tif'
        target = self.root / 'output.tif'
        data = (np.arange(517 * 519).reshape(517, 519) % 35).astype('uint8')
        data[0, 0] = data[-1, -1] = 255
        mask = np.full(data.shape, 255, dtype='uint8')
        mask[data == 255] = 0
        mask[513, 514] = 0
        transform = from_origin(883668.9, 10664279.6, 279.6098595442334, 279.6098595442334)
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(source, 'w', driver='GTiff', width=519, height=517,
                               count=1, dtype='uint8', crs='EPSG:5641',
                               transform=transform, nodata=255) as dataset:
                dataset.write(data, 1)
                dataset.write_mask(mask)
                dataset.set_band_description(1, 'Relative resistance')
                dataset.set_band_unit(1, '1')
        archive = self.source / 'native.zip'
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.write(source, 'study/native.tif')
        source.unlink()  # The converter must actually read the archive member.
        result = prepare.prepare_raster(self.source, target, {
            'operation': {'type': 'raster', 'source': 'native.zip',
                          'archive_member': 'study/native.tif'}})
        with rasterio.open(target) as dataset:
            self.assertEqual(dataset.crs.to_epsg(), 5641)
            self.assertEqual(dataset.transform, transform)
            self.assertEqual(dataset.dtypes, ('uint8',))
            self.assertEqual(dataset.nodata, 255)
            self.assertEqual(dataset.descriptions, ('Relative resistance',))
            self.assertEqual(dataset.units, ('1',))
            self.assertEqual(dataset.tags(ns='IMAGE_STRUCTURE')['LAYOUT'], 'COG')
            np.testing.assert_array_equal(dataset.read(1), data)
            np.testing.assert_array_equal(dataset.read_masks(1), mask)
        self.assertEqual(result['valid_pixels'], [517 * 519 - 3])
        self.assertEqual(result['value_ranges'], [[0.0, 34.0]])
        self.assertTrue(result['base_values_identical'])
        self.assertTrue(result['masks_identical'])

    def test_raster_without_crs_is_refused_before_output_creation(self):
        source = self.source / 'unreferenced.tif'
        target = self.root / 'output.tif'
        with rasterio.open(source, 'w', driver='GTiff', width=2, height=2,
                           count=1, dtype='float32', transform=from_origin(-60, 1, .1, .1)) as dataset:
            dataset.write(np.zeros((2, 2), dtype='float32'), 1)
        with self.assertRaisesRegex(ValueError, 'CRS is unverified'):
            prepare.prepare_raster(self.source, target,
                                   {'operation': {'type': 'raster', 'source': source.name}})
        self.assertFalse(target.exists())

    def test_float_raster_keeps_negative_extremes_zero_and_nan_nodata(self):
        source = self.source / 'signed.tif'
        target = self.root / 'output.tif'
        data = np.array([[np.nan, -27.63535], [0, 22.88876]], dtype='float32')
        with rasterio.open(source, 'w', driver='GTiff', width=2, height=2,
                           count=1, dtype='float32', crs='EPSG:4326', nodata=np.nan,
                           transform=from_origin(-60, 1, .1, .1)) as dataset:
            dataset.write(data, 1)
            dataset.scales = (0.5,)
            dataset.offsets = (-1.0,)
        checks = prepare.prepare_raster(self.source, target,
                                       {'operation': {'type': 'raster', 'source': source.name}})
        with rasterio.open(target) as dataset:
            np.testing.assert_array_equal(dataset.read(1), data)
            self.assertEqual(dataset.scales, (0.5,))
            self.assertEqual(dataset.offsets, (-1.0,))
        self.assertEqual(checks['valid_pixels'], [3])
        self.assertEqual(checks['value_ranges'], [[float(data[0, 1]), float(data[1, 1])]])

    def test_latin1_selection_and_decimal_comma_preserve_other_cells(self):
        source = self.write_csv('measurements.csv', [
            ['Original study notes'],
            ['site', 'code', 'value', 'excluded'],
            ['São Tomé', '0017', '-0,250', '8,5'],
            ['Pará', '0002', '0', '9,5'],
            ['Belém', '0003', '', '1,5'],
        ], encoding='latin-1', delimiter=';')
        before = source.read_bytes()
        checks = self.table({'type': 'csv_table', 'source': source.name,
                             'encoding': 'latin-1', 'delimiter': ';', 'header_row': 2,
                             'columns': ['code', 'site', 'value'], 'decimal_columns': ['value']},
                            expected_rows=3)
        self.assertEqual(prepare.read_csv(self.root / 'output.csv'), [
            ['code', 'site', 'value'], ['0017', 'São Tomé', '-0.250'],
            ['0002', 'Pará', '0'], ['0003', 'Belém', '']])
        self.assertEqual(checks['decimal_comma_normalized_columns'], ['value'])
        self.assertEqual(checks['source_encoding'], 'latin-1')
        self.assertEqual(source.read_bytes(), before)

    def test_duplicate_headers_require_explicit_position_based_names(self):
        self.write_csv('duplicate.csv', [['site', 'value', 'value'], ['A', '12', '34']])
        with self.assertRaisesRegex(ValueError, 'Duplicate headers'):
            self.table({'type': 'csv_table', 'source': 'duplicate.csv'})
        self.assertFalse((self.root / 'output.csv').exists())
        checks = self.table({'type': 'csv_table', 'source': 'duplicate.csv',
                             'column_indices': [0, 2], 'output_headers': ['site', 'second_value']})
        self.assertEqual(prepare.read_csv(self.root / 'output.csv'),
                         [['site', 'second_value'], ['A', '34']])
        self.assertEqual(checks['source_column_indices_zero_based'], [0, 2])

    def test_name_selection_does_not_silently_choose_first_duplicate_header(self):
        self.write_csv('duplicate.csv', [['site', 'value', 'value'], ['A', '12', '34']])
        with self.assertRaises(ValueError):
            self.table({'type': 'csv_table', 'source': 'duplicate.csv', 'columns': ['value']})
        self.assertFalse((self.root / 'output.csv').exists())

    def test_hydropower_filter_records_source_scenario_and_exact_selected_values(self):
        self.write_csv('forest.csv', [
            ['metric', 'value'], ['x_hydropower', '-2.00'],
            ['hydropower_extra', '999'], ['x_solar', '888'], ['y_hydropower', '0']])
        self.write_csv('deforested.csv', [
            ['metric', 'value'], ['x_hydropower', '-3.50'], ['x_solar', '777']])
        checks = self.table({'type': 'csv_concat', 'sources': [
            {'path': 'forest.csv', 'land_management': 'forest'},
            {'path': 'deforested.csv', 'land_management': 'deforested'}],
            'filter': {'column': 'metric', 'endswith': '_hydropower'}}, expected_rows=3)
        self.assertEqual(prepare.read_csv(self.root / 'output.csv'), [
            ['metric', 'value', 'land_management'],
            ['x_hydropower', '-2.00', 'forest'], ['y_hydropower', '0', 'forest'],
            ['x_hydropower', '-3.50', 'deforested']])
        self.assertEqual(checks['source_row_counts'], {'forest.csv': 2, 'deforested.csv': 1})

    def test_concat_refuses_mismatched_headers_and_existing_scenario_column(self):
        self.write_csv('one.csv', [['metric', 'value'], ['x', '1']])
        self.write_csv('two.csv', [['value', 'metric'], ['2', 'x']])
        operation = {'type': 'csv_concat', 'sources': [
            {'path': 'one.csv', 'land_management': 'forest'},
            {'path': 'two.csv', 'land_management': 'deforested'}]}
        with self.assertRaisesRegex(ValueError, 'headers differ'):
            self.table(operation)
        self.write_csv('one.csv', [['metric', 'land_management'], ['x', 'original']])
        with self.assertRaisesRegex(ValueError, 'overwrite a source column'):
            self.table(operation)
        self.assertFalse((self.root / 'output.csv').exists())

    def test_xlsx_selects_named_sheet_and_header_row_with_explicit_date_strings(self):
        source = self.source / 'study.xlsx'
        book = Workbook()
        book.active.title = 'Ignore'
        book.active.append(['wrong sheet'])
        sheet = book.create_sheet('Selected')
        sheet.append(['Study notes'])
        sheet.append(['site', 'date', 'count', 'note'])
        sheet.append(['São Tomé', datetime(2023, 4, 6, 12, 30), 0, None])
        sheet.append([None, None, None, None])
        book.save(source)
        book.close()
        self.table({'type': 'xlsx_table', 'source': source.name, 'sheet': 'Selected',
                    'header_row': 2, 'columns': ['site', 'date', 'count', 'note']}, expected_rows=1)
        self.assertEqual(prepare.read_csv(self.root / 'output.csv'), [
            ['site', 'date', 'count', 'note'], ['São Tomé', '2023-04-06T12:30:00', '0', '']])

    def test_xlsx_formula_is_refused_instead_of_exported_or_treated_as_empty(self):
        source = self.source / 'formula.xlsx'
        book = Workbook()
        book.active.append(['site', 'value'])
        book.active.append(['A', '=1+2'])
        book.save(source)
        book.close()
        with self.assertRaisesRegex(ValueError, 'Formula cells'):
            self.table({'type': 'xlsx_table', 'source': source.name, 'sheet': 'Sheet'})
        self.assertFalse((self.root / 'output.csv').exists())

    def test_table_refuses_ragged_rows_and_reviewed_count_mismatch(self):
        self.write_csv('ragged.csv', [['site', 'value'], ['A']])
        with self.assertRaisesRegex(ValueError, 'ragged rows'):
            self.table({'type': 'csv_table', 'source': 'ragged.csv'})
        self.write_csv('valid.csv', [['site', 'value'], ['A', '0']])
        with self.assertRaisesRegex(ValueError, 'row count differs'):
            self.table({'type': 'csv_table', 'source': 'valid.csv'}, expected_rows=2)
        self.assertFalse((self.root / 'output.csv').exists())

    def test_decimal_conversion_refuses_nonfinite_values(self):
        for value in ['NaN', 'Infinity', '-Infinity']:
            with self.subTest(value=value):
                self.write_csv('value.csv', [['value'], [value]])
                with self.assertRaisesRegex(ValueError, 'Non-finite decimal'):
                    self.table({'type': 'csv_table', 'source': 'value.csv',
                                'decimal_columns': ['value']})
                self.assertFalse((self.root / 'output.csv').exists())

    def plan(self, *, operation=None, source_files=None, attachments=None, bundles=None):
        operation = operation or {'type': 'copy', 'source': 'source.csv'}
        descriptor = {
            'schema': 'eolab/item/v1', 'id': 'test-matched-table', 'kind': 'nonspatial',
            'primary_asset': 'data', 'temporal': {'mode': 'modified'},
            'metadata': {'title': 'Test table'},
            'assets': {'data': {'location': 'local', 'path': 'data.csv', 'media_type': 'text/csv',
                                'roles': ['data']},
                       'review_context': {'location': 'local', 'path': 'review-context.json',
                                          'media_type': 'application/json', 'roles': ['metadata']}}}
        for index, bundle in enumerate(bundles or []):
            descriptor['assets'][f'original_archive_{index}'] = {
                'location': 'local', 'path': bundle['path'],
                'media_type': 'application/zip', 'roles': ['metadata']}
        record = {'id': descriptor['id'], 'directory': 'table', 'kind': 'nonspatial',
                  'row_ids': ['row-017'], 'output_file': 'data.csv', 'operation': operation,
                  'descriptor': descriptor, 'source_files': source_files or {},
                  'attachments': attachments or [], 'bundles': bundles or []}
        directory = self.root / 'plans'
        directory.mkdir(exist_ok=True)
        (directory / 'plan.json').write_text(json.dumps({'records': [record]}), encoding='utf-8')
        return directory

    def test_changed_source_checksum_refuses_entire_delivery(self):
        source = self.write_csv('source.csv', [['value'], ['original']])
        plan = self.plan(source_files={'source.csv': prepare.sha256(source)})
        source.write_text('value\nchanged\n', encoding='utf-8')
        output = self.root / 'delivery'
        with self.assertRaisesRegex(ValueError, 'checksum changed'):
            prepare.prepare(self.source, output, plan)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob('.matched-evidence-*')))

    def test_every_consumed_source_requires_a_reviewed_checksum_before_staging(self):
        source = self.write_csv('source.csv', [['metric', 'value'], ['x', '1']])
        second = self.write_csv('second.csv', [['metric', 'value'], ['x', '2']])
        cases = [
            ({'type': 'csv_table', 'source': source.name}, {}, []),
            ({'type': 'csv_concat', 'sources': [
                {'path': source.name, 'land_management': 'forest'},
                {'path': second.name, 'land_management': 'deforested'}]},
             {source.name: prepare.sha256(source)}, []),
            ({'type': 'copy', 'source': source.name}, {source.name: prepare.sha256(source)},
             [{'source': second.name, 'path': 'source/second.csv'}]),
        ]
        for number, (operation, checksums, attachments) in enumerate(cases):
            with self.subTest(case=number):
                plan = self.plan(operation=operation, source_files=checksums, attachments=attachments)
                output = self.root / f'unstaged-{number}' / 'delivery'
                with self.assertRaises(ValueError):
                    prepare.prepare(self.source, output, plan)
                self.assertFalse(output.exists())
                self.assertFalse(output.parent.exists())
                self.assertFalse(list(self.root.glob('.matched-evidence-*')))

    def test_copy_delivery_keeps_source_bytes_and_auditable_payload_checksums(self):
        source = self.write_csv('source.csv', [['site', 'value'], ['São Tomé', '001.20']])
        checksum = prepare.sha256(source)
        plan = self.plan(source_files={source.name: checksum})
        output = self.root / 'delivery'
        report = prepare.prepare(self.source, output, plan)
        folder = output / 'table'
        self.assertEqual((folder / 'data.csv').read_bytes(), source.read_bytes())
        dataset = report['datasets'][0]
        self.assertTrue(dataset['checks']['source_bytes_identical'])
        self.assertEqual(dataset['source_files'], {source.name: checksum})
        for name, state in dataset['files'].items():
            self.assertEqual(state['sha256'], prepare.sha256(folder / name))
            self.assertEqual(state['bytes'], (folder / name).stat().st_size)
        context = json.loads((folder / 'review-context.json').read_text(encoding='utf-8'))
        self.assertEqual(context['source_sheet_rows'][0]['row_id'], 'row-017')
        self.assertEqual(context['source_files'], {source.name: checksum})
        self.assertEqual(json.loads((output / 'preparation-report.json').read_text(encoding='utf-8')), report)

    def bundle_fixture(self):
        primary = self.write_csv('source.csv', [['site', 'value'], ['A', '0']])
        forest = self.source / 'forest-original.csv'
        forest.write_bytes('site;value\r\nSão Tomé;1,25\r\n'.encode('latin-1'))
        deforested = self.source / 'deforested-original.csv'
        deforested.write_bytes(b'\xef\xbb\xbfsite,value\r\nA,001.20\r\n')
        files = [primary, forest, deforested]
        checksums = {source.name: prepare.sha256(source) for source in files}
        bundles = [{'path': 'source/originals.zip', 'files': [
            {'source': forest.name, 'path': 'models/forest.csv'},
            {'source': deforested.name, 'path': 'models/deforested.csv'}]}]
        return files, checksums, bundles

    def test_supporting_zip_keeps_exact_member_bytes_and_per_member_audit(self):
        files, checksums, bundles = self.bundle_fixture()
        plan = self.plan(source_files=checksums, bundles=bundles)
        output = self.root / 'delivery'
        report = prepare.prepare(self.source, output, plan)
        folder = output / 'table'
        archive_path = bundles[0]['path']
        expected_members = {}
        with zipfile.ZipFile(folder / archive_path) as archive:
            self.assertEqual(set(archive.namelist()), {'models/forest.csv', 'models/deforested.csv'})
            for entry in bundles[0]['files']:
                source = self.source / entry['source']
                self.assertEqual(archive.read(entry['path']), source.read_bytes())
                expected_members[entry['path']] = {
                    'source': source.name, 'sha256': checksums[source.name],
                    'bytes': source.stat().st_size}
        context = json.loads((folder / 'review-context.json').read_text(encoding='utf-8'))
        expected_audit = {archive_path: expected_members}
        self.assertEqual(context['preparation_checks']['supporting_archives'], expected_audit)
        self.assertEqual(report['datasets'][0]['checks']['supporting_archives'], expected_audit)
        self.assertEqual(context['source_files'], checksums)
        self.assertEqual(report['datasets'][0]['files'][archive_path]['sha256'],
                         prepare.sha256(folder / archive_path))
        self.assertEqual({source.name: prepare.sha256(source) for source in files}, checksums)
        # Supporting originals live only inside the single declared archive.
        self.assertEqual({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()},
                         {'data.csv', 'data.csv.eolab.yaml', 'review-context.json', archive_path})

    def test_bundle_sources_require_hashes_and_reject_source_drift_before_staging(self):
        files, checksums, bundles = self.bundle_fixture()
        supporting = files[-1]
        original_bytes = supporting.read_bytes()
        for case in ['missing-checksum', 'changed-source']:
            with self.subTest(case=case):
                supporting.write_bytes(original_bytes)
                declared = dict(checksums)
                if case == 'missing-checksum':
                    del declared[supporting.name]
                else:
                    supporting.write_bytes(b'changed supporting data')
                plan = self.plan(source_files=declared, bundles=bundles)
                output = self.root / case / 'delivery'
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    prepare.prepare(self.source, output, plan)
                self.assertFalse(output.parent.exists())

    def test_unsafe_or_duplicate_bundle_members_are_refused_before_publication(self):
        _, checksums, bundles = self.bundle_fixture()
        for index, member in enumerate(['../escape.csv', '/absolute.csv',
                                         'folder\\unsafe.csv', 'C:unsafe.csv', 'models/forest.csv']):
            with self.subTest(member=member):
                bundles[0]['files'][1]['path'] = member
                plan = self.plan(source_files=checksums, bundles=bundles)
                output = self.root / f'invalid-member-{index}' / 'delivery'
                with self.assertRaises(ValueError):
                    prepare.prepare(self.source, output, plan)
                self.assertFalse(output.exists())
                self.assertFalse(output.parent.exists())
        self.assertFalse((self.root / 'escape.csv').exists())

    def test_final_plans_sidecars_hash_coverage_and_all_matched_sheet_rows(self):
        # This check reads tracked recipes, sidecars and freshly rebuilt matching records;
        # CI does not need the downloaded scientific collection.
        records = prepare.load_records(ROOT / 'evidence/matched/recipes')
        self.assertEqual(len(records), 21)
        validator = Draft202012Validator(json.loads(prepare.SCHEMA.read_text(encoding='utf-8')))
        sidecar_root = ROOT / 'evidence/matched/sidecars'
        expected_sidecars = set()
        for record in records:
            with self.subTest(dataset=record['id']):
                descriptor = record['descriptor']
                validator.validate(descriptor)
                self.assertEqual(descriptor['id'], record['id'])
                self.assertEqual(descriptor['kind'], record['kind'])
                self.assertEqual(descriptor['assets'][descriptor['primary_asset']]['path'],
                                 record['output_file'])
                name = record['output_file'] + '.eolab.yaml'
                expected_sidecars.add(name)
                self.assertEqual(yaml.safe_load((sidecar_root / name).read_text(encoding='utf-8')),
                                 descriptor)
                operation = record['operation']
                consumed = ({operation['source']} if operation.get('source') else
                            {entry['path'] for entry in operation['sources']})
                consumed.update(entry['source'] for entry in record.get('attachments', []))
                consumed.update(entry['source'] for bundle in record.get('bundles', [])
                                for entry in bundle['files'])
                self.assertTrue(consumed <= record['source_files'].keys(),
                                f'Missing reviewed hashes: {consumed - record["source_files"].keys()}')
                for source in consumed:
                    self.assertRegex(record['source_files'][source], r'^[0-9a-f]{64}$')
        self.assertEqual({path.name for path in sidecar_root.glob('*.eolab.yaml')}, expected_sidecars)

        pilot = load_pilot_plan(ROOT / 'evidence/pilot/recipes')['records']
        all_records = [*pilot, *records]
        self.assertEqual(len({record['id'] for record in all_records}), len(all_records))
        matched = {row['row_id'] for row in reconciliation_tables()['matches'] if row['match_status'] == 'Matched'}
        self.assertEqual(len(matched), 19)
        represented = {row for record in all_records for row in record['row_ids']}
        barrier = next(record for record in pilot if record['id'] == 'wwf-amazon-barrier-locations')
        related_barrier_rows = set(barrier['row_ids'])
        self.assertEqual(represented, matched | related_barrier_rows)
        self.assertEqual(represented & matched, matched)

    def test_human_review_tables_rebuild_exactly_without_scientific_inputs(self):
        output = self.root / 'rebuilt-reports'
        datasets, coverage = delivery_report.build(output)
        self.assertEqual(len(datasets), 24)
        self.assertEqual(len(coverage), 19)
        summary = (output / 'catalog-summaries.md').read_text(encoding='utf-8')
        publication_groups = {tuple(sorted(dataset['paper_doi'].split('; ')))
                              for dataset in datasets}
        self.assertEqual(sum(line.startswith('## ') for line in summary.splitlines()),
                         len(publication_groups))
        self.assertEqual(sum(line.startswith('### ') for line in summary.splitlines()),
                         len(datasets))
        for dataset in datasets:
            with self.subTest(dataset=dataset['dataset_id']):
                self.assertEqual(summary.count('`' + dataset['file'] + '`'), 1)
                self.assertEqual(summary.count('`' + dataset['evidence_summary'] + '`'), 1)
        for group in publication_groups:
            for doi in group:
                self.assertEqual(summary.count('(https://doi.org/' + doi + ')'), 1)
        for title, path in [
            ('Carbon recovery workbook',
             'matched/forest-carbon-loss-gain-compilation/source/AGC_accumulation_forest_type_current_v2.xlsx'),
            ('Complete original 2014-2023 table',
             'pilot/atto-fluxes-2023/source/ATTO_monthly_eddyfluxes_deltaCO2_2014_2023_v202511.csv'),
            ('Original Shapefile SHP component',
             'pilot/amazon-barriers/source/barriers_all_validas4326.shp'),
        ]:
            with self.subTest(supporting_data=title):
                self.assertIn(title + ': `' + path + '`', summary)
        repeated = self.root / 'repeat-reports'
        self.assertEqual(delivery_report.build(repeated), (datasets, coverage))
        for name in ['datasets.csv', 'study_coverage.csv', 'catalog-summaries.md']:
            with self.subTest(report=name):
                self.assertEqual((output / name).read_bytes(),
                                 (repeated / name).read_bytes())

    def test_existing_delivery_and_source_nested_output_are_not_modified(self):
        output = self.root / 'existing'
        output.mkdir()
        marker = output / 'keep.txt'
        marker.write_text('keep', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            prepare.prepare(self.source, output, self.root / 'missing-plan')
        self.assertEqual(marker.read_text(encoding='utf-8'), 'keep')
        with self.assertRaisesRegex(ValueError, 'outside the source collection'):
            prepare.prepare(self.source, self.source / 'new-output', self.root / 'missing-plan')
        self.assertFalse((self.source / 'new-output').exists())


if __name__ == '__main__':
    unittest.main()
