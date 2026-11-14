# Optional local archive inspection

To compare an external data folder with the frozen manifest without opening the scientific data files:

Set `WWF_EVIDENCE_SOURCE` to the local source collection in your environment.

```powershell
python scripts/compare_local_inventory.py --data-root "$env:WWF_EVIDENCE_SOURCE"
```

This read-only check reports added, missing, and size/mtime-changed files and exits nonzero if it finds differences or read errors. It does not update the manifest, assign new matches, or detect same-size changes whose timestamps were preserved. The original inventory excludes `_inventory` and tooling directories; the comparator uses the same exclusions. File modification dates are not observation dates.

The offline workbook rebuild uses the committed metadata and decisions; it does not require the study datasets, Fiona or 7-Zip. To repeat the specialized archive inspection against your own local data, install Fiona with GDAL OpenFileGDB support and put `7z` or `7zz` on PATH, then run:

```powershell
python scripts/inspect_archives.py --data-root "$env:WWF_EVIDENCE_SOURCE" --output-dir build/archive-inspection
```

Use `--seven-zip` with a locally configured executable if needed; keep that machine-specific setting out of committed text. The helper specifically expects `urn_uuid_3132083d_2fc5_4ef9_895d_1666954ad536/data/gdaldegan.11.3-DATAnull` and nested ZIPs in `HotDroughts`. Its output directory must be outside the data root and repository input/source directories; existing output files are never overwritten. It writes `fish_layers.json` with layer counts, schemas, CRS and bounds, and `nested_archive_inventory.json` with member names, sizes, CRCs, recognized first CSV header lines and three small header-dictionary TXT files. It does not export feature properties or CSV data rows. Unrecognized or oversized CSV headers are omitted for review. The fish geodatabase is extracted only into a temporary directory after all member paths and link metadata have been checked; nested ZIPs are spooled to temporary files without extracting their members. Temporary storage may need space comparable to the nested ZIP size. No study code is executed, and the generated inspection reports stay untracked under `build/`. Review their findings before updating the authoritative records in `data/evidence/` or the reviewed decisions.
