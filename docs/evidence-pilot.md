# Forest vulnerability, river barriers and carbon exchange

These three studies offer different ways to investigate resilience: statistical signals of forest vulnerability, inputs for modeling fish access to habitat, and observed carbon exchange during drought. Start with the linked study notes to understand the finding and its limits. The prepared data are one raster, one vector layer and one table, each accompanied by catalog metadata, paper and source references, and its file-matching record.

| Study and use | Prepared file | What it contains | What to keep in mind |
| --- | --- | --- | --- |
| [Forest biomass vulnerability](../evidence/notes/wwf-tfvi-agb-01deg.md): examine statistical signals of forest response to climate and land-use pressures. | `tfvi-agb/tfvi-agb-0.1deg.tif` | The published 0.1-degree TFVI grid, encoded as a Cloud Optimized GeoTIFF. | Pan-tropical coverage, not an Amazon-only subset. Values are an index, not biomass stocks, collapse probabilities or measured intervention benefits. Exact map observation dates remain unresolved. |
| [Amazon river barriers](../evidence/notes/wwf-amazon-barrier-locations.md): inputs for modeling fish access to suitable habitat under climate change and hydropower expansion. | `amazon-barriers/amazon-barriers.gpkg` | 562 points: 359 dams and 203 waterfalls, with all 31 source attributes. | Current and future scenario inputs, not the connectivity results or impact rankings. Natural and human-made barriers differ. Some auxiliary field definitions remain unresolved. |
| [ATTO carbon exchange during the 2023 drought](../evidence/notes/wwf-atto-monthly-carbon-fluxes-2023.md): the local forest remained an annual carbon sink. | `atto-fluxes-2023/atto-monthly-carbon-fluxes-2023.csv` | Twelve monthly records of net carbon exchange, gross photosynthesis and ecosystem respiration, with their original date labels. | The tower represents a local forest area, not the whole Amazon carbon balance. These monthly estimates are not the original half-hourly measurements. The source's trajectory coordinates are not station coordinates. |

The pilot preparation command generates a three-row CSV review table alongside its JSON report under `build/evidence/pilot/`. The files, references and checks come from the committed reviewed sources.

These paths are relative to `processed-evidence-data/pilot/`. Each primary file has an adjacent `.eolab.yaml` sidecar. Original files are retained as supporting assets inside each dataset's `source/` directory. The original study-data collection is unchanged.

## What was checked

The preparation script checks source hashes before processing. It compares every full-resolution raster value and mask, every vector coordinate and decoded attribute, and every selected table value with the originals. The spatial files retain EPSG:4326; no reprojection, clipping, coordinate inference or geometry repair is applied. Raster overviews use nearest-neighbour sampling for display.

The EOLab check uses its existing filesystem discovery and native metadata readers, then its public metadata projection. It checks that supporting files do not become duplicate datasets, annotations and publication references survive, repeated discovery is stable, and public file links use catalog identities rather than machine paths. This is a local admission check, not a deployment or a write to a running STAC database. All three passed these local checks. The Docker service was unavailable, so no live HTTP/pgSTAC import was attempted. Rebuilding and validating writes current preparation and admission results under ignored `build/evidence/pilot/`; these reports are not committed.

The generated `build/evidence/pilot/stac-preview.json` is an inspection artifact. Its local asset URLs become usable after the datasets are imported into EOLab; the preview is not a standalone hosted catalog.

## Metadata and remaining questions

The canonical committed [sidecars](../evidence/pilot/sidecars/) contain the catalog description, references, rights, variable meanings and essential limitations. Each description explains the scientific finding and what the file provides. The adjacent `evidence-summary.md` note has **Findings**, **Using these data**, **Limits** and **Sources**, including specific paper passages. Both notes and data can be downloaded from the catalog.

Each dataset also includes `review-context.json`, the file-matching and preparation record. Worksheet matching labels remain here as history; they describe file identification, not scientific strength. A fresh build combines the original spreadsheet rows and regenerated matching records with preparation checks and the current reviewed interpretation in `curated_evidence`. For ATTO, that reviewed evidence explains the corrected date-column and coordinate meanings. A metadata refresh also preserves the previously delivered full contexts in generated `provenance_history`; a fresh build has no prior-delivery history.

The [pilot recipes](../evidence/pilot/recipes/) define source files, checksums and preparation choices. They reference the canonical YAMLs, [scientific Markdown notes](../evidence/notes/) and detailed [curation records](../evidence/curation/). Edit those sources directly. Preparation copies the YAMLs and renders `evidence-summary.md`, adding its link to the complete generated review context. Supporting-file declarations remain in the YAML so EOLab groups the originals with their prepared dataset instead of importing them again.

