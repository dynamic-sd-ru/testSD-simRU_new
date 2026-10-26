#!/usr/bin/env python3
"""js_localize.py BASE TR TARGET [--report out.json]

JavaScript blocks ({! ... !}) contain user visible strings and, for lookup
tables, object keys.  The translation of BASE localised both.  This tool learns
that localisation from (BASE, TR) and replays it on TARGET:

  * string literals : English literal -> Russian literal
  * object keys     : `Name: value` inside a table -> Russian key, together with
                      every `table.Name` / `table['Name']` access
"""
import sys
import os
import re
import json
import glob
import difflib
import collections

LIT = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
KEYLINE = re.compile(r'^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(\S.*)$')
ANYKEY = re.compile(r'^(\s*)([^\s:{}]+)\s*:\s*(\S.*)$')
ACCESS = re.compile(r'\.([A-Za-z_][A-Za-z0-9_]*)')
CYR = re.compile(r'[А-Яа-яЁё]')


def js_blocks(text):
    """[(start, end)] line ranges of multi-line {! ... !} blocks."""
    lines = text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        if '{!' in lines[i]:
            opened = lines[i].count('{!') - lines[i].count('!}')
            if opened <= 0:
                i += 1
                continue
            start = i
            j = i
            while opened > 0 and j + 1 < len(lines):
                j += 1
                opened += lines[j].count('{!') - lines[j].count('!}')
            if j > start:
                out.append((start, j))
            i = j + 1
            continue
        i += 1
    return out


def literals(line):
    return [m.group(1) if m.group(1) is not None else m.group(2)
            for m in LIT.finditer(line)]


def blank_strings(line):
    line = LIT.sub('S', line)
    return re.sub(r'^(\s*)([^\s:{}]+)(\s*:\s)', r'\1K\3', line)


def learn(base_dir, tr_dir):
    strings = collections.defaultdict(collections.Counter)
    keys = collections.defaultdict(collections.Counter)
    files = 0
    for p in sorted(glob.glob(base_dir + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, base_dir)
        t = os.path.join(tr_dir, rel)
        if not os.path.exists(t):
            continue
        bb = js_blocks(open(p, encoding='utf-8').read())
        tb = js_blocks(open(t, encoding='utf-8').read())
        if not bb or not tb:
            continue
        files += 1
        for (bs, be), (ts, te) in zip(bb, tb):
            bl = open(p, encoding='utf-8').read().split('\n')[bs:be + 1]
            tl = open(t, encoding='utf-8').read().split('\n')[ts:te + 1]
            sm = difflib.SequenceMatcher(None, [blank_strings(x) for x in bl],
                                         [blank_strings(x) for x in tl], autojunk=False)
            for i, j, n in sm.get_matching_blocks():
                for k in range(n):
                    a, b = bl[i + k], tl[j + k]
                    la, lb = literals(a), literals(b)
                    if len(la) == len(lb):
                        for en, ru in zip(la, lb):
                            if en != ru and re.search(r'[A-Za-z]', en) and CYR.search(ru):
                                strings[en][ru] += 1
                    ka, kb = KEYLINE.match(a), ANYKEY.match(b)
                    if ka and kb and ka.group(2) != kb.group(2) and CYR.search(kb.group(2)):
                        keys[ka.group(2)][kb.group(2)] += 1
    return strings, keys, files


def main(base_dir, tr_dir, target, report_path=None):
    strings, keys, files = learn(base_dir, tr_dir)
    str_map = {en: c.most_common(1)[0][0] for en, c in strings.items()}
    key_map = {en: c.most_common(1)[0][0] for en, c in keys.items()}
    for kw in ('if', 'for', 'while', 'switch', 'return', 'function', 'else', 'var'):
        key_map.pop(kw, None)

    n_str = n_key = 0
    for p in sorted(glob.glob(target + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        text = open(p, encoding='utf-8').read()
        blocks = js_blocks(text)
        if not blocks:
            continue
        lines = text.split('\n')
        touched = False
        for start, end in blocks:
            for i in range(start, end + 1):
                line = lines[i]

                def sub(m):
                    nonlocal n_str
                    quote = m.group(1) is not None and '"' or "'"
                    val = literals(m.group(0))[0]
                    ru = str_map.get(val)
                    if ru is None:
                        return m.group(0)
                    n_str += 1
                    return quote + ru + quote

                new = LIT.sub(sub, line)
                km = KEYLINE.match(new)
                if km and km.group(2) in key_map:
                    new = '%s%s: %s' % (km.group(1), key_map[km.group(2)], km.group(3))
                    n_key += 1
                new = ACCESS.sub(
                    lambda m: '.' + key_map.get(m.group(1), m.group(1)), new)
                if new != line:
                    lines[i] = new
                    touched = True
        if touched:
            open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    print('learned from %d files: strings %d, keys %d' % (files, len(str_map), len(key_map)))
    print('applied: strings %d, keys %d' % (n_str, n_key))
    if report_path:
        json.dump({'strings': str_map, 'keys': key_map},
                  open(report_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    argv = sys.argv[1:]
    rp = None
    if '--report' in argv:
        i = argv.index('--report')
        rp = argv[i + 1]
        del argv[i:i + 2]
    main(argv[0], argv[1], argv[2], rp)
