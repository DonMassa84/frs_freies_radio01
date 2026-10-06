"""Staging copies with a controlled ID3 archive reference.

Workflow (originals are only ever read):

    plan      config + catalog -> PLAN.json (writes nothing else)
    apply     PLAN.json + its SHA-256 -> real copies, one TXXX frame written
    validate  PLAN.json -> re-read tags, compare frames and decoded audio,
              re-check original checksums, write REPORT.json

Only TXXX:FRS_ARCHIVE_SOURCE_FILE_ID is written. Its value is the catalog
UUID of the ORIGINAL file (from pilot.py's ``assets`` table). Each copy gets
its own UUID in ``derived_copies`` with a derived_from reference.
"""
import argparse
import fcntl
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mutagen.id3 import ID3, ID3NoHeaderError, TXXX

SCHEMA_PLAN = '0.1-staging-plan'
SCHEMA_REPORT = '0.1-staging-report'
TAG_DESC = 'FRS_ARCHIVE_SOURCE_FILE_ID'
TAG_KEY = 'TXXX:' + TAG_DESC
TAG_PROFILE = 'frs-source-id-v1'
COPY_ACTIONS = {'copy_and_tag', 'copy_only'}
REPO_ROOT = Path(__file__).resolve().parents[1]


class StagingError(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def inside(child, parent):
    return child == parent or parent in child.parents


def read_v1(path):
    """Return raw trailing ID3v1 block (128 bytes) or None; reject TAG+."""
    with Path(path).open('rb') as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size < 128:
            return None, False
        handle.seek(size - 128)
        tail = handle.read(128)
        extended = False
        if size >= 355:
            handle.seek(size - 355)
            extended = handle.read(4) == b'TAG+'
    return (tail if tail[:3] == b'TAG' else None), extended


def read_id3(path):
    """Return (tags or None, error code or None)."""
    try:
        return ID3(path, translate=False), None
    except ID3NoHeaderError:
        return None, 'ID3_MISSING'
    except Exception as exc:  # damaged tags stay for manual decision
        return None, 'ID3_ERROR:' + type(exc).__name__


def frame_fingerprint(tags):
    """Stable per-frame hashes; APIC data is included via repr."""
    result = {}
    for key, frame in sorted(tags.items()):
        if key == TAG_KEY:
            continue
        result[key] = hashlib.sha256(
            (type(frame).__name__ + repr(frame)).encode('utf-8', 'surrogatepass')).hexdigest()
    return result


def audio_md5(path, timeout=600):
    """Full decode to 32-bit float PCM; returns (md5 or None, error or None)."""
    cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-v', 'error', '-xerror',
           '-i', str(path), '-map', '0:a:0', '-c:a', 'pcm_f32le', '-f', 'md5', '-']
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, 'DECODE_TIMEOUT'
    except OSError as exc:
        return None, 'DECODE_TOOL_ERROR:' + type(exc).__name__
    if res.returncode != 0:
        return None, 'DECODE_ERROR'
    if res.stderr.strip():  # strict: any decoder message needs manual review
        return None, 'DECODE_MESSAGES'
    line = res.stdout.strip()
    return (line.split('=', 1)[1] if line.startswith('MD5=') else None), None


def tool_versions():
    versions = {}
    try:
        import mutagen
        versions['mutagen'] = mutagen.version_string
    except Exception:
        versions['mutagen'] = None
    try:
        first = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True,
                               timeout=30).stdout.splitlines()
        versions['ffmpeg'] = first[0] if first else None
    except OSError:
        versions['ffmpeg'] = None
    return versions


# ---------------------------------------------------------------- catalog

