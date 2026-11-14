"""Validate a reconciliation snapshot offline, independently of the builder.

Only the committed source, manifest, decisions and reports are required. This
checks preservation and relational integrity, not scientific correctness or the
continued availability of publisher pages or externally stored datasets.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from openpyxl import load_workbook


REPO = Path(__file__).resolve().parents[1]
DECISION_NAMES = ("matching_tables", "matching_spatial", "matching_hydropower", "matching_root")
STATUS_NAMES = {
    "matched": "Matched", "partial": "Partial match",
    "not_located": "Related inputs/code only", "related_only": "Related inputs/code only",
    "unresolved": "Unresolved", "different_product": "Different product",
    "no_local_match": "No local match",
}
DISPOSITIONS = {
    "matched_data", "partial_data", "related_input", "code", "documentation",
    "figure", "sidecar", "archive_container", "unmatched_data", "unresolved_data",
}
RELATIONSHIPS = {
    "described_asset", "partial_or_processed", "related_input", "code",
    "documentation", "figure", "sidecar", "archive_container", "different_product", "unresolved",
}
PRIMARY_RELATIONSHIPS = {"described_asset", "partial_or_processed", "different_product", "unresolved"}
UNMATCHED_DISPOSITIONS = {"unmatched_data", "unresolved_data"}
SHORTENED_SUFFIX = "\n[Display shortened. Full content is preserved in the corresponding CSV/JSON and AssetLinks.]"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON {path}: {exc}") from exc


def index_unique(records, key, label):
    require(isinstance(records, list), f"{label} must be a list")
    result = {}
    for position, record in enumerate(records, 1):
        require(isinstance(record, dict), f"{label} record {position} must be an object")
        value = record.get(key)
        require(value is not None and value != "", f"{label} record {position} lacks {key}")
        require(value not in result, f"Duplicate {label} {key}: {value}")
        result[value] = record
    return result


def equal(actual, expected, label):
    require(actual == expected, f"{label} differs: expected {str(expected)[:180]!r}, got {str(actual)[:180]!r}")


def exact_set(actual, expected, label):
    actual, expected = set(actual), set(expected)
    require(actual == expected,
            f"{label}: missing {sorted(expected-actual)[:8]!r}; unexpected {sorted(actual-expected)[:8]!r}")


def cell_value(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def row_id(number):
    require(isinstance(number, int) and not isinstance(number, bool) and number > 0,
            f"Invalid parsed row number: {number!r}")
    return f"row-{number:03d}"


def row_ids(value, label):
    require(isinstance(value, str), f"{label} row_ids must be a semicolon-separated string")
    result = [part.strip() for part in value.split(";") if part.strip()]
    require(len(result) == len(set(result)), f"Duplicate row IDs in {label}")
    require(all(re.fullmatch(r"row-\d{3,}", r) for r in result), f"Malformed row IDs in {label}")
    return result


def publisher_url(value, label):
    require(isinstance(value, str), f"{label} publisher URL must be text")
    parsed = urlsplit(value)
    require(parsed.scheme in {"http", "https"} and bool(parsed.hostname), f"Invalid {label} publisher URL: {value}")
    host, path = parsed.hostname.lower(), parsed.path.lower()
    repository_hosts = ("zenodo.org", "figshare.com", "datadryad.org", "data.mendeley.com", "pangaea.de",
                        "edirepository.org", "redu.unicamp.br", "data.4tu.nl", "github.com", "osf.io")
    require(not any(host == h or host.endswith("." + h) for h in repository_hosts)
            and "dataverse" not in host,
            f"{label} uses a repository/download URL instead of an article publisher URL: {value}")
    require(not re.search(r"/(?:download|dataset|datasets|doi/pdf|content/pdf)(?:/|$)|\.pdf$", path),
            f"{label} uses a download/PDF URL rather than an article landing page: {value}")


def compare_csv(path, expected_records):
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            actual = list(reader)
            headers = reader.fieldnames
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f"Cannot read CSV {path}: {exc}") from exc
    require(headers is not None and len(headers) == len(set(headers)), f"Missing/duplicate CSV headers in {path.name}")
    expected_headers = list(dict.fromkeys(key for record in expected_records for key in record))
    if expected_records:
        equal(headers, expected_headers, f"{path.name} columns")
    equal(len(actual), len(expected_records), f"{path.name} record count")
    for position, (got, expected) in enumerate(zip(actual, expected_records), 1):
        for key in headers:
            equal(got.get(key), str(cell_value(expected.get(key, ""))), f"{path.name} record {position} column {key}")


def parse_source(input_dir, parsed):
    path = input_dir / "source" / "source_sheet.tsv"
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Cannot read source TSV {path}: {exc}") from exc
    digest = hashlib.sha256(content).hexdigest()
    equal(digest, parsed.get("source", {}).get("source_sha256"), "Preserved source SHA256")
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter="\t", strict=True)
            banner, columns = next(reader), next(reader)
            raw_rows = []
            for record in reader:
                require(len(record) == len(columns), f"Source TSV record {len(raw_rows)+1} has {len(record)} columns, expected {len(columns)}")
                raw_rows.append(record)
    except (OSError, UnicodeError, csv.Error, StopIteration) as exc:
        raise ValueError(f"Cannot parse source TSV: {exc}") from exc
    equal(columns, parsed.get("columns"), "Original source column names/order")
    require(len(columns) == len(set(columns)), "Original source columns are not unique")
    records = parsed.get("rows")
    require(isinstance(records, list), "Parsed source rows must be a list")
    equal(len(records), len(raw_rows), "Parsed/source row count")
    by_id = index_unique(records, "row_id", "source row")
    for number, (raw, record) in enumerate(zip(raw_rows, records), 1):
        equal(record.get("row_id"), row_id(number), f"Source record {number} ID")
        equal(record.get("parsed_row_number"), number, f"Source record {number} parsed number")
        for key, value in zip(columns, raw):
            equal(record.get(key), value, f"Original source record {number} column {key}")
    if "source_banner" in parsed.get("source", {}):
        equal(banner[0], parsed["source"]["source_banner"], "Original source banner")
    return digest, columns, records, by_id


def validate_workbook(path, tables, source_columns):
    try:
        workbook = load_workbook(path, read_only=False, data_only=False)
    except (OSError, ValueError, KeyError) as exc:
        raise ValueError(f"Cannot open workbook {path}: {exc}") from exc
    shortened = []
    try:
        for worksheet in workbook:
            for values in worksheet:
                for cell in values:
                    require(cell.data_type != "f", f"Unexpected Excel formula in {worksheet.title}!{cell.coordinate}")
        for name, records in tables.items():
            require(name in workbook.sheetnames, f"Workbook lacks {name} sheet")
            worksheet = workbook[name]
            columns = (["row_id", "paper_id"] + source_columns if name == "SourceSheet"
                       else list(dict.fromkeys(k for r in records for k in r)))
            equal(worksheet.max_row, len(records) + 1, f"Workbook {name} row count")
            if columns:
                equal([c.value for c in worksheet[1]], columns, f"Workbook {name} column names/order")
            for position, record in enumerate(records, 2):
                for col, key in enumerate(columns, 1):
                    wanted = cell_value(record.get(key, ""))
                    if isinstance(wanted, str) and len(wanted) > 32000:
                        shortened.append(dict(sheet=name, row=position, column=key, original_chars=len(wanted)))
                        wanted = wanted[:31000] + SHORTENED_SUFFIX
                    cell = worksheet.cell(position, col)
                    actual = "" if cell.value is None else cell.value
                    equal(actual, wanted, f"Workbook {name}!{cell.coordinate} ({key})")
                    if key in {"publisher_link", "publisher_url"} and wanted:
                        require(cell.hyperlink is not None and cell.hyperlink.target == wanted,
                                f"Workbook publisher hyperlink differs in {name}!{cell.coordinate}")
    finally:
        workbook.close()
    return shortened


def validate(input_dir=REPO / "data", output_dir=REPO / "outputs"):
    """Return concise validation counts, or raise ValueError with the first fault."""
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    snapshot = read_json(input_dir / "snapshot.json")
    parsed = read_json(input_dir / "source" / "parsed_sheet.json")
    digest, columns, source_rows, source_by = parse_source(input_dir, parsed)
    manifest = read_json(input_dir / "source" / "file_manifest.json")["files"]
    manifest_by = index_unique(manifest, "relative_path", "manifest file")
    substantive = {p: f for p, f in manifest_by.items() if f.get("role_guess") != "os_artifact"}
    folders = {f["study_folder"] for f in substantive.values()}
    papers = read_json(input_dir / "decisions" / "papers_verified.json")
    paper_by = index_unique(papers, "paper_id", "paper")
    exact_set(paper_by, {r.get("paper_id") for r in source_rows}, "Source paper coverage")
    for paper in papers:
        publisher_url(paper.get("publisher_url"), paper["paper_id"])
        require(paper.get("verified_title") and paper.get("article_doi") and paper.get("evidence_urls"),
                f"{paper['paper_id']} lacks article identity or publisher-verification evidence")
        require(paper.get("verification_status") == "verified_primary_source",
                f"{paper['paper_id']} is not marked verified against a primary source")
    folder_paper = {}
    for source in source_rows:
        folder = source.get("candidate_folder")
        if folder:
            require(folder not in folder_paper or folder_paper[folder] == source["paper_id"],
                    f"Conflicting paper association for folder {folder}")
            folder_paper[folder] = source["paper_id"]
    exact_set(folder_paper, folders, "Study folder associations")

    decisions = [read_json(input_dir / "decisions" / (name + ".json")) for name in DECISION_NAMES]
    file_decisions = [f for d in decisions for f in d["files"]]
    row_decisions = [r for d in decisions for r in d["rows"]]
    decisions_by_file = index_unique(file_decisions, "relative_path", "file decision")
    decisions_by_number = index_unique(row_decisions, "row_id", "row decision")
    exact_set(decisions_by_file, substantive, "File decision coverage")
    for number, decision in decisions_by_number.items():
        require(row_id(number) in source_by, f"Row decision references unknown row {number}")
        require(decision.get("status") in STATUS_NAMES, f"Unknown row-decision status for {number}")
        for item in decision.get("assets", []):
            require(item.get("relative_path") in substantive, f"Row {number} references missing asset {item.get('relative_path')}")
            require(item.get("relationship") in RELATIONSHIPS, f"Unknown relationship in row {number}")
    for path, decision in decisions_by_file.items():
        require(decision.get("disposition") in DISPOSITIONS, f"Unknown file disposition for {path}")
        for number in decision.get("row_ids", []):
            require(row_id(number) in source_by, f"File decision {path} references unknown row {number}")

    report = read_json(output_dir / "reconciliation.json")
    summary = read_json(output_dir / "summary.json")
    equal(report.get("summary"), summary, "JSON summary copies")
    equal(report.get("papers"), papers, "Verified paper registry preservation")
    matches, files, archives, links = (report[k] for k in ("matches", "files", "archive_assets", "asset_links"))
    match_by = index_unique(matches, "row_id", "match")
    file_by_path = index_unique(files, "relative_path", "reported file")
    file_by_id = index_unique(files, "asset_id", "physical asset")
    archive_by_id = index_unique(archives, "asset_id", "archive asset")
    index_unique(links, "link_id", "asset link")
    require(not set(file_by_id) & set(archive_by_id), "Asset ID collision between physical and archived assets")
    asset_by = {**file_by_id, **archive_by_id}
    exact_set(match_by, source_by, "Match row coverage")
    exact_set(file_by_path, substantive, "Reported non-OS file coverage")
    for match in matches:
        source = source_by[match["row_id"]]
        paper = paper_by[source["paper_id"]]
        for key, expected in {"description": source["dataset_description"], "paper_id": source["paper_id"],
                              "title_as_supplied": source["title"], "year_as_supplied": source["year"],
                              "paper": paper["verified_title"], "publisher_link": paper["publisher_url"],
                              "article_doi": paper["article_doi"]}.items():
            equal(match.get(key), expected, f"{match['row_id']} {key}")
        decision = decisions_by_number.get(source["parsed_row_number"])
        expected_status = STATUS_NAMES[decision["status"]] if decision else "No local match"
        equal(match.get("match_status"), expected_status, f"{match['row_id']} status")
        equal(match.get("review_needed"), expected_status != "Matched", f"{match['row_id']} review flag")

    def validate_paper(record, label):
        pid = record.get("paper_id")
        require(pid in paper_by, f"Unknown paper ID in {label}: {pid}")
        equal(record.get("publisher_link"), paper_by[pid]["publisher_url"], f"{label} publisher link")
        for rid in row_ids(record.get("row_ids", ""), label):
            require(rid in source_by, f"Unknown row ID {rid} in {label}")
            equal(source_by[rid]["paper_id"], pid, f"{label} row/paper association")

    for path, record in file_by_path.items():
        decision, original = decisions_by_file[path], substantive[path]
        validate_paper(record, path)
        equal(record["paper_id"], folder_paper[original["study_folder"]], f"{path} folder/paper association")
        equal(record["disposition"], decision["disposition"], f"{path} disposition")
        equal(record.get("reason", ""), decision.get("reason", ""), f"{path} disposition reason")
        exact_set(row_ids(record.get("row_ids", ""), path), [row_id(n) for n in decision.get("row_ids", [])], f"{path} row associations")
        for field in ("size_bytes", "extension", "modified_utc", "study_folder"):
            equal(record.get(field), original.get(field), f"{path} manifest {field}")

    archive_inputs = [a for d in decisions for a in d.get("archived_assets", [])]
    archive_inputs += read_json(input_dir / "decisions" / "archive_assets_root.json")
    expected_archive = {}
    for item in archive_inputs:
        key = (item.get("archive_path", item.get("outer_path")), item.get("member_path", item.get("member")), item.get("selector", ""))
        require(key not in expected_archive, f"Duplicate input archive locator: {key}")
        expected_archive[key] = item
    actual_archive = {}
    for item in archives:
        key = (item.get("outer_path"), item.get("member_path"), item.get("selector", ""))
        require(key not in actual_archive, f"Duplicate output archive locator: {key}")
        actual_archive[key] = item
        require(item.get("outer_path") in file_by_path, f"Archive references unknown outer file: {key}")
        validate_paper(item, str(key))
        equal(item["paper_id"], file_by_path[item["outer_path"]]["paper_id"], f"{key} parent paper")
    exact_set(actual_archive, expected_archive, "Archive member/layer coverage")
    for key, item in actual_archive.items():
        expected = expected_archive[key]
        equal(item["disposition"], expected["disposition"], f"{key} disposition")
        equal(item.get("reason", ""), expected.get("reason", ""), f"{key} disposition reason")
        exact_set(row_ids(item.get("row_ids", ""), str(key)), [row_id(n) for n in expected.get("row_ids", [])], f"{key} rows")
    with (input_dir / "source" / "archive_members.csv").open(encoding="utf-8-sig", newline="") as handle:
        zip_members = {(r["archive_path"], r["member_path"]) for r in csv.DictReader(handle) if r["is_directory"] != "True"}
    require(zip_members <= {(k[0], k[1]) for k in actual_archive}, "One or more non-directory ZIP members lack dispositions")

    links_by_row = {rid: [] for rid in source_by}
    link_keys = set()
    for link in links:
        rid, aid, parent = link.get("row_id"), link.get("asset_id"), link.get("parent_file_id")
        require(rid in source_by, f"Link {link['link_id']} has unknown row ID: {rid}")
        require(aid in asset_by, f"Link {link['link_id']} has dangling asset_id: {aid}")
        require(parent in file_by_id, f"Link {link['link_id']} has dangling parent_file_id: {parent}")
        require(link.get("relationship") in RELATIONSHIPS, f"Link {link['link_id']} has unknown relationship")
        equal(link.get("local_path"), file_by_id[parent]["relative_path"], f"Link {link['link_id']} parent path")
        if aid in archive_by_id:
            equal(archive_by_id[aid]["outer_path"], link["local_path"], f"Link {link['link_id']} archive parent")
        else:
            equal(aid, parent, f"Link {link['link_id']} physical asset/parent identity")
        equal(link.get("paper_id"), source_by[rid]["paper_id"], f"Link {link['link_id']} row/paper association")
        equal(link.get("paper_id"), asset_by[aid]["paper_id"], f"Link {link['link_id']} asset/paper association")
        equal(link.get("publisher_link"), paper_by[link["paper_id"]]["publisher_url"], f"Link {link['link_id']} publisher")
        key = (rid, link["local_path"], link.get("selector", ""), link["relationship"])
        require(key not in link_keys, f"Duplicate semantic asset link: {key}")
        link_keys.add(key)
        links_by_row[rid].append(link)
    for number, decision in decisions_by_number.items():
        for item in decision.get("assets", []):
            key = (row_id(number), item["relative_path"], item.get("selector", ""), item["relationship"])
            require(key in link_keys, f"Missing explicitly reviewed row/asset link: {key}")
    for path, decision in decisions_by_file.items():
        for number in decision.get("row_ids", []):
            require(any(l["local_path"] == path for l in links_by_row[row_id(number)]), f"Missing file-disposition link for row {number}: {path}")
    for item in archives:
        for rid in row_ids(item.get("row_ids", ""), item["asset_id"]):
            require(any(l["asset_id"] == item["asset_id"] for l in links_by_row[rid]), f"Missing archive link for {rid}: {item['asset_id']}")
    for match in matches:
        related = links_by_row[match["row_id"]]
        equal(match.get("all_asset_link_count"), len(related), f"{match['row_id']} link count")
        equal(match.get("primary_asset_link_count"), sum(l["relationship"] in PRIMARY_RELATIONSHIPS for l in related), f"{match['row_id']} primary link count")
        for local in match.get("local_files", "").splitlines():
            require(local in file_by_path, f"{match['row_id']} lists unknown local file: {local}")

    unmatched = report["unmatched_local_data"]
    unmatched_by = index_unique(unmatched, "asset_id", "unmatched local asset")
    expected_unmatched = {aid for aid, r in asset_by.items() if r["disposition"] in UNMATCHED_DISPOSITIONS}
    exact_set(unmatched_by, expected_unmatched, "Unmatched local data/disposition coverage")
    for aid, item in unmatched_by.items():
        original = asset_by[aid]
        validate_paper(item, aid)
        equal(item["disposition"], original["disposition"], f"Unmatched {aid} disposition")
        equal(item["paper_id"], original["paper_id"], f"Unmatched {aid} paper")
        equal(item.get("description"), original.get("reason"), f"Unmatched {aid} description")
        equal(item.get("row_ids", ""), original.get("row_ids", ""), f"Unmatched {aid} row associations")
        expected_status = "Unmatched local data" if original["disposition"] == "unmatched_data" else "Unresolved local data"
        equal(item.get("match_status"), expected_status, f"Unmatched {aid} match status")
        expected_path = original["relative_path"] if aid in file_by_id else original["outer_path"] + "!" + original["member_path"]
        equal(item["local_path"], expected_path, f"Unmatched {aid} locator")
        equal(item.get("selector", ""), original.get("selector", ""), f"Unmatched {aid} selector")
    unmatched_sheet = [m for m in matches if m["match_status"] not in {"Matched", "Partial match"}]
    review = [m for m in matches if m["match_status"] != "Matched"]
    counters = {
        "source_sha256": digest, "sheet_rows": len(source_rows), "papers": len(papers),
        "publisher_links_verified": len(papers), "study_folders": len(folders),
        "standalone_files": len(substantive), "os_artifacts_excluded": len(manifest) - len(substantive),
        "status_counts": dict(Counter(m["match_status"] for m in matches)),
        "file_disposition_counts": dict(Counter(f["disposition"] for f in files)),
        "archived_assets": len(archives), "zip_members_classified": len(zip_members), "asset_links": len(links),
        "unmatched_sheet_entries": len(unmatched_sheet), "review_gap_entries": len(review),
        "unmatched_local_entries": len(unmatched), "unmatched_local_by_level": dict(Counter(u["asset_level"] for u in unmatched)),
    }
    for key, expected in counters.items():
        equal(summary.get(key), expected, f"Summary {key}")
    snapshot_counts = {
        "source_sha256": digest, "source_records": len(source_rows), "source_columns": len(columns),
        "paper_count": len(papers), "total_files": len(manifest), "substantive_files": len(substantive),
        "study_folders": len(folders), "status_counts": counters["status_counts"],
        "assessed_row_ids": sorted(decisions_by_number),
        "no_local_match_row_ids": sorted(r["parsed_row_number"] for r in source_rows if r["parsed_row_number"] not in decisions_by_number),
        "zip_members": len(zip_members), "archive_entries": len(archives), "unmatched_local_entries": len(unmatched),
    }
    for key, expected in snapshot_counts.items():
        equal(snapshot.get(key), expected, f"Snapshot {key}")
    equal(summary.get("generated_utc"), snapshot.get("report_timestamp_utc"), "Frozen report timestamp")

    tables = {
        "matches": matches, "asset_links": links, "papers": papers, "all_local_files": files,
        "archive_assets": archives, "unmatched_sheet_entries": unmatched_sheet,
        "review_gaps": review, "unmatched_local_data": unmatched,
    }
    for name, records in tables.items():
        compare_csv(output_dir / (name + ".csv"), records)
    workbook_tables = {"Matches": matches, "UnmatchedSheet": unmatched_sheet, "UnmatchedLocal": unmatched,
                       "ReviewGaps": review, "Papers": papers, "AssetLinks": links, "AllLocalFiles": files,
                       "ArchiveAssets": archives, "SourceSheet": source_rows}
    shortened = validate_workbook(output_dir / "study_data_matches.xlsx", workbook_tables, columns)
    qa = read_json(output_dir / "validation.json")
    for key in ("sheet_rows_unique", "papers_unique", "all_files_accounted", "all_zip_members_accounted",
                "workbook_reopened", "all_asset_foreign_keys_resolve", "all_parent_file_foreign_keys_resolve",
                "unique_link_ids", "descriptions_preserved", "publisher_hyperlinks_checked", "source_text_not_executed_as_formulas"):
        equal(qa.get(key), True, f"Builder validation flag {key}")
    equal(qa.get("shortened_workbook_cells"), shortened, "Documented workbook display shortening")
    return {"rows": len(matches), "papers": len(papers), "files": len(files), "archived_assets": len(archives),
            "links": len(links), "unmatched_local_entries": len(unmatched), "source_sha256": digest}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=REPO / "data")
    parser.add_argument("--output-dir", type=Path, default=REPO / "outputs")
    args = parser.parse_args(argv)
    try:
        counts = validate(args.input_dir, args.output_dir)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1
    print("Validated: " + ", ".join(f"{counts[k]} {k.replace('_', ' ')}" for k in ("rows", "papers", "files", "archived_assets", "links", "unmatched_local_entries")) + ".")
    print("Source SHA256: " + counts["source_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
