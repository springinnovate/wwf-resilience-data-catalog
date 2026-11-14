#!/usr/bin/env python3
"""Optionally inspect two known local study packages without publishing data rows.

This helper is independent of the offline reconciliation build. It reads the fish
RAR named DATAnull and nested ZIPs in HotDroughts; it never executes study code.
"""

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath


FISH_ARCHIVE = (
    "urn_uuid_3132083d_2fc5_4ef9_895d_1666954ad536/data/gdaldegan.11.3-DATAnull"
)
FISH_GDB = "SNAPP_Fish_Data.gdb"
OUTPUT_NAMES = ("fish_layers.json", "nested_archive_inventory.json")
MAX_TEXT_BYTES = 16_384
HEADER_DICTIONARIES = {
    "BIONTE_mortality-rates_headers.txt",
    "Drought-Indices-Embrapa-Ducke_met_spi_headers.txt",
    "CESM2-CMIP6_forcing_K34-Manaus_headers.txt",
}
# Known first-column labels, not a guess that any CSV's first row is a header.
CSV_FIRST_COLUMNS = {
    "year", "date", "time", "date_time", "date_time_morning",
    "date_time_leaf_temp", "date_time_sap_velocity", "date_time_1",
    "date_time_direct_solar_rad", "date_time_sap_vel",
    "date_time_sap_vel_p_anomala",
}


def within(path, directory):
    return path == directory or directory in path.parents


def validate_locations(data_root, output_dir):
    data_root = data_root.expanduser().resolve(strict=True)
    output_dir = output_dir.expanduser().resolve()
    if not data_root.is_dir():
        raise ValueError("--data-root must be a directory")
    if within(output_dir, data_root):
        raise ValueError("--output-dir must be outside --data-root")
    repository = Path(__file__).resolve().parents[1]
    for protected in ("data", "scripts", "docs", ".git"):
        if within(output_dir, (repository / protected).resolve()):
            raise ValueError("--output-dir must not be in repository input/source directories")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("--output-dir exists and is not a directory")
    for name in OUTPUT_NAMES:
        target = output_dir / name
        if target.exists() or target.is_symlink():
            raise ValueError(f"Refusing to overwrite existing output: {name}")
    return data_root, output_dir


def find_seven_zip(requested):
    if requested:
        executable = shutil.which(requested)
        if executable is None:
            candidate = Path(requested).expanduser()
            executable = str(candidate.resolve()) if candidate.is_file() else None
    else:
        executable = shutil.which("7z") or shutil.which("7zz")
    if executable is None:
        raise RuntimeError(
            "Optional dependency 7-Zip is missing. Install 7z/7zz on PATH "
            "or provide --seven-zip PATH_TO_EXECUTABLE."
        )
    return executable


def run_seven_zip(executable, *arguments):
    result = subprocess.run(
        [executable, *arguments], capture_output=True, text=True, stdin=subprocess.DEVNULL,
        encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"7-Zip {arguments[0]} failed (exit {result.returncode})")
    return result.stdout


def safe_member_parts(name):
    windows = PureWindowsPath(name)
    normalized = name.replace("\\", "/")
    parts = normalized.rstrip("/").split("/")
    if (
        not name or "\x00" in name or windows.drive or windows.root
        or PurePosixPath(normalized).is_absolute()
        or any(part in {"", ".", ".."} or ":" in part for part in parts)
    ):
        raise ValueError("Archive contains an unsafe member path; extraction refused")
    return parts


def validated_fish_members(listing):
    if "----------" not in listing:
        raise ValueError("Unrecognized 7-Zip member listing; extraction refused")
    member_text = listing.split("----------", 1)[1]
    records, record = [], {}
    for line in member_text.splitlines() + [""]:
        if not line.strip():
            if record:
                records.append(record)
                record = {}
        elif " = " in line:
            key, value = line.split(" = ", 1)
            record[key] = value
    names = []
    for record in records:
        name = record.get("Path")
        if name is None:
            raise ValueError("Incomplete 7-Zip member listing; extraction refused")
        parts = safe_member_parts(name)
        if parts[0] != FISH_GDB:
            raise ValueError("Fish archive contains a member outside the expected geodatabase")
        for key, value in record.items():
            if "link" in key.lower() and value not in {"", "-", "0"}:
                raise ValueError("Archive links are not permitted; extraction refused")
        attributes = record.get("Attributes", "") + " " + record.get("Mode", "")
        if re.search(r"(?:^|\s)l[rwxstST-]{9}(?:\s|$)", attributes):
            raise ValueError("Archive symbolic links are not permitted")
        if record.get("Alternate Stream") == "+" or record.get("Anti") == "+":
            raise ValueError("Archive streams/anti-items are not permitted")
        names.append(name)
    if not names:
        raise ValueError("No fish archive members were listed; extraction refused")
    return names


