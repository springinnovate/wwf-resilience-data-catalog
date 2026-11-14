# WWF resilience data catalog

We are preparing a STAC catalog of research data for the WWF resilience platform. Before building it, we needed to establish which datasets described in our study sheet were actually present in the downloaded files, and what other useful data those files contained.

This review compares **78 dataset descriptions from 30 papers** with **1,882 data and supporting files in 23 study folders**. It uses file contents, metadata, documentation and study code to distinguish the requested data from inputs, related results and missing outputs.

**Start with the [study data review workbook](outputs/study_data_matches.xlsx).** It shows what was found, what needs checking, and the evidence behind each decision. The review describes the files available on 13 November 2026; it is not yet a STAC catalog.

## What we found

| Result | Descriptions | What it means |
| --- | ---: | --- |
| Found | 19 | The requested data were identified. Metadata or other checks may still be needed. |
| Partly found | 29 | Only some requested content was found, or the files contain filtered or processed results with different coverage. |
| Supporting files only | 8 | Inputs, code or documentation are present, but the requested output was not found. |
| Different data | 1 | The candidate file contains a different drought index: SPI instead of SPEI. |
| Not found locally | 21 | No corresponding study package was found in the indexed folders. These descriptions belong to seven papers. |

All **30 paper identities have been checked**, with article DOIs and links to their publisher pages. Those links identify the papers; they are separate from dataset download links. “Not found locally” does not mean that data are unavailable online.

We also found **670 additional or unresolved scientific entries associated with 16 papers**: **627 files and 43 archived members or layers** that were not assigned to a supplied description. These are **not 670 distinct datasets**. Copies, alternative formats, related outputs and unresolved files remain visible. Code, ordinary inputs, figures and technical support files are counted separately.

These are two different kinds of follow-up: locate requested data that are missing, and decide which additional data deserve their own descriptions in the catalog.

## Article full text

We also searched for full-text copies of the **30 papers**. **24 PDFs were downloaded**, **5 downloads were blocked**, and **no open copy was found for 1 paper**. The [article download workbook](reports/article_downloads.xlsx) and [CSV table](reports/article_downloads.csv) list each paper, its source, the copy obtained and any remaining access problem.

The PDFs are stored locally in `C:\Users\richp\Downloads\wwf-resilience-articles`, outside Git. Paper 013, on Amazon hot droughts, came from the U.S. Department of Energy repository as an author manuscript with an earlier title and editing notes; the final publisher PDF was not obtained. Version differences are recorded in the table.

For the six outstanding papers, the [article-search findings](docs/article-downloads.md) give specific links to try. Manual access has not been verified. A listed full-text link is not a successful download, and an article PDF does not establish that its underlying dataset is present.

## How to use the workbook

Download the workbook and open it in Excel or another spreadsheet application. Start with these tabs:

| Tab | What to read |
| --- | --- |
| **Study review** | All 78 descriptions, using short dataset names, a result, what was found and what needs checking. |
| **Other available data** | A summary of additional or unresolved data for each of the 16 papers. |
| **Details** | The original descriptions and full recorded evidence and limitations, without shortening. |
| **Guide** | How to interpret the review and navigate the supporting records. |

For closer inspection, **Paper references** holds article identities and verification sources; **File links** identifies the exact file, sheet, variable or archive member behind a match. **Other data files**, **File inventory** and **Archive contents** provide the complete lists. **Source sheet** preserves the supplied sheet, and **Match records** preserves the detailed matching table.

The same results are available as text tables:

- [Study review](outputs/review_summary.csv): the short review of all 78 descriptions.
- [Other available data](outputs/other_data_summary.csv): the 16-paper summary of extra or unresolved data.
- [Full matching evidence](outputs/matches.csv) and [exact file links](outputs/asset_links.csv): the detail behind the summaries.
- [Descriptions without a full or partial match](outputs/unmatched_sheet_entries.csv): 30 entries needing the requested data, rather than merely supporting files or a different product.
- [Additional or unresolved files and layers](outputs/unmatched_local_data.csv): all 670 entries behind the other-data summary.
- [Paper references](outputs/papers.csv): article DOIs, publisher links, verification sources and publication-year notes.

File paths point into the external study-data folder. They identify what was inspected; they are not public download links. The underlying study datasets are not included in this repository.

## How to interpret the findings

“Found” means that the described data were identified. It does not mean they are ready to publish or that every scientific calculation has been reproduced. The review examined headers, samples, documentation and code; it did not run the studies' models or check every value.

Some gaps affect how the data can be used. For example:

- The aircraft files contain carbon dioxide samples, but no carbon monoxide data were found, and the samples have not been reconstructed into the stated 590 profiles.
- Only 234 of 292 mapped Amazon dieback points meet the description's greater-than-80% decline threshold.
- The tree density, diversity and richness grids were found, but their coordinate system and observation period still need confirmation.

Before creating catalog entries, we need to resolve product and coverage differences, confirm coordinates, dates and units, check source rights, choose stable file locations, and avoid counting duplicate files or overlapping descriptions as separate datasets. The [STAC readiness notes](docs/stac-readiness.md) set out the specific outstanding work by paper and description.

The repository's [Apache-2.0 license](LICENSE) covers this project's code and original annotations. It does not establish redistribution rights for the referenced papers, descriptions or third-party datasets. Their own attribution and usage terms still apply.

For rebuilding the workbook or updating the evidence, see the [rebuilding and maintenance guide](docs/rebuilding.md).
