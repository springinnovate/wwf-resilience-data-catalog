## Question

How does tree species richness per hectare vary across Amazonian forest types and regions?

## What the study found

The paper reports highest richness in terra-firme forests of the Pebas region and French Guiana, with lower richness in several sandy-soil, floodplain and swamp forests. The spatial model explained 71% of plot-level variation, dropping to 65% when plots were left out in turn; white-sand and swamp predictions weakened especially strongly in that check (Results: Tree species-richness; Figure 2).

## How to use the evidence

Each value estimates species per hectare, standardized from the plot data using Fisher's alpha and tree density. It is not the total number of species in the 0.1-degree cell. The model uses old-growth inventories of trees with diameter at breast height of at least 10 cm and covers the original lowland forest extent. It provides baseline ecological context; it does not quantify present habitat quality or the gain from restoration.

## How the evidence was obtained

Forest-inventory baseline with spatial interpolation

## What this dataset contributes

Interpolated tree species-richness baseline, species per hectare.

## Limits and interpretation

- The model represents old-growth conditions across original forest extent, not current forest cover or an intervention outcome.
- Inventory dates vary; the April 2023 compilation does not establish a single map observation period.
- The leave-one-out check reduced overall explained variation from 71% to 65%, with particularly large losses for sparsely sampled white-sand and swamp forests.
- Geographic CRS is undocumented; map display is withheld pending confirmation. The original ASCII grid remains downloadable.

## Sources for these statements

- [ter Steege et al. (2023), richness results](https://www.nature.com/articles/s42003-023-05514-6). PDF pp.3-4, Results: Tree species-richness; Figure 2; leave-one-out check and Supplementary Figure 6 discussed on PDF p.4. Per-hectare richness, regional pattern, fitted and leave-one-out model results, and higher uncertainty in white-sand and swamp forests.
- [ter Steege et al. (2023), sampling and map construction](https://www.nature.com/articles/s42003-023-05514-6). PDF p.2, original-forest mapping scope and sampling caveats; PDF p.8, Methods: Tree data and Modelling density, diversity, and richness patterns. Old-growth inventories; diameter-at-breast-height threshold of 10 cm; April 2023 compilation; interpolation by forest/soil group over original extent; hectare standardization for richness.
- [Amazon tree flora data, version 2](https://doi.org/10.6084/m9.figshare.22786166.v2). TreeRichness_ha.asc; TreeDiversityScript.R and TreeDiversityFunctions.R. Exact output variable and scripts. The full review records source-grid identity and the lack of a documented geographic CRS.
