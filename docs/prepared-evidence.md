# Prepared evidence for EOLab

We wanted to turn the datasets identified in the study review into usable catalog entries, while keeping descriptions short and preserving the evidence behind them.

**All 19 descriptions classified as Matched are now accounted for.** The delivery contains 23 entries for those descriptions, plus the existing pilot barrier-input layer: **24 catalog entries in total**. The 21 new entries are in `matched/`; the three existing pilot entries remain in `pilot/` with their paths and identities preserved.

| Available in the catalog | Entries | What is included |
| --- | ---: | --- |
| Maps | 7 | Four forest-vulnerability rasters, terrestrial resistance, commercial fish catch, and the pilot barrier points. |
| Tables and workbooks | 8 | Carbon studies, fisheries metrics, heat exposure, site biodiversity/carbon, tree plots, dispersal traits, hydropower, and the pilot ATTO flux table. |
| Native grids available for download | 9 | Six WBGT scenarios and three tree grids. Their geographic CRS remains undocumented, so map geometry is withheld. |

Start with the [dataset list](../evidence/matched/reports/datasets.csv) or the [19-description coverage table](../evidence/matched/reports/study_coverage.csv). File paths in those tables are relative to `processed-evidence-data/`. Multiple scenarios can belong to one description, and the two site biodiversity/carbon descriptions share one prepared table. Entry counts are therefore different from description counts.

## What readers see

Each entry has a concise YAML description with its purpose, paper and dataset references, rights, variable meanings, time interpretation and limitations that affect use. The linked **Full review evidence and source history** file retains the original sheet rows, matching decisions, source links, detailed field definitions, source checksums and preparation checks. Original files are included as supporting assets.

The hydropower originals are grouped into one ZIP containing all 16 original KNN/BCSD result tables and the two inspected scripts. Every member was compared with its source checksum. The prepared CSV contains only the requested KNN mean/firm power results, with source scenario codes preserved.

An independent [YAML review](../evidence/matched/review/yaml-review.md) checked both completeness and readability, then checked that all generated sidecars matched the reviewed plans. The review led to clearer geographic coverage, heat-exposure meaning, soil depth, tree sampling definitions and time qualifications.

## What was checked

- Every selected source file was checked against its recorded checksum. Copied originals retain their bytes.
- COG conversion preserves the native CRS, grid, every full-resolution cell and mask. The resistance grid retains EPSG:5641; the vulnerability grids retain EPSG:4326.
- The fish-catch GeoPackage retains all 198 records and every attribute value. Its current reader identified 35 invalid polygons. Validity repair produced valid polygons with a maximum relative planar area change below `2e-14`, with repair details recorded per feature. Original archives remain available.
- CSV extraction checks the selected cells, row counts, field order, encodings and any declared decimal conversion. Formula-bearing carbon workbooks are preserved without recalculation.
- EOLab's actual discovery and native readers admitted the collection with all linked files present, metadata retained, repeated scans stable, and public map footprints expressed in WGS84. This is a filesystem/admission check; the running catalog still needs a rescan.

See the [preparation report](../evidence/matched/reports/preparation.json), [admission report](../evidence/matched/reports/admission.json), and [publication check](../evidence/matched/reports/publication.json). The [STAC preview](../evidence/matched/reports/stac-preview.json) illustrates the admitted metadata; its asset URLs are usable through EOLab after import.

## Questions that remain

The coverage table keeps dataset-specific limitations next to the corresponding files. The main outstanding questions are:

- **Nine grids need a confirmed CRS.** Latitude/longitude-looking coordinates do not establish a datum. The WBGT and tree grids are preserved and downloadable, with no invented map footprint.
- **Fish source rights need clarification.** The metadata names CC-BY-4.0 but also says “share alike.” The conflicting original text is retained; the sidecar does not assert a resolved license.
- **Carbon-study references need a crosswalk correction.** RefID 96 identifies two citations, and four of the 212 loss records have no cached RefID. Original formulas and saved values remain intact.
- **Some scientific definitions and periods remain uncertain.** Examples include the hydropower firm-power reliability criterion and scenario-period mapping, and exact seed-mass class boundaries. These are stated in the sidecars rather than inferred.

The earlier matching tables remain a historical snapshot. New inspection findings are recorded in the prepared evidence, including the carbon row-count explanation and three tree-plot establishment years of 2021 beyond the paper's stated range. Establishment years are not measurement dates.

This delivery covers the descriptions marked **Matched**, plus the existing supporting-input pilot layer. Partial matches, missing study outputs and unmatched local data remain in the earlier reconciliation for a later preparation pass. “Matched” establishes the association with the study sheet; it does not certify the study's calculations or suitability for every analysis.

## Rebuild or update the collection

Use Python 3.12 with `requirements-evidence.txt` and EOLab's compatible native GIS libraries. The fisheries archive also needs 7-Zip. In a conda-forge environment, set `GDAL_DATA` and `PROJ_DATA` to that environment's corresponding resource directories if they are not already configured.

Keep machine-specific roots in local environment variables. `WWF_EVIDENCE_SOURCE` identifies the source collection, currently kept in the ignored `data/evidence_data/` directory. `WWF_EVIDENCE_STAGE` identifies a **new** staging directory for the new matched entries, and `EOLAB_SOURCE` identifies a checkout with the reviewed sidecar importer.

```powershell
python scripts/prepare_matched_evidence.py --source-root "$env:WWF_EVIDENCE_SOURCE" --output-root "$env:WWF_EVIDENCE_STAGE" --report build/matched-preparation.json --sidecar-dir build/matched-sidecars
python scripts/validate_matched_evidence.py --data-root "$env:WWF_EVIDENCE_STAGE" --eolab-source "$env:EOLAB_SOURCE" --report build/matched-admission.json --items build/matched-stac.json
python scripts/build_evidence_delivery_report.py --output-dir build/evidence-review
python -m unittest discover -s tests/evidence -v
```

Edit the [plans](../evidence/matched/plans/) to change descriptions or preparation choices, then rebuild into a fresh staging directory. Existing outputs are never overwritten. Review changes before publishing the new `matched/` folder; keep `pilot/` in place. Source archives, rasters, tables and PDFs remain untracked.

For the combined published folder, run `validate_matched_evidence.py` with `--include-pilot` and `--data-root` set to the processed-data root. This also requires all 19 matched descriptions to be represented and verifies the existing pilot. Then use **Scan directories** in EOLab. The existing pilot preparation and refresh commands remain documented in the [pilot guide](evidence-pilot.md).
