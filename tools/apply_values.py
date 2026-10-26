#!/usr/bin/env python3
"""apply_values.py ROOT MAP [MAP...]

Rewrites quoted game values in code lines of ROOT (view-if:, on-arrival:, go-to:
...) from English to the Russian wording used by the translation.
Translation units: a value map per variable, with a global fallback.
Values that look like markup (colour codes, image paths, css) are left alone.
"""
import sys
import os
import re
import json
import glob

PAIR = re.compile(r'([A-Za-z_][\w.]*)\s*(=|!=|==)\s*"([^"]*)"')
STYLE = re.compile(r'^(color:|#|img/|background|font|text-align|\d)')
SKIP_KEYS = ('title:', 'subtitle:', 'unavailable-subtitle:')


def load_maps(paths):
    per_var, glob_map = {}, {}
    for path in paths:
        d = json.load(open(path, encoding='utf-8'))
        for v, m in d['per_var'].items():
            per_var.setdefault(v, {}).update(m)
        glob_map.update(d['global'])
    return per_var, glob_map


def main(root, *map_paths):
    per_var, glob_map = load_maps(map_paths)
    changed = 0
    for p in sorted(glob.glob(root + '/**/*.dry', recursive=True)):
        lines = open(p, encoding='utf-8').read().split('\n')
        touched = False
        for i, line in enumerate(lines):
            s = line.strip()
            if not s or s.startswith('=') or s.startswith('>') or s.startswith('*'):
                continue
            if any(s.startswith(k) for k in SKIP_KEYS):
                continue
            if s.startswith('- @'):
                continue

            def sub(m):
                nonlocal changed
                var, op, val = m.group(1).split('.')[-1], m.group(2), m.group(3)
                if not val or STYLE.match(val):
                    return m.group(0)
                ru = per_var.get(var, {}).get(val)
                if ru is None:
                    ru = glob_map.get(val)
                if ru is None or ru == val:
                    return m.group(0)
                changed += 1
                return '%s %s "%s"' % (m.group(1), op, ru)

            new = PAIR.sub(sub, line)
            if new != line:
                lines[i] = new
                touched = True
        if touched:
            open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    print('values replaced: %d' % changed)


if __name__ == '__main__':
    main(*sys.argv[1:])
