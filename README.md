# WWF resilience data catalog

This collection brings together research findings and data relevant to forest conservation, regeneration, fisheries and water management. Start with a scientific question, read the finding and its limits, then choose the files needed for your analysis.

| Question | A place to start |
| --- | --- |
| How does disturbance history affect forest carbon recovery? | [Carbon loss and recovery](evidence/notes/wwf-forest-carbon-loss-gain-compilation.md): recovering degraded forests held more aboveground carbon after 20 years than forests regrowing after clearance. Retained carbon contributes to the difference; higher stocks do not mean faster accumulation. |
| Does forest area alone capture ecological condition? | [Biodiversity and carbon across land uses](evidence/notes/wwf-amazon-land-use-biodiversity-carbon.md): ecological differences occur among standing forest conditions as well as between forest and agriculture. These are observational site comparisons, not before-and-after intervention measurements. |
| How could forest loss affect heat exposure? | [Amazon forest cover and heat exposure](evidence/notes/wwf-brazil-heat-stress-exposure.md): modeled complete replacement of Amazon forest by savanna increases heat stress and population exposure. This is an imposed extreme scenario, not an observed health effect or a forecast of a particular policy. |
| Can total catch hide changes in a fishery? | [Fisheries harvest trends](evidence/notes/wwf-amazon-fisheries-annual-metrics.md): shifts toward smaller-bodied species can matter even without a consistent decline in total landings. The study distinguishes these observations from its theoretical biodiversity and collapse results. |

The [study index](docs/prepared-evidence.md#find-a-study) also links directly to forest vulnerability, tree diversity and traits, river and terrestrial connectivity, local carbon exchange and hydropower scenarios. The study notes explain **Findings**, **Using these data**, **Limits** and **Sources**. Relevance to a management question does not by itself establish the effect of an intervention.

## Available data

The prepared collection has **24 catalog entries: 7 maps, 8 tables/workbooks, and 9 native grids available for download while their CRS is confirmed**. It covers all 19 matched descriptions plus the existing barrier-input pilot. One description may supply several scenarios, while two descriptions can share a table.

The committed [matched YAMLs](evidence/matched/sidecars/) and [pilot YAMLs](evidence/pilot/sidecars/) supply each catalog description, file definition and reference. Maps, tables, model outputs and study inputs retain their different purposes. Open a study note for the comparison, applicability and cited paper sections before treating a supplied file as evidence for your question.

The collection has passed local preparation and EOLab admission checks. An EOLab directory scan is still needed to update the running catalog. Important remaining limits include:

- Nine WBGT and tree grids lack a confirmed CRS, so no map geometry is inferred.
- Fish-package rights contain conflicting wording.
- Carbon-study reference IDs need correction before joining some records to citations.
- Hydropower scenario periods and the firm-power definition, and seed-mass class boundaries, remain unresolved.

The [readiness notes](docs/stac-readiness.md) preserve the wider matching-review gaps, including partial matches, missing outputs and additional local data. Finding the right file does not establish scientific validity or suitability for every analysis.

## Checking which study files were found

The historical file review covers **78 dataset descriptions from 30 papers**, checked against **1,882 data and supporting files in 23 study folders**. Its labels describe whether the requested files were identified; they do not grade scientific evidence or intervention effectiveness.

| Result | Descriptions | What it means |
| --- | ---: | --- |
| Found | 19 | The requested data were identified. Metadata or other checks may still be needed. |
| Partly found | 29 | Some requested content is present, or processed results have different coverage. |
| Supporting files only | 8 | Inputs, code or documentation are present, but the requested output was not found. |
| Different data | 1 | The candidate contains SPI rather than the requested SPEI drought index. |
| Not found locally | 21 | No corresponding study package was found. These descriptions belong to seven papers. |

All **30 paper identities were checked**, with article DOIs and publisher links in the [paper registry](data/decisions/papers_verified.json). Publisher links identify papers; dataset repositories and download links are recorded separately. “Not found locally” does not mean unavailable online.

The review also identified **670 additional or unresolved scientific entries associated with 16 papers**: 627 files and 43 archived members or layers. These are not 670 independent datasets. Copies, alternative formats and related products remain visible for a later catalog pass.

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

Preparation combines these sources with the study files. Each processed dataset includes `evidence-summary.md` for scientific interpretation and `review-context.json` for the original matching records, source history and preparation checks. Generated workbooks, reports and validation results stay under ignored `build/` folders; the reviewed `.eolab.yaml` files remain committed.

The [Apache-2.0 license](LICENSE) covers this project’s code and original annotations. Referenced studies and datasets retain their own attribution and usage terms. Bulk scientific files and article PDFs are not included in Git.
