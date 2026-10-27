#!/usr/bin/env python3
"""Reject new Trivy configuration findings and findings in changed source files."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile


def source_digest(root, source):
    if not source.is_relative_to(root):
        raise ValueError(f'Finding target escapes the checkout: {source}')
    if source.is_file():
        return hashlib.sha256(source.read_bytes()).hexdigest()
    # Trivy expands vendored Helm archives into virtual template paths. Hash the
    # owning archive without extracting it; any dependency change invalidates it.
    for parent in source.parents:
        if not parent.is_relative_to(root):
            break
        if parent.name != 'charts' or not parent.is_dir():
            continue
        chart_name = source.relative_to(parent).parts[0]
        candidates = []
        for path in parent.glob('*.tgz'):
            with tarfile.open(path, 'r:gz') as archive:
                first = archive.next()
                if first and first.name.split('/')[0] == chart_name:
                    candidates.append(path)
        if len(candidates) == 1:
            return hashlib.sha256(candidates[0].read_bytes()).hexdigest()
    raise ValueError(f'Finding target has no verifiable source file or vendored chart: {source}')


def findings(report, root):
    if report.get('SchemaVersion') != 2 or not isinstance(report.get('Results'), list):
        raise ValueError('Expected a complete Trivy JSON report with schema version 2')
    root = root.resolve()
    result = Counter()
    for item in report['Results']:
        problems = [m for m in item.get('Misconfigurations', [])
                    if m.get('Status') == 'FAIL' and m.get('Severity') in ('HIGH', 'CRITICAL')]
        if not problems:
            continue
        target = Path(item['Target'])
        source = (root / target).resolve()
        digest = source_digest(root, source)
        for problem in problems:
            result[(source.relative_to(root).as_posix(), problem['ID'], problem['Message'], digest)] += 1
    return result


def assess(previous, current, previous_root, current_root):
    before = findings(previous, previous_root)
    after = findings(current, current_root)
    return after - before, after & before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('current', type=Path)
    parser.add_argument('--base-root', type=Path, required=True)
    parser.add_argument('--head-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        regressions, existing = assess(json.loads(args.baseline.read_text()),
                                      json.loads(args.current.read_text()), args.base_root, args.head_root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f'Configuration scan could not be verified: {error}') from error
    print(f'Existing findings in byte-identical files: {sum(existing.values())}')
    print(f'New findings or findings in changed files: {sum(regressions.values())}')
    for (target, ident, message, _), count in sorted(regressions.items()):
        print(f'{target}: {ident}: {message} (count={count})')
    if regressions:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
