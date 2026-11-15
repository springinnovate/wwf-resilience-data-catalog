## Findings

Old-growth forest inventories show higher tree densities in northwestern Amazonia and lower densities in central-southern and eastern Amazonia. The spatial model explained 43% of variation among inventory plots (Results: Tree density; Supplementary Figure 1). Substantial variation remains unexplained.

## Using these data

The 0.1-degree grid estimates trees per hectare by interpolating between old-growth inventory plots over the original lowland forest extent. The inventories count free-standing woody individuals at least 10 cm in diameter at breast height. Compare forest types and regions to examine natural differences in forest structure; tree density alone does not establish carbon stocks.

## Limits

- This is a baseline of old-growth conditions across the original forest extent, not a current forest-cover map or evidence of change after an intervention.
- Inventory dates vary. The April 2023 compilation date does not establish a single map observation period.
- The fitted model explains variation among sampled plots; this is not a guarantee of accuracy at an individual location.
- The geographic coordinate reference system (CRS) is undocumented. The original ASCII grid is downloadable, but map display awaits confirmation.

## Sources

- [ter Steege et al. (2023), density results](https://www.nature.com/articles/s42003-023-05514-6). PDF p.2, Results: Tree density; Supplementary Figure 1 discussed there. Regional density pattern, units and the density model's 43% explained variation.
- [ter Steege et al. (2023), sampling and map construction](https://www.nature.com/articles/s42003-023-05514-6). PDF p.2, original-forest mapping scope and sampling caveats; PDF p.8, Methods: Tree data and Modelling density, diversity, and richness patterns. Old-growth inventories; diameter-at-breast-height threshold of 10 cm; April 2023 compilation; interpolation by forest/soil group over original extent; hectare standardization for richness.
- [Amazon tree flora data, version 2](https://doi.org/10.6084/m9.figshare.22786166.v2). TreeDensity.asc; TreeDiversityScript.R and TreeDiversityFunctions.R. Exact output variable and scripts. The full review records source-grid identity and the lack of a documented geographic CRS.