def inspect_fish(data_root, seven_zip):
    try:
        import fiona
    except ImportError as exc:
        raise RuntimeError(
            "Optional dependency Fiona is missing. Install Fiona with GDAL "
            "OpenFileGDB support in the environment used for this helper."
        ) from exc
    archive = data_root / FISH_ARCHIVE
    if not archive.is_file():
        raise FileNotFoundError(f"Required fish archive is missing: {FISH_ARCHIVE}")
    names = validated_fish_members(run_seven_zip(seven_zip, "l", "-slt", str(archive)))
    with tempfile.TemporaryDirectory(prefix="fish-archive-inspection-") as folder:
        target = Path(folder).resolve()
        # Every listed path is validated before 7-Zip receives an extraction command.
        run_seven_zip(seven_zip, "x", "-y", "-o" + str(target), str(archive))
        for extracted in target.rglob("*"):
            junction = getattr(extracted, "is_junction", lambda: False)()
            if extracted.is_symlink() or junction or not within(extracted.resolve(), target):
                raise ValueError("Extracted archive contains an unsafe filesystem link")
            if extracted.relative_to(target).parts[0] != FISH_GDB:
                raise ValueError("Extraction produced an unexpected path")
        geodatabase = target / FISH_GDB
        layers = []
        try:
            for name in fiona.listlayers(geodatabase):
                with fiona.open(geodatabase, layer=name) as source:
                    try:
                        bounds = list(source.bounds)
                    except (ValueError, RuntimeError):
                        bounds = None
                    layers.append({
                        "layer": name, "count": len(source), "crs": str(source.crs),
                        "schema": dict(source.schema), "bounds": bounds,
                    })
        except Exception as exc:
            raise RuntimeError(
                "Fiona could not inspect the fish geodatabase; check GDAL OpenFileGDB support."
            ) from exc
    return {"archive": FISH_ARCHIVE, "members": names, "layers": layers}


def member_metadata(archive, info):
    item = {"member_path": info.filename, "size_bytes": info.file_size,
            "crc32": format(info.CRC, "08x")}
    name = PurePosixPath(info.filename.replace("\\", "/"))
    if name.suffix.lower() == ".csv":
        with archive.open(info) as source:
            first_line = source.readline(MAX_TEXT_BYTES + 1)
        if len(first_line) > MAX_TEXT_BYTES:
            item["header_omitted"] = "First physical line exceeds metadata limit"
            return item
        line = first_line.decode("utf-8-sig", errors="replace").rstrip("\r\n")
        try:
            fields = next(csv.reader([line], strict=True))
        except (csv.Error, StopIteration):
            fields = []
        labels_only = all(any(character.isalpha() or character == "_" for character in field)
                          for field in fields if field.strip())
        if fields and fields[0].strip().lower() in CSV_FIRST_COLUMNS and labels_only:
            item["header_line"] = line
        else:
            item["header_omitted"] = "First line does not have a recognized study header"
    elif name.name in HEADER_DICTIONARIES and info.file_size <= MAX_TEXT_BYTES:
        with archive.open(info) as source:
            text = source.read(MAX_TEXT_BYTES + 1).decode("utf-8-sig", errors="replace")
        if text.lstrip().startswith("HEADERS"):
            item["header_dictionary"] = text
    return item


def inspect_nested_archives(data_root):
    folder = data_root / "HotDroughts"
    outers = sorted(folder.glob("*.zip"))
    if not outers:
        raise FileNotFoundError("No ZIP packages found in HotDroughts under --data-root")
    nested = []
    for outer in outers:
        relative = outer.relative_to(data_root).as_posix()
        with zipfile.ZipFile(outer) as archive:
            for member in archive.infolist():
                if member.is_dir() or not member.filename.lower().endswith(".zip"):
                    continue
                # Spool the nested ZIP itself; never extract its scientific members.
                with tempfile.TemporaryFile() as temporary:
                    with archive.open(member) as source:
                        shutil.copyfileobj(source, temporary, 1024 * 1024)
                    temporary.seek(0)
                    with zipfile.ZipFile(temporary) as inner:
                        files = [member_metadata(inner, info) for info in inner.infolist()
                                 if not info.is_dir()]
                    nested.append({"archive": relative, "nested_member": member.filename,
                                   "files": files})
    return nested


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path,
                        help="Local study folder containing the fish package and HotDroughts")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Separate output directory outside the data root; existing files are refused")
    parser.add_argument("--seven-zip", help="7-Zip executable; defaults to 7z or 7zz on PATH")
    args = parser.parse_args(argv)
    try:
        data_root, output_dir = validate_locations(args.data_root, args.output_dir)
        seven_zip = find_seven_zip(args.seven_zip)
        fish = inspect_fish(data_root, seven_zip)
        nested = inspect_nested_archives(data_root)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, value in zip(OUTPUT_NAMES, (fish, nested)):
            with (output_dir / name).open("x", encoding="utf-8", newline="\n") as target:
                json.dump(value, target, indent=2, ensure_ascii=False, default=str)
                target.write("\n")
        print(f"Wrote metadata for {len(fish['layers'])} fish layers and {len(nested)} nested ZIPs.")
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"Archive inspection failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
