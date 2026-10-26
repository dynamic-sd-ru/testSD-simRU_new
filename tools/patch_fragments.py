#!/usr/bin/env python3
"""patch_fragments.py OUT TR [--report log.json]

Line based assembly cannot map files whose translation re-flowed a block onto
one long line (cabinet lists, status tables, library tables).  This pass works
on *fragments*: a line is split into structural tokens (tags, `[? if cond:`,
`?]`, `[+ var +]`, `**`) and the text between them.  Structural tokens are
language independent, so they are used to find the translated counterpart of an
untranslated line and to transplant its text fragments.

Two strategies:
  1. same signature - identical structural token sequence;
  2. label        - short "Something:" lines, paired by order inside a scene.
"""
import sys
import os
import re
import glob
import json
import difflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dry import parse

TOKEN = re.compile(r'(\[\?\s*if\s+[^:]*?:|\?\]|\[\+\s*[^\]]*?\s*\+\]|'
                   r'</?[a-zA-Z][^>]*>|\*\*)')
CYR = re.compile(r'[А-Яа-яЁё]')
LABEL = re.compile(r'^([A-Za-z][A-Za-z \'\-]{2,40}):\s*$')


def split_line(line):
    """-> (tokens, texts). texts has len(tokens)+1 items."""
    parts = TOKEN.split(line)
    tokens, texts = [], []
    for i, part in enumerate(parts):
        if i % 2:
            tokens.append(part)
        else:
            texts.append(part)
    return tokens, texts


def join_line(tokens, texts):
    out = [texts[0]]
    for i, tok in enumerate(tokens):
        out.append(tok)
        out.append(texts[i + 1])
    return ''.join(out)


def is_english(text):
    return bool(re.search(r'[A-Za-z]{2,}', text)) and not CYR.search(text)


def scene_index(scenes):
    out = {}
    for sc in scenes:
        out.setdefault(sc['id'], sc)
    return out


def prose_lines(scene):
    return [c for c in scene['chunks'] if c[0] == 'prose']


def main(out_dir, tr_dir, report_path=None):
    stats = {'fragment': 0, 'label': 0, 'files': 0}
    details = []
    for p in sorted(glob.glob(out_dir + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, out_dir)
        t = os.path.join(tr_dir, rel)
        if not os.path.exists(t):
            continue
        out_text = open(p, encoding='utf-8').read()
        out_scenes = scene_index(parse(out_text))
        tr_scenes = scene_index(parse(open(t, encoding='utf-8').read()))
        lines = out_text.split('\n')
        changed = False
        for sid, sc in out_scenes.items():
            tr_sc = tr_scenes.get(sid)
            if not tr_sc:
                continue
            tr_lines = []
            tr_labels = []
            for ch in prose_lines(tr_sc):
                tokens, texts = split_line(ch[1])
                tr_lines.append((tokens, texts))
                lead = texts[0].strip()
                if lead.endswith(':') and len(lead) <= 60:
                    tr_labels.append(lead)

            out_prose = prose_lines(sc)
            out_texts = {c[1] for c in out_prose}
            tr_labels = [x for x in tr_labels if x not in out_texts]

            # strategy 1: contiguous token subsequence, unique in the scene
            for ch in out_prose:
                tokens, texts = split_line(ch[1])
                if len(tokens) < 2 or CYR.search(ch[1]):
                    continue
                if not any(is_english(x) for x in texts):
                    continue
                hits = []
                for tl_tokens, tl_texts in tr_lines:
                    for off in range(len(tl_tokens) - len(tokens) + 1):
                        if tl_tokens[off:off + len(tokens)] == tokens:
                            hits.append(tl_texts[off:off + len(texts)])
                if len(hits) != 1 or len(hits[0]) != len(texts):
                    continue
                cand = hits[0]
                # only short fragments are safe to transplant
                if max(len(x) for x in texts + cand) > 120:
                    continue
                if (texts[0].strip() == '') != (cand[0].strip() == ''):
                    continue
                if (texts[-1].strip() == '') != (cand[-1].strip() == ''):
                    continue
                new_line = join_line(tokens, hits[0])
                if not CYR.search(new_line):
                    continue
                lines[ch[-1]] = lines[ch[-1]].replace(ch[1], new_line)
                stats['fragment'] += 1
                details.append([rel, ch[-1], 'fragment', ch[1][:80], new_line[:80]])
                changed = True

            # strategy 2: label lines in order
            out_labels = [c for c in out_prose
                          if not split_line(c[1])[0] and LABEL.match(c[1])]
            if out_labels and len(out_labels) == len(tr_labels):
                for ch, ru in zip(out_labels, tr_labels):
                    if not is_english(ch[1].split(':')[0]):
                        continue
                    lines[ch[-1]] = lines[ch[-1]].replace(ch[1], ru + ' ')
                    stats['label'] += 1
                    details.append([rel, ch[-1], 'label', ch[1], ru])
                    changed = True
        if changed:
            stats['files'] += 1
            open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    print('fragment patches: %s' % stats)
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
    main(argv[0], argv[1], rp)
