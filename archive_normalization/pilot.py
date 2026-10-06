"""Offline pilot: inventory JSON -> persistent IDs, findings, JSON export."""
import argparse
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from uuid import uuid4


def run(records, db_path):
    accepted, rejected, findings = [], [], []
    seen = set()
    with sqlite3.connect(db_path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS assets (source TEXT PRIMARY KEY, checksum TEXT NOT NULL, file_id TEXT UNIQUE NOT NULL)')
        for item in records:
            source = item.get('source_path') if isinstance(item, dict) else None
            checksum = item.get('sha256') if isinstance(item, dict) else None
            title = item.get('title') if isinstance(item, dict) else None
            code = None
            if not isinstance(source, str) or not source.strip():
                code = 'SOURCE_REQUIRED'
            elif not isinstance(checksum, str) or not re.fullmatch('[0-9a-f]{64}', checksum):
                code = 'INVALID_SHA256'
            elif title is not None and not isinstance(title, str):
                code = 'INVALID_TITLE_TYPE'
            elif source in seen:
                code = 'DUPLICATE_SOURCE_IN_BATCH'
            if code:
                rejected.append({'source_path': source, 'code': code, 'raw_record': item})
                continue
            seen.add(source)
            row = db.execute('SELECT checksum, file_id FROM assets WHERE source=?', (source,)).fetchone()
            if row and row[0] != checksum:
                rejected.append({'source_path': source, 'code': 'SOURCE_CONTENT_CHANGED', 'raw_record': item})
                continue
            file_id = row[1] if row else str(uuid4())
            if row is None:
                db.execute('INSERT INTO assets VALUES (?, ?, ?)', (source, checksum, file_id))
            normalized = ' '.join(unicodedata.normalize('NFC', title).split()) if title else None
            normalized = normalized or None
            if normalized is None:
                findings.append({'file_id': file_id, 'code': 'TITLE_MISSING', 'severity': 'warning', 'field': 'title'})
            accepted.append({'file_id': file_id, 'source_path': source, 'sha256': checksum,
                             'title': normalized, 'rights_status': 'unknown', 'raw_record': item})
    groups = {}
    for item in accepted:
        groups.setdefault(item['sha256'], []).append(item['file_id'])
    return {'schema_version': '0.1-pilot',
            'accepted': sorted(accepted, key=lambda x: x['source_path']),
            'rejected': rejected, 'findings': findings,
            'byte_duplicate_candidates': [{'sha256': key, 'file_ids': sorted(ids)}
                                          for key, ids in sorted(groups.items()) if len(ids) > 1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--catalog', type=Path, required=True)
    args = parser.parse_args()
    inventory_path = args.inventory.resolve(strict=True)
    catalog = args.catalog.resolve()
    if inventory_path == catalog or catalog.suffix != '.sqlite':
        parser.error('catalog must be a separate .sqlite file outside the source archive')
    data = json.loads(inventory_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('records'), list):
        parser.error('expected inventory object with records list')
    if data.get('errors'):
        parser.error('inventory contains scan errors; review before importing')
    report = run(data['records'], catalog)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 1 if report['rejected'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
