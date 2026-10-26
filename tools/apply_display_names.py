#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_display_names.py ROOT

Bold party labels that the translation shows in Russian (`**СДПГ**`,
`**ФНЕГ**`, ...) sometimes survive upstream edits as Latin abbreviations
because the surrounding line was re-flowed by upstream.  This step rewrites
such labels using the party table of the translation.  Only `**LABEL**` tokens
are touched, never scene code, comments or html attributes.
"""
import glob
import re
import sys

PARTIES = {
    'DNEF': 'ФНЕГ', 'DNF': 'НФГ', 'DSU': 'НСС', 'NVF': 'ННФ', 'SAPD': 'СРПГ',
    'VNR': 'ННОР', 'CVD': 'ХНС', 'CSVD': 'ХСНС', 'CNBLP': 'ХНПКЗ',
    'KPD': 'КПГ', 'SPD': 'СДПГ', 'DVP': 'ННП', 'DNVP': 'НННП', 'KVP': 'КНП',
    'CVP': 'ХНП', 'LVP': 'ЛНП', 'NSDAP': 'НСДАП', 'WP': 'ЭП', 'BVP': 'БНП',
    'DDP': 'НДП', 'DStP': 'НГП', 'FKP': 'СКП', 'Z': 'Центр', 'I': 'б/п',
    'SA': 'СА', 'RFB': 'РФБ', 'Stahlhelm': 'Стальной Шлем',
    'Others': 'Прочие', 'Communists': 'коммунисты', 'Nazi': 'нацисты',
}
BOLD = re.compile(r'\*\*([A-Za-zА-Яа-яЁё][\w -]{0,12})\*\*')
ATTR = re.compile(r'(?:title|alt|src|id|class|style)="[^"]*"')


def convert(line):
    if line.lstrip().startswith('#'):
        return line
    parts = []
    last = 0
    for m in ATTR.finditer(line):
        parts.append((line[last:m.start()], True))
        parts.append((m.group(0), False))
        last = m.end()
    parts.append((line[last:], True))

    def sub(m):
        return '**%s**' % PARTIES.get(m.group(1), m.group(1))

    out = ''.join(BOLD.sub(sub, text) if free else text for text, free in parts)
    return out


def main(root):
    changed = 0
    files = 0
    for path in sorted(glob.glob(root + '/**/*.dry', recursive=True)):
        text = open(path, encoding='utf-8').read()
        lines = text.split('\n')
        touched = False
        for i, line in enumerate(lines):
            new = convert(line)
            if new != line:
                lines[i] = new
                changed += 1
                touched = True
        if touched:
            files += 1
            open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('party labels localised: %d in %d files' % (changed, files))


if __name__ == '__main__':
    main(sys.argv[1])
