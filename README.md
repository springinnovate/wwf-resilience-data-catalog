# WWF resilience data catalog

This repository preserves the study-data reconciliation that will inform a future STAC catalog.

**The main reviewable result is [study_data_matches.xlsx](outputs/study_data_matches.xlsx).** It links each supplied dataset description to its paper, article DOI and publisher page, local files, match status, evidence and remaining limitations. It also includes unmatched sheet entries and local scientific data that do not correspond to a supplied description.

The workbook is a generated review artifact. The versioned source sheet, file manifest and reviewed decisions in [`data/`](data/) are the rebuild inputs. This repository does not yet contain a STAC catalog or the underlying study datasets.

## Current snapshot

The reconciliation was completed on **13 November 2026** (local date), covering 78 descriptions, 30 verified paper identities, and 1,882 substantive local files across 23 study folders.

| Match status | Descriptions | Meaning |
| --- | ---: | --- |
| Matched | 19 | The described product was identified from contents, metadata or explicit code provenance. |
| Partial match | 29 | Only part of the requested content, or a filtered/processed/alternate-format counterpart, was found. |
| Related inputs/code only | 8 | The study package is identified, but the requested output is missing. |
| Different product | 1 | An inspected candidate represents a different quantity: SPI rather than the requested SPEI. |
| No local match | 21 | No corresponding package was found locally; availability elsewhere is not ruled out. |

`UnmatchedLocal` contains **627 physical files and 43 archived members/layers**: additional scientific products or unresolved data. These are file/layer entries, not 670 independent datasets. Code, figures, documentation, inputs and sidecars have their own dispositions. Duplicate files and shapefile components remain visible.

Every substantive file has one disposition. All 327 non-directory ZIP members, 126 nested drought-archive files, 209 fish-geodatabase physical components and 21 fish-geodatabase layers are indexed separately: 683 archive entries in total. Archive entries are not added to physical-file counts. The hash-identical `test.rar` copy uses the original fish payload's member inventory.

## Read the result

Download the [Excel workbook](outputs/study_data_matches.xlsx) to open it in Excel or another spreadsheet application. GitHub also displays the text tables:

| Artifact | Purpose |
| --- | --- |
| [`outputs/matches.csv`](outputs/matches.csv) | All 78 descriptions, paper/publisher links, files, statuses and limitations. |
| [`outputs/unmatched_sheet_entries.csv`](outputs/unmatched_sheet_entries.csv) | The 30 descriptions without a confirmed full or partial product match. |
| [`outputs/review_gaps.csv`](outputs/review_gaps.csv) | All 59 descriptions needing product-match review, including partial matches. Metadata gaps can also remain on matched rows. |
| [`outputs/unmatched_local_data.csv`](outputs/unmatched_local_data.csv) | Additional/unresolved local scientific files and archive members/layers. |
| [`outputs/asset_links.csv`](outputs/asset_links.csv) | Expanded row-to-asset links with workbook sheet, variable, member or layer selectors. |
| [`outputs/all_local_files.csv`](outputs/all_local_files.csv), [`outputs/archive_assets.csv`](outputs/archive_assets.csv) | Complete file and archive dispositions. |
| [`outputs/papers.csv`](outputs/papers.csv) | Article DOIs, publisher URLs, verification sources and supplied/verified publication years. |
| [`outputs/reconciliation.json`](outputs/reconciliation.json) | Combined structured results for downstream processing. |
| [`outputs/matching_summary.html`](outputs/matching_summary.html) | Searchable summary; download and open locally. |

The workbook includes the same tables plus `ReadMe`, `SourceSheet` and `StatusDefinitions` tabs. `UnmatchedSheet` excludes partial matches, which are in `Matches` and `ReviewGaps`.

Local paths are relative to an external `evidence_data` directory. They are evidence locators, not download URLs. `!` separates an archive from its member or nested archive; selectors name a table, variable or geodatabase layer. Article publisher links are kept separate from the source sheet's repository/download references.

## Rebuild from a fresh checkout

Use **Python 3.11 or newer**; continuous integration runs Python 3.12 on Windows and Linux. The report rebuild needs only the committed inputs and the packages in [`requirements.txt`](requirements.txt). It requires no network drive, GIS libraries, credentials, study datasets or model execution. Installing dependencies requires a package source or an existing local wheel cache.

From the repository root, in a Python environment of your choice:

```sh
python -m pip install -r requirements.txt
python scripts/check_inputs.py
python scripts/build_reconciliation.py
python scripts/validate_reconciliation.py
```

The builder writes the workbook, HTML, CSV, JSON, summary and validation files to `outputs/`. Use an alternate directory to compare a rebuild with the committed result:

```sh
python scripts/build_reconciliation.py --output-dir build/rebuilt
python scripts/validate_reconciliation.py --output-dir build/rebuilt
python scripts/compare_outputs.py build/rebuilt
python -m unittest discover -s tests -v
```

All scripts resolve default locations relative to this checkout, so they can also be invoked by absolute path from another working directory. `--input-dir` selects a complete alternate input snapshot. The builder refuses overlapping input/output directories.

