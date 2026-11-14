"""Read-only check of external study files against the frozen path/size/mtime manifest."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', required=True, type=Path)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).resolve().parents[1] / 'data/source/file_manifest.json')
    args = parser.parse_args()
    root = args.data_root.resolve()
    if not root.is_dir():
        parser.error('--data-root must name an existing directory.')
    previous = {f['relative_path']: f for f in json.loads(args.manifest.read_text(encoding='utf-8'))['files']}
    actual, errors = {}, []
    for base, dirs, names in os.walk(root, onerror=lambda e: errors.append(str(e)), followlinks=False):
        dirs[:] = [d for d in dirs if d not in {'_inventory', '.git', '.codex', '.agents'}]
        for name in names:
            path = Path(base) / name
            try:
                stat = path.stat()
                actual[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime)
            except OSError as exc:
                errors.append(str(exc))
    changed = [name for name in sorted(previous.keys() & actual.keys())
               if previous[name]['size_bytes'] != actual[name][0]
               or abs(datetime.fromisoformat(previous[name]['modified_utc']).timestamp() - actual[name][1]) > 0.00001]
    result = {'expected_files': len(previous), 'current_files': len(actual),
              'added': sorted(actual.keys()-previous.keys()), 'missing': sorted(previous.keys()-actual.keys()),
              'size_or_mtime_changed': changed, 'errors': errors,
              'method': 'Path/size/mtime comparison only; not a full content-hash verification.'}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result['added'] or result['missing'] or changed or errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
