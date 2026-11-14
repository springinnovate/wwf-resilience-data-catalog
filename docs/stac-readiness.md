# What remains before building the STAC catalog

This note summarizes the reconciliation completed on 13 November 2026, from the supplied description sheet and local study packages. It records outstanding work; it does not certify scientific validity or permission to publish the source data. The detailed evidence, file paths, selectors and limitations remain in `study_data_matches.xlsx`, `matches.csv`, `asset_links.csv`, `unmatched_local_data.csv` and `reconciliation.json`.

The review covers 78 descriptions for 30 papers and all 1,882 substantive local files in 23 study folders. It assigns 19 descriptions **Matched**, 29 **Partial match**, 8 **Related inputs/code only**, 21 **No local match**, and 1 **Different product**. These are product-identification decisions. **The 19 matched descriptions are not declarations of STAC readiness.** Some lack a confirmed CRS, measurement period, units, license or a publishable asset location.

`row-001` through `row-078` are parsed description-record numbers, excluding the pasted banner and header. They are not original Excel row numbers or folder-name suffixes. Use `paper_id` to distinguish papers and `asset_id`/`parent_file_id` to follow indexed assets; `link_id` identifies a particular row-to-asset relationship and its selector. Counts of files, archived members and sheet descriptions are not counts of independent datasets.

## 1. Seven study packages were not found locally

These seven papers account for all 21 **No local match** descriptions. Their article links were identified, but no corresponding local study package was found. This does not establish that the data are unavailable online. The original download references are preserved in **Source sheet** for subsequent retrieval and checking.

| Paper | Description rows | Package to locate |
| --- | --- | --- |
| `paper-001` | 001 | *A first glimpse into the Selva*: stingless bee specimens and plant-bee links. |
| `paper-004` | 004-007 | *Amazon forest loss: An all-sky biophysical top-of-atmosphere cooling feedback*: cloud and radiation changes. |
| `paper-012` | 024-026 | *Global forests risk to climate and land-use change*. |
| `paper-017` | 042-044 | *Mapping Resilient Landscapes to Climate Change in a Megadiverse Country*: Brazilian resilience, heterogeneity and connectedness products. The Colombian `DATA` folder belongs to `paper-021`, not this paper. |
| `paper-025` | 059-066 | *Spatially explicit valuation of the Brazilian Amazon Forest's Ecosystem Services*: the valuation and biodiversity maps. |
| `paper-029` | 077 | *Weather disasters and their underreported transboundary impacts on Amazonian communities*: standardized disaster reports. |
| `paper-030` | 078 | *Western Amazon Basin limits*: Ecuadorian river dolphin survey results. |

Confirm the repository record, version, files and rights when obtaining each package. A publisher article URL identifies the paper; it is not a dataset download or proof that a particular product is supplied.

## 2. Requested outputs missing from supplied packages

The following gaps need an additional source, a narrower catalog description, or an explicitly documented derivation. The reconciliation inspected study code without running the models or generating missing outputs.

| Paper and rows | Present locally | Work still needed |
| --- | --- | --- |
| Anthropogenic barriers, `paper-006`, 009-012 | Continuous suitability tables, networks, barrier points and scripts. | Row 009 lacks identified binary presence/absence thresholds. Rows 010-011 lack the generated RCIsuit table/layer; their descriptions overlap. Row 012 lacks the generated dCCI/impact ranking. Raw network CSI and barrier locations are inputs, not these indices. |
| Cacao frontiers, `paper-008`, 014-016 | Training polygons, GEE/eCognition instructions and field measurements. | Obtain the regional 2020/2025 and fine-scale classification maps. GEE asset paths contain placeholders. Clarify the 2023-2025 SWIR predictor in the 2020-labelled model. Resolve 23 versus 24 field plots and obtain a verified plot-coordinate join. |
| Hot droughts, `paper-013`, 027-030 | Scenario VPD series, weather/SPI, annual mortality, and 2015-2017 leaf-temperature/sap-velocity records. | Row 027 lacks the threshold/extreme-day outputs. Row 028 requests SPEI; the supplied SPI is a different product. Row 029 lacks growth, wood density and biomass. Row 030 lacks the described 2023 measurements and soil moisture/stem-soil water-potential records. |
| Ecosystem connectivity, `paper-014`, 031-034 | Selected wetland, river and land connectivity-unit rasters, resistance raster and polygonization code. | Final polygons for rows 031, 032 and 034 are absent. The code identifies wetland 0, river 35 and land 225 raster precursors. If conversion is chosen, record it as a new derivative; confirm the terrestrial centroid/kernel-density interpretation and stated 56 km spacing. Alternate thresholds are separate scientific outputs. |
| Tree diversity under human modification, `paper-018`, 045-046 | Metadata for 215 plots and diversity matrices/summaries. | Obtain the 55,383 individual tree measurements and the named functional traits. Diversity matrices cannot replace raw census/trait records. A candidate coordinate join covers 206/215 region-plus-plot keys in another study, but identity and CRS are unverified. |
| Amazon resilience loss, `paper-022`, 051 | Monthly VOD AR(1) and variance arrays, residuals and supporting layers. | The Kendall-tau change map and spatial-mean AR(1) series were not found as saved products. Specify NetCDF variables explicitly and resolve decimal-year timestamps and 60-month window endpoints before deriving these outputs. |
| ATTO fluxes, `paper-023`, 052-053 | Monthly delta-CO2 and carbon-flux totals. | Row 052's continuous CO2 series is absent. Monthly derivatives are not the underlying observations. The full 2014-2023 series has 119 records and omits May 2021; the requested 2023 flux subset in row 053 is present. |
| Andes-Amazon management, `paper-026`, 067-071 | Mean/firm-power results, annual crop aggregates, climate inputs and model scripts. | Row 068 lacks final sediment-retention products; SWAT sediment flow is not the described InVEST service. Row 069 lacks the downscaled KNN climatology/backcast package. Rows 070-071 share annual crop aggregates; the complete daily, spatial 1,371-HRU product is absent. The bundled 27-HRU, one-year configuration is not that published scenario run. |
| Dung beetle gradient, `paper-027`, 072-075 | TMS data, specimen counts, pooled plot metrics and thermal assays. | No distinct iButton series or raw camera-trap detections/effort were found. The mammal link is only a derived `MamMass` covariate for 25 plots. Resolve specimen/BIN and thermal-assay count differences before describing coverage. |

