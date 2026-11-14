"""Verify metadata refresh preserves data and refuses partial or misleading updates."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import yaml

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import test_preparation
import refresh_evidence_metadata as refresh
from evidence_notes import render_evidence_summary


class ScientificMetadataRefreshTests(unittest.TestCase):
    def setUp(self):
        test_preparation.MetadataRefreshTests.setUp(self)
        for record in self.plan['records']:
            record['evidence_summary']=dict(question='How does land use affect habitat?',
                finding='Observed differences vary among sites.',interpretation='Compare similar settings.',
                evidence_type='Observational comparison',dataset_role='Site observations',
                limitations=['No before/after policy comparison.'],sources=[dict(title='Study',
                url='https://doi.org/10.1234/example',location='Figure 2',supports='Site comparison.')])
            record['descriptor']['assets']['evidence_summary']=dict(location='local',
                path='evidence-summary.md',media_type='text/markdown',roles=['metadata'])
            record['review_context']['evidence_summary']=record['evidence_summary']

    def snapshot(self):
        return {p.relative_to(self.output).as_posix():(p.read_bytes(),p.stat().st_mtime_ns)
                for p in self.output.rglob('*') if p.is_file()}

    def plan_refresh(self):
        return refresh.plan_collection(self.output,self.plan['records'],
            {r['id']:r['review_context'] for r in self.plan['records']},
            {'records_sha256':'reviewed-plan'},json.loads(self.schema_path.read_text()))

    def test_adds_linked_brief_and_keeps_original_data_times_and_checks(self):
        before=self.snapshot()
        report,updates,old,payloads=self.plan_refresh()
        refresh.publish(self.output,updates,old,payloads)
        after=self.snapshot()
        self.assertEqual(len(after),len(before)+3)
        for name,expected in before.items():
            if name.endswith('.bin'):self.assertEqual(after[name],expected)
        self.assertEqual(report['runtime'],self.previous['runtime'])
        self.assertEqual(report['datasets'][0]['checks'],self.previous['datasets'][0]['checks'])
        for record in self.plan['records']:
            folder=self.output/record['directory']
            self.assertEqual((folder/'evidence-summary.md').read_text(encoding='utf-8'),
                             render_evidence_summary(record))
            self.assertEqual(json.loads((folder/'review-context.json').read_text())['evidence'],
                             'original notes')
        self.assertEqual(json.loads((self.output/'preparation-report.json').read_text()),report)

    def test_pilot_refresh_entry_point_updates_the_linked_note(self):
        import prepare_evidence_pilot as pilot
        pilot.write_json(self.records_path,self.plan)
        report=pilot.refresh_metadata(self.source,self.output,self.records_path,self.schema_path)
        self.assertEqual(report['metadata_refresh']['payload_files_verified'],6)
        for record in self.plan['records']:
            self.assertEqual((self.output/record['directory']/'evidence-summary.md').read_text(encoding='utf-8'),
                             render_evidence_summary(record))

    def test_source_refactor_preserves_old_context_once_in_delivery_history(self):
        previous={'evidence':'old detailed evidence','metadata_history':[{'decision':'keep me'}]}
        current={'curated_evidence':{'decision':'reviewed'},'source_files':{'data.csv':'hash'}}
        migrated=refresh.preserve_provenance(previous,current)
        self.assertEqual(migrated['provenance_history'],[previous])
        self.assertEqual(refresh.preserve_provenance(migrated,current),migrated)
        revised=dict(current,curated_evidence={'decision':'updated'})
        second=refresh.preserve_provenance(migrated,revised)
        self.assertEqual(second['provenance_history'],[previous,current])

    def test_changed_payload_is_rejected_without_writes(self):
        (self.output/'vector/data.bin').write_bytes(b'changed scientific data')
        before=self.snapshot()
        with self.assertRaisesRegex(ValueError,'Delivered checksum differs'):self.plan_refresh()
        self.assertEqual(before,self.snapshot())

    def test_claim_or_asset_redirection_is_rejected(self):
        initial=deepcopy(self.plan)
        for case in ['date','identity','asset','new-data-asset']:
            with self.subTest(case=case):
                self.plan=deepcopy(initial);d=self.plan['records'][0]['descriptor']
                if case=='date':d['temporal']={'mode':'instant','datetime':'2001-01-01T00:00:00Z'}
                elif case=='identity':d['id']='different'
                elif case=='asset':d['assets']['original']['path']='data.bin'
                else:d['assets']['fabricated']={'location':'local','path':'data.bin'}
                before=self.snapshot()
                with self.assertRaises(ValueError):self.plan_refresh()
                self.assertEqual(before,self.snapshot())

    def test_historical_evidence_cannot_be_discarded(self):
        self.plan['records'][0]['review_context'].pop('evidence')
        before=self.snapshot()
        with self.assertRaisesRegex(ValueError,'Historical evidence changed'):self.plan_refresh()
        self.assertEqual(before,self.snapshot())

    def test_failed_publish_removes_new_brief_and_restores_existing_metadata(self):
        report,updates,old,payloads=self.plan_refresh();before=self.snapshot()
        native=os.replace;calls=0
        def fail_once(source,target):
            nonlocal calls
            calls+=1
            if calls==5:raise OSError('simulated publication failure')
            return native(source,target)
        with patch.object(refresh.os,'replace',side_effect=fail_once):
            with self.assertRaisesRegex(OSError,'simulated publication failure'):
                refresh.publish(self.output,updates,old,payloads)
        self.assertEqual(self.snapshot(),before)
        self.assertFalse(list(self.root.glob('.evidence-refresh-*')))

    def test_concurrent_change_prevents_any_publication(self):
        report,updates,old,payloads=self.plan_refresh()
        (self.output/'vector/data.bin').write_bytes(b'changed after preflight')
        before=self.snapshot()
        with self.assertRaisesRegex(ValueError,'changed during preflight'):
            refresh.publish(self.output,updates,old,payloads)
        self.assertEqual(self.snapshot(),before)

    def test_unrecorded_file_is_rejected(self):
        (self.output/'unexpected.csv').write_text('unreviewed data')
        with self.assertRaisesRegex(ValueError,'Unrecorded files'):self.plan_refresh()

    def test_all_public_summaries_have_roles_sources_and_no_sheet_bookkeeping(self):
        from jsonschema import Draft202012Validator
        schema=json.loads((ROOT/'evidence/pilot/eolab-item-v1.schema.json').read_text(encoding='utf-8'))
        collections=refresh.reviewed_records()
        self.assertEqual(sum(map(len,collections.values())),24)
        for collection,records in collections.items():
            for record in records:
                with self.subTest(dataset=record['id']):
                    descriptor=record['descriptor'];Draft202012Validator(schema).validate(descriptor)
                    metadata=descriptor['metadata'];note=record['scientific_note_text']
                    self.assertNotRegex(json.dumps(metadata),r'paper-\d{3}|row-\d{3}|Matched to sheet')
                    for key in ['evidence_type','dataset_role']:
                        self.assertIn(metadata['annotations'][key],note)
                    for section in ['Question','What the study found','Limits and interpretation',
                                    'Sources for these statements']:
                        self.assertIn('## '+section,note)
                    self.assertRegex(note,r'https://(?:doi.org|www\.|[a-z])')
                    self.assertNotIn('](review-context.json)',note)
                    self.assertNotIn('../plans/',note)
                    self.assertNotIn('../records.json',note)
                    self.assertTrue(record['review_context'])
                    self.assertEqual(descriptor['assets']['evidence_summary']['path'],'evidence-summary.md')
                    path=ROOT/'evidence'/collection/'sidecars'/(record['output_file']+'.eolab.yaml')
                    self.assertEqual(yaml.safe_load(path.read_text(encoding='utf-8')),descriptor)
                    self.assertNotIn('metadata_history',record)


if __name__=='__main__':unittest.main()
