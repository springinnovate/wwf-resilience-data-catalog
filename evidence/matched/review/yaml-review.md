# Independent YAML review

The 21 additional dataset descriptions are concise enough for catalog use and retain the information needed to interpret the supplied files. After the revisions below, no unresolved presentation issue prevents this delivery. This is a metadata review; source preservation and EOLab admission are checked separately by the preparation and validation scripts.

The review covered the [spatial plans](../plans/spatial.json), [table plans](../plans/tables.json) and [fish plan](../plans/fish.json), using the source sheet, matching evidence, relevant data headers, source code and paper passages. All 21 descriptors validate against the EOLab schema. A final check of all [generated sidecars](../sidecars/) confirmed exact semantic equality with those reviewed plans and verified that the requested clarifications remain visible. No live catalog scan was performed as part of this review. They account for 17 matched sheet descriptions; the existing pilot supplies the other two matched descriptions and retains its separate barrier-input example.

## What belongs in the catalog description

Each item states its product and selection, meaningful units or category definitions, temporal interpretation, paper and dataset references, and limitations that affect use. The linked review context carries original sheet rows, matching decisions, field inventories, detailed source citations and preparation checks. Supporting assets retain the original data needed to inspect or reproduce the preparation.

The reviewed YAMLs are 77-161 lines. Longer files chiefly declare supporting assets and useful column definitions. Removing those declarations merely to meet a line target would make the supporting evidence harder to access. The hydropower originals were bundled into one linked archive, reducing its sidecar to 89 lines while preserving all 18 original files and their member checksums.

## Changes made during review

- **Heat-stress grids:** clarify that the files cover South America, although the land-cover scenarios concern the Amazon. State that catalog periods follow the paper's Methods and that figure captions differ. Keep the native 1987 placeholder warning.
- **Tree grids:** keep the old-growth sampling population, diameter threshold and original-forest interpretation visible. These estimates are not a current forest-cover inventory. Repeated CRS and time warnings were shortened.
- **Heat-stress population table:** retain the paper's interpretation as additional exposure attributed to deforestation. Distinguish total affected population from the high-vulnerability subset, and retain millions of people as the unit.
- **Site biodiversity and carbon:** expose the 0-30 cm soil-carbon depth and define forest species as those recorded at least once at a primary forest site.
- **Tree plots and traits:** state the tree diameter threshold, keep establishment years separate from measurement dates, preserve accented names during UTF-8 conversion, distinguish the two dispersal classifications, and identify seed-mass values as class codes.
- **Fish catches:** distinguish historical annual maxima from a common-year observation or current stock estimate. Describe the geometry repair, retain original area attributes, and preserve the source's contradictory license wording. Current field names were checked with explicit UTF-8 decoding; historical dictionaries remain labeled as history.
- **Hydropower:** retain the KNN selection, original management/climatology codes and MW units. The firm-power reliability criterion remains explicitly unresolved after checking the paper, accessible supplement and supplied model code.

## Remaining limits visible to users

Five new datasets have mapped spatial products, and seven are usable tables or workbooks. Nine native grids remain **download only pending CRS confirmation**: six WBGT scenarios and three tree grids. Their descriptions identify them as spatial grids, while the catalog deliberately supplies no inferred geometry or datum.

Other material questions remain visible where relevant: the carbon-reference ID collision and uncached formulas; missing field dates; seed-mass class boundaries; hydropower scenario/period mappings and firm-power criterion; and the fish package's contradictory rights text. They are preserved as specific limitations rather than hidden by a generic readiness label.

The catalog metadata does not equate matching to the source sheet with scientific validation. The full supporting evidence remains linked for readers who need to inspect these questions.
