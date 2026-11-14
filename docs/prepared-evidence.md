# Prepared evidence for EOLab

We wanted to turn the datasets identified in the study review into usable catalog entries, while keeping descriptions short and preserving the evidence behind them.

**All 19 descriptions classified as Matched are now accounted for.** The delivery contains 23 entries for those descriptions, plus the existing pilot barrier-input layer: **24 catalog entries in total**. The 21 new entries are in `matched/`; the three pilot entries remain in `pilot/`. All 24 have revised descriptions and linked scientific notes; data paths, catalog identities, scientific file bytes and data modification times are preserved.

| Available in the catalog | Entries | What is included |
| --- | ---: | --- |
| Maps | 7 | Four forest-vulnerability rasters, terrestrial resistance, commercial fish catch, and the pilot barrier points. |
| Tables and workbooks | 8 | Carbon studies, fisheries metrics, heat exposure, site biodiversity/carbon, tree plots, dispersal traits, hydropower, and the pilot ATTO flux table. |
| Native grids available for download | 9 | Six WBGT scenarios and three tree grids. Their geographic CRS remains undocumented, so map geometry is withheld. |

Read the committed [scientific notes](../evidence/notes/) to see what the studies found and how each supplied dataset contributes. Running `python scripts/build_evidence_delivery_report.py` creates the catalog summaries, dataset list and 19-description coverage table in ignored `build/evidence/delivery/`. These reports are generated locally, not committed. File paths in those tables are relative to `processed-evidence-data/`. Multiple scenarios can belong to one description, and the two site biodiversity/carbon descriptions share one prepared table. Entry counts are therefore different from description counts.

## What readers see

Each entry leads with the scientific question or finding, its relevance, and the role of that particular file. The summaries distinguish observed comparisons, models, research syntheses and ecological baselines. They do not attribute an entire paper’s conclusions to every input file.

The linked **Study findings, interpretation and sources** note (`evidence-summary.md`) gives the comparison, finding, interpretation, limitations and specific paper sections or figures behind the summary. The separate **Full review evidence and source history** file (`review-context.json`) combines original sheet rows, regenerated matching decisions, reviewed field definitions, checksums and preparation checks. On refresh, it also retains previously delivered full contexts in generated `provenance_history`; fresh builds have no prior-delivery history. Original scientific files remain supporting assets. Internal sheet identifiers and matching labels no longer appear in the public descriptions.

An independent [scientific framing review](../evidence/matched/review/evidence-framing-review.md) checked all 24 entries. Examples include the distinction between higher carbon stocks and faster accumulation, land-use comparisons versus before/after interventions, and the local ATTO carbon sink versus the paper’s broader regional result.

The hydropower originals are grouped into one ZIP containing all 16 original KNN/BCSD result tables and the two inspected scripts. Every member was compared with its source checksum. The prepared CSV contains only the requested KNN mean/firm power results, with source scenario codes preserved.

An independent [YAML review](../evidence/matched/review/yaml-review.md) checked completeness and readability of the descriptions that are now maintained as the canonical committed sidecars. The review led to clearer geographic coverage, heat-exposure meaning, soil depth, tree sampling definitions and time qualifications.

## What was checked

- Every selected source file was checked against its recorded checksum. Copied originals retain their bytes.
- COG conversion preserves the native CRS, grid, every full-resolution cell and mask. The resistance grid retains EPSG:5641; the vulnerability grids retain EPSG:4326.
- The fish-catch GeoPackage retains all 198 records and every attribute value. Its current reader identified 35 invalid polygons. Validity repair produced valid polygons with a maximum relative planar area change below `2e-14`, with repair details recorded per feature. Original archives remain available.
- CSV extraction checks the selected cells, row counts, field order, encodings and any declared decimal conversion. Formula-bearing carbon workbooks are preserved without recalculation.
- EOLab's actual discovery and native readers admitted the collection with all linked files present, metadata retained, repeated scans stable, and public map footprints expressed in WGS84. This is a filesystem/admission check; the running catalog still needs a rescan.

Current preparation and admission reports are generated under `build/evidence/matched/` and `build/evidence/pilot/`. The combined refresh audit is `build/evidence/metadata-refresh.json`. The commands below produce those local results and a STAC preview. Preview asset URLs become usable through EOLab after import; the preview is not a hosted catalog.

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
python scripts/prepare_matched_evidence.py --source-root "$env:WWF_EVIDENCE_SOURCE" --output-root "$env:WWF_EVIDENCE_STAGE" --report build/evidence/matched/preparation.json
python scripts/validate_matched_evidence.py --data-root "$env:WWF_EVIDENCE_STAGE" --eolab-source "$env:EOLAB_SOURCE" --report build/evidence/matched/admission.json --items build/evidence/matched/stac-preview.json
python scripts/build_evidence_delivery_report.py
python -m unittest discover -s tests/evidence -v
```

The command defaults to the committed [matched recipes](../evidence/matched/recipes/). Each recipe references a canonical [YAML sidecar](../evidence/matched/sidecars/), a [scientific note](../evidence/notes/) and a detailed [curation record](../evidence/curation/). Change the recipe when changing data selection or transformation; edit the YAML for catalog metadata, the Markdown note for scientific prose, and the curation record for detailed supporting interpretation.

A data rebuild needs a fresh staging directory; existing outputs are never overwritten. Review changes before publishing the new `matched/` folder and retain `pilot/`. Preparation copies the canonical YAML and renders the note with a link to the complete generated `review-context.json`. Source archives, rasters, tables and PDFs remain untracked. Rebuilding provenance uses the frozen inputs directly and does not require pre-existing reconciliation reports.

For the combined published folder, run `validate_matched_evidence.py` with `--include-pilot` and `--data-root` set to the processed-data root. This also requires all 19 matched descriptions to be represented and verifies the existing pilot. Then use **Scan directories** in EOLab. The existing pilot preparation and refresh commands remain documented in the [pilot guide](evidence-pilot.md).

### Refresh scientific descriptions

Edit the canonical [matched YAMLs](../evidence/matched/sidecars/) or [pilot YAMLs](../evidence/pilot/sidecars/), the [scientific notes](../evidence/notes/), and any affected [curation records](../evidence/curation/). Keep reviewed source interpretation and corrections in the curation records; the refresh retains prior delivered contexts in generated history. To check and export note previews without modifying a delivery or overwriting the canonical YAMLs:

```powershell
python scripts/refresh_evidence_metadata.py --export-only
python scripts/build_evidence_delivery_report.py
```

Preview notes are written under `build/evidence/matched/briefs/` and `build/evidence/pilot/briefs/`. They are generated copies; edit the sources above, not the previews.

For the existing combined collection, set `WWF_PROCESSED_EVIDENCE` to its root in your local environment:

```powershell
python scripts/refresh_evidence_metadata.py --data-root "$env:WWF_PROCESSED_EVIDENCE"
python scripts/validate_matched_evidence.py --data-root "$env:WWF_PROCESSED_EVIDENCE" --include-pilot --eolab-source "$env:EOLAB_SOURCE" --report build/evidence/matched/admission.json --items build/evidence/matched/stac-preview.json
```

The refresh checks both collections before replacing metadata. It adds or updates the scientific notes and updates YAMLs, full review context and preparation reports. Original data and supporting assets retain their bytes and modification times; dataset identities, native geometry and temporal declarations cannot change. Previous scientific preparation checks remain in the reports. Unexpected file changes stop publication. Caught replacement errors trigger rollback; replacements are atomic per file rather than a whole-directory transaction. Wait for validation to finish before running **Scan directories** in EOLab.