## 3. Product identity and coverage need reconciliation

Resolve these specific discrepancies before exposing a product under the sheet's full description. Preserve the supplied values and explain corrections or filters; do not silently change them to agree with the paper.

| Paper and rows | Decision or check needed |
| --- | --- |
| Carbon meta-analysis, `paper-002`, 002 | `RefID 96` identifies two different citations. There are 147 reference rows and 146 unique IDs; fix the citation crosswalk before joining carbon records to studies. |
| Amazon dieback, `paper-003`, 003 | All 292 supplied candidate points have future/past GPP ratios below 0.30, but only 234 are below 0.20. They do not all meet the description's greater-than-80% decrease. Resolve the intended threshold. Some `npp`-named tables contain GPP summaries, inspected `_change` IDs are offset by one, and global grids require a deliberate Amazon selection. Validate calendars, periods and inherited metadata. |
| Aircraft carbon profiles, `paper-005`, 008 | The files contain 8,294 CO2 samples, not a verified reconstruction of 590 profiles; no CO concentration asset was identified. Explain TAB-to-TEF site replacement and resolve manifest site/file mapping, ALF end date and nominal-coordinate inconsistencies. Preserve rejection flags and the 23-token schema. |
| Soil properties, `paper-015`, 037 | Available values are site aggregates, not the described raw depth increments, five-point samples or intact-core bulk densities. |
| Understorey birds, `paper-019`, 047 | The delivered capture matrix is 190 species by 211 filtered terra-firme plots, not the original 716-plot, 646-species compilation. Use signed coordinates from Table S1; Table S3's absolute latitude is an analysis variable. |
| Pollination/dispersal, `paper-020`, 048-049 | Reconcile local pollination counts and 804 genera with reported totals using the actual filtering/version history. The two `Unassisted` columns in the dispersal table belong to separate source blocks; selectors must retain their positions and source meanings. |
| Colombian protected-area connectivity, `paper-021`, 050 | Confirm all six dispersal distances and the claimed 10/20 km buffer coverage. The DECA RDS object remains uninspected; the C5KM input shapefile lacks `.shx`. Habitat-loss statistics are distinct from ECA results. |
| Dam portfolios, `paper-024`, 054-058 | Inputs cover 509 Amazon dam edges and 24 Napo edges; delivered solutions are Napo-only. Verify metrics, normalization, units and the spatial dam/network join. Keep input-field selectors distinct from solution-objective columns. |
| Andes-Amazon management, `paper-026`, 067, 070-071 | Map E0/E1/E2/E4 and climatology codes to named scenarios and periods. Separate KNN and BCSD results. Crop aggregates cover 2000-2014 and 2019-2099, not the full described period; clarify POTA plus half-weighted POSE production and units. |
| Dung beetle gradient, `paper-027`, 073, 075 | Local specimen counts sum to 6,001 with 103 BINs versus 4,937/104 in the description. Thermal data have 64 CTmax and 49 CTmin records versus 125 described upper-limit individuals, with no BIN column. These may be filtering/version differences; their cause is unconfirmed. |
| Forest degradation, `paper-028`, 076 | Ten BAU/GOV rasters are plausible final products, but band meanings, units, periods and correspondence to differently named script outputs need confirmation. Three supporting files are empty, and referenced inputs are absent. Preserve the leading space in the BAU logging filename. The verified article year is 2023; the source sheet says 2022. |

