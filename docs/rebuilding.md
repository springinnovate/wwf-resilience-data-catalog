# Rebuilding and maintaining the review

The workbook and reports are generated from the versioned source sheet, file manifest, reviewed matching decisions and presentation text in [`data/`](../data/). Rebuilding reproduces the recorded review; it does not inspect the study datasets again, discover new matches or repeat the paper search.

## Rebuild from a fresh checkout

Use **Python 3.11 or newer**. Continuous integration runs Python 3.12 on Windows and Linux. The rebuild needs only the committed inputs and the packages in [`requirements.txt`](../requirements.txt): pinned versions of `openpyxl` and `et-xmlfile`. It requires no network drive, GIS libraries, credentials, study datasets or model execution. Installing dependencies requires a package source or an existing local wheel cache.

From the repository root, in a Python environment of your choice:

```sh
python -m pip install -r requirements.txt
python scripts/check_inputs.py
python scripts/build_reconciliation.py
python scripts/validate_reconciliation.py
```

The builder writes **15 generated files** to the ignored `build/reconciliation/` directory, including `study_data_matches.xlsx`, detailed CSV/JSON results and the short reader summaries. These files are not committed. To check that repeated builds agree:

```sh
python scripts/build_reconciliation.py --output-dir build/reconciliation-repeat
python scripts/validate_reconciliation.py --output-dir build/reconciliation-repeat
python scripts/compare_outputs.py build/reconciliation-repeat --expected build/reconciliation
python -m unittest discover -s tests -v
```

Scripts resolve their default locations relative to the checkout, so they can also be invoked by absolute path from another working directory. Explicit relative path arguments are interpreted from the current working directory. `--input-dir` selects a complete alternate input snapshot for the builder and validator. The builder refuses overlapping input/output directories.

[`data/snapshot.json`](../data/snapshot.json) records the original report timestamp and expected coverage. That timestamp is retained during rebuilds; it is not the wall-clock time of the latest run. Workbook timestamps and ZIP entry timestamps are fixed. Literal XML CRLF line endings are normalized to LF to remove the platform's text-mode serialization difference. Output comparison checks text bytes and the uncompressed XLSX package contents, allowing differences in ZIP compression metadata across runtimes.

Validation checks source-sheet hashes and exact text, record uniqueness, decision coverage, paper and asset references, archive coverage, unmatched-data sets, CSV/JSON/workbook agreement and literal treatment of spreadsheet text. It verifies the recorded reconciliation; it does not independently validate scientific calculations or recheck live publisher pages. The [CI workflow](../.github/workflows/rebuild.yml) runs the checksum, rebuild, validation, comparison and test commands on both operating systems.

## Rebuild the article download table

The article-search report is separate from the study-data review. [`scripts/build_article_report.py`](../scripts/build_article_report.py) reads [`data/articles/article_search.json`](../data/articles/article_search.json) and [`data/decisions/papers_verified.json`](../data/decisions/papers_verified.json) directly to write **two generated files** in ignored `build/articles/`: `article_downloads.xlsx` and `article_downloads.csv`. It does not need a pre-existing reconciliation report.

From the repository root:

```sh
python scripts/check_inputs.py
python scripts/build_article_report.py
```

This reproduces the **recorded search results**. It does not search publishers, retry blocked links, download articles or confirm that a manual download will work. A normal report rebuild does not need the local PDFs. If the PDFs are present in `wwf-resilience-articles/`, optionally check each PDF's file signature, size and SHA256 hash with:

```sh
python scripts/build_article_report.py --verify-local
```

To compare two article-report builds:

```sh
python scripts/build_article_report.py --output-dir build/articles-repeat
python scripts/compare_outputs.py build/articles-repeat --expected build/articles
```

To record a later successful download, first confirm that the file is the intended full article or clearly labelled manuscript, rather than a supplement or access-error page. Update that paper's search record with the source, filename, version, validation metadata and any remaining caveat. Keep the PDF in the ignored `wwf-resilience-articles/` folder; do not add article files to Git. Review the changed record, refresh the input checksums with `python scripts/check_inputs.py --write`, then rebuild the article report and verify the local files. A report rebuild alone must not change an access result from blocked to downloaded.

The `local_directory` field must use a repository-relative path with forward slashes. CSV file paths are relative to the repository root; Excel PDF hyperlinks are relative to the actual workbook location. Rebuild after moving only the workbook to a different folder. Moving the entire checkout preserves its links. For repeatability comparisons, use sibling output folders so their relative PDF links are the same. If the article folder changes within the checkout, update its relative path, keep it ignored, refresh the input checksum and rebuild both tables. Do not publish drive letters, usernames or full machine paths in notes, reports or PR descriptions. The recorded search date and download results do not change merely because files move.

## Inputs and their roles

