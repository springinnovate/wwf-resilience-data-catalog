# In-shade heat stress: RCP8.5 with retained Amazon forest

## Question

How would complete Amazon savannization affect heat stress under historical climate and the RCP4.5 and RCP8.5 climate scenarios?

## What the study found

The paired simulations in the paper show that complete savannization increases warmest-month daily maximum in-shade WBGT by 1-5 degrees Celsius under historical atmospheric conditions, with increases reaching 7.5 degrees Celsius in future experiments and stronger effects under RCP8.5. These are comparisons across model runs in the paper; this file contains only scenario 85F.

## How to use the evidence

This 85F grid supplies one component of the comparison: RCP8.5 climate (2071-2100) with retained Amazon forest. Compare it with the appropriate paired scenario to investigate the model experiment. Complete forest replacement by savanna is an extreme imposed boundary condition, not an observed land-cover trajectory or a forecast of policy implementation. WBGT represents environmental heat stress and does not record illness, deaths, or people exposed.

## How the evidence was obtained

Climate model scenario experiment

## What this dataset contributes

Single modeled climate and land-cover scenario (85F), Figure 1.

## Limits and interpretation

- Complete savannization is an extreme model experiment; the runs do not evaluate a specific conservation policy or gradual deforestation pathway.
- This is a single-scenario climatology, not a scenario difference, population-exposure table, daily time series, or observed health outcome.
- Geographic CRS is undocumented. The original NetCDF is downloadable, but map display is withheld pending confirmation.
- Coverage dates follow Methods; figure captions differ. The native 1987 timestamp is a shared placeholder, not the modeled period.

## Sources for these statements

- [Oliveira et al. (2021), savannization and heat stress](https://www.nature.com/articles/s43247-021-00275-8). PDF p.2, Results and discussion: Amazon savannization and heat stress; PDF p.3, Figure 1, panel 85F. Paired-simulation findings, complete forest replacement, in-shade WBGT meaning and units. Panel 85F identifies this scenario rather than a difference map.
- [Oliveira et al. (2021), experimental design](https://www.nature.com/articles/s43247-021-00275-8). PDF p.7, Methods: Experimental design; PDF p.6, Population analysis. Imposed forested and savanna conditions; historical 1981-2010 and future 2071-2100 periods; distinction between climate grids and subsequent exposure calculations.
- [Figure 1 source data, version 1](https://doi.org/10.6084/m9.figshare.15128664.v1). WBGTid_COR-mdmx_AS_MesMax_rcp8_comflor.nc. Original NetCDF for scenario 85F. File identity, grid attributes and missing CRS definition are documented in review-context.json.

These notes describe scientific findings and their potential use. They do not establish that a particular policy was adopted because of the study.

[Full provenance, matching evidence and preparation checks](../plans/spatial.json).
