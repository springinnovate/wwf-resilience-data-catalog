## Findings

In paired climate-model experiments, complete replacement of Amazon forest by savanna increased warmest-month daily maximum in-shade wet-bulb globe temperature (WBGT) by 1–5 °C under historical conditions. Increases reached 7.5 °C in future experiments and were stronger under RCP8.5. These are comparisons between runs reported in the paper; this file contains scenario 85S only.

## Using these data

Scenario 85S represents RCP8.5 climate (2071–2100) with complete replacement of Amazon forest by savanna. Its values are the warmest-month average daily maximum in-shade WBGT, in degrees Celsius, on the South American model grid. WBGT measures environmental heat stress, rather than air temperature alone.

Pair 85S with 85F in Figure 1. The difference 85S minus 85F gives the modeled effect of complete forest replacement under the same climate. Comparing a future savanna run with historical retained forest combines land-cover and climate change. The files provide scenario averages, not daily time series.

## Limits

- Complete savannization is an extreme imposed model condition, not an observed land-cover trajectory or a gradual deforestation pathway. The experiment does not evaluate a particular conservation policy.
- The grid does not contain population exposure, illness or deaths. Population calculations are supplied separately.
- The geographic coordinate reference system (CRS) is undocumented. The original NetCDF is downloadable, but map display awaits confirmation.
- Coverage dates follow Methods; figure captions differ. The native 1987 timestamp is shared by all six scenarios and is a placeholder, not the modeled period.

## Sources

- [Oliveira et al. (2021), savannization and heat stress](https://www.nature.com/articles/s43247-021-00275-8). PDF p.2, Results and discussion: Amazon savannization and heat stress; PDF p.3, Figure 1, panel 85S. Paired-simulation findings, complete forest replacement, in-shade WBGT meaning and units. Panel 85S identifies this scenario rather than a difference map.
- [Oliveira et al. (2021), experimental design](https://www.nature.com/articles/s43247-021-00275-8). PDF p.7, Methods: Experimental design; PDF p.6, Population analysis. Imposed forested and savanna conditions; historical 1981-2010 and future 2071-2100 periods; distinction between climate grids and subsequent exposure calculations.
- [Figure 1 source data, version 1](https://doi.org/10.6084/m9.figshare.15128664.v1). WBGTid_COR-mdmx_AS_MesMax_rcp8_se6flor.nc. Original NetCDF for scenario 85S. File identity, grid attributes and missing CRS definition are documented in review-context.json.
