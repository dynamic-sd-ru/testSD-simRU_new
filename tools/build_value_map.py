#!/usr/bin/env python3
"""build_value_map.py BASE TR OUT

Derives the English->Russian dictionary of *game values* (party names, leader
names, ideologies, ...) from the pair (upstream base, its translation).

Code lines of both trees are structurally identical, so they are aligned
directive-by-directive inside every scene; quoted literals that sit in the same
position are then paired.  A per-variable map is produced, plus a global
fallback map.
"""
import sys
import os
import re
import glob
import json
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dry import parse

LIT = re.compile(r'"([^"]*)"')
VAR = re.compile(r'([A-Za-z_][\w.]*)\s*(=|!=|==)\s*$')
PAIR = re.compile(r'([A-Za-z_][\w.]*)\s*(=|!=|==)\s*"([^"]*)"')


def code_lines(path):
    out = []
    for sc in parse(open(path, encoding='utf-8').read()):
        sid = sc['id'] or ''
        for ch in sc['chunks']:
            if ch[0] == 'code':
                out.append((sid, ch[1]))
            elif ch[0] == 'option':
                out.append((sid, 'OPTION:' + ch[1]))
    return out


def var_of(line, pos):
    m = VAR.search(line[:pos])
    if m:
        return m.group(1).split('.')[-1]
    return None


def main(base_dir, tr_dir, out_path):
    per_var = collections.defaultdict(collections.Counter)
    global_map = collections.defaultdict(collections.Counter)
    pairs = 0
    for p in sorted(glob.glob(base_dir + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, base_dir)
        t = os.path.join(tr_dir, rel)
        if not os.path.exists(t):
            continue
        bl = code_lines(p)
        tl = code_lines(t)
        # align by (scene id, keyword)
        key = lambda x: (x[0], x[1].split(':')[0][:20] if ': ' in x[1] or ':' in x[1] else x[1])
        i = j = 0
        while i < len(bl) and j < len(tl):
            b_sid, b_line = bl[i]
            t_sid, t_line = tl[j]
            if b_sid != t_sid:
                # resynchronise on scene id
                if b_sid < t_sid:
                    i += 1
                else:
                    j += 1
                continue
            i += 1
            if b_line.startswith('OPTION:') or t_line.startswith('OPTION:'):
                continue
            b = LIT.findall(b_line)
            x = LIT.findall(t_line)
            if len(b) == len(x):
                j += 1
                for pos_m, en in zip(LIT.finditer(b_line), b):
                    ru = x[b.index(en)] if b.count(en) == 1 else None
                    if ru is None:
                        continue
                    if en == ru or not re.search(r'[А-Яа-яЁё]', ru):
                        if en != ru:
                            per_var['__raw__'][(en, ru)] += 0
                        continue
                    global_map[en][ru] += 1
                    v = var_of(b_line, pos_m.start())
                    if not v:
                        continue
                    per_var[v][(en, ru)] += 1
                    pairs += 1
            else:
                # keep going, mismatched line simply skipped
                pass
    per = {v: {en: c.most_common(1)[0][0] for (en, ru), n in cnt.items()
               for _ in [0]
               for c in [collections.Counter({ru: n for (e, r), n in cnt.items() if e == en and r == ru})]
               if n > 0}
           for v, cnt in per_var.items() if v != '__raw__'}
    # simpler rebuild (the comprehension above is only a placeholder for clarity)
    per = {}
    for v, cnt in per_var.items():
        if v == '__raw__':
            continue
        best = {}
        for (en, ru), n in cnt.items():
            if en not in best or n > best[en][1]:
                best[en] = (ru, n)
        per[v] = {en: ru for en, (ru, n) in best.items()}
    glob_map = {en: c.most_common(1)[0][0] for en, c in global_map.items()}
    json.dump({'per_var': per, 'global': glob_map, 'pairs': pairs},
              open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('variables: %d, global entries: %d, pairs: %d' % (len(per), len(glob_map), pairs))


if __name__ == '__main__':
    main(*sys.argv[1:4])
