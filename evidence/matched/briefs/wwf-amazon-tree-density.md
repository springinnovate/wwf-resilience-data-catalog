# Tree density across the original Amazon forest

## Question

How does tree density vary across Amazonian forest types and regions?

## What the study found

The paper reports higher tree densities in northwestern Amazonia and lower densities in central-southern and eastern Amazonia. The spatial density model explained 43% of variation among inventory plots (Results: Tree density; Supplementary Figure 1). This describes a modeled ecological baseline, not a present-day census of the grid cells.

## How to use the evidence

Values estimate the number of trees per hectare for woody individuals with diameter at breast height of at least 10 cm. The model interpolates old-growth plot observations over the original lowland forest extent. It can provide background on natural differences in forest structure, but it does not measure present forest cover, degradation, carbon stocks, or restoration outcomes.

## How the evidence was obtained

Forest-inventory baseline with spatial interpolation

## What this dataset contributes

Interpolated tree-density baseline, trees per hectare.

## Limits and interpretation

- The model represents old-growth conditions across original forest extent, not current forest cover or an intervention outcome.
- Inventory dates vary; the April 2023 compilation does not establish a single map observation period.
- The density model explained 43% of variation among inventory plots; substantial variation remains unexplained.
- Geographic CRS is undocumented; map display is withheld pending confirmation. The original ASCII grid remains downloadable.

## Sources for these statements

- [ter Steege et al. (2023), density results](https://www.nature.com/articles/s42003-023-05514-6). PDF p.2, Results: Tree density; Supplementary Figure 1 discussed there. Regional density pattern, units and the density model's 43% explained variation.
- [ter Steege et al. (2023), sampling and map construction](https://www.nature.com/articles/s42003-023-05514-6). PDF p.2, original-forest mapping scope and sampling caveats; PDF p.8, Methods: Tree data and Modelling density, diversity, and richness patterns. Old-growth inventories; diameter-at-breast-height threshold of 10 cm; April 2023 compilation; interpolation by forest/soil group over original extent; hectare standardization for richness.
- [Amazon tree flora data, version 2](https://doi.org/10.6084/m9.figshare.22786166.v2). TreeDensity.asc; TreeDiversityScript.R and TreeDiversityFunctions.R. Exact output variable and scripts. The full review records source-grid identity and the lack of a documented geographic CRS.

These notes describe scientific findings and their potential use. They do not establish that a particular policy was adopted because of the study.

[Full provenance, matching evidence and preparation checks](../plans/spatial.json).
