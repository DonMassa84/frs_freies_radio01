"""Sample-scoped pipeline: file list -> inventory -> pilot -> staging dry-run.

Never touches source files. All artifacts land in <workdir>/.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_file_list(list_path):
    paths = []
    for line in Path(list_path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            paths.append(line)
    return paths


def step_inventory(list_file, out_json):
    sys.path.insert(0, str(HERE))
    from inventory import inspect
    records, errors = [], []
    for item in load_file_list(list_file):
        try:
            p = Path(item).resolve(strict=True)
        except FileNotFoundError:
            errors.append({'source_path': item, 'error': 'FILE_NOT_FOUND'})
            continue
        try:
            records.append(inspect(p))
        except Exception as exc:
            errors.append({'source_path': item, 'error': type(exc).__name__})
    groups = {}
    for r in records:
        groups.setdefault(r['sha256'], []).append(r['source_path'])
    report = {'schema_version': '0.1-inventory', 'records': records,
              'byte_duplicates': [{'sha256': k, 'paths': sorted(v)}
                                  for k, v in groups.items() if len(v) > 1],
              'errors': errors}
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def run_sub(module, *argv, out):
    res = subprocess.run([sys.executable, str(HERE / module), *map(str, argv)],
                         capture_output=True, text=True)
    Path(out).write_text(res.stdout)
    if res.returncode not in (0, 1):
        raise RuntimeError(f'{module} exit {res.returncode}: {res.stderr.strip()}')
    return res.returncode


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('filelist', type=Path)
    p.add_argument('workdir', type=Path)
    args = p.parse_args()
    reports = args.workdir / 'reports'
    reports.mkdir(parents=True, exist_ok=True)
    catalog_dir = args.workdir / 'catalog'
    catalog_dir.mkdir(parents=True, exist_ok=True)
    staging = args.workdir / 'staging'
    staging.mkdir(parents=True, exist_ok=True)

    inv_json = reports / 'inventory_01.json'
    exp_json = reports / 'export_1.json'
    staging_json = reports / 'staging_dryrun.json'

    inv = step_inventory(args.filelist, inv_json)
    summary = {
        'files_requested': len(load_file_list(args.filelist)),
        'inventory_records': len(inv['records']),
        'inventory_errors': len(inv['errors']),
        'duplicate_groups': len(inv['byte_duplicates']),
        'pilot_exit': run_sub('pilot.py', inv_json, '--catalog',
                              catalog_dir / 'archive.sqlite', out=exp_json),
    }
    export = json.loads(exp_json.read_text())
    summary['accepted'] = len(export.get('accepted', []))
    summary['rejected'] = len(export.get('rejected', []))
    summary['staging_exit'] = run_sub('staging_writer.py', exp_json, staging, out=staging_json)
    plan = json.loads(staging_json.read_text())
    summary['staging_planned'] = sum(1 for i in plan['items'] if i['status'] == 'planned')
    summary['staging_blocked'] = sum(1 for i in plan['items'] if i['status'] == 'blocked')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
