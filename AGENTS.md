## Local paths in shared content

Use relative paths when mentioning files in README files, documentation, reports, PR descriptions, review replies and other shared text. Do not include full machine-specific paths, drive letters, home directories or private folder layouts. Describe downloaded files with a relative folder or filename. Keep required absolute paths confined to local execution or untracked configuration.

## Authored evidence and generated files

Keep reviewed `*.eolab.yaml` sidecars committed. Catalog metadata is authored in these YAMLs; scientific explanations belong in `evidence/notes/`, detailed reviewed interpretation in `evidence/curation/`, and preparation choices in the recipe directories.

Generated workbooks, reconciliation tables, preparation/admission reports, rendered delivery contexts and STAC previews belong in ignored `build/` directories or the processed delivery. Rebuild them from the committed inputs instead of tracking copies. Scientific payloads and article PDFs remain untracked.

## Writing for scientific use

Write for a scientist considering a management or conservation action. Lead with the finding or comparison, name the study setting, and explain what the supplied file contains. Keep study findings separate from results a reader can calculate from that file. Distinguish observed associations, model scenarios, synthesis estimates, baselines and model inputs without implying a causal intervention effect.

Use consistent variable names and concrete file labels. Explain a necessary limitation once in the relevant section instead of repeating generic warnings. Scientific notes use Findings, Using these data, Limits and Sources; retain quantitative uncertainty, units, comparators and precise citations. A file-matching status describes availability, not scientific evidence strength.
