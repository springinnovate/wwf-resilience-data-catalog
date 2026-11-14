"""Exercise evidence transformations with small real files and reviewed metadata."""
import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

import fiona
from jsonschema import Draft202012Validator
import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import prepare_evidence_pilot as prepare


class EvidencePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_cog_preserves_negative_zero_nodata_and_grid(self):
        source, target = self.root/'source.tif', self.root/'output.tif'
        data = np.array([[-9999, -143.25, 0], [250.5, 1.25, -1]], dtype='float32')
        with rasterio.open(source, 'w', driver='GTiff', width=3, height=2, count=1,
                           dtype='float32', crs='EPSG:4326', transform=from_origin(-60, 4, .1, .1),
                           nodata=-9999) as ds:
            ds.write(data, 1)
        result = prepare.prepare_raster(source, target, {'expected_valid_pixels': 5})
        self.assertEqual(result['minimum'], -143.25)
        self.assertEqual(result['maximum'], 250.5)
        self.assertTrue(result['base_values_identical'])
        with rasterio.open(target) as ds:
            np.testing.assert_array_equal(ds.read(1), data)
            self.assertEqual(ds.crs.to_epsg(), 4326)

    def test_vector_preserves_unicode_attributes_and_coordinates(self):
        source, target = self.root/'source.shp', self.root/'output.gpkg'
        schema = {'geometry': 'Point', 'properties': {'id': 'int', 'label': 'str:40', 'value': 'float'}}
        with fiona.open(source, 'w', driver='ESRI Shapefile', crs='EPSG:4326',
                        schema=schema, encoding='UTF-8') as ds:
            ds.write({'geometry': {'type': 'Point', 'coordinates': (-60.25, -3.5)},
                      'properties': {'id': 7, 'label': 'São Tomé', 'value': -2.5}})
        result = prepare.prepare_vector(source, target, {'expected_features': 1, 'output_layer': 'points'})
        self.assertTrue(result['attributes_identical'])
        self.assertTrue(result['coordinates_identical'])
        with fiona.open(target, layer='points') as ds:
            feature = next(iter(ds))
            self.assertEqual(feature.properties['label'], 'São Tomé')
            self.assertEqual(tuple(feature.geometry.coordinates), (-60.25, -3.5))

    def test_missing_or_duplicate_month_is_rejected(self):
        source, target = self.root/'source.csv', self.root/'output.csv'
        source.write_text('Time,Year,Month,value\n2023-01-31,2023,1,0\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'each month exactly once'):
            prepare.prepare_table(source, target, {'expected_source_rows': 1, 'year': 2023,
                                                   'columns': ['Time','Year','Month','value']})
        self.assertFalse(target.exists())

    def test_reviewed_records_match_schema_and_keep_paper_identity(self):
        plan = json.loads((ROOT/'evidence/pilot/records.json').read_text(encoding='utf-8'))
        schema = json.loads((ROOT/'evidence/pilot/eolab-item-v1.schema.json').read_text(encoding='utf-8'))
        with (ROOT/'outputs/papers.csv').open(encoding='utf-8-sig', newline='') as f:
            papers = {row['article_doi']: row for row in csv.DictReader(f)}
        self.assertEqual(sorted(row['kind'] for row in plan['records']), ['nonspatial','raster','vector'])
        for row in plan['records']:
            declaration = row['descriptor']
            Draft202012Validator(schema).validate(declaration)
            self.assertEqual(row['id'], declaration['id'])
            for paper in declaration['metadata']['publications']:
                self.assertIn(paper['doi'], papers)
                self.assertEqual(paper['id'], 'doi-' + paper['doi'].replace('/', '-').replace(':', '-'))
            for asset in declaration['assets'].values():
                if asset['location'] == 'local':
                    prepare.relative_file(self.root, asset['path'])
            self.assertEqual(declaration['assets']['data']['path'], row['output_file'])

    def test_output_cannot_overwrite_an_existing_collection(self):
        (self.root/'source').mkdir()
        destination = self.root/'existing'
        destination.mkdir()
        marker = destination/'keep.txt'
        marker.write_text('keep', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            prepare.prepare(self.root/'source', destination, ROOT/'missing.json', ROOT/'missing-schema.json')
        self.assertEqual(marker.read_text(encoding='utf-8'), 'keep')


class MetadataRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.output = self.root / 'delivery'
        self.source.mkdir()
        self.output.mkdir()
        self.records_path = self.root / 'records.json'
        self.schema_path = self.root / 'schema.json'
        schema = {'type': 'object', 'required': ['id', 'kind', 'primary_asset', 'metadata', 'assets'],
                  'properties': {'metadata': {'type': 'object', 'properties': {'title': {'type': 'string'}}}}}
        prepare.write_json(self.schema_path, schema)
        self.plan = {'eolab_contract': {'schema': 'test'}, 'records': []}
        self.previous = {'eolab_contract': {'schema': 'test'}, 'records_sha256': 'previous-records',
                         'runtime': {'test': 'original-runtime'}, 'gdal_version': 'original-gdal', 'datasets': []}
        for kind in ['raster', 'vector', 'nonspatial']:
            source_name = kind + '.bin'
            source_file = self.source / source_name
            source_file.write_bytes((kind + '-original').encode())
            folder = self.output / kind
            folder.mkdir()
            (folder / 'data.bin').write_bytes((kind + '-prepared').encode())
            (folder / 'original.bin').write_bytes(source_file.read_bytes())
            descriptor = {'id': kind, 'kind': kind, 'primary_asset': 'data',
                          'temporal': {'mode': 'modified'}, 'metadata': {'title': 'Old title'},
                          'assets': {'data': {'location': 'local', 'path': 'data.bin'},
                                     'original': {'location': 'local', 'path': 'original.bin'},
                                     'context': {'location': 'local', 'path': 'review-context.json'}}}
            (folder / 'data.bin.eolab.yaml').write_text(yaml.safe_dump(descriptor), encoding='utf-8')
            prepare.write_json(folder / 'review-context.json', {'evidence': 'original notes'})
            # Stable non-current times make accidental data replacement detectable.
            for path in folder.iterdir():
                os.utime(path, ns=(1600000000000000000, 1600000000000000000))
            source_files = {source_name: prepare.sha256(source_file)}
            self.previous['datasets'].append(dict(id=kind, kind=kind, directory=kind, primary='data.bin',
                sidecar='data.bin.eolab.yaml', source_files=source_files,
                files={path.name: {'sha256': prepare.sha256(path), 'bytes': path.stat().st_size}
                       for path in folder.iterdir()}, checks={'transformation': 'original preparation'}))
            descriptor['metadata']['title'] = 'Readable ' + kind
            self.plan['records'].append(dict(id=kind, kind=kind, directory=kind, output_file='data.bin',
                source_files=source_files, descriptor=descriptor,
                review_context={'evidence': 'original notes', 'detail': 'full supporting evidence'}))
        prepare.write_json(self.output / 'preparation-report.json', self.previous)
        prepare.write_json(self.records_path, self.plan)

    def refresh(self):
        return prepare.refresh_metadata(self.source, self.output, self.records_path, self.schema_path)

    def snapshot(self):
        return {path.relative_to(self.output).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.output.rglob('*') if path.is_file()}

    def test_refresh_preserves_payloads_times_and_original_checks(self):
        before = self.snapshot()
        report = self.refresh()
        after = self.snapshot()
        self.assertEqual(before.keys(), after.keys())
        for name in before:
            if name.endswith('.bin'):
                self.assertEqual(before[name], after[name])
        self.assertEqual(report['runtime'], self.previous['runtime'])
        self.assertEqual(report['gdal_version'], self.previous['gdal_version'])
        self.assertEqual(report['records_sha256'], prepare.sha256(self.records_path))
        audit = report['metadata_refresh']
        self.assertEqual(audit['previous_records_sha256'], 'previous-records')
        self.assertEqual(audit['payload_files_verified'], 6)
        self.assertFalse(audit['data_transformations_rerun'])
        for old, updated in zip(self.previous['datasets'], report['datasets']):
            self.assertEqual(old['checks'], updated['checks'])
            folder = self.output / updated['directory']
            sidecar = yaml.safe_load((folder / updated['sidecar']).read_text(encoding='utf-8'))
            self.assertEqual(sidecar['metadata']['title'], 'Readable ' + updated['kind'])
            self.assertEqual(json.loads((folder / 'review-context.json').read_text())['detail'],
                             'full supporting evidence')
            for name, details in updated['files'].items():
                self.assertEqual(details['sha256'], prepare.sha256(folder / name))
                self.assertEqual(details['bytes'], (folder / name).stat().st_size)
        self.assertEqual(json.loads((self.output / 'preparation-report.json').read_text()), report)

    def test_source_drift_refuses_all_writes(self):
        (self.source / 'vector.bin').write_bytes(b'changed source')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Source checksum differs'):
            self.refresh()
        self.assertEqual(self.snapshot(), before)

    def test_payload_drift_refuses_all_writes(self):
        (self.output / 'vector' / 'data.bin').write_bytes(b'changed payload')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Delivered file differs'):
            self.refresh()
        self.assertEqual(self.snapshot(), before)

    def test_schema_and_claim_changes_refuse_all_writes(self):
        before = self.snapshot()
        self.plan['records'][0]['descriptor']['metadata']['title'] = 42
        prepare.write_json(self.records_path, self.plan)
        from jsonschema import ValidationError
        with self.assertRaises(ValidationError):
            self.refresh()
        self.assertEqual(self.snapshot(), before)
        self.plan['records'][0]['descriptor']['metadata']['title'] = 'Valid title'
        del self.plan['records'][0]['descriptor']['assets']['original']
        prepare.write_json(self.records_path, self.plan)
        with self.assertRaisesRegex(ValueError, 'asset locations or claims'):
            self.refresh()
        self.assertEqual(self.snapshot(), before)

    def test_failed_replacement_restores_metadata_and_times(self):
        before = self.snapshot()
        native_replace = os.replace
        calls = []

        def fail_once(source, destination):
            calls.append((source, destination))
            if len(calls) == 3:
                raise OSError('simulated replacement failure')
            return native_replace(source, destination)

        with patch.object(prepare.os, 'replace', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'simulated replacement failure'):
                self.refresh()
        self.assertGreater(len(calls), 3)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(list(self.root.glob('.evidence-metadata-*')))


    def test_failed_rollback_keeps_recovery_copies(self):
        before = self.snapshot()
        native_replace = os.replace
        call_count = 0

        def fail_publication_and_one_restore(source, destination):
            nonlocal call_count
            call_count += 1
            if call_count in (3, 4):
                raise OSError('simulated filesystem failure')
            return native_replace(source, destination)

        with patch.object(prepare.os, 'replace', side_effect=fail_publication_and_one_restore):
            with self.assertRaisesRegex(RuntimeError, 'Recovery copies retained'):
                self.refresh()
        recovery = list(self.root.glob('.evidence-metadata-*'))
        self.assertEqual(len(recovery), 1)
        self.assertEqual((recovery[0] / '1.previous').read_bytes(), before['raster/review-context.json'][0])
        self.assertEqual(self.snapshot()['raster/data.bin.eolab.yaml'], before['raster/data.bin.eolab.yaml'])


if __name__ == '__main__':
    unittest.main()
