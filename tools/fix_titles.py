#!/usr/bin/env python3
"""fix_titles.py BASE TR TARGET [--report log.json]

HTML attributes `title="..."` (tooltips) and `alt="..."` (image descriptions)
are user visible, but they live inside markup and therefore survived the line
based assembly in English.  The translation of BASE has them translated; this
pass pairs them by order per file (only when the counts agree) and replays the
pairs on TARGET by exact string match.
"""
import sys
import os
import re
import glob
import json

ATTR = re.compile(r'\b(title|alt)="([^"]*)"')
CYR = re.compile(r'[А-Яа-яЁё]')


def collect(path):
    out = []
    for m in ATTR.finditer(open(path, encoding='utf-8').read()):
        out.append((m.group(1), m.group(2)))
    return out


def main(base_dir, tr_dir, target, report_path=None):
    pairs = {}
    files_used = 0
    for p in sorted(glob.glob(base_dir + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, base_dir)
        t = os.path.join(tr_dir, rel)
        if not os.path.exists(t):
            continue
        b, tr = collect(p), collect(t)
        if len(b) != len(tr):
            continue
        files_used += 1
        for (kb, vb), (kt, vt) in zip(b, tr):
            if kb != kt or vb == vt:
                continue
            if re.search(r'[A-Za-z]', vb) and CYR.search(vt):
                pairs.setdefault((kb, vb), {})
                pairs[(kb, vb)][vt] = pairs[(kb, vb)].get(vt, 0) + 1
    flat = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in pairs.items()}

    changed = 0
    details = []
    for p in sorted(glob.glob(target + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        text = open(p, encoding='utf-8').read()

        def sub(m):
            nonlocal changed
            ru = flat.get((m.group(1), m.group(2)))
            if not ru:
                return m.group(0)
            changed += 1
            details.append([os.path.relpath(p, target), m.group(1), m.group(2), ru])
            return '%s="%s"' % (m.group(1), ru)

        new = ATTR.sub(sub, text)
        if new != text:
            open(p, 'w', encoding='utf-8').write(new)
    print('title/alt pairs learned from %d files: %d; applied: %d'
          % (files_used, len(flat), changed))
    if report_path:
        json.dump(details, open(report_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)


if __name__ == '__main__':
    argv = sys.argv[1:]
    rp = None
    if '--report' in argv:
        i = argv.index('--report')
        rp = argv[i + 1]
        del argv[i:i + 2]
    main(argv[0], argv[1], argv[2], rp)
