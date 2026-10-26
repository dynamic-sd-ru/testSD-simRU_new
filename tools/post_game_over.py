#!/usr/bin/env python3
"""post_game_over.py TARGET TR [REPORT]

The translation re-flowed every achievement row of game_over.scene.dry onto one
line, so the line based assembler cannot map them.  Rows are paired by the
achievement condition (`achievement_x` / `game_achievement_x`): the translated
row replaces the upstream row, rows added upstream stay in English.

Brackets are matched with a depth counter because rows may contain nested
`[? if ... ?]` blocks.
"""
import re
import sys

ROW_START = re.compile(
    r'\[\?\s*if\s+(not\s+)?((?:game_)?achievement_[A-Za-z0-9_]+)\s*:')


def rows(text):
    """(negated, name) -> (start, end) spans of every achievement row."""
    out = {}
    i = 0
    while True:
        m = ROW_START.search(text, i)
        if not m:
            break
        depth = 0
        j = m.start()
        end = None
        while j < len(text):
            if text.startswith('[?', j):
                depth += 1
                j += 2
                continue
            if text.startswith('?]', j):
                depth -= 1
                j += 2
                if depth == 0:
                    end = j
                    break
                continue
            j += 1
        if end is None:
            break
        out[(bool(m.group(1)), m.group(2))] = (m.start(), end)
        i = end
    return out


def main(target, tr_path, report=None):
    text = open(target, encoding='utf-8').read()
    source = open(tr_path, encoding='utf-8').read()
    tr_rows = {name: source[a:b] for name, (a, b) in rows(source).items()}
    replaced, kept = [], []
    out = text
    spans = sorted(rows(text).items(), key=lambda kv: kv[1][0], reverse=True)
    for name, (a, b) in spans:
        if name in tr_rows:
            out = out[:a] + tr_rows[name].strip() + out[b:]
            replaced.append(name)
        else:
            kept.append(name)
    open(target, 'w', encoding='utf-8').write(out)
    print('achievement rows translated: %d, left in English: %d'
          % (len(replaced), len(kept)))
    if report:
        open(report, 'w', encoding='utf-8').write(
            'translated rows: %d\n\nNew upstream achievements (left in English):\n%s\n'
            % (len(replaced), '\n'.join(sorted('%s%s' % ('not ' if neg else '', n) for neg, n in kept))))


if __name__ == '__main__':
    main(*sys.argv[1:])
