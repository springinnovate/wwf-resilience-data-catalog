## Findings

In the modeled upper Huallaga system, maintaining current land use produced comparatively modest climate-only changes in hydropower. Irrigation expansion could substantially reduce Chaglla's firm power and create years with none. The coupled watershed and reservoir analysis found that options favoring food production, hydropower or ecosystems separately could impose losses on other sectors. More efficient irrigation and coordinated decisions reduced some trade-offs without eliminating them.

## Using these data

The table contains modeled mean and firm power in MW for 16 management configurations, each with 21 selected KNN climate/model combinations: 336 rows. Use it to examine how upstream land management and water use affect the modeled power estimates alongside climate variation. The broader 10,080-pathway analysis also evaluates crops, ecosystems, reservoir operation and target screening; those results are not all supplied here.

These comparisons are conditional model outcomes. They do not measure the effects of implemented policies or observed electricity generation.

## Limits

- Source management and climatology codes are preserved. Their complete mapping to published scenario names and precise time periods remains unresolved; the paper and code use differing period bounds.
- The firm-power field is in MW, but its reliability/exceedance criterion was not established in the inspected paper, supplementary methods or supplied algorithms.
- The analysis assumes management configurations remain constant within each climatic period. Transitional effects, wider crop choices and future changes in electricity demand are not fully represented.
- The prepared table contains summary power, not daily series, and retains only KNN results. The linked archive preserves the complete original KNN/BCSD tables and inspected scripts.

## Sources

- [Sustainable land and irrigation management to limit loss of hydropower in the Andes-Amazon headwaters](https://www.nature.com/articles/s43247-024-01738-4). Results, Sectoral impacts of climate and landuse change and Conflicting outcomes for hydropower, food, and ecosystems; Figures 3-4; PDF pages 3-5. Climate-only comparisons, effects of irrigation and modeled cross-sector trade-offs.
- [Sustainable land and irrigation management to limit loss of hydropower in the Andes-Amazon headwaters](https://www.nature.com/articles/s43247-024-01738-4). Results, multisector pathways; Figure 5; PDF pages 5-6; Discussion, study limitations; PDF page 8. The broader decision analysis, limits of optimizing one sector, and assumptions about fixed land-use configurations and demand.
- [Sustainable land and irrigation management to limit loss of hydropower in the Andes-Amazon headwaters](https://www.nature.com/articles/s43247-024-01738-4). Methods, Climate and landuse scenarios and Hydropower services modeling; PDF page 9. Selection of KNN downscaling, three GCMs, 16 management scenarios and daily reservoir modeling.
- [Original dataset repository](https://doi.org/10.5281/zenodo.8161594). Zenodo Data repository.zip: Results/energy/energy_*_PF0.csv; SRC/SWAT/Run_landuse_analysis.R and scenario plotting script. Source energy summaries and exact management filenames. The prepared table selects 336 KNN rows and mean/firm-power fields while keeping originals in a supporting archive.
