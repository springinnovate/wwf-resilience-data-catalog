## Findings

Tree species richness was highest in nonflooded (terra-firme) forests of the Pebas region and French Guiana, and lower in several sandy-soil, floodplain and swamp forests. The spatial model explained 71% of plot-level variation. This fell to 65% when plots were left out in turn and their values predicted, with particularly large losses for white-sand and swamp forests (Results: Tree species-richness; Figure 2).

## Using these data

Each value estimates species per hectare, standardized from plot observations using Fisher's alpha and tree density. It is not the total number of species in the 0.1-degree grid cell. The model interpolates old-growth inventories of trees at least 10 cm in diameter at breast height over the original lowland forest extent. Compare like forest types; natural richness differences alone do not establish habitat damage or restoration need.

## Limits

- This is a baseline of old-growth conditions across the original forest extent, not a current forest-cover map or evidence of change after an intervention.
- Inventory dates vary. The April 2023 compilation date does not establish a single map observation period.
- Predictions are less reliable in sparsely sampled white-sand and swamp forests. The difference between fitted and leave-one-out results matters when applying the map to new locations.
- The geographic coordinate reference system (CRS) is undocumented. The original ASCII grid is downloadable, but map display awaits confirmation.

## Sources

- [ter Steege et al. (2023), richness results](https://www.nature.com/articles/s42003-023-05514-6). PDF pp.3-4, Results: Tree species-richness; Figure 2; leave-one-out check and Supplementary Figure 6 discussed on PDF p.4. Per-hectare richness, regional pattern, fitted and leave-one-out model results, and higher uncertainty in white-sand and swamp forests.
- [ter Steege et al. (2023), sampling and map construction](https://www.nature.com/articles/s42003-023-05514-6). PDF p.2, original-forest mapping scope and sampling caveats; PDF p.8, Methods: Tree data and Modelling density, diversity, and richness patterns. Old-growth inventories; diameter-at-breast-height threshold of 10 cm; April 2023 compilation; interpolation by forest/soil group over original extent; hectare standardization for richness.
- [Amazon tree flora data, version 2](https://doi.org/10.6084/m9.figshare.22786166.v2). TreeRichness_ha.asc; TreeDiversityScript.R and TreeDiversityFunctions.R. Exact output variable and scripts. The full review records source-grid identity and the lack of a documented geographic CRS.
