#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the hand written translations of genuinely new upstream lines.

`maps/neo_ru.json` is an {english line: russian line} map produced from
`maps/neo_sources.json` (see docs/Нейронный доперевод.md).  A line is replaced
only when its text (without the `- @anchor:` / `- #anchor:` option prefix)
is exactly the English source line, so nothing is replaced twice and no markup
can be damaged.
"""
import json
import os
import sys


def split_prefix(line):
    """(indent + option prefix, body) of a scene line."""
    indent = line[:len(line) - len(line.lstrip())]
    s = line.strip()
    prefix = ''
    for key in ('title:', 'subtitle:', 'unavailable-subtitle:'):
        if s.startswith(key + ' '):
            prefix, s = key + ' ', s[len(key) + 1:]
            break
    if s.startswith('- '):
        prefix, s = '- ', s[2:]
        head = s.split(':', 1)
        if len(head) == 2 and head[0][:1] in ('@', '#') and ' ' not in head[0]:
            prefix, s = prefix + head[0] + ':', head[1].lstrip()
    return indent + prefix, s


def main(out_dir, map_path, report_path=None):
    pairs = json.load(open(map_path, encoding='utf-8'))
    hits, files = {}, 0
    used = set()
    for root, _, names in os.walk(out_dir):
        for name in sorted(names):
            if not name.endswith('.dry'):
                continue
            path = os.path.join(root, name)
            with open(path, encoding='utf-8') as f:
                lines = f.read().split('\n')
            touched = False
            for i, line in enumerate(lines):
                prefix, body = split_prefix(line)
                ru = pairs.get(body)
                if ru is None:
                    continue
                sep = '' if prefix.endswith(':') or not prefix else ''
                lines[i] = prefix + sep + ru
                hits[body] = hits.get(body, 0) + 1
                used.add(body)
                touched = True
            if touched:
                files += 1
                with open(path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
    unmatched = sorted(set(pairs) - used)
    print('neo translations applied: %d in %d files (%d of %d lines used)'
          % (sum(hits.values()), files, len(used), len(pairs)))
    if unmatched:
        print('not found in build: %d' % len(unmatched))
    if report_path:
        json.dump({'applied': hits, 'unmatched': unmatched},
                  open(report_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)


if __name__ == '__main__':
    out = sys.argv[1]
    mp = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'maps', 'neo_ru.json')
    rep = None
    if '--report' in sys.argv:
        rep = sys.argv[sys.argv.index('--report') + 1]
    main(out, mp, rep)
