# First EOLab evidence datasets

This pilot prepares one raster, one vector and one nonspatial table from the study review. Each has a usable data file, an EOLab YAML sidecar, links to its paper and source package, and a copy of the original matching evidence.

| Dataset | Prepared file | What it contains | What to keep in mind |
| --- | --- | --- | --- |
| Tropical forest biomass vulnerability | `tfvi-agb/tfvi-agb-0.1deg.tif` | The published 0.1-degree TFVI grid, encoded as a Cloud Optimized GeoTIFF. | Pan-tropical coverage, not an Amazon-only subset. Values are an index, not biomass stocks or probabilities. Exact map observation dates remain unresolved. |
| Amazon river barriers | `amazon-barriers/amazon-barriers.gpkg` | 562 points: 359 dams and 203 waterfalls, with all 31 source attributes. | Supporting input locations, including current and future scenarios. These are not the missing connectivity indices or impact rankings. Some auxiliary field definitions remain unresolved. |
| ATTO carbon fluxes, 2023 | `atto-fluxes-2023/atto-monthly-carbon-fluxes-2023.csv` | Twelve monthly records of NEE, GPP and ecosystem respiration, with their original date labels. | Monthly derivatives, not the original half-hourly measurements. The source's trajectory coordinates are not station coordinates. |

The [three-row review table](../evidence/pilot/reports/evidence_pilot.csv) lists the files, references and checks.

These paths are relative to `processed-evidence-data/pilot/`. Each primary file has an adjacent `.eolab.yaml` sidecar. Original files are retained as supporting assets inside each dataset's `source/` directory. The original study-data collection is unchanged.

## What was checked

The preparation script checks source hashes before processing. It compares every full-resolution raster value and mask, every vector coordinate and decoded attribute, and every selected table value with the originals. The spatial files retain EPSG:4326; no reprojection, clipping, coordinate inference or geometry repair is applied. Raster overviews use nearest-neighbour sampling for display.

The EOLab check uses its existing filesystem discovery and native metadata readers, then its public metadata projection. It checks that supporting files do not become duplicate datasets, annotations and publication references survive, repeated discovery is stable, and public file links use catalog identities rather than machine paths. This is a local admission check, not a deployment or a write to a running STAC database. All three passed these local checks. The Docker service was unavailable, so no live HTTP/pgSTAC import was attempted. See the [preparation report](../evidence/pilot/reports/evidence_pilot.json) and [EOLab admission report](../evidence/pilot/reports/evidence_pilot_admission.json) for the actual results.

The [public STAC preview](../evidence/pilot/reports/evidence_pilot_stac.json) is an inspection artifact. Its local asset URLs become usable after the datasets are imported into EOLab; the preview is not a standalone hosted catalog.

## Metadata and remaining questions

The [sidecar copies](../evidence/pilot/sidecars/) contain the catalog description, references, rights, variable meanings and essential limitations. “Matched to sheet description” and “Supporting input for sheet descriptions” describe the association with the original workbook; they do not certify scientific validity or suitability for a particular analysis.

Each dataset links to **Full review evidence and source history** (`review-context.json`). This preserves the original spreadsheet rows and matching records. Its `pilot_sidecar_snapshot` also preserves every field from the first pilot sidecar: detailed source citations, processing notes, checksums, technical inventories, complete field dictionaries, limitations and corrections. It is labeled as historical evidence so old comments and readiness judgments can be read in context. For ATTO, `pilot_sidecar_snapshot.metadata.annotations.pilot_corrections` explains the corrected date-column and coordinate interpretations.

The versioned [records](../evidence/pilot/records.json) are the authoring source for both the YAML and linked review context. Edit those records and regenerate the files together. Supporting-file declarations remain in the YAML so EOLab groups the originals with their prepared dataset instead of importing them again.

- **Raster time:** biomass response inputs span 2000–2018, while broader study/stressor records span 1982–2018. Neither is silently asserted to be an exact map observation interval. EOLab uses the original file modification time, explicitly labeled as such, while the scientific periods remain in the metadata.
- **Vector time and meaning:** current/future are source scenario labels, not verified observation dates. EOLab again uses a disclosed source-modification timestamp. The points are study inputs, not final connectivity outputs.
- **Table corrections:** the date column is `Time`, not `TimeYearMonth`. The complete source's `finalLat` and `finalLon` are mean STILT backward-trajectory endpoints, not fixed ATTO coordinates. Those earlier matching annotations are preserved as history and corrected explicitly for this pilot. The complete source lacks May 2021; the 2023 subset has all twelve months.
- **Source rights:** the raster and barrier package records declare CC-BY-4.0; the ATTO package declares CC0-1.0. Paper and dataset references remain separate. Article PDFs are not included in this delivery.