## 4. Metadata still missing on identified products

- **Geometry and CRS:** LULC biodiversity/carbon tables (035-037) use `UTM_X/UTM_Y`, not longitude/latitude; zone and datum are unresolved. Tree density/diversity/richness ASCII grids (038-040) have no supplied CRS definition; degree-like coordinates are insufficient evidence of a datum. Fisheries metrics (013) need an explicit join from six region names to geometry. Species traits (049) are nonspatial; attaching arbitrary occurrence geometry would misrepresent the table.
- **Time:** Filesystem modification dates are not observation dates. `year_est` in tree plots (041) is establishment year, not a demonstrated measurement date. WBGT files (017) all carry the same nominal 1987 timestamp, including future scenarios; the actual climatology periods need documentation. TFVI maps (019-022) need temporal provenance. Retain historical observations, modeled futures, aggregation periods and publication dates as separate concepts.
- **Units, values and quality:** WBGT variables lack embedded units. TFVI values need interpretation. The matched resistance raster (033) has generating-code provenance but its coefficients and calculations were not independently validated. The catch layer (023) has the expected schema, but historical aggregation and units were not recomputed. VPD samples (027) include RH above 100% and negative VPD; the header's kPa unit needs checking without silently replacing source values. Verify no-data values, scale/offset, variable names and categorical meanings for each selected product.
- **Table parsing and joins:** Retain delimiter/decimal conventions, explicit sheet names, column positions and identifier rules. Examples include semicolon/comma-decimal heat-stress tables (018), duplicate dispersal headers (049), the carbon reference collision (002), and region/plot joins. A workbook or NetCDF filename alone does not identify which described data it supplies.
- **Methods and provenance:** Keep model, scenario, version, time window and aggregation in the asset description. An available script does not establish reproducibility: some expect missing inputs, author-specific paths, external Earth Engine assets or an incomplete model setup. Rebuilding this repository's reconciliation tables does not rerun those scientific analyses.

## 5. Rights, hosting and duplicate handling

The repository license applies to material within its stated scope; it is **not a blanket license to redistribute the scientific source files**. Record each source package's license, attribution, version and any redistribution conditions from authoritative source metadata. Distinguish author code, third-party inputs, derived products and article/supplement rights. Record unresolved rights as unresolved rather than inferring permission from a public download or an article license.

Choose durable asset locations before publishing catalog entries. Current local/shared-drive paths are inventory locators, not public URLs. Decide whether to reference a stable upstream download or host a permitted copy, and record checksums and source version. Archive-member selectors and geodatabase-layer names identify content; they are not independently downloadable URLs. If files are extracted, converted or generated for access, retain the original archive/member locator and describe the transformation. Keep source assets unchanged.

There are 670 unmatched or unresolved scientific entries: 627 standalone files plus 43 archive members or geodatabase layers. They exclude code, ordinary inputs, figures and technical sidecars. They are not disposable clutter: many are additional legitimate products without a matching sheet description. Decide whether to add descriptions for them or keep them outside the initial catalog scope. This includes alternate connectivity thresholds, diversity matrices, ancillary fish layers, and climate/disturbance outputs.

Do not create one catalog dataset per file or per description automatically:

- `DATAnull` and `test.rar` are hash-identical copies of the fish geodatabase; its topology/error components are sidecars, while eight other scientific layers are separately unmatched.
- Main/supplementary TFVI maps, repeated municipal tables, and CSV/XLSX versions may represent copies or alternate encodings. Confirm byte identity or scientific equivalence before selecting a canonical asset.
- Shapefile components, archive containers and their members must retain their relationships without inflating dataset counts. A figure or TIFF poster is not automatically a georeferenced data product.
- Rows 010/011 and 070/071 overlap; a shared asset link does not prove two independent products. Conversely, one workbook may contain several distinct products requiring different selectors.

## 6. Practical publication sequence

1. Choose the first products to publish and resolve their exact identity and scope using **Study review**, **Details** and **File links**. Keep absent outputs and alternative products clearly labelled.
2. Obtain missing packages or outputs where needed; inspect their contents and update the reconciliation. Record any new derivation as a separate provenance step.
3. Complete each selected product's geometry/CRS, temporal coverage, units, variables, scenario/version, rights and attribution. Preserve unresolved fields instead of guessing.
4. Select canonical assets and stable hosting, then verify access and checksums. Retain the inventory crosswalk and original source locators.
5. Build and validate the catalog against those verified records, including a check that links retrieve the intended files and selectors identify the intended contents. The current reconciliation validates coverage and relationships, not scientific reproducibility or catalog conformance.
