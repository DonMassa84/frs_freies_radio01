"""One-command sample pipeline: inventory -> pilot catalog -> staging plan/apply/validate.

Reads a fixed sample list (one absolute file path per line, '#' comments),
inventories only those files, imports them into a persistent SQLite catalog,
builds a staging plan filtered to the sample, and optionally applies and
validates it. Originals are only ever read. Report files are never overwritten:
use a fresh --run-id for every invocation.
"""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import inventory
import pilot
import staging

WORKFLOW_VERSION = '0.1-sample-pipeline'


def fail(message):
    raise SystemExit('ERROR: %s' % message)


def read_sample_list(path):
    entries = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        entries.append(Path(line).expanduser())
    if not entries:
        fail('sample list is empty: %s' % path)
    return entries


def git_head():
    result = subprocess.run(['git', '-C', str(staging.REPO_ROOT), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True)
    if result.returncode != 0:
        fail('cannot read git HEAD in %s' % staging.REPO_ROOT)
    return result.stdout.strip()


def recompute_summary(plan):
    todo = [e for e in plan['entries'] if e['action'] in staging.COPY_ACTIONS]
    needed = sum(e['size_bytes'] for e in todo)
    reserve = plan['summary']['reserve_ratio']
    required = int(needed * (1 + reserve)) + 1048576
    free = staging.free_bytes(Path(plan['target']))
    actions = {}
    for entry in plan['entries']:
        actions[entry['action']] = actions.get(entry['action'], 0) + 1
    plan['summary'].update({'files': len(plan['entries']), 'actions': actions,
                           'copy_bytes': needed, 'required_bytes': required,
                           'free_bytes': free, 'sufficient_space': free >= required,
                           'sample_filtered': True})


def dump_text(path, data):
    staging.write_new(path, json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--sample-list', required=True,
                        help='text file with one absolute MP3 path per line')
    parser.add_argument('--workdir', required=True, type=Path,
                        help='catalog and reports; outside source root and repository')
    parser.add_argument('--target', required=True, type=Path,
                        help='staging directory for the copies')
    parser.add_argument('--namespace', default='sample')
    parser.add_argument('--run-id', default=None,
                        help='unique id for this run; default: UTC timestamp')
    parser.add_argument('--expect-commit', default=None,
                        help='abort unless git HEAD equals this commit')
    parser.add_argument('--apply', action='store_true',
                        help='actually copy and tag; default is dry-run')
    parser.add_argument('--reserve-ratio', type=float, default=0.1)
    args = parser.parse_args(argv)

    if args.expect_commit:
        head = git_head()
        if head != args.expect_commit:
            fail('HEAD %s does not match expected commit %s' % (head, args.expect_commit))
    run_id = args.run_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    workdir = args.workdir.expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    target = args.target.expanduser().resolve()

    sample = []
    for item in read_sample_list(args.sample_list):
        path = item.resolve(strict=True)
        if path.suffix.lower() != '.mp3':
            fail('not an MP3: %s' % item)
        sample.append(path)
    root = Path(os.path.commonpath([str(p) for p in sample])).resolve()
    if staging.inside(target, root) or staging.inside(root, target):
        fail('target overlaps source root %s' % root)
    if staging.inside(workdir, root) or staging.inside(root, workdir):
        fail('workdir overlaps source root %s' % root)
    if staging.inside(target, staging.REPO_ROOT):
        fail('target is inside the git repository')

    # 1) read-only inventory of exactly the sample files
    records, errors = [], []
    for path in sample:
        try:
            records.append(inventory.inspect(path))
        except Exception as exc:
            errors.append({'source_path': str(path), 'error': str(exc)})
    dump_text(workdir / ('inventory_%s.json' % run_id),
              {'schema_version': '0.1-inventory', 'records': records,
               'byte_duplicates': inventory.duplicate_groups(records), 'errors': errors})
    if errors:
        fail('inventory reported errors; see inventory_%s.json' % run_id)

    # 2) persistent catalog
    catalog = workdir / 'catalog.sqlite'
    pilot_report = pilot.run(records, catalog)
    dump_text(workdir / ('pilot_%s.json' % run_id), pilot_report)
    if pilot_report['rejected']:
        fail('pilot rejected records; see pilot_%s.json' % run_id)

    # 3) staging plan, filtered to the sample files
    config = workdir / ('sources_%s.json' % run_id)
    dump_text(config, {'sources': [{'namespace': args.namespace, 'path': str(root)}],
                       'target': str(target), 'reserve_ratio': args.reserve_ratio})
    plan = staging.build_plan(config, catalog)
    keep = {str(p) for p in sample}
    missing = keep - {e['source_path'] for e in plan['entries']}
    if missing:
        fail('sample files missing from plan: %s' % sorted(missing))
    plan['entries'] = [e for e in plan['entries'] if e['source_path'] in keep]
    recompute_summary(plan)
    plan_path = workdir / ('plan_%s.json' % run_id)
    text = json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2)
    staging.write_new(plan_path, text)
    plan_sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
    print(json.dumps({'workflow_version': WORKFLOW_VERSION, 'run_id': run_id,
                      'plan': str(plan_path), 'plan_sha256': plan_sha,
                      'summary': plan['summary']}, indent=2))
    if not args.apply:
        return 0

    # 4) apply (bound to the plan hash), 5) validate
    try:
        apply_report = staging.apply_plan(plan_path, plan_sha)
        dump_text(workdir / ('apply_%s.json' % run_id), apply_report)
        report = staging.validate_plan(plan_path)
    except staging.StagingError as exc:
        fail(str(exc))
    dump_text(workdir / ('report_%s.json' % run_id), report)
    print(json.dumps({'summary': report['summary'],
                      'originals_unchanged': report['originals_unchanged']}, indent=2))
    ok = (report['originals_unchanged'] and not report['summary']['failed']
          and set(apply_report['summary']) <= {'written', 'already_done'})
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
