#!/usr/bin/env python3
"""fix_candkeys.py NEW_DIR TARGET

The translation renders the candidates' names in Russian, so the election code
builds variables like `Q["Гитлер_votes"]`, while the rest of the game (and the
new upstream code) reads `Q.Hitler_votes`.  This step inserts a small
`candkey()` helper (Russian name -> upstream key, taken from the new upstream
file itself) and wraps the dynamically built candidate variables with it.
"""
import json
import os
import re
import sys

FILES = [
    'scenes/events/death_of_hindenburg_president.scene.dry',
    'scenes/events/death_of_hindenburg_president_rubicon.scene.dry',
    'scenes/events/hindenburg_explode_president.scene.dry',
]

DYN = re.compile(r"Q\[([^\[\]]+?)\s*\+\s*'(_[a-z_]+)'\]")
WRAP = ('_votes', '_votes_disp', '_running', '_bonus')


def candidate_keys(text):
    m = re.search(r'candidate_descs\s*=\s*\{(.*?)\n\}', text, re.S)
    if not m:
        return []
    out = []
    for ln in m.group(1).split('\n'):
        mm = re.match(r'\s*"?([^":\s]+)"?\s*:', ln)
        if mm:
            out.append(mm.group(1).strip())
    return out


def block_spans(text):
    spans = []
    i = 0
    while True:
        a = text.find('{!', i)
        if a < 0:
            return spans
        depth, j = 0, a
        while j < len(text):
            if text.startswith('{!', j):
                depth += 1
                j += 2
                continue
            if text.startswith('!}', j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
                continue
            j += 1
        spans.append((a, j))
        i = j


def value_map_names(paths):
    """Russian -> upstream key for every value the translation renames."""
    out = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        tables = [d.get('global', {})]
        tables += list(d.get('per_var', {}).values())
        for t in tables:
            for en, ru in t.items():
                if not isinstance(ru, str) or not isinstance(en, str):
                    continue
                if re.match(r'^[A-Za-z][A-Za-z_\- ]*$', en) and re.match(
                        r'^[А-Яа-яЁё][А-Яа-яЁё_\- ]*$', ru):
                    out.setdefault(ru, en)
    return out


def main(new_dir, target_dir, log_path=None, *maps):
    stats = []
    for rel in FILES:
        tp = os.path.join(target_dir, rel)
        np_ = os.path.join(new_dir, rel)
        if not (os.path.exists(tp) and os.path.exists(np_)):
            continue
        text = open(tp, encoding='utf-8').read()
        ru = candidate_keys(text)
        en = candidate_keys(open(np_, encoding='utf-8').read())
        if not ru or len(ru) != len(en):
            stats.append((rel, 'ключи не совпали: %d/%d' % (len(ru), len(en)), 0))
            continue
        mapping = {r: e for r, e in zip(ru, en) if r != e}
        extra = value_map_names(maps or ('work/value_map.json', 'work/extra_map.json'))
        for r, e in extra.items():
            mapping.setdefault(r, e)
        helper = ('var cand_ascii = %s;\nfunction candkey(n) { return cand_ascii[n] || n; }\n'
                  % json.dumps(mapping, ensure_ascii=False))
        # work on blocks, from the end so the offsets stay valid
        for a, b in reversed(block_spans(text)):
            body = text[a:b]
            if 'cand_ascii' in body:
                continue
            needs = 'candidate_descs' in body or any(
                m.group(2) in WRAP for m in DYN.finditer(body))
            if not needs:
                continue
            new_body = DYN.sub(
                lambda m: ("Q[candkey(%s) + '%s']" % (m.group(1), m.group(2)))
                if m.group(2) in WRAP else m.group(0), body)
            anchor = new_body.find('\n', new_body.find('{!'))
            if anchor < 0:
                continue
            new_body = new_body[:anchor + 1] + helper + new_body[anchor + 1:]
            text = text[:a] + new_body + text[b:]
        open(tp, 'w', encoding='utf-8').write(text)
        n = text.count('candkey(')
        stats.append((rel, 'вставлено вызовов candkey', n))
    for rel, msg, n in stats:
        print('%-60s %-28s %d' % (rel, msg, n))
    if log_path:
        json.dump([{'file': r, 'note': m, 'calls': n} for r, m, n in stats],
                  open(log_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:])
