## Local paths in shared content

Use relative paths when mentioning files in README files, documentation, reports, PR descriptions, review replies and other shared text. Do not include full machine-specific paths, drive letters, home directories or private folder layouts. Describe downloaded files with a relative folder or filename. Keep required absolute paths confined to local execution or untracked configuration.

## Authored evidence and generated files

Keep reviewed `*.eolab.yaml` sidecars committed. Catalog metadata is authored in these YAMLs; scientific explanations belong in `evidence/notes/`, detailed reviewed interpretation in `evidence/curation/`, and preparation choices in the recipe directories.

Generated workbooks, reconciliation tables, preparation/admission reports, rendered delivery contexts and STAC previews belong in ignored `build/` directories or the processed delivery. Rebuild them from the committed inputs instead of tracking copies. Scientific payloads and article PDFs remain untracked.
