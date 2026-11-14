"""Exercise evidence transformations with small real files and reviewed metadata."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

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
            papers = {row['paper_id']: row for row in csv.DictReader(f)}
        self.assertEqual(sorted(row['kind'] for row in plan['records']), ['nonspatial','raster','vector'])
        for row in plan['records']:
            declaration = row['descriptor']
            Draft202012Validator(schema).validate(declaration)
            self.assertEqual(row['id'], declaration['id'])
            for paper in declaration['metadata']['publications']:
                self.assertEqual(paper['doi'], papers[paper['id']]['article_doi'])
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


if __name__ == '__main__':
    unittest.main()
