#!/usr/bin/env python3
"""carry_code.py BASE TR TARGET

The translation carries a few hand written JavaScript changes (candidate name
mapping for the 1934 election, tutorial card captions, the "Continue"
detection).  The assembler keeps the code of the current upstream version, so
those edits are re-applied here.

Rules (per scene, per code block):
  * only hunks whose TARGET side is still identical to the same lines of BASE
    (string literals and whitespace normalised) are touched, i.e. upstream did
    not edit that code;
  * a hunk is applied only when its structure really changed - differences
    limited to string literals are handled by js_localize / apply_values and
    are left alone;
  * code that introduces Cyrillic identifiers is never carried;
  * insertions are only taken from a small whitelist of files, where the
    translation deliberately adds lines.
"""
import difflib
import os
import re
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dry

LIT = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
CYR = re.compile(r'[А-Яа-яЁё]')
WS = re.compile(r'\s+')

# files where the translation adds code lines upstream does not have
CARRY_FILES = {
    'scenes/main.scene.dry',
    'scenes/post_event.scene.dry',
}
INSERT_FILES = CARRY_FILES


def mask(text):
    return LIT.sub('"S"', text)


def norm_key(text):
    """comparison key: literals and whitespace normalised away"""
    return WS.sub('', mask(text))


def bad_identifier(text):
    return bool(CYR.search(mask(text)))


def scene_codes(path):
    """[(scene key, [line numbers of code chunks])]"""
    text = open(path, encoding='utf-8', errors='replace').read()
    out = []
    anon = 0
    for sc in dry.parse(text):
        key = sc['id']
        if key is None:
            key = '#anon%d' % anon
            anon += 1
        out.append((key, [c[-1] for c in sc['chunks'] if c[0] == 'code']))
    return out


def read_lines(path):
    return open(path, encoding='utf-8', errors='replace').read().split('\n')


def main(base_dir, tr_dir, target_dir):
    n_set = n_ins = n_files = 0
    for p in sorted(glob.glob(os.path.join(target_dir, '**', '*.dry'), recursive=True)):
        rel = os.path.relpath(p, target_dir)
        bp, tp = os.path.join(base_dir, rel), os.path.join(tr_dir, rel)
        if not (os.path.exists(bp) and os.path.exists(tp)):
            continue
        out_lines, base_lines, tr_lines = read_lines(p), read_lines(bp), read_lines(tp)
        if rel not in CARRY_FILES:
            continue
        base_codes, tr_codes = dict(scene_codes(bp)), dict(scene_codes(tp))
        edits = []                       # (start, end, [new lines])
        for key, out_no in scene_codes(p):
            tr_no = tr_codes.get(key)
            if not tr_no:
                continue
            a = [norm_key(out_lines[i].strip()) for i in out_no if i < len(out_lines)]
            b = [norm_key(tr_lines[j].strip()) for j in tr_no if j < len(tr_lines)]
            bc = [norm_key(base_lines[i].strip())
                  for i in base_codes.get(key, []) if i < len(base_lines)]
            same_as_base = [False] * len(a)
            if bc:
                for i, j, n in difflib.SequenceMatcher(
                        None, bc, a, autojunk=False).get_matching_blocks():
                    for k in range(n):
                        same_as_base[j + k] = True
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                    None, a, b, autojunk=False).get_opcodes():
                if tag == 'equal' or not all(same_as_base[i] for i in range(i1, i2)):
                    continue
                new = [tr_lines[tr_no[j]] for j in range(j1, j2)]
                if tag == 'replace':
                    if a[i1:i2] == b[j1:j2]:
                        continue         # only literals/whitespace differ
                    if any(bad_identifier(x) for x in new):
                        continue
                    start = out_no[i1]
                    end = out_no[i2 - 1] + 1 if i2 > i1 else start
                    edits.append((start, end, new))
                    n_set += len(new)
                elif tag == 'insert':
                    if rel not in INSERT_FILES or i1 == 0:
                        continue
                    if any(bad_identifier(x) for x in new):
                        continue
                    anchor = out_no[i1 - 1]
                    edits.append((anchor + 1, anchor + 1, new))
                    n_ins += len(new)
                # 'delete' is ignored: upstream code is never dropped
        if not edits:
            continue
        for start, end, new in sorted(edits, key=lambda e: -e[0]):
            indent = ''
            if start < len(out_lines):
                old = out_lines[start]
                indent = old[:len(old) - len(old.lstrip())]
            payload = []
            for x in new:
                payload.append(x if x[:1].isspace() or not indent else indent + x)
            out_lines[start:end] = payload
        open(p, 'w', encoding='utf-8').write('\n'.join(out_lines))
        n_files += 1
    print('code: replaced/inserted lines %d/%d in %d files'
          % (n_set, n_ins, n_files))


if __name__ == '__main__':
    main(*sys.argv[1:4])
