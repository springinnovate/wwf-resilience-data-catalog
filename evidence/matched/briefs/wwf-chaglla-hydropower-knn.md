# Chaglla hydropower: irrigation and climate scenarios

## Question

How do upstream land management and irrigation interact with climate change to affect Chaglla hydropower, and what trade-offs arise with food production and ecosystems?

## What the study found

In the modeled upper Huallaga system, maintaining current land use produced comparatively modest climate-only changes in hydropower, while irrigation expansion could substantially reduce firm power and create years with none. The broader analysis found that options favoring food production, hydropower or ecosystems separately could impose losses on other sectors, with more efficient irrigation and coordinated decisions reducing some trade-offs rather than eliminating them.

## How to use the evidence

The evidence motivates considering upstream water use alongside reservoir operation when comparing adaptation options. These are conditional outcomes of a coupled modeling framework, not measured effects of implemented policies. The delivered table is a power-output subset with 16 management configurations and 21 KNN climate/model combinations each. It does not supply all crop, ecosystem, reservoir-operation or target-screening results from the 10,080-pathway decision analysis.

## How the evidence was obtained

Coupled watershed–reservoir modeling and climate/management scenario analysis

## What this dataset contributes

Selected modeled mean/firm-power outputs; a subset of the broader multisector analysis.

## Limits and interpretation

- Source management and climatology codes are preserved. Their complete mapping to published scenario names and precise time periods remains unresolved; the paper and code use differing period bounds.
- The firm-power field is in MW, but its reliability/exceedance criterion was not established in the inspected paper, supplementary methods or supplied algorithms.
- The analysis assumes management configurations remain constant within each climatic period; transitional effects, wider crop choices and future changes in electricity demand are not fully represented.
- The prepared table contains modeled summary power, not measured generation or daily series, and retains only KNN results; the linked archive preserves the complete original KNN/BCSD tables and inspected scripts.

## Sources for these statements

- [Sustainable land and irrigation management to limit loss of hydropower in the Andes-Amazon headwaters](https://www.nature.com/articles/s43247-024-01738-4). Results, Sectoral impacts of climate and landuse change and Conflicting outcomes for hydropower, food, and ecosystems; Figures 3-4; PDF pages 3-5. Climate-only comparisons, effects of irrigation and modeled cross-sector trade-offs.
- [Sustainable land and irrigation management to limit loss of hydropower in the Andes-Amazon headwaters](https://www.nature.com/articles/s43247-024-01738-4). Results, multisector pathways; Figure 5; PDF pages 5-6; Discussion, study limitations; PDF page 8. The broader decision analysis, limits of optimizing one sector, and assumptions about fixed land-use configurations and demand.
- [Sustainable land and irrigation management to limit loss of hydropower in the Andes-Amazon headwaters](https://www.nature.com/articles/s43247-024-01738-4). Methods, Climate and landuse scenarios and Hydropower services modeling; PDF page 9. Selection of KNN downscaling, three GCMs, 16 management scenarios and daily reservoir modeling.
- [Original dataset repository](https://doi.org/10.5281/zenodo.8161594). Zenodo Data repository.zip: Results/energy/energy_*_PF0.csv; SRC/SWAT/Run_landuse_analysis.R and scenario plotting script. Source energy summaries and exact management filenames. The prepared table selects 336 KNN rows and mean/firm-power fields while keeping originals in a supporting archive.

These notes describe scientific findings and their potential use. They do not establish that a particular policy was adopted because of the study.

[Full provenance, matching evidence and preparation checks](../plans/tables.json).
