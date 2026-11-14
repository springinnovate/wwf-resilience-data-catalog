"""Check canonical metadata loading and confined, complete evidence input references."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from evidence_sources import load_records, input_fingerprints, inputs_sha256


class EvidenceSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'evidence'
        self.recipes=self.root/'matched/recipes'
        self.recipes.mkdir(parents=True)
        for folder in ['matched/sidecars','notes','curation']:
            (self.root/folder).mkdir(exist_ok=True)
        self.descriptor=dict(schema='eolab/item/v1',id='example',kind='nonspatial',
            primary_asset='data',metadata={'title':'Reviewed title'},
            assets={'data':dict(location='local',path='data.csv')})
        self.sidecar=self.root/'matched/sidecars/data.csv.eolab.yaml'
        self.sidecar.write_text(yaml.safe_dump(self.descriptor),encoding='utf-8')
        (self.root/'notes/example.md').write_text('Authored interpretation.\n',encoding='utf-8')
        (self.root/'curation/example.json').write_text('{"dataset_id":"example","limitation":"Unknown units"}',encoding='utf-8')
        self.recipe=dict(sidecar='matched/sidecars/data.csv.eolab.yaml',
            scientific_note='notes/example.md',curation='curation/example.json',
            directory='example',row_ids=['row-001'],source_files={'raw.csv':'hash'},
            operation={'type':'copy','source':'raw.csv'})
        self.write_recipe()

    def write_recipe(self):
        (self.recipes/'example.json').write_text(json.dumps(self.recipe),encoding='utf-8')

    def test_yaml_is_the_only_metadata_source_and_all_authored_inputs_are_hashed(self):
        record=load_records(self.recipes)[0]
        self.assertEqual(record['descriptor'],self.descriptor)
        self.assertEqual(record['scientific_note_text'],'Authored interpretation.\n')
        self.assertEqual(record['review_context'],{'dataset_id':'example','limitation':'Unknown units'})
        self.assertEqual(record['output_file'],'data.csv')
        fingerprints=input_fingerprints(self.recipes)
        self.assertEqual(set(fingerprints),{'matched/recipes/example.json',
            'matched/sidecars/data.csv.eolab.yaml','notes/example.md','curation/example.json'})
        before=inputs_sha256(self.recipes)
        self.descriptor['metadata']['title']='Revised title'
        self.sidecar.write_text(yaml.safe_dump(self.descriptor),encoding='utf-8')
        self.assertEqual(load_records(self.recipes)[0]['descriptor']['metadata']['title'],'Revised title')
        self.assertNotEqual(inputs_sha256(self.recipes),before)

    def test_missing_or_escaping_authored_reference_is_rejected(self):
        for name in ['../outside.json','/outside.json','C:outside.json','folder\\outside.json']:
            with self.subTest(path=name):
                self.recipe['curation']=name;self.write_recipe()
                with self.assertRaises(ValueError):load_records(self.recipes)
        self.recipe['curation']='curation/missing.json';self.write_recipe()
        with self.assertRaises(FileNotFoundError):load_records(self.recipes)

    def test_another_datasets_note_or_curation_cannot_be_attached(self):
        curation=self.root/'curation/example.json'
        curation.write_text('{"dataset_id":"another-study"}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'same dataset as the sidecar'):
            load_records(self.recipes)
        curation.write_text('{"dataset_id":"example"}',encoding='utf-8')
        (self.root/'notes/another-study.md').write_text('Different study.',encoding='utf-8')
        self.recipe['scientific_note']='notes/another-study.md';self.write_recipe()
        with self.assertRaisesRegex(ValueError,'same dataset as the sidecar'):
            load_records(self.recipes)

    def test_dataset_rename_cannot_silently_detach_recipe_from_sidecar(self):
        self.descriptor['id']='different-id'
        self.sidecar.write_text(yaml.safe_dump(self.descriptor),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'filename must match'):load_records(self.recipes)


if __name__=='__main__':unittest.main()