The fisheries catch polygons were considered for the vector example but deferred: 147 of 198 source geometries failed validity checks. A later geometry-repair task would need to document its effects. The point layer lets this first pilot exercise EOLab without introducing that additional transformation.

## Rebuild the prepared files

Use a GIS-enabled Python 3.12 environment with `requirements-evidence.txt`. EOLab's vector admission also needs the `osgeo` Python bindings matched to its native GDAL library. A conda-forge environment containing `python=3.12`, `gdal`, `rasterio`, `fiona`, `pyproj`, `shapely`, `numpy`, `pyyaml`, `pydantic`, `jsonschema` and `ijson` is suitable. Record actual versions from the preparation report; GeoPackage byte hashes can change with library versions even when coordinates and values are unchanged.

Set `WWF_EVIDENCE_SOURCE`, `WWF_EVIDENCE_OUTPUT` and `EOLAB_SOURCE` in your local environment. They identify the source collection, a **new** output directory, and an EOLab checkout containing the merged sidecar importer. The source collection is currently under `data/evidence_data/`, which is Git-ignored. Keep these machine-specific settings untracked; source paths in the records remain relative to that collection. The workbook checksum checker excludes only this local source directory from its frozen input inventory.

From the repository root, in PowerShell:

```powershell
python scripts/prepare_evidence_pilot.py --source-root "$env:WWF_EVIDENCE_SOURCE" --output-root "$env:WWF_EVIDENCE_OUTPUT" --report build/evidence-pilot.json --sidecar-dir build/evidence-sidecars
python scripts/validate_evidence_pilot.py --data-root "$env:WWF_EVIDENCE_OUTPUT" --eolab-source "$env:EOLAB_SOURCE" --report build/evidence-admission.json --items build/evidence-stac.json
python -m unittest discover -s tests/evidence -v
```

The `--report` option writes both JSON detail and a CSV summary; summary paths are relative to the pilot output directory.

The preparer refuses to overwrite an existing output directory and publishes the three datasets together after its checks pass. Give a rebuild a fresh destination; compare the reported content checks before replacing an earlier delivery.

### Refresh descriptions on an existing delivery

After editing the records, set `WWF_EVIDENCE_OUTPUT` to the existing pilot directory and run:

```powershell
python scripts/prepare_evidence_pilot.py --source-root "$env:WWF_EVIDENCE_SOURCE" --output-root "$env:WWF_EVIDENCE_OUTPUT" --refresh-metadata --report build/evidence-pilot.json --sidecar-dir evidence/pilot/sidecars
python scripts/validate_evidence_pilot.py --data-root "$env:WWF_EVIDENCE_OUTPUT" --eolab-source "$env:EOLAB_SOURCE" --report build/evidence-admission.json --items build/evidence-stac.json
```

The refresh verifies source and delivered-file hashes before replacing the YAMLs, linked review-context files and preparation report. Scientific files retain their bytes and modification times. The report keeps the original transformation checks and records the metadata refresh separately. If files have changed unexpectedly, it stops for review. Changes to data selection or processing require a fresh build; the refresh also refuses changes to temporal declarations or local asset locations. Files are replaced individually, with rollback on reported errors. Wait for the refresh and validation to finish before rescanning.

After validation, use **Scan directories** in EOLab. The same dataset paths and identifiers are retained. A metadata refresh prepares the files for rescanning; it does not itself update the running catalog.

The [schema snapshot](../evidence/pilot/eolab-item-v1.schema.json) was exported from EOLab's `descriptor_contract` module. It is EOLab's Apache-2.0-licensed authoring contract, not a new sidecar format maintained here. The recorded merged revision is `cee788e82e7577afb57681cc962acd764a67f3b6`; the reviewed PR source `73215e7d91dac57edad0882a388989e9c6bdf8a6` has identical file content. Use EOLab's own validator and readers again when adopting a later contract.

To make the pilot available in EOLab, expose the prepared directory within its configured source mount and scan it using the merged importer. Existing evidence can remain in place until the replacement has been checked in the application.
