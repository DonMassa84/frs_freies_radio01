"""Read-only MP3 inventory. JSON goes to stdout, never to source files."""
import argparse
import hashlib
import json
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path
from mutagen.id3 import ID3, ID3NoHeaderError


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def normalize_title(value):
    return ' '.join(unicodedata.normalize('NFC', value).split())


def signature(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def inspect(path):
    path = Path(path).resolve(strict=True)
    before = signature(path)
    record = {'source_path': str(path), 'size_bytes': before[2],
              'sha256': sha256(path), 'title': None, 'quality_issues': [],
              'id3': None, 'technical': None}
    try:
        tags = ID3(path, translate=False)
        record['id3'] = {'version': list(tags.version),
                        'diagnostic_frames': {k: v.pprint() for k, v in tags.items()}}
        titles = tags.getall('TIT2')
        if titles and titles[0].text:
            record['title'] = normalize_title(str(titles[0].text[0])) or None
    except ID3NoHeaderError:
        record['quality_issues'].append('ID3_MISSING')
    except Exception as exc:
        record['quality_issues'].append('ID3_ERROR:' + type(exc).__name__)
    if record['title'] is None:
        record['quality_issues'].append('TITLE_MISSING')
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_format', '-show_streams',
             '-of', 'json', str(path)], capture_output=True, text=True,
            encoding='utf-8', timeout=120, check=True)
        record['technical'] = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        record['quality_issues'].append('PROBE_ERROR:' + type(exc).__name__)
    if signature(path) != before or sha256(path) != record['sha256']:
        raise RuntimeError('SOURCE_CHANGED_DURING_SCAN')
    return record


def duplicate_groups(records):
    groups = defaultdict(list)
    for item in records:
        if item.get('sha256'):
            groups[item['sha256']].append(item['source_path'])
    return [{'sha256': key, 'paths': paths} for key, paths in sorted(groups.items())
            if len(paths) > 1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    root = args.source.resolve(strict=True)
    if not root.is_dir():
        parser.error('source must be a directory')
    records, errors = [], []
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() != '.mp3':
            continue
        resolved = path.resolve(strict=True)
        if root not in resolved.parents:
            errors.append({'source_path': str(path), 'error': 'OUTSIDE_SOURCE'})
            continue
        try:
            records.append(inspect(resolved))
        except Exception as exc:
            errors.append({'source_path': str(path), 'error': str(exc)})
    report = {'schema_version': '0.1-inventory', 'records': records,
              'byte_duplicates': duplicate_groups(records), 'errors': errors}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors or any(r['quality_issues'] for r in records) else 0


if __name__ == '__main__':
    raise SystemExit(main())
