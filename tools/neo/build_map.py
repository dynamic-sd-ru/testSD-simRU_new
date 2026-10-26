# -*- coding: utf-8 -*-
"""Собрать tools/maps/neo_ru.json из part_a/part_b/part_c.

part_a и part_b — ручной перевод 154 строк из tools/maps/neo_sources.json,
part_c — точечные строки, найденные по подстроке в исходнике upstream.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NEW = os.environ.get('NEW_SRC', '/home/user/work/new/source')


def load_dict(path):
    g = {}
    exec(open(path, encoding='utf-8').read(), g)
    return g['RU']


def main():
    items = json.load(open(os.path.join(REPO, 'tools/maps/neo_sources.json'),
                           encoding='utf-8'))
    ru = {}
    ru.update(load_dict(os.path.join(HERE, 'part_a.py')))
    ru.update(load_dict(os.path.join(HERE, 'part_b.py')))
    pairs = {}
    for i, it in enumerate(items):
        val = ru.get(i)
        if val is None or val == 'KEEP':
            continue
        pairs[it['en']] = val
    sys.path.insert(0, os.path.join(REPO, 'tools'))
    import part_c
    from apply_neo import split_prefix
    for rel, needle, text in part_c.OVERRIDES:
        path = os.path.join(NEW, rel)
        hits = [l.strip() for l in open(path, encoding='utf-8').read().split('\n')
                if needle in l and l.strip() and not l.strip().startswith('#')]
        if not hits:
            raise SystemExit('%s: %r не найдено' % (rel, needle))
        if len(set(hits)) != 1:
            raise SystemExit('%s: %r -> %d разных строк' % (rel, needle, len(set(hits))))
        _, body = split_prefix(hits[0])
        pairs[body] = text
    out = os.path.join(REPO, 'tools/maps/neo_ru.json')
    json.dump(pairs, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('neo_ru.json: %d строк' % len(pairs))


if __name__ == '__main__':
    main()