| Location | Contents |
| --- | --- |
| [`data/source/`](../data/source/) | Exact pasted TSV, parsed 33-column records, a metadata-only file manifest and ZIP member inventory. |
| [`data/decisions/`](../data/decisions/) | Reviewed row/file/member decisions and the verified paper registry. These preserve the matching judgments and their limitations. |
| [`data/evidence/`](../data/evidence/) | Fish layer schemas, nested-archive names/headers and the recorded local-folder parity check. Scientific sample values are excluded. |
| [`data/presentation/`](../data/presentation/) | Short labels and summaries for readers. These explain the decisions without replacing the original descriptions or detailed evidence. |
| [`data/articles/article_search.json`](../data/articles/article_search.json) | Recorded article searches, access results, version notes and metadata for the local PDFs. The PDFs themselves are in the ignored local article folder. |
| [`data/snapshot.json`](../data/snapshot.json) | Snapshot date, source hash, expected counts and explicit assessed/unmatched row IDs. |
| [`data/checksums.sha256`](../data/checksums.sha256) | Checksums for the 18 input files: the 14 original snapshot files, three presentation files and the article-search record. The checksum file does not include itself. |
| [`scripts/`](../scripts/) | Rebuild, validation and optional local inspection tools. |

The source was a **tab-delimited paste from Excel**, including five quoted multiline records, not an original `.xlsx` file. Parsing uses Python's strict CSV reader with a tab delimiter. The original bytes are retained; their SHA256 is `60d713a723995d2566ee1f32823868089e1aafa04fa4ec7c8973bfa976201632`. Machine-specific absolute paths were removed from metadata; relative study paths and all 33 source columns are preserved. Publisher identities were checked using publisher/article or author-institution records; supporting URLs and year distinctions remain in the paper registry.

The manifest retains 3,226 physical-file records, including 1,344 OS housekeeping files excluded from report counts. It preserves metadata from the earlier inspection rather than sampled scientific observations. Inspection used headers, bounded samples, README/EML documents and relevant code; it did not execute study models or validate every raster cell. The final local parity check found no path, size or modification-time changes. That was not a complete hash audit of the bulk data.

All 1,882 substantive files have a recorded classification. There are also 683 archive entries: 327 non-directory, non-OS ZIP members, 126 nested drought-archive files, 209 fish-geodatabase physical components and 21 fish-geodatabase layers. These entries are not added to physical-file counts. The hash-identical `test.rar` copy uses the original fish payload's member inventory.

## Editing reader-facing text

The three presentation inputs are:

- [`review_rows_001_041.json`](../data/presentation/review_rows_001_041.json): descriptions 001-041.
- [`review_rows_042_078.json`](../data/presentation/review_rows_042_078.json): descriptions 042-078.
- [`other_data_notes.json`](../data/presentation/other_data_notes.json): additional-data summaries for 16 papers.

Each review-row record has `row_id`, `dataset_label`, `found` and `attention`. Keep the label to 65 characters, the finding to 180 and the attention text to 190. Summarize the evidence plainly, retain uncertainty and important discrepancies, and avoid introducing new scientific claims. Other-data notes have `paper_id` and `summary`; the file/archive counts are calculated from the matching decisions, not manually entered in the notes.

The short review CSV uses `row_id`, `dataset`, `match_result`, `what_we_found`, `needs_checking`, `paper` and `publisher_link`. The other-data CSV uses `paper_id`, `paper`, `publisher_link`, `additional_data`, `files` and `archive_entries`.

Reader-facing result labels map to the existing detailed statuses:

| Reader label | Detailed matching status |
| --- | --- |
| Found | Matched |
| Partly found | Partial match |
| Supporting files only | Related inputs/code only |
| Different data | Different product |
| Not found locally | No local match |

Changing a short label or explanation does not change a matching decision. The original descriptions and full evidence remain in the detailed records. The existing machine-readable CSV/JSON tables retain their matching schema and terminology. If the evidence changes, update the reviewed decision first, then bring the presentation text into agreement.

## Updating the review

1. Inspect new or changed packages and record the evidence. Keep bulk source data outside this repository. The optional [inspection tools](inspection.md) can compare an external folder with the manifest and inspect the known archives.
2. Update the source/manifest and the appropriate reviewed decision JSON. Preserve existing row/paper identifiers where possible. New descriptions and files need explicit decisions; a shared folder or paper is not sufficient evidence of a match.
3. Update the presentation summaries and [STAC readiness notes](stac-readiness.md) to reflect the reviewed changes. Update the explicit snapshot counts/row lists and report timestamp after completing a new evidence review.
4. Review the input diff, then run `python scripts/check_inputs.py --write` to accept the new input bytes. Rebuild, validate and test. Commit the reviewed inputs, notes and any code changes. Keep generated workbooks and reports untracked. For EOLab metadata, the reviewed `.eolab.yaml` files are also committed.

For wording-only changes, edit the presentation inputs and refresh their checksums before rebuilding; do not change scientific decisions or the original evidence timestamp merely to record an editorial revision.

