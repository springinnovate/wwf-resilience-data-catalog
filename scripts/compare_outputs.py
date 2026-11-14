"""Compare a rebuild with committed outputs, ignoring XLSX ZIP compression metadata."""
import argparse
from pathlib import Path
from zipfile import ZipFile


def content(path):
    if path.suffix == '.xlsx':
        with ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist()}
    return path.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rebuilt', type=Path)
    parser.add_argument('--expected', type=Path, default=Path(__file__).resolve().parents[1] / 'outputs')
    args = parser.parse_args()
    def files(root):
        return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    expected, actual = files(args.expected), files(args.rebuilt)
    if not expected or expected.keys() != actual.keys():
        parser.exit(1, f'Output file sets differ: missing={sorted(expected.keys()-actual.keys())}; extra={sorted(actual.keys()-expected.keys())}\n')
    changed = [name for name in expected if content(expected[name]) != content(actual[name])]
    if changed:
        parser.exit(1, 'Rebuilt output content differs: ' + ', '.join(changed) + '\n')
    print(f'All {len(actual)} rebuilt outputs match the committed content.')


if __name__ == '__main__':
    main()
