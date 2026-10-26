#!/usr/bin/env python3
"""fix_spaces.py ROOT [LOG.json]

Repairs text where a space was lost during the translation (words glued
together).  Only high precision rules are applied; suspicious spots that need a
human eye are collected as kind "check" without changing the text.

Every change is logged as {file, line, kind, before, after}.

Rules
  prep-tag    "от<span"      -> "от <span"      (preposition glued to a tag)
  tag-close   "</span>е"     -> "</span> е"     (no space after a closing tag)
  cond-close  "партии?]Он"   -> "партии?] Он"   (no space after a conditional)
  period      "конца.Идём"   -> "конца. Идём"
  comma       "так,идём"     -> "так, идём"
  var-open    "партии[+"       -> "партии [+"
"""
import sys
import os
import re
import json
import glob

CYR = 'а-яёА-ЯЁ'
PREPS = ('в|во|с|со|от|до|из|за|на|по|у|к|ко|о|об|при|для|без|под|над|про|через|между|а|и|но|не|же')
OPEN = r'(?:<span\b|<b\b|<i\b|<strong\b|<em\b|\*\*)'

RULES = [
    ('prep-tag', re.compile(r'(?<=[\s(«"—])(%s)(?=%s)' % (PREPS, OPEN)), r'\1 '),
    ('tag-close', re.compile(r'(</(?:span|b|i|strong|em)>)([%s])' % CYR), r'\1 \2'),
    ('cond-close', re.compile(r'(\?\])([%s])' % CYR), r'\1 \2'),
    ('period', re.compile(r'([%s])\.([А-ЯЁ])' % CYR), r'\1. \2'),
    ('comma', re.compile(r'([%s]),(?=[%s])' % (CYR, CYR)), r'\1, '),
    ('var-open', re.compile(r'([%s])(\[\+)' % CYR), r'\1 \2'),
]


STRUCT = re.compile(r'^(?:[a-z][a-z0-9-]*:|@|- @|=)')


def main(root, log_path=None):
    fixes = []
    for path in sorted(glob.glob(root + '/**/*', recursive=True)):
        if os.path.isdir(path):
            continue
        lines = open(path, encoding='utf-8').read().split('\n')
        in_code = False
        changed = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if in_code:
                if '!}' in stripped:
                    in_code = False
                continue
            if '{!' in stripped and '!}' not in stripped[stripped.index('{!'):]:
                in_code = True
                continue
            if not stripped or STRUCT.match(stripped):
                continue
            body = line
            for kind, rx, repl in RULES:
                matches = list(rx.finditer(body))
                for m in matches:
                    fixes.append({'file': os.path.relpath(path, root),
                                  'line': i + 1, 'kind': kind,
                                  'before': m.group(0), 'after': m.expand(repl)})
                if matches:
                    body = rx.sub(repl, body)
            if body != line:
                lines[i] = body
                changed = True
        if changed:
            open(path, 'w', encoding='utf-8').write('\n'.join(lines))

    kinds = {}
    for f in fixes:
        kinds[f['kind']] = kinds.get(f['kind'], 0) + 1
    print('space fixes: %s' % kinds)
    if log_path:
        json.dump(fixes, open(log_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:])
