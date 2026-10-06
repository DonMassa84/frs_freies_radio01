"""ID3 staging writer: copies approved originals and stamps their source file ID.

Dry-run by default; --apply executes an approved plan only. Originals are
read-only: only hash verification reads. Copies are real files, no hardlinks,
no overwrite. Existing foreign ID markers are conflicts, never overwritten.
"""
import argparse
import hashlib
import json
import unicodedata
from pathlib import Path
from uuid import UUID
from mutagen.id3 import ID3, ID3NoHeaderError, TXXX

TAG_DESC = 'FRS_ARCHIVE_SOURCE_FILE_ID'
SUPPORTED_ID3_VERSIONS = {(2, 3, 0), (2, 4, 0)}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def plan_item(source, staging_dir, source_file_id, source_sha256):
    source = Path(source).resolve(strict=True)
    staging_dir = staging_dir.resolve(strict=True)
    if not staging_dir.is_dir():
        raise ValueError('staging dir must exist')
    if source == staging_dir or staging_dir in source.parents or source.parent == staging_dir:
        raise ValueError('source inside staging or staging on source')
    UUID(source_file_id)
    if source.suffix.lower() != '.mp3':
        raise ValueError('only .mp3 supported')
    actual = sha256(source)
    item = {
        'source_path': str(source),
        'expected_sha256': source_sha256,
        'source_file_id': source_file_id,
        'target_path': str(staging_dir / (source_file_id + '.mp3')),
        'status': 'planned',
        'reason': None,
    }
    if actual != source_sha256:
        item.update(status='blocked', reason='HASH_MISMATCH')
        return item
    try:
        tags = ID3(source, translate=False)
        version = tuple(tags.version)
        item['id3_version'] = list(version)
    except ID3NoHeaderError:
        item.update(status='blocked', reason='NO_ID3_TAG', id3_version=None)
        return item
    except Exception:
        item.update(status='blocked', reason='ID3_UNREADABLE', id3_version=None)
        return item
    if version not in SUPPORTED_ID3_VERSIONS:
        item.update(status='blocked', reason='UNSUPPORTED_ID3_VERSION')
        return item
    existing = tags.getall('TXXX:' + TAG_DESC)
    if existing:
        value = str(existing[0].text[0]) if existing[0].text else ''
        if value == source_file_id:
            item['existing_tag'] = 'same'
        else:
            item.update(status='blocked', reason='FOREIGN_ID_MARKER', existing_tag=value)
            return item
    if Path(item['target_path']).exists():
        item.update(status='blocked', reason='TARGET_EXISTS')
    return item


def apply_item(item):
    if item['status'] != 'planned':
        return item
    source = Path(item['source_path'])
    target = Path(item['target_path'])
    if sha256(source) != item['expected_sha256']:
        item.update(status='failed', reason='SOURCE_CHANGED_BEFORE_COPY')
        return item
    try:
        with source.open('rb') as src, target.open('xb') as dst:
            for block in iter(lambda: src.read(1048576), b''):
                dst.write(block)
    except FileExistsError:
        item.update(status='failed', reason='TARGET_RACE')
        return item
    if sha256(target) != item['expected_sha256']:
        item.update(status='failed', reason='COPY_MISMATCH')
        return item
    try:
        tags = ID3(target, translate=False)
        normals = tags.getall('TXXX:' + TAG_DESC)
        if normals:
            existing = str(normals[0].text[0]) if normals[0].text else ''
            assert existing == item['source_file_id'], 'unexpected marker changed'
            tags.save(target)
        else:
            norm_id = unicodedata.normalize('NFC', item['source_file_id'])
            tags.add(TXXX(encoding=3, desc=TAG_DESC, text=[norm_id]))
            if list(tags.version) == item['id3_version']:
                tags.save(target)
            else:
                raise ValueError('ID3 version drift')
        reread = ID3(target, translate=False)
        stamped = reread.getall('TXXX:' + TAG_DESC)
        assert stamped and str(stamped[0].text[0]) == item['source_file_id']
    except Exception as exc:
        item.update(status='failed', reason='TAG_WRITE_FAILED:' + type(exc).__name__)
        target.unlink(missing_ok=True)
        return item
    item['staging_sha256'] = sha256(target)
    item['status'] = 'done'
    item['derived_from'] = item['source_path']
    return item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path, help='pilot export JSON with accepted records')
    parser.add_argument('staging_dir', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    data = json.loads(args.export.read_text(encoding='utf-8'))
    items = [plan_item(r['source_path'], args.staging_dir, r['file_id'], r['sha256'])
             for r in data.get('accepted', [])]
    if args.apply:
        items = [apply_item(i) for i in items]
    report = {'schema_version': '0.1-staging', 'mode': 'apply' if args.apply else 'dry-run', 'items': items}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any(i['status'] not in ('planned', 'done') for i in items) else 0


if __name__ == '__main__':
    raise SystemExit(main())
