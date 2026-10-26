#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_tr_breaks.py ROOT MAP

Точечные исправления мест, где готовый перевод оказался испорчен: оборванная
строка, потерянный абзац, сломанная разметка `<span>`.  Карта — JSON-список
[файл, что_заменить, чем_заменить]; замена выполняется только если фрагмент
встретился ровно один раз.
"""
import json
import os
import sys


def main(root, map_path):
    fixes = json.load(open(map_path, encoding='utf-8'))
    done = 0
    for rel, old, new in fixes:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            print('  нет файла:', rel)
            continue
        text = open(path, encoding='utf-8').read()
        cnt = text.count(old)
        if cnt != 1:
            print('  %s: фрагмент встречается %d раз — пропуск' % (rel, cnt))
            continue
        open(path, 'w', encoding='utf-8').write(text.replace(old, new))
        done += 1
    print('tr fixes applied: %d of %d' % (done, len(fixes)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
