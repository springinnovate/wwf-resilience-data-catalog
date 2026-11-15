# Study findings and prepared data

Use this collection to examine forest recovery and degradation, biodiversity, heat stress, connectivity, fisheries and water-management trade-offs. Follow a question below to the study's finding, limits and available data. The collection includes observations, research syntheses, modeled scenarios and ecological baselines; read the study's limits before transferring its findings to another place or intervention.

## Find a study

| Question | Study notes |
| --- | --- |
| How does disturbance history affect carbon loss and recovery? | [Forest carbon loss and regrowth](../evidence/notes/wwf-forest-carbon-loss-gain-compilation.md) |
| How do biodiversity and carbon differ across land uses and forest conditions? | [Eastern Amazon site comparisons](../evidence/notes/wwf-amazon-land-use-biodiversity-carbon.md) |
| How did a forest site exchange carbon during the 2023 drought? | [ATTO carbon exchange and historical comparison](../evidence/notes/wwf-atto-monthly-carbon-fluxes-2023.md) |
| Where do statistical signals of forest vulnerability differ? | [Biomass](../evidence/notes/wwf-tfvi-agb-01deg.md), [carbon uptake](../evidence/notes/wwf-tfvi-gpp-01deg.md), [water returned to the atmosphere](../evidence/notes/wwf-tfvi-aet-01deg.md), [surface warming](../evidence/notes/wwf-tfvi-lst-01deg.md) |
| How does modeled Amazon forest loss change heat stress? | Paired forest and savanna runs: historical [forest](../evidence/notes/wwf-wbgt-hist-forested.md), [savanna](../evidence/notes/wwf-wbgt-hist-deforested.md); RCP4.5 [forest](../evidence/notes/wwf-wbgt-rcp4-forested.md), [savanna](../evidence/notes/wwf-wbgt-rcp4-deforested.md); RCP8.5 [forest](../evidence/notes/wwf-wbgt-rcp8-forested.md), [savanna](../evidence/notes/wwf-wbgt-rcp8-deforested.md) |
| How many more people could face heat stress in those scenarios? | [Additional population exposure in Brazil](../evidence/notes/wwf-brazil-heat-stress-exposure.md) |
| How could dams affect fish access to suitable habitat? | [Dam and waterfall inputs to river-connectivity modeling](../evidence/notes/wwf-amazon-barrier-locations.md) |
| Can total catch hide changes in a fishery? | [Fisheries harvest trends and resilience](../evidence/notes/wwf-amazon-fisheries-annual-metrics.md) |
| How are fisheries connected to wetlands across basins and borders? | [Historical commercial catches and wetlands](../evidence/notes/wwf-amazon-commercial-fish-catch.md) |
| What barriers are assumed in terrestrial-connectivity modeling? | [Amazon terrestrial resistance](../evidence/notes/wwf-amazon-terrestrial-resistance.md) |
| What natural tree variation provides context for conservation and restoration? | Baselines for [species richness](../evidence/notes/wwf-amazon-tree-richness.md), [diversity](../evidence/notes/wwf-amazon-tree-diversity.md) and [tree density](../evidence/notes/wwf-amazon-tree-density.md), with [plot observations](../evidence/notes/wwf-amazon-tree-plot-metadata.md) |
| Which tree species may depend on animals for seed movement? | [Tree dispersal and seed traits](../evidence/notes/wwf-amazon-tree-dispersal-traits.md) |
| How might upstream irrigation and climate affect hydropower? | [Chaglla hydropower scenarios](../evidence/notes/wwf-chaglla-hydropower-knn.md) |

## Available files

The delivery contains **24 catalog entries**: 23 covering the 19 descriptions classified as Matched in the original file review, plus the pilot barrier-input layer. There are 21 entries in `matched/` and three in `pilot/`. Each has a catalog description and study note, with source files and references recorded. Descriptive updates preserve data paths, catalog identities, scientific file bytes and data modification times.

| Available in the catalog | Entries | What is included |
| --- | ---: | --- |
| Maps | 7 | Four forest-vulnerability rasters, terrestrial resistance, commercial fish catch, and the pilot barrier points. |
| Tables and workbooks | 8 | Carbon studies, fisheries metrics, heat exposure, site biodiversity/carbon, tree plots, dispersal traits, hydropower, and the pilot ATTO flux table. |
| Native grids available for download | 9 | Six WBGT scenarios and three tree grids. Their geographic CRS remains undocumented, so map geometry is withheld. |