- **Raster time:** biomass response inputs span 2000–2018, while broader study/stressor records span 1982–2018. Neither is silently asserted to be an exact map observation interval. EOLab uses the original file modification time, explicitly labeled as such, while the scientific periods remain in the metadata.
- **Vector time and meaning:** current/future are source scenario labels, not verified observation dates. EOLab again uses a disclosed source-modification timestamp. The points are study inputs, not final connectivity outputs.
- **Table corrections:** the date column is `Time`, not `TimeYearMonth`. The complete source's `finalLat` and `finalLon` are mean STILT backward-trajectory endpoints, not fixed ATTO coordinates. Those earlier matching annotations are preserved as history and corrected explicitly for this pilot. The complete source lacks May 2021; the 2023 subset has all twelve months.
- **Source rights:** the raster and barrier package records declare CC-BY-4.0; the ATTO package declares CC0-1.0. Paper and dataset references remain separate. Article PDFs are not included in this delivery.

The initial pilot deferred the fisheries catch polygons after its reader reported invalid geometry. The [expanded delivery](prepared-evidence.md) now includes that layer, with a fresh reader check, documented repairs and preserved original data. Historical inspection results remain in its linked provenance.

## Rebuild the prepared files

Use a GIS-enabled Python 3.12 environment with `requirements-evidence.txt`. EOLab's vector admission also needs the `osgeo` Python bindings matched to its native GDAL library. A conda-forge environment containing `python=3.12`, `gdal`, `rasterio`, `fiona`, `pyproj`, `shapely`, `numpy`, `pyyaml`, `pydantic`, `jsonschema` and `ijson` is suitable. Record actual versions from the preparation report; GeoPackage byte hashes can change with library versions even when coordinates and values are unchanged.

Set `WWF_EVIDENCE_SOURCE`, `WWF_EVIDENCE_OUTPUT` and `EOLAB_SOURCE` in your local environment. They identify the source collection, a **new** output directory, and an EOLab checkout containing the merged sidecar importer. The source collection is currently under `data/evidence_data/`, which is Git-ignored. Keep these machine-specific settings untracked; source paths in the recipes remain relative to that collection. The workbook checksum checker excludes only this local source directory from its frozen input inventory.

From the repository root, in PowerShell:

```powershell
python scripts/prepare_evidence_pilot.py --source-root "$env:WWF_EVIDENCE_SOURCE" --output-root "$env:WWF_EVIDENCE_OUTPUT" --report build/evidence/pilot/preparation.json
python scripts/validate_evidence_pilot.py --data-root "$env:WWF_EVIDENCE_OUTPUT" --eolab-source "$env:EOLAB_SOURCE" --report build/evidence/pilot/admission.json --items build/evidence/pilot/stac-preview.json
python -m unittest discover -s tests/evidence -v
```

The preparer defaults to the committed pilot recipes. The `--report` option writes both JSON detail and a CSV summary; summary paths are relative to the pilot output directory.

The preparer refuses to overwrite an existing output directory and publishes the three datasets together after its checks pass. Give a rebuild a fresh destination; compare the reported content checks before replacing an earlier delivery.

### Refresh descriptions on an existing delivery

The pilot is now refreshed together with the remaining matched entries. Follow the [combined metadata refresh instructions](prepared-evidence.md#refresh-scientific-descriptions). They update all 24 descriptions and their linked scientific notes while preserving scientific files and catalog identities. The pilot-only refresh also understands scientific notes, but the combined command keeps this 24-entry delivery and its reports synchronized.

After validation, use **Scan directories** in EOLab. The same dataset paths and identifiers are retained. A metadata refresh prepares the files for rescanning; it does not itself update the running catalog.

The [schema snapshot](../evidence/pilot/eolab-item-v1.schema.json) was exported from EOLab's `descriptor_contract` module. It is EOLab's Apache-2.0-licensed authoring contract, not a new sidecar format maintained here. The recorded merged revision is `cee788e82e7577afb57681cc962acd764a67f3b6`; the reviewed PR source `73215e7d91dac57edad0882a388989e9c6bdf8a6` has identical file content. Use EOLab's own validator and readers again when adopting a later contract.

To make the pilot available in EOLab, expose the prepared directory within its configured source mount and scan it using the merged importer. Existing evidence can remain in place until the replacement has been checked in the application.
