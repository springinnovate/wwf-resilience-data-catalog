## Question

How do human activities and natural barriers shape Amazonian connectivity, and how does modeled connectivity compare inside and outside Indigenous Territories and Protected Areas?

## What the study found

Across terrestrial, wetland, and river analyses, the paper reports higher modeled connectivity inside Indigenous Territories and Protected Areas than outside. For terrestrial ecosystems it identifies substantial impacts in the southern and eastern Amazon. These findings come from the full resistance-based connectivity analysis and area comparisons, not from this resistance grid alone.

## How to use the evidence

This raster is an input to the terrestrial connectivity model. It sums ecosystem-specific resistance weights for overlapping pressures and incorporates natural barriers. Larger values represent greater assumed barriers to ecological movement and processes. Use it to inspect that model input; final connected-area polygons and inside/outside comparisons are separate results. The spatial comparison does not establish a causal effect of a protection policy.

## How the evidence was obtained

Spatial connectivity modeling and area comparison

## What this dataset contributes

Terrestrial resistance input to the connectivity analysis.

## Limits and interpretation

- Resistance weights are model assumptions; values are not probabilities or measured movement rates.
- The grid ranges from 1 to 34 and has not been shifted to the paper's conceptual zero-impact baseline.
- Components represent different dates. Some dates in the paper differ from source-code labels; the full evidence retains that discrepancy.
- This is not a map of final connectivity, protected-area effectiveness, or restoration benefits.

## Sources for these statements

- [Ritter et al. (2025), connectivity findings](https://doi.org/10.1073/pnas.2418189122). PDF p.1, Abstract; PDF p.2, Results and Impacts on Terrestrial Ecosystems. Whole-study findings and modeled inside/outside comparisons, which require analyses beyond the supplied resistance input.
- [Ritter et al. (2025), resistance and connectivity methods](https://doi.org/10.1073/pnas.2418189122). PDF p.7, Materials and Methods, resistance construction and grainscape analysis; SI Appendix Table S2 cited there. Weighted additive resistance, natural barriers, higher scores as greater barriers, and the distinction between the input raster and downstream connectivity results.
- [Amazon Basin data and code, version 1](https://doi.org/10.6084/m9.figshare.28089815.v1). _2SPAnew2024_Resistance_analysis.R, lines 38-89; _2SPAnew2024_Resistance_analysis_DATASET.zip, resLand_EPSG5641.tif. Exact terrestrial input and producing script. Native CRS, score range and source identities are recorded in the full evidence.
