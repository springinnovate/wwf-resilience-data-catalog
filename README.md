# WWF resilience data catalog

We are preparing research data for the WWF resilience platform. First, we needed to establish which datasets described in the study sheet were present in the downloaded files, identify their papers, and keep the evidence behind each match.

The review covers **78 dataset descriptions from 30 papers**, checked against **1,882 data and supporting files in 23 study folders**. **19 descriptions were found and 29 were partly found.** The 19 matched descriptions are now represented in a prepared EOLab collection, with the limitations below kept visible.

## What we found

| Result | Descriptions | What it means |
| --- | ---: | --- |
| Found | 19 | The requested data were identified. Metadata or other checks may still be needed. |
| Partly found | 29 | Some requested content is present, or processed results have different coverage. |
| Supporting files only | 8 | Inputs, code or documentation are present, but the requested output was not found. |
| Different data | 1 | The candidate contains SPI rather than the requested SPEI drought index. |
| Not found locally | 21 | No corresponding study package was found. These descriptions belong to seven papers. |

All **30 paper identities were checked**, with article DOIs and publisher links in the [paper registry](data/decisions/papers_verified.json). Publisher links identify papers; dataset repositories and download links are recorded separately. “Not found locally” does not mean unavailable online.

We also identified **670 additional or unresolved scientific entries associated with 16 papers**: 627 files and 43 archived members or layers. These are not 670 independent datasets. Copies, alternative formats and related products remain visible so they can be considered for a later catalog pass.

## Prepared evidence

The prepared collection has **24 catalog entries: 7 maps, 8 tables/workbooks, and 9 native grids available for download while their CRS is confirmed**. It covers all 19 matched descriptions plus the existing barrier-input pilot. One description may supply several scenarios, while two descriptions can share a table.

Start with the [prepared evidence results](docs/prepared-evidence.md) and the [scientific notes](evidence/notes/). The notes explain each study’s question, findings, interpretation and the role of the supplied data, with specific sources. The committed [matched YAMLs](evidence/matched/sidecars/) and [pilot YAMLs](evidence/pilot/sidecars/) are the catalog descriptions used when preparing or refreshing the processed files.

The collection has passed local preparation and EOLab admission checks. An EOLab directory scan is still needed to update the running catalog. Important remaining limits include:

- Nine WBGT and tree grids lack a confirmed CRS, so no map geometry is inferred.
- Fish-package rights contain conflicting wording.
- Carbon-study reference IDs need correction before joining some records to citations.
- Hydropower scenario periods and the firm-power definition, and seed-mass class boundaries, remain unresolved.

The [readiness notes](docs/stac-readiness.md) preserve the wider matching-review gaps, including partial matches, missing outputs and additional local data. Finding the right file does not establish scientific validity or suitability for every analysis.

## Reading the matching result

The main matching result is **`study_data_matches.xlsx`**, generated in `build/reconciliation/`. It reproduces the recorded review of the files available on 13 November 2026. Workbooks and generated reports are rebuilt locally rather than stored in Git; use the [rebuilding guide](docs/rebuilding.md) to create them from the committed inputs.

| Workbook tab | What it tells you |
| --- | --- |
| **Study review** | All 78 descriptions, short dataset names, results and what needs checking. |
| **Other available data** | Additional or unresolved data for each of the 16 papers. |
| **Details** | Original descriptions, recorded evidence and limitations. |
| **Guide** | How to interpret the review and navigate supporting records. |

For closer inspection, **Paper references** gives paper identities and verification sources; **File links** identifies the exact file, sheet, variable or archive member behind a match. **File inventory**, **Archive contents** and **Other data files** retain the complete lists. The same information is exported as CSV and JSON in `build/reconciliation/`.

## Article full text

The recorded search obtained **24 PDFs**, encountered **5 blocked downloads**, and found **no open copy for 1 paper**. The [article-search findings](docs/article-downloads.md) give links and access notes for follow-up. Rebuilding the article report creates `article_downloads.xlsx` and `article_downloads.csv` in `build/articles/`; PDFs remain untracked in `wwf-resilience-articles/`.

Copies are labeled by version. For example, the hot-drought paper was obtained as an author manuscript with an earlier title and editing notes, rather than the final publisher PDF. Finding an article does not establish that its dataset is present.

## What is kept in this repository

| Reviewed source | Purpose |
| --- | --- |
| [Data inputs](data/) | Preserved sheet, inventory, matching decisions, verified papers and article-search records. |
| [Matched YAMLs](evidence/matched/sidecars/) and [pilot YAMLs](evidence/pilot/sidecars/) | Canonical catalog metadata, references, units and essential limitations. |
| [Scientific notes](evidence/notes/) | Human-readable study findings and interpretation. |
| [Curation records](evidence/curation/) | Detailed reviewed evidence, unique field definitions, corrections and source interpretation. |
| [Matched recipes](evidence/matched/recipes/) and [pilot recipes](evidence/pilot/recipes/) | Source checksums, selections, conversions and supporting-file declarations. |

Preparation combines these sources with the study files. Each processed dataset links to `evidence-summary.md` and a complete `review-context.json`, preserving the original matching evidence and preparation checks. Generated workbooks, reports and validation results stay under ignored `build/` folders; the reviewed `.eolab.yaml` files remain committed.

The [Apache-2.0 license](LICENSE) covers this project’s code and original annotations. Referenced studies and datasets retain their own attribution and usage terms. Bulk scientific files and article PDFs are not included in Git.
