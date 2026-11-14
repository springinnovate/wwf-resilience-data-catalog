# Evidence summary review

The revised descriptions explain what the studies found, how the supplied data support those findings, and where interpretation must stop. An independent review covered all 24 item descriptions and their supporting scientific notes. No scientific framing blockers remain in the reviewed descriptions. This is a review of the summaries and their supporting sources, not a rerun or independent validation of the studies.

The review checked each description against the relevant article sections, figures and deposited metadata. It distinguished observations, model scenarios, synthesis estimates, baseline maps and supporting inputs. Spreadsheet matching labels and internal row identifiers are absent from the public summaries; the original matching history remains supporting provenance.

## Scientific boundaries checked

| Study and items | What the summaries now explain | Essential boundary retained |
| --- | --- | --- |
| [Forest vulnerability](https://doi.org/10.1016/j.oneear.2021.06.002), four indices | Regional vulnerability patterns differ among biomass, productivity, evapotranspiration and surface temperature. | Diagnostic, signed indices are not measured changes, collapse probabilities or restoration benefits. The four variables retain different meanings. |
| [Fish access and barriers](https://doi.org/10.1111/gcb.70685), one layer | The study examines access to suitable habitat under climate change and hydropower expansion. | The delivered points are inputs, not habitat-access results or dam rankings. Future conditions combine current and additional barriers. |
| [ATTO carbon exchange](https://doi.org/10.1029/2025AV001658), one table | The local forest remained an annual carbon sink in 2023, with reduced respiration contributing to its response. | The local eddy-covariance footprint differs from the regional atmospheric footprint and basin-wide carbon balance. The full linked time series is needed for historical comparisons. |
| [Carbon loss and recovery](https://doi.org/10.1126/sciadv.adz1923), one compilation | Recovering degraded forests held more aboveground carbon after 20 years than secondary regrowth after clearance. | Higher stocks partly reflect retained carbon and do not mean faster accumulation. Percentages use reference forest stock, not the amount of lost carbon recovered. |
| [Fisheries resilience](https://doi.org/10.1098/rspb.2022.0726), one table | Catch composition and body-size changes can matter even when total landings do not decline. | Observed landings patterns and theoretical model results are distinguished. Delayed collapse with greater biodiversity is a model result; effort and independent stock data are absent. |
| [Forest loss and heat stress](https://doi.org/10.1038/s43247-021-00275-8), six grids and one table | Paired climate experiments connect complete Amazon savannization with increased environmental heat stress and population exposure. | Complete forest replacement is an extreme imposed scenario. Each grid is one scenario, while the exposure table reports additional exposure using fixed 2019 population. Neither reports observed health outcomes. |
| [Land use, biodiversity and carbon](https://doi.org/10.1073/pnas.2202310119), one table | Ecological differences occur among forest conditions as well as between forests and agricultural land. | Observational site comparisons are not before-and-after intervention measurements. The table contains site aggregates, not the published transition-effect estimates. |
| [Amazon tree diversity](https://doi.org/10.1038/s42003-023-05514-6), three grids and one table | Density, richness and diversity vary among forest types and regions. | Old-growth inventories support a baseline over original forest extent, not a current-condition map. Species per hectare, trees per hectare and Fisher's alpha remain distinct; sparse forest types have greater uncertainty. |
| [Tree dispersal traits](https://doi.org/10.1038/s42003-026-09896-1), one table | Animal-mediated dispersal is widespread and helps explain potential tree–animal dependencies. | Trait assignments include inference and are not measured restoration responses. The selected dispersal fields cannot reproduce the full pollination and population-weighted network analysis. |
| [Chaglla hydropower](https://doi.org/10.1038/s43247-024-01738-4), one table | Upstream irrigation choices create modeled trade-offs among food, hydropower and ecosystems. | The KNN power summaries are only part of the multisector analysis. Scenario mapping, exact periods and the firm-power reliability criterion remain unresolved. |
| [Historical fish catches and wetlands](https://doi.org/10.1111/faf.12328), one layer | Migratory fisheries and wetland connections motivate management across basins and borders. | Historical maxima from different places and years are neither current stocks nor a common-year census. The layer lacks the complete wetland regression and does not estimate a policy effect. |

## Corrections made during review

- Clarified the carbon reference and expressed annual relative gains as percentage points of reference stock per year. Avoided claiming that degraded forests recover faster.
- Made complete Amazon savannization explicit in the population-exposure summary, matching the grid summaries and the experiment described in the paper.
- Kept the ATTO local carbon-sink finding distinct from the paper's regional carbon-source finding.
- Corrected the biomass-index methods locator and the ATTO section/figure page references against the articles.

The briefs identify research relevance without claiming that a policy was adopted or that an intervention produced the reported result. Model results remain conditional, observational comparisons retain their design limitations, and baseline datasets are not presented as treatment effects.

## Remaining limits

Nine native grids still await CRS confirmation before map display. Plot coordinates also lack a verified datum. Hydropower scenario interpretation, seed-mass class boundaries and the fish database's inconsistent rights wording remain documented. Better summaries do not resolve these source-data limitations.

## Review scope and maintained sources

At the conclusion of the scientific review, all 24 generated YAML sidecars matched their reviewed descriptors, and all 24 notes retained the question, findings, interpretation, evidence type, dataset role, limitations and source references. These are now maintained directly as committed [matched YAMLs](../sidecars/), [pilot YAMLs](../../pilot/sidecars/) and [scientific notes](../../notes/). Detailed supporting interpretation is kept in [curation records](../../curation/), connected to each dataset by its recipe. During preparation or refresh, the rendered note links to the adjacent complete `review-context.json`.

Public descriptions contain 91–110 words; detailed briefs retain the supporting explanation and citations. No internal `row-` or `paper-` identifiers or machine-specific absolute paths were found in the public descriptions or briefs. Essential uncertainties remain visible, including withheld map display where the CRS is unconfirmed.

This check covers the reviewed scientific descriptions and notes. It does not claim that physical datasets have been republished or that a live EOLab catalog has been rescanned.