Running `python scripts/build_evidence_delivery_report.py` creates `catalog-summaries.md`, grouped by publication, with each entry's description, primary file, supporting data files and study-note path. `datasets.csv` lists primary files and review records; the separate `study_coverage.csv` checks the 19 matched descriptions. These reports are generated under ignored `build/evidence/delivery/`, not committed. Their file paths are relative to `processed-evidence-data/`; open the corresponding EOLab entry to download a file, or find it in the prepared folder. Multiple scenarios can belong to one original description, and the two site biodiversity/carbon descriptions share one prepared table. Entry counts are therefore different from description counts.

The hydropower originals are grouped into one ZIP containing all 16 original KNN/BCSD result tables and the two inspected scripts. The prepared CSV contains only the requested KNN mean/firm power results, with source scenario codes preserved.

## Study notes and source records

Each entry includes a downloadable `evidence-summary.md` with **Findings**, **Using these data**, **Limits** and **Sources**. It cites the paper sections or figures behind its statements.

Use `review-context.json` to inspect file matching and preparation: original sheet rows, matching decisions, reviewed field definitions, checksums and checks. Metadata refreshes retain previously delivered contexts in `provenance_history`; fresh builds have no prior-delivery history. Original scientific files remain supporting assets.

## What was checked

- Every selected source file was checked against its recorded checksum. Copied originals retain their bytes.
- COG conversion preserves the native CRS, grid, every full-resolution cell and mask. The resistance grid retains EPSG:5641; the vulnerability grids retain EPSG:4326.
- The fish-catch GeoPackage retains all 198 records and every attribute value. Its current reader identified 35 invalid polygons. Validity repair produced valid polygons with a maximum relative planar area change below `2e-14`, with repair details recorded per feature. Original archives remain available.
- CSV extraction checks the selected cells, row counts, field order, encodings and any declared decimal conversion. Formula-bearing carbon workbooks are preserved without recalculation.
- Every member of the hydropower ZIP was compared with its source checksum.
- EOLab's actual discovery and native readers admitted the collection with all linked files present, metadata retained, repeated scans stable, and public map footprints expressed in WGS84. This is a filesystem/admission check; the running catalog still needs a rescan.

The recorded [scientific framing review](../evidence/matched/review/evidence-framing-review.md) and [YAML review](../evidence/matched/review/yaml-review.md) retain the earlier interpretation and metadata checks.

Current preparation and admission reports are generated under `build/evidence/matched/` and `build/evidence/pilot/`. The combined refresh audit is `build/evidence/metadata-refresh.json`. The commands below produce those local results and a STAC preview. Preview asset URLs become usable through EOLab after import; the preview is not a hosted catalog.

## Questions that remain

The coverage table keeps dataset-specific limitations next to the corresponding files. The main outstanding questions are:

- **Nine grids need a confirmed CRS.** Latitude/longitude-looking coordinates do not establish a datum. The WBGT and tree grids are preserved and downloadable, with no invented map footprint.
- **Fish source rights need clarification.** The metadata names CC-BY-4.0 but also says “share alike.” The conflicting original text is retained; the sidecar does not assert a resolved license.
- **Carbon-study references need a crosswalk correction.** RefID 96 identifies two citations, and four of the 212 loss records have no cached RefID. Original formulas and saved values remain intact.
- **Some scientific definitions and periods remain uncertain.** Examples include the hydropower firm-power reliability criterion and scenario-period mapping, and exact seed-mass class boundaries. These are stated in the sidecars rather than inferred.

The earlier matching tables remain a historical snapshot. New inspection findings are recorded in the prepared evidence, including the carbon row-count explanation and three tree-plot establishment years of 2021 beyond the paper's stated range. Establishment years are not measurement dates.

This delivery covers the descriptions marked **Matched**, plus the supporting-input pilot layer. Partial matches, missing study outputs and unmatched local data remain in the earlier reconciliation for a later preparation pass. The historical `study_data_matches.xlsx` workbook answers which requested files were found. Its matching labels do not grade study quality or intervention effectiveness.

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