Workbook edits are **not** imported by the scripts and will be overwritten on rebuild. Apply corrections to the appropriate inputs first. A changed source paste also requires updating its recorded hash and parsed representation, with a deliberate row-ID migration if records were reordered.

## Following the detailed records

`row_id` numbers parsed description records, excluding the pasted banner/header; these are not original Excel row numbers. `paper_id` identifies a paper. `asset_id` identifies an indexed file/member/layer, `parent_file_id` points to its physical file, and `link_id` identifies a particular row/asset/selector relationship. Asset IDs derive from relative paths and, for archived entries, selectors. Renaming or reorganizing files requires a migration rather than treating those IDs as permanent external identifiers.

Source-data paths are relative to the local `evidence_data` collection. They identify inspected files, not public downloads. `!` separates an archive from its member or nested archive. Selectors name a workbook sheet, variable or geodatabase layer. Article publisher links are separate from the source sheet's repository/download references.

The following files are generated under `build/reconciliation/`; they are not repository links.

| Detailed output | Purpose |
| --- | --- |
| `matches.csv` | All 78 original descriptions, paper links, files, detailed statuses, evidence and limitations. |
| `unmatched_sheet_entries.csv` | The 30 descriptions without a full or partial product match. |
| `review_gaps.csv` | All 59 descriptions other than Matched. Metadata gaps can still remain on matched rows. |
| `unmatched_local_data.csv` | The 670 additional or unresolved scientific file/member/layer entries. |
| `asset_links.csv` | Expanded row-to-asset links and exact selectors. |
| `all_local_files.csv`, `archive_assets.csv` | Complete file and archive classifications. |
| `papers.csv` | Article DOIs, publisher URLs, verification sources and supplied/verified publication years. |
| `reconciliation.json` | Combined structured results for downstream processing. |
| `summary.json`, `validation.json` | Recorded coverage and builder validation results. |
| `matching_summary.html` | Searchable summary; download and open locally. |

The workbook presents short summaries in **Study review** and **Other available data**, with the complete descriptions and evidence in **Details**. **Guide** explains navigation. Its reference tabs are **Paper references**, **File links**, **Other data files**, **File inventory**, **Archive contents**, **Source sheet** and **Match records**.

## Scope and source rights

The report rebuild does not generate a STAC catalog, establish stable public asset hosting or grant rights to the scientific data. The [readiness notes](stac-readiness.md) identify the remaining product, metadata and publication questions.

The existing [Apache-2.0 license](../LICENSE) is retained for this project's code and original annotations. It does not establish redistribution rights for referenced papers, descriptions or third-party study datasets. Preserve their attribution and applicable licenses, and confirm permissions before publishing source data as catalog assets. Bulk data, article PDFs and sampled scientific observations are not included here.

## Reviewed EOLab sources and generated files

The catalog descriptions have separate authoring sources:

| Source | Edit here when changing |
| --- | --- |
| [`evidence/matched/sidecars/`](../evidence/matched/sidecars/) and [`evidence/pilot/sidecars/`](../evidence/pilot/sidecars/) | Public metadata, references, units, asset declarations and essential limitations. These YAMLs are canonical committed files. |
| [`evidence/notes/`](../evidence/notes/) | Scientific questions, findings, interpretation and cited source passages in Markdown. |
| [`evidence/curation/`](../evidence/curation/) | Detailed source interpretation, unique reviewed field definitions and corrections. |
| [`evidence/matched/recipes/`](../evidence/matched/recipes/) and [`evidence/pilot/recipes/`](../evidence/pilot/recipes/) | Source hashes, selected rows/layers/variables, preparation operations and supporting files. Each recipe references its YAML, note and curation record. |

Preparation and metadata refresh consume these sources. They render `evidence-summary.md` beside each processed dataset and add a link to `review-context.json`. That context combines the reviewed interpretation with the frozen sheet, matching evidence and preparation checks. It is generated from the source inputs, without requiring an existing `build/reconciliation/` directory. Fresh builds contain current reviewed evidence; refreshes additionally retain previously delivered full contexts in generated `provenance_history`.

The generated dataset list and coverage tables belong in `build/evidence/delivery/`. Preparation, admission, note previews and STAC previews belong under `build/evidence/matched/` and `build/evidence/pilot/`. The combined refresh audit is `build/evidence/metadata-refresh.json`. These are local outputs, not additional authoring sources. Do not edit a rendered note or generated report to change the reviewed content.

## Prepare the EOLab evidence pilot

The three-dataset preparation is separate from rebuilding the frozen matching review and article table. It requires the actual study files and GIS libraries. See [pilot results and rebuilding instructions](evidence-pilot.md#rebuild-the-prepared-files). Its reviewed inputs are in `evidence/pilot/`; it does not alter the historical matching snapshot under `data/`.

For the expanded EOLab evidence collection, see [prepared results and rebuilding](prepared-evidence.md).
