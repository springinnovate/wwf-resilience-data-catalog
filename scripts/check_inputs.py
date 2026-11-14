"""Check the frozen input checksums, or deliberately refresh them after review."""
import argparse
import hashlib
import os
from pathlib import Path


def manifest(root):
    """Hash frozen inputs, pruning the top-level local scientific data folder."""
    root = Path(root)
    files = []

    def reject_walk_error(error):
        raise error

    for directory, directories, names in os.walk(root, onerror=reject_walk_error):
        current = Path(directory)
        if current == root:
            directories[:] = [name for name in directories if name != 'evidence_data']
        files.extend(current / name for name in names
                     if name != 'checksums.sha256' and (current / name).is_file())
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    parser.add_argument('--write', action='store_true', help='Accept the current input bytes after reviewing their changes.')
    args = parser.parse_args()
    root = args.input_dir.resolve()
    if not (root / 'snapshot.json').is_file():
        parser.error('Input directory must contain snapshot.json.')
    path = root / 'checksums.sha256'
    actual = manifest(root)
    if args.write:
        path.write_text(''.join(f'{digest}  {name}\n' for name, digest in actual.items()), encoding='utf-8', newline='\n')
        print(f'Recorded checksums for {len(actual)} input files.')
        return
    expected = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        if name in expected:
            parser.error(f'Duplicate checksum entry: {name}')
        expected[name] = digest
    mismatches = [name for name in sorted(expected.keys() | actual.keys()) if expected.get(name) != actual.get(name)]
    if mismatches:
        parser.exit(1, 'Input checksum mismatch (review before using --write):\n' + '\n'.join(mismatches) + '\n')
    print(f'All {len(actual)} input checksums match.')


if __name__ == '__main__':
    main()