`data/snapshot.json` records the original report timestamp and expected coverage. That timestamp is retained during rebuilds; it is not the wall-clock time of the latest run. Workbook timestamps and ZIP entry timestamps are fixed, and literal XML CRLF line endings are normalized to LF to remove the platform's text-mode serialization difference. Output comparison checks text bytes and the uncompressed XLSX package contents, allowing differences in ZIP compression metadata across runtimes.

Validation checks source-sheet hashes and exact text, record uniqueness, decision coverage, paper and asset references, archive coverage, unmatched-data sets, CSV/JSON/workbook agreement and literal treatment of spreadsheet text. It verifies the recorded reconciliation; it does not independently validate the studies' scientific calculations or recheck live publisher pages.

## Inputs, provenance and updates

| Location | Contents |
| --- | --- |
| [`data/source/`](data/source/) | Exact pasted TSV, parsed 33-column records, a metadata-only file manifest and ZIP member inventory. |
| [`data/decisions/`](data/decisions/) | Reviewed row/file/member decisions and the verified paper registry. These preserve expert judgments and their limitations. |
| [`data/evidence/`](data/evidence/) | Fish layer schemas, nested-archive names/headers and the recorded local-folder parity check. Scientific sample values are excluded. |
| [`data/snapshot.json`](data/snapshot.json) | Snapshot date, source hash, expected counts and explicit assessed/unmatched row IDs. |
| [`data/checksums.sha256`](data/checksums.sha256) | Checksums of all committed input files. |
| [`scripts/`](scripts/) | Rebuild, validation and optional local inspection tools. |
| [`docs/stac-readiness.md`](docs/stac-readiness.md) | Concrete outstanding work before STAC publication, with row references. |

The source was a **tab-delimited paste from Excel**, including five quoted multiline records, not an original `.xlsx` file. Parsing uses Python's strict CSV reader with a tab delimiter. The original bytes are retained; the SHA256 is `60d713a723995d2566ee1f32823868089e1aafa04fa4ec7c8973bfa976201632`. Machine-specific absolute paths were removed from metadata; relative study paths and all 33 source columns are preserved. Publisher identities were checked using publisher/article or author-institution records; supporting URLs and year distinctions are in the paper registry.

The file manifest retains 3,226 physical-file records, including 1,344 OS housekeeping files excluded from report counts. It preserves selected metadata from the earlier inspection rather than the full sampled scientific data. The original file inspection used headers, bounded samples, README/EML documents and relevant source code. It did not execute study models or validate every raster cell. The final local parity check found no path, size or modification-time changes; that check is not a complete hash audit of the bulk data.

Rebuilding **does not automatically discover matches or repeat the literature review**. To update the reconciliation:

1. Inspect new or changed packages and record the evidence. Keep bulk source data outside this repository. The optional [inspection tools](docs/inspection.md) can compare the local folder with the manifest and inspect the known archives.
2. Update the source/manifest and the appropriate reviewed decision JSON. Preserve existing row/paper identifiers where possible. New descriptions and files need explicit decisions; do not infer matches merely from a shared folder or paper.
3. Update the explicit snapshot counts/row lists and report timestamp after completing the review. Update the notes when an outstanding issue is resolved.
4. Review the input diff, then run `python scripts/check_inputs.py --write` to accept the new input bytes. Rebuild and validate, and commit the inputs, outputs and notes together.

Workbook edits are **not** imported by the scripts and will be overwritten on rebuild. Apply corrections to the source/decision inputs first. A changed source paste also requires updating its recorded hash and parsed representation, with a deliberate row-ID migration if records were reordered.

Identifiers are local crosswalk keys: `row_id` numbers the parsed data records, `paper_id` identifies a paper, `asset_id` identifies an indexed file/member/layer, `parent_file_id` points to its physical container, and `link_id` identifies a particular row/asset/selector relationship. Asset IDs derive from relative paths and selectors; renaming/reorganizing files requires a migration rather than treating those IDs as permanent external identifiers.

## Before STAC

The [readiness notes](docs/stac-readiness.md) give the full row-by-row priorities. The main outstanding work is to:

- Locate seven absent study packages and requested outputs missing from otherwise identified packages.
- Resolve partial content and discrepancies: SPI versus SPEI, dieback thresholds, filtered species/plot counts, raw versus processed tables, and scenario/time coverage.
- Confirm spatial reference systems, observation/model periods, units, variable definitions, provenance, source versions and licenses. Filesystem timestamps do not establish observation dates.
- Decide which of the additional local scientific products belong in the catalog; reconcile duplicates and overlapping descriptions into logical datasets.
- Choose stable asset hosting and an archive/extraction policy, then design Collections, Items, asset roles and appropriate extensions for the selected products. Some nonspatial tables may be better represented as related resources.
- Generate and validate STAC only after those decisions are recorded. A successful workbook rebuild or a `Matched` label is not a declaration of STAC readiness.

## License and source rights

The existing [Apache-2.0 license](LICENSE) is retained for this project's code and original annotations. It does not establish redistribution rights for the referenced papers, descriptions or third-party study datasets. Preserve their attribution and applicable licenses, and confirm permissions before publishing source data as catalog assets. Bulk data, article PDFs and sampled scientific observations are not included here.
