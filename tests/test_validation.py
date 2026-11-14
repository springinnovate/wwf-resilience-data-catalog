"""Corrupt copies of the small committed snapshot; no bulk datasets are needed."""
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from openpyxl import load_workbook
from openpyxl.worksheet.hyperlink import Hyperlink


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_reconciliation", ROOT / "scripts" / "validate_reconciliation.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SnapshotCorruptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The negative fixtures must start from a known-good complete report.
        VALIDATOR.validate(ROOT / "data", ROOT / "outputs")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="reconciliation-validation-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.data = self.path / "data"
        self.outputs = self.path / "outputs"
        shutil.copytree(
            ROOT / "data", self.data,
            ignore=lambda directory, names: {"evidence_data"}
            if Path(directory) == ROOT / "data" else set(),
        )
        shutil.copytree(ROOT / "outputs", self.outputs)

    def edit_json(self, path, transform):
        value = json.loads(path.read_text(encoding="utf-8"))
        transform(value)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def rejected(self, message):
        with self.assertRaisesRegex(ValueError, message):
            VALIDATOR.validate(self.data, self.outputs)

    def test_missing_file_decision_is_not_hidden_by_old_outputs(self):
        self.edit_json(self.data / "decisions" / "matching_spatial.json", lambda v: v["files"].pop())
        self.rejected("File decision coverage")

    def test_modified_original_source_is_rejected(self):
        path = self.data / "source" / "source_sheet.tsv"
        path.write_bytes(path.read_bytes() + b"\n")
        self.rejected("Preserved source SHA256")

    def test_csv_description_drift_is_rejected(self):
        path = self.outputs / "matches.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields, records = reader.fieldnames, list(reader)
        records[0]["description"] += " altered"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
        self.rejected("matches.csv record 1 column description")

    def test_dangling_parent_file_reference_is_rejected(self):
        self.edit_json(self.outputs / "reconciliation.json",
                       lambda v: v["asset_links"][0].update(parent_file_id="asset-does-not-exist"))
        self.rejected("dangling parent_file_id")

    def test_duplicate_link_identifier_is_rejected(self):
        def duplicate(report):
            report["asset_links"][1]["link_id"] = report["asset_links"][0]["link_id"]
        self.edit_json(self.outputs / "reconciliation.json", duplicate)
        self.rejected("Duplicate asset link link_id")

    def test_archive_member_link_cannot_collapse_to_container(self):
        # Regression for a real bug: selector deduplication kept the outer ZIP's
        # asset ID instead of upgrading it to the separately indexed member ID.
        def collapse(report):
            archived_ids = {a["asset_id"] for a in report["archive_assets"]}
            link = next(l for l in report["asset_links"] if l["asset_id"] in archived_ids)
            link["asset_id"] = link["parent_file_id"]
        self.edit_json(self.outputs / "reconciliation.json", collapse)
        self.rejected("Missing archive link")

    def test_corrupted_summary_is_rejected_even_when_copies_agree(self):
        self.edit_json(self.outputs / "summary.json", lambda v: v.update(standalone_files=v["standalone_files"] - 1))
        self.edit_json(self.outputs / "reconciliation.json",
                       lambda v: v["summary"].update(standalone_files=v["summary"]["standalone_files"] - 1))
        self.rejected("Summary standalone_files")

    def test_unmatched_data_cannot_disappear(self):
        self.edit_json(self.outputs / "reconciliation.json", lambda v: v["unmatched_local_data"].pop())
        self.rejected("Unmatched local data/disposition coverage")

    def test_workbook_formula_is_rejected(self):
        path = self.outputs / "study_data_matches.xlsx"
        workbook = load_workbook(path)
        workbook["Match records"]["B2"] = '=HYPERLINK("https://example.invalid","changed")'
        workbook.save(path)
        workbook.close()
        self.rejected("Unexpected Excel formula")

    def test_missing_presentation_row_is_rejected(self):
        self.edit_json(self.data / "presentation" / "review_rows_001_041.json", lambda v: v.pop())
        self.rejected("Presentation row coverage")

    def test_front_view_cannot_change_the_canonical_result(self):
        path = self.outputs / "study_data_matches.xlsx"
        workbook = load_workbook(path)
        cell = workbook["Study review"]["C6"]
        cell.value = "Found" if cell.value != "Found" else "Not found locally"
        workbook.save(path)
        workbook.close()
        self.rejected("Study review!C6")

    def test_front_view_cannot_link_to_the_wrong_existing_card(self):
        path = self.outputs / "study_data_matches.xlsx"
        workbook = load_workbook(path)
        cell = workbook["Study review"]["G6"]
        cell.hyperlink = Hyperlink(ref=cell.coordinate, location="'Details'!A15")
        workbook.save(path)
        workbook.close()
        self.rejected("Internal link at Study review!G6")


if __name__ == "__main__":
    unittest.main()