def open_catalog(path):
    path = Path(path)
    if not path.exists():
        raise StagingError('CATALOG_MISSING: run pilot.py first')
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS assets (source TEXT PRIMARY KEY, '
               'checksum TEXT NOT NULL, file_id TEXT UNIQUE NOT NULL)')
    db.execute('''CREATE TABLE IF NOT EXISTS derived_copies (
        copy_id TEXT PRIMARY KEY,
        source_file_id TEXT NOT NULL REFERENCES assets(file_id),
        source_sha256 TEXT NOT NULL,
        target_path TEXT UNIQUE NOT NULL,
        copy_sha256 TEXT,
        relation TEXT NOT NULL DEFAULT 'derived_from',
        tag_profile TEXT NOT NULL,
        status TEXT NOT NULL,
        detail TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL)''')
    return db


# ---------------------------------------------------------------- config

def load_config(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    sources = data.get('sources')
    if not isinstance(sources, list) or not sources:
        raise StagingError('CONFIG: sources list required')
    if not isinstance(data.get('target'), str):
        raise StagingError('CONFIG: target path required')
    target = Path(data['target']).expanduser().resolve()
    roots, names = [], set()
    for item in sources:
        name, raw = item.get('namespace'), item.get('path')
        if not isinstance(name, str) or not name or '/' in name or name in ('.', '..'):
            raise StagingError('CONFIG: invalid namespace %r' % name)
        if name in names:
            raise StagingError('CONFIG: duplicate namespace %r' % name)
        names.add(name)
        root = Path(raw).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise StagingError('CONFIG: source is not a directory: %s' % root)
        roots.append((name, root))
    for i, (_, a) in enumerate(roots):
        if inside(target, a) or inside(a, target):
            raise StagingError('CONFIG: target and source overlap: %s' % a)
        for _, b in roots[i + 1:]:
            if inside(a, b) or inside(b, a):
                raise StagingError('CONFIG: nested sources: %s / %s' % (a, b))
    if inside(target, REPO_ROOT):
        raise StagingError('CONFIG: target must be outside the git repository')
    reserve = float(data.get('reserve_ratio', 0.1))
    if reserve < 0:
        raise StagingError('CONFIG: reserve_ratio must be >= 0')
    return roots, target, reserve


def free_bytes(target):
    probe = target
    while not probe.exists():
        probe = probe.parent
    return shutil.disk_usage(probe).free


# ---------------------------------------------------------------- plan

def classify(path, digest, file_id, target_file):
    if file_id is None:
        return 'not_cataloged', None, None
    _, extended = read_v1(path)
    if extended:
        return 'unsupported_id3', None, 'ID3V1_EXTENDED_TAG'
    tags, error = read_id3(path)
    if tags is None:
        return 'unsupported_id3', None, error
    version = '2.%d' % tags.version[1]
    if tags.version[:2] not in ((2, 3), (2, 4)):
        return 'unsupported_id3', version, 'ID3_VERSION_UNSUPPORTED'
    current = [str(t) for f in tags.getall(TAG_KEY) for t in f.text]
    if current and current != [file_id]:
        return 'conflict', version, 'FOREIGN_SOURCE_ID'
    if target_file.exists() or target_file.is_symlink():
        return 'target_exists', version, None
    return ('copy_only' if current == [file_id] else 'copy_and_tag'), version, None


def build_plan(config_path, catalog_path):
    roots, target, reserve = load_config(config_path)
    db = open_catalog(catalog_path)
    entries, errors = [], []
    for namespace, root in roots:
        for path in sorted(root.rglob('*')):
            if path.is_symlink() or not path.is_file() or path.suffix.lower() != '.mp3':
                continue
            resolved = path.resolve(strict=True)
            if not inside(resolved, root):
                errors.append({'source_path': str(path), 'error': 'OUTSIDE_SOURCE'})
                continue
            rel = resolved.relative_to(root).as_posix()
            target_file = target / namespace / rel
            try:
                digest = sha256_file(resolved)
            except OSError as exc:
                errors.append({'source_path': str(resolved), 'error': 'READ_ERROR:' + type(exc).__name__})
                continue
            row = db.execute('SELECT checksum, file_id FROM assets WHERE source=?',
                             (str(resolved),)).fetchone()
            file_id = None
            action_note = None
            if row and row[0] != digest:
                action, version, action_note = 'reject', None, 'SOURCE_CONTENT_CHANGED'
            else:
                file_id = row[1] if row else None
                action, version, action_note = classify(resolved, digest, file_id, target_file)
            entries.append({
                'namespace': namespace, 'relative_path': rel,
                'source_path': str(resolved), 'size_bytes': resolved.stat().st_size,
                'source_sha256': digest, 'source_file_id': file_id,
                'id3_version': version, 'target_path': str(target_file),
                'action': action, 'note': action_note,
                'planned_tag': {TAG_KEY: file_id} if action == 'copy_and_tag' else {}})
    db.close()
    needed = sum(e['size_bytes'] for e in entries if e['action'] in COPY_ACTIONS)
    required = int(needed * (1 + reserve)) + 1048576
    counts = {}
    for e in entries:
        counts[e['action']] = counts.get(e['action'], 0) + 1
    return {'schema_version': SCHEMA_PLAN, 'created_at': now(),
            'tag_profile': TAG_PROFILE, 'tag_key': TAG_KEY,
            'catalog': str(Path(catalog_path).resolve()), 'target': str(target),
            'sources': [{'namespace': n, 'path': str(r)} for n, r in roots],
            'entries': entries, 'scan_errors': errors,
            'summary': {'files': len(entries), 'actions': counts,
                        'copy_bytes': needed, 'reserve_ratio': reserve,
                        'required_bytes': required, 'free_bytes': free_bytes(target),
                        'sufficient_space': free_bytes(target) >= required},
            'tools': tool_versions()}


def write_new(path, text):
    """Write a new file; never overwrite."""
    with Path(path).open('x', encoding='utf-8') as handle:
        handle.write(text)


def load_plan(plan_path, expected_sha=None):
    raw = Path(plan_path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if expected_sha is not None and actual != expected_sha.lower():
        raise StagingError('PLAN_SHA256_MISMATCH')
    plan = json.loads(raw)
    if plan.get('schema_version') != SCHEMA_PLAN:
        raise StagingError('PLAN_SCHEMA_UNSUPPORTED')
    return plan, actual


# ---------------------------------------------------------------- apply

def write_tag(path, file_id, version_minor):
    """Add the TXXX frame, keep ID3v2 version and raw ID3v1 bytes."""
    v1_raw, _ = read_v1(path)
    tags = ID3(path, translate=False)
    tags.delall(TAG_KEY)
    tags.add(TXXX(encoding=0, desc=TAG_DESC, text=[file_id]))
    tags.save(path, v1=0, v2_version=version_minor)
    if v1_raw is not None:
        with Path(path).open('ab') as handle:
            handle.write(v1_raw)


def apply_plan(plan_path, plan_sha):
    plan, _ = load_plan(plan_path, plan_sha)
    target = Path(plan['target'])
    todo = [e for e in plan['entries'] if e['action'] in COPY_ACTIONS]
    required = int(sum(e['size_bytes'] for e in todo) * (1 + plan['summary']['reserve_ratio']))
    target.mkdir(parents=True, exist_ok=True)
    results = []
    lock_path = target / '.frs-staging.lock'
    with lock_path.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise StagingError('STAGING_LOCKED: another apply is running')
        db = open_catalog(plan['catalog'])
        try:
            pending = [e for e in todo if not Path(e['target_path']).exists()]
            pending_bytes = int(sum(e['size_bytes'] for e in pending)
                                * (1 + plan['summary']['reserve_ratio']))
            if pending and free_bytes(target) < min(required, pending_bytes) + 1048576:
                raise StagingError('INSUFFICIENT_SPACE')
            for entry in todo:
                results.append(apply_entry(db, plan, entry))
                db.commit()
        finally:
            db.close()
    counts = {}
    for r in results:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    return {'schema_version': '0.1-staging-apply', 'finished_at': now(),
            'results': results, 'summary': counts}


def apply_entry(db, plan, entry):
    src = Path(entry['source_path'])
    dst = Path(entry['target_path'])
    base = {'source_path': entry['source_path'], 'target_path': entry['target_path']}
    existing = db.execute('SELECT copy_id, status, copy_sha256 FROM derived_copies '
                          'WHERE target_path=?', (str(dst),)).fetchone()
    if existing:
        if dst.exists() and existing[2] and sha256_file(dst) == existing[2]:
            return dict(base, status='already_done', copy_id=existing[0])
        return dict(base, status='needs_review', copy_id=existing[0],
                    detail='RECORDED_COPY_MISSING_OR_CHANGED')
    if dst.exists() or dst.is_symlink():
        return dict(base, status='skipped', detail='TARGET_EXISTS')
    row = db.execute('SELECT checksum, file_id FROM assets WHERE source=?',
                     (str(src),)).fetchone()
    if not row or row[1] != entry['source_file_id'] or row[0] != entry['source_sha256']:
        return dict(base, status='rejected', detail='CATALOG_CHANGED_SINCE_PLAN')
    if sha256_file(src) != entry['source_sha256']:
        return dict(base, status='rejected', detail='SOURCE_CHANGED_SINCE_PLAN')
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix='.frs-tmp-', suffix='.mp3', dir=dst.parent)
    tmp = Path(tmp_name)
    try:
        with src.open('rb') as fin, os.fdopen(fd, 'wb') as fout:
            shutil.copyfileobj(fin, fout, 1048576)
            fout.flush()
            os.fsync(fout.fileno())
        if sha256_file(tmp) != entry['source_sha256']:
            return dict(base, status='failed', detail='COPY_NOT_BYTE_IDENTICAL')
        if entry['action'] == 'copy_and_tag':
            write_tag(tmp, entry['source_file_id'], int(entry['id3_version'].split('.')[1]))
        os.link(tmp, dst)  # fails if dst appeared meanwhile; never overwrites
    except FileExistsError:
        return dict(base, status='skipped', detail='TARGET_EXISTS')
    except Exception as exc:
        return dict(base, status='failed', detail='APPLY_ERROR:' + type(exc).__name__)
    finally:
        if tmp.exists():
            tmp.unlink()
    if sha256_file(src) != entry['source_sha256']:
        status, detail = 'failed', 'ORIGINAL_CHANGED_DURING_APPLY'
    else:
        status, detail = 'written', None
    copy_id = str(uuid4())
    stamp = now()
    db.execute('INSERT INTO derived_copies VALUES (?,?,?,?,?,?,?,?,?,?,?)',
               (copy_id, entry['source_file_id'], entry['source_sha256'], str(dst),
                sha256_file(dst), 'derived_from', plan['tag_profile'], status,
                detail, stamp, stamp))
    return dict(base, status=status, detail=detail, copy_id=copy_id)


# ---------------------------------------------------------------- validate

def validate_entry(entry, copy_row):
    src, dst = Path(entry['source_path']), Path(entry['target_path'])
    checks, problems = {}, []
    checks['original_unchanged'] = sha256_file(src) == entry['source_sha256']
    checks['copy_unchanged_since_apply'] = dst.exists() and sha256_file(dst) == copy_row[2]
    src_tags, _ = read_id3(src)
    dst_tags, err = read_id3(dst)
    if dst_tags is None:
        problems.append(err or 'COPY_ID3_UNREADABLE')
        checks['tag_value'] = checks['other_frames_equal'] = checks['id3_version_kept'] = False
    else:
        values = [str(t) for f in dst_tags.getall(TAG_KEY) for t in f.text]
        checks['tag_value'] = values == [entry['source_file_id']]
        checks['other_frames_equal'] = frame_fingerprint(src_tags) == frame_fingerprint(dst_tags)
        checks['id3_version_kept'] = src_tags.version[:2] == dst_tags.version[:2]
    checks['id3v1_kept'] = read_v1(src)[0] == read_v1(dst)[0]
    md5_src, err_src = audio_md5(src)
    md5_dst, err_dst = audio_md5(dst)
    checks['copy_decodes'] = md5_dst is not None
    checks['audio_equal'] = md5_src is not None and md5_src == md5_dst
    problems += [e for e in (err_src and 'ORIGINAL_' + err_src, err_dst and 'COPY_' + err_dst) if e]
    problems += ['CHECK_FAILED:' + k for k, ok in checks.items() if not ok]
    return checks, sorted(set(problems))


def validate_plan(plan_path):
    plan, plan_sha = load_plan(plan_path)
    db = open_catalog(plan['catalog'])
    items = []
    originals_ok = True
    for entry in plan['entries']:
        if entry['action'] not in COPY_ACTIONS:
            continue
        row = db.execute('SELECT copy_id, status, copy_sha256 FROM derived_copies '
                         'WHERE target_path=?', (entry['target_path'],)).fetchone()
        if row is None:
            items.append({'target_path': entry['target_path'], 'status': 'not_applied'})
            if sha256_file(entry['source_path']) != entry['source_sha256']:
                originals_ok = False
            continue
        checks, problems = validate_entry(entry, row)
        originals_ok &= checks['original_unchanged']
        status = 'validated' if not problems else 'failed'
        db.execute('UPDATE derived_copies SET status=?, detail=?, updated_at=? WHERE copy_id=?',
                   (status, ';'.join(problems) or None, now(), row[0]))
        items.append({'copy_id': row[0], 'source_file_id': entry['source_file_id'],
                      'relation': 'derived_from', 'source_sha256': entry['source_sha256'],
                      'copy_sha256': row[2], 'target_path': entry['target_path'],
                      'tag_diff': {TAG_KEY: {'before': None if entry['action'] == 'copy_and_tag'
                                             else entry['source_file_id'],
                                             'after': entry['source_file_id']}},
                      'status': status, 'checks': checks, 'problems': problems})
    db.commit()
    db.close()
    counts = {'found': len(plan['entries']),
              'copied': sum(1 for i in items if 'copy_id' in i),
              'tagged': sum(1 for e in plan['entries'] if e['action'] == 'copy_and_tag'),
              'validated': sum(1 for i in items if i['status'] == 'validated'),
              'failed': sum(1 for i in items if i['status'] == 'failed'),
              'not_applied': sum(1 for i in items if i['status'] == 'not_applied'),
              'excluded_or_rejected': sum(1 for e in plan['entries']
                                          if e['action'] not in COPY_ACTIONS)}
    return {'schema_version': SCHEMA_REPORT, 'validated_at': now(), 'plan_sha256': plan_sha,
            'items': items, 'summary': counts, 'originals_unchanged': originals_ok,
            'tools': tool_versions()}


# ---------------------------------------------------------------- cli

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--config', required=True)
    p.add_argument('--catalog', required=True)
    p.add_argument('--out', required=True)
    a = sub.add_parser('apply')
    a.add_argument('--plan', required=True)
    a.add_argument('--plan-sha256', required=True)
    a.add_argument('--out', required=True)
    v = sub.add_parser('validate')
    v.add_argument('--plan', required=True)
    v.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    try:
        if args.cmd == 'plan':
            plan = build_plan(args.config, args.catalog)
            text = json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2)
            write_new(args.out, text)
            print(json.dumps({'plan': args.out,
                              'plan_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                              'summary': plan['summary']}, indent=2))
            return 0
        if args.cmd == 'apply':
            report = apply_plan(args.plan, args.plan_sha256)
            write_new(args.out, json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
            print(json.dumps(report['summary'], indent=2))
            return 0 if set(report['summary']) <= {'written', 'already_done'} else 1
        report = validate_plan(args.plan)
        write_new(args.out, json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        print(json.dumps({'summary': report['summary'],
                          'originals_unchanged': report['originals_unchanged']}, indent=2))
        return 0 if report['originals_unchanged'] and not report['summary']['failed'] else 1
    except (StagingError, FileExistsError) as exc:
        print('ERROR: %s' % exc)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
